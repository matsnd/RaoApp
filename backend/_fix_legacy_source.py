"""Jednorazowy cleanup: source=legacy w nowych rozliczeniach → manual (gruba krecha: legacy tylko w archiwum)."""
import asyncio, sys
import sqlalchemy as sa
sys.stdout.reconfigure(encoding='utf-8')
from database import AsyncSessionLocal
import contracts.models, articles.models, settings.models, settlements.models, integrations.fakturownia.models, audit.models, contract_costs.models, archive.models, reservations.models  # noqa

async def run():
    async with AsyncSessionLocal() as db:
        r = await db.execute(sa.text(
            "UPDATE contract_settlements SET source='manual', notes=CONCAT(notes, ' [RAO-P2-067: legacy->manual, gruba krecha]') WHERE source='legacy'"
        ))
        await db.commit()
        print(f"Zmieniono {r.rowcount} rozliczeń legacy → manual")

asyncio.run(run())
