"""
CampusIQ — Attendance Routes
QR generation, marking, and analytics endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import User, UserRole, Student, Faculty
from app.schemas.schemas import QRCodeGenerate, AttendanceMark
from app.services.attendance_service import (
    generate_qr, mark_attendance, get_course_attendance_analytics,
)
from sqlalchemy import select

router = APIRouter()


@router.post("/generate-qr")
async def generate_qr_code(
    data: QRCodeGenerate,
    current_user: User = Depends(require_role(UserRole.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    """Faculty generates a time-limited QR code for attendance."""
    result = await db.execute(select(Faculty).where(Faculty.user_id == current_user.id))
    faculty = result.scalar_one_or_none()
    faculty_id = faculty.id if faculty else 0
    return await generate_qr(db, data.course_id, faculty_id, data.valid_seconds)


@router.post("/mark")
async def mark_student_attendance(
    data: AttendanceMark,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Student marks attendance by scanning QR code."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "Student profile not found"}
    return await mark_attendance(db, data.qr_token, student.id)


@router.get("/analytics/{course_id}")
async def get_attendance_analytics(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.FACULTY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance analytics for a course (faculty/admin only)."""
    return await get_course_attendance_analytics(db, course_id)
