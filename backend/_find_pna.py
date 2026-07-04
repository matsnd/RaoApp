"""Znajdź dobre PNA (prawdziwe miasta) dla demo (tymczasowy)."""
import asyncio, sys
import sqlalchemy as sa
sys.stdout.reconfigure(encoding='utf-8')
from database import AsyncSessionLocal
import contracts.models, articles.models, settings.models, settlements.models, integrations.fakturownia.models, audit.models, contract_costs.models, archive.models, reservations.models  # noqa

CITIES = ['Warszawa', 'Kraków', 'Poznań', 'Wrocław', 'Łódź', 'Gdynia', 'Gdańsk', 'Katowice', 'Bydgoszcz', 'Lublin', 'Szczecin', 'Radom']

async def run():
    async with AsyncSessionLocal() as db:
        for c in CITIES:
            r = await db.execute(sa.text(
                "SELECT postal_code, city, gmina, powiat FROM postal_codes WHERE city = :c ORDER BY postal_code LIMIT 3"
            ), {"c": c})
            rows = r.fetchall()
            sys.stdout.write(f'{c}: ' + '; '.join(f'{x[0]}->{x[1]}/{x[2]}/{x[3]}' for x in rows) + '\n')

asyncio.run(run())
