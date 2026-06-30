"""
Shared revenue computation — RAO-P2-028.

Wyciągnięte z `stats/router.py` aby uniknąć rozjazdu przychodu między
statystykami (kaskadowe `calculate_position_value`) a eksploratorem
(wcześniej `rate1 * period_count`).

Public API:
    compute_position_revenues(db, df, dt, *, service_filter, exclude_archival,
                              category_main_filter, category_sub1_filter,
                              category_sub2_filter) -> list[dict]
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from articles.models import Article
from contracts.models import Contract, ContractPosition, PositionCondition
from stats.calc import calculate_position_value


async def compute_position_revenues(
    db: AsyncSession,
    df: date,
    dt: date,
    *,
    service_filter: bool | None = None,
    exclude_archival: bool = True,
    category_main_filter: list[str] | None = None,
    category_sub1_filter: str | None = None,
    category_sub2_filter: str | None = None,
) -> list[dict]:
    """
    Fetch positions+conditions for contracts overlapping [df, dt],
    compute value per position using spec algorithm (04_BUSINESS_LOGIC.md).

    Returns list of dicts with keys:
        position_id, article_id, contract_id, contractor_id,
        article_name, internal_number, is_service, contract_number,
        contractor_name, rental_days, revenue, date_from, date_to,
        category_main, category_sub1, category_sub2, category_sub3,
        contract_date_from, clamped_days
    """
    stmt = (
        select(
            ContractPosition.id,            # p[0]
            ContractPosition.article_id,    # p[1]
            ContractPosition.contract_id,   # p[2]
            ContractPosition.rental_days,   # p[3]
            ContractPosition.billing_frequency,  # p[4]
            ContractPosition.unit_price,    # p[5]
            ContractPosition.quantity,      # p[6]
            Article.name.label("article_name"),  # p[7]
            Article.internal_number,        # p[8]
            Article.is_service,             # p[9]
            Contract.number.label("contract_number"),  # p[10]
            Contract.contractor_name,       # p[11]
            Contract.contractor_id,         # p[12]
            Contract.date_from,             # p[13]
            Contract.date_to,               # p[14]
            Article.category_main,          # p[15]
            Article.category_sub1,          # p[16]
            Article.category_sub2,          # p[17]
            Article.category_sub3,          # p[18]
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Article, Article.id == ContractPosition.article_id)
        .where(and_(Contract.date_from <= dt, Contract.date_to >= df))
    )
    if service_filter is not None:
        stmt = stmt.where(Article.is_service == service_filter)
    if exclude_archival:
        stmt = stmt.where(Article.is_archival == False)
        stmt = stmt.where(Article.is_external == False)  # RAO-P1-027
    if category_main_filter:
        stmt = stmt.where(Article.category_main.in_(category_main_filter))
    if category_sub1_filter:
        stmt = stmt.where(Article.category_sub1 == category_sub1_filter)
    if category_sub2_filter:
        stmt = stmt.where(Article.category_sub2 == category_sub2_filter)

    pos_result = await db.execute(stmt)
    positions = pos_result.all()

    if not positions:
        return []

    pos_ids = [p[0] for p in positions]
    cond_result = await db.execute(
        select(
            PositionCondition.position_id,
            PositionCondition.rate1,
            PositionCondition.rate2,
            PositionCondition.period_count,
            PositionCondition.minimum,
            PositionCondition.rate_type_id,
        )
        .where(PositionCondition.position_id.in_(pos_ids))
        .order_by(PositionCondition.position_id, PositionCondition.period_count)
    )
    cond_rows = cond_result.all()

    conds_by_pos = defaultdict(list)
    for c in cond_rows:
        conds_by_pos[c[0]].append({
            "rate1": c[1], "rate2": c[2], "period_count": c[3],
            "minimum": c[4], "rate_type_id": c[5],
        })

    results = []
    for p in positions:
        pid = p[0]
        conds = conds_by_pos.get(pid, [])
        revenue = calculate_position_value(
            rental_days=p[3],
            billing_frequency=p[4],
            unit_price=p[5],
            quantity=p[6],
            conditions=conds,
        )
        c_from = p[13] if p[13] >= df else df
        c_to = p[14] if p[14] <= dt else dt
        clamped_days = max((c_to - c_from).days + 1, 0)

        results.append({
            "position_id": pid,
            "article_id": p[1],
            "contract_id": p[2],
            "rental_days": p[3] or 0,
            "article_name": p[7],
            "internal_number": p[8],
            "is_service": p[9],
            "contract_number": p[10],
            "contractor_name": p[11],
            "contractor_id": p[12],
            "date_from": p[13],
            "date_to": p[14],
            "contract_date_from": p[13],
            "clamped_days": clamped_days,
            "revenue": revenue,
            "category_main": p[15],
            "category_sub1": p[16],
            "category_sub2": p[17],
            "category_sub3": p[18],
        })
    return results
