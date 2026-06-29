"""RAO-P0-030: Fix duplicate contract numbers before adding UNIQUE constraint.

Strategy:
- For duplicate '111': both are type S, same contractor, same dates → one is a true duplicate.
  Keep the older one (lower id), rename the newer to next available number.
- For duplicate 'S142/2026': one is type U (id=15238), one is type S (id=15239).
  They are different contract types — rename the S one to next available S number.
- For duplicate auto_numbers (397-401): these are from different years (2025 vs 2026).
  The 2026 ones (id=15488-15492) should get new auto_numbers.
"""
import sys, io, asyncio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, ".")
from database import AsyncSessionLocal
from sqlalchemy import text


async def main():
    async with AsyncSessionLocal() as db:
        # Step 1: Fix duplicate '111' — rename id=10207 to next available
        r = await db.execute(text(
            "SELECT MAX(auto_number) FROM contracts WHERE contract_type = 'S'"
        ))
        max_s = r.scalar() or 0
        new_auto = max_s + 1
        year = 2025  # created in 2025
        new_number = f"S{new_auto}/{year}"
        print(f"Renaming contract id=10207 (dup '111') → number='{new_number}' auto_number={new_auto}")
        await db.execute(text(
            "UPDATE contracts SET number = :num, auto_number = :auto WHERE id = 10207"
        ), {"num": new_number, "auto": new_auto})

        # Step 2: Fix duplicate 'S142/2026' — rename id=15239 (type S) to next available S
        r2 = await db.execute(text(
            "SELECT MAX(auto_number) FROM contracts"
        ))
        max_all = r2.scalar() or 0
        new_auto2 = max_all + 1
        new_number2 = f"S{new_auto2}/2026"
        print(f"Renaming contract id=15239 (dup 'S142/2026') → number='{new_number2}' auto_number={new_auto2}")
        await db.execute(text(
            "UPDATE contracts SET number = :num, auto_number = :auto WHERE id = 15239"
        ), {"num": new_number2, "auto": new_auto2})

        # Step 3: Fix duplicate auto_numbers 397-401 (2026 contracts id=15488-15492)
        # These have auto_number=397-401 but should have unique values
        current_max = max_all + 2  # after step 2
        for cid in [15488, 15489, 15490, 15491, 15492]:
            r3 = await db.execute(text(
                "SELECT number, auto_number FROM contracts WHERE id = :id"
            ), {"id": cid})
            row = r3.fetchone()
            if not row:
                continue
            old_num = row[0]
            old_auto = row[1]
            # Extract the numeric part from the number (e.g. "S397/2026G" → 397)
            # and renumber to current_max
            new_auto3 = current_max
            # Rebuild number: replace the old auto with new
            # e.g. "S397/2026G" → "S{new_auto3}/2026G"
            import re
            new_num = re.sub(r'^S\d+/', f'S{new_auto3}/', old_num)
            print(f"Renaming contract id={cid} auto {old_auto}→{new_auto3} number '{old_num}'→'{new_num}'")
            await db.execute(text(
                "UPDATE contracts SET auto_number = :auto, number = :num WHERE id = :id"
            ), {"auto": new_auto3, "num": new_num, "id": cid})
            current_max += 1

        await db.commit()
        print("\n=== Commit complete ===")

        # Verify: no more duplicates
        r4 = await db.execute(text(
            "SELECT number, COUNT(*) FROM contracts GROUP BY number HAVING COUNT(*) > 1"
        ))
        dups = r4.fetchall()
        print(f"Duplicate numbers after fix: {len(dups)}")
        for d in dups:
            print(f"  {d[0]!r}: {d[1]}")

        r5 = await db.execute(text(
            "SELECT auto_number, COUNT(*) FROM contracts WHERE auto_number IS NOT NULL "
            "GROUP BY auto_number HAVING COUNT(*) > 1"
        ))
        auto_dups = r5.fetchall()
        print(f"Duplicate auto_numbers after fix: {len(auto_dups)}")
        for d in auto_dups:
            print(f"  auto={d[0]}: {d[1]}")


if __name__ == "__main__":
    asyncio.run(main())
