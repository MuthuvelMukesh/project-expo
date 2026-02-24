"""
CampusIQ — User Management Routes (Admin)
Full CRUD for users with linked student/faculty profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.core.database import get_db
from app.core.security import hash_password
from app.api.dependencies import require_role
from app.models.models import User, UserRole, Student, Faculty, Department

router = APIRouter()


@router.get("/")
async def list_users(
    role: str = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users with their profile info."""
    stmt = select(User).order_by(User.created_at.desc())
    if role:
        stmt = stmt.where(User.role == role)
    result = await db.execute(stmt)
    users = result.scalars().all()

    user_list = []
    for u in users:
        detail = {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }

        # Attach profile info
        if u.role == UserRole.STUDENT or u.role == "student":
            sp = await db.execute(select(Student).where(Student.user_id == u.id))
            student = sp.scalar_one_or_none()
            if student:
                dept = await db.execute(select(Department).where(Department.id == student.department_id))
                dept_obj = dept.scalar_one_or_none()
                detail.update({
                    "roll_number": student.roll_number,
                    "semester": student.semester,
                    "section": student.section,
                    "cgpa": student.cgpa,
                    "department_name": dept_obj.name if dept_obj else None,
                    "department_id": student.department_id,
                })
        elif u.role == UserRole.FACULTY or u.role == "faculty":
            fp = await db.execute(select(Faculty).where(Faculty.user_id == u.id))
            faculty = fp.scalar_one_or_none()
            if faculty:
                dept = await db.execute(select(Department).where(Department.id == faculty.department_id))
                dept_obj = dept.scalar_one_or_none()
                detail.update({
                    "employee_id": faculty.employee_id,
                    "designation": faculty.designation,
                    "department_name": dept_obj.name if dept_obj else None,
                    "department_id": faculty.department_id,
                })

        user_list.append(detail)

    return user_list


@router.post("/", status_code=201)
async def create_user(
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user with linked profile."""
    # Check duplicate email
    existing = await db.execute(select(User).where(User.email == data["email"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data["email"],
        hashed_password=hash_password(data["password"]),
        full_name=data["full_name"],
        role=data["role"],
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    role = data["role"]
    dept_id = data.get("department_id", 1)

    if role == "student":
        roll = data.get("roll_number")
        if not roll:
            count = (await db.execute(select(func.count(Student.id)))).scalar() or 0
            roll = f"STU{datetime.now().year}{count + 1:04d}"
        student = Student(
            user_id=user.id,
            roll_number=roll,
            department_id=dept_id,
            semester=data.get("semester", 1),
            section=data.get("section", "A"),
            cgpa=0.0,
            admission_year=datetime.now().year,
        )
        db.add(student)
    elif role == "faculty":
        emp_id = data.get("employee_id")
        if not emp_id:
            count = (await db.execute(select(func.count(Faculty.id)))).scalar() or 0
            emp_id = f"FAC{datetime.now().year}{count + 1:04d}"
        faculty = Faculty(
            user_id=user.id,
            employee_id=emp_id,
            department_id=dept_id,
            designation=data.get("designation", "Assistant Professor"),
        )
        db.add(faculty)

    await db.flush()
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": role}


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Update a user and their linked profile."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "full_name" in data:
        user.full_name = data["full_name"]
    if "is_active" in data:
        user.is_active = data["is_active"]

    # Update linked profile
    if user.role == UserRole.STUDENT or user.role == "student":
        sp = await db.execute(select(Student).where(Student.user_id == user_id))
        student = sp.scalar_one_or_none()
        if student:
            if "department_id" in data:
                student.department_id = data["department_id"]
            if "semester" in data:
                student.semester = data["semester"]
            if "section" in data:
                student.section = data["section"]

    elif user.role == UserRole.FACULTY or user.role == "faculty":
        fp = await db.execute(select(Faculty).where(Faculty.user_id == user_id))
        faculty = fp.scalar_one_or_none()
        if faculty:
            if "department_id" in data:
                faculty.department_id = data["department_id"]
            if "designation" in data:
                faculty.designation = data["designation"]

    await db.flush()
    return {"message": "User updated", "id": user_id}


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete: deactivate a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = not user.is_active
    await db.flush()
    return {"message": f"User {'deactivated' if not user.is_active else 'reactivated'}", "id": user_id}
