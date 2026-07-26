"""Audit: investigate duplicate contract numbers origin."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Duplicate "111"
        r = await db.execute(text(
            "SELECT id, number, auto_number, contract_type, created_at, "
            "date_from, date_to, contractor_name FROM contracts "
            "WHERE number IN ('111', 'S142/2026') ORDER BY number, id"
        ))
        print("=== Duplicate contracts detail ===")
        for row in r.fetchall():
            print(f"  id={row[0]} number={row[1]!r} auto={row[2]} type={row[3]} created={row[4]} from={row[5]} to={row[6]} contractor={row[7]!r}")

        # Duplicate auto_numbers 397-401
        r2 = await db.execute(text(
            "SELECT id, number, auto_number, contract_type, created_at, contractor_name "
            "FROM contracts WHERE auto_number IN (397, 398, 399, 400, 401) "
            "ORDER BY auto_number, id"
        ))
        print("\n=== Duplicate auto_numbers 397-401 detail ===")
        for row in r2.fetchall():
            print(f"  id={row[0]} number={row[1]!r} auto={row[2]} type={row[3]} created={row[4]} contractor={row[5]!r}")

        # Check max auto_number vs total
        r3 = await db.execute(text("SELECT MAX(auto_number), COUNT(*) FROM contracts"))
        row = r3.fetchone()
        print(f"\n=== Max auto_number={row[0]}, total={row[1]} ===")
        print(f"  Gap: {row[0] - row[1]} (suggests duplicates or deletes)")


if __name__ == "__main__":
    asyncio.run(main())
