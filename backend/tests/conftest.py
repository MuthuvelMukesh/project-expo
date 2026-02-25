"""
Pytest configuration and shared fixtures for CampusIQ tests
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient


# ── Test Database Setup ──────────────────────────────────────────

TEST_SQLALCHEMY_DATABASE_URL = (
    "sqlite+aiosqlite:///:memory:"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def override_get_db(db_session):
    """Override FastAPI's get_db dependency."""
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """Create a test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings():
    """Override settings for testing."""
    return Settings(
        DEBUG=True,
        DATABASE_URL=TEST_SQLALCHEMY_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/1",  # Use separate Redis DB for tests
        SECRET_KEY="test-secret-key",
        OLLAMA_BASE_URL="http://localhost:11434",
        OLLAMA_MODEL="gemma:2b",
        LLM_PROVIDER="ollama",
    )


# ── Test Data Factories ──────────────────────────────────────────


@pytest.fixture
async def create_test_user(db_session):
    """Factory to create test users."""
    from app.models.models import User, UserRole
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    async def _create_user(
        email: str = "test@campusiq.edu",
        password: str = "testpassword123",
        role: UserRole = UserRole.STUDENT,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            hashed_password=pwd_context.hash(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
async def create_test_student(db_session, create_test_user):
    """Factory to create test students."""
    from app.models.models import Student, Department, UserRole

    async def _create_student(
        email: str = "student1@campusiq.edu",
        roll_number: str = "CSE001",
        semester: int = 1,
        section: str = "A",
        cgpa: float = 8.5,
    ) -> Student:
        # Create department if needed
        dept_query = "SELECT * FROM departments WHERE code = 'CSE' LIMIT 1"
        dept = await db_session.execute(dept_query)
        if not dept:
            from app.models.models import Department

            dept = Department(
                name="Computer Science and Engineering",
                code="CSE",
                head_faculty_id=None,
            )
            db_session.add(dept)
            await db_session.commit()

        # Create user
        user = await create_test_user(email=email, role=UserRole.STUDENT)

        # Create student
        student = Student(
            user_id=user.id,
            roll_number=roll_number,
            department_id=dept.id,
            semester=semester,
            section=section,
            cgpa=cgpa,
        )
        db_session.add(student)
        await db_session.commit()
        await db_session.refresh(student)
        return student

    return _create_student


@pytest.fixture
async def create_test_faculty(db_session, create_test_user):
    """Factory to create test faculty."""
    from app.models.models import Faculty, Department, UserRole

    async def _create_faculty(
        email: str = "faculty1@campusiq.edu",
        employee_id: str = "FAC001",
        designation: str = "Assistant Professor",
    ) -> Faculty:
        # Create department if needed
        dept_query = "SELECT * FROM departments WHERE code = 'CSE' LIMIT 1"
        dept = await db_session.execute(dept_query)
        if not dept:
            from app.models.models import Department

            dept = Department(
                name="Computer Science and Engineering",
                code="CSE",
                head_faculty_id=None,
            )
            db_session.add(dept)
            await db_session.commit()

        # Create user
        user = await create_test_user(email=email, role=UserRole.FACULTY)

        # Create faculty
        faculty = Faculty(
            user_id=user.id,
            employee_id=employee_id,
            department_id=dept.id,
            designation=designation,
        )
        db_session.add(faculty)
        await db_session.commit()
        await db_session.refresh(faculty)
        return faculty

    return _create_faculty


# ── Auth Helpers ──────────────────────────────────────────────────


@pytest.fixture
def create_access_token():
    """Factory to create JWT tokens for testing."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    def _create_token(
        user_id: int,
        email: str,
        role: str = "student",
        expires_in_minutes: int = 60,
    ) -> str:
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=expires_in_minutes),
        }
        return jwt.encode(
            to_encode, "test-secret-key", algorithm="HS256"
        )

    return _create_token
