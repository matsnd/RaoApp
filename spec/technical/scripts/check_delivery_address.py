"""Check delivery_address for contracts in DB (P1-016 investigation)."""
import asyncio
import sys
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Search for S869/2026 or any contract with 869 in number
        r = await db.execute(text(
            "SELECT id, number, delivery_address, contractor_id "
            "FROM contracts WHERE number LIKE '%869%' ORDER BY id DESC LIMIT 10"
        ))
        rows = r.fetchall()
        print(f"Found {len(rows)} contracts with '869' in number:")
        for row in rows:
            print(f"  id={row[0]} number={row[1]} delivery_address=[{row[2]}] contractor_id={row[3]}")

        # Also check recent contracts — how many have empty delivery_address?
        r2 = await db.execute(text(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN delivery_address IS NULL OR delivery_address = '' THEN 1 ELSE 0 END) as empty "
            "FROM contracts"
        ))
        stats = r2.fetchone()
        print(f"\nAll contracts: {stats[0]} total, {stats[1]} with empty delivery_address")

        # Show a few with non-empty delivery_address
        r3 = await db.execute(text(
            "SELECT id, number, delivery_address FROM contracts "
            "WHERE delivery_address IS NOT NULL AND delivery_address != '' "
            "ORDER BY id DESC LIMIT 5"
        ))
        non_empty = r3.fetchall()
        print(f"\nContracts WITH delivery_address ({len(non_empty)} shown):")
        for row in non_empty:
            print(f"  id={row[0]} number={row[1]} delivery_address=[{row[2]}]")


if __name__ == "__main__":
    asyncio.run(main())
