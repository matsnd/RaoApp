"""RAO-P0-054: Normalize category names — fix diacritics + trailing spaces."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Step 1: Merge 'Ladowarki teleskopowe ' → 'Ładowarki Teleskopowe'
        r = await db.execute(text(
            "UPDATE articles SET category_main = 'Ładowarki Teleskopowe' "
            "WHERE category_main = 'Ladowarki teleskopowe '"
        ))
        print(f"Step 1: Merged 'Ladowarki teleskopowe ' → 'Ładowarki Teleskopowe' ({r.rowcount} rows)")

        # Step 2: TRIM trailing spaces on all categories
        r2 = await db.execute(text(
            "UPDATE articles SET category_main = TRIM(category_main) "
            "WHERE category_main != TRIM(category_main)"
        ))
        print(f"Step 2: TRIM category_main ({r2.rowcount} rows)")

        r3 = await db.execute(text(
            "UPDATE articles SET category_sub1 = TRIM(category_sub1) "
            "WHERE category_sub1 != TRIM(category_sub1)"
        ))
        print(f"Step 3: TRIM category_sub1 ({r3.rowcount} rows)")

        await db.commit()
        print("\n=== Commit complete ===")

        # Verify: no more duplicates
        r4 = await db.execute(text(
            "SELECT category_main, COUNT(*) FROM articles "
            "WHERE category_main IS NOT NULL "
            "GROUP BY category_main ORDER BY COUNT(*) DESC LIMIT 10"
        ))
        print("\n=== Top 10 categories after fix ===")
        for row in r4.fetchall():
            print(f"  {row[0]!r}: {row[1]} articles")

        # Check Ładowarki specifically
        r5 = await db.execute(text(
            "SELECT category_main, COUNT(*) FROM articles "
            "WHERE category_main LIKE '%adowarki%eleskop%' "
            "GROUP BY category_main"
        ))
        print("\n=== Ładowarki teleskopowe after fix ===")
        for row in r5.fetchall():
            print(f"  {row[0]!r}: {row[1]} articles")


if __name__ == "__main__":
    asyncio.run(main())
