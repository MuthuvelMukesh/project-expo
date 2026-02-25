"""
CampusIQ — AI Copilot Service
Master orchestrator that translates natural language into multi-step action
plans with human-in-the-loop confirmation for destructive operations.
"""

import json
import re
import uuid
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.models import (
    User, UserRole, Department, Student, Faculty, Course,
    Attendance, Prediction, ActionLog,
)
from app.services.nlp_crud_service import process_nlp_crud, MODEL_REGISTRY

settings = get_settings()
log = logging.getLogger("campusiq.copilot")

# ─── Role Capability Matrix ─────────────────────────────────────
ROLE_CAPABILITIES = {
    "admin": {
        "label": "Administrator",
        "can_read": ["student", "faculty", "course", "department", "attendance", "prediction", "user"],
        "can_create": ["student", "faculty", "course", "department", "user"],
        "can_update": ["student", "faculty", "course", "department", "user"],
        "can_delete": ["student", "faculty", "course", "department"],
        "can_analyze": ["student", "faculty", "course", "department", "attendance", "prediction"],
        "special": ["view_admin_dashboard", "view_all_analytics", "manage_users"],
    },
    "faculty": {
        "label": "Faculty",
        "can_read": ["student", "course", "department", "attendance", "prediction"],
        "can_create": ["attendance"],
        "can_update": ["attendance", "course"],
        "can_delete": [],
        "can_analyze": ["student", "course", "attendance", "prediction"],
        "special": ["generate_qr", "view_risk_roster", "view_faculty_dashboard"],
    },
    "student": {
        "label": "Student",
        "can_read": ["student", "course", "department", "attendance", "prediction"],
        "can_create": [],
        "can_update": ["student"],
        "can_delete": [],
        "can_analyze": ["attendance", "prediction"],
        "special": ["view_student_dashboard", "mark_attendance", "view_own_predictions"],
    },
}

# ─── Risk Classification ────────────────────────────────────────
RISK_LEVELS = {
    "READ": "safe",
    "ANALYZE": "safe",
    "NAVIGATE": "safe",
    "CREATE": "high",
    "UPDATE": "low",
    "DELETE": "high",
}


def _classify_risk(action_type: str, entity: str, is_self: bool = False) -> str:
    """Classify the risk level of an action."""
    base_risk = RISK_LEVELS.get(action_type, "high")
    if action_type == "UPDATE" and is_self:
        return "low"
    if action_type in ("CREATE", "DELETE"):
        return "high"
    return base_risk


def _needs_confirmation(risk_level: str) -> bool:
    """Determine if an action requires human confirmation."""
    return risk_level in ("low", "high")


# ─── Action Planning via LLM ────────────────────────────────────

async def _plan_with_llm(message: str, user_role: str) -> Optional[list]:
    """Use Ollama to break a NL request into structured actions."""
    capabilities = ROLE_CAPABILITIES.get(user_role, ROLE_CAPABILITIES["student"])

    prompt = f"""You are the CampusIQ AI Copilot, a college ERP action planner.
The user is a **{capabilities['label']}** ({user_role}).

Their capabilities:
- Can READ: {', '.join(capabilities['can_read'])}
- Can CREATE: {', '.join(capabilities['can_create']) or 'nothing'}
- Can UPDATE: {', '.join(capabilities['can_update']) or 'nothing'}
- Can DELETE: {', '.join(capabilities['can_delete']) or 'nothing'}
- Special: {', '.join(capabilities['special'])}

Database entities: students, faculty, courses, departments, attendance, predictions, users.

Break the user's request into a JSON array of atomic actions. Each action:
{{
  "type": "READ" | "CREATE" | "UPDATE" | "DELETE" | "ANALYZE" | "NAVIGATE",
  "entity": "student" | "faculty" | "course" | "department" | "attendance" | "prediction" | "user" | "dashboard",
  "description": "Human-readable description of what this action does",
  "params": {{}} // relevant parameters like filters, values, names
}}

Rules:
- If the user asks something they have no capability for, return an action with type "DENIED"
- For multi-step tasks, break into individual atomic actions
- For "show my dashboard" → type "NAVIGATE", entity "dashboard"
- For "generate QR" → type "CREATE", entity "attendance", params with course info
- Keep params simple: use "name", "filters", "values", "count" etc.

User request: "{message}"

Return ONLY a valid JSON array, no other text."""

    provider = (settings.LLM_PROVIDER or "ollama").strip().lower()

    async def _parse_actions(content: str) -> Optional[list]:
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None

    async def _plan_via_google() -> Optional[list]:
        if not settings.GOOGLE_API_KEY:
            log.warning("Google provider selected but GOOGLE_API_KEY is not set.")
            return None

        endpoint = (
            f"{settings.GOOGLE_BASE_URL}/models/{settings.GOOGLE_MODEL}:generateContent"
            f"?key={settings.GOOGLE_API_KEY}"
        )
        payload = {
            "systemInstruction": {
                "parts": [{"text": "You are a precise JSON-only action planner. Return only valid JSON arrays."}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {"temperature": 0.1},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload)

        if response.status_code != 200:
            log.error("Google planner HTTP %s — %s", response.status_code, response.text[:200])
            return None

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        content = "".join(p.get("text", "") for p in parts)
        return await _parse_actions(content)

    async def _plan_via_ollama() -> Optional[list]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a precise JSON-only action planner. Return only valid JSON arrays."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1},
                },
            )

        if response.status_code != 200:
            return None

        data = response.json()
        content = data.get("message", {}).get("content", "")
        return await _parse_actions(content)

    try:
        if provider == "google":
            actions = await _plan_via_google()
            if actions is not None:
                return actions
            log.info("Falling back to Ollama planner after Google LLM failure.")

        actions = await _plan_via_ollama()
        if actions is not None:
            return actions

    except httpx.ConnectError:
        log.info("LLM provider not reachable for copilot action planning — using keyword fallback.")
    except httpx.TimeoutException:
        log.warning("LLM provider timed out during copilot action planning.")
    except json.JSONDecodeError as e:
        log.warning("Copilot LLM returned invalid JSON: %s", e)
    except Exception as e:
        log.error("Unexpected error in copilot _plan_with_llm: %s", e, exc_info=True)

    return None


def _plan_with_keywords(message: str, user_role: str) -> list:
    """Keyword-based fallback for action planning."""
    msg = message.lower().strip()
    capabilities = ROLE_CAPABILITIES.get(user_role, ROLE_CAPABILITIES["student"])
    actions = []

    # Detect dashboard/navigation requests
    if any(w in msg for w in ["dashboard", "home", "overview", "my page"]):
        actions.append({
            "type": "NAVIGATE",
            "entity": "dashboard",
            "description": f"Open your {user_role} dashboard",
            "params": {"page": f"{user_role}_dashboard"},
        })
        return actions

    # Detect QR generation
    if any(w in msg for w in ["generate qr", "qr code", "create qr"]):
        course_match = re.search(r'(?:for|in)\s+(?:my\s+)?(.+?)(?:\s+class|\s+course|$)', msg, re.IGNORECASE)
        course_name = course_match.group(1).strip() if course_match else "unknown"
        actions.append({
            "type": "CREATE",
            "entity": "attendance",
            "description": f"Generate QR code for attendance in {course_name}",
            "params": {"course_name": course_name, "operation": "generate_qr"},
        })
        return actions

    # Detect mark attendance
    if any(w in msg for w in ["mark attendance", "scan qr", "mark my attendance"]):
        actions.append({
            "type": "UPDATE",
            "entity": "attendance",
            "description": "Mark your attendance",
            "params": {"operation": "mark_attendance"},
        })
        return actions

    # Detect risk roster
    if any(w in msg for w in ["risk roster", "at-risk students", "risk list"]):
        course_match = re.search(r'(?:for|in)\s+(.+?)(?:\s+course|\s+class|$)', msg, re.IGNORECASE)
        course_name = course_match.group(1).strip() if course_match else "all"
        actions.append({
            "type": "READ",
            "entity": "prediction",
            "description": f"View risk roster for {course_name}",
            "params": {"operation": "risk_roster", "course_name": course_name},
        })
        return actions

    # Detect batch/multiple operations: "register 3 students"
    count_match = re.search(r'(\d+)\s+(?:new\s+)?(\w+)', msg)
    if count_match and any(w in msg for w in ["register", "add", "create", "insert", "enroll"]):
        count = int(count_match.group(1))
        entity_raw = count_match.group(2).rstrip('s')  # "students" → "student"
        entity = entity_raw if entity_raw in MODEL_REGISTRY else "student"

        dept_match = re.search(r'(?:in|for|to)\s+(?:the\s+)?(.+?)(?:\s+department|\s+dept|$)', msg, re.IGNORECASE)
        dept_name = dept_match.group(1).strip() if dept_match else None

        for i in range(min(count, 10)):  # Cap at 10
            params = {"index": i + 1}
            if dept_name:
                params["department"] = dept_name
            actions.append({
                "type": "CREATE",
                "entity": entity,
                "description": f"Create {entity} #{i+1}" + (f" in {dept_name}" if dept_name else ""),
                "params": params,
            })
        return actions

    # Detect show/view/list queries (single)
    if any(w in msg for w in ["show", "list", "get", "fetch", "view", "display", "find"]):
        entity = _detect_entity(msg)
        filters = _extract_filters(msg)
        actions.append({
            "type": "READ",
            "entity": entity,
            "description": f"Fetch {entity} data" + (f" with filters: {filters}" if filters else ""),
            "params": {"filters": filters},
        })
        return actions

    # Detect analytics
    if any(w in msg for w in ["how many", "count", "average", "total", "analyze", "statistics",
                                "compare", "top", "highest", "lowest", "distribution"]):
        entity = _detect_entity(msg)
        actions.append({
            "type": "ANALYZE",
            "entity": entity,
            "description": f"Analyze {entity} data",
            "params": {"query": msg},
        })
        return actions

    # Detect update (self or general)
    if any(w in msg for w in ["update", "change", "modify", "set", "edit", "fill", "enter"]):
        entity = _detect_entity(msg)
        values = _extract_values(msg)
        is_self = any(w in msg for w in ["my", "mine", "self", "own"])
        actions.append({
            "type": "UPDATE",
            "entity": entity,
            "description": f"Update {'your' if is_self else ''} {entity} record",
            "params": {"values": values, "self_update": is_self},
        })
        return actions

    # Detect delete
    if any(w in msg for w in ["delete", "remove", "drop", "erase"]):
        entity = _detect_entity(msg)
        filters = _extract_filters(msg)
        actions.append({
            "type": "DELETE",
            "entity": entity,
            "description": f"Delete {entity} records matching: {filters}",
            "params": {"filters": filters},
        })
        return actions

    # Detect single create
    if any(w in msg for w in ["add", "create", "new", "register", "insert"]):
        entity = _detect_entity(msg)
        values = _extract_values(msg)
        actions.append({
            "type": "CREATE",
            "entity": entity,
            "description": f"Create a new {entity} record",
            "params": {"values": values},
        })
        return actions

    # Fallback: treat as a read
    entity = _detect_entity(msg)
    actions.append({
        "type": "READ",
        "entity": entity,
        "description": f"Look up {entity} information",
        "params": {"query": msg},
    })
    return actions


def _detect_entity(msg: str) -> str:
    """Detect the target entity from a message."""
    entity_map = {
        "student": ["student", "students", "learner", "roll"],
        "faculty": ["faculty", "teacher", "professor", "instructor"],
        "course": ["course", "courses", "subject", "subjects", "class"],
        "department": ["department", "dept", "branch"],
        "attendance": ["attendance", "present", "absent", "qr"],
        "prediction": ["prediction", "grade", "risk", "score"],
        "user": ["user", "users", "account"],
    }
    for entity, keywords in entity_map.items():
        if any(kw in msg for kw in keywords):
            return entity
    return "student"


def _extract_filters(msg: str) -> dict:
    """Extract simple filters from a message."""
    filters = {}
    dept_match = re.search(r'(?:in|from|of|for)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:department|dept|branch)?', msg, re.IGNORECASE)
    if dept_match:
        filters["department"] = dept_match.group(1).strip()
    sem_match = re.search(r'semester\s+(\d+)', msg, re.IGNORECASE)
    if sem_match:
        filters["semester"] = int(sem_match.group(1))
    return filters


def _extract_values(msg: str) -> dict:
    """Extract values for create/update from a message."""
    values = {}
    name_match = re.search(r'(?:called|named|name)\s+["\']?([^"\']+?)["\']?(?:\s+with|\s+in|\s+for|$)', msg, re.IGNORECASE)
    if name_match:
        values["name"] = name_match.group(1).strip()
    code_match = re.search(r'(?:code|id)\s+["\']?([A-Z0-9]+)["\']?', msg, re.IGNORECASE)
    if code_match:
        values["code"] = code_match.group(1).strip()
    sem_match = re.search(r'semester\s+(?:to\s+)?(\d+)', msg, re.IGNORECASE)
    if sem_match:
        values["semester"] = int(sem_match.group(1))
    cgpa_match = re.search(r'cgpa\s+(?:to\s+)?([\d.]+)', msg, re.IGNORECASE)
    if cgpa_match:
        values["cgpa"] = float(cgpa_match.group(1))
    section_match = re.search(r'section\s+(?:to\s+)?([A-Z])', msg, re.IGNORECASE)
    if section_match:
        values["section"] = section_match.group(1).upper()
    return values


# ─── Access Control ──────────────────────────────────────────────

def _check_capability(user_role: str, action_type: str, entity: str) -> tuple:
    """Check if the user role can perform the action. Returns (allowed, reason)."""
    caps = ROLE_CAPABILITIES.get(user_role, ROLE_CAPABILITIES["student"])

    type_map = {
        "READ": "can_read",
        "ANALYZE": "can_analyze",
        "CREATE": "can_create",
        "UPDATE": "can_update",
        "DELETE": "can_delete",
        "NAVIGATE": None,
    }

    cap_key = type_map.get(action_type)
    if cap_key is None:
        return True, ""

    allowed_entities = caps.get(cap_key, [])
    if entity in allowed_entities:
        return True, ""

    return False, f"As a {caps['label']}, you cannot {action_type} {entity} records."


# ─── Main Entry Points ──────────────────────────────────────────

async def create_plan(
    message: str,
    user_role: str,
    user_id: int,
    db: AsyncSession,
) -> dict:
    """
    Create an action plan from a natural language request.
    Safe actions are auto-executed. Dangerous ones need confirmation.
    """
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"

    # Step 1: Generate action list
    raw_actions = await _plan_with_llm(message, user_role)
    if raw_actions is None:
        raw_actions = _plan_with_keywords(message, user_role)

    # Step 2: Enrich each action with risk + capability check
    actions = []
    auto_executed_results = []
    needs_confirm = False

    for i, raw in enumerate(raw_actions):
        action_type = raw.get("type", "READ")
        entity = raw.get("entity", "student")
        description = raw.get("description", "Unknown action")
        params = raw.get("params", {})

        # Check capability
        allowed, deny_reason = _check_capability(user_role, action_type, entity)
        if not allowed:
            actions.append({
                "action_id": f"{plan_id}_act_{i}",
                "type": "DENIED",
                "entity": entity,
                "description": f"❌ {deny_reason}",
                "risk_level": "high",
                "requires_confirmation": False,
                "params": params,
            })
            continue

        # Classify risk
        is_self = params.get("self_update", False)
        risk = _classify_risk(action_type, entity, is_self)
        confirm = _needs_confirmation(risk)

        action_obj = {
            "action_id": f"{plan_id}_act_{i}",
            "type": action_type,
            "entity": entity,
            "description": description,
            "risk_level": risk,
            "requires_confirmation": confirm,
            "params": params,
        }

        # Auto-execute safe actions immediately
        if not confirm:
            try:
                exec_result = await _execute_single_action(
                    db, action_type, entity, params, user_id, user_role, message
                )
                auto_executed_results.append({
                    "action_id": action_obj["action_id"],
                    "description": description,
                    "status": "executed",
                    "result": _safe_result(exec_result),
                })

                # Log to audit trail
                log = ActionLog(
                    user_id=user_id,
                    plan_id=plan_id,
                    action_id=action_obj["action_id"],
                    action_type=action_type,
                    entity=entity,
                    description=description,
                    risk_level=risk,
                    status="executed",
                    payload=params,
                    result=_safe_result(exec_result),
                    executed_at=datetime.now(timezone.utc),
                )
                db.add(log)
            except Exception as e:
                auto_executed_results.append({
                    "action_id": action_obj["action_id"],
                    "description": description,
                    "status": "failed",
                    "error": str(e),
                })
        else:
            needs_confirm = True
            actions.append(action_obj)

            # Log as pending
            log = ActionLog(
                user_id=user_id,
                plan_id=plan_id,
                action_id=action_obj["action_id"],
                action_type=action_type,
                entity=entity,
                description=description,
                risk_level=risk,
                status="pending",
                payload=params,
            )
            db.add(log)

    await db.flush()

    # Build summary
    total = len(raw_actions)
    auto_count = len(auto_executed_results)
    pending_count = len(actions)
    denied_count = sum(1 for a in actions if a["type"] == "DENIED")

    summary_parts = []
    if auto_count > 0:
        summary_parts.append(f"✅ **{auto_count}** action(s) executed automatically")
    if pending_count - denied_count > 0:
        summary_parts.append(f"⏳ **{pending_count - denied_count}** action(s) need your approval")
    if denied_count > 0:
        summary_parts.append(f"❌ **{denied_count}** action(s) denied (insufficient permissions)")

    summary = " · ".join(summary_parts) if summary_parts else "No actions generated."

    return {
        "plan_id": plan_id,
        "message": message,
        "actions": actions,
        "summary": summary,
        "requires_confirmation": needs_confirm,
        "auto_executed": auto_executed_results if auto_executed_results else None,
    }


async def execute_plan(
    plan_id: str,
    approved_ids: list,
    rejected_ids: list,
    user_id: int,
    user_role: str,
    db: AsyncSession,
) -> dict:
    """Execute confirmed actions and reject others."""
    results = []
    executed = 0
    failed = 0
    rejected = 0

    # Get pending actions from DB
    stmt = select(ActionLog).where(
        ActionLog.plan_id == plan_id,
        ActionLog.user_id == user_id,
        ActionLog.status == "pending",
    )
    result = await db.execute(stmt)
    pending_logs = result.scalars().all()

    # Build lookup sets for fast matching
    rejected_set = set(rejected_ids)
    approved_set = set(approved_ids)

    for log in pending_logs:
        log_action_id = log.action_id or ""

        # Check if this action was explicitly rejected
        if log_action_id in rejected_set:
            log.status = "rejected"
            rejected += 1
            results.append({
                "action_id": log_action_id,
                "description": log.description,
                "status": "rejected",
            })
            continue

        # If approved list is empty and not in rejected → reject (reject-all case)
        if not approved_set and not rejected_set:
            log.status = "rejected"
            rejected += 1
            results.append({
                "action_id": log_action_id,
                "description": log.description,
                "status": "rejected",
            })
            continue

        # If approved list given but action not in it → reject
        if approved_set and log_action_id not in approved_set:
            log.status = "rejected"
            rejected += 1
            results.append({
                "action_id": log_action_id,
                "description": log.description,
                "status": "rejected",
            })
            continue

        # Execute the action
        try:
            exec_result = await _execute_single_action(
                db, log.action_type, log.entity, log.payload or {},
                user_id, user_role, ""
            )
            log.status = "executed"
            log.result = _safe_result(exec_result)
            log.executed_at = datetime.utcnow()
            executed += 1
            results.append({
                "action_id": log_action_id,
                "description": log.description,
                "status": "executed",
                "result": _safe_result(exec_result),
            })
        except Exception as e:
            log.status = "failed"
            log.result = {"error": str(e)}
            failed += 1
            results.append({
                "action_id": log_action_id,
                "description": log.description,
                "status": "failed",
                "error": str(e),
            })

    await db.flush()

    summary_parts = []
    if executed > 0:
        summary_parts.append(f"✅ **{executed}** action(s) executed successfully")
    if failed > 0:
        summary_parts.append(f"❌ **{failed}** action(s) failed")
    if rejected > 0:
        summary_parts.append(f"🚫 **{rejected}** action(s) rejected")

    return {
        "plan_id": plan_id,
        "actions_executed": executed,
        "actions_failed": failed,
        "actions_rejected": rejected,
        "results": results,
        "summary": " · ".join(summary_parts) if summary_parts else "No actions to process.",
    }


async def get_history(user_id: int, db: AsyncSession, limit: int = 50) -> list:
    """Get copilot action history for a user."""
    stmt = (
        select(ActionLog)
        .where(ActionLog.user_id == user_id)
        .order_by(ActionLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "plan_id": log.plan_id,
            "action_type": log.action_type,
            "entity": log.entity,
            "description": log.description,
            "risk_level": log.risk_level,
            "status": log.status,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "executed_at": log.executed_at.isoformat() if log.executed_at else None,
        }
        for log in logs
    ]


# ─── Single Action Executor ─────────────────────────────────────


def _safe_result(result) -> dict:
    """Ensure result is JSON-serializable for storage in ActionLog."""
    if not isinstance(result, dict):
        return {"raw": str(result)}
    safe = {}
    for key, val in result.items():
        try:
            json.dumps(val)
            safe[key] = val
        except (TypeError, ValueError):
            safe[key] = str(val)
    return safe


async def _execute_single_action(
    db: AsyncSession,
    action_type: str,
    entity: str,
    params: dict,
    user_id: int,
    user_role: str,
    original_message: str,
) -> dict:
    """Execute a single atomic action using the NLP CRUD engine or special handlers."""

    # Handle special operations
    operation = params.get("operation")

    if operation == "generate_qr":
        return await _handle_generate_qr(db, params, user_id)

    if operation == "risk_roster":
        return await _handle_risk_roster(db, params)

    if entity == "dashboard" or action_type == "NAVIGATE":
        return {"navigated_to": params.get("page", "dashboard"), "status": "ok"}

    # Delegate to NLP CRUD engine for standard CRUD
    query = original_message or _build_query_from_params(action_type, entity, params)
    result = await process_nlp_crud(
        message=query,
        user_role=user_role,
        user_id=user_id,
        db=db,
    )
    return result


def _build_query_from_params(action_type: str, entity: str, params: dict) -> str:
    """Build a natural language query from structured params."""
    filters = params.get("filters", {})
    values = params.get("values", {})

    if action_type == "READ":
        query = f"Show all {entity}s"
        if filters.get("department"):
            query += f" in {filters['department']} department"
        if filters.get("semester"):
            query += f" in semester {filters['semester']}"
        return query

    if action_type == "ANALYZE":
        return params.get("query", f"Analyze {entity} data")

    if action_type == "CREATE":
        query = f"Create a new {entity}"
        if values.get("name"):
            query += f" called {values['name']}"
        if values.get("code"):
            query += f" with code {values['code']}"
        if filters.get("department") or values.get("department"):
            dept = filters.get("department") or values.get("department")
            query += f" in {dept} department"
        return query

    if action_type == "UPDATE":
        query = f"Update {entity}"
        for key, val in values.items():
            query += f" {key} to {val}"
        return query

    if action_type == "DELETE":
        query = f"Delete {entity}"
        for key, val in filters.items():
            query += f" with {key} {val}"
        return query

    return f"{action_type} {entity}"


async def _handle_generate_qr(db: AsyncSession, params: dict, user_id: int) -> dict:
    """Handle QR code generation for attendance."""
    course_name = params.get("course_name", "")

    # Find the course
    stmt = select(Course).where(func.lower(Course.name).like(f"%{course_name.lower()}%"))
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    if not course:
        return {"status": "error", "message": f"Course '{course_name}' not found"}

    # Import QR generation service
    from app.services.attendance_service import generate_qr
    stmt2 = select(Faculty).where(Faculty.user_id == user_id)
    result2 = await db.execute(stmt2)
    faculty = result2.scalar_one_or_none()

    if not faculty:
        return {"status": "error", "message": "Faculty profile not found"}

    qr_result = await generate_qr(db, course.id, faculty.id, 90)
    return {"status": "ok", "qr_generated": True, "course": course.name, **qr_result}


async def _handle_risk_roster(db: AsyncSession, params: dict) -> dict:
    """Handle risk roster fetch."""
    course_name = params.get("course_name", "")

    stmt = select(Course).where(func.lower(Course.name).like(f"%{course_name.lower()}%"))
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    if not course:
        return {"status": "error", "message": f"Course '{course_name}' not found"}

    # Count students
    stmt2 = select(func.count(Student.id)).where(
        Student.department_id == course.department_id,
        Student.semester == course.semester,
    )
    result2 = await db.execute(stmt2)
    count = result2.scalar() or 0

    return {
        "status": "ok",
        "course": course.name,
        "course_id": course.id,
        "total_students": count,
        "message": f"Risk roster for {course.name}: {count} students enrolled",
    }
