"""
Conversational Operational AI routes.
Direct execution — no approval gates.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    AuditHistoryItem,
    ConversationalRequest,
    ConversationalResponse,
    OperationalRollbackRequest,
    OperationalRollbackResponse,
    OpsStatsResponse,
)
from app.services.conversational_ops_service import (
    create_and_execute,
    get_audit_history,
    get_ops_stats,
    rollback_execution,
)

router = APIRouter()


@router.post("/execute", response_model=ConversationalResponse)
async def execute_command(
    data: ConversationalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single entry point: message in → result out. No approval gates."""
    result = await create_and_execute(
        db=db,
        user=current_user,
        message=data.message,
        module=data.module,
    )
    return ConversationalResponse(**result)


@router.post("/rollback", response_model=OperationalRollbackResponse)
async def rollback_plan_execution(
    data: OperationalRollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await rollback_execution(db=db, user=current_user, execution_id=data.execution_id)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return OperationalRollbackResponse(**result)


@router.get("/history", response_model=list[AuditHistoryItem])
async def audit_history(
    module: Optional[str] = Query(default=None),
    operation_type: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    actor_user_id: Optional[int] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_audit_history(
        db=db,
        user=current_user,
        module=module,
        operation_type=operation_type,
        risk_level=risk_level,
        actor_user_id=actor_user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )


@router.get("/stats", response_model=OpsStatsResponse)
async def ops_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate operation statistics for the governance dashboard."""
    result = await get_ops_stats(db=db, user=current_user)
    return OpsStatsResponse(**result)
