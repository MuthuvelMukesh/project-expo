import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_sqlalchemy():
    # Test with different SSL modes
    urls = [
        "postgresql+asyncpg://campusiq:campusiq_secret@127.0.0.1:5433/campusiq",
        "postgresql+asyncpg://campusiq:campusiq_secret@127.0.0.1:5433/campusiq?ssl=disable",
        "postgresql+asyncpg://campusiq:campusiq_secret@127.0.0.1:5433/campusiq?ssl=prefer",
    ]
    
    for url in urls:
        print(f"\nTesting: {url}")
        try:
            engine = create_async_engine(url, echo=False)
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ SUCCESS: {version[:50]}")
            await engine.dispose()
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}: {str(e)[:100]}")

if __name__ == "__main__":
    asyncio.run(test_sqlalchemy())
