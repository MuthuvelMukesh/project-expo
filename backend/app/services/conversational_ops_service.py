"""
Conversational Operational AI layer for CampusIQ.
Intent -> Clarification -> Risk -> Approval -> Controlled Execution -> Audit.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import (
    Attendance,
    Course,
    Department,
    Employee,
    Faculty,
    ImmutableAuditLog,
    Invoice,
    OperationalApprovalDecision,
    OperationalExecution,
    OperationalPlan,
    Payment,
    Prediction,
    SalaryRecord,
    Student,
    StudentFees,
    User,
)
from app.services.gemini_pool_service import GeminiPoolClient, GeminiPoolError

settings = get_settings()

ALLOWED_INTENTS = {"READ", "CREATE", "UPDATE", "DELETE", "ANALYZE", "ESCALATE"}

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
    "courses": "course",
    "departments": "department",
    "attendances": "attendance",
    "predictions": "prediction",
    "fees": "student_fee",
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
        "CREATE": {"attendance"},
        "UPDATE": {"attendance", "course"},
        "DELETE": set(),
    },
    "admin": {
        "READ": set(ENTITY_REGISTRY.keys()),
        "ANALYZE": set(ENTITY_REGISTRY.keys()),
        "CREATE": set(ENTITY_REGISTRY.keys()),
        "UPDATE": set(ENTITY_REGISTRY.keys()),
        "DELETE": set(ENTITY_REGISTRY.keys()),
    },
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


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

    cgpa_match = re.search(r"cgpa\s*(?:to|=)\s*([\d.]+)", msg)
    if cgpa_match:
        values["cgpa"] = float(cgpa_match.group(1))

    confidence = 0.62
    ambiguity = []
    if intent in {"UPDATE", "DELETE"} and not filters:
        ambiguity.append("scope")
        confidence -= 0.2
    if intent in {"CREATE", "UPDATE"} and not values:
        ambiguity.append("affected_fields")
        confidence -= 0.2

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
Return keys exactly:
intent: READ|CREATE|UPDATE|DELETE|ANALYZE|ESCALATE
entity: canonical lowercase singular entity
filters: object
scope: object
affected_fields: array of strings
values: object
confidence: float between 0 and 1
ambiguity: {{is_ambiguous: boolean, fields: array[string], question: string|null}}

Message: {message}
"""
    try:
        llm = await GeminiPoolClient.generate_json(module=module, prompt=prompt)
        parsed = _json_extract(llm.get("text", ""))
        if parsed:
            parsed["intent"] = str(parsed.get("intent", "READ")).upper()
            if parsed["intent"] not in ALLOWED_INTENTS:
                parsed["intent"] = "READ"
            parsed["entity"] = _normalize_entity(str(parsed.get("entity", "student")))
            parsed["filters"] = parsed.get("filters") or {}
            parsed["scope"] = parsed.get("scope") or {}
            parsed["affected_fields"] = parsed.get("affected_fields") or list((parsed.get("values") or {}).keys())
            parsed["values"] = parsed.get("values") or {}
            parsed["confidence"] = float(parsed.get("confidence", 0.6))
            parsed["ambiguity"] = parsed.get("ambiguity") or {"is_ambiguous": False, "fields": []}
            return parsed, None
    except GeminiPoolError as pool_err:
        return _keyword_intent(message), {
            "code": pool_err.code,
            "message": pool_err.message,
            "retry_eta_seconds": pool_err.retry_eta_seconds,
            "fallback": "explicit_crud_ui",
        }

    return _keyword_intent(message), None


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
    if intent == "ESCALATE":
        return True
    matrix = ROLE_MATRIX.get(role, ROLE_MATRIX["student"])
    return entity in matrix.get(intent, set())


async def _permission_gate(db: AsyncSession, user: User, intent: str, entity: str, filters: dict) -> tuple[bool, str, bool]:
    if not _is_allowed(user.role.value, intent, entity):
        return False, "ROLE_RESTRICTED", True

    user_dept = await _user_department_scope(db, user)
    target_dept = await _resolve_department_filter(db, filters)

    if user.role.value in {"student", "faculty"} and target_dept and user_dept and target_dept != user_dept:
        return False, "DEPARTMENT_SCOPE_RESTRICTED", True

    if user.role.value == "student" and intent in {"UPDATE", "DELETE", "CREATE"}:
        return False, "STUDENT_WRITE_RESTRICTED", True

    return True, "OK", False


async def _estimate_impact(db: AsyncSession, entity: str, filters: dict) -> int:
    model = ENTITY_REGISTRY[entity]["model"]
    stmt = select(func.count()).select_from(model)
    stmt = _apply_filters(stmt, model, entity, filters)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


def _classify_risk(intent: str, entity: str, impact_count: int, fields: list[str]) -> str:
    if intent in {"READ", "ANALYZE"}:
        return "LOW"

    high_fields = {"salary", "base_salary", "net_salary", "gross_salary", "tax_rate"}
    if intent == "DELETE" and impact_count >= 1:
        return "HIGH" if impact_count > 1 else "MEDIUM"
    if any(field in high_fields for field in fields):
        return "HIGH"
    if impact_count > 25:
        return "HIGH"
    if intent in {"UPDATE", "CREATE"}:
        return "MEDIUM"
    return "LOW"


async def _audit(
    db: AsyncSession,
    *,
    user: User,
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
        user_id=user.id,
        role=user.role.value,
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


def _model_to_dict(instance, include_id: bool = True) -> dict:
    data = {}
    for column in instance.__table__.columns:
        if not include_id and column.name == "id":
            continue
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data


def _apply_filters(stmt, model, entity: str, filters: dict):
    if not filters:
        return stmt

    for key, value in filters.items():
        if key == "id" and hasattr(model, "id"):
            stmt = stmt.where(model.id == int(value))
        elif key == "semester" and hasattr(model, "semester"):
            stmt = stmt.where(model.semester == int(value))
        elif key == "department_id" and hasattr(model, "department_id"):
            stmt = stmt.where(model.department_id == int(value))
        elif key == "department" and entity in {"student", "faculty", "course"}:
            if entity == "student":
                stmt = stmt.join(Department, Student.department_id == Department.id)
            elif entity == "faculty":
                stmt = stmt.join(Department, Faculty.department_id == Department.id)
            elif entity == "course":
                stmt = stmt.join(Department, Course.department_id == Department.id)
            stmt = stmt.where(func.lower(Department.name).like(f"%{str(value).lower()}%"))
        elif hasattr(model, key):
            stmt = stmt.where(getattr(model, key) == value)
    return stmt


async def _build_preview(db: AsyncSession, entity: str, filters: dict, values: dict) -> dict:
    model = ENTITY_REGISTRY[entity]["model"]
    max_rows = settings.OPS_MAX_PREVIEW_ROWS

    stmt = select(model)
    stmt = _apply_filters(stmt, model, entity, filters).limit(max_rows)
    rows = (await db.execute(stmt)).scalars().all()

    affected = [_model_to_dict(row) for row in rows]
    proposed = []
    for row in rows:
        updated = _model_to_dict(row)
        for key, value in values.items():
            if key in updated:
                updated[key] = value
        proposed.append(updated)

    return {
        "affected_records": affected,
        "proposed_changes": proposed if values else [],
        "rollback_plan": {
            "strategy": "before_state_snapshot",
            "supports_rollback": True,
            "note": "Rollback restores before_state for UPDATE/DELETE and deletes created records.",
        },
    }


def _clarification_needed(intent_payload: dict) -> tuple[bool, dict]:
    confidence = float(intent_payload.get("confidence", 0.0))
    ambiguity = intent_payload.get("ambiguity") or {}
    fields = ambiguity.get("fields") or []

    if confidence < settings.OPS_CONFIDENCE_THRESHOLD or ambiguity.get("is_ambiguous"):
        missing = fields or ["entity/scope/filter/action"]
        return True, {
            "code": "CLARIFICATION_REQUIRED",
            "message": "Intent is ambiguous; execution has been paused.",
            "unclear_parts": missing,
            "question": ambiguity.get("question") or "Please clarify the missing operation details.",
            "confidence": confidence,
            "threshold": settings.OPS_CONFIDENCE_THRESHOLD,
        }

    return False, {}


async def create_operational_plan(
    *,
    db: AsyncSession,
    user: User,
    message: str,
    module: str = "nlp",
    clarification: Optional[str] = None,
) -> dict:
    final_message = f"{message}\nClarification: {clarification}" if clarification else message
    intent_payload, ai_status = await _extract_intent(final_message, module)

    intent = str(intent_payload.get("intent", "READ")).upper()
    entity = _normalize_entity(intent_payload.get("entity", "student"))
    filters = intent_payload.get("filters") or {}
    values = intent_payload.get("values") or {}
    affected_fields = intent_payload.get("affected_fields") or list(values.keys())

    needs_clarification, clarification_payload = _clarification_needed(intent_payload)

    # Permission gate / escalation decision
    allowed, reason, must_escalate = await _permission_gate(db, user, intent, entity, filters)
    if must_escalate and intent != "ESCALATE":
        intent = "ESCALATE"

    impact = await _estimate_impact(db, entity, filters)
    risk = _classify_risk(intent, entity, impact, affected_fields)

    preview = await _build_preview(db, entity, filters, values)

    plan_id = f"ops_{uuid.uuid4().hex[:12]}"
    requires_confirmation = risk == "MEDIUM"
    requires_senior_approval = risk == "HIGH" or intent == "ESCALATE"
    requires_2fa = bool(settings.OPS_REQUIRE_2FA_HIGH_RISK and risk == "HIGH")

    plan_status = "clarification_required" if needs_clarification else "awaiting_confirmation"
    if requires_senior_approval:
        plan_status = "awaiting_approval"
    if intent == "READ" and risk == "LOW" and not needs_clarification and allowed:
        plan_status = "ready_for_execution"

    plan = OperationalPlan(
        plan_id=plan_id,
        user_id=user.id,
        module=module,
        message=final_message,
        intent_type=intent,
        entity=entity,
        filters=filters,
        scope=intent_payload.get("scope") or {},
        affected_fields=affected_fields,
        values=values,
        confidence=float(intent_payload.get("confidence", 0.0)),
        ambiguity=intent_payload.get("ambiguity") or {},
        risk_level=risk,
        estimated_impact_count=impact,
        status=plan_status,
        requires_confirmation=requires_confirmation,
        requires_senior_approval=requires_senior_approval,
        requires_2fa=requires_2fa,
        escalation_required=(intent == "ESCALATE"),
        preview=preview,
        rollback_plan=preview.get("rollback_plan", {}),
        error=None if allowed else reason,
    )
    db.add(plan)
    await db.flush()

    await _audit(
        db,
        user=user,
        module=module,
        operation_type=intent,
        event_type="clarification_required" if needs_clarification else "intent_extracted",
        risk_level=risk,
        plan_id=plan_id,
        intent_payload=intent_payload,
        meta={"permission_reason": reason, "ai_status": ai_status},
    )

    auto_execution = None
    if plan_status == "ready_for_execution":
        auto_execution = await execute_operational_plan(
            db=db,
            user=user,
            plan_id=plan_id,
        )

    return {
        "plan_id": plan_id,
        "intent": intent,
        "entity": entity,
        "confidence": plan.confidence,
        "risk_level": risk,
        "estimated_impact_count": impact,
        "requires_confirmation": requires_confirmation,
        "requires_senior_approval": requires_senior_approval,
        "requires_2fa": requires_2fa,
        "status": plan.status,
        "clarification": clarification_payload if needs_clarification else None,
        "preview": preview,
        "auto_execution": auto_execution,
        "ai_service": ai_status,
        "permission": {
            "allowed": allowed and not must_escalate,
            "reason": reason,
            "escalation_required": must_escalate,
        },
    }


async def add_approval_decision(
    *,
    db: AsyncSession,
    user: User,
    plan_id: str,
    decision: str,
    approved_ids: Optional[list[int]] = None,
    rejected_ids: Optional[list[int]] = None,
    comment: Optional[str] = None,
    two_factor_code: Optional[str] = None,
) -> dict:
    stmt = select(OperationalPlan).where(OperationalPlan.plan_id == plan_id)
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        return {"error": "PLAN_NOT_FOUND"}

    normalized_decision = decision.strip().upper()
    two_factor_verified = bool(two_factor_code and len(two_factor_code.strip()) >= 6)

    if plan.requires_senior_approval and user.role.value not in settings.OPS_SENIOR_ROLE_SET:
        return {"error": "SENIOR_APPROVAL_REQUIRED"}

    if plan.requires_2fa and not two_factor_verified:
        return {"error": "TWO_FACTOR_REQUIRED"}

    approval = OperationalApprovalDecision(
        plan_id=plan_id,
        reviewer_id=user.id,
        reviewer_role=user.role.value,
        decision=normalized_decision,
        approved_scope={"ids": approved_ids or []},
        rejected_scope={"ids": rejected_ids or []},
        comment=comment,
        two_factor_verified=two_factor_verified,
    )
    db.add(approval)

    if normalized_decision == "APPROVE":
        plan.status = "approved"
    elif normalized_decision == "REJECT":
        plan.status = "rejected"
    else:
        plan.status = "escalated"

    await db.flush()

    await _audit(
        db,
        user=user,
        module=plan.module,
        operation_type=plan.intent_type,
        event_type=normalized_decision.lower(),
        risk_level=plan.risk_level,
        plan_id=plan.plan_id,
        intent_payload={
            "entity": plan.entity,
            "filters": plan.filters,
            "values": plan.values,
            "approved_ids": approved_ids or [],
            "rejected_ids": rejected_ids or [],
        },
    )

    return {
        "plan_id": plan_id,
        "status": plan.status,
        "decision": normalized_decision,
        "two_factor_verified": two_factor_verified,
        "approved_ids": approved_ids or [],
        "rejected_ids": rejected_ids or [],
    }


async def _rows_for_execution(db: AsyncSession, plan: OperationalPlan) -> list:
    model = ENTITY_REGISTRY[plan.entity]["model"]
    stmt = select(model)
    stmt = _apply_filters(stmt, model, plan.entity, plan.filters or {})

    decision_stmt = (
        select(OperationalApprovalDecision)
        .where(OperationalApprovalDecision.plan_id == plan.plan_id)
        .order_by(OperationalApprovalDecision.id.desc())
    )
    latest_decision = (await db.execute(decision_stmt)).scalars().first()

    if latest_decision and latest_decision.approved_scope:
        ids = (latest_decision.approved_scope or {}).get("ids") or []
        if ids and hasattr(model, "id"):
            stmt = stmt.where(model.id.in_(ids))

    result = await db.execute(stmt)
    return result.scalars().all()


async def execute_operational_plan(*, db: AsyncSession, user: User, plan_id: str) -> dict:
    plan_stmt = select(OperationalPlan).where(OperationalPlan.plan_id == plan_id)
    plan = (await db.execute(plan_stmt)).scalar_one_or_none()
    if not plan:
        return {"error": "PLAN_NOT_FOUND"}

    if plan.status in {"clarification_required", "rejected", "escalated"}:
        return {"error": f"PLAN_NOT_EXECUTABLE:{plan.status}"}

    if plan.requires_senior_approval and plan.status != "approved":
        return {"error": "APPROVAL_REQUIRED"}

    if plan.requires_confirmation and plan.status not in {"approved", "ready_for_execution"}:
        return {"error": "CONFIRMATION_REQUIRED"}

    model = ENTITY_REGISTRY[plan.entity]["model"]
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    execution = OperationalExecution(
        execution_id=execution_id,
        plan_id=plan.plan_id,
        executed_by=user.id,
        status="pending",
    )
    db.add(execution)
    await db.flush()

    before_state: list[dict] = []
    after_state: list[dict] = []

    try:
        rows = await _rows_for_execution(db, plan)
        before_state = [_model_to_dict(row) for row in rows]

        if plan.intent_type in {"READ", "ANALYZE", "ESCALATE"}:
            execution.status = "executed"
            execution.before_state = before_state
            execution.after_state = before_state
            execution.executed_at = _now()
            plan.status = "executed"
            await db.flush()

            await _audit(
                db,
                user=user,
                module=plan.module,
                operation_type=plan.intent_type,
                event_type="executed",
                risk_level=plan.risk_level,
                plan_id=plan.plan_id,
                execution_id=execution_id,
                intent_payload={"entity": plan.entity, "filters": plan.filters},
                before_state=before_state,
                after_state=before_state,
            )
            return {
                "plan_id": plan.plan_id,
                "execution_id": execution_id,
                "status": "executed",
                "affected_count": len(before_state),
                "before_state": before_state,
                "after_state": before_state,
            }

        if plan.intent_type == "CREATE":
            new_obj = model(**(plan.values or {}))
            db.add(new_obj)
            await db.flush()
            after_state = [_model_to_dict(new_obj)]

        elif plan.intent_type == "UPDATE":
            for row in rows:
                for key, value in (plan.values or {}).items():
                    if hasattr(row, key):
                        setattr(row, key, value)
            await db.flush()
            after_state = [_model_to_dict(row) for row in rows]

        elif plan.intent_type == "DELETE":
            for row in rows:
                await db.delete(row)
            await db.flush()
            after_state = []

        execution.status = "executed"
        execution.before_state = before_state
        execution.after_state = after_state
        execution.executed_at = _now()
        plan.status = "executed"
        await db.flush()

        await _audit(
            db,
            user=user,
            module=plan.module,
            operation_type=plan.intent_type,
            event_type="executed",
            risk_level=plan.risk_level,
            plan_id=plan.plan_id,
            execution_id=execution_id,
            intent_payload={"entity": plan.entity, "filters": plan.filters, "values": plan.values},
            before_state=before_state,
            after_state=after_state,
        )

        return {
            "plan_id": plan.plan_id,
            "execution_id": execution_id,
            "status": "executed",
            "affected_count": len(before_state) if plan.intent_type != "CREATE" else len(after_state),
            "before_state": before_state,
            "after_state": after_state,
        }

    except Exception as exc:
        await db.rollback()
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
            user=user,
            module=plan.module,
            operation_type=plan.intent_type,
            event_type="failed",
            risk_level=plan.risk_level,
            plan_id=plan.plan_id,
            execution_id=execution_id,
            intent_payload={"entity": plan.entity, "filters": plan.filters, "values": plan.values},
            before_state=before_state,
            after_state=after_state,
            meta={"alert": "Approver must review partial execution failure."},
        )

        return {
            "plan_id": plan.plan_id,
            "execution_id": execution_id,
            "status": "failed",
            "error": str(exc),
            "alert": "Approver alerted for failure review.",
        }


async def rollback_execution(*, db: AsyncSession, user: User, execution_id: str) -> dict:
    exec_stmt = select(OperationalExecution).where(OperationalExecution.execution_id == execution_id)
    execution = (await db.execute(exec_stmt)).scalar_one_or_none()
    if not execution:
        return {"error": "EXECUTION_NOT_FOUND"}

    plan_stmt = select(OperationalPlan).where(OperationalPlan.plan_id == execution.plan_id)
    plan = (await db.execute(plan_stmt)).scalar_one_or_none()
    if not plan:
        return {"error": "PLAN_NOT_FOUND"}

    if user.role.value not in settings.OPS_SENIOR_ROLE_SET and execution.executed_by != user.id:
        return {"error": "ROLLBACK_NOT_PERMITTED"}

    model = ENTITY_REGISTRY[plan.entity]["model"]

    try:
        if plan.intent_type == "CREATE":
            created_ids = [row.get("id") for row in (execution.after_state or []) if row.get("id") is not None]
            if created_ids:
                rows = (await db.execute(select(model).where(model.id.in_(created_ids)))).scalars().all()
                for row in rows:
                    await db.delete(row)

        elif plan.intent_type == "UPDATE":
            before = execution.before_state or []
            for snapshot in before:
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
            before = execution.before_state or []
            for snapshot in before:
                record_data = {k: v for k, v in snapshot.items() if k != "id"}
                restored = model(**record_data)
                if snapshot.get("id") is not None and hasattr(restored, "id"):
                    setattr(restored, "id", snapshot["id"])
                db.add(restored)

        else:
            return {"error": "ROLLBACK_NOT_REQUIRED_FOR_OPERATION"}

        execution.status = "rolled_back"
        execution.rolled_back_at = _now()
        execution.rollback_state = {"rolled_back": True}
        plan.status = "rolled_back"
        await db.flush()

        await _audit(
            db,
            user=user,
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
            "execution_id": execution_id,
            "plan_id": plan.plan_id,
            "status": "rolled_back",
        }

    except Exception as exc:
        return {
            "execution_id": execution_id,
            "status": "rollback_failed",
            "error": str(exc),
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
    stmt = select(ImmutableAuditLog)

    filters = []
    if module:
        filters.append(ImmutableAuditLog.module == module)
    if operation_type:
        filters.append(ImmutableAuditLog.operation_type == operation_type.upper())
    if risk_level:
        filters.append(ImmutableAuditLog.risk_level == risk_level.upper())
    if actor_user_id:
        filters.append(ImmutableAuditLog.user_id == actor_user_id)
    if start_date:
        filters.append(ImmutableAuditLog.created_at >= start_date)
    if end_date:
        filters.append(ImmutableAuditLog.created_at <= end_date)

    if user.role.value != "admin":
        filters.append(ImmutableAuditLog.user_id == user.id)

    if filters:
        stmt = stmt.where(and_(*filters))

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
