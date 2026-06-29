"""Audit: Do categorizations actually feed into stats correctly?"""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # 1. Categories — how many articles have NULL categories?
        print("=== 1. ARTICLES — category coverage ===")
        r = await db.execute(text(
            "SELECT "
            "SUM(category_main IS NOT NULL) as has_main, "
            "SUM(category_sub1 IS NOT NULL) as has_sub1, "
            "SUM(category_sub2 IS NOT NULL) as has_sub2, "
            "SUM(category_sub3 IS NOT NULL) as has_sub3, "
            "COUNT(*) as total "
            "FROM articles"
        ))
        row = r.fetchone()
        print(f"  total={row[4]}  main={row[0]}  sub1={row[1]}  sub2={row[2]}  sub3={row[3]}")
        print(f"  main coverage: {row[0]}/{row[4]} = {100*row[0]/row[4]:.1f}%")

        # Articles without category_main — are they in contracts?
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM contract_positions cp "
            "JOIN articles a ON a.id = cp.article_id "
            "WHERE a.category_main IS NULL"
        ))
        uncat_in_contracts = r2.scalar()
        print(f"  Positions with articles lacking category_main: {uncat_in_contracts}")

        # 2. is_service — consistency
        print("\n=== 2. IS_SERVICE — consistency ===")
        r = await db.execute(text(
            "SELECT is_service, COUNT(*) FROM articles GROUP BY is_service"
        ))
        for row in r.fetchall():
            print(f"  is_service={row[0]} count={row[1]}")

        # Articles with is_service=1 but in contract_positions (should they be in /top-machines?)
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM contract_positions cp "
            "JOIN articles a ON a.id = cp.article_id WHERE a.is_service = 1"
        ))
        svc_in_pos = r2.scalar()
        print(f"  Service articles in contract_positions: {svc_in_pos}")

        # 3. is_external — does stats handle it?
        print("\n=== 3. IS_EXTERNAL — coverage + stats handling ===")
        r = await db.execute(text(
            "SELECT is_external, COUNT(*) FROM articles GROUP BY is_external"
        ))
        for row in r.fetchall():
            print(f"  is_external={row[0]} count={row[1]}")

        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM contract_positions cp "
            "JOIN articles a ON a.id = cp.article_id WHERE a.is_external = 1"
        ))
        ext_in_pos = r2.scalar()
        print(f"  External articles in contract_positions: {ext_in_pos}")

        # 4. Branch (G suffix) — is there a stats-by-branch endpoint?
        print("\n=== 4. BRANCH — does stats use it? ===")
        r = await db.execute(text(
            "SELECT branch_id, COUNT(*) FROM contracts GROUP BY branch_id"
        ))
        for row in r.fetchall():
            print(f"  branch_id={row[0]} contracts={row[1]}")

        # Contracts with G in number but branch_id=NULL
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM contracts "
            "WHERE number REGEXP '[0-9]G$' AND branch_id IS NULL"
        ))
        g_no_branch = r2.scalar()
        print(f"  Contracts with G suffix but branch_id=NULL: {g_no_branch}")
        print(f"  → These won't show up in any stats-by-branch filter!")

        # 5. contract_type (S vs U) — does stats distinguish?
        print("\n=== 5. CONTRACT_TYPE (S/U) — stats distinction ===")
        r = await db.execute(text(
            "SELECT contract_type, COUNT(*) FROM contracts GROUP BY contract_type"
        ))
        for row in r.fetchall():
            print(f"  type={row[0]!r} count={row[1]}")

        # 6. Check what /by-category actually groups by
        print("\n=== 6. /by-category — what categories exist? ===")
        r = await db.execute(text(
            "SELECT category_main, COUNT(*) as cnt FROM articles "
            "WHERE category_main IS NOT NULL "
            "GROUP BY category_main ORDER BY cnt DESC LIMIT 15"
        ))
        for row in r.fetchall():
            print(f"  {row[0]!r}: {row[1]} articles")

        # 7. Revenue by category — does it match total?
        print("\n=== 7. Revenue coverage by category ===")
        r = await db.execute(text(
            "SELECT "
            "SUM(CASE WHEN a.category_main IS NOT NULL THEN 1 ELSE 0 END) as with_cat, "
            "SUM(CASE WHEN a.category_main IS NULL THEN 1 ELSE 0 END) as without_cat, "
            "COUNT(*) as total "
            "FROM contract_positions cp JOIN articles a ON a.id = cp.article_id"
        ))
        row = r.fetchone()
        print(f"  Positions with category: {row[0]}/{row[2]} ({100*row[0]/row[2]:.1f}%)")
        print(f"  Positions WITHOUT category: {row[1]} → grouped as '(bez kategorii)' in stats")

        # 8. is_archival × is_service matrix
        print("\n=== 8. IS_ARCHIVAL × IS_SERVICE matrix ===")
        r = await db.execute(text(
            "SELECT is_archival, is_service, COUNT(*) FROM articles "
            "GROUP BY is_archival, is_service ORDER BY is_archival, is_service"
        ))
        for row in r.fetchall():
            label = []
            label.append("archival" if row[0] else "active")
            label.append("service" if row[1] else "machine")
            print(f"  {'+'.join(label)}: {row[2]}")


if __name__ == "__main__":
    asyncio.run(main())
