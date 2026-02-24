"""
CampusIQ — Timetable Routes
Weekly schedule management for students, faculty, and admins.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.api.dependencies import get_current_user, require_role
from app.models.models import Timetable, Course, Faculty, Student, User
from app.schemas.schemas import TimetableSlotCreate, TimetableSlotOut

router = APIRouter()


def _build_slot_out(slot, course, instructor_name=""):
    """Build a TimetableSlotOut from a Timetable row + Course."""
    return TimetableSlotOut(
        id=slot.id,
        course_id=slot.course_id,
        course_name=course.name if course else "",
        course_code=course.code if course else "",
        instructor_name=instructor_name,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        room=slot.room,
        class_type=slot.class_type,
    )


@router.get("/student", response_model=list[TimetableSlotOut])
async def get_student_timetable(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current student's weekly timetable based on enrolled courses."""
    if user.role.value != "student":
        raise HTTPException(status_code=403, detail="Students only")

    # Get student's department courses for their semester
    student_result = await db.execute(
        select(Student).where(Student.user_id == user.id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Courses in student's department + semester
    course_result = await db.execute(
        select(Course).where(
            Course.department_id == student.department_id,
            Course.semester == student.semester,
        )
    )
    courses = {c.id: c for c in course_result.scalars().all()}
    if not courses:
        return []

    # Get timetable entries for those courses
    slots_result = await db.execute(
        select(Timetable).where(Timetable.course_id.in_(courses.keys()))
        .order_by(Timetable.day_of_week, Timetable.start_time)
    )

    result = []
    for slot in slots_result.scalars().all():
        course = courses.get(slot.course_id)
        # Get instructor name
        instructor_name = ""
        if course and course.instructor_id:
            fac_result = await db.execute(
                select(Faculty).where(Faculty.id == course.instructor_id)
            )
            fac = fac_result.scalar_one_or_none()
            if fac:
                user_result = await db.execute(
                    select(User).where(User.id == fac.user_id)
                )
                fac_user = user_result.scalar_one_or_none()
                instructor_name = fac_user.full_name if fac_user else ""
        result.append(_build_slot_out(slot, course, instructor_name))

    return result


@router.get("/faculty", response_model=list[TimetableSlotOut])
async def get_faculty_timetable(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current faculty's weekly timetable."""
    if user.role.value != "faculty":
        raise HTTPException(status_code=403, detail="Faculty only")

    fac_result = await db.execute(
        select(Faculty).where(Faculty.user_id == user.id)
    )
    fac = fac_result.scalar_one_or_none()
    if not fac:
        raise HTTPException(status_code=404, detail="Faculty profile not found")

    # Courses this faculty teaches
    course_result = await db.execute(
        select(Course).where(Course.instructor_id == fac.id)
    )
    courses = {c.id: c for c in course_result.scalars().all()}
    if not courses:
        return []

    slots_result = await db.execute(
        select(Timetable).where(Timetable.course_id.in_(courses.keys()))
        .order_by(Timetable.day_of_week, Timetable.start_time)
    )

    return [
        _build_slot_out(slot, courses.get(slot.course_id), user.full_name)
        for slot in slots_result.scalars().all()
    ]


@router.post("/", response_model=TimetableSlotOut)
async def create_timetable_slot(
    data: TimetableSlotCreate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a timetable entry."""
    # Verify course exists
    course_result = await db.execute(select(Course).where(Course.id == data.course_id))
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    slot = Timetable(
        course_id=data.course_id,
        day_of_week=data.day_of_week,
        start_time=data.start_time,
        end_time=data.end_time,
        room=data.room,
        class_type=data.class_type,
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)

    instructor_name = ""
    if course.instructor_id:
        fac_r = await db.execute(select(Faculty).where(Faculty.id == course.instructor_id))
        fac = fac_r.scalar_one_or_none()
        if fac:
            u_r = await db.execute(select(User).where(User.id == fac.user_id))
            u = u_r.scalar_one_or_none()
            instructor_name = u.full_name if u else ""

    return _build_slot_out(slot, course, instructor_name)


@router.delete("/{slot_id}")
async def delete_timetable_slot(
    slot_id: int,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes a timetable entry."""
    result = await db.execute(select(Timetable).where(Timetable.id == slot_id))
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Schedule entry not found")
    await db.delete(slot)
    await db.commit()
    return {"detail": "Schedule entry deleted"}
