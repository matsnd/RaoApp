"""Sprawdź strukturę postal_codes — czy miasto ma wiele PNA."""
import asyncio
from database import AsyncSessionLocal
from integrations.models import PostalCode
from sqlalchemy import select, func

async def main():
    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count()).select_from(PostalCode))).scalar()
        print(f"postal_codes total: {total}")

        # Top cities by PNA count
        rows = (await db.execute(
            select(PostalCode.city, func.count())
            .group_by(PostalCode.city)
            .order_by(func.count().desc())
            .limit(10)
        )).all()
        print("\nTop miasta (ile PNA per miasto):")
        for r in rows:
            print(f"  {r[0]}: {r[1]} PNA")

        # Kraków sample
        krakow = (await db.execute(
            select(PostalCode.postal_code, PostalCode.city, PostalCode.wojewodztwo, PostalCode.powiat, PostalCode.gmina)
            .where(PostalCode.city == "Kraków")
            .limit(5)
        )).all()
        print(f"\nKraków sample (5 z {len(krakow)} PNA):")
        for r in krakow:
            print(f"  {r[0]} | woj={r[2]} | pow={r[3]} | gim={r[4]}")

        # Warszawa
        warszawa = (await db.execute(
            select(func.count()).select_from(PostalCode).where(PostalCode.city == "Warszawa")
        )).scalar()
        print(f"\nWarszawa: {warszawa} PNA")

        # Umowy per city w contracts
        from contracts.models import Contract
        contracts_by_city = (await db.execute(
            select(Contract.city, Contract.postal_code, func.count())
            .where(Contract.city.isnot(None))
            .group_by(Contract.city, Contract.postal_code)
            .order_by(func.count().desc())
            .limit(10)
        )).all()
        print("\nUmowy per (city, postal_code):")
        for r in contracts_by_city:
            print(f"  {r[0]} {r[1]}: {r[2]} umów")

asyncio.run(main())
