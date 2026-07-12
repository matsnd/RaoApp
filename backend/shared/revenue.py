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

from machines.models import Machine
from services.models import Service
from contracts.models import Contract, ContractPosition, PositionCondition
from contractors.models import Contractor
from settlements.models import ContractSettlement
from stats.calc import calculate_position_value


# ── RAO-P2-032: Algorytm cena_pozycji (lookup) — reimplementacja starej funkcji SQL ──

def compute_position_value_lookup(
    rental_days: int | None,
    conditions: list[dict],
    quantity: int | None = None,
    is_service: bool = False,
) -> Decimal:
    """
    Reimplementacja `cena_pozycji` z starej aplikacji WinForms.

    Algorytm (lookup, NIE kaskadowe):
    1. Jeśli liczba okresów > max(liczba_dni where oplata2>0):
       - Weź ostatni warunek (order by id desc) gdzie liczba_dni >= w.liczba_dni
       - cena = oplata2 (lub oplata1 jeśli oplata2=0)
    2. W przeciwnym razie:
       - Weź pierwszy warunek (order by id) gdzie liczba_dni <= w.liczba_dni
       - cena = oplata2 (lub oplata1 jeśli oplata2=0)
    3. revenue = cena × liczba okresów

    Source: AppRao/rao/FormU4.cs:1390-1396 + migrator/translated_objects/SQL_SCALAR_FUNCTION_cena_pozycji.sql
    """
    # Phase 2: service contracts use quantity (hours) as the period value.
    period_value = (quantity if is_service else rental_days) or 0
    if not conditions or period_value <= 0:
        return Decimal("0.00")

    # Sort by period_count (liczba_dni) — zgodnie ze starą funkcją
    sorted_conds = sorted(conditions, key=lambda c: c.get("period_count") or 0)

    # max(liczba_dni where oplata2>0)
    max_pc_with_oplata2 = max(
        (c.get("period_count") or 0 for c in sorted_conds if (c.get("rate2") or 0) > 0),
        default=0,
    )

    rate = Decimal("0.00")
    if period_value > max_pc_with_oplata2:
        # powyżej zakresu: ostatni warunek gdzie liczba_dni <= period_value
        candidates = [c for c in sorted_conds if (c.get("period_count") or 0) <= period_value]
        if candidates:
            c = candidates[-1]  # ostatni (najwyższy period_count)
            op2 = Decimal(str(c.get("rate2") or 0))
            op1 = Decimal(str(c.get("rate1") or 0))
            rate = op2 if op2 > 0 else op1
    else:
        # w zakresie: pierwszy warunek gdzie liczba_dni >= period_value
        candidates = [c for c in sorted_conds if (c.get("period_count") or 0) >= period_value]
        if candidates:
            c = candidates[0]  # pierwszy (najniższy period_count)
            op2 = Decimal(str(c.get("rate2") or 0))
            op1 = Decimal(str(c.get("rate1") or 0))
            rate = op2 if op2 > 0 else op1

    if rate <= 0:
        return Decimal("0.00")

    # revenue = cena × liczba okresów
    return rate * period_value


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
    contract_ids: set[int] | None = None,
) -> list[dict]:
    """
    Fetch positions+conditions+settlements for contracts overlapping [df, dt],
    compute value per position using 3 sources (actual > lookup > tiered).

    RAO-P2-062 Faza 1: legacy filter usuniety — contracts zawiera tylko nowe
    umowy (legacy przeniesione do archive_*). Statystyki archiwum osobno.

    Returns list of dicts with keys:
        position_id, machine_id, service_id, contract_id, contractor_id,
        machine_name, service_name, article_name (alias), internal_number,
        is_service, contract_number,
        contractor_name, rental_days, date_from, date_to,
        category_main, category_sub1, category_sub2, category_sub3,
        contract_date_from, clamped_days,
        revenue_actual, revenue_estimate_lookup, revenue_estimate_tiered,
        revenue, revenue_source

    Args:
        contract_ids: opcjonalny zbiór contract_id — gdy podany, pozycje są
            filtrowane w SQL (WHERE contract_id IN ...) zamiast w Pythonie.
            Używane przez /explorer/locations/city/{city} (RAO-P2-052).
    """
    stmt = (
        select(
            ContractPosition.id,            # p[0]
            ContractPosition.machine_id,    # p[1]  (was article_id)
            ContractPosition.contract_id,   # p[2]
            ContractPosition.rental_days,   # p[3]
            ContractPosition.billing_frequency,  # p[4]
            ContractPosition.unit_price,    # p[5]
            ContractPosition.quantity,      # p[6]
            Machine.name.label("machine_name"),  # p[7]  (was article_name)
            Machine.internal_number,        # p[8]
            ContractPosition.service_id,    # p[9]  (was Article.is_service; None=machine, !None=service)
            Contract.number.label("contract_number"),  # p[10]
            # RAO-P2-065 #2: coalesce Contractor.name z snapshot contractor_name
            # — snapshot może być NULL gdy umowa ma contractor_id (FK) ale nie
            # zapisano denormalizowanej nazwy. LEFT JOIN rozwiązuje z contractors.
            func.coalesce(Contractor.name, Contract.contractor_name).label("contractor_name"),  # p[11]
            Contract.contractor_id,         # p[12]
            Contract.date_from,             # p[13]
            Contract.date_to,               # p[14]
            Machine.category_main,          # p[15]
            Machine.category_sub1,          # p[16]
            Machine.category_sub2,          # p[17]
            Machine.category_sub3,          # p[18]
            Contract.city,                  # p[19] — RAO: filtr city w stats
            Contract.contract_type,         # p[20] — RAO-P2-056: grupowanie po S/U
            Contract.branch_id,             # p[21] — RAO-P1-055: grupowanie po oddziale
            Service.name.label("service_name"),  # p[22] — LEFT JOIN, NULL dla machine pozycji
        )
        .select_from(ContractPosition)
        .join(Contract, Contract.id == ContractPosition.contract_id)
        # RAO-P2-065 #2: LEFT JOIN contractors — contractor_name snapshot NULL
        # dla umów z contractor_id (FK) — rozwiązujemy nazwę z contractors.name
        .outerjoin(Contractor, Contractor.id == Contract.contractor_id)
        # articles split: LEFT JOIN machines + services (pozycja ma machine_id LUB service_id)
        .outerjoin(Machine, Machine.id == ContractPosition.machine_id)
        .outerjoin(Service, Service.id == ContractPosition.service_id)
    )
    # RAO-P0-006/BUG-6: df/dt mogą być None (preset='all' = brak filtra daty).
    # Buduj warunki tylko dla nie-None wartości.
    _date_conds = []
    if dt is not None:
        _date_conds.append(Contract.date_from <= dt)
    if df is not None:
        _date_conds.append(Contract.date_to >= df)
    if _date_conds:
        stmt = stmt.where(and_(*_date_conds))
    if service_filter is not None:
        # articles split: service_filter=True → tylko usługi (service_id != None);
        # False → tylko maszyny (machine_id != None); None → wszystkie
        if service_filter:
            stmt = stmt.where(ContractPosition.service_id.isnot(None))
        else:
            stmt = stmt.where(ContractPosition.machine_id.isnot(None))
    if exclude_archival:
        # maszyny: Machine.is_archival == False; usługi: Service.is_archival == False
        # (pozycja ma machine_id LUB service_id — coalesce rozwiązuje NULL z drugiego JOIN)
        stmt = stmt.where(func.coalesce(Machine.is_archival, Service.is_archival) == False)
        # is_external dotyczy tylko maszyn (Service nie ma tej flagi) — coalesce z False
        stmt = stmt.where(func.coalesce(Machine.is_external, False) == False)  # RAO-P1-027
    if category_main_filter:
        # kategorie tylko dla maszyn — service pozycje mają NULL i zostaną odfiltrowane
        stmt = stmt.where(Machine.category_main.in_(category_main_filter))
    if category_sub1_filter:
        stmt = stmt.where(Machine.category_sub1 == category_sub1_filter)
    if category_sub2_filter:
        stmt = stmt.where(Machine.category_sub2 == category_sub2_filter)
    # RAO-P2-052: filtr po konkretnych kontraktach (SQL WHERE IN) — używany
    # przez /explorer/locations/city/{city} po wstępnym zmatchowaniu miasta w SQL.
    if contract_ids is not None:
        if not contract_ids:
            return []  # pusty zbiór → brak wyników (uniknij nieprawidłowego `IN ()`)
        stmt = stmt.where(ContractPosition.contract_id.in_(list(contract_ids)))

    pos_result = await db.execute(stmt)
    positions = pos_result.all()

    # RAO Faza 2a (opcja E): NIE early-return gdy brak positions — umowa może mieć
    # tylko unmapped settlements (position_id=NULL). Unmapped block na końcu funkcji
    # doda syntetyczne wiersze. Early-return skipowałby je.
    pos_ids = [p[0] for p in positions]

    # 1. Pobierz warunki rozliczenia (position_conditions) — skip gdy brak positions
    conds_by_pos = defaultdict(list)
    if pos_ids:
        cond_result = await db.execute(
            select(
                PositionCondition.position_id,
                PositionCondition.rate1,
                PositionCondition.rate2,
                PositionCondition.period_count,
                PositionCondition.period_from,
                PositionCondition.period_to,
            )
            .where(PositionCondition.position_id.in_(pos_ids))
            .order_by(PositionCondition.position_id, PositionCondition.period_from)
        )
        cond_rows = cond_result.all()
        for c in cond_rows:
            conds_by_pos[c[0]].append({
                "rate1": c[1], "rate2": c[2], "period_count": c[3],
                "period_from": c[4], "period_to": c[5],
            })

    # 2. Pobierz settlements (rzeczywiste rozliczenia) — skip gdy brak positions
    sett_by_pos = {}
    if pos_ids:
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
        # articles split: is_service z position type (service_id != None), nie contract_type
        is_service = p[9] is not None  # service_id is not None → usługa

        # 3 źródła przychodu
        revenue_actual = sett_by_pos.get(pid)  # None jeśli brak settlements
        revenue_estimate_lookup = compute_position_value_lookup(
            rental_days=p[3],
            conditions=conds,
            quantity=p[6],
            is_service=is_service,
        )
        revenue_estimate_tiered = calculate_position_value(
            rental_days=p[3],
            billing_frequency=p[4],
            unit_price=p[5],
            quantity=p[6],
            conditions=conds,
            is_service=is_service,
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
        # RAO-P0-006/BUG-6: df/dt mogą być None (preset='all' = brak filtra daty).
        # Gdy df=None → clamp od dołu = contract.date_from (nie ograniczaj).
        # Gdy dt=None → clamp od góry = contract.date_to (nie ograniczaj).
        if p[13] is None or p[14] is None:
            # Umowa bez daty końcowej — użyj df/dt jako fallback (jeśli też None → 0 dni)
            c_from = df if df is not None else p[13]
            c_to = dt if dt is not None else p[14]
            if c_from is None or c_to is None:
                # Brak jakiejkolwiek daty — nie da się policzyć dni
                clamped_days = 0
            else:
                clamped_days = max((c_to - c_from).days + 1, 0)
        else:
            c_from = p[13] if (df is None or p[13] >= df) else df
            c_to = p[14] if (dt is None or p[14] <= dt) else dt
            clamped_days = max((c_to - c_from).days + 1, 0)

        results.append({
            "position_id": pid,
            "machine_id": p[1],           # was article_id (articles split)
            "service_id": p[9],           # NEW: service_id (None dla machine pozycji)
            "contract_id": p[2],
            "rental_days": p[3] or 0,
            "machine_name": p[7],         # was article_name (Machine.name)
            "service_name": p[22],        # NEW: Service.name (None dla machine pozycji)
            "article_name": p[7] or p[22],  # backward compat: coalesce(machine_name, service_name)
            "internal_number": p[8],
            "is_service": p[9] is not None,  # was p[9]=Article.is_service; now service_id != None
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
            # kategorie tylko dla maszyn (Service nie ma kategorii → NULL dla service pozycji)
            "category_main": p[15],
            "category_sub1": p[16],
            "category_sub2": p[17],
            "category_sub3": p[18],
            "city": p[19],                  # RAO: filtr city w stats
            "contract_type": p[20] or "S",  # RAO-P2-056: "S" (najem) | "U" (usługa); fallback "S"
            "branch_id": p[21],             # RAO-P1-055: FK do branches (może być NULL dla starych umów)
        })

    # RAO Faza 2a (opcja E): unmapped settlements — syntetyczne wiersze dla analytics.
    # Pozycje FA nieobecne w umowie (position_id=NULL, service_fee_id=NULL, source='fa_unmapped')
    # dostają syntetyczny wiersz z machine_id=None, service_id=None, is_service=None, category_*=None.
    # revenue = cost_client (actual), clamped_days=0 (nie zaburza utilization).
    # Filtry service_filter/exclude_archival/category_* NIE aplikowane (unmapped nie ma Machine/Service).
    unmapped_stmt = (
        select(
            ContractSettlement.id,                       # u[0]
            ContractSettlement.contract_id,              # u[1]
            ContractSettlement.article_name_snapshot,    # u[2]
            ContractSettlement.fakturownia_product_id,   # u[3]
            ContractSettlement.cost_client,              # u[4]
            ContractSettlement.settled_at,               # u[5]
            Contract.number.label("contract_number"),    # u[6]
            # RAO-P2-065 #2: coalesce Contractor.name z snapshot (jak w głównym zapytaniu)
            func.coalesce(Contractor.name, Contract.contractor_name).label("contractor_name"),  # u[7]
            Contract.contractor_id,                      # u[8]
            Contract.date_from,                          # u[9]
            Contract.date_to,                            # u[10]
            Contract.city,                               # u[11]
            Contract.contract_type,                      # u[12]
            Contract.branch_id,                          # u[13]
        )
        .select_from(ContractSettlement)
        .join(Contract, Contract.id == ContractSettlement.contract_id)
        # RAO-P2-065 #2: LEFT JOIN contractors — rozwiązuj nazwę z contractor_id
        .outerjoin(Contractor, Contractor.id == Contract.contractor_id)
        .where(ContractSettlement.position_id.is_(None))
        .where(ContractSettlement.service_fee_id.is_(None))
        .where(ContractSettlement.source == "fa_unmapped")
        .where(ContractSettlement.cost_client.isnot(None))
    )
    if _date_conds:
        unmapped_stmt = unmapped_stmt.where(and_(*_date_conds))
    if contract_ids is not None:
        if not contract_ids:
            return results  # pusty zbiór
        unmapped_stmt = unmapped_stmt.where(ContractSettlement.contract_id.in_(list(contract_ids)))

    unmapped_result = await db.execute(unmapped_stmt)
    unmapped_rows = unmapped_result.all()

    for u in unmapped_rows:
        cost_client = Decimal(str(u[4])) if u[4] is not None else Decimal("0")
        results.append({
            "position_id": None,
            "machine_id": None,           # was article_id (articles split)
            "service_id": None,           # NEW: unmapped nie ma service_id
            "contract_id": u[1],
            "rental_days": 0,
            "machine_name": None,         # was article_name
            "service_name": None,         # NEW
            "article_name": u[2] or "(niezmapowane z FA)",  # backward compat: snapshot z FA
            "internal_number": None,
            "is_service": None,
            "contract_number": u[6],
            "contractor_name": u[7],
            "contractor_id": u[8],
            "date_from": u[9],
            "date_to": u[10],
            "contract_date_from": u[9],
            "clamped_days": 0,  # unmapped nie zaburza utilization
            "revenue_actual": cost_client,
            "revenue_estimate_lookup": Decimal("0"),
            "revenue_estimate_tiered": Decimal("0"),
            "revenue": cost_client,
            "revenue_source": "actual",
            "category_main": None,
            "category_sub1": None,
            "category_sub2": None,
            "category_sub3": None,
            "city": u[11],
            "contract_type": u[12] or "S",
            "branch_id": u[13],
        })

    # RAO: Usługi dodatkowe (contract_settlements z service_fee_id IS NOT NULL).
    # Syntetyczne wiersze dla analytics — jak unmapped, ale z service_id i nazwą usługi.
    # Dzięki temu wszystkie endpointy używające compute_position_revenues (fleet-summary,
    # top-machines, by-category, by-period, by-contract-type, by-branch, locations,
    # commissions) automatycznie uwzględniają przychód z usług dodatkowych.
    from contracts.models import ContractServiceFee
    from additional_services.models import AdditionalService

    addl_stmt = (
        select(
            ContractSettlement.id,                       # a[0]
            ContractSettlement.contract_id,              # a[1]
            ContractSettlement.cost_client,              # a[2]
            ContractSettlement.settled_at,               # a[3]
            AdditionalService.id,                        # a[4]
            AdditionalService.name,                      # a[5]
            Contract.number.label("contract_number"),    # a[6]
            func.coalesce(Contractor.name, Contract.contractor_name).label("contractor_name"),  # a[7]
            Contract.contractor_id,                      # a[8]
            Contract.date_from,                          # a[9]
            Contract.date_to,                            # a[10]
            Contract.city,                               # a[11]
            Contract.contract_type,                      # a[12]
            Contract.branch_id,                          # a[13]
        )
        .select_from(ContractSettlement)
        .join(Contract, Contract.id == ContractSettlement.contract_id)
        .outerjoin(Contractor, Contractor.id == Contract.contractor_id)
        .join(ContractServiceFee, ContractServiceFee.id == ContractSettlement.service_fee_id)
        .join(AdditionalService, AdditionalService.id == ContractServiceFee.additional_service_id)
        .where(ContractSettlement.service_fee_id.isnot(None))
        .where(ContractSettlement.cost_client.isnot(None))
    )
    if _date_conds:
        addl_stmt = addl_stmt.where(and_(*_date_conds))
    if contract_ids is not None:
        if not contract_ids:
            return results  # pusty zbiór
        addl_stmt = addl_stmt.where(ContractSettlement.contract_id.in_(list(contract_ids)))

    # service_filter=False → tylko maszyny, pomiń usługi dodatkowe.
    # service_filter=True lub None → uwzględnij usługi dodatkowe.
    if service_filter is False:
        addl_rows = []
    else:
        addl_result = await db.execute(addl_stmt)
        addl_rows = addl_result.all()

    for a in addl_rows:
        cost_client = Decimal(str(a[2])) if a[2] is not None else Decimal("0")
        results.append({
            "position_id": None,
            "machine_id": None,
            "service_id": a[4],            # AdditionalService.id
            "contract_id": a[1],
            "rental_days": 0,
            "machine_name": None,
            "service_name": a[5],          # AdditionalService.name
            "article_name": a[5],          # backward compat
            "internal_number": None,
            "is_service": True,            # usługa dodatkowa = usługa
            "contract_number": a[6],
            "contractor_name": a[7],
            "contractor_id": a[8],
            "date_from": a[9],
            "date_to": a[10],
            "contract_date_from": a[9],
            "clamped_days": 0,
            "revenue_actual": cost_client,
            "revenue_estimate_lookup": Decimal("0"),
            "revenue_estimate_tiered": Decimal("0"),
            "revenue": cost_client,
            "revenue_source": "actual",
            "category_main": None,
            "category_sub1": None,
            "category_sub2": None,
            "category_sub3": None,
            "city": a[11],
            "contract_type": a[12] or "S",
            "branch_id": a[13],
        })

    return results
