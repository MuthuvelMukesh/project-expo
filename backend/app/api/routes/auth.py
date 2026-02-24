"""
CampusIQ — Auth Routes
Registration, login, password reset, and current user endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib, secrets

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, Token, UserOut
from app.services.auth_service import register_user, authenticate_user
from app.core.security import hash_password, verify_password

router = APIRouter()

# Simple in-memory reset token store (use Redis in production)
_reset_tokens: dict = {}


@router.post("/register", response_model=UserOut)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    return await register_user(db, data)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and return a JWT token."""
    return await authenticate_user(db, data)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserOut.model_validate(current_user)


@router.post("/forgot-password")
async def forgot_password(data: dict, db: AsyncSession = Depends(get_db)):
    """Generate a password reset token."""
    email = data.get("email", "")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a reset token has been generated."}

    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = user.id
    # In production, send this via email. For demo, return it.
    return {
        "message": "Reset token generated. Use it with /auth/reset-password.",
        "reset_token": token,  # Remove in production
    }


@router.post("/reset-password")
async def reset_password(data: dict, db: AsyncSession = Depends(get_db)):
    """Reset password using a reset token."""
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user_id = _reset_tokens.pop(token, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "Password reset successfully"}


@router.put("/change-password")
async def change_password(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user."""
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    current_user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "Password changed successfully"}
