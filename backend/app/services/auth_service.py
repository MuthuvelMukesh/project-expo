"""
CampusIQ — Auth Service
User registration, authentication, and token management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from datetime import datetime

from app.models.models import User, UserRole, Student, Faculty, Department
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.schemas import UserCreate, UserLogin, Token, UserOut


async def register_user(db: AsyncSession, data: UserCreate) -> UserOut:
    """Register a new user and auto-create linked profile (Student/Faculty)."""
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Auto-create linked profile based on role
    if data.role == "student" or data.role == UserRole.STUDENT:
        # Get first department as default
        dept_result = await db.execute(select(Department).limit(1))
        default_dept = dept_result.scalar_one_or_none()
        dept_id = default_dept.id if default_dept else 1

        # Generate roll number
        count_result = await db.execute(select(func.count(Student.id)))
        count = count_result.scalar() or 0
        roll = f"STU{datetime.now().year}{count + 1:04d}"

        student = Student(
            user_id=user.id,
            roll_number=roll,
            department_id=dept_id,
            semester=1,
            section="A",
            cgpa=0.0,
            admission_year=datetime.now().year,
        )
        db.add(student)
        await db.flush()

    elif data.role == "faculty" or data.role == UserRole.FACULTY:
        dept_result = await db.execute(select(Department).limit(1))
        default_dept = dept_result.scalar_one_or_none()
        dept_id = default_dept.id if default_dept else 1

        count_result = await db.execute(select(func.count(Faculty.id)))
        count = count_result.scalar() or 0
        emp_id = f"FAC{datetime.now().year}{count + 1:04d}"

        faculty = Faculty(
            user_id=user.id,
            employee_id=emp_id,
            department_id=dept_id,
            designation="Assistant Professor",
        )
        db.add(faculty)
        await db.flush()

    return UserOut.model_validate(user)


async def authenticate_user(db: AsyncSession, data: UserLogin) -> Token:
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return Token(access_token=access_token)
