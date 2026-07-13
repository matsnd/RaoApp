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
from machines.models import Machine
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contractors.models import Contractor
from settlements.models import ContractSettlement
from settings.models import Salesperson
from additional_services.models import AdditionalService
from sqlalchemy import func as sqlfunc
from stats.calc import calculate_position_value, aggregate_by_category, aggregate_by_period, aggregate_by_contract_type, aggregate_by_branch, clamp_days
from shared.revenue import compute_position_revenues as _compute_position_revenues  # RAO-P2-028
from shared.locations import aggregate_by_pna  # RAO-P2-028
from shared.cache import cache, cached_or_compute, TTL_STATS  # RAO-P2-051: cache TTL 5 min
from stats.schemas import (
    FleetSummary, TopMachineItem, CurrentlyRentedResponse, CurrentlyRentedItem,
    AdditionalFeesResponse, ServiceFeeItem, LocationStatItem,
    ExpiringContractItem, OverdueContractItem, DeliveryTodayItem, UnprintedContractItem, StalePrintContractItem,
    SalespersonCommissionItem, CommissionReportResponse,
    SalespersonCommissionContractsResponse,
    CategoryStatItem, CategoryStatsResponse,
    PositionStatItem, PositionStatsResponse,
    ByPeriodItem, ByPeriodResponse, CategoriesListNode,
    ContractTypeStatItem, ContractTypeStatsResponse,
    BranchStatItem, ByBranchStatsResponse,
)

router = APIRouter(prefix="/stats", tags=["stats"])


# RAO: whitelist kolumn do sortowania /stats/positions (ochrona przed SQL injection)
ALLOWED_SORT = {
    "article_name", "internal_number", "category_main",
    "revenue", "rented_days", "contracts_count", "times_settled",
}
# alias: nazwa z zadania → rzeczywiste pole na PositionStatItem
_SORT_FIELD_ALIASES = {"times_settled": "times_billed"}


def _apply_position_filters(
    all_pos: list[dict],
    *,
    contractor_id: int | None = None,
    city: str | None = None,
    internal_number: str | None = None,
) -> list[dict]:
    """Filtruj listę pozycji z compute_position_revenues po contractor_id / city / internal_number.

    RAO-P0-001/BUG-1: city jest accent-insensitive (Gdansk == Gdańsk) via NFD normalization.
    """
    if contractor_id is not None:
        all_pos = [p for p in all_pos if p.get("contractor_id") == contractor_id]
    if city:
        city_norm = _normalize_ascii(city)
        all_pos = [p for p in all_pos if p.get("city") and _normalize_ascii(p["city"]) == city_norm]
    if internal_number:
        all_pos = [p for p in all_pos if p["internal_number"] == internal_number]
    return all_pos


def _normalize_ascii(s: str) -> str:
    """Znormalizuj string do ASCII (usuń akcenty/diakrytyki) + lowercase — RAO-P0-001/BUG-1."""
    import unicodedata
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower()


def _default_dates(date_from: date | None, date_to: date | None):
    """Defaultuj date_to=dziś gdy brak, ale NIE defaultuj date_from (RAO-P0-006/BUG-6).

    Gdy date_from=None → zostaw None (brak dolnego filtra = "od zawsze").
    Gdy date_to=None → defaultuj do dziś.
    Frontend preset='all' wysyła tylko date_to (bez date_from) → backend ma
    szanować to i NIE defaultować date_from do początku miesiąca.
    """
    today = date.today()
    if not date_to:
        date_to = today
    return date_from, date_to


def _validate_date_range(date_from: date | None, date_to: date | None):
    """RAO-P2-065 #10: walidacja date_from > date_to → 422.

    Alias dla compat testów P2-065. Waliduje zakres dat przed defaultowaniem.
    Rzuca HTTPException(422) gdy date_from > date_to (gdy oba podane).
    """
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail=f"Data początkowa ({date_from}) nie może być późniejsza niż końcowa ({date_to}).",
        )
    return _default_dates(date_from, date_to)


def _contract_date_filter(df: date | None, dt: date | None):
    """Zbuduj warunki nakładania się umowy z okresem [df, dt] (RAO-P0-006/BUG-6).

    Obsługuje None (preset='all'): gdy df=None → brak dolnego filtra,
    gdy dt=None → brak górnego filtra. Zwraca listę warunków SQLAlchemy.
    """
    _conds = []
    if dt is not None:
        _conds.append(Contract.date_from <= dt)
    if df is not None:
        _conds.append(Contract.date_to >= df)
    return _conds


# RAO-P2-028: `_compute_position_revenues` przeniesione do `shared/revenue.py`.
# Pozostawiono re-eksport pod oryginalną nazwą dla zgodności wstecznej
# (m.in. `reports/service.py` importuje `from stats.router import _compute_position_revenues`).


@router.get("/fleet-summary", response_model=FleetSummary)
async def fleet_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie (RAO-P0-001/BUG-1)"),
    city: str | None = Query(None, description="Filtruj po mieście umowy, case-insensitive (RAO-P0-001/BUG-1)"),
    article_type: str | None = Query(None, pattern="^(all|machine|service)$", description="Filtruj po typie pozycji (RAO-P0-001/BUG-1)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _validate_date_range(date_from, date_to)
    today = date.today()

    # RAO-P2-051: cache TTL 5 min — stats read-heavy
    _ckey = cache.make_key("stats:fleet-summary", _.id, {
        "df": str(df), "dt": str(dt), "in": internal_number,
        "cid": contractor_id, "city": city, "at": article_type,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    # RAO-P0-001/BUG-1: article_type → service_filter dla compute_position_revenues
    service_filter = {"machine": False, "service": True}.get(article_type)  # None dla "all"/None

    # Build base query for machines (Machine table = tylko maszyny, nie usługi)
    machines_query = select(func.count(Machine.id)).where(
        Machine.is_external == False  # RAO-P1-027
    )
    if internal_number:
        machines_query = machines_query.where(Machine.internal_number == internal_number)

    # Total machines (not archival) — RAO-P1-017
    total_q = await db.execute(machines_query)
    total_machines = total_q.scalar() or 0

    # Currently rented (active contracts with machine positions) — RAO-P1-017
    rented_query = (
        select(func.count(func.distinct(ContractPosition.machine_id)))
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        .join(Machine, Machine.id == ContractPosition.machine_id)
        .where(
            and_(
                Machine.is_external == False,       # RAO-P1-027
                Contract.date_from <= today,
                # RAO-P2-060 bug #3: umowa na czas nieokreślony (date_to=NULL) = wciąż wynajęta
                (Contract.date_to.is_(None)) | (Contract.date_to >= today),
            )
        )
    )
    if internal_number:
        rented_query = rented_query.where(Machine.internal_number == internal_number)
    # RAO-P0-001/BUG-1: filtruj rented po contractor_id/city (accent-insensitive)
    if contractor_id is not None:
        rented_query = rented_query.where(Contract.contractor_id == contractor_id)
    if city:
        # accent-insensitive: COLLATE utf8mb4_polish_ci traktuje ń=n
        rented_query = rented_query.where(Contract.city.collate("utf8mb4_polish_ci") == city)

    rented_q = await db.execute(rented_query)
    total_rented = rented_q.scalar() or 0
    util_pct = round((total_rented / total_machines * 100) if total_machines else 0, 1)

    # Revenue — computed via spec algorithm
    # RAO-P2-029: period_revenue uwzględnia archiwalne maszyny (statystyki historyczne)
    # total_machines/total_rented pozostają bez archiwalnych (stan floty teraz)
    # RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    # BUG FIX: compute_position_revenues uwzględnia też usługi dodatkowe
    # (contract_settlements z service_fee_id) jako syntetyczne wiersze is_service=True.
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=service_filter)
    # RAO-P0-001/BUG-1: filtruj pozycje po contractor_id/city/internal_number
    all_pos = _apply_position_filters(
        all_pos, contractor_id=contractor_id, city=city, internal_number=internal_number
    )
    period_revenue = sum(p["revenue"] for p in all_pos)

    # Contracts in period (RAO-P0-001/BUG-1: filtruj po contractor_id/city, accent-insensitive)
    _cnt_conds = _contract_date_filter(df, dt)
    if contractor_id is not None:
        _cnt_conds.append(Contract.contractor_id == contractor_id)
    if city:
        _cnt_conds.append(Contract.city.collate("utf8mb4_polish_ci") == city)
    if _cnt_conds:
        cnt_q = await db.execute(
            select(func.count())
            .select_from(Contract)
            .where(and_(*_cnt_conds))
        )
    else:
        cnt_q = await db.execute(select(func.count()).select_from(Contract))
    contracts_in_period = cnt_q.scalar() or 0

    # Top machine by revenue (machines only, not services)
    machine_rev = defaultdict(lambda: {"name": "", "rev": Decimal(0)})
    for p in all_pos:
        if not p["is_service"]:
            key = p["machine_id"]
            machine_rev[key]["name"] = p["machine_name"]
            machine_rev[key]["rev"] += p["revenue"]

    top_name, top_rev = None, None
    if machine_rev:
        top = max(machine_rev.values(), key=lambda x: x["rev"])
        top_name = top["name"]
        top_rev = top["rev"]

    result = FleetSummary(
        total_rented=total_rented,
        total_machines=total_machines,
        utilization_pct=util_pct,
        period_revenue=period_revenue,
        top_machine_name=top_name,
        top_machine_revenue=top_rev,
        contracts_in_period=contracts_in_period,
    )
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


@router.get("/top-machines", response_model=list[TopMachineItem])
async def top_machines(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy (case-insensitive)"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _validate_date_range(date_from, date_to)
    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:top-machines", _.id, {
        "df": str(df), "dt": str(dt), "in": internal_number,
        "cid": contractor_id, "city": city, "lim": limit,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    # RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=False)
    all_pos = _apply_position_filters(
        all_pos, contractor_id=contractor_id, city=city, internal_number=internal_number
    )

    # Aggregate by machine
    agg = defaultdict(lambda: {
        "name": "", "internal_number": None,
        "revenue": Decimal(0), "days": 0, "contracts": set(),
    })
    # RAO Faza 2a (opcja E): bucket dla unmapped (machine_id=None) — marker __unmapped__
    unmapped_bucket = {
        "name": "Inne (niezmapowane z FA)", "internal_number": None,
        "revenue": Decimal(0), "days": 0, "contracts": set(),
    }
    for p in all_pos:
        if p["machine_id"] is None:
            # unmapped settlement → bucket "Inne (niezmapowane z FA)"
            unmapped_bucket["revenue"] += p["revenue"]
            unmapped_bucket["contracts"].add(p["contract_id"])
            continue
        key = p["machine_id"]
        agg[key]["name"] = p["machine_name"]
        agg[key]["internal_number"] = p["internal_number"]
        agg[key]["revenue"] += p["revenue"]
        agg[key]["days"] += clamp_days(p["clamped_days"])  # RAO-P1-016: defensive clamp
        agg[key]["contracts"].add(p["contract_id"])

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue"], reverse=True)
    # Dodaj bucket unmapped na końcu jeśli ma revenue > 0
    if unmapped_bucket["revenue"] > 0:
        sorted_items.append((None, unmapped_bucket))
    sorted_items = sorted_items[:limit]
    result = [
        TopMachineItem(
            article_id=aid, name=d["name"], internal_number=d["internal_number"],
            revenue=d["revenue"], rented_days=d["days"],
            contracts_count=len(d["contracts"]),
        )
        for aid, d in sorted_items
    ]
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


@router.get("/currently-rented", response_model=CurrentlyRentedResponse)
async def currently_rented(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = date.today()

    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:currently-rented", _.id, {})
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    # RAO-P1-017: licznik floty
    total_q = await db.execute(
        select(func.count()).select_from(Machine).where(
            Machine.is_external == False  # RAO-P1-027
        )
    )
    total_machines = total_q.scalar() or 0

    q = await db.execute(
        select(
            Machine.id,               # r[0]
            Machine.name,             # r[1]
            Machine.internal_number,  # r[2]
            Machine.category_main,    # r[3] — RAO-P1-017
            Contract.number,          # r[4]
            # RAO-P2-065 #2: coalesce Contractor.name z snapshot contractor_name
            func.coalesce(Contractor.name, Contract.contractor_name).label("contractor_name"),  # r[5]
            Contract.date_to,         # r[6]
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        # RAO-P2-065 #2: LEFT JOIN contractors — contractor_name snapshot NULL dla umów z contractor_id
        .outerjoin(Contractor, Contractor.id == Contract.contractor_id)
        .join(Machine, Machine.id == ContractPosition.machine_id)
        .where(
            and_(
                Machine.is_external == False,   # RAO-P1-027: wyklucz zewnętrzne
                Contract.date_from <= today,
                # RAO-P2-065 #4: umowa na czas nieokreślony (date_to=NULL) = wciąż wynajęta
                (Contract.date_to.is_(None)) | (Contract.date_to >= today),
                # RAO-P2-065 #4: wyklucz rozliczone umowy (zgodnie z fleet-summary)
                Contract.is_settled == False,
            )
        )
        # RAO-P2-065 #2: group_by po coalesce zamiast po Contract.contractor_name
        .group_by(
            Machine.id, Machine.name, Machine.internal_number, Machine.category_main,
            Contract.number, Contractor.name, Contract.contractor_name, Contract.date_to,
        )
        .order_by(Machine.name)
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
    # RAO-P1-120: rented = unikalne maszyny (DISTINCT Machine.id), nie wiersze
    # Jedna maszyna w 3 umowach = 1 maszyna wynajęta, nie 3
    rented = len(set(r[0] for r in rows))
    util = round((rented / total_machines * 100) if total_machines else 0, 1)

    result = CurrentlyRentedResponse(
        total_rented=rented, total_machines=total_machines,
        utilization_pct=util, items=items,
    )
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


@router.get("/additional-fees", response_model=AdditionalFeesResponse)
async def additional_fees(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy, case-insensitive (RAO-P0-001/BUG-5)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _validate_date_range(date_from, date_to)
    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:additional-fees", _.id, {"df": str(df), "dt": str(dt), "cid": contractor_id, "city": city})
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached
    # BUG FIX: statystyki usług dodatkowych — zliczamy contract_settlements
    # z service_fee_id IS NOT NULL (rozliczone usługi dodatkowe z Fakturownia/manual).
    # Wcześniej endpoint używał _compute_position_revenues (pozycje umowy = maszyny/usługi)
    # co ignorowało całkowicie contract_service_fees → puste statystyki.
    stmt = (
        select(
            AdditionalService.id.label("article_id"),
            AdditionalService.name.label("service_name"),
            ContractSettlement.cost_client,
            ContractSettlement.contract_id,
            Contract.contractor_id,
            Contract.city,
        )
        .select_from(ContractSettlement)
        .join(ContractServiceFee, ContractServiceFee.id == ContractSettlement.service_fee_id)
        .join(AdditionalService, AdditionalService.id == ContractServiceFee.additional_service_id)
        .join(Contract, Contract.id == ContractSettlement.contract_id)
        .where(ContractSettlement.service_fee_id.isnot(None))
        .where(ContractSettlement.cost_client.isnot(None))
    )
    _date_conds = []
    if dt is not None:
        _date_conds.append(Contract.date_from <= dt)
    if df is not None:
        _date_conds.append(Contract.date_to >= df)
    if _date_conds:
        stmt = stmt.where(and_(*_date_conds))
    if contractor_id is not None:
        stmt = stmt.where(Contract.contractor_id == contractor_id)
    if city is not None:
        stmt = stmt.where(func.lower(Contract.city) == func.lower(city))

    rows = (await db.execute(stmt)).all()

    agg = defaultdict(lambda: {"name": "", "revenue": Decimal(0), "contracts": set()})
    for r in rows:
        aid = r.article_id
        agg[aid]["name"] = r.service_name
        agg[aid]["revenue"] += Decimal(r.cost_client)
        agg[aid]["contracts"].add(r.contract_id)

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue"], reverse=True)
    breakdown = [
        ServiceFeeItem(
            article_id=aid, service_name=d["name"],
            total_revenue=d["revenue"], times_billed=len(d["contracts"]),
            contracts_count=len(d["contracts"]),
        )
        for aid, d in sorted_items
    ]
    total = sum(item.total_revenue for item in breakdown)

    result = AdditionalFeesResponse(
        date_from=df, date_to=dt,
        total_services_revenue=total, breakdown=breakdown,
    )
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


@router.get("/locations", response_model=list[LocationStatItem])
async def locations(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    internal_number: str | None = Query(None, description="Filtruj po numerze wewnętrznym maszyny"),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy, case-insensitive (RAO-P0-001/BUG-5)"),
    group_by: Literal["city", "pna"] = Query("city", description="Grupowanie: city (1 wiersz/miasto) lub pna (rozbicie)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    df, dt = _validate_date_range(date_from, date_to)
    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:locations", _.id, {
        "df": str(df), "dt": str(dt), "in": internal_number, "cid": contractor_id, "city": city, "gb": group_by,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    # RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    all_pos = await _compute_position_revenues(db, df, dt)
    # RAO-P0-001/BUG-5: filtruj po contractor_id/city/internal_number
    all_pos = _apply_position_filters(
        all_pos, contractor_id=contractor_id, city=city, internal_number=internal_number
    )

    # RAO-P2-028: agregacja po PNA z rollup po city/woj/pow/gmina (shared helper)
    # RAO-P1-009: group_by='city' pomija bucket "(brak PNA)" w tabeli głównej
    result = await aggregate_by_pna(all_pos, db, limit=20, group_by=group_by)
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


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
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie (RAO-P0-001/BUG-3)"),
    city: str | None = Query(None, description="Filtruj po mieście umowy, case-insensitive (RAO-P0-001/BUG-3)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki wynajmu maszyn agregowane po kategorii (RAO-P1-017, RAO-P1-026).

    - level=main|sub1|sub2|sub3 → GROUP BY odpowiedniego pola kategorii
    - Archiwalne maszyny SĄ ZAWSZE uwzględniane — stare umowy z migracji mają archiwalne
      maszyny i ich przychód musi być widoczny w statystykach kategorii.
    - category_main=[...] → opcjonalny filtr kategorii głównych (multi-value)
    - category_sub1/sub2 → opcjonalne filtry sub-kategorii
    - article_type=all|machine|service → filtr rodzaju pozycji
    - contractor_id/city → RAO-P0-001/BUG-3: filtr po kontrahencie/mieście
    - Maszyny bez kategorii trafiają do grupy "(bez kategorii)"
    - RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    """
    df, dt = _validate_date_range(date_from, date_to)
    service_filter = {"machine": False, "service": True}.get(article_type)  # None dla "all"

    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:by-category", _.id, {
        "lvl": level, "df": str(df), "dt": str(dt),
        "cm": sorted(category_main), "cs1": category_sub1, "cs2": category_sub2, "at": article_type,
        "cid": contractor_id, "city": city,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    all_pos = await _compute_position_revenues(
        db, df, dt,
        service_filter=service_filter,
        category_main_filter=category_main or None,
        category_sub1_filter=category_sub1,
        category_sub2_filter=category_sub2,
    )
    # RAO-P0-001/BUG-3: filtruj pozycje po contractor_id/city
    all_pos = _apply_position_filters(all_pos, contractor_id=contractor_id, city=city)

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

    result = CategoryStatsResponse(
        date_from=df,
        date_to=dt,
        level=level,
        total_revenue=total_revenue,
        items=items,
    )
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


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
    - RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    """
    df, dt = _validate_date_range(date_from, date_to)
    service_filter = {"machine": False, "service": True}.get(article_type)

    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:by-period", _.id, {
        "g": granularity, "df": str(df), "dt": str(dt),
        "cm": sorted(category_main), "at": article_type,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    all_pos = await _compute_position_revenues(
        db, df, dt,
        service_filter=service_filter,
        category_main_filter=category_main or None,
    )

    items_raw = aggregate_by_period(
        all_pos,
        granularity=granularity,
        category_main_filter=category_main or None,
    )

    result = ByPeriodResponse(
        date_from=df,
        date_to=dt,
        granularity=granularity,
        items=[ByPeriodItem(**item) for item in items_raw],
    )
    cache.set(_ckey, result, ttl=TTL_STATS)  # RAO-P2-051
    return result


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
    Zlicza tylko aktywne (nie-archiwalne) maszyny przypisane do każdej kategorii.
    """
    # RAO-P2-051: cache TTL 5 min (drzewo kategorii + liczniki — read-heavy)
    _ckey = cache.make_key("stats:categories-list", _.id, {})
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    from categories.models import Category

    # Pobierz wszystkie kategorie posortowane alfabetycznie
    cats_result = await db.execute(
        select(Category).order_by(Category.name)
    )
    all_cats = cats_result.scalars().all()

    # Policz maszyny per category_id (aktywne)
    counts_result = await db.execute(
        select(Machine.category_id, sqlfunc.count(Machine.id))
        .where(Machine.category_id.is_not(None))
        .group_by(Machine.category_id)
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

    cache.set(_ckey, roots, ttl=TTL_STATS)  # RAO-P2-051
    return roots


# ---------------------------------------------------------------------------
# RAO-P2-010: STATYSTYKI POZYCJI Z FILTREM TYPU
# ---------------------------------------------------------------------------

@router.get("/positions", response_model=PositionStatsResponse)
async def positions(
    position_type: Literal["machines", "services", "all"] = Query("all", alias="type"),
    contract_type: str | None = Query(None, description="Filtruj po typie umowy: S=najem, U=usługa"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy (case-insensitive)"),
    category_main: list[str] = Query(
        default=[],
        description="Filtr kategorii głównych (multi-value, opcjonalny) — drilldown kategorii",
    ),
    category_sub1: str | None = Query(
        None,
        description="Filtr sub-kategorii (opcjonalny) — drilldown kategorii sub1",
    ),
    limit: int | None = Query(
        None,
        ge=1,
        le=200,
        description="RAO-P2-053: paginacja — max 200 wierszy. Brak = bez limitu (backward compat).",
    ),
    offset: int = Query(0, ge=0, description="RAO-P2-053: offset paginacji (default 0)"),
    sort_by: str | None = Query(
        None,
        description=(
            "Pole sortowania: article_name | internal_number | category_main | "
            "revenue | rented_days | contracts_count | times_settled "
            "(wartości spoza whitelist są ignorowane)"
        ),
    ),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$", description="Kierunek sortowania: asc|desc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki pozycji umowy z filtrem typu (RAO-P2-010).

    - type=machines → tylko maszyny (service_filter=False)
    - type=services → tylko usługi (service_filter=True)
    - type=all → wszystkie pozycje (service_filter=None, default)
    - contractor_id → filtr po kontrahencie (opcjonalny)
    - city → filtr po mieście umowy, case-insensitive (opcjonalny)
    - sort_by → pole sortowania z whitelist ALLOWED_SORT (nieznane = ignorowane)
    - sort_dir → asc|desc (default desc)
    - limit/offset → paginacja (RAO-P2-053). Brak limitu = wszystkie wiersze (backward compat).
    - RAO-P2-053: pojedyncze wywołanie _compute_position_revenues (wcześniej 2× —
      raz z service_filter, raz bez dla total_*_revenue). Teraz jedno z service_filter=None,
      filtrowanie typu robione in-memory, totale liczone z tego samego zbioru.
    - RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    """
    df, dt = _validate_date_range(date_from, date_to)

    # RAO-P2-051: cache TTL 5 min
    _ckey = cache.make_key("stats:positions", _.id, {
        "t": position_type, "ct": contract_type, "df": str(df), "dt": str(dt),
        "cid": contractor_id, "city": city, "lim": limit, "off": offset,
        "sb": sort_by, "sd": sort_dir,
    })
    _cached = cache.get(_ckey)
    if _cached is not None:
        return _cached

    # RAO-P2-053: pojedyncze wywołanie z service_filter=None (pobiera wszystkie pozycje).
    # Filtrowanie po type robione in-memory — totale liczone z tego samego zbioru.
    # RAO-P2-029: uwzględnia archiwalne maszyny (statystyki historyczne)
    # RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    # RAO Faza 2a (opcja E): pomiń unmapped (machine_id is not None) — to lista pozycji umowy,
    # unmapped nie ma pozycji. Totale per typ też skip unmapped.
    # RAO: usługi dodatkowe (is_additional_service=True) mają machine_id=None i service_id=None,
    # ale mają additional_service_id — nie odfiltruj ich.
    all_pos = await _compute_position_revenues(db, df, dt, service_filter=None)
    all_pos = [p for p in all_pos if p["machine_id"] is not None or p["service_id"] is not None or p.get("is_additional_service")]

    # Totale per typ — z pełnego zbioru (zamiast drugiego wywołania _compute)
    total_machines_rev = sum(p["revenue"] for p in all_pos if p["is_service"] is False)
    total_services_rev = sum(p["revenue"] for p in all_pos if p["is_service"] is True)

    # Filtrowanie po type — in-memory (zamiast drugiego zapytania DB)
    if position_type == "machines":
        all_pos = [p for p in all_pos if p["is_service"] is False]
    elif position_type == "services":
        all_pos = [p for p in all_pos if p["is_service"] is True]

    # Filtr contract_type (S=najem, U=usługa) — in-memory
    if contract_type and contract_type in ("S", "U"):
        all_pos = [p for p in all_pos if (p.get("contract_type") or "S") == contract_type]

    # Filtry contractor_id / city / internal_number
    all_pos = _apply_position_filters(all_pos, contractor_id=contractor_id, city=city)

    # Filtr category_main (drilldown kategorii) — in-memory
    if category_main:
        cm_set = set(category_main)
        all_pos = [p for p in all_pos if p["category_main"] in cm_set]

    # Filtr category_sub1 (drilldown kategorii sub1) — in-memory
    if category_sub1:
        all_pos = [p for p in all_pos if p.get("category_sub1") == category_sub1]

    # Agregacja per pozycja (machine_id lub service_id)
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
        # RAO: 3 kategorie — maszyny (machine_id), usługi zwykłe (service_id),
        # usługi dodatkowe (additional_service_id). Kolizja ID między services
        # i additional_services — użyj prefixu żeby uniknąć zderzenia bucketów.
        if p.get("is_additional_service"):
            key = ("addl", p.get("additional_service_id"))
        elif p["is_service"]:
            key = ("svc", p["service_id"])
        else:
            key = ("mach", p["machine_id"])
        agg[key]["name"] = p["article_name"]
        agg[key]["internal_number"] = p["internal_number"]
        agg[key]["is_service"] = p["is_service"]
        agg[key]["category_main"] = p["category_main"]
        agg[key]["revenue"] += p["revenue"]
        agg[key]["rented_days"] += clamp_days(p["clamped_days"]) if not p["is_service"] else 0  # RAO-P1-016
        agg[key]["contracts"].add(p["contract_id"])
        agg[key]["times_billed"] += 1

    # Build response items — klucz to tupla ("mach"|"svc"|"addl", id); wyciągnij ID
    items = [
        PositionStatItem(
            article_id=aid[1] if isinstance(aid, tuple) else aid,
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

    # Sortuj po revenue descending (default) lub po sort_by z whitelist
    if sort_by and sort_by in ALLOWED_SORT:
        field = _SORT_FIELD_ALIASES.get(sort_by, sort_by)
        reverse = sort_dir == "desc"
        # string-safe klucz: dla pól tekstowych użyj "", dla liczbowych 0
        def _key(x: PositionStatItem):
            v = getattr(x, field, None)
            if v is None:
                return "" if field in ("article_name", "internal_number", "category_main") else 0
            return v
        items.sort(key=_key, reverse=reverse)
    else:
        items.sort(key=lambda x: x.revenue, reverse=True)

    total_revenue = sum(item.revenue for item in items)
    total_count = len(items)

    # RAO-P2-053: paginacja — stosuj tylko gdy limit podany (backward compat: brak limitu = wszystkie)
    if limit is not None:
        items = items[offset : offset + limit]
    elif offset:
        items = items[offset:]

    return PositionStatsResponse(
        date_from=df,
        date_to=dt,
        type=position_type,
        total_revenue=total_revenue,
        total_machines_revenue=total_machines_rev,
        total_services_revenue=total_services_rev,
        total_count=total_count,
        limit=limit,
        offset=offset,
        items=items,
    )


# ---------------------------------------------------------------------------
# RAO-P2-056: Statystyki po contract_type (S=najem, U=usługa)
# ---------------------------------------------------------------------------

@router.get("/by-contract-type", response_model=ContractTypeStatsResponse)
async def by_contract_type(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki zagregowane po contract_type (S=najem, U=usługa) — RAO-P2-056.

    Grupuje pozycje umów po typie umowy nadrzędnej (Contract.contract_type):
      - "S" → umowa najmu (maszyny)
      - "U" → umowa usługi

    Zwraca per-typ: liczbę umów, pozycji, unikalnych artykułów, dni wynajmu, przychód.
    Filtry contractor_id / city opcjonalne (analogicznie do /stats/positions).
    Archiwalne maszyny uwzględnione (statystyki historyczne).
    RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    """
    df, dt = _validate_date_range(date_from, date_to)

    all_pos = await _compute_position_revenues(db, df, dt, service_filter=None)
    all_pos = _apply_position_filters(all_pos, contractor_id=contractor_id, city=city)

    # Agregacja per contract_type (logika w calc.py — testowalny pure function)
    grouped = aggregate_by_contract_type(all_pos)

    items = [
        ContractTypeStatItem(
            contract_type=g["contract_type"],
            contract_type_label=g["contract_type_label"],
            contracts_count=g["contracts_count"],
            positions_count=g["positions_count"],
            articles_count=g["articles_count"],
            rented_days=g["rented_days"],
            revenue=g["revenue"],
        )
        for g in grouped
    ]
    total_revenue = sum(item.revenue for item in items)

    return ContractTypeStatsResponse(
        date_from=df,
        date_to=dt,
        total_revenue=total_revenue,
        items=items,
    )


@router.get("/by-branch", response_model=ByBranchStatsResponse)
async def by_branch(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contractor_id: int | None = Query(None, description="Filtruj po kontrahencie"),
    city: str | None = Query(None, description="Filtruj po mieście umowy (case-insensitive)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Statystyki zagregowane po oddziale (branch) — RAO-P1-055.

    Grupuje pozycje umów po `contracts.branch_id` (FK do branches).
    Umowy bez przypisanego oddziału (branch_id IS NULL) trafiają do
    wiersza "(bez oddziału)" — na końcu listy.

    Zwraca per-oddział: liczbę umów, pozycji, unikalnych artykułów,
    dni wynajmu, przychód.

    Filtry `contractor_id` / `city` opcjonalne (analogicznie do /stats/positions).
    Archiwalne maszyny uwzględnione (statystyki historyczne).
    RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe umowy.
    """
    from settings.models import Branch

    df, dt = _validate_date_range(date_from, date_to)

    all_pos = await _compute_position_revenues(db, df, dt, service_filter=None)
    all_pos = _apply_position_filters(all_pos, contractor_id=contractor_id, city=city)

    # Pobierz nazwy oddziałów do mapowania branch_id → branch_name
    branches_q = await db.execute(select(Branch.id, Branch.name))
    branches = [{"id": r[0], "name": r[1]} for r in branches_q.all()]

    # Agregacja per branch (logika w calc.py — testowalny pure function)
    grouped = aggregate_by_branch(all_pos, branches=branches)

    items = [
        BranchStatItem(
            branch_id=g["branch_id"],
            branch_name=g["branch_name"],
            contracts_count=g["contracts_count"],
            positions_count=g["positions_count"],
            articles_count=g["articles_count"],
            rented_days=g["rented_days"],
            revenue=g["revenue"],
        )
        for g in grouped
    ]
    total_revenue = sum(item.revenue for item in items)

    return ByBranchStatsResponse(
        date_from=df,
        date_to=dt,
        total_revenue=total_revenue,
        items=items,
    )



# ---------------------------------------------------------------------------
# RAO-P2-051: Cache management (admin only)
# ---------------------------------------------------------------------------

@router.post("/cache/clear")
async def clear_cache(
    _: User = Depends(get_current_user),
):
    """Wyczyść cały cache statystyk/słowników (admin). Zwraca liczbę usuniętych wpisów."""
    from auth.models import User as _U
    # NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. Brak admin check.
    removed = cache.clear()
    return {"cleared": removed, "remaining": cache.stats()["entries"]}


@router.get("/cache/stats")
async def cache_stats(
    _: User = Depends(get_current_user),
):
    """Statystyki cache (liczba wpisów)."""
    return cache.stats()


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
    """Contracts printed but with stale print_hash (print-relevant data changed after print).

    RAO: print_hash IS NULL + print_date IS NOT NULL = nieaktualny wydruk.
    (print_hash is set at print time, cleared on any print-relevant mutation.)
    """
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
            Contract.print_hash.is_(None),  # RAO: invalidated by mutation
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
    """Commission report: margin per salesperson × commission_rate (RAO-P1-018).

    Prowizja liczona WYŁĄCZNIE od rzeczywistych rozliczeń (contract_settlements).
    Brak fallbacku do szacunkowego przychodu z pozycji umowy.
    Umowy bez rozliczeń nie wliczają się do prowizji.
    """
    from settings.models import Salesperson
    from settlements.models import ContractSettlement
    df, dt = _validate_date_range(date_from, date_to)

    # Prowizja od marży z contract_settlements (rzeczywiste rozliczenia)
    settlement_q = await db.execute(
        select(
            Contract.salesperson_id,
            func.sum(ContractSettlement.cost_client - ContractSettlement.cost_company).label("total_margin")
        )
        .join(ContractSettlement, Contract.id == ContractSettlement.contract_id)
        .where(and_(*_contract_date_filter(df, dt)))
        .where(Contract.salesperson_id.isnot(None))
        .where(ContractSettlement.cost_client.isnot(None))
        .where(ContractSettlement.cost_company.isnot(None))
        .group_by(Contract.salesperson_id)
    )
    settlement_margins = {r[0]: r[1] for r in settlement_q.all()}

    # Liczba umów z rozliczeniem per handlowiec (tylko umowy z kompletnym settlement)
    settled_contracts_q = await db.execute(
        select(
            Contract.salesperson_id,
            func.count(func.distinct(Contract.id)).label("contracts_count")
        )
        .join(ContractSettlement, Contract.id == ContractSettlement.contract_id)
        .where(and_(*_contract_date_filter(df, dt)))
        .where(Contract.salesperson_id.isnot(None))
        .where(ContractSettlement.cost_client.isnot(None))
        .where(ContractSettlement.cost_company.isnot(None))
        .group_by(Contract.salesperson_id)
    )
    settled_counts = {r[0]: r[1] for r in settled_contracts_q.all()}

    sp_q = await db.execute(
        select(Salesperson.id, Salesperson.name, Salesperson.commission_rate)
        .where(Salesperson.is_active == True)
        .order_by(Salesperson.name)
    )
    salespeople = {r[0]: {"name": r[1], "rate": r[2]} for r in sp_q.all()}

    items = []
    for sp_id, sp_data in salespeople.items():
        rate = sp_data["rate"] or Decimal(0)
        margin = settlement_margins.get(sp_id, Decimal("0.00"))
        base_amount = (margin or Decimal("0.00")).quantize(Decimal("0.01"))
        commission = (base_amount * rate / Decimal(100)).quantize(Decimal("0.01"))
        contracts_count = settled_counts.get(sp_id, 0)

        items.append(SalespersonCommissionItem(
            salesperson_id=sp_id,
            salesperson_name=sp_data["name"],
            commission_rate=sp_data["rate"],
            contracts_count=contracts_count,
            total_revenue=base_amount,  # revenue = margin (prowizja od marży, nie od przychodu)
            total_margin=base_amount,
            commission_amount=commission,
        ))

    items.sort(key=lambda x: x.commission_amount, reverse=True)
    grand_margin = sum(i.total_margin for i in items)
    grand_commission = sum(i.commission_amount for i in items)

    return CommissionReportResponse(
        date_from=df, date_to=dt,
        items=items,
        grand_total_revenue=grand_margin,
        grand_total_margin=grand_margin,
        grand_total_commission=grand_commission,
    )


@router.get(
    "/commissions/{salesperson_id}/contracts",
    response_model=SalespersonCommissionContractsResponse,
)
async def salesperson_commission_contracts(
    salesperson_id: int,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Contract-level commission detail for one active salesperson."""
    from stats.service import get_salesperson_commission_contracts
    df, dt = _validate_date_range(date_from, date_to)
    salesperson = await db.scalar(
        select(Salesperson).where(
            Salesperson.id == salesperson_id,
            Salesperson.is_active == True,
        )
    )
    if salesperson is None:
        raise HTTPException(status_code=404, detail="Handlowiec nie istnieje")
    items = await get_salesperson_commission_contracts(
        db, salesperson_id, df, dt, salesperson=salesperson
    )
    return SalespersonCommissionContractsResponse(
        salesperson_id=salesperson.id,
        salesperson_name=salesperson.name,
        date_from=df,
        date_to=dt,
        items=items,
        total_revenue=sum((item["total_revenue"] for item in items), Decimal("0.00")),
        total_company_cost=sum((item["total_company_cost"] for item in items), Decimal("0.00")),
        total_earnings=sum((item["earnings"] for item in items), Decimal("0.00")),
        total_commission=sum((item["commission_amount"] for item in items), Decimal("0.00")),
    )
