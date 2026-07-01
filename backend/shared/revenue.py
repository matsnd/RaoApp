"""
Shared revenue computation — RAO-P2-028 + RAO-P2-032 + RAO-P2-062 Faza 1.

Trzy źródła przychodu (precedence: actual > lookup > tiered):
1. **actual** — SUM(contract_settlements.cost_client) per pozycja (rzeczywiste rozliczenia)
   - source='fakturownia': import z Fakturownia API
   - source='manual': wpisane ręcznie w UI
   (RAO-P2-062: source='legacy' usunięte — legacy settlements przeniesione do archive_*)
2. **estimate_lookup** — algorytm cena_pozycji (lookup oplata1 po liczba_dni)
   - Reimplementacja starej funkcji SQL z WinForms
   - Wybiera JEDNĄ stawkę na podstawie liczba_dni (nie kaskadowe)
3. **estimate_tiered** — kaskadowy calculate_position_value (obecny algorytm)
   - Używany gdy brak settlements i brak warunków lookup

Public API:
    compute_position_revenues(db, df, dt, *, service_filter, exclude_archival,
                              category_main_filter, ...) -> list[dict]

Każdy dict zawiera:
    revenue_actual: Decimal | None  — z settlements (rzeczywiste)
    revenue_estimate_lookup: Decimal — z cena_pozycji (lookup, legacy algorytm)
    revenue_estimate_tiered: Decimal — z calculate_position_value (kaskadowy)
    revenue: Decimal — wybrane wg mode (actual > lookup > tiered)
    revenue_source: str — "actual" | "estimate_lookup" | "estimate_tiered"

RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy
(legacy przeniesione do archive_*). Statystyki historyczne obsługiwane osobno
przez moduł archive.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from articles.models import Article
from contracts.models import Contract, ContractPosition, PositionCondition
from settlements.models import ContractSettlement
from stats.calc import calculate_position_value


# ── RAO-P2-032: Algorytm cena_pozycji (lookup) — reimplementacja starej funkcji SQL ──

def compute_position_value_lookup(
    rental_days: int | None,
    conditions: list[dict],
) -> Decimal:
    """
    Reimplementacja `cena_pozycji` z starej aplikacji WinForms.

    Algorytm (lookup, NIE kaskadowe):
    1. Jeśli liczba_dni > max(liczba_dni where oplata2>0):
       - Weź ostatni warunek (order by id desc) gdzie liczba_dni >= w.liczba_dni
       - cena = oplata2 (lub oplata1 jeśli oplata2=0)
    2. W przeciwnym razie:
       - Weź pierwszy warunek (order by id) gdzie liczba_dni <= w.liczba_dni
       - cena = oplata2 (lub oplata1 jeśli oplata2=0)
    3. revenue = cena × liczba_dni

    Source: AppRao/rao/FormU4.cs:1390-1396 + migrator/translated_objects/SQL_SCALAR_FUNCTION_cena_pozycji.sql
    """
    if not conditions or not rental_days or rental_days <= 0:
        return Decimal("0.00")

    # Sort by period_count (liczba_dni) — zgodnie ze starą funkcją
    sorted_conds = sorted(conditions, key=lambda c: c.get("period_count") or 0)

    # max(liczba_dni where oplata2>0)
    max_pc_with_oplata2 = max(
        (c.get("period_count") or 0 for c in sorted_conds if (c.get("rate2") or 0) > 0),
        default=0,
    )

    rate = Decimal("0.00")
    if rental_days > max_pc_with_oplata2:
        # powyżej zakresu: ostatni warunek gdzie liczba_dni <= rental_days
        candidates = [c for c in sorted_conds if (c.get("period_count") or 0) <= rental_days]
        if candidates:
            c = candidates[-1]  # ostatni (najwyższy period_count)
            op2 = Decimal(str(c.get("rate2") or 0))
            op1 = Decimal(str(c.get("rate1") or 0))
            rate = op2 if op2 > 0 else op1
    else:
        # w zakresie: pierwszy warunek gdzie liczba_dni >= rental_days
        candidates = [c for c in sorted_conds if (c.get("period_count") or 0) >= rental_days]
        if candidates:
            c = candidates[0]  # pierwszy (najniższy period_count)
            op2 = Decimal(str(c.get("rate2") or 0))
            op1 = Decimal(str(c.get("rate1") or 0))
            rate = op2 if op2 > 0 else op1

    if rate <= 0:
        return Decimal("0.00")

    # revenue = cena × liczba_dni (zgodnie z FormU4.cs: rozliczenie insert per dzień)
    return rate * rental_days


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
    Fetch positions+conditions+settlements for contracts overlapping [df, dt],
    compute value per position using 3 sources (actual > lookup > tiered).

    RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe
    umowy (legacy przeniesione do archive_*). Statystyki archiwum osobno.

    Returns list of dicts with keys:
        position_id, article_id, contract_id, contractor_id,
        article_name, internal_number, is_service, contract_number,
        contractor_name, rental_days, date_from, date_to,
        category_main, category_sub1, category_sub2, category_sub3,
        contract_date_from, clamped_days,
        revenue_actual, revenue_estimate_lookup, revenue_estimate_tiered,
        revenue, revenue_source
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
            Contract.city,                  # p[19] — RAO: filtr city w stats
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

    # 1. Pobierz warunki rozliczenia (position_conditions)
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

    # 2. Pobierz settlements (rzeczywiste rozliczenia) — RAO-P2-032
    sett_result = await db.execute(
        select(
            ContractSettlement.position_id,
            func.sum(ContractSettlement.cost_client).label("total_cost_client"),
        )
        .where(ContractSettlement.position_id.in_(pos_ids))
        .where(ContractSettlement.cost_client.isnot(None))
        .group_by(ContractSettlement.position_id)
    )
    sett_rows = sett_result.all()
    sett_by_pos = {r[0]: Decimal(str(r[1])) for r in sett_rows if r[1] is not None}

    results = []
    for p in positions:
        pid = p[0]
        conds = conds_by_pos.get(pid, [])

        # 3 źródła przychodu
        revenue_actual = sett_by_pos.get(pid)  # None jeśli brak settlements
        revenue_estimate_lookup = compute_position_value_lookup(
            rental_days=p[3],
            conditions=conds,
        )
        revenue_estimate_tiered = calculate_position_value(
            rental_days=p[3],
            billing_frequency=p[4],
            unit_price=p[5],
            quantity=p[6],
            conditions=conds,
        )

        # Precedence: actual > lookup > tiered
        # RAO-P2-060 bug #4/#5: cost_client=0 (bezpłatny wynajem) i ujemny (korekta) = nadal actual
        if revenue_actual is not None:
            revenue = revenue_actual
            revenue_source = "actual"
        elif revenue_estimate_lookup > 0:
            revenue = revenue_estimate_lookup
            revenue_source = "estimate_lookup"
        else:
            revenue = revenue_estimate_tiered
            revenue_source = "estimate_tiered"

        # RAO-P2-060 bug #6/#7: date_from/date_to=NULL crash (umowa na czas nieokreślony)
        if p[13] is None or p[14] is None:
            # Umowa bez daty końcowej — użyj df/dt jako fallback dla clamped_days
            c_from = df
            c_to = dt
        else:
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
            # RAO-P2-032: 3 źródła przychodu
            "revenue_actual": revenue_actual,
            "revenue_estimate_lookup": revenue_estimate_lookup,
            "revenue_estimate_tiered": revenue_estimate_tiered,
            "revenue": revenue,
            "revenue_source": revenue_source,
            "category_main": p[15],
            "category_sub1": p[16],
            "category_sub2": p[17],
            "category_sub3": p[18],
            "city": p[19],                  # RAO: filtr city w stats
        })
    return results
