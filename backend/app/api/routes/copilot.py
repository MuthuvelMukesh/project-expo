"""
CampusIQ — AI Copilot Routes (Legacy Compatibility Layer)
Thin wrapper around /api/ops-ai/ for backward compatibility.
New code should use /api/ops-ai/ endpoints directly.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User, ImmutableAuditLog
from app.schemas.schemas import CopilotRequest, CopilotHistoryItem
from app.services.conversational_ops_service import create_and_execute

router = APIRouter()


@router.post("/plan")
async def copilot_plan(
    data: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a natural language request to the AI Copilot.
    Executes directly — no approval step.
    NOTE: Legacy endpoint. Use /api/ops-ai/execute for new integrations.
    """
    result = await create_and_execute(
        db=db,
        user=current_user,
        message=data.message,
        module="nlp",
    )
    return result


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
