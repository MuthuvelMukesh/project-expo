"""
CampusIQ — Course Management Routes
CRUD for courses with department and instructor assignment.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.dependencies import require_role, get_current_user
from app.models.models import User, UserRole, Course, Department, Faculty

router = APIRouter()


@router.get("/")
async def list_courses(
    department_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all courses with department and instructor details."""
    stmt = select(Course).order_by(Course.semester, Course.code)
    if department_id:
        stmt = stmt.where(Course.department_id == department_id)
    result = await db.execute(stmt)
    courses = result.scalars().all()

    course_list = []
    for c in courses:
        dept = await db.execute(select(Department).where(Department.id == c.department_id))
        dept_obj = dept.scalar_one_or_none()

        instructor_name = None
        if c.instructor_id:
            instr = await db.execute(
                select(Faculty, User)
                .join(User, Faculty.user_id == User.id)
                .where(Faculty.id == c.instructor_id)
            )
            row = instr.first()
            if row:
                instructor_name = row[1].full_name

        course_list.append({
            "id": c.id,
            "code": c.code,
            "name": c.name,
            "department_id": c.department_id,
            "department_name": dept_obj.name if dept_obj else None,
            "semester": c.semester,
            "credits": c.credits,
            "instructor_id": c.instructor_id,
            "instructor_name": instructor_name,
        })

    return course_list


@router.post("/", status_code=201)
async def create_course(
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new course."""
    # Check duplicate code
    existing = await db.execute(select(Course).where(Course.code == data["code"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Course code '{data['code']}' already exists")

    course = Course(
        code=data["code"],
        name=data["name"],
        department_id=data["department_id"],
        semester=data.get("semester", 1),
        credits=data.get("credits", 3),
        instructor_id=data.get("instructor_id"),
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)

    return {"id": course.id, "code": course.code, "name": course.name, "message": "Course created"}


@router.put("/{course_id}")
async def update_course(
    course_id: int,
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update course details."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for field in ["name", "department_id", "semester", "credits", "instructor_id"]:
        if field in data:
            setattr(course, field, data[field])

    await db.flush()
    return {"message": "Course updated", "id": course_id}


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a course."""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await db.delete(course)
    await db.flush()
    return {"message": "Course deleted", "id": course_id}
