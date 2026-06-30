from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from articles.models import Article
from contracts.models import Contract, ContractPosition, PositionCondition
from contractors.models import Contractor
from sqlalchemy import func as sqlfunc
from stats.calc import calculate_position_value, aggregate_by_category, aggregate_by_period
from shared.revenue import compute_position_revenues as _compute_position_revenues  # RAO-P2-028
from shared.locations import aggregate_by_pna  # RAO-P2-028
from stats.schemas import (
    FleetSummary, TopMachineItem, CurrentlyRentedResponse, CurrentlyRentedItem,
    MachineRoiResponse, AdditionalFeesResponse, ServiceFeeItem, LocationStatItem,
    ExpiringContractItem, OverdueContractItem, DeliveryTodayItem, UnprintedContractItem, StalePrintContractItem,
    SalespersonCommissionItem, CommissionReportResponse,
    CategoryStatItem, CategoryStatsResponse,
    PositionStatItem, PositionStatsResponse,
    ByPeriodItem, ByPeriodResponse, CategoriesListNode,
)

router = APIRouter(prefix="/stats", tags=["stats"])


def _default_dates(date_from: date | None, date_to: date | None):
    today = date.today()
    if not date_from:
        date_from = today.replace(day=1)
    if not date_to:
        date_to = today
    return date_from, date_to


# RAO-P2-028: `_compute_position_revenues` przeniesione do `shared/revenue.py`.
# Pozostawiono re-eksport pod oryginalną nazwą dla zgodności wstecznej
# (m.in. `reports/service.py` importuje `from stats.router import _compute_position_revenues`).


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
    machines_query = select(func.count(Article.id)).where(
        and_(Article.is_service == False, Article.is_archival == False, Article.is_external == False)  # RAO-P1-027
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
                Article.is_external == False,       # RAO-P1-027
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
    # RAO-P2-029: period_revenue uwzględnia archiwalne maszyny (statystyki historyczne)
    # total_machines/total_rented pozostają bez archiwalnych (stan floty teraz)
    all_pos = await _compute_position_revenues(db, df, dt, exclude_archival=False)
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
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=False, exclude_archival=False)
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
            and_(Article.is_service == False, Article.is_archival == False, Article.is_external == False)  # RAO-P1-027
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
                Article.is_external == False,   # RAO-P1-027: wyklucz zewnętrzne
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
    # RAO-P2-029: uwzględnia archiwalne usługi (statystyki historyczne)
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=True, exclude_archival=False)

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
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    all_pos = await _compute_position_revenues(db, df, dt, exclude_archival=False)
    if internal_number:
        all_pos = [p for p in all_pos if p["internal_number"] == internal_number]

    # RAO-P2-028: agregacja po PNA z rollup po city/woj/pow/gmina (shared helper)
    return await aggregate_by_pna(all_pos, db, limit=20)


# ---------------------------------------------------------------------------
# RAO-P1-017: STATYSTYKI PO KATEGORIACH
# ---------------------------------------------------------------------------

@router.get("/by-category", response_model=CategoryStatsResponse)
async def by_category(
    level: str = Query(
        "main",
        pattern="^(main|sub1|sub2|sub3)$",
        description="Poziom kategorii: main|sub1|sub2|sub3",
    ),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_main: list[str] = Query(
        default=[],
        description="Filtr kategorii głównych (multi-value, opcjonalny) — RAO-P1-026",
    ),
    category_sub1: str | None = Query(
        None,
        description="Filtr sub1 (opcjonalny, używany przy level=sub2/sub3) — RAO-P1-026",
    ),
    category_sub2: str | None = Query(
        None,
        description="Filtr sub2 (opcjonalny, używany przy level=sub3) — RAO-P1-026",
    ),
    article_type: str = Query(
        "all",
        pattern="^(all|machine|service)$",
        description="Filtr rodzaju: all|machine|service — RAO-P1-026",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki wynajmu maszyn agregowane po kategorii (RAO-P1-017, RAO-P1-026).

    - level=main|sub1|sub2|sub3 → GROUP BY odpowiedniego pola kategorii
    - Archiwalne maszyny SĄ ZAWSZE uwzględniane — stare umowy z migracji mają archiwalne
      artykuły i ich przychód musi być widoczny w statystykach kategorii.
    - category_main=[...] → opcjonalny filtr kategorii głównych (multi-value)
    - category_sub1/sub2 → opcjonalne filtry sub-kategorii
    - article_type=all|machine|service → filtr rodzaju pozycji
    - Maszyny bez kategorii trafiają do grupy "(bez kategorii)"
    """
    df, dt = _default_dates(date_from, date_to)
    service_filter = {"machine": False, "service": True}.get(article_type)  # None dla "all"

    all_pos = await _compute_position_revenues(
        db, df, dt,
        service_filter=service_filter,
        exclude_archival=False,  # kategorie zawsze zliczają archiwalne (stare umowy)
        category_main_filter=category_main or None,
        category_sub1_filter=category_sub1,
        category_sub2_filter=category_sub2,
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
# RAO-P1-026: STATYSTYKI PO OKRESACH
# ---------------------------------------------------------------------------

@router.get("/by-period", response_model=ByPeriodResponse)
async def by_period(
    granularity: str = Query(
        "month",
        pattern="^(month|year)$",
        description="Granulacja: month (YYYY-MM) | year (YYYY)",
    ),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_main: list[str] = Query(
        default=[],
        description="Filtr kategorii głównych (multi-value) — osobna seria per kategorię gdy podany",
    ),
    article_type: str = Query(
        "all",
        pattern="^(all|machine|service)$",
        description="Filtr rodzaju: all|machine|service",
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Agregaty per okres dla Historia sub-tab (wykres i tabela pivot) — RAO-P1-026.

    - granularity=month → period = "YYYY-MM"
    - granularity=year  → period = "YYYY"
    - category_main=[...] → osobna seria per kategorię; gdy brak → jedna seria "__all__"
    - article_type=all|machine|service → filtr rodzaju pozycji
    - Archiwalne maszyny SĄ ZAWSZE uwzględniane (spójne z /by-category).
    """
    df, dt = _default_dates(date_from, date_to)
    service_filter = {"machine": False, "service": True}.get(article_type)

    all_pos = await _compute_position_revenues(
        db, df, dt,
        service_filter=service_filter,
        exclude_archival=False,  # kategorie zawsze zliczają archiwalne (stare umowy)
        category_main_filter=category_main or None,
    )

    items_raw = aggregate_by_period(
        all_pos,
        granularity=granularity,
        category_main_filter=category_main or None,
    )

    return ByPeriodResponse(
        date_from=df,
        date_to=dt,
        granularity=granularity,
        items=[ByPeriodItem(**item) for item in items_raw],
    )


# ---------------------------------------------------------------------------
# RAO-P1-026: LISTA KATEGORII Z LICZNIKAMI ARTYKUŁÓW
# ---------------------------------------------------------------------------

@router.get("/categories-list", response_model=list[CategoriesListNode])
async def categories_list(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Pełne drzewo kategorii z liczbą maszyn per węzeł — RAO-P1-026.

    Używane przez frontend do drilldown i detekcji klikowalnych wierszy.
    Zlicza tylko aktywne (nie-archiwalne) artykuły przypisane do każdej kategorii.
    """
    from categories.models import Category

    # Pobierz wszystkie kategorie posortowane alfabetycznie
    cats_result = await db.execute(
        select(Category).order_by(Category.name)
    )
    all_cats = cats_result.scalars().all()

    # Policz artykuły per category_id (aktywne, nie archiwalne)
    counts_result = await db.execute(
        select(Article.category_id, sqlfunc.count(Article.id))
        .where(Article.is_archival == False)
        .where(Article.category_id.is_not(None))
        .group_by(Article.category_id)
    )
    art_counts: dict[int, int] = {row[0]: row[1] for row in counts_result.all()}

    # Zbuduj słownik id → CategoriesListNode
    nodes: dict[int, CategoriesListNode] = {
        c.id: CategoriesListNode(
            id=c.id,
            name=c.name,
            level=c.level,
            articles_count=art_counts.get(c.id, 0),
        )
        for c in all_cats
    }

    # Zbuduj drzewo (parent_id → children)
    roots: list[CategoriesListNode] = []
    for cat in all_cats:
        node = nodes[cat.id]
        if cat.parent_id is None:
            roots.append(node)
        elif cat.parent_id in nodes:
            nodes[cat.parent_id].children.append(node)

    return roots


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
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=service_filter, exclude_archival=False)

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
    # RAO-P2-029: uwzględnia archiwalne (spójne z głównym zapytaniem)
    all_pos_unfiltered = await _compute_position_revenues(db, df, dt, service_filter=None, exclude_archival=False)
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
        .where(and_(
            Contract.date_to >= today, Contract.date_to <= deadline,
            Contract.is_settled == False,  # RAO-P2-022: rozliczone nie pokazują się w alarmach
        ))
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
        .where(and_(
            Contract.date_to < today,
            Contract.is_settled == False,  # RAO-P2-022: rozliczone nie pokazują się w alarmach
        ))
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
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    all_pos = await _compute_position_revenues(db, df, dt, exclude_archival=False)
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
