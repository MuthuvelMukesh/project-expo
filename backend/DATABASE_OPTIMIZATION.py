"""
CampusIQ — Optimized Database Configuration
Enhanced connection pooling and query options.

Apply these changes to: backend/app/core/database.py
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import get_settings

settings = get_settings()

# ─── OPTIMIZED ENGINE CONFIGURATION ───────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    
    # Connection Pool Tuning
    poolclass=QueuePool,           # Use queue-based pool (better for async)
    pool_size=20,                  # Increase from 10
    max_overflow=40,               # Increase from 20
    pool_pre_ping=True,            # ← TEST connections before reuse (prevents stale connections)
    pool_recycle=3600,             # ← RECYCLE connections after 1 hour (prevents timeout)
    
    # Query Optimization
    future=True,                   # Use SQLAlchemy 2.0 future mode
    execution_options={
        "compiled_cache": None,    # Disable query compilation cache in dev (set to lru_cache in prod)
    }
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency: yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── HEALTH CHECK ───────────────────────────────────────────────────────

async def verify_db_connection():
    """Test database connectivity."""
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
