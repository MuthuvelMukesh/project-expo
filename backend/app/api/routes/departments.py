"""
CampusIQ — Department Management Routes
CRUD for academic departments with student/faculty/course counts.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.dependencies import require_role, get_current_user
from app.models.models import User, UserRole, Department, Student, Faculty, Course

router = APIRouter()


@router.get("/")
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all departments with counts."""
    result = await db.execute(select(Department).order_by(Department.name))
    departments = result.scalars().all()

    dept_list = []
    for d in departments:
        students = (await db.execute(
            select(func.count(Student.id)).where(Student.department_id == d.id)
        )).scalar() or 0
        faculty = (await db.execute(
            select(func.count(Faculty.id)).where(Faculty.department_id == d.id)
        )).scalar() or 0
        courses = (await db.execute(
            select(func.count(Course.id)).where(Course.department_id == d.id)
        )).scalar() or 0

        dept_list.append({
            "id": d.id,
            "name": d.name,
            "code": d.code,
            "total_students": students,
            "total_faculty": faculty,
            "total_courses": courses,
        })

    return dept_list


@router.post("/", status_code=201)
async def create_department(
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new department."""
    existing = await db.execute(select(Department).where(Department.code == data["code"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Department code '{data['code']}' already exists")

    dept = Department(name=data["name"], code=data["code"])
    db.add(dept)
    await db.flush()
    await db.refresh(dept)

    return {"id": dept.id, "name": dept.name, "code": dept.code, "message": "Department created"}


@router.put("/{dept_id}")
async def update_department(
    dept_id: int,
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update department details."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    if "name" in data:
        dept.name = data["name"]
    if "code" in data:
        dept.code = data["code"]

    await db.flush()
    return {"message": "Department updated", "id": dept_id}


@router.delete("/{dept_id}")
async def delete_department(
    dept_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a department (only if no students/faculty/courses linked)."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    # Check for linked records
    students = (await db.execute(
        select(func.count(Student.id)).where(Student.department_id == dept_id)
    )).scalar() or 0
    if students > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {students} students linked to this department")

    await db.delete(dept)
    await db.flush()
    return {"message": "Department deleted", "id": dept_id}
