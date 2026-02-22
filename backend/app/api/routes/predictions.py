"""
CampusIQ — Predictions Routes
AI-powered grade prediction endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import User, UserRole
from app.services.prediction_service import predict_student_performance

router = APIRouter()


@router.get("/{student_id}")
async def get_student_predictions(
    student_id: int,
    current_user: User = Depends(require_role(UserRole.FACULTY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI predictions for a specific student (faculty/admin only)."""
    return await predict_student_performance(db, student_id)


@router.get("/course/{course_id}/batch")
async def get_batch_predictions(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.FACULTY, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get predictions for all students in a course."""
    from sqlalchemy import select
    from app.models.models import Student, Course

    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        return {"error": "Course not found"}

    students_result = await db.execute(
        select(Student).where(
            Student.semester == course.semester,
            Student.department_id == course.department_id,
        )
    )
    students = students_result.scalars().all()

    results = []
    for student in students:
        preds = await predict_student_performance(db, student.id, course_id)
        if preds:
            pred = preds[0]
            results.append({
                "student_id": student.id,
                "roll_number": student.roll_number,
                **pred,
            })

    # Sort by risk score descending
    results.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_students": len(results),
        "predictions": results,
        "risk_distribution": {
            "high": sum(1 for r in results if r.get("risk_level") == "high"),
            "moderate": sum(1 for r in results if r.get("risk_level") == "moderate"),
            "low": sum(1 for r in results if r.get("risk_level") == "low"),
        },
    }
