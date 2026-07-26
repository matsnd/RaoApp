"""RAO-P0-054: Find all category duplicates and generate normalization SQL."""
import os
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Find all category_main duplicates (case-insensitive + diacritic-insensitive + trimmed)
        # MariaDB doesn't have a simple unaccent function, so we normalize in Python
        r = await db.execute(text(
            "SELECT DISTINCT category_main FROM articles "
            "WHERE category_main IS NOT NULL ORDER BY category_main"
        ))
        all_cats = [row[0] for row in r.fetchall()]
        print(f"=== All distinct category_main values: {len(all_cats)} ===")

        # Group by normalized form (lowercase + strip + remove diacritics)
        import unicodedata
        def normalize(s):
            s = s.strip().lower()
            # Manual replace for Polish chars (NFKD doesn't decompose Ł/ł)
            for k, v in {'ł':'l','Ł':'l','ą':'a','ć':'c','ę':'e','ń':'n',
                         'ó':'o','ś':'s','ż':'z','ź':'z'}.items():
                s = s.replace(k, v)
            return s

        groups = {}
        for cat in all_cats:
            norm = normalize(cat)
            if norm not in groups:
                groups[norm] = []
            groups[norm].append(cat)

        # Find groups with >1 variant
        dups = {k: v for k, v in groups.items() if len(v) > 1}
        print(f"\n=== Duplicate groups: {len(dups)} ===")
        for norm, variants in sorted(dups.items()):
            # Get count per variant
            counts = []
            for v in variants:
                r2 = await db.execute(text(
                    "SELECT COUNT(*) FROM articles WHERE category_main = :cat"
                ), {"cat": v})
                cnt = r2.scalar()
                counts.append((v, cnt))
            print(f"  norm='{norm}'")
            for v, cnt in counts:
                print(f"    {v!r}: {cnt} articles")

        # Also check category_sub1
        r3 = await db.execute(text(
            "SELECT DISTINCT category_sub1 FROM articles "
            "WHERE category_sub1 IS NOT NULL ORDER BY category_sub1"
        ))
        all_sub1 = [row[0] for row in r3.fetchall()]
        groups_sub1 = {}
        for cat in all_sub1:
            norm = normalize(cat)
            if norm not in groups_sub1:
                groups_sub1[norm] = []
            groups_sub1[norm].append(cat)
        dups_sub1 = {k: v for k, v in groups_sub1.items() if len(v) > 1}
        print(f"\n=== category_sub1 duplicate groups: {len(dups_sub1)} ===")
        for norm, variants in sorted(dups_sub1.items()):
            counts = []
            for v in variants:
                r4 = await db.execute(text(
                    "SELECT COUNT(*) FROM articles WHERE category_sub1 = :cat"
                ), {"cat": v})
                cnt = r4.scalar()
                counts.append((v, cnt))
            print(f"  norm='{norm}'")
            for v, cnt in counts:
                print(f"    {v!r}: {cnt} articles")

        # Generate fix SQL — pick canonical form (most common variant)
        print("\n=== FIX SQL ===")
        for norm, variants in sorted(dups.items()):
            # Pick the variant with most articles as canonical
            counts = []
            for v in variants:
                r5 = await db.execute(text(
                    "SELECT COUNT(*) FROM articles WHERE category_main = :cat"
                ), {"cat": v})
                counts.append((v, r5.scalar()))
            counts.sort(key=lambda x: -x[1])
            canonical = counts[0][0]
            for v, _ in counts[1:]:
                if v != canonical:
                    print(f"UPDATE articles SET category_main = '{canonical.replace("'", "''")}' "
                          f"WHERE category_main = '{v.replace("'", "''")}';  -- {norm}")

        for norm, variants in sorted(dups_sub1.items()):
            counts = []
            for v in variants:
                r6 = await db.execute(text(
                    "SELECT COUNT(*) FROM articles WHERE category_sub1 = :cat"
                ), {"cat": v})
                counts.append((v, r6.scalar()))
            counts.sort(key=lambda x: -x[1])
            canonical = counts[0][0]
            for v, _ in counts[1:]:
                if v != canonical:
                    print(f"UPDATE articles SET category_sub1 = '{canonical.replace("'", "''")}' "
                          f"WHERE category_sub1 = '{v.replace("'", "''")}';  -- {norm}")

        # Also TRIM all categories (trailing spaces)
        print("\n=== TRIM SQL ===")
        print("UPDATE articles SET category_main = TRIM(category_main) WHERE category_main != TRIM(category_main);")
        print("UPDATE articles SET category_sub1 = TRIM(category_sub1) WHERE category_sub1 != TRIM(category_sub1);")


if __name__ == "__main__":
    asyncio.run(main())
