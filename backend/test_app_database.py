import asyncio
from sqlalchemy import text

# Import from actual app
from app.core.database import engine
from app.core.config import get_settings

async def test_app_database():
    settings = get_settings()
    print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")
    print(f"\nTesting engine connection...")
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version(), current_database()"))
            row = result.first()
            print(f"✅ SUCCESS!")
            print(f"   PostgreSQL version: {row[0][:70]}")
            print(f"   Database: {row[1]}")
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"   Error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_app_database())
