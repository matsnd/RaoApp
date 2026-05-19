from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from articles.models import Article
from contracts.models import Contract, ContractPosition, PositionCondition
from contractors.models import Contractor
from stats.calc import calculate_position_value, aggregate_by_category
from stats.schemas import (
    FleetSummary, TopMachineItem, CurrentlyRentedResponse, CurrentlyRentedItem,
    MachineRoiResponse, AdditionalFeesResponse, ServiceFeeItem, LocationStatItem,
    ExpiringContractItem, OverdueContractItem, DeliveryTodayItem, UnprintedContractItem, StalePrintContractItem,
    SalespersonCommissionItem, CommissionReportResponse,
    CategoryStatItem, CategoryStatsResponse,
    PositionStatItem, PositionStatsResponse,
)

router = APIRouter(prefix="/stats", tags=["stats"])


def _default_dates(date_from: date | None, date_to: date | None):
    today = date.today()
    if not date_from:
        date_from = today.replace(day=1)
    if not date_to:
        date_to = today
    return date_from, date_to


async def _compute_position_revenues(
    db: AsyncSession,
    df: date,
    dt: date,
    *,
    service_filter: bool | None = None,
    exclude_archival: bool = True,
) -> list[dict]:
    """
    Fetch positions+conditions for contracts overlapping [df, dt],
    compute value per position using spec algorithm (04_BUSINESS_LOGIC.md).

    Returns list of dicts with keys:
        position_id, article_id, contract_id, contractor_id,
        article_name, internal_number, is_service, contract_number,
        contractor_name, rental_days, revenue, date_from, date_to,
        category_main, category_sub1                       ← RAO-P1-017

    Args:
        exclude_archival: gdy True (domyślnie), wyklucza maszyny z is_archival=TRUE.
                          Nie dotyczy usług (service_filter=True). RAO-P1-017
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
            Article.category_main,          # p[15] — RAO-P1-017
            Article.category_sub1,          # p[16] — RAO-P1-017
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Article, Article.id == ContractPosition.article_id)
        .where(and_(Contract.date_from <= dt, Contract.date_to >= df))
    )
    if service_filter is not None:
        stmt = stmt.where(Article.is_service == service_filter)
    # RAO-P1-017: domyślnie wyklucz maszyny archiwalne (nie dotyczy usług)
    if exclude_archival and service_filter is not True:
        stmt = stmt.where(Article.is_archival == False)

    pos_result = await db.execute(stmt)
    positions = pos_result.all()

    if not positions:
        return []

    # Batch-fetch all conditions for these positions
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

    # Group conditions by position_id
    conds_by_pos = defaultdict(list)
    for c in cond_rows:
        conds_by_pos[c[0]].append({
            "rate1": c[1], "rate2": c[2], "period_count": c[3],
            "minimum": c[4], "rate_type_id": c[5],
        })

    # Compute revenue per position
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
        # Clamp rented days to the query window
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
            "clamped_days": clamped_days,
            "revenue": revenue,
            "category_main": p[15],   # RAO-P1-017
            "category_sub1": p[16],   # RAO-P1-017
        })
    return results


@router.get("/fleet-summary", response_model=FleetSummary)
async def fleet_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _default_dates(date_from, date_to)
    today = date.today()

    # Build base query for machines
    machines_query = select(Article).where(
        and_(Article.is_service == False, Article.is_archival == False)
    )
    if internal_number:
        machines_query = machines_query.where(Article.internal_number == internal_number)

    # Total machines (not services, not archival) — RAO-P1-017
    total_q = await db.execute(machines_query)
    total_machines = total_q.scalar() or 0

    # Currently rented (active contracts with machine positions, not archival) — RAO-P1-017
    rented_query = (
        select(func.count(func.distinct(ContractPosition.article_id)))
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Article, Article.id == ContractPosition.article_id)
        .where(
            and_(
                Article.is_service == False,
                Article.is_archival == False,       # RAO-P1-017
                Contract.date_from <= today,
                Contract.date_to >= today,
            )
        )
    )
    if internal_number:
        rented_query = rented_query.where(Article.internal_number == internal_number)

    rented_q = await db.execute(rented_query)
    total_rented = rented_q.scalar() or 0
    util_pct = round((total_rented / total_machines * 100) if total_machines else 0, 1)

    # Revenue — computed via spec algorithm
    all_pos = await _compute_position_revenues(db, df, dt)
    if internal_number:
        all_pos = [p for p in all_pos if p["internal_number"] == internal_number]
    period_revenue = sum(p["revenue"] for p in all_pos)

    # Contracts in period
    cnt_q = await db.execute(
        select(func.count())
        .select_from(Contract)
        .where(and_(Contract.date_from <= dt, Contract.date_to >= df))
    )
    contracts_in_period = cnt_q.scalar() or 0

    # Top machine by revenue (machines only, not services)
    machine_rev = defaultdict(lambda: {"name": "", "rev": Decimal(0)})
    for p in all_pos:
        if not p["is_service"]:
            key = p["article_id"]
            machine_rev[key]["name"] = p["article_name"]
            machine_rev[key]["rev"] += p["revenue"]

    top_name, top_rev = None, None
    if machine_rev:
        top = max(machine_rev.values(), key=lambda x: x["rev"])
        top_name = top["name"]
        top_rev = top["rev"]

    return FleetSummary(
        total_rented=total_rented,
        total_machines=total_machines,
        utilization_pct=util_pct,
        period_revenue=period_revenue,
        top_machine_name=top_name,
        top_machine_revenue=top_rev,
        contracts_in_period=contracts_in_period,
    )


@router.get("/top-machines", response_model=list[TopMachineItem])
async def top_machines(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _default_dates(date_from, date_to)
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=False)
    if internal_number:
        all_pos = [p for p in all_pos if p["internal_number"] == internal_number]

    # Aggregate by article
    agg = defaultdict(lambda: {
        "name": "", "internal_number": None,
        "revenue": Decimal(0), "days": 0, "contracts": set(),
    })
    for p in all_pos:
        key = p["article_id"]
        agg[key]["name"] = p["article_name"]
        agg[key]["internal_number"] = p["internal_number"]
        agg[key]["revenue"] += p["revenue"]
        agg[key]["days"] += p["clamped_days"]
        agg[key]["contracts"].add(p["contract_id"])

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue"], reverse=True)[:limit]
    return [
        TopMachineItem(
            article_id=aid, name=d["name"], internal_number=d["internal_number"],
            revenue=d["revenue"], rented_days=d["days"],
            contracts_count=len(d["contracts"]),
        )
        for aid, d in sorted_items
    ]


@router.get("/currently-rented", response_model=CurrentlyRentedResponse)
async def currently_rented(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = date.today()

    # RAO-P1-017: wyklucz maszyny archiwalne z licznika floty
    total_q = await db.execute(
        select(func.count()).select_from(Article).where(
            and_(Article.is_service == False, Article.is_archival == False)
        )
    )
    total_machines = total_q.scalar() or 0

    q = await db.execute(
        select(
            Article.id,               # r[0]
            Article.name,             # r[1]
            Article.internal_number,  # r[2]
            Article.category_main,    # r[3] — RAO-P1-017
            Contract.number,          # r[4]
            Contract.contractor_name, # r[5]
            Contract.date_to,         # r[6]
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Article, Article.id == ContractPosition.article_id)
        .where(
            and_(
                Article.is_service == False,
                Article.is_archival == False,   # RAO-P1-017: wyklucz archiwalne
                Contract.date_from <= today,
                Contract.date_to >= today,
            )
        )
        .group_by(
            Article.id, Article.name, Article.internal_number, Article.category_main,
            Contract.number, Contract.contractor_name, Contract.date_to,
        )
        .order_by(Article.name)
    )
    rows = q.all()
    items = [
        CurrentlyRentedItem(
            article_id=r[0], name=r[1], internal_number=r[2],
            category_main=r[3],                              # RAO-P1-017
            contract_number=r[4], contractor_name=r[5], return_date=r[6],
        )
        for r in rows
    ]
    rented = len(items)
    util = round((rented / total_machines * 100) if total_machines else 0, 1)

    return CurrentlyRentedResponse(
        total_rented=rented, total_machines=total_machines,
        utilization_pct=util, items=items,
    )


@router.get("/machine-roi", response_model=MachineRoiResponse)
async def machine_roi(
    article_id: int = Query(...),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_archival: bool = Query(False, description="Uwzględnij maszyny archiwalne"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    ROI konkretnej maszyny (article_id). RAO-P1-017: dodano category_main w odpowiedzi.
    include_archival=False (domyślnie) — jeśli maszyna jest archiwalna, zwraca 404.
    """
    df, dt = _default_dates(date_from, date_to)

    art_q = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    art = art_q.scalar_one_or_none()
    if not art:
        raise HTTPException(404, "Artykuł nie znaleziony")

    # RAO-P1-017: blokuj dostęp do archiwalnej maszyny gdy include_archival=False
    if not include_archival and art.is_archival:
        raise HTTPException(404, "Artykuł jest archiwalny (użyj include_archival=true)")

    # Dla zapytania o konkretną maszynę: bez filtra archiwum (artykuł już sprawdzony powyżej)
    all_pos = await _compute_position_revenues(db, df, dt, exclude_archival=False)
    filtered = [p for p in all_pos if p["article_id"] == article_id]

    revenue = sum(p["revenue"] for p in filtered)
    days = sum(p["clamped_days"] for p in filtered)
    cnt = len(set(p["contract_id"] for p in filtered))

    roi_pct = None
    if art.replacement_value and art.replacement_value > 0:
        roi_pct = round(float(revenue) / float(art.replacement_value) * 100, 2)

    return MachineRoiResponse(
        article_id=art.id, name=art.name, internal_number=art.internal_number,
        category_main=art.category_main,                # RAO-P1-017
        replacement_value=art.replacement_value,
        total_rented_days=days, estimated_revenue=revenue,
        contracts_count=cnt, roi_pct=roi_pct,
    )


@router.get("/additional-fees", response_model=AdditionalFeesResponse)
async def additional_fees(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _default_dates(date_from, date_to)
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=True)

    # Aggregate by service article
    agg = defaultdict(lambda: {"name": "", "revenue": Decimal(0), "contracts": set()})
    for p in all_pos:
        key = p["article_id"]
        agg[key]["name"] = p["article_name"]
        agg[key]["revenue"] += p["revenue"]
        agg[key]["contracts"].add(p["contract_id"])

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue"], reverse=True)
    breakdown = [
        ServiceFeeItem(
            article_id=aid, service_name=d["name"],
            total_revenue=d["revenue"], times_billed=len(d["contracts"]),
        )
        for aid, d in sorted_items
    ]
    total = sum(item.total_revenue for item in breakdown)

    return AdditionalFeesResponse(
        date_from=df, date_to=dt,
        total_services_revenue=total, breakdown=breakdown,
    )


@router.get("/locations", response_model=list[LocationStatItem])
async def locations(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _default_dates(date_from, date_to)
    all_pos = await _compute_position_revenues(db, df, dt)
    if internal_number:
        all_pos = [p for p in all_pos if p["internal_number"] == internal_number]

    # Get contract cities (RAO-P1-008: changed from Contractor.city to Contract.city)
    contract_ids = set(p["contract_id"] for p in all_pos if p["contract_id"])
    city_map = {}
    if contract_ids:
        city_q = await db.execute(
            select(Contract.id, Contract.city)
            .where(
                and_(
                    Contract.id.in_(contract_ids),
                    Contract.city.isnot(None),
                    Contract.city != "",
                )
            )
        )
        city_map = {r[0]: r[1] for r in city_q.all()}

    # Aggregate by city
    agg = defaultdict(lambda: {"cnt": 0, "rev": Decimal(0), "contracts": set()})
    for p in all_pos:
        city = city_map.get(p["contract_id"])
        if not city:
            continue
        agg[city]["rev"] += p["revenue"]
        agg[city]["contracts"].add(p["contract_id"])

    for city, d in agg.items():
        d["cnt"] = len(d["contracts"])

    sorted_cities = sorted(agg.items(), key=lambda x: x[1]["cnt"], reverse=True)[:20]
    return [
        LocationStatItem(city=city, rentals_count=d["cnt"], total_revenue=d["rev"])
        for city, d in sorted_cities
    ]


# ---------------------------------------------------------------------------
# RAO-P1-017: STATYSTYKI PO KATEGORIACH
# ---------------------------------------------------------------------------

@router.get("/by-category", response_model=CategoryStatsResponse)
async def by_category(
    level: str = Query(
        "main",
        pattern="^(main|sub1)$",
        description="Poziom kategorii: 'main' = category_main, 'sub1' = category_sub1",
    ),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    include_archival: bool = Query(
        False,
        description="Uwzględnij maszyny archiwalne (domyślnie wykluczone)",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki wynajmu maszyn agregowane po kategorii (RAO-P1-017).

    - level=main  → GROUP BY category_main  (domyślny)
    - level=sub1  → GROUP BY category_sub1
    - include_archival=false (domyślnie) → wyklucza maszyny is_archival=TRUE
    - Maszyny bez kategorii trafiają do grupy "(bez kategorii)"
    """
    df, dt = _default_dates(date_from, date_to)

    # Tylko maszyny (nie usługi), z filtrem archiwum
    all_pos = await _compute_position_revenues(
        db, df, dt,
        service_filter=False,
        exclude_archival=not include_archival,
    )

    # Czysta agregacja po kategorii (logika w calc.py — testowalny pure function)
    grouped = aggregate_by_category(all_pos, level=level)

    items = [
        CategoryStatItem(
            category_name=g["category_name"],
            articles_count=g["articles_count"],
            rented_days=g["rented_days"],
            revenue=g["revenue"],
            contracts_count=g["contracts_count"],
        )
        for g in grouped
    ]
    total_revenue = sum(item.revenue for item in items)

    return CategoryStatsResponse(
        date_from=df,
        date_to=dt,
        level=level,
        total_revenue=total_revenue,
        items=items,
    )


# ---------------------------------------------------------------------------
# RAO-P2-010: STATYSTYKI POZYCJI Z FILTREM TYPU
# ---------------------------------------------------------------------------

@router.get("/positions", response_model=PositionStatsResponse)
async def positions(
    position_type: Literal["machines", "services", "all"] = Query("all", alias="type"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki pozycji umowy z filtrem typu (RAO-P2-010).

    - type=machines → tylko maszyny (service_filter=False)
    - type=services → tylko usługi (service_filter=True)
    - type=all → wszystkie pozycje (service_filter=None, default)
    """
    df, dt = _default_dates(date_from, date_to)

    # Mapowanie type → service_filter
    service_filter = None
    if position_type == "machines":
        service_filter = False
    elif position_type == "services":
        service_filter = True

    # Pobierz pozycje z odpowiednim filtrem
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=service_filter)

    # Agregacja per article
    agg = defaultdict(lambda: {
        "name": "",
        "internal_number": None,
        "is_service": False,
        "category_main": None,
        "revenue": Decimal(0),
        "rented_days": 0,
        "contracts": set(),
        "times_billed": 0,
    })

    for p in all_pos:
        key = p["article_id"]
        agg[key]["name"] = p["article_name"]
        agg[key]["internal_number"] = p["internal_number"]
        agg[key]["is_service"] = p["is_service"]
        agg[key]["category_main"] = p["category_main"]
        agg[key]["revenue"] += p["revenue"]
        agg[key]["rented_days"] += p["clamped_days"] if not p["is_service"] else 0
        agg[key]["contracts"].add(p["contract_id"])
        agg[key]["times_billed"] += 1

    # Oblicz total_machines_revenue i total_services_revenue (zawsze, niezależnie od filtra)
    all_pos_unfiltered = await _compute_position_revenues(db, df, dt, service_filter=None)
    total_machines_rev = sum(p["revenue"] for p in all_pos_unfiltered if not p["is_service"])
    total_services_rev = sum(p["revenue"] for p in all_pos_unfiltered if p["is_service"])

    # Build response items
    items = [
        PositionStatItem(
            article_id=aid,
            article_name=d["name"],
            internal_number=d["internal_number"],
            is_service=d["is_service"],
            category_main=d["category_main"],
            revenue=d["revenue"],
            rented_days=d["rented_days"],
            contracts_count=len(d["contracts"]),
            times_billed=d["times_billed"],
        )
        for aid, d in agg.items()
    ]

    # Sortuj po revenue descending
    items.sort(key=lambda x: x.revenue, reverse=True)

    total_revenue = sum(item.revenue for item in items)

    return PositionStatsResponse(
        date_from=df,
        date_to=dt,
        type=position_type,
        total_revenue=total_revenue,
        total_machines_revenue=total_machines_rev,
        total_services_revenue=total_services_rev,
        items=items,
    )


# ---------------------------------------------------------------------------
# WORKER REPORTS
# ---------------------------------------------------------------------------

@router.get("/expiring-contracts", response_model=list[ExpiringContractItem])
async def expiring_contracts(
    days: int = Query(14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contracts ending within the next N days (inclusive)."""
    from settings.models import Salesperson
    today = date.today()
    deadline = today + timedelta(days=days)

    q = await db.execute(
        select(
            Contract.id, Contract.number, Contract.contractor_name,
            Contract.date_from, Contract.date_to,
            Contract.delivery_address, Contract.contact_person1, Contract.contact_phone1,
            Contract.salesperson_id,
        )
        .where(and_(Contract.date_to >= today, Contract.date_to <= deadline))
        .order_by(Contract.date_to)
    )
    rows = q.all()

    salesperson_ids = {r[8] for r in rows if r[8]}
    sp_map: dict[int, str] = {}
    if salesperson_ids:
        sp_q = await db.execute(
            select(Salesperson.id, Salesperson.name).where(Salesperson.id.in_(salesperson_ids))
        )
        sp_map = {r[0]: r[1] for r in sp_q.all()}

    return [
        ExpiringContractItem(
            id=r[0], number=r[1], contractor_name=r[2],
            date_from=r[3], date_to=r[4],
            days_left=(r[4] - today).days if r[4] else 0,
            delivery_address=r[5], contact_person1=r[6], contact_phone1=r[7],
            salesperson_name=sp_map.get(r[8]) if r[8] else None,
        )
        for r in rows
    ]


@router.get("/overdue-contracts", response_model=list[OverdueContractItem])
async def overdue_contracts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contracts where date_to has passed but are still active (not archived)."""
    today = date.today()

    q = await db.execute(
        select(
            Contract.id, Contract.number, Contract.contractor_name,
            Contract.date_from, Contract.date_to,
            Contract.delivery_address, Contract.contact_person1, Contract.contact_phone1,
        )
        .where(Contract.date_to < today)
        .order_by(Contract.date_to)
    )
    rows = q.all()

    return [
        OverdueContractItem(
            id=r[0], number=r[1], contractor_name=r[2],
            date_from=r[3], date_to=r[4],
            days_overdue=(today - r[4]).days if r[4] else 0,
            delivery_address=r[5], contact_person1=r[6], contact_phone1=r[7],
        )
        for r in rows
    ]


@router.get("/deliveries-today", response_model=list[DeliveryTodayItem])
async def deliveries_today(
    lookahead: int = Query(1, ge=1, le=7),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contract positions with delivery_date within next N days."""
    today = date.today()
    deadline = today + timedelta(days=lookahead - 1)

    q = await db.execute(
        select(
            Contract.id, Contract.number, Contract.contractor_name,
            ContractPosition.article_name, ContractPosition.delivery_date,
            Contract.delivery_address, Contract.contact_person1, Contract.contact_phone1,
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .where(and_(ContractPosition.delivery_date >= today, ContractPosition.delivery_date <= deadline))
        .order_by(ContractPosition.delivery_date, Contract.number)
    )
    rows = q.all()

    return [
        DeliveryTodayItem(
            contract_id=r[0], contract_number=r[1], contractor_name=r[2],
            article_name=r[3], delivery_date=r[4],
            delivery_address=r[5], contact_person1=r[6], contact_phone1=r[7],
        )
        for r in rows
    ]


@router.get("/unprinted-contracts", response_model=list[UnprintedContractItem])
async def unprinted_contracts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contracts never printed: active OR created in last 60 days."""
    from datetime import timedelta
    from sqlalchemy import or_
    today = date.today()
    cutoff = today - timedelta(days=60)

    q = await db.execute(
        select(
            Contract.id, Contract.number, Contract.contractor_name,
            Contract.date_from, Contract.date_to, Contract.created_at,
        )
        .where(and_(
            Contract.print_date.is_(None),
            or_(Contract.date_to >= today, Contract.created_at >= cutoff),
        ))
        .order_by(Contract.date_from.desc())
    )
    rows = q.all()

    return [
        UnprintedContractItem(
            id=r[0], number=r[1], contractor_name=r[2],
            date_from=r[3], date_to=r[4],
            created_at=r[5].strftime("%d.%m.%Y") if r[5] else None,
        )
        for r in rows
    ]


@router.get("/stale-print-contracts", response_model=list[StalePrintContractItem])
async def stale_print_contracts(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contracts printed before last modification: active OR modified in last 30 days."""
    from datetime import timedelta
    from sqlalchemy import or_
    today = date.today()
    cutoff = today - timedelta(days=30)

    q = await db.execute(
        select(
            Contract.id, Contract.number, Contract.contractor_name,
            Contract.date_from, Contract.date_to, Contract.print_date, Contract.updated_at,
        )
        .where(and_(
            Contract.print_date.isnot(None),
            Contract.updated_at.isnot(None),
            Contract.print_date < Contract.updated_at,
            or_(Contract.date_to >= today, Contract.updated_at >= cutoff),
        ))
        .order_by(Contract.updated_at.desc())
    )
    rows = q.all()

    def _fmt(dt):
        return dt.strftime("%d.%m.%Y %H:%M") if dt else None

    return [
        StalePrintContractItem(
            id=r[0], number=r[1], contractor_name=r[2],
            date_from=r[3], date_to=r[4],
            print_date=_fmt(r[5]), updated_at=_fmt(r[6]),
        )
        for r in rows
    ]


@router.get("/commissions", response_model=CommissionReportResponse)
async def commissions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Commission report: margin per salesperson × commission_rate (RAO-P1-018)."""
    from settings.models import Salesperson
    from settlements.models import ContractSettlement
    df, dt = _default_dates(date_from, date_to)

    # RAO-P1-018: Prowizja od marży, nie od przychodu
    # Oblicz marżę z contract_settlements dla umów w zakresie dat
    settlement_q = await db.execute(
        select(
            Contract.salesperson_id,
            func.sum(ContractSettlement.cost_client - ContractSettlement.cost_company).label("total_margin")
        )
        .join(ContractSettlement, Contract.id == ContractSettlement.contract_id)
        .where(and_(Contract.date_from <= dt, Contract.date_to >= df))
        .where(Contract.salesperson_id.isnot(None))
        .where(ContractSettlement.cost_client.isnot(None))
        .where(ContractSettlement.cost_company.isnot(None))
        .group_by(Contract.salesperson_id)
    )
    settlement_margins = {r[0]: r[1] for r in settlement_q.all()}

    sp_q = await db.execute(
        select(Salesperson.id, Salesperson.name, Salesperson.commission_rate)
        .where(Salesperson.is_active == True)
        .order_by(Salesperson.name)
    )
    salespeople = {r[0]: {"name": r[1], "rate": r[2]} for r in sp_q.all()}

    # Dla backward compatibility, oblicz również revenue (stara metoda)
    all_pos = await _compute_position_revenues(db, df, dt)
    contract_sp_q = await db.execute(
        select(Contract.id, Contract.salesperson_id)
        .where(and_(Contract.date_from <= dt, Contract.date_to >= df))
        .where(Contract.salesperson_id.isnot(None))
    )
    contract_sp_map = {r[0]: r[1] for r in contract_sp_q.all()}

    agg: dict[int, dict] = defaultdict(lambda: {"revenue": Decimal(0), "contracts": set()})
    for p in all_pos:
        sp_id = contract_sp_map.get(p["contract_id"])
        if sp_id and sp_id in salespeople:
            agg[sp_id]["revenue"] += p["revenue"]
            agg[sp_id]["contracts"].add(p["contract_id"])

    items = []
    for sp_id, sp_data in salespeople.items():
        data = agg.get(sp_id, {"revenue": Decimal(0), "contracts": set()})
        rate = sp_data["rate"] or Decimal(0)
        
        # RAO-P1-018: Użyj marży z settlement jeśli dostępna, wpp. revenue (backward compatibility)
        margin = settlement_margins.get(sp_id, Decimal(0))
        if margin is not None and margin != 0:
            # Nowa formuła: prowizja od marży
            commission = (margin * rate / Decimal(100)).quantize(Decimal("0.01"))
            base_amount = margin
        else:
            # Backward compatibility: jeśli brak danych settlement, użyj revenue
            revenue = data["revenue"]
            commission = (revenue * rate / Decimal(100)).quantize(Decimal("0.01"))
            base_amount = revenue
        
        items.append(SalespersonCommissionItem(
            salesperson_id=sp_id,
            salesperson_name=sp_data["name"],
            commission_rate=sp_data["rate"],
            contracts_count=len(data["contracts"]),
            total_revenue=data["revenue"],  # Zachowaj revenue dla informacji
            commission_amount=commission,
        ))

    items.sort(key=lambda x: x.commission_amount, reverse=True)
    grand_revenue = sum(i.total_revenue for i in items)
    grand_commission = sum(i.commission_amount for i in items)

    return CommissionReportResponse(
        date_from=df, date_to=dt,
        items=items,
        grand_total_revenue=grand_revenue,
        grand_total_commission=grand_commission,
    )


# ---------------------------------------------------------------------------
# RAO-P3-004: EKSPORT CSV
# ---------------------------------------------------------------------------

@router.get("/export/csv")
async def export_csv(
    export_type: Literal["contracts", "articles", "contractors"] = Query(
        ...,
        alias="type",
        description="Typ eksportu: contracts | articles | contractors",
    ),
    from_date: date | None = Query(
        None,
        description="Filtr od daty (YYYY-MM-DD) — dotyczy Contract.date_from dla type=contracts",
    ),
    to_date: date | None = Query(
        None,
        description="Filtr do daty (YYYY-MM-DD) — dotyczy Contract.date_from dla type=contracts",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    RAO-P3-004: Eksport danych statystyk do pliku CSV.

    Zwraca plik CSV z UTF-8 BOM (poprawne otwarcie w Excel PL).
    Delimiter: średnik.

    Typy eksportu:
    - **contracts**: lista umów (nr_umowy, kontrahent, data_od, data_do, status, handlowiec, wartosc_netto)
    - **articles**: lista artykułów niearchiwalnych (nazwa, kategoria, nr_wewn, aktywna_umowa)
    - **contractors**: lista kontrahentów (nazwa, nip, miasto, email, telefon, aktywna_umowa)

    Parametry `from_date`/`to_date` są opcjonalne i dotyczą wyłącznie type=contracts
    (filtrują po Contract.date_from).
    """
    from stats import service as stats_service

    filename = f"rao_stats_{date.today().strftime('%Y%m%d')}.csv"
    csv_data = await stats_service.export_csv_data(db, export_type, from_date, to_date)

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
