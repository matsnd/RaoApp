"""Dump delivery_address values from DB (P1-017 pattern analysis)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import asyncio
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # All distinct delivery_address values
        r = await db.execute(text(
            "SELECT delivery_address, COUNT(*) as cnt FROM contracts "
            "WHERE delivery_address IS NOT NULL AND delivery_address != '' "
            "GROUP BY delivery_address ORDER BY cnt DESC LIMIT 100"
        ))
        rows = r.fetchall()
        print(f"=== {len(rows)} distinct delivery_address values (top 100 by frequency) ===\n")
        for i, row in enumerate(rows, 1):
            print(f"{i:3d}. [{row[1]}x] {row[0]!r}")


if __name__ == "__main__":
    asyncio.run(main())
