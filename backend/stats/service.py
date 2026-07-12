from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from contractors.models import Contractor
from contracts.models import Contract
from settlements.models import ContractSettlement
from settings.models import Salesperson
from shared.revenue import compute_position_revenues


_CENT = Decimal("0.01")


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(_CENT, rounding=ROUND_HALF_UP)


def calculate_commission_base(
    *,
    settlement_client: Decimal | None,
    settlement_company: Decimal | None,
    fallback_revenue: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (client cost, company cost, commission base).

    Only complete settlement rows are a source of truth for commission.  When
    there is no complete settlement, this deliberately falls back to computed
    revenue.  A complete settlement whose margin is zero is still authoritative
    and must not trigger the fallback. Partial settlement values cannot be used
    to manufacture a margin from incomplete data.
    """
    client = _money(settlement_client)
    company = _money(settlement_company)
    if settlement_client is not None and settlement_company is not None:
        return client, company, client - company
    return client, company, _money(fallback_revenue)


async def get_salesperson_commission_contracts(
    db: AsyncSession,
    salesperson_id: int,
    date_from: date | None,
    date_to: date | None,
    *,
    salesperson: Salesperson | None = None,
) -> list[dict]:
    """Fetch one commission drill-down row per contract with no N+1 queries.

    ``salesperson`` may be supplied by the router to avoid a second lookup.
    Direct service callers still get the same active-salesperson validation.
    """
    date_conditions = []
    if date_to is not None:
        date_conditions.append(
            or_(Contract.date_from.is_(None), Contract.date_from <= date_to)
        )
    if date_from is not None:
        date_conditions.append(
            or_(Contract.date_to.is_(None), Contract.date_to >= date_from)
        )

    if salesperson is None:
        salesperson = await db.scalar(
            select(Salesperson).where(
                Salesperson.id == salesperson_id,
                Salesperson.is_active == True,
            )
        )
    if salesperson is None or not salesperson.is_active:
        raise HTTPException(status_code=404, detail="Handlowiec nie istnieje")

    settlement_q = (
        select(
            Contract.id.label("contract_id"),
            Contract.number,
            Contract.date_from,
            Contract.date_to,
            Contractor.name.label("contractor_name_from_table"),
            Contract.contractor_name.label("contractor_name_snapshot"),
            Salesperson.commission_rate,
            ContractSettlement.cost_client.label("settlement_client"),
            ContractSettlement.cost_company.label("settlement_company"),
        )
        .select_from(Contract)
        .outerjoin(Contractor, Contractor.id == Contract.contractor_id)
        .join(Salesperson, Salesperson.id == Contract.salesperson_id)
        .outerjoin(ContractSettlement, ContractSettlement.contract_id == Contract.id)
        .where(Contract.salesperson_id == salesperson_id)
        .where(and_(*date_conditions) if date_conditions else True)
        .order_by(Contract.date_from, Contract.number)
    )
    result = await db.execute(settlement_q)
    settlement_rows = result.all()
    if not settlement_rows:
        return []

    contracts: dict[int, dict] = {}
    for row in settlement_rows:
        contract = contracts.setdefault(row.contract_id, {
            "contract_id": row.contract_id,
            "number": row.number,
            "date_from": row.date_from,
            "date_to": row.date_to,
            "contractor_name": row.contractor_name_from_table or row.contractor_name_snapshot,
            "commission_rate": row.commission_rate,
            "cost_client": Decimal("0.00"),
            "cost_company": Decimal("0.00"),
            "complete_settlements": 0,
        })
        if row.settlement_client is not None and row.settlement_company is not None:
            contract["cost_client"] += _money(row.settlement_client)
            contract["cost_company"] += _money(row.settlement_company)
            contract["complete_settlements"] += 1

    rows = list(contracts.values())
    contract_ids = set(contracts)
    # The contract query above already applies the overlap filter. Passing no
    # date filter here keeps open-ended contracts consistent without touching
    # shared/revenue.py, while contract_ids still bounds the fallback query.
    position_revenues = await compute_position_revenues(
        db, None, None, contract_ids=contract_ids
    )
    fallback_by_contract: dict[int, Decimal] = {}
    for position in position_revenues:
        fallback_by_contract[position["contract_id"]] = (
            fallback_by_contract.get(position["contract_id"], Decimal("0"))
            + _money(position.get("revenue"))
        )

    items = []
    for row in rows:
        has_complete_settlement = bool(row["complete_settlements"])
        fallback_revenue = fallback_by_contract.get(row["contract_id"], Decimal("0"))
        if has_complete_settlement:
            client = _money(row["cost_client"])
            company = _money(row["cost_company"])
            base = client - company
        else:
            # Existing report policy: no complete settlement means revenue fallback.
            # Never use this path when even one complete company-cost row exists.
            client = fallback_revenue
            company = Decimal("0.00")
            base = fallback_revenue
        rate = _money(row["commission_rate"]) if row["commission_rate"] is not None else None
        commission = _money(base * (rate or Decimal("0")) / Decimal("100"))
        items.append({
            "contract_id": row["contract_id"],
            "number": row["number"],
            "date_from": row["date_from"],
            "date_to": row["date_to"],
            "contractor_name": row["contractor_name"],
            "total_revenue": client,
            "total_company_cost": company,
            "earnings": base,
            "margin": base,
            "commission_rate": rate,
            "commission_amount": commission,
            "fallback_applied": not has_complete_settlement,
        })
    return items
