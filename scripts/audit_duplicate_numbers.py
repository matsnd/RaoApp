"""Audit: Check for duplicate contract numbers and auto_numbers."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Duplicate numbers
        r = await db.execute(text(
            "SELECT number, COUNT(*) as cnt FROM contracts "
            "GROUP BY number HAVING COUNT(*) > 1 ORDER BY cnt DESC LIMIT 20"
        ))
        dups = r.fetchall()
        print(f"=== Duplicate contract numbers: {len(dups)} groups ===")
        for row in dups[:10]:
            print(f"  number={row[0]!r} count={row[1]}")

        # Duplicate auto_numbers
        r2 = await db.execute(text(
            "SELECT auto_number, COUNT(*) as cnt FROM contracts "
            "WHERE auto_number IS NOT NULL "
            "GROUP BY auto_number HAVING COUNT(*) > 1 ORDER BY cnt DESC LIMIT 20"
        ))
        auto_dups = r2.fetchall()
        print(f"\n=== Duplicate auto_numbers: {len(auto_dups)} groups ===")
        for row in auto_dups[:10]:
            print(f"  auto_number={row[0]} count={row[1]}")

        # Total contracts
        r3 = await db.execute(text("SELECT COUNT(*) FROM contracts"))
        total = r3.scalar()
        print(f"\n=== Total contracts: {total} ===")

        # Null auto_number
        r4 = await db.execute(text("SELECT COUNT(*) FROM contracts WHERE auto_number IS NULL"))
        null_auto = r4.scalar()
        print(f"=== Contracts with NULL auto_number: {null_auto} ===")

        # Null number
        r5 = await db.execute(text("SELECT COUNT(*) FROM contracts WHERE number IS NULL OR number = ''"))
        null_num = r5.scalar()
        print(f"=== Contracts with NULL/empty number: {null_num} ===")


if __name__ == "__main__":
    asyncio.run(main())
