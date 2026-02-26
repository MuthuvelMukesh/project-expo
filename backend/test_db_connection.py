import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='127.0.0.1',
            port=5433,
            user='campusiq',
            password='campusiq_secret',
            database='campusiq',
            ssl=False
        )
        print("✅ Connection successful!")
        version = await conn.fetchval('SELECT version()')
        print(f"PostgreSQL version: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
