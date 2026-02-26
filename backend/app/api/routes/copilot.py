"""
CampusIQ — AI Copilot Routes (Legacy Compatibility Layer)
Routes to conversational_ops_service for backward compatibility.
New code should use /api/ops-ai/ endpoints directly.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, ImmutableAuditLog
from app.schemas.schemas import (
    CopilotRequest, CopilotPlan, CopilotConfirm,
    CopilotResult, CopilotHistoryItem,
)
from app.services.conversational_ops_service import (
    create_operational_plan,
    execute_operational_plan,
)

router = APIRouter()


def _convert_ops_plan_to_copilot_format(ops_result: dict) -> dict:
    """Convert conversational_ops_service response to legacy copilot format."""
    preview = ops_result.get("preview", {})
    auto_executed = None
    
    # If auto-executed (LOW risk READ), build results
    if ops_result.get("auto_execution"):
        auto_exec = ops_result["auto_execution"]
        auto_executed = [{
            "action_id": f"{ops_result['plan_id']}_act_0",
            "description": f"{ops_result['intent']} {ops_result['entity']}",
            "status": auto_exec.get("status", "executed"),
            "result": {
                "data": auto_exec.get("after_state", []),
                "count": auto_exec.get("affected_count", 0),
            },
        }]
    
    # Build actions list for pending confirmation
    actions = []
    if ops_result.get("status") not in ("executed", "ready_for_execution"):
        actions.append({
            "action_id": f"{ops_result['plan_id']}_act_0",
            "type": ops_result.get("intent", "READ"),
            "entity": ops_result.get("entity", "student"),
            "description": f"{ops_result['intent']} {ops_result['entity']} ({ops_result.get('estimated_impact_count', 0)} records)",
            "risk_level": ops_result.get("risk_level", "LOW").lower(),
            "requires_confirmation": ops_result.get("requires_confirmation", False),
            "params": {"filters": ops_result.get("preview", {}).get("affected_records", [])[:5]},
        })
    
    summary_parts = []
    if auto_executed:
        summary_parts.append(f"✅ **1** action executed automatically")
    if ops_result.get("requires_confirmation"):
        summary_parts.append(f"⏳ **1** action needs your approval")
    if ops_result.get("requires_senior_approval"):
        summary_parts.append(f"🔒 Requires senior admin approval")
    
    return {
        "plan_id": ops_result.get("plan_id", ""),
        "message": "",
        "actions": actions,
        "summary": " · ".join(summary_parts) if summary_parts else "Operation ready.",
        "requires_confirmation": ops_result.get("requires_confirmation", False) or ops_result.get("requires_senior_approval", False),
        "auto_executed": auto_executed,
    }


@router.post("/plan", response_model=CopilotPlan)
async def copilot_plan(
    data: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a natural language request to the AI Copilot.
    
    NOTE: This is a legacy endpoint. Use /api/ops-ai/plan for new integrations.
    """
    ops_result = await create_operational_plan(
        db=db,
        user=current_user,
        message=data.message,
        module="nlp",
    )
    return CopilotPlan(**_convert_ops_plan_to_copilot_format(ops_result))


@router.post("/execute", response_model=CopilotResult)
async def copilot_execute(
    data: CopilotConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a confirmed plan.
    
    NOTE: This is a legacy endpoint. Use /api/ops-ai/execute for new integrations.
    """
    result = await execute_operational_plan(
        db=db,
        user=current_user,
        plan_id=data.plan_id,
    )
    
    # Convert to legacy format
    status = result.get("status", "failed")
    executed = 1 if status == "executed" else 0
    failed = 1 if "error" in result else 0
    rejected = len(data.rejected_action_ids)
    
    return CopilotResult(
        plan_id=data.plan_id,
        actions_executed=executed,
        actions_failed=failed,
        actions_rejected=rejected,
        results=[{
            "action_id": f"{data.plan_id}_act_0",
            "description": f"Executed plan {data.plan_id}",
            "status": status,
            "result": result.get("after_state", []),
        }] if executed else [],
        summary=f"{'✅' if executed else '❌'} Plan {status}",
    )


@router.get("/history")
async def copilot_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """
    Get action history for the current user from the audit log.
    
    NOTE: This is a legacy endpoint. Use /api/ops-ai/audit for new integrations.
    """
    stmt = (
        select(ImmutableAuditLog)
        .where(ImmutableAuditLog.user_id == current_user.id)
        .order_by(ImmutableAuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        {
            "id": log.id,
            "plan_id": log.plan_id or "",
            "action_type": log.operation_type or "READ",
            "entity": (log.intent_payload or {}).get("entity", "unknown"),
            "description": f"{log.operation_type} operation via {log.module}",
            "risk_level": (log.risk_level or "LOW").lower(),
            "status": log.event_type or "unknown",
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "executed_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
