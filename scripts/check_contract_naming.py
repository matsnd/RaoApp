"""P1-022: Check contract numbers and branch assignments."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Branches
        r = await db.execute(text("SELECT id, name FROM branches ORDER BY id"))
        print("=== Branches ===")
        for row in r.fetchall():
            print(f"  id={row[0]} name={row[1]!r}")

        # Contract number patterns
        r2 = await db.execute(text(
            "SELECT number, contract_type, branch_id FROM contracts "
            "ORDER BY number LIMIT 30"
        ))
        print("\n=== Sample 30 contracts (number, type, branch_id) ===")
        for row in r2.fetchall():
            print(f"  {row[0]:20s} type={row[1]} branch_id={row[2]}")

        # Find SG* pattern (incorrect)
        r3 = await db.execute(text(
            "SELECT id, number, contract_type, branch_id FROM contracts "
            "WHERE number LIKE 'SG%' OR number LIKE 'UG%' "
            "ORDER BY number"
        ))
        sg_rows = r3.fetchall()
        print(f"\n=== Contracts with SG*/UG* pattern (INCORRECT): {len(sg_rows)} ===")
        for row in sg_rows:
            print(f"  id={row[0]} number={row[1]!r} type={row[2]} branch_id={row[3]}")

        # Find *G pattern at end (correct Gdańsk)
        r4 = await db.execute(text(
            "SELECT id, number, contract_type, branch_id FROM contracts "
            "WHERE number REGEXP '[0-9]G$' "
            "ORDER BY number LIMIT 20"
        ))
        print(f"\n=== Contracts with G at end (correct Gdańsk): ===")
        for row in r4.fetchall():
            print(f"  id={row[0]} number={row[1]!r} type={row[2]} branch_id={row[3]}")

        # Contracts with branch_id but no G suffix
        r5 = await db.execute(text(
            "SELECT id, number, branch_id FROM contracts "
            "WHERE branch_id IS NOT NULL AND number NOT REGEXP '[0-9]G$' "
            "ORDER BY number LIMIT 20"
        ))
        print(f"\n=== Contracts with branch_id but NO G suffix: ===")
        for row in r5.fetchall():
            print(f"  id={row[0]} number={row[1]!r} branch_id={row[2]}")

        # Contracts with G suffix but branch_id NULL
        r6 = await db.execute(text(
            "SELECT id, number, branch_id FROM contracts "
            "WHERE number REGEXP '[0-9]G$' AND branch_id IS NULL "
            "ORDER BY number LIMIT 20"
        ))
        print(f"\n=== Contracts with G suffix but branch_id NULL: ===")
        for row in r6.fetchall():
            print(f"  id={row[0]} number={row[1]!r} branch_id={row[2]}")


if __name__ == "__main__":
    asyncio.run(main())
