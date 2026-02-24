"""
CampusIQ — AI Copilot Routes
Plan, confirm, execute, and view history of AI-driven operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    CopilotRequest, CopilotPlan, CopilotConfirm,
    CopilotResult, CopilotHistoryItem,
)
from app.services.copilot_service import create_plan, execute_plan, get_history

router = APIRouter()


@router.post("/plan", response_model=CopilotPlan)
async def copilot_plan(
    data: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a natural language request to the AI Copilot.

    Returns an action plan with:
    - Safe actions already executed
    - Dangerous actions awaiting your confirmation
    """
    result = await create_plan(
        message=data.message,
        user_role=current_user.role.value,
        user_id=current_user.id,
        db=db,
    )
    return CopilotPlan(**result)


@router.post("/execute", response_model=CopilotResult)
async def copilot_execute(
    data: CopilotConfirm,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Confirm and execute pending actions from a plan.

    Send approved_action_ids to execute and rejected_action_ids to skip.
    """
    result = await execute_plan(
        plan_id=data.plan_id,
        approved_ids=data.approved_action_ids,
        rejected_ids=data.rejected_action_ids,
        user_id=current_user.id,
        user_role=current_user.role.value,
        db=db,
    )
    return CopilotResult(**result)


@router.get("/history")
async def copilot_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the action history for the current user."""
    return await get_history(current_user.id, db)
