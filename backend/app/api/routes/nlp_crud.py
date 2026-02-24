"""
CampusIQ — NLP CRUD API Routes
Natural language data operations endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import NLPCrudQuery, NLPCrudResponse
from app.services.nlp_crud_service import process_nlp_crud

router = APIRouter()


@router.post("/query", response_model=NLPCrudResponse)
async def nlp_crud_query(
    data: NLPCrudQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Process a natural language query to perform data operations.

    Supports:
    - **READ**: "Show all students in CS department"
    - **CREATE**: "Add a new course called AI" (admin only)
    - **UPDATE**: "Update my semester to 5" (students: own data only)
    - **DELETE**: "Delete course CS301" (admin only)
    - **ANALYZE**: "Average CGPA by department"
    """
    result = await process_nlp_crud(
        message=data.message,
        user_role=current_user.role.value,
        user_id=current_user.id,
        db=db,
    )
    return NLPCrudResponse(**result)
