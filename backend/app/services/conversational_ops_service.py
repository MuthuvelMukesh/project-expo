"""
Conversational Operational AI – CampusIQ
Direct execution pipeline: parse → permission → execute → audit.
No approval gates. No confirmation prompts. No 2FA.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone, date as date_type, time as time_type
from typing import Any, Optional

logger = logging.getLogger(__name__)

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import (
    Attendance,
    Course,
    Department,
    Employee,
    Faculty,
    ImmutableAuditLog,
    OperationalExecution,
    OperationalPlan,
    Invoice,
    Payment,
    Prediction,
    SalaryRecord,
    Student,
    StudentFees,
    User,
)
from app.services.gemini_pool_service import GeminiClient, GeminiError

# ── Constants ──────────────────────────────────────────────────

ALLOWED_INTENTS = {"READ", "CREATE", "UPDATE", "DELETE", "ANALYZE"}

ENTITY_REGISTRY: dict[str, dict[str, Any]] = {
    "student": {"model": Student, "fields": ["roll_number", "semester", "section", "cgpa", "admission_year"], "module": "nlp"},
    "faculty": {"model": Faculty, "fields": ["employee_id", "designation", "department_id"], "module": "hr"},
    "course": {"model": Course, "fields": ["code", "name", "semester", "credits", "department_id"], "module": "nlp"},
    "department": {"model": Department, "fields": ["name", "code"], "module": "nlp"},
    "attendance": {"model": Attendance, "fields": ["date", "is_present", "method", "student_id", "course_id"], "module": "nlp"},
    "prediction": {"model": Prediction, "fields": ["predicted_grade", "risk_score", "confidence", "student_id", "course_id"], "module": "predictions"},
    "student_fee": {"model": StudentFees, "fields": ["student_id", "fee_type", "amount", "due_date", "semester", "academic_year", "is_paid"], "module": "finance"},
    "invoice": {"model": Invoice, "fields": ["student_id", "invoice_number", "amount_due", "status", "description"], "module": "finance"},
    "payment": {"model": Payment, "fields": ["student_id", "amount", "payment_method", "reference_number", "status", "notes"], "module": "finance"},
    "employee": {"model": Employee, "fields": ["employee_type", "date_of_joining", "phone", "city", "state"], "module": "hr"},
    "salary_record": {"model": SalaryRecord, "fields": ["employee_id", "month", "year", "gross_salary", "deductions", "net_salary", "status"], "module": "hr"},
}

ENTITY_ALIASES = {
    "students": "student",
    "facultys": "faculty",
    "teachers": "faculty",
    "teacher": "faculty",
    "professor": "faculty",
    "professors": "faculty",
    "staff": "faculty",
    "courses": "course",
    "departments": "department",
    "attendances": "attendance",
    "predictions": "prediction",
    "fees": "student_fee",
    "fee": "student_fee",
    "salary": "salary_record",
    "salaries": "salary_record",
    "employees": "employee",
    "invoices": "invoice",
    "payments": "payment",
}

ROLE_MATRIX = {
    "student": {
        "READ": {"student", "course", "department", "attendance", "prediction"},
        "ANALYZE": {"attendance", "prediction"},
        "CREATE": set(),
        "UPDATE": {"student"},
        "DELETE": set(),
    },
    "faculty": {
        "READ": {"student", "course", "department", "attendance", "prediction"},
        "ANALYZE": {"student", "course", "attendance", "prediction"},
        "CREATE": {"attendance", "prediction"},
        "UPDATE": {"student", "attendance", "course", "prediction"},
        "DELETE": {"attendance"},
    },
    "admin": {
        "READ": set(ENTITY_REGISTRY.keys()),
        "ANALYZE": set(ENTITY_REGISTRY.keys()),
        "CREATE": set(ENTITY_REGISTRY.keys()),
        "UPDATE": set(ENTITY_REGISTRY.keys()),
        "DELETE": set(ENTITY_REGISTRY.keys()),
    },
}

# ── Field validation rules ─────────────────────────────────────

FIELD_RULES: dict[str, dict[str, Any]] = {
    "semester": {"type": int, "min": 1, "max": 8},
    "cgpa": {"type": float, "min": 0.0, "max": 10.0},
    "credits": {"type": int, "min": 1, "max": 6},
    "amount": {"type": float, "min": 0.0},
    "amount_due": {"type": float, "min": 0.0},
    "is_present": {"type": bool},
    "is_paid": {"type": bool},
    "risk_score": {"type": float, "min": 0.0, "max": 1.0},
    "confidence": {"type": float, "min": 0.0, "max": 1.0},
    "gross_salary": {"type": float, "min": 0.0},
    "deductions": {"type": float, "min": 0.0},
    "net_salary": {"type": float, "min": 0.0},
    "month": {"type": int, "min": 1, "max": 12},
    "year": {"type": int, "min": 2000, "max": 2100},
    "admission_year": {"type": int, "min": 2000, "max": 2100},
    "department_id": {"type": int, "min": 1},
    "student_id": {"type": int, "min": 1},
    "course_id": {"type": int, "min": 1},
    "employee_id": {"type": str},
}


# ── Helpers ────────────────────────────────────────────────────

def _now() -> datetime:
    """Return a timezone-naive UTC datetime (matches DB column type)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _json_extract(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _normalize_entity(raw_entity: str) -> str:
    entity = (raw_entity or "").strip().lower()
    entity = ENTITY_ALIASES.get(entity, entity)
    return entity if entity in ENTITY_REGISTRY else "student"


def _model_to_dict(instance, include_id: bool = True) -> dict:
    data = {}
    for column in instance.__table__.columns:
        if not include_id and column.name == "id":
            continue
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        elif isinstance(value, date_type):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data


def _validate_field_values(values: dict) -> tuple[dict, list[str]]:
    """Validate and coerce values against FIELD_RULES. Returns (clean_values, errors)."""
    clean: dict[str, Any] = {}
    errors: list[str] = []
    for key, val in values.items():
        rule = FIELD_RULES.get(key)
        if not rule:
            clean[key] = val
            continue
        try:
            coerced = rule["type"](val)
        except (ValueError, TypeError):
            errors.append(f"{key}: expected {rule['type'].__name__}")
            continue
        if "min" in rule and coerced < rule["min"]:
            errors.append(f"{key}: must be >= {rule['min']}")
            continue
        if "max" in rule and coerced > rule["max"]:
            errors.append(f"{key}: must be <= {rule['max']}")
            continue
        clean[key] = coerced
    return clean, errors


def _human_summary(intent: str, entity: str, count: int) -> str:
    """Generate a short human-readable summary of what was done."""
    label = entity.replace("_", " ")
    if intent == "READ":
        return f"Found {count} {label} record{'s' if count != 1 else ''}."
    if intent == "ANALYZE":
        return f"Analyzed {count} {label} record{'s' if count != 1 else ''}."
    if intent == "CREATE":
        return f"Created {count} new {label} record{'s' if count != 1 else ''}."
    if intent == "UPDATE":
        return f"Updated {count} {label} record{'s' if count != 1 else ''}."
    if intent == "DELETE":
        return f"Deleted {count} {label} record{'s' if count != 1 else ''}."
    return f"Completed {intent} on {count} {label} record{'s' if count != 1 else ''}."


# ── Intent extraction ─────────────────────────────────────────

def _keyword_intent(message: str) -> dict:
    msg = message.lower().strip()
    intent = "READ"
    if any(token in msg for token in ["create", "add", "insert", "register", "new"]):
        intent = "CREATE"
    elif any(token in msg for token in ["update", "modify", "change", "set"]):
        intent = "UPDATE"
    elif any(token in msg for token in ["delete", "remove", "erase"]):
        intent = "DELETE"
    elif any(token in msg for token in ["analyze", "analysis", "count", "average", "sum", "total", "trend"]):
        intent = "ANALYZE"

    entity = "student"
    for k, v in {**{k: k for k in ENTITY_REGISTRY.keys()}, **ENTITY_ALIASES}.items():
        if k in msg:
            entity = v
            break

    filters: dict[str, Any] = {}
    values: dict[str, Any] = {}

    dept_match = re.search(r"department\s+([a-zA-Z\s]+)$", msg)
    if dept_match:
        filters["department"] = dept_match.group(1).strip()

    sem_match = re.search(r"semester\s+(\d+)", msg)
    if sem_match:
        filters["semester"] = int(sem_match.group(1))

    cgpa_below = re.search(r"cgpa\s+(?:below|less than|under|<)\s+([\d.]+)", msg)
    cgpa_above = re.search(r"cgpa\s+(?:above|greater than|over|>)\s+([\d.]+)", msg)
    cgpa_equals = re.search(r"cgpa\s*(?:to|=|equals?|is)\s*([\d.]+)", msg)

    if cgpa_below and intent == "READ":
        filters["cgpa__lt"] = float(cgpa_below.group(1))
    elif cgpa_above and intent == "READ":
        filters["cgpa__gt"] = float(cgpa_above.group(1))
    elif cgpa_equals:
        if intent == "READ":
            filters["cgpa"] = float(cgpa_equals.group(1))
        else:
            values["cgpa"] = float(cgpa_equals.group(1))

    confidence = 0.78
    ambiguity = []
    if intent in {"UPDATE", "DELETE"} and not filters:
        ambiguity.append("scope")
        confidence -= 0.2
    if intent in {"CREATE", "UPDATE"} and not values:
        ambiguity.append("affected_fields")
        confidence -= 0.2
    # Boost confidence if we found specific filters
    if filters:
        confidence = min(0.95, confidence + 0.05)

    return {
        "intent": intent,
        "entity": entity,
        "filters": filters,
        "scope": {},
        "affected_fields": list(values.keys()),
        "values": values,
        "confidence": max(0.1, min(0.99, confidence)),
        "ambiguity": {
            "is_ambiguous": bool(ambiguity),
            "fields": ambiguity,
            "question": "Please provide missing scope and/or values." if ambiguity else None,
        },
    }


async def _extract_intent(message: str, module: str) -> tuple[dict, Optional[dict]]:
    prompt = f"""
Extract a strict JSON object for ERP operations from this user message.

Available entities (use singular): student, faculty, course, department, attendance, prediction, student_fee, invoice, payment, employee, salary_record

Entity fields:
- student: roll_number, semester (1-8), section, cgpa (0-10), admission_year, department_id
- faculty: employee_id, designation, department_id
- course: code, name, semester, credits, department_id
- attendance: date, is_present, method, student_id, course_id
- prediction: predicted_grade, risk_score, confidence, student_id, course_id
- student_fee: student_id, fee_type, amount, due_date, semester, academic_year, is_paid
- invoice: student_id, invoice_number, amount_due, status, description
- payment: student_id, amount, payment_method, reference_number, status, notes
- employee: employee_type, date_of_joining, phone, city, state
- salary_record: employee_id, month, year, gross_salary, deductions, net_salary, status

Return keys exactly:
intent: READ|CREATE|UPDATE|DELETE|ANALYZE
entity: one of the entity names above (singular lowercase)
filters: object (for numeric comparisons use field__lt, field__lte, field__gt, field__gte, field__eq suffixes. Examples: {{"cgpa__lt": 7.0}}, {{"semester__gte": 4}})
scope: object
affected_fields: array of strings
values: object (field values for CREATE/UPDATE)
confidence: float between 0 and 1
ambiguity: {{is_ambiguous: boolean, fields: array[string], question: string|null}}

If the entity is "attendance" but the user mentions "semester", use filter {{"semester__eq": N}} — the system will join to the student table.

Message: {message}
"""
    try:
        parsed = await GeminiClient.ask_json(prompt=prompt)
        if parsed:
            parsed["intent"] = str(parsed.get("intent", "READ")).upper()
            if parsed["intent"] not in ALLOWED_INTENTS:
                parsed["intent"] = "READ"
            parsed["entity"] = _normalize_entity(str(parsed.get("entity", "student")))
            parsed["filters"] = parsed.get("filters") or {}
            parsed["scope"] = parsed.get("scope") or {}
            parsed["affected_fields"] = parsed.get("affected_fields") or list((parsed.get("values") or {}).keys())
            parsed["values"] = parsed.get("values") or {}
            conf = parsed.get("confidence", 0.6)
            # Ensure LLM-parsed results always have reasonable confidence
            parsed["confidence"] = max(0.65, min(0.99, float(conf)))
            parsed["ambiguity"] = parsed.get("ambiguity") or {"is_ambiguous": False, "fields": []}
            return parsed, None
    except (GeminiError, ValueError) as e:
        logger.warning(f"LLM intent extraction failed, using keyword fallback: {e}")

    return _keyword_intent(message), None


# ── Authorization ──────────────────────────────────────────────

async def _user_department_scope(db: AsyncSession, user: User) -> Optional[int]:
    if user.role.value == "student":
        row = await db.execute(select(Student.department_id).where(Student.user_id == user.id))
        return row.scalar_one_or_none()
    if user.role.value == "faculty":
        row = await db.execute(select(Faculty.department_id).where(Faculty.user_id == user.id))
        return row.scalar_one_or_none()
    return None


async def _resolve_department_filter(db: AsyncSession, filters: dict) -> Optional[int]:
    if "department_id" in filters:
        try:
            return int(filters["department_id"])
        except Exception:
            return None
    dep_name = filters.get("department")
    if not dep_name:
        return None
    row = await db.execute(
        select(Department.id).where(func.lower(Department.name).like(f"%{str(dep_name).lower()}%"))
    )
    return row.scalar_one_or_none()


def _is_allowed(role: str, intent: str, entity: str) -> bool:
    matrix = ROLE_MATRIX.get(role, ROLE_MATRIX["student"])
    return entity in matrix.get(intent, set())


async def _permission_gate(
    db: AsyncSession, user: User, intent: str, entity: str, filters: dict
) -> tuple[bool, str]:
    """Check permissions. Returns (allowed, reason)."""
    if not _is_allowed(user.role.value, intent, entity):
        return False, "ROLE_RESTRICTED"

    user_dept = await _user_department_scope(db, user)
    target_dept = await _resolve_department_filter(db, filters)

    if user.role.value in {"student", "faculty"} and target_dept and user_dept and target_dept != user_dept:
        return False, "DEPARTMENT_SCOPE_RESTRICTED"

    if user.role.value == "student" and intent in {"UPDATE", "DELETE", "CREATE"}:
        return False, "STUDENT_WRITE_RESTRICTED"

    return True, "OK"


# ── Risk & impact (audit only) ─────────────────────────────────

async def _estimate_impact(db: AsyncSession, entity: str, filters: dict) -> int:
    model = ENTITY_REGISTRY[entity]["model"]
    stmt = select(func.count()).select_from(model)
    stmt = _apply_filters(stmt, model, entity, filters)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


def _classify_risk(intent: str, entity: str, impact_count: int, fields: list[str] = None) -> str:
    """Classify risk for audit logging. Does NOT gate execution."""
    if intent in {"READ", "ANALYZE"}:
        return "LOW"
    if intent == "DELETE":
        return "HIGH"
    if entity == "user" and intent in {"UPDATE", "CREATE"}:
        return "HIGH"
    if impact_count > settings.RISK_HIGH_IMPACT_COUNT:
        return "HIGH"
    if intent in {"UPDATE", "CREATE"}:
        return "MEDIUM"
    return "LOW"


# ── Audit ──────────────────────────────────────────────────────

async def _audit(
    db: AsyncSession,
    *,
    user_id: int,
    role: str,
    module: str,
    operation_type: str,
    event_type: str,
    risk_level: str,
    intent_payload: dict,
    plan_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    before_state: Optional[list] = None,
    after_state: Optional[list] = None,
    meta: Optional[dict] = None,
) -> None:
    record = ImmutableAuditLog(
        event_id=f"audit_{uuid.uuid4().hex[:16]}",
        plan_id=plan_id,
        execution_id=execution_id,
        user_id=user_id,
        role=role,
        module=module,
        operation_type=operation_type,
        event_type=event_type,
        risk_level=risk_level,
        intent_payload=intent_payload,
        before_state=before_state or [],
        after_state=after_state or [],
        event_metadata=meta or {},
    )
    db.add(record)
    await db.flush()


# ── Query filters ──────────────────────────────────────────────

def _apply_filters(stmt, model, entity: str, filters: dict):
    if not filters:
        return stmt

    for key, value in filters.items():
        # Parse operator suffix (e.g., cgpa__lt → field=cgpa, op=lt)
        field_name = key
        operator = None
        if "__" in key:
            field_name, operator = key.rsplit("__", 1)
            if operator not in {"lt", "lte", "gt", "gte", "eq", "ne"}:
                # Not a recognized operator, treat the whole key as field name
                field_name = key
                operator = None

        # Handle cross-entity filters (e.g., semester on attendance → join student)
        if not hasattr(model, field_name):
            # Try joining through related entity to resolve the field
            if field_name == "semester" and entity == "attendance":
                stmt = stmt.join(Student, Attendance.student_id == Student.id)
                field = Student.semester
            elif field_name == "department" and entity in {"student", "faculty", "course"}:
                if entity == "student":
                    stmt = stmt.join(Department, Student.department_id == Department.id)
                elif entity == "faculty":
                    stmt = stmt.join(Department, Faculty.department_id == Department.id)
                elif entity == "course":
                    stmt = stmt.join(Department, Course.department_id == Department.id)
                stmt = stmt.where(func.lower(Department.name).like(f"%{str(value).lower()}%"))
                continue
            else:
                # Skip unknown fields silently
                continue
        else:
            field = getattr(model, field_name)

        # Apply the operator
        if operator == "lt":
            stmt = stmt.where(field < value)
        elif operator == "lte":
            stmt = stmt.where(field <= value)
        elif operator == "gt":
            stmt = stmt.where(field > value)
        elif operator == "gte":
            stmt = stmt.where(field >= value)
        elif operator == "eq":
            stmt = stmt.where(field == value)
        elif operator == "ne":
            stmt = stmt.where(field != value)
        elif key == "id" and hasattr(model, "id"):
            stmt = stmt.where(model.id == int(value))
        else:
            stmt = stmt.where(field == value)

    return stmt


# ── Analysis builder ───────────────────────────────────────────

def _build_analysis(rows: list[dict], entity: str) -> dict:
    """Build a simple aggregation summary for ANALYZE intent."""
    count = len(rows)
    if count == 0:
        return {"count": 0, "summary": "No records found."}

    numeric_fields = {}
    for row in rows:
        for k, v in row.items():
            if isinstance(v, (int, float)) and k != "id":
                if k not in numeric_fields:
                    numeric_fields[k] = []
                numeric_fields[k].append(v)

    aggregations = {}
    for field, vals in numeric_fields.items():
        aggregations[field] = {
            "count": len(vals),
            "min": round(min(vals), 2),
            "max": round(max(vals), 2),
            "avg": round(sum(vals) / len(vals), 2),
            "sum": round(sum(vals), 2),
        }

    return {
        "count": count,
        "aggregations": aggregations,
        "sample": rows[:5],
    }


async def _db_analysis(db: AsyncSession, model, entity: str, filters: dict) -> dict:
    """Perform aggregation at the database level for better performance."""
    # Get COUNT first
    count_stmt = select(func.count()).select_from(model)
    count_stmt = _apply_filters(count_stmt, model, entity, filters)
    total_count = (await db.execute(count_stmt)).scalar() or 0

    if total_count == 0:
        return {"count": 0, "summary": "No records found.", "aggregations": {}, "sample": []}

    # Identify numeric columns for aggregation
    numeric_cols = []
    for col in model.__table__.columns:
        if col.name == "id":
            continue
        if col.type.__class__.__name__ in ("Integer", "Float", "Numeric"):
            numeric_cols.append(col)

    aggregations = {}
    if numeric_cols:
        agg_exprs = []
        for col in numeric_cols:
            agg_exprs.extend([
                func.min(col).label(f"{col.name}_min"),
                func.max(col).label(f"{col.name}_max"),
                func.avg(col).label(f"{col.name}_avg"),
                func.sum(col).label(f"{col.name}_sum"),
            ])
        agg_stmt = select(*agg_exprs).select_from(model)
        agg_stmt = _apply_filters(agg_stmt, model, entity, filters)
        agg_row = (await db.execute(agg_stmt)).one()

        for col in numeric_cols:
            min_val = getattr(agg_row, f"{col.name}_min", None)
            max_val = getattr(agg_row, f"{col.name}_max", None)
            avg_val = getattr(agg_row, f"{col.name}_avg", None)
            sum_val = getattr(agg_row, f"{col.name}_sum", None)
            if min_val is not None:
                aggregations[col.name] = {
                    "count": total_count,
                    "min": round(float(min_val), 2),
                    "max": round(float(max_val), 2),
                    "avg": round(float(avg_val), 2),
                    "sum": round(float(sum_val), 2),
                }

    # Get a small sample (5 rows) instead of loading all data
    sample_stmt = select(model)
    sample_stmt = _apply_filters(sample_stmt, model, entity, filters)
    sample_stmt = sample_stmt.limit(5)
    sample_rows = (await db.execute(sample_stmt)).scalars().all()
    sample = [_model_to_dict(r) for r in sample_rows]

    return {
        "count": total_count,
        "aggregations": aggregations,
        "sample": sample,
    }

# Max rows to return for READ operations
READ_ROW_LIMIT = 200


# ── Main entry point ──────────────────────────────────────────

async def create_and_execute(
    *,
    db: AsyncSession,
    user: User,
    message: str,
    module: str = "nlp",
) -> dict:
    """
    Single entry point: parse intent -> check permission -> execute -> audit.
    No confirmation. No approval. No 2FA.
    """
    user_id = user.id
    user_role = user.role.value

    # 1. Parse intent
    intent_payload, ai_status = await _extract_intent(message, module)

    intent = str(intent_payload.get("intent", "READ")).upper()
    entity = _normalize_entity(intent_payload.get("entity", "student"))
    filters = intent_payload.get("filters") or {}
    values = intent_payload.get("values") or {}
    affected_fields = intent_payload.get("affected_fields") or list(values.keys())
    confidence = float(intent_payload.get("confidence", 0.0))

    # 2. Low confidence -> ask for clarification (no execution)
    if confidence < settings.OPS_CONFIDENCE_THRESHOLD:
        ambiguity = intent_payload.get("ambiguity") or {}
        await _audit(
            db,
            user_id=user_id,
            role=user_role,
            module=module,
            operation_type=intent,
            event_type="clarification_needed",
            risk_level="LOW",
            intent_payload=intent_payload,
            meta={"confidence": confidence},
        )
        return {
            "status": "clarification_needed",
            "message": ambiguity.get("question") or "Could you rephrase? I'm not sure what you want.",
            "confidence": confidence,
            "parsed": {"intent": intent, "entity": entity, "filters": filters, "values": values},
        }

    # 3. Permission check
    allowed, reason = await _permission_gate(db, user, intent, entity, filters)
    if not allowed:
        await _audit(
            db,
            user_id=user_id,
            role=user_role,
            module=module,
            operation_type=intent,
            event_type="permission_denied",
            risk_level="LOW",
            intent_payload=intent_payload,
            meta={"reason": reason},
        )
        return {
            "status": "denied",
            "message": f"Permission denied: {reason}",
            "intent": intent,
            "entity": entity,
        }

    # 4. Validate field values for write operations
    if values and intent in {"CREATE", "UPDATE"}:
        values, val_errors = _validate_field_values(values)
        if val_errors:
            return {
                "status": "validation_error",
                "message": "Some field values are invalid.",
                "errors": val_errors,
                "parsed": {"intent": intent, "entity": entity, "filters": filters, "values": values},
            }

    # 5. Impact & risk (for audit only — does NOT gate execution)
    impact = await _estimate_impact(db, entity, filters)
    risk = _classify_risk(intent, entity, impact, affected_fields)

    # 6. Create plan record (for tracking & rollback)
    plan_id = f"ops_{uuid.uuid4().hex[:12]}"
    plan = OperationalPlan(
        plan_id=plan_id,
        user_id=user_id,
        module=module,
        message=message,
        intent_type=intent,
        entity=entity,
        filters=filters,
        scope=intent_payload.get("scope") or {},
        affected_fields=affected_fields,
        values=values,
        confidence=confidence,
        ambiguity=intent_payload.get("ambiguity") or {},
        risk_level=risk,
        estimated_impact_count=impact,
        status="executing",
        requires_confirmation=False,
        requires_senior_approval=False,
        requires_2fa=False,
        escalation_required=False,
        preview={},
        rollback_plan={"strategy": "before_state_snapshot", "supports_rollback": intent in {"CREATE", "UPDATE", "DELETE"}},
    )
    db.add(plan)
    await db.flush()

    # 7. Create execution record
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    execution = OperationalExecution(
        execution_id=execution_id,
        plan_id=plan_id,
        executed_by=user_id,
        status="pending",
    )
    db.add(execution)
    await db.flush()

    # 8. Execute the operation
    model = ENTITY_REGISTRY[entity]["model"]
    before_state: list[dict] = []
    after_state: list[dict] = []

    try:
        analysis = None

        if intent == "ANALYZE":
            # Use database-level aggregation — no need to load all rows
            analysis = await _db_analysis(db, model, entity, filters)
            before_state = analysis.get("sample", [])
            after_state = before_state

        elif intent == "READ":
            # Get total count first, then fetch limited rows
            count_stmt = select(func.count()).select_from(model)
            count_stmt = _apply_filters(count_stmt, model, entity, filters)
            total_count = (await db.execute(count_stmt)).scalar() or 0

            stmt = select(model)
            stmt = _apply_filters(stmt, model, entity, filters)
            stmt = stmt.limit(READ_ROW_LIMIT)
            rows = (await db.execute(stmt)).scalars().all()
            before_state = [_model_to_dict(row) for row in rows]
            after_state = before_state

            # If results were truncated, note it in the summary
            if total_count > READ_ROW_LIMIT:
                impact = total_count  # override for accurate message

        else:
            # For CREATE/UPDATE/DELETE: fetch matching rows for before_state
            stmt = select(model)
            stmt = _apply_filters(stmt, model, entity, filters)
            rows = (await db.execute(stmt)).scalars().all()
            before_state = [_model_to_dict(row) for row in rows]

            if intent == "CREATE":
                new_obj = model(**values)
                db.add(new_obj)
                await db.flush()
                after_state = [_model_to_dict(new_obj)]

            elif intent == "UPDATE":
                for row in rows:
                    for key, value in values.items():
                        if hasattr(row, key):
                            setattr(row, key, value)
                await db.flush()
                after_state = [_model_to_dict(row) for row in rows]

            elif intent == "DELETE":
                for row in rows:
                    await db.delete(row)
                await db.flush()
                after_state = []

        # Update execution & plan records
        # For READ/ANALYZE, limit what's stored in execution state (avoid bloating DB)
        if intent in {"READ", "ANALYZE"}:
            execution.before_state = before_state[:10]  # sample only
            execution.after_state = after_state[:10]
        else:
            execution.before_state = before_state
            execution.after_state = after_state
        execution.status = "executed"
        execution.executed_at = _now()
        plan.status = "executed"
        await db.flush()

        # Auto-audit — also limit stored state for read-only operations
        if intent == "ANALYZE":
            affected_count = analysis.get("count", 0) if analysis else 0
        elif intent == "CREATE":
            affected_count = len(after_state)
        else:
            affected_count = len(before_state)

        audit_before = before_state[:10] if intent in {"READ", "ANALYZE"} else before_state
        audit_after = after_state[:10] if intent in {"READ", "ANALYZE"} else after_state
        await _audit(
            db,
            user_id=user_id,
            role=user_role,
            module=module,
            operation_type=intent,
            event_type="executed",
            risk_level=risk,
            plan_id=plan_id,
            execution_id=execution_id,
            intent_payload=intent_payload,
            before_state=audit_before,
            after_state=audit_after,
        )

        result = {
            "status": "executed",
            "plan_id": plan_id,
            "execution_id": execution_id,
            "intent": intent,
            "entity": entity,
            "risk_level": risk,
            "affected_count": affected_count,
            "before_state": before_state,
            "after_state": after_state,
            "message": _human_summary(intent, entity, affected_count),
            "confidence": confidence,
            "parsed": {"intent": intent, "entity": entity, "filters": filters, "values": values},
            "analysis": analysis,
        }
        return result

    except Exception as exc:
        await db.rollback()
        # Re-fetch plan and execution after rollback
        plan = (
            await db.execute(select(OperationalPlan).where(OperationalPlan.plan_id == plan_id))
        ).scalar_one_or_none()
        execution = (
            await db.execute(select(OperationalExecution).where(OperationalExecution.execution_id == execution_id))
        ).scalar_one_or_none()
        if plan:
            plan.status = "failed"
        if execution:
            execution.status = "failed"
            execution.failure_state = {"error": str(exc)}
        await db.flush()

        await _audit(
            db,
            user_id=user_id,
            role=user_role,
            module=module,
            operation_type=intent,
            event_type="failed",
            risk_level=risk,
            plan_id=plan_id,
            execution_id=execution_id,
            intent_payload=intent_payload,
            before_state=before_state,
            after_state=after_state,
            meta={"error": str(exc)},
        )

        return {
            "status": "failed",
            "plan_id": plan_id,
            "execution_id": execution_id,
            "intent": intent,
            "entity": entity,
            "risk_level": risk,
            "affected_count": 0,
            "before_state": before_state,
            "after_state": after_state,
            "confidence": confidence,
            "parsed": {"intent": intent, "entity": entity, "filters": filters, "values": values},
            "error": str(exc),
            "message": f"Operation failed: {str(exc)}",
        }


# ── Rollback ───────────────────────────────────────────────────

async def rollback_execution(*, db: AsyncSession, user: User, execution_id: str) -> dict:
    """Rollback a previously executed operation using before_state snapshots."""
    exec_stmt = select(OperationalExecution).where(OperationalExecution.execution_id == execution_id)
    execution = (await db.execute(exec_stmt)).scalar_one_or_none()
    if not execution:
        return {"error": "EXECUTION_NOT_FOUND"}

    plan_stmt = select(OperationalPlan).where(OperationalPlan.plan_id == execution.plan_id)
    plan = (await db.execute(plan_stmt)).scalar_one_or_none()
    if not plan:
        return {"error": "PLAN_NOT_FOUND"}

    # Only the executor or admins can rollback
    if user.role.value != "admin" and execution.executed_by != user.id:
        return {"error": "ROLLBACK_NOT_PERMITTED"}

    if execution.status != "executed":
        return {"error": f"CANNOT_ROLLBACK_STATUS:{execution.status}"}

    model = ENTITY_REGISTRY[plan.entity]["model"]

    try:
        if plan.intent_type == "CREATE":
            created_ids = [row.get("id") for row in (execution.after_state or []) if row.get("id") is not None]
            if created_ids:
                rows = (await db.execute(select(model).where(model.id.in_(created_ids)))).scalars().all()
                for row in rows:
                    await db.delete(row)

        elif plan.intent_type == "UPDATE":
            for snapshot in (execution.before_state or []):
                row_id = snapshot.get("id")
                if row_id is None:
                    continue
                row = (await db.execute(select(model).where(model.id == row_id))).scalar_one_or_none()
                if not row:
                    continue
                for key, value in snapshot.items():
                    if key == "id":
                        continue
                    if hasattr(row, key):
                        setattr(row, key, value)

        elif plan.intent_type == "DELETE":
            for snapshot in (execution.before_state or []):
                record_data = {k: v for k, v in snapshot.items() if k != "id"}
                restored = model(**record_data)
                if snapshot.get("id") is not None and hasattr(restored, "id"):
                    setattr(restored, "id", snapshot["id"])
                db.add(restored)

        else:
            return {"error": "ROLLBACK_NOT_SUPPORTED_FOR_OPERATION"}

        execution.status = "rolled_back"
        execution.rolled_back_at = _now()
        execution.rollback_state = {"rolled_back": True}
        plan.status = "rolled_back"
        await db.flush()

        await _audit(
            db,
            user_id=user.id,
            role=user.role.value,
            module=plan.module,
            operation_type=plan.intent_type,
            event_type="rollback",
            risk_level=plan.risk_level,
            plan_id=plan.plan_id,
            execution_id=execution.execution_id,
            intent_payload={"entity": plan.entity},
            before_state=execution.after_state or [],
            after_state=execution.before_state or [],
        )

        return {
            "status": "rolled_back",
            "execution_id": execution_id,
            "plan_id": plan.plan_id,
            "message": f"Rollback completed for {plan.entity} {plan.intent_type} operation.",
        }

    except Exception as exc:
        return {
            "execution_id": execution_id,
            "status": "rollback_failed",
            "error": str(exc),
        }


# ── Stats & history ────────────────────────────────────────────

async def get_ops_stats(*, db: AsyncSession, user: User) -> dict:
    """Return aggregate operation statistics."""
    today_start = datetime.combine(date_type.today(), time_type.min)

    total_plans = (await db.execute(select(func.count()).select_from(OperationalPlan))).scalar() or 0

    executed_today = (
        await db.execute(
            select(func.count())
            .select_from(OperationalExecution)
            .where(
                and_(
                    OperationalExecution.status == "executed",
                    OperationalExecution.executed_at >= today_start,
                )
            )
        )
    ).scalar() or 0

    failed_total = (
        await db.execute(
            select(func.count()).select_from(OperationalExecution).where(OperationalExecution.status == "failed")
        )
    ).scalar() or 0

    rolled_back_total = (
        await db.execute(
            select(func.count()).select_from(OperationalExecution).where(OperationalExecution.status == "rolled_back")
        )
    ).scalar() or 0

    # Risk distribution
    risk_rows = (
        await db.execute(
            select(OperationalPlan.risk_level, func.count().label("cnt"))
            .group_by(OperationalPlan.risk_level)
        )
    ).all()
    by_risk = [{"risk_level": r, "count": c} for r, c in risk_rows]

    # Module distribution
    module_rows = (
        await db.execute(
            select(
                OperationalPlan.module,
                func.count().label("total"),
                func.sum(case((OperationalPlan.status == "executed", 1), else_=0)).label("executed"),
                func.sum(case((OperationalPlan.status == "failed", 1), else_=0)).label("failed"),
                func.sum(case((OperationalPlan.status == "rolled_back", 1), else_=0)).label("rolled_back"),
            ).group_by(OperationalPlan.module)
        )
    ).all()
    by_module = [
        {"module": m, "total": t, "executed": e or 0, "failed": f or 0, "rolled_back": rb or 0}
        for m, t, e, f, rb in module_rows
    ]

    return {
        "total_plans": total_plans,
        "executed_today": executed_today,
        "failed_total": failed_total,
        "rolled_back_total": rolled_back_total,
        "by_risk": by_risk,
        "by_module": by_module,
    }


async def get_audit_history(
    *,
    db: AsyncSession,
    user: User,
    module: Optional[str] = None,
    operation_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
) -> list[dict]:
    """Return audit history. Admins see all; others see only their own."""
    stmt = select(ImmutableAuditLog)

    conditions = []
    if module:
        conditions.append(ImmutableAuditLog.module == module)
    if operation_type:
        conditions.append(ImmutableAuditLog.operation_type == operation_type.upper())
    if risk_level:
        conditions.append(ImmutableAuditLog.risk_level == risk_level.upper())
    if actor_user_id:
        conditions.append(ImmutableAuditLog.user_id == actor_user_id)
    if start_date:
        conditions.append(ImmutableAuditLog.created_at >= start_date)
    if end_date:
        conditions.append(ImmutableAuditLog.created_at <= end_date)

    if user.role.value != "admin":
        conditions.append(ImmutableAuditLog.user_id == user.id)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(ImmutableAuditLog.created_at.desc()).limit(min(limit, 500))
    rows = (await db.execute(stmt)).scalars().all()

    return [
        {
            "event_id": row.event_id,
            "plan_id": row.plan_id,
            "execution_id": row.execution_id,
            "user_id": row.user_id,
            "role": row.role,
            "module": row.module,
            "operation_type": row.operation_type,
            "event_type": row.event_type,
            "risk_level": row.risk_level,
            "intent_payload": row.intent_payload,
            "before_state": row.before_state,
            "after_state": row.after_state,
            "metadata": row.event_metadata,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]
