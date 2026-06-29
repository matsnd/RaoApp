"""Verify P0-030: UNIQUE index on contracts.number exists."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(
            "SHOW INDEX FROM contracts WHERE Key_name = 'uq_contracts_number'"
        ))
        rows = r.fetchall()
        print(f"UNIQUE index on contracts.number: {'EXISTS' if rows else 'MISSING'}")
        for row in rows:
            print(f"  {row}")


if __name__ == "__main__":
    asyncio.run(main())
