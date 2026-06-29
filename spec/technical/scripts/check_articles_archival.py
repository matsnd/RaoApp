"""Quick check: articles archival breakdown."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text(
            "SELECT is_archival, is_service, is_external, COUNT(*) "
            "FROM articles GROUP BY is_archival, is_service, is_external "
            "ORDER BY is_archival, is_service, is_external"
        ))
        print("is_archival | is_service | is_external | count")
        print("-" * 50)
        for row in r.fetchall():
            print(f"  {row[0]:>10} | {row[1]:>10} | {row[2]:>11} | {row[3]}")

        # Active (non-archival) machines
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM articles WHERE is_archival=0 AND is_service=0 AND is_external=0"
        ))
        print(f"\nActive machines (is_archival=0, is_service=0, is_external=0): {r2.scalar()}")

        # Sample 5 active machines
        r3 = await db.execute(text(
            "SELECT id, name, internal_number, is_archival, is_service, is_external "
            "FROM articles WHERE is_service=0 LIMIT 5"
        ))
        print("\nSample 5 non-service articles:")
        for row in r3.fetchall():
            print(f"  id={row[0]} name={row[1]!r} num={row[2]} arch={row[3]} svc={row[4]} ext={row[5]}")


if __name__ == "__main__":
    asyncio.run(main())
