"""Audit: Category name duplicates (case/spacing) + branch stats gap."""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # 1. Category duplicates — normalized (lowercase + stripped)
        print("=== 1. CATEGORY DUPLICATES (normalized) ===")
        r = await db.execute(text(
            "SELECT LOWER(TRIM(category_main)) as norm, "
            "GROUP_CONCAT(DISTINCT category_main SEPARATOR ' | ') as variants, "
            "COUNT(*) as total "
            "FROM articles WHERE category_main IS NOT NULL "
            "GROUP BY LOWER(TRIM(category_main)) "
            "HAVING COUNT(DISTINCT category_main) > 1 "
            "ORDER BY total DESC"
        ))
        dups = r.fetchall()
        print(f"  Categories with duplicate variants: {len(dups)}")
        for row in dups:
            print(f"  '{row[0]}' ({row[2]} articles): {row[1]}")

        # 2. Revenue impact — how much revenue is split across duplicates
        print("\n=== 2. REVENUE IMPACT of category duplicates ===")
        r = await db.execute(text(
            "SELECT a.category_main, COUNT(DISTINCT cp.id) as positions, "
            "COUNT(DISTINCT c.id) as contracts "
            "FROM contract_positions cp "
            "JOIN articles a ON a.id = cp.article_id "
            "JOIN contracts c ON c.id = cp.contract_id "
            "WHERE a.category_main IS NOT NULL "
            "GROUP BY a.category_main ORDER BY positions DESC LIMIT 20"
        ))
        for row in r.fetchall():
            print(f"  {row[0]!r}: {row[1]} positions in {row[2]} contracts")

        # 3. Is there a stats-by-branch endpoint?
        print("\n=== 3. STATS-BY-BRANCH — does it exist? ===")
        # Check stats router for branch
        r = await db.execute(text(
            "SELECT branch_id, COUNT(*) as cnt FROM contracts "
            "GROUP BY branch_id"
        ))
        print("  Contracts by branch_id:")
        for row in r.fetchall():
            print(f"    branch_id={row[0]}: {row[1]} contracts")

        # G suffix vs branch_id
        r2 = await db.execute(text(
            "SELECT "
            "SUM(number REGEXP '[0-9]G$') as has_g, "
            "SUM(branch_id IS NOT NULL) as has_branch, "
            "SUM(number REGEXP '[0-9]G$' AND branch_id IS NOT NULL) as both, "
            "SUM(number REGEXP '[0-9]G$' AND branch_id IS NULL) as g_no_branch, "
            "SUM(number NOT REGEXP '[0-9]G$' AND branch_id IS NOT NULL) as branch_no_g, "
            "COUNT(*) as total "
            "FROM contracts"
        ))
        row = r2.fetchone()
        print(f"  Contracts with G suffix: {row[0]}")
        print(f"  Contracts with branch_id: {row[1]}")
        print(f"  Both G + branch_id: {row[2]}")
        print(f"  G suffix but NO branch_id: {row[3]} ← can't filter by branch!")
        print(f"  branch_id but NO G suffix: {row[4]}")

        # 4. contract_type S vs U in stats — are they distinguished?
        print("\n=== 4. CONTRACT_TYPE in stats ===")
        # Check if /top-machines filters by contract_type
        r = await db.execute(text(
            "SELECT contract_type, COUNT(*) as cnt, "
            "SUM(CASE WHEN is_settled = 1 THEN 1 ELSE 0 END) as settled "
            "FROM contracts GROUP BY contract_type"
        ))
        for row in r.fetchall():
            print(f"  type={row[0]!r}: {row[1]} contracts, {row[2]} settled")

        # 5. Category sub1 duplicates
        print("\n=== 5. CATEGORY_SUB1 duplicates (normalized) ===")
        r = await db.execute(text(
            "SELECT LOWER(TRIM(category_sub1)) as norm, "
            "GROUP_CONCAT(DISTINCT category_sub1 SEPARATOR ' | ') as variants, "
            "COUNT(*) as total "
            "FROM articles WHERE category_sub1 IS NOT NULL "
            "GROUP BY LOWER(TRIM(category_sub1)) "
            "HAVING COUNT(DISTINCT category_sub1) > 1 "
            "ORDER BY total DESC"
        ))
        sub1_dups = r.fetchall()
        print(f"  sub1 duplicates: {len(sub1_dups)}")
        for row in sub1_dups[:10]:
            print(f"  '{row[0]}' ({row[2]}): {row[1]}")


if __name__ == "__main__":
    asyncio.run(main())
