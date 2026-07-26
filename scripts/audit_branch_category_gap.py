"""Audit: Branch gap + category collation check."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # G suffix vs branch_id
        r = await db.execute(text(
            "SELECT "
            "SUM(number REGEXP '[0-9]G$') as has_g, "
            "SUM(branch_id IS NOT NULL) as has_branch, "
            "SUM(number REGEXP '[0-9]G$' AND branch_id IS NOT NULL) as g_and_branch, "
            "SUM(number REGEXP '[0-9]G$' AND branch_id IS NULL) as g_no_branch, "
            "COUNT(*) as total "
            "FROM contracts"
        ))
        row = r.fetchone()
        print("=== BRANCH GAP ===")
        print(f"  Contracts with G suffix: {row[0]}")
        print(f"  Contracts with branch_id NOT NULL: {row[1]}")
        print(f"  G + branch_id: {row[2]}")
        print(f"  G but NO branch_id: {row[3]}")
        print(f"  Total: {row[4]}")

        # Category variants — raw
        r2 = await db.execute(text(
            "SELECT category_main, COUNT(*) FROM articles "
            "WHERE category_main LIKE '%adowarki%' "
            "GROUP BY category_main ORDER BY category_main"
        ))
        print("\n=== 'Ładowarki' variants in DB (raw) ===")
        for row in r2.fetchall():
            print(f"  {row[0]!r}: {row[1]} articles")

        # Does polish_ci collation merge them?
        r3 = await db.execute(text(
            "SELECT category_main COLLATE utf8mb4_polish_ci as cat, COUNT(*) FROM articles "
            "WHERE category_main LIKE '%adowarki%' "
            "GROUP BY category_main COLLATE utf8mb4_polish_ci"
        ))
        print("\n=== After COLLATE utf8mb4_polish_ci ===")
        for row in r3.fetchall():
            print(f"  {row[0]!r}: {row[1]} articles")

        # What collation does the column actually use?
        r4 = await db.execute(text(
            "SELECT COLUMN_NAME, COLLATION_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = 'rao_new' AND TABLE_NAME = 'articles' "
            "AND COLUMN_NAME = 'category_main'"
        ))
        print("\n=== Column collation ===")
        for row in r4.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Check if /by-category GROUP BY merges or splits
        r5 = await db.execute(text(
            "SELECT a.category_main, COUNT(DISTINCT cp.id) as pos_count "
            "FROM contract_positions cp JOIN articles a ON a.id = cp.article_id "
            "WHERE a.category_main LIKE '%adowarki%' "
            "GROUP BY a.category_main ORDER BY pos_count DESC"
        ))
        print("\n=== /by-category would show (Ładowarki): ===")
        for row in r5.fetchall():
            print(f"  {row[0]!r}: {row[1]} positions")


if __name__ == "__main__":
    asyncio.run(main())
