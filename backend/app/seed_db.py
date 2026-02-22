"""
CampusIQ — Database Startup Seeder
Called from Dockerfile CMD to initialize DB tables and seed demo data.
Idempotent: checks if data already exists before seeding.

Usage:
    python -m app.seed_db
"""

import asyncio
from sqlalchemy import select, text
from app.core.database import engine, AsyncSessionLocal, Base
from app.models.models import User


async def init_db():
    """Create tables and seed if empty."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Check if already seeded
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            print("✅ Database already seeded — skipping.")
            return

    # Seed fresh data
    print("🌱 First run — seeding database...")
    from app.seed import seed
    await seed()


if __name__ == "__main__":
    asyncio.run(init_db())
