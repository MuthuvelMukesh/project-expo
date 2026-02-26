"""
CampusIQ — NLP CRUD Engine Service
Translates natural language queries into safe database operations.
Uses Gemini (via key-pool client) for intent detection and entity extraction,
with keyword-based fallback when Gemini is unavailable.
"""

import json
import re
import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, insert, and_, or_, cast, String
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.models import (
    User, UserRole, Department, Student, Faculty, Course, Attendance, Prediction
)
from app.services.gemini_pool_service import GeminiPoolClient, GeminiPoolError

settings = get_settings()
log = logging.getLogger("campusiq.nlp_crud")

# ─── Model Registry ─────────────────────────────────────────────
# Maps natural language entity names to SQLAlchemy models + metadata
MODEL_REGISTRY = {
    "student": {
        "model": Student,
        "display": "Student",
        "columns": ["id", "roll_number", "semester", "section", "cgpa", "admission_year"],
        "searchable": ["roll_number", "section"],
        "relationships": {"user": User, "department": Department},
        "join_display": {
            "user.full_name": "Name",
            "user.email": "Email",
            "department.name": "Department",
        },
    },
    "faculty": {
        "model": Faculty,
        "display": "Faculty",
        "columns": ["id", "employee_id", "designation"],
        "searchable": ["employee_id", "designation"],
        "relationships": {"user": User, "department": Department},
        "join_display": {
            "user.full_name": "Name",
            "user.email": "Email",
            "department.name": "Department",
        },
    },
    "course": {
        "model": Course,
        "display": "Course",
        "columns": ["id", "code", "name", "semester", "credits"],
        "searchable": ["code", "name"],
        "relationships": {"department": Department, "instructor": Faculty},
        "join_display": {
            "department.name": "Department",
        },
    },
    "department": {
        "model": Department,
        "display": "Department",
        "columns": ["id", "name", "code"],
        "searchable": ["name", "code"],
        "relationships": {},
        "join_display": {},
    },
    "attendance": {
        "model": Attendance,
        "display": "Attendance",
        "columns": ["id", "date", "is_present", "method", "marked_at"],
        "searchable": ["method"],
        "relationships": {"student": Student, "course": Course},
        "join_display": {
            "course.name": "Course",
        },
    },
    "prediction": {
        "model": Prediction,
        "display": "Prediction",
        "columns": ["id", "predicted_grade", "risk_score", "confidence", "created_at"],
        "searchable": ["predicted_grade"],
        "relationships": {"student": Student},
        "join_display": {},
    },
    "user": {
        "model": User,
        "display": "User",
        "columns": ["id", "email", "full_name", "role", "is_active", "created_at"],
        "searchable": ["email", "full_name"],
        "relationships": {},
        "join_display": {},
    },
}

# Entity aliases for NL understanding
ENTITY_ALIASES = {
    "students": "student", "learner": "student", "learners": "student",
    "teachers": "faculty", "teacher": "faculty", "professor": "faculty",
    "professors": "faculty", "instructor": "faculty", "instructors": "faculty",
    "courses": "course", "subject": "course", "subjects": "course",
    "class": "course", "classes": "course",
    "departments": "department", "dept": "department", "depts": "department",
    "branch": "department", "branches": "department",
    "users": "user", "account": "user", "accounts": "user",
    "attendances": "attendance", "presence": "attendance",
    "predictions": "prediction", "grades": "prediction", "results": "prediction",
}

# ─── Access Control ──────────────────────────────────────────────
ACCESS_RULES = {
    "student": {
        "allowed_intents": ["READ", "ANALYZE", "UPDATE"],
        "self_update_only": True,
        "updatable_entities": ["student"],
        "updatable_fields": ["section", "semester"],
    },
    "faculty": {
        "allowed_intents": ["READ", "ANALYZE", "CREATE", "UPDATE", "DELETE"],
        "self_update_only": False,
        "updatable_entities": ["student", "attendance", "course", "prediction"],
        "creatable_entities": ["attendance", "prediction"],
        "deletable_entities": ["attendance"],
    },
    "admin": {
        "allowed_intents": ["READ", "ANALYZE", "CREATE", "UPDATE", "DELETE"],
        "self_update_only": False,
        "updatable_entities": None,  # all
        "creatable_entities": None,  # all
    },
}


def _check_access(user_role: str, intent: str, entity: str) -> tuple[bool, str]:
    """Check if the user role can perform the given intent on the entity."""
    rules = ACCESS_RULES.get(user_role, ACCESS_RULES["student"])

    if intent not in rules["allowed_intents"]:
        return False, f"❌ As a **{user_role}**, you don't have permission to **{intent}** data. Please contact an admin."

    if intent in ("CREATE",):
        allowed = rules.get("creatable_entities")
        if allowed is not None and entity not in allowed:
            return False, f"❌ As a **{user_role}**, you cannot create **{entity}** records."

    if intent in ("UPDATE",):
        allowed = rules.get("updatable_entities")
        if allowed is not None and entity not in allowed:
            return False, f"❌ As a **{user_role}**, you cannot modify **{entity}** records."

    if intent in ("DELETE",):
        allowed = rules.get("deletable_entities", rules.get("updatable_entities"))
        if allowed is not None and entity not in allowed:
            return False, f"❌ As a **{user_role}**, you cannot delete **{entity}** records."

    return True, ""


# ─── Intent Detection ────────────────────────────────────────────

async def detect_intent_llm(message: str) -> Optional[dict]:
    """Use Gemini to detect intent and extract structured info from a natural language message."""
    prompt = f"""You are a database query classifier for a college ERP system called CampusIQ.
The database has these tables: students, faculty, courses, departments, attendance, predictions, users.

Analyze the user's message and return a JSON object with:
- "intent": one of "READ", "CREATE", "UPDATE", "DELETE", "ANALYZE"
- "entity": the main table being referenced (student, faculty, course, department, attendance, prediction, user)
- "filters": object with column-value filters if any (e.g. {{"department": "Computer Science", "semester": 5}})
- "values": object with values for CREATE/UPDATE (e.g. {{"name": "AI", "code": "CS501"}})
- "aggregation": for ANALYZE queries, one of "count", "average", "sum", "min", "max", "group_by" or null
- "group_by": column to group by if aggregation uses group_by, or null
- "limit": number of results to limit to, or null

User message: "{message}"

Return ONLY valid JSON, no other text."""

    try:
        result = await GeminiPoolClient.generate_json(module="nlp", prompt=prompt, timeout=20.0)
        content = result.get("text", "")
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except GeminiPoolError as e:
        log.warning("Gemini NLP pool error in detect_intent_llm: %s (code=%s)", e.message, e.code)
    except json.JSONDecodeError as e:
        log.warning("Failed to parse Gemini JSON response for intent detection: %s", e)
    except Exception as e:
        log.error("Unexpected error in detect_intent_llm: %s", e, exc_info=True)

    return None


def detect_intent_keyword(message: str) -> dict:
    """Keyword-based fallback for intent detection when LLM is unavailable."""
    msg = message.lower().strip()

    # Detect intent
    intent = "READ"
    if any(w in msg for w in ["add", "create", "insert", "register", "new", "enroll"]):
        intent = "CREATE"
    elif any(w in msg for w in ["update", "change", "modify", "set", "edit", "fill", "enter my"]):
        intent = "UPDATE"
    elif any(w in msg for w in ["delete", "remove", "drop", "erase"]):
        intent = "DELETE"
    elif any(w in msg for w in ["how many", "count", "average", "avg", "total",
                                  "statistics", "stats", "analyze", "analysis",
                                  "percentage", "distribution", "group by",
                                  "compare", "top", "highest", "lowest", "minimum",
                                  "maximum", "sum"]):
        intent = "ANALYZE"

    # Detect entity
    entity = None
    for alias, canonical in {**{k: k for k in MODEL_REGISTRY}, **ENTITY_ALIASES}.items():
        if alias in msg:
            entity = canonical
            break

    if entity is None:
        # Default guessing based on context
        if any(w in msg for w in ["attendance", "present", "absent", "class"]):
            entity = "attendance"
        elif any(w in msg for w in ["grade", "risk", "predict", "score"]):
            entity = "prediction"
        elif any(w in msg for w in ["cgpa", "roll", "semester"]):
            entity = "student"
        else:
            entity = "student"  # default

    # Detect aggregation
    aggregation = None
    group_by = None
    if intent == "ANALYZE":
        if any(w in msg for w in ["how many", "count", "total number"]):
            aggregation = "count"
        elif any(w in msg for w in ["average", "avg", "mean"]):
            aggregation = "average"
        elif "sum" in msg:
            aggregation = "sum"
        elif any(w in msg for w in ["highest", "maximum", "max", "top"]):
            aggregation = "max"
        elif any(w in msg for w in ["lowest", "minimum", "min"]):
            aggregation = "min"
        elif any(w in msg for w in ["group", "by department", "by semester", "distribution",
                                      "per department", "per semester"]):
            aggregation = "group_by"
            if "department" in msg or "dept" in msg or "branch" in msg:
                group_by = "department"
            elif "semester" in msg:
                group_by = "semester"
            elif "section" in msg:
                group_by = "section"
            elif "course" in msg or "subject" in msg:
                group_by = "course"

    # Simple filter extraction
    filters = {}
    # Department filter
    dept_match = re.search(r'(?:in|from|of|for)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:department|dept|branch)', msg, re.IGNORECASE)
    if dept_match:
        filters["department"] = dept_match.group(1)

    # Semester filter
    sem_match = re.search(r'semester\s+(\d+)', msg, re.IGNORECASE)
    if sem_match:
        filters["semester"] = int(sem_match.group(1))

    # CGPA filter
    cgpa_match = re.search(r'cgpa\s*(?:below|under|less than|<)\s*([\d.]+)', msg, re.IGNORECASE)
    if cgpa_match:
        filters["cgpa_lt"] = float(cgpa_match.group(1))
    cgpa_match = re.search(r'cgpa\s*(?:above|over|greater than|more than|>)\s*([\d.]+)', msg, re.IGNORECASE)
    if cgpa_match:
        filters["cgpa_gt"] = float(cgpa_match.group(1))

    # Attendance percentage filter
    att_match = re.search(r'attendance\s*(?:below|under|less than|<)\s*(\d+)%?', msg, re.IGNORECASE)
    if att_match:
        filters["attendance_below"] = int(att_match.group(1))

    # Limit
    limit = None
    limit_match = re.search(r'(?:top|first|show)\s+(\d+)', msg, re.IGNORECASE)
    if limit_match:
        limit = int(limit_match.group(1))

    # Extract values for CREATE/UPDATE
    values = {}
    if intent in ("CREATE", "UPDATE"):
        # Name value
        name_match = re.search(r'(?:called|named|name)\s+["\']?([^"\']+?)["\']?(?:\s+with|\s+in|\s+for|$)', msg, re.IGNORECASE)
        if name_match:
            values["name"] = name_match.group(1).strip()

        # Code value
        code_match = re.search(r'(?:code|id)\s+["\']?([A-Z0-9]+)["\']?', msg, re.IGNORECASE)
        if code_match:
            values["code"] = code_match.group(1).strip()

        # CGPA value for update
        cgpa_val = re.search(r'cgpa\s+(?:to\s+)?([\d.]+)', msg, re.IGNORECASE)
        if cgpa_val:
            values["cgpa"] = float(cgpa_val.group(1))

        # Semester value
        sem_val = re.search(r'semester\s+(?:to\s+)?(\d+)', msg, re.IGNORECASE)
        if sem_val and intent == "UPDATE":
            values["semester"] = int(sem_val.group(1))

    return {
        "intent": intent,
        "entity": entity,
        "filters": filters,
        "values": values,
        "aggregation": aggregation,
        "group_by": group_by,
        "limit": limit,
    }


# ─── Query Execution ─────────────────────────────────────────────

async def execute_read(
    db: AsyncSession, entity: str, filters: dict, limit: Optional[int] = None
) -> dict:
    """Execute a READ query and return formatted results."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    stmt = select(model)

    # Apply relationship joins for display
    for rel_name in reg["relationships"]:
        if hasattr(model, rel_name):
            stmt = stmt.options(selectinload(getattr(model, rel_name)))

    # Apply filters
    stmt = _apply_filters(stmt, model, entity, filters)

    if limit:
        stmt = stmt.limit(limit)
    else:
        stmt = stmt.limit(50)  # Safety cap

    result = await db.execute(stmt)
    rows = result.scalars().all()

    # Format results
    formatted_rows = []
    for row in rows:
        row_data = {}
        for col in reg["columns"]:
            val = getattr(row, col, None)
            if val is not None:
                row_data[col] = str(val)

        # Add joined display fields
        for rel_path, display_name in reg["join_display"].items():
            parts = rel_path.split(".")
            obj = row
            for p in parts:
                obj = getattr(obj, p, None)
                if obj is None:
                    break
            if obj is not None:
                row_data[display_name] = str(obj)

        formatted_rows.append(row_data)

    total_count = len(formatted_rows)

    # Build human-readable summary
    if total_count == 0:
        summary = f"No **{reg['display']}** records found matching your criteria."
    elif total_count == 1:
        summary = f"Found **1 {reg['display']}** record:"
    else:
        summary = f"Found **{total_count} {reg['display']}** records:"

    return {
        "intent": "READ",
        "entity": reg["display"],
        "result": {"data": formatted_rows},
        "summary": summary,
        "row_count": total_count,
    }


async def execute_analyze(
    db: AsyncSession, entity: str, filters: dict,
    aggregation: Optional[str] = None, group_by_col: Optional[str] = None
) -> dict:
    """Execute an ANALYZE (aggregation) query."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    if aggregation == "count":
        stmt = select(func.count()).select_from(model)
        stmt = _apply_filters(stmt, model, entity, filters)
        result = await db.execute(stmt)
        count = result.scalar()
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {"count": count},
            "summary": f"📊 Total **{reg['display']}** count: **{count}**",
            "row_count": 1,
        }

    elif aggregation == "average" and entity == "student":
        stmt = select(func.avg(Student.cgpa))
        stmt = _apply_filters(stmt, model, entity, filters)
        result = await db.execute(stmt)
        avg_val = result.scalar()
        avg_val = round(float(avg_val), 2) if avg_val else 0
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {"average_cgpa": avg_val},
            "summary": f"📊 Average CGPA: **{avg_val}**",
            "row_count": 1,
        }

    elif aggregation == "group_by" and group_by_col:
        return await _execute_group_by(db, entity, group_by_col, filters)

    elif aggregation in ("max", "min") and entity == "student":
        agg_func = func.max if aggregation == "max" else func.min
        stmt = select(agg_func(Student.cgpa))
        stmt = _apply_filters(stmt, model, entity, filters)
        result = await db.execute(stmt)
        val = result.scalar()
        val = round(float(val), 2) if val else 0
        label = "Highest" if aggregation == "max" else "Lowest"
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {f"{aggregation}_cgpa": val},
            "summary": f"📊 {label} CGPA: **{val}**",
            "row_count": 1,
        }

    # Default: just count
    stmt = select(func.count()).select_from(model)
    stmt = _apply_filters(stmt, model, entity, filters)
    result = await db.execute(stmt)
    count = result.scalar()
    return {
        "intent": "ANALYZE",
        "entity": reg["display"],
        "result": {"count": count},
        "summary": f"📊 Total **{reg['display']}** records: **{count}**",
        "row_count": 1,
    }


async def _execute_group_by(
    db: AsyncSession, entity: str, group_by_col: str, filters: dict
) -> dict:
    """Execute a GROUP BY aggregation."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    if group_by_col == "department" and entity == "student":
        stmt = (
            select(Department.name, func.count(Student.id), func.avg(Student.cgpa))
            .join(Department, Student.department_id == Department.id)
            .group_by(Department.name)
        )
        result = await db.execute(stmt)
        rows = result.all()
        data = [
            {"Department": r[0], "Student Count": r[1], "Avg CGPA": round(float(r[2]), 2) if r[2] else 0}
            for r in rows
        ]
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {"data": data},
            "summary": f"📊 **Students grouped by Department** ({len(data)} departments):",
            "row_count": len(data),
        }

    elif group_by_col == "semester" and entity == "student":
        stmt = (
            select(Student.semester, func.count(Student.id), func.avg(Student.cgpa))
            .group_by(Student.semester)
            .order_by(Student.semester)
        )
        result = await db.execute(stmt)
        rows = result.all()
        data = [
            {"Semester": r[0], "Student Count": r[1], "Avg CGPA": round(float(r[2]), 2) if r[2] else 0}
            for r in rows
        ]
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {"data": data},
            "summary": f"📊 **Students grouped by Semester** ({len(data)} semesters):",
            "row_count": len(data),
        }

    elif group_by_col == "department" and entity == "course":
        stmt = (
            select(Department.name, func.count(Course.id))
            .join(Department, Course.department_id == Department.id)
            .group_by(Department.name)
        )
        result = await db.execute(stmt)
        rows = result.all()
        data = [
            {"Department": r[0], "Course Count": r[1]}
            for r in rows
        ]
        return {
            "intent": "ANALYZE",
            "entity": reg["display"],
            "result": {"data": data},
            "summary": f"📊 **Courses grouped by Department** ({len(data)} departments):",
            "row_count": len(data),
        }

    # Fallback: simple count
    stmt = select(func.count()).select_from(model)
    result = await db.execute(stmt)
    count = result.scalar()
    return {
        "intent": "ANALYZE",
        "entity": reg["display"],
        "result": {"count": count},
        "summary": f"📊 Total **{reg['display']}** records: **{count}**",
        "row_count": 1,
    }


async def execute_create(
    db: AsyncSession, entity: str, values: dict
) -> dict:
    """Execute a CREATE operation."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    try:
        if entity == "department":
            new_obj = Department(
                name=values.get("name", "New Department"),
                code=values.get("code", "NEW"),
            )
        elif entity == "course":
            dept_name = values.get("department")
            dept_id = None
            if dept_name:
                result = await db.execute(
                    select(Department).where(
                        func.lower(Department.name).like(f"%{dept_name.lower()}%")
                    )
                )
                dept = result.scalar_one_or_none()
                if dept:
                    dept_id = dept.id

            new_obj = Course(
                name=values.get("name", "New Course"),
                code=values.get("code", "NEW101"),
                department_id=dept_id or 1,
                semester=values.get("semester", 1),
                credits=values.get("credits", 3),
            )
        else:
            return {
                "intent": "CREATE",
                "entity": reg["display"],
                "result": None,
                "summary": f"❌ Auto-creation of **{reg['display']}** records is not supported via NL. Please use the dedicated API endpoints.",
                "row_count": 0,
                "error": "Unsupported entity for NL create",
            }

        db.add(new_obj)
        await db.flush()

        return {
            "intent": "CREATE",
            "entity": reg["display"],
            "result": {"id": new_obj.id},
            "summary": f"✅ Successfully created a new **{reg['display']}** record (ID: {new_obj.id}).",
            "row_count": 1,
        }

    except Exception as e:
        return {
            "intent": "CREATE",
            "entity": reg["display"],
            "result": None,
            "summary": f"❌ Failed to create **{reg['display']}** record: {str(e)}",
            "row_count": 0,
            "error": str(e),
        }


async def execute_update(
    db: AsyncSession, entity: str, filters: dict, values: dict,
    user_id: Optional[int] = None, self_only: bool = False
) -> dict:
    """Execute an UPDATE operation."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    try:
        # Build select to find target row(s)
        stmt = select(model)
        stmt = _apply_filters(stmt, model, entity, filters)

        # For self-update (students), restrict to own records
        if self_only and entity == "student":
            stmt = stmt.where(Student.user_id == user_id)

        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return {
                "intent": "UPDATE",
                "entity": reg["display"],
                "result": None,
                "summary": f"❌ No **{reg['display']}** records found matching your criteria to update.",
                "row_count": 0,
            }

        updated = 0
        for row in rows:
            for key, val in values.items():
                if hasattr(row, key):
                    setattr(row, key, val)
                    updated += 1

        await db.flush()

        return {
            "intent": "UPDATE",
            "entity": reg["display"],
            "result": {"updated_count": len(rows)},
            "summary": f"✅ Updated **{len(rows)} {reg['display']}** record(s) successfully.",
            "row_count": len(rows),
        }

    except Exception as e:
        return {
            "intent": "UPDATE",
            "entity": reg["display"],
            "result": None,
            "summary": f"❌ Failed to update **{reg['display']}** record: {str(e)}",
            "row_count": 0,
            "error": str(e),
        }


async def execute_delete(
    db: AsyncSession, entity: str, filters: dict
) -> dict:
    """Execute a DELETE operation."""
    reg = MODEL_REGISTRY[entity]
    model = reg["model"]

    try:
        # First find how many will be affected
        stmt = select(model)
        stmt = _apply_filters(stmt, model, entity, filters)
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            return {
                "intent": "DELETE",
                "entity": reg["display"],
                "result": None,
                "summary": f"❌ No **{reg['display']}** records found matching your criteria to delete.",
                "row_count": 0,
            }

        count = len(rows)
        for row in rows:
            await db.delete(row)

        await db.flush()

        return {
            "intent": "DELETE",
            "entity": reg["display"],
            "result": {"deleted_count": count},
            "summary": f"🗑️ Deleted **{count} {reg['display']}** record(s) successfully.",
            "row_count": count,
        }

    except Exception as e:
        return {
            "intent": "DELETE",
            "entity": reg["display"],
            "result": None,
            "summary": f"❌ Failed to delete **{reg['display']}** record: {str(e)}",
            "row_count": 0,
            "error": str(e),
        }


# ─── Filter Builder ──────────────────────────────────────────────

def _apply_filters(stmt, model, entity: str, filters: dict):
    """Apply parsed filters to a SQLAlchemy statement."""
    if not filters:
        return stmt

    for key, value in filters.items():
        # Department name filter (requires join)
        if key == "department" and entity in ("student", "course", "faculty"):
            if entity == "student":
                stmt = stmt.join(Department, Student.department_id == Department.id)
            elif entity == "course":
                stmt = stmt.join(Department, Course.department_id == Department.id)
            elif entity == "faculty":
                stmt = stmt.join(Department, Faculty.department_id == Department.id)
            stmt = stmt.where(func.lower(Department.name).like(f"%{value.lower()}%"))

        # Semester filter
        elif key == "semester" and hasattr(model, "semester"):
            stmt = stmt.where(model.semester == value)

        # CGPA filters (support both cgpa_lt and cgpa__lt formats)
        elif key in ("cgpa_lt", "cgpa__lt") and entity == "student":
            stmt = stmt.where(Student.cgpa < value)
        elif key in ("cgpa_gt", "cgpa__gt") and entity == "student":
            stmt = stmt.where(Student.cgpa > value)
        elif key in ("cgpa_lte", "cgpa__lte") and entity == "student":
            stmt = stmt.where(Student.cgpa <= value)
        elif key in ("cgpa_gte", "cgpa__gte") and entity == "student":
            stmt = stmt.where(Student.cgpa >= value)

        # ID filter
        elif key == "id":
            stmt = stmt.where(model.id == int(value))

        # Roll number filter
        elif key == "roll_number" and entity == "student":
            stmt = stmt.where(func.lower(Student.roll_number).like(f"%{str(value).lower()}%"))

        # Name filter (search in user.full_name for student/faculty)
        elif key == "name":
            if entity in ("student", "faculty"):
                stmt = stmt.join(User, model.user_id == User.id)
                stmt = stmt.where(func.lower(User.full_name).like(f"%{value.lower()}%"))
            elif hasattr(model, "name"):
                stmt = stmt.where(func.lower(model.name).like(f"%{value.lower()}%"))

        # Code filter
        elif key == "code" and hasattr(model, "code"):
            stmt = stmt.where(func.lower(model.code) == value.lower())

        # Attendance below threshold
        elif key == "attendance_below":
            pass  # Complex subquery; handled separately if needed

        # Direct column match
        elif hasattr(model, key):
            stmt = stmt.where(getattr(model, key) == value)

    return stmt


# ─── Main Entry Point ────────────────────────────────────────────

async def process_nlp_crud(
    message: str,
    user_role: str,
    user_id: int,
    db: AsyncSession,
) -> dict:
    """
    Main entry: process a natural language query into a CRUD operation.

    Returns a dict with: intent, entity, result, summary, row_count, error (if any).
    """
    # Step 1: Detect intent (try LLM, fallback to keyword)
    parsed = await detect_intent_llm(message)

    if parsed is None:
        parsed = detect_intent_keyword(message)

    intent = parsed.get("intent", "READ")
    raw_entity = parsed.get("entity", "student")
    filters = parsed.get("filters", {})
    values = parsed.get("values", {})
    aggregation = parsed.get("aggregation")
    group_by_col = parsed.get("group_by")
    limit = parsed.get("limit")

    # Resolve entity alias
    entity = ENTITY_ALIASES.get(raw_entity, raw_entity)
    if entity not in MODEL_REGISTRY:
        entity = "student"  # safe default

    # Step 2: Check access control
    allowed, deny_msg = _check_access(user_role, intent, entity)
    if not allowed:
        return {
            "intent": intent,
            "entity": MODEL_REGISTRY[entity]["display"],
            "result": None,
            "summary": deny_msg,
            "row_count": 0,
            "error": "access_denied",
        }

    # Step 3: Execute the operation
    try:
        if intent == "READ":
            return await execute_read(db, entity, filters, limit)
        elif intent == "ANALYZE":
            return await execute_analyze(db, entity, filters, aggregation, group_by_col)
        elif intent == "CREATE":
            return await execute_create(db, entity, values)
        elif intent == "UPDATE":
            rules = ACCESS_RULES.get(user_role, {})
            self_only = rules.get("self_update_only", False)
            return await execute_update(db, entity, filters, values, user_id, self_only)
        elif intent == "DELETE":
            return await execute_delete(db, entity, filters)
        else:
            return await execute_read(db, entity, filters, limit)

    except Exception as e:
        return {
            "intent": intent,
            "entity": MODEL_REGISTRY[entity]["display"],
            "result": None,
            "summary": f"❌ An error occurred while processing your query: {str(e)}",
            "row_count": 0,
            "error": str(e),
        }
