import asyncio, sqlalchemy as sa, sys
from database import AsyncSessionLocal
import contracts.models, articles.models, settings.models, settlements.models, integrations.fakturownia.models, audit.models, contract_costs.models, archive.models, reservations.models

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(sa.text('SELECT id, name FROM articles WHERE is_service = 1 ORDER BY id LIMIT 15'))
        rows = r.fetchall()
        sys.stdout.write('ARTYKULY USLUG (is_service=1) first 15:\n')
        for s in rows:
            sys.stdout.write(f'  id={s[0]} name={repr(s[1])}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM articles WHERE is_service = 1'))
        sys.stdout.write(f'  TOTAL: {r.scalar()}\n\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM service_fee_templates'))
        sys.stdout.write(f'ServiceFeeTemplate: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM service_fee_templates WHERE article_id IS NOT NULL'))
        sys.stdout.write(f'  with article_id: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT id, name, article_id, default_price, preset_id FROM service_fee_templates ORDER BY id LIMIT 10'))
        sys.stdout.write('  sample:\n')
        for t in r.fetchall():
            sys.stdout.write(f'    id={t[0]} name={repr(t[1])} article_id={t[2]} default_price={t[3]} preset_id={t[4]}\n')
        sys.stdout.write('\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM service_fee_template_items'))
        sys.stdout.write(f'ServiceFeeTemplateItem: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM contract_service_fees'))
        sys.stdout.write(f'ContractServiceFee: {r.scalar()}\n')
        r = await db.execute(sa.text('SELECT COUNT(*) FROM archive_contract_service_fees'))
        sys.stdout.write(f'archive_contract_service_fees: {r.scalar()}\n\n')
        r = await db.execute(sa.text('SELECT id, name, contract_type, is_default FROM fee_preset_groups ORDER BY id'))
        sys.stdout.write('FeePresetGroups:\n')
        for g in r.fetchall():
            sys.stdout.write(f'  id={g[0]} name={repr(g[1])} type={g[2]} default={g[3]}\n')
        sys.stdout.flush()

asyncio.run(check())
