"""
CampusIQ — Student Routes
Student dashboard, attendance, and prediction endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import User, UserRole, Student
from app.schemas.schemas import StudentDashboard, StudentProfileOut
from app.services.attendance_service import get_student_attendance_summary
from app.services.prediction_service import predict_student_performance, generate_ai_recommendations
from sqlalchemy import select

router = APIRouter()


@router.get("/me/dashboard")
async def get_student_dashboard(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get the full student dashboard with AI insights."""
    # Get student profile
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "Student profile not found. Please contact admin."}

    # Get attendance summary
    attendance_summary = await get_student_attendance_summary(db, student.id)

    # Get predictions
    predictions = await predict_student_performance(db, student.id)

    # Generate AI recommendations
    recommendations = generate_ai_recommendations(predictions, attendance_summary)

    # Calculate overall metrics
    overall_attendance = (
        sum(a["percentage"] for a in attendance_summary) / len(attendance_summary)
        if attendance_summary else 100.0
    )

    high_risk_count = sum(1 for p in predictions if p["risk_level"] == "high")
    overall_risk = (
        "high" if high_risk_count >= 2
        else "moderate" if high_risk_count == 1
        else "low"
    )

    return {
        "student": {
            "id": student.id,
            "roll_number": student.roll_number,
            "semester": student.semester,
            "section": student.section,
            "cgpa": student.cgpa,
            "full_name": current_user.full_name,
            "email": current_user.email,
        },
        "attendance_summary": attendance_summary,
        "predictions": predictions,
        "overall_risk": overall_risk,
        "overall_attendance": round(overall_attendance, 1),
        "ai_recommendations": recommendations,
    }


@router.get("/me/attendance")
async def get_my_attendance(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance summary for the current student."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "Student profile not found"}

    return await get_student_attendance_summary(db, student.id)


@router.get("/me/predictions")
async def get_my_predictions(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI predictions for the current student."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        return {"error": "Student profile not found"}

    return await predict_student_performance(db, student.id)
