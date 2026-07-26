"""RAO-P2-071: Seed postal_codes from CSV (Spis PNA Poczty Polskiej).

Wyciągnięte z migrate.py step9 — standalone skrypt dla czystej bazy.
Idempotentny (INSERT IGNORE).

Użycie:
    cd backend && python seed_postal_codes.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
import csv
import os
from pathlib import Path

from database import AsyncSessionLocal
import integrations.models  # noqa — PostalCode model
from integrations.models import PostalCode


async def main():
    csv_path = Path(__file__).parent / "data" / "postal_codes.csv"
    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found")
        return

    print(f"Seeding postal_codes from {csv_path}...")
    inserted = 0
    async with AsyncSessionLocal() as db:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) < 2:
                    continue
                code = row[0].strip()
                city = row[1].strip()
                gmina = row[2].strip() if len(row) > 2 and row[2].strip() else None
                powiat = row[3].strip() if len(row) > 3 and row[3].strip() else None
                wojewodztwo = row[4].strip() if len(row) > 4 and row[4].strip() else None
                if code and city:
                    existing = await db.execute(
                        PostalCode.__table__.select().where(PostalCode.postal_code == code).limit(1)
                    )
                    if not existing.first():
                        db.add(PostalCode(
                            postal_code=code, city=city, gmina=gmina,
                            powiat=powiat, wojewodztwo=wojewodztwo,
                        ))
                        inserted += 1
                        if inserted % 1000 == 0:
                            await db.commit()
                            print(f"  {inserted}...")
        await db.commit()
    print(f"DONE — {inserted} postal codes seeded")


if __name__ == "__main__":
    asyncio.run(main())
