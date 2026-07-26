"""P1-022: Verify migration result."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Check the 2 migrated contracts
        r = await db.execute(text(
            "SELECT id, number FROM contracts WHERE id IN (15224, 15231)"
        ))
        print("=== Migrated contracts ===")
        for row in r.fetchall():
            print(f"  id={row[0]} number={row[1]!r}")

        # Check no more SG* or UG* patterns
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM contracts WHERE number LIKE 'SG%' OR number LIKE 'UG%'"
        ))
        count = r2.scalar()
        print(f"\n=== Remaining SG*/UG* patterns: {count} ===")

        # Test generate_contract_number
        from contracts.service import generate_contract_number
        num_gdansk, _ = await generate_contract_number(db, "S", branch_id=2)
        print(f"\n=== generate_contract_number test ===")
        print(f"  Gdańsk (branch_id=2): {num_gdansk}")
        num_warsaw, _ = await generate_contract_number(db, "S", branch_id=1)
        print(f"  Warszawa (branch_id=1): {num_warsaw}")
        num_none, _ = await generate_contract_number(db, "S", branch_id=None)
        print(f"  None (branch_id=None): {num_none}")


if __name__ == "__main__":
    asyncio.run(main())
