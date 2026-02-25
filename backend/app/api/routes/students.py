"""
CampusIQ — Student Routes
Student dashboard, profile, attendance, and prediction endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import User, UserRole, Student, Department, Attendance, Course
from app.schemas.schemas import StudentProfileUpdate
from app.services.attendance_service import get_student_attendance_summary
from app.services.prediction_service import predict_student_performance, generate_ai_recommendations
from sqlalchemy import select, func

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
        raise HTTPException(status_code=404, detail="Student profile not found. Please contact admin.")

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


@router.get("/me/profile")
async def get_my_profile(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get student profile with department info."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    dept = await db.execute(select(Department).where(Department.id == student.department_id))
    dept_obj = dept.scalar_one_or_none()

    return {
        "id": student.id,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "roll_number": student.roll_number,
        "department_id": student.department_id,
        "department_name": dept_obj.name if dept_obj else None,
        "semester": student.semester,
        "section": student.section,
        "cgpa": student.cgpa,
        "admission_year": student.admission_year,
    }


@router.put("/me/profile")
async def update_my_profile(
    data: StudentProfileUpdate,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Update student's own profile (limited fields)."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    updates = data.model_dump(exclude_unset=True)

    if "section" in updates:
        student.section = updates["section"]
    if "full_name" in updates:
        current_user.full_name = updates["full_name"]

    await db.flush()
    return {"message": "Profile updated"}


@router.get("/me/attendance")
async def get_my_attendance(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get attendance summary for the current student."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return await get_student_attendance_summary(db, student.id)


@router.get("/me/attendance/details")
async def get_my_attendance_details(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get per-course, per-date attendance records for calendar view."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Get all attendance records
    stmt = (
        select(Attendance, Course)
        .join(Course, Attendance.course_id == Course.id)
        .where(Attendance.student_id == student.id)
        .order_by(Attendance.date.desc())
    )
    records = await db.execute(stmt)
    rows = records.all()

    # Group by course
    by_course = {}
    all_dates = []
    for att, course in rows:
        if course.id not in by_course:
            by_course[course.id] = {
                "course_id": course.id,
                "course_name": course.name,
                "course_code": course.code,
                "records": [],
                "total": 0,
                "present": 0,
            }
        by_course[course.id]["records"].append({
            "date": att.date.isoformat(),
            "is_present": att.is_present,
            "method": att.method,
        })
        by_course[course.id]["total"] += 1
        if att.is_present:
            by_course[course.id]["present"] += 1

        all_dates.append({
            "date": att.date.isoformat(),
            "is_present": att.is_present,
            "course_code": course.code,
        })

    # Add percentage
    for cid in by_course:
        c = by_course[cid]
        c["percentage"] = round((c["present"] / c["total"]) * 100, 1) if c["total"] > 0 else 0

    return {
        "courses": list(by_course.values()),
        "calendar": all_dates,
    }


@router.get("/me/predictions")
async def get_my_predictions(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """Get AI predictions for the current student."""
    result = await db.execute(select(Student).where(Student.user_id == current_user.id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    return await predict_student_performance(db, student.id)

