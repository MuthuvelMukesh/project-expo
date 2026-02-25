"""
Conversational Operational AI routes.
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
    OperationalDecisionRequest,
    OperationalDecisionResponse,
    OperationalExecuteRequest,
    OperationalExecuteResponse,
    OperationalPlanRequest,
    OperationalPlanResponse,
    OperationalRollbackRequest,
    OperationalRollbackResponse,
    OpsStatsResponse,
    PendingApprovalItem,
)
from app.services.conversational_ops_service import (
    add_approval_decision,
    create_operational_plan,
    execute_operational_plan,
    get_audit_history,
    get_ops_stats,
    get_pending_approvals,
    rollback_execution,
)

router = APIRouter()


@router.post("/plan", response_model=OperationalPlanResponse)
async def create_plan(
    data: OperationalPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await create_operational_plan(
        db=db,
        user=current_user,
        message=data.message,
        module=data.module,
        clarification=data.clarification,
    )
    return OperationalPlanResponse(**result)


@router.post("/decision", response_model=OperationalDecisionResponse)
async def submit_decision(
    data: OperationalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await add_approval_decision(
        db=db,
        user=current_user,
        plan_id=data.plan_id,
        decision=data.decision,
        approved_ids=data.approved_ids,
        rejected_ids=data.rejected_ids,
        comment=data.comment,
        two_factor_code=data.two_factor_code,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return OperationalDecisionResponse(**result)


@router.post("/execute", response_model=OperationalExecuteResponse)
async def execute_plan(
    data: OperationalExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await execute_operational_plan(
        db=db,
        user=current_user,
        plan_id=data.plan_id,
    )
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return OperationalExecuteResponse(**result)


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


@router.get("/audit", response_model=list[AuditHistoryItem])
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


@router.get("/pending", response_model=list[PendingApprovalItem])
async def pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all plans awaiting senior approval. Admin-only; non-admins receive empty list."""
    return await get_pending_approvals(db=db, user=current_user)


@router.get("/stats", response_model=OpsStatsResponse)
async def ops_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate operation statistics for the governance dashboard."""
    result = await get_ops_stats(db=db, user=current_user)
    return OpsStatsResponse(**result)
