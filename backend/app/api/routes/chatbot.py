"""
CampusIQ — Chatbot Routes
Natural language AI query endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import ChatQuery, ChatResponse
from app.services.chatbot_service import process_query

router = APIRouter()


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    data: ChatQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a natural language query to the CampusIQ AI assistant."""
    result = await process_query(
        message=data.message,
        user_role=current_user.role.value,
        user_id=current_user.id,
        db=db,
    )
    return ChatResponse(**result)
