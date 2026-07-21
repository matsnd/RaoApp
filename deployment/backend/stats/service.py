from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from contractors.models import Contractor
from contracts.models import Contract
from settlements.models import ContractSettlement
from settings.models import Salesperson


_CENT = Decimal("0.01")


def _money(value: Decimal | int | float | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(_CENT, rounding=ROUND_HALF_UP)


def calculate_commission_base(
    *,
    settlement_client: Decimal | None,
    settlement_company: Decimal | None,
) -> tuple[Decimal, Decimal, Decimal]:
    """Return (client cost, company cost, commission base).

    Prowizja liczona WYŁĄCZNIE od rzeczywistych rozliczeń (contract_settlements).
    Brak fallbacku do szacunkowego przychodu. Jeśli brak kompletnego settlementu
    (oba koszty nie-NULL), umowa nie jest brana pod uwagę do prowizji.
    Kompletna marża równa zero jest autorytatywna (prowizja = 0).
    """
    client = _money(settlement_client)
    company = _money(settlement_company)
    if settlement_client is not None and settlement_company is not None:
        return client, company, client - company
    # Brak kompletnego settlementu — nie ma podstawy prowizji
    return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")


async def get_salesperson_commission_contracts(
    db: AsyncSession,
    salesperson_id: int,
    date_from: date | None,
    date_to: date | None,
    *,
    salesperson: Salesperson | None = None,
) -> list[dict]:
    """Fetch one commission drill-down row per contract with no N+1 queries.

    Prowizja liczona WYŁĄCZNIE od rzeczywistych rozliczeń (contract_settlements).
    Umowy bez kompletnego settlementu są POMIJANE (nie szacunkowe).
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

    # INNER JOIN z ContractSettlement — tylko umowy z rozliczeniem
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
        .join(ContractSettlement, ContractSettlement.contract_id == Contract.id)
        .where(Contract.salesperson_id == salesperson_id)
        .where(and_(*date_conditions) if date_conditions else True)
        .where(ContractSettlement.cost_client.isnot(None))
        .where(ContractSettlement.cost_company.isnot(None))
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
        contract["cost_client"] += _money(row.settlement_client)
        contract["cost_company"] += _money(row.settlement_company)
        contract["complete_settlements"] += 1

    items = []
    for row in contracts.values():
        client = _money(row["cost_client"])
        company = _money(row["cost_company"])
        base = client - company
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
        })
    return items
