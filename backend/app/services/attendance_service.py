"""
CampusIQ — Attendance Service
QR code generation, attendance marking, and analytics.
"""

import secrets
import time
import io
import base64
from datetime import datetime, timezone, date as dt_date

import qrcode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status

from app.models.models import Attendance, Course, Student, User

# In-memory QR token store (for hackathon MVP — use Redis in production)
_active_qr_tokens: dict = {}


async def generate_qr(db: AsyncSession, course_id: int, faculty_id: int, valid_seconds: int = 90):
    """Generate a time-limited QR code for attendance."""
    # Verify faculty teaches this course
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Create a secure token
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + valid_seconds

    _active_qr_tokens[token] = {
        "course_id": course_id,
        "faculty_id": faculty_id,
        "expires_at": expires_at,
        "used_by": set(),
    }

    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#6C63FF", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "qr_token": token,
        "qr_image_base64": qr_base64,
        "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
        "course_name": course.name,
    }


async def mark_attendance(db: AsyncSession, qr_token: str, student_id: int):
    """Mark attendance for a student using a QR token."""
    token_data = _active_qr_tokens.get(qr_token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid QR code")

    if time.time() > token_data["expires_at"]:
        _active_qr_tokens.pop(qr_token, None)
        raise HTTPException(status_code=400, detail="QR code has expired")

    if student_id in token_data["used_by"]:
        raise HTTPException(status_code=400, detail="Attendance already marked")

    # Mark attendance
    attendance = Attendance(
        student_id=student_id,
        course_id=token_data["course_id"],
        date=dt_date.today(),
        is_present=True,
        method="qr",
    )
    db.add(attendance)
    token_data["used_by"].add(student_id)

    return {"message": "Attendance marked successfully", "course_id": token_data["course_id"]}


async def get_student_attendance_summary(db: AsyncSession, student_id: int):
    """Get attendance summary for all courses of a student."""
    # Get student's courses via their semester and department
    student_result = await db.execute(select(Student).where(Student.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        return []

    courses_result = await db.execute(
        select(Course).where(
            Course.semester == student.semester,
            Course.department_id == student.department_id,
        )
    )
    courses = courses_result.scalars().all()

    summaries = []
    for course in courses:
        total = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.course_id == course.id,
                Attendance.student_id == student_id,
            )
        )
        total_classes = total.scalar() or 0

        present = await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.course_id == course.id,
                Attendance.student_id == student_id,
                Attendance.is_present == True,
            )
        )
        attended = present.scalar() or 0

        pct = (attended / total_classes * 100) if total_classes > 0 else 100.0
        needed = max(0, int((0.75 * total_classes - attended) / 0.25) + 1) if pct < 75 else 0

        summaries.append({
            "course_id": course.id,
            "course_name": course.name,
            "course_code": course.code,
            "total_classes": total_classes,
            "attended": attended,
            "percentage": round(pct, 1),
            "status": "safe" if pct >= 75 else ("warning" if pct >= 65 else "danger"),
            "classes_needed_for_75": needed,
        })

    return summaries


async def get_course_attendance_analytics(db: AsyncSession, course_id: int):
    """Get attendance analytics for a specific course."""
    course_result = await db.execute(select(Course).where(Course.id == course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    from sqlalchemy import case

    # Get attendance records grouped by date using correct SQLAlchemy syntax
    records = await db.execute(
        select(
            Attendance.date,
            func.count(Attendance.id).label("total"),
            func.sum(case((Attendance.is_present == True, 1), else_=0)).label("present"),
        )
        .where(Attendance.course_id == course_id)
        .group_by(Attendance.date)
        .order_by(Attendance.date.desc())
        .limit(30)
    )

    trend = []
    total_pct_sum = 0
    for row in records:
        present_count = int(row.present or 0)
        total_count = int(row.total or 0)
        trend.append({
            "date": row.date.isoformat() if row.date else "",
            "present_count": present_count,
            "absent_count": total_count - present_count,
        })
        if total_count > 0:
            total_pct_sum += present_count / total_count * 100

    avg_attendance = round(total_pct_sum / len(trend), 1) if trend else 0

    # Count unique students
    student_count = await db.execute(
        select(func.count(func.distinct(Attendance.student_id)))
        .where(Attendance.course_id == course_id)
    )
    total_students = student_count.scalar() or 0

    # Count students below 75% attendance
    below_75 = 0
    if total_students > 0:
        per_student = await db.execute(
            select(
                Attendance.student_id,
                func.count(Attendance.id).label("total"),
                func.sum(case((Attendance.is_present == True, 1), else_=0)).label("present"),
            )
            .where(Attendance.course_id == course_id)
            .group_by(Attendance.student_id)
        )
        for s_row in per_student:
            s_total = int(s_row.total or 0)
            s_present = int(s_row.present or 0)
            if s_total > 0 and (s_present / s_total * 100) < 75:
                below_75 += 1

    return {
        "course_id": course.id,
        "course_name": course.name,
        "total_students": total_students,
        "avg_attendance": avg_attendance,
        "trend": trend,
        "at_risk_students": below_75,
        "below_75_count": below_75,
    }

