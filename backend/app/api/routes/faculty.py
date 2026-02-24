"""
CampusIQ — Faculty Routes
Faculty console endpoints: class analytics, risk roster.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import require_role
from app.models.models import User, UserRole, Faculty, Course, Student
from app.services.prediction_service import predict_student_performance
from app.services.attendance_service import get_student_attendance_summary

router = APIRouter()


@router.get("/me/courses")
async def get_my_courses(
    current_user: User = Depends(require_role(UserRole.FACULTY)),
    db: AsyncSession = Depends(get_db),
):
    """Get all courses taught by the current faculty."""
    result = await db.execute(select(Faculty).where(Faculty.user_id == current_user.id))
    faculty = result.scalar_one_or_none()
    if not faculty:
        return []

    courses_result = await db.execute(
        select(Course).where(Course.instructor_id == faculty.id)
    )
    courses = courses_result.scalars().all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "semester": c.semester,
            "credits": c.credits,
        }
        for c in courses
    ]


@router.get("/course/{course_id}/risk-roster")
async def get_risk_roster(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.FACULTY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get students sorted by risk score for a specific course."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    students_result = await db.execute(
        select(Student).where(
            Student.semester == course.semester,
            Student.department_id == course.department_id,
        )
    )
    students = students_result.scalars().all()

    roster = []
    for student in students:
        preds = await predict_student_performance(db, student.id, course_id)
        att_summary = await get_student_attendance_summary(db, student.id)

        att_for_course = next((a for a in att_summary if a["course_id"] == course_id), None)
        att_pct = att_for_course["percentage"] if att_for_course else 0

        # Get student user info
        user_result = await db.execute(select(User).where(User.id == student.user_id))
        user = user_result.scalar_one_or_none()

        if preds:
            pred = preds[0]
            roster.append({
                "student_id": student.id,
                "student_name": user.full_name if user else "Unknown",
                "roll_number": student.roll_number,
                "attendance_pct": att_pct,
                "predicted_grade": pred["predicted_grade"],
                "risk_score": pred["risk_score"],
                "risk_level": pred["risk_level"],
                "top_factors": pred["top_factors"],
            })

    roster.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_students": len(roster),
        "risk_distribution": {
            "high": sum(1 for r in roster if r["risk_level"] == "high"),
            "moderate": sum(1 for r in roster if r["risk_level"] == "moderate"),
            "low": sum(1 for r in roster if r["risk_level"] == "low"),
        },
        "students": roster,
    }
