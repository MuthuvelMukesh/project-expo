"""
CampusIQ — Export Routes
CSV download for attendance, risk roster, and student lists.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import csv
import io

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import User, UserRole, Student, Faculty, Course, Attendance, Department, Prediction

router = APIRouter()


def _make_csv(headers: list, rows: list) -> StreamingResponse:
    """Generate a CSV StreamingResponse."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )


@router.get("/students")
async def export_students(
    department_id: int = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Export student list as CSV."""
    stmt = select(Student, User, Department).join(
        User, Student.user_id == User.id
    ).join(Department, Student.department_id == Department.id)

    if department_id:
        stmt = stmt.where(Student.department_id == department_id)

    result = await db.execute(stmt)
    rows_data = result.all()

    headers = ["Roll Number", "Name", "Email", "Department", "Semester", "Section", "CGPA"]
    rows = [
        [s.roll_number, u.full_name, u.email, d.name, s.semester, s.section, s.cgpa]
        for s, u, d in rows_data
    ]

    return _make_csv(headers, rows)


@router.get("/attendance/{course_id}")
async def export_attendance(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export attendance records for a course as CSV."""
    stmt = select(Attendance, Student, User).join(
        Student, Attendance.student_id == Student.id
    ).join(User, Student.user_id == User.id).where(
        Attendance.course_id == course_id
    ).order_by(Attendance.date.desc())

    result = await db.execute(stmt)
    rows_data = result.all()

    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    course_name = course.name if course else "Unknown"

    headers = ["Date", "Roll Number", "Student Name", "Present", "Method"]
    rows = [
        [a.date.isoformat(), s.roll_number, u.full_name, "Yes" if a.is_present else "No", a.method]
        for a, s, u in rows_data
    ]

    response = _make_csv(headers, rows)
    response.headers["Content-Disposition"] = f'attachment; filename=attendance_{course_name}.csv'
    return response


@router.get("/risk-roster/{course_id}")
async def export_risk_roster(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export risk roster for a course as CSV."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Get students in the department/semester
    stmt = select(Student, User, Prediction).join(
        User, Student.user_id == User.id
    ).outerjoin(
        Prediction, (Prediction.student_id == Student.id) & (Prediction.course_id == course_id)
    ).where(
        Student.department_id == course.department_id,
        Student.semester == course.semester,
    )

    result = await db.execute(stmt)
    rows_data = result.all()

    headers = ["Roll Number", "Name", "CGPA", "Predicted Grade", "Risk Score", "Risk Level"]
    rows = []
    for s, u, p in rows_data:
        risk_score = p.risk_score if p else 0
        risk_level = "high" if risk_score > 0.6 else ("moderate" if risk_score > 0.3 else "low")
        rows.append([
            s.roll_number, u.full_name, s.cgpa,
            p.predicted_grade if p else "N/A",
            round(risk_score * 100, 1),
            risk_level,
        ])

    response = _make_csv(headers, rows)
    response.headers["Content-Disposition"] = f'attachment; filename=risk_roster_{course.name}.csv'
    return response
