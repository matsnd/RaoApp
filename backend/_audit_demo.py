"""Audyt stanu DB pod demo (tymczasowy skrypt — do usunięcia)."""
import asyncio, sys
import sqlalchemy as sa
sys.stdout.reconfigure(encoding='utf-8')
from database import AsyncSessionLocal
import contracts.models, articles.models, settings.models, settlements.models, integrations.fakturownia.models, audit.models, contract_costs.models, archive.models, reservations.models  # noqa

async def run():
    async with AsyncSessionLocal() as db:
        out = sys.stdout.write
        r = await db.execute(sa.text('SELECT id, enabled, domain_subdomain, api_token_preview FROM fakturownia_settings'))
        rows = r.fetchall()
        out(f'FA settings: {len(rows)} rows\n')
        for row in rows:
            out(f'  id={row[0]} enabled={row[1]} domain={row[2]} preview={row[3]}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM contracts WHERE is_settled=0'))
        out(f'unsettled contracts: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT source, COUNT(*) FROM contract_settlements GROUP BY source'))
        for row in r.fetchall():
            out(f'  settlements source={row[0]}: {row[1]}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM contracts'))
        out(f'contracts total: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT MIN(date_from), MAX(date_to) FROM contracts'))
        row = r.fetchone()
        out(f'contracts date range: {row[0]} .. {row[1]}\n')
        r = await db.execute(sa.text('SELECT id, name, contract_type, is_default FROM fee_preset_groups ORDER BY id'))
        out('FeePresetGroups:\n')
        for row in r.fetchall():
            out(f'  id={row[0]} {row[1]!r} type={row[2]} default={row[3]}\n')
        r = await db.execute(sa.text('SELECT preset_id, COUNT(*) FROM service_fee_templates GROUP BY preset_id'))
        for row in r.fetchall():
            out(f'  templates in preset {row[0]}: {row[1]}\n')
        r = await db.execute(sa.text('SELECT id, name, nip, city FROM company LIMIT 3'))
        out('Company:\n')
        for row in r.fetchall():
            out(f'  id={row[0]} name={row[1]!r} nip={row[2]} city={row[3]}\n')
        r = await db.execute(sa.text('SELECT id, name FROM rate_types ORDER BY id'))
        out('RateTypes:\n')
        for row in r.fetchall():
            out(f'  id={row[0]} {row[1]!r}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM postal_codes'))
        out(f'postal_codes: {r.scalar()}\n')
        r = await db.execute(sa.text("SELECT postal_code, city FROM postal_codes WHERE postal_code IN ('02-100','30-001','61-001','50-001','93-001','81-001','40-001','85-001','00-001') ORDER BY postal_code"))
        out('PNA lookup (kontrahenci demo):\n')
        for row in r.fetchall():
            out(f'  {row[0]} -> {row[1]}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM salespeople'))
        out(f'salespeople: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM archive_contracts'))
        out(f'archive_contracts: {r.scalar()}\n')

asyncio.run(run())
