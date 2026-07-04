"""Sprawdź stan demo data po seedzie RAO-P2-068."""
import asyncio
from database import AsyncSessionLocal
from settings.models import Company, FeePresetGroup, ServiceFeeTemplate, ServiceFeeTemplateItem, RateType
from contracts.models import Contract, ContractPosition, PositionCondition
from sqlalchemy import select, func

# Import wszystkich modeli żeby SQLAlchemy skonfigurowało relacje
import auth.models  # noqa
import contractors.models  # noqa
import articles.models  # noqa
import contracts.models  # noqa
import settings.models  # noqa
import categories.models  # noqa
import settlements.models  # noqa
import archive.models  # noqa
import audit.models  # noqa
import contract_costs.models  # noqa
import deliveries.models  # noqa
import reservations.models  # noqa
import integrations.fakturownia.models  # noqa
import integrations.models  # noqa

async def main():
    async with AsyncSessionLocal() as db:
        # Firma
        c = (await db.execute(select(Company).where(Company.id == 1))).scalar_one_or_none()
        print(f"Firma: name={c.name!r}, nip={c.nip!r}, bank_account={c.bank_account!r}")
        print(f"  header_text={(c.header_text or '')[:80]!r}, numbering_start={c.numbering_start}")

        # Rate types
        rts = (await db.execute(select(RateType).order_by(RateType.id))).scalars().all()
        print(f"\nRate types ({len(rts)}):")
        for rt in rts:
            print(f"  - {rt.name}: {rt.description}")

        # Presets
        groups = (await db.execute(select(FeePresetGroup).order_by(FeePresetGroup.id))).scalars().all()
        print(f"\nZestawy presetów ({len(groups)}):")
        for g in groups:
            tpls = (await db.execute(select(ServiceFeeTemplate).where(ServiceFeeTemplate.preset_id == g.id).order_by(ServiceFeeTemplate.sort_order))).scalars().all()
            print(f"  [{g.contract_type}] {g.name} (default={g.is_default}) — {len(tpls)} szablonów")
            for t in tpls[:3]:
                print(f"      {t.sort_order}. {t.name} | art={t.article_id} | price={t.default_price}")

        # ServiceFeeTemplateItem
        items_count = (await db.execute(select(func.count()).select_from(ServiceFeeTemplateItem))).scalar_one()
        print(f"\nServiceFeeTemplateItem: {items_count} relacji")

        # Warunki kaskadowe — sprawdź pierwszą umowę z pozycjami
        contract = (await db.execute(select(Contract).where(Contract.number == "S001/2025"))).scalar_one_or_none()
        if contract:
            positions = (await db.execute(select(ContractPosition).where(ContractPosition.contract_id == contract.id))).scalars().all()
            for pos in positions:
                conds = (await db.execute(select(PositionCondition).where(PositionCondition.position_id == pos.id).order_by(PositionCondition.id))).scalars().all()
                print(f"\nUmowa S001/2025, pozycja '{pos.article_name}': {len(conds)} warunków kaskadowych")
                for cond in conds:
                    print(f"  rate1={cond.rate1}, rate2={cond.rate2}, period_count={cond.period_count}, label={cond.billing_label}")
                    print(f"  desc: {cond.description}")

asyncio.run(main())
