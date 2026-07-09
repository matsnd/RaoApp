from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.models import User
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contracts.schemas import ContractCreate, PositionCreate, ConditionCreate, ContractServiceFeeCreate
from shared.exceptions import bad_request, forbidden, not_found, conflict
from shared.locations import resolve_postal_code_id


async def generate_contract_number(db: AsyncSession, contract_type: str, branch_id: int | None = None) -> tuple[str, int]:
    """Generate a unique contract number.

    RAO-P0-030: Uses SELECT ... FOR UPDATE on Company row to serialize
    concurrent contract creation. Falls back to retry on IntegrityError
    (defensive — UNIQUE index on contracts.number is the last line of defense).

    RAO-P1-022: Format S{NNN}/{ROK}[G] — wszystkie umowy zaczynają się na S.
    G na końcu jeśli oddział ≠ Warszawa (id=1).
    Zgodne ze starą aplikacją WinForms (FormU4.cs:734-764 + 2645-2655).
    """
    from settings.models import Company, Branch
    from sqlalchemy import text as sa_text

    # Lock the Company row to serialize concurrent number generation
    company_result = await db.execute(
        sa_text("SELECT numbering_start FROM company WHERE id = 1 FOR UPDATE")
    )
    start = company_result.scalar_one_or_none() or 1

    max_result = await db.execute(select(func.max(Contract.auto_number)))
    current_max = max_result.scalar_one_or_none() or 0

    new_number = max(start, current_max) + 1
    year = datetime.now().year

    # RAO-P1-022: G na końcu jeśli oddział ≠ Warszawa (id=1)
    # Zgodne ze starą aplikacją: cbxoddzial_SelectedIndexChanged (FormU4.cs:2645-2655)
    suffix = ""
    if branch_id and branch_id != 1:  # id=1 = Warszawa, wszystko inne = Gdańsk
        suffix = "G"

    # RAO-P1-022: Zawsze prefiks "S" (nie contract_type) — zgodne z wymogiem klienta
    return f"S{new_number:03d}/{year}{suffix}", new_number


async def copy_fee_templates(db: AsyncSession, contract_id: int, contract_type: str):
    from settings.models import ServiceFeeTemplate, FeePresetGroup
    # Prefer the default preset for this contract type; fallback to all active templates
    # only when no default group is configured (legacy / test data).
    default_group = await db.execute(
        select(FeePresetGroup).where(
            FeePresetGroup.contract_type == contract_type,
            FeePresetGroup.is_default == True,
        )
    )
    group = default_group.scalar_one_or_none()
    if group:
        stmt = (
            select(ServiceFeeTemplate)
            .where(ServiceFeeTemplate.preset_id == group.id)
            .where(ServiceFeeTemplate.is_active == True)
            .order_by(ServiceFeeTemplate.sort_order)
        )
    else:
        stmt = (
            select(ServiceFeeTemplate)
            .where(ServiceFeeTemplate.contract_type == contract_type)
            .where(ServiceFeeTemplate.is_active == True)
            .order_by(ServiceFeeTemplate.sort_order)
        )
    templates = await db.execute(stmt)
    for t in templates.scalars():
        db.add(ContractServiceFee(
            contract_id=contract_id,
            sort_order=t.sort_order,
            name=t.name,
            amount_from=t.amount_from,
            amount_to=t.amount_to,
            description=t.description,
            is_active=t.is_active,
        ))
    await db.commit()


def _condition_effective_rate(c: PositionCondition) -> Decimal | None:
    """RAO-P2-071: new source is rate1; rate2 is legacy/fallback only."""
    if c.rate1 is not None and c.rate1 > 0:
        return c.rate1
    if c.rate2 is not None and c.rate2 > 0:
        return c.rate2
    return None


def _format_rate(value: Decimal | None) -> str:
    if value is None:
        return "0,00"
    return f"{value:.2f}".replace('.', ',')


def _sync_condition_derived_fields(cond: PositionCondition) -> None:
    """
    RAO-P2-071: period_count/rate2 are derived/sync columns for legacy consumers
    (stats/calc.py, shared/revenue.py). The new source of truth is
    period_from/period_to/rate1/is_flat_rate.

    - period_count mirrors period_to when period_to is known.
    - rate2 is kept only for legacy open-ended tiers where rate1 is missing.
      In the new UI rate1 is always set for every tier, so rate2 is nulled.
    """
    # Normalize rate2: only keep it when rate1 is missing (true legacy tier).
    if cond.rate1 is not None and cond.rate1 > 0:
        cond.rate2 = None

    # Sync period_count to the closed upper bound for backward compatibility.
    if cond.period_to is not None:
        cond.period_count = cond.period_to
    elif cond.period_from is not None and cond.period_from > 0:
        # Open-ended: legacy period_count is best represented by its start (or None)
        # when no explicit end exists. For compatibility, leave it None.
        cond.period_count = None
    else:
        cond.period_count = None


def _unit_labels(label: str | None, contract_type: str = "S") -> tuple[str, str]:
    """
    Returns (count_unit, rate_unit) for a billing label.

    Legacy format (c:\\Temp\\legacy_pdfs\\):
    - Rental: count="dni" (or "dzień" for 1), rate="doba"
    - Service: count="godzin", rate="godzina"
    """
    l = (label or "").lower()
    if "godz" in l or "godzina" in l:
        return "godzin", "godzina"
    if "mies" in l:
        return "mies.", "mies."
    if "tyg" in l:
        return "tyg.", "tyg."
    # Default for rental (S) is "doba"/"dni"; for service (U) "godzina"/"godzin" is used when
    # no explicit billing label was provided.
    if contract_type == "U":
        return "godz.", "godz."
    return "dni", "doba"


def _format_count_unit(count: int, unit: str) -> str:
    """Pluralize Polish count unit for the number 1 (dni -> dzień).
    0 and >=2 use the plural form. Other units keep short forms."""
    if count == 1 and unit == "dni":
        return "dzień"
    return unit


def _format_period_range(
    period_from: int | None,
    period_to: int | None,
    count_unit: str,
    is_flat_rate: bool = True,
) -> str:
    """Build a human-readable period range for PDF/print.

    Legacy format (from WinForms app, confirmed via c:\\Temp\\legacy_pdfs\\):
      - Flat rate:    "230,00zł / doba" (no range text — just rate in line)
      - Closed range: "1 - 3 dni"
      - Single day:   "1 dzień"
      - Open-ended:   "powyżej 3 dni"  (NOT "3 dni i więcej")
      - Service 0-X:  "do 8 godzin" (flat rate) / "0 - 8 godzin" (stawka per unit)
    """
    pf = period_from if period_from is not None else 1
    if pf < 0:
        pf = 0

    if period_to is not None:
        if period_to < pf:
            period_to = pf
        # P1-101: flat rate (ryczałt) with period_from=0 → "do X godzin"
        # (kwota całkowita, nie per jednostka)
        if is_flat_rate and pf == 0:
            return f"do {period_to} {_format_count_unit(period_to, count_unit)}"
        if pf == period_to:
            return f"{pf} {_format_count_unit(1, count_unit)}"
        return f"{pf} - {period_to} {_format_count_unit(period_to - pf + 1, count_unit)}"

    # Open-ended: flat rate (pf <= 1) has NO range prefix in legacy.
    # Legacy: "230,00zł / doba" — just the rate, no "powyżej 0 dni".
    if pf <= 1:
        return ""

    # Open-ended after a closed tier: "powyżej X dni" where X = pf - 1.
    threshold = pf - 1
    return f"powyżej {threshold} {_format_count_unit(threshold, count_unit)}"


def _normalize_conditions_for_format(
    conditions: list[PositionCondition],
) -> list[dict]:
    """
    Convert PositionCondition objects into a normalized list of:
        {period_from, period_to, rate, is_flat_rate, billing_label}

    New source-of-truth fields (period_from/period_to/rate1) are preferred.
    Legacy rows using period_count/rate2 are converted to equivalent ranges.
    """
    # If at least one condition has the new source fields, treat the whole set
    # as new data. Otherwise fall back to legacy period_count/rate2 parsing.
    has_new_fields = any(
        c.period_from is not None or c.period_to is not None
        for c in conditions
    )

    normalized: list[dict] = []
    if has_new_fields:
        for c in conditions:
            rate = _condition_effective_rate(c)
            if rate is None or rate <= 0:
                continue
            normalized.append({
                "period_from": c.period_from,
                "period_to": c.period_to,
                "rate": rate,
                "is_flat_rate": getattr(c, "is_flat_rate", True),
                "billing_label": c.billing_label,
            })
        return normalized

    # Legacy fallback: build cascading ranges from period_count/rate1/rate2
    # exactly like the old WinForms formatter.
    sorted_conds = sorted(
        conditions,
        key=lambda c: (c.period_count is None, c.period_count or 0),
    )
    current_end = 0

    for i, c in enumerate(sorted_conds):
        pc = c.period_count
        rate1 = c.rate1 if c.rate1 is not None and c.rate1 > 0 else None
        rate2 = c.rate2 if c.rate2 is not None and c.rate2 > 0 else None

        next_pc = None
        for j in range(i + 1, len(sorted_conds)):
            npc = sorted_conds[j].period_count
            if npc is not None:
                next_pc = npc
                break

        if rate1 is not None and pc is not None:
            start = current_end + 1
            end = pc
            if start <= end:
                normalized.append({
                    "period_from": start,
                    "period_to": end,
                    "rate": rate1,
                    "is_flat_rate": getattr(c, "is_flat_rate", True),
                    "billing_label": c.billing_label,
                })
                current_end = end

        if rate2 is not None:
            if rate1 is not None and pc is not None:
                start = pc + 1
            else:
                start = current_end + 1

            if next_pc is not None:
                end = next_pc - 1
            else:
                end = None

            if end is None or start <= end:
                if start > current_end or end is None:
                    normalized.append({
                        "period_from": start,
                        "period_to": end,
                        "rate": rate2,
                        "is_flat_rate": getattr(c, "is_flat_rate", True),
                        "billing_label": c.billing_label,
                    })
                    if end is not None:
                        current_end = end

    return normalized


def format_position_conditions_cascading(
    conditions: list[PositionCondition],
    contract_type: str = "S",
) -> str:
    """Buduje opis kaskadowych warunków rozliczenia (źródło prawdy: period_from/period_to/rate1).

    Przykład wyjścia (3 warunki):
      1 - 3 dni - 540,00 / doba
      4 - 16 dni - 410,00 / doba
      17 dni i więcej - 350,00 / doba

    RAO-P2-071: Obsługuje również stare dane oparte na period_count/rate2.
    """
    if not conditions:
        return ""

    normalized = _normalize_conditions_for_format(conditions)

    # Deduplicate by (period_from, period_to, rate) to avoid duplicates after migration
    seen = set()
    unique = []
    for n in normalized:
        key = (n["period_from"], n["period_to"], n["rate"])
        if key not in seen:
            seen.add(key)
            unique.append(n)

    # Sort closed-ended ranges first, then open-ended; within each group by start/end.
    unique.sort(
        key=lambda n: (
            n["period_to"] is None,
            n["period_from"] is None,
            n["period_from"] or 0,
            n["period_to"] or 0,
        )
    )

    lines = []
    for n in unique:
        label = n["billing_label"]
        if not label:
            label = "doba" if contract_type == "S" else "godzina"
        count_unit, rate_unit = _unit_labels(label, contract_type)

        is_flat = n.get("is_flat_rate", True)
        range_text = _format_period_range(
            n['period_from'], n['period_to'], count_unit, is_flat_rate=is_flat
        )
        if range_text:
            if is_flat:
                # P1-101: ryczałt — kwota całkowita, BEZ / unit
                lines.append(f"{range_text} - {_format_rate(n['rate'])}zł")
            else:
                # P1-101: stawka — kwota per jednostka, Z / unit
                lines.append(f"{range_text} - {_format_rate(n['rate'])}zł / {rate_unit}")
        else:
            # Flat rate with no range prefix
            if is_flat:
                lines.append(f"{_format_rate(n['rate'])}zł")
            else:
                lines.append(f"{_format_rate(n['rate'])}zł / {rate_unit}")

    return '\n'.join(lines)


async def apply_preset_to_contract(db: AsyncSession, contract_id: int, preset_id: int, replace: bool = True):
    from settings.models import FeePresetGroup, ServiceFeeTemplate
    contract = await db.get(Contract, contract_id)
    if not contract:
        from shared.exceptions import not_found
        raise not_found("Umowa")
    if contract.is_settled:
        from shared.exceptions import conflict
        raise conflict("Umowa jest rozliczona — modyfikacja zablokowana.")
    result = await db.execute(
        select(FeePresetGroup).where(FeePresetGroup.id == preset_id)
    )
    grp = result.scalar_one_or_none()
    if not grp:
        from shared.exceptions import not_found
        raise not_found("Zestaw usług")
    if replace:
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.contract_id == contract_id))
        await db.flush()
    templates = await db.execute(
        select(ServiceFeeTemplate)
        .where(ServiceFeeTemplate.preset_id == preset_id)
        .where(ServiceFeeTemplate.is_active == True)
        .order_by(ServiceFeeTemplate.sort_order)
    )
    for t in templates.scalars():
        db.add(ContractServiceFee(
            contract_id=contract_id,
            sort_order=t.sort_order,
            name=t.name,
            amount_from=t.amount_from,
            amount_to=t.amount_to,
            unit=t.unit,
            description=t.description,
            is_active=t.is_active,
        ))
    await db.commit()


class ContractService:
    async def verify_contract_access(
        self,
        db: AsyncSession,
        contract_id: int,
        user: User,
        allow_mutation: bool = False,
    ) -> Contract:
        """RAO-P0-049: IDOR guard — sprawdź czy użytkownik widzi/modyfikuje dany kontrakt.

        - admin widzi wszystko i może modyfikować
        - user/viewer widzi tylko własny branch
        - viewer może tylko odczytywać (allow_mutation=False)
        - kontrakty bez branch_id (legacy) są widoczne dla wszystkich zalogowanych
        """
        contract = await self.get_contract(db, contract_id)

        if user.role == "admin":
            if allow_mutation and contract.is_settled:
                raise conflict("Umowa jest rozliczona — modyfikacja zablokowana. Najpierw cofnij rozliczenie.")
            return contract

        if contract.branch_id is not None and contract.branch_id != user.branch_id:
            raise not_found("Umowa")  # 404 — nie ujawniaj istnienia cudzego zasobu

        if allow_mutation and user.role == "viewer":
            from shared.exceptions import forbidden
            raise forbidden("Tylko odczyt — brak uprawnień do modyfikacji.")

        if allow_mutation and contract.is_settled:
            raise conflict("Umowa jest rozliczona — modyfikacja zablokowana. Najpierw cofnij rozliczenie.")

        return contract

    async def list_contracts(
        self, db: AsyncSession,
        user: User,
        search: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        contract_type: str | None = None,
        is_settled: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        from contractors.models import Contractor
        from settings.models import Salesperson
        from contracts.schemas import ContractListItem

        stmt = select(Contract)
        if user.role != "admin":
            # user/viewer widzą tylko swój branch; NULL branch = legacy, visible to all
            stmt = stmt.where(
                (Contract.branch_id == user.branch_id) |
                (Contract.branch_id.is_(None))
            )
        if search:
            stmt = stmt.where(
                (Contract.number.ilike(f"%{search}%")) |
                (Contract.contractor_name.ilike(f"%{search}%"))
            )
        if date_from:
            stmt = stmt.where(Contract.date_from >= date_from)
        if date_to:
            stmt = stmt.where(Contract.date_to <= date_to)
        if contract_type:
            stmt = stmt.where(Contract.contract_type == contract_type)
        if is_settled is not None:
            if is_settled:
                # Rozliczone umowy
                stmt = stmt.where(Contract.is_settled == True)
            else:
                # Aktywne umowy: nie rozliczone i nie zamknięte (date_to >= dzisiaj)
                today = date.today()
                stmt = stmt.where(Contract.is_settled == False, Contract.date_to >= today)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Contract.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        contracts = result.scalars().all()

        # RAO-P0-035: Batch-fetch contractors & salespeople to eliminate N+1 queries
        contractor_ids = {c.contractor_id for c in contracts if not (c.contractor_name or "")}
        salesperson_ids = {c.salesperson_id for c in contracts if c.salesperson_id}

        contractor_map = {}
        if contractor_ids:
            ct_result = await db.execute(
                select(Contractor.id, Contractor.name).where(Contractor.id.in_(contractor_ids))
            )
            contractor_map = dict(ct_result.all())

        sp_map = {}
        if salesperson_ids:
            sp_result = await db.execute(
                select(Salesperson.id, Salesperson.name).where(Salesperson.id.in_(salesperson_ids))
            )
            sp_map = dict(sp_result.all())

        items = []
        for c in contracts:
            contractor_name = c.contractor_name or contractor_map.get(c.contractor_id, "")

            sp_name = sp_map.get(c.salesperson_id) if c.salesperson_id else None

            duration = None
            if c.date_from and c.date_to:
                duration = (c.date_to - c.date_from).days

            is_print_current = False
            if c.print_date and c.updated_at:
                is_print_current = c.print_date >= c.updated_at

            items.append(ContractListItem(
                id=c.id, contractor_id=c.contractor_id,
                contractor_name=contractor_name,
                number=c.number,
                contract_type=c.contract_type,
                type_label="Umowa najmu" if c.contract_type == "S" else "Umowa usługi",
                delivery_address=c.delivery_address,
                postal_code=c.postal_code,
                city=c.city,
                latitude=c.latitude,
                longitude=c.longitude,
                date_from=c.date_from, date_to=c.date_to,
                # RAO-P1-021/P2-033: total_value usunięte
                prepayment_amount=c.prepayment_amount,
                prepayment_document=c.prepayment_document,
                notes=c.notes,
                contact_person1=c.contact_person1,
                contact_phone1=c.contact_phone1,
                show_person1=c.show_person1,
                contact_person2=c.contact_person2,
                contact_phone2=c.contact_phone2,
                show_person2=c.show_person2,
                email=c.email,
                phone=c.phone,
                print_path=c.print_path,
                print_date=c.print_date,
                is_print_current=is_print_current,
                report_without_data=c.report_without_data,
                hide_delivery_address=c.hide_delivery_address,
                signatures_on_page1=c.signatures_on_page1,
                working_days_per_week=c.working_days_per_week,
                position_count=c.position_count,
                is_settled=c.is_settled,
                settled_at=c.settled_at,
                salesperson_name=sp_name,
                duration_days=duration,
                created_at=c.created_at,
                updated_at=c.updated_at,
            ))
        return items, total

    async def list_overdue_contracts(
        self, db: AsyncSession,
        user: User,
        page: int = 1,
        per_page: int = 50,
    ):
        """Lista przeterminowanych (zamkniętych) umów - date_to < dzisiaj i is_settled = false"""
        from contractors.models import Contractor
        from settings.models import Salesperson
        from contracts.schemas import ContractListItem

        today = date.today()
        stmt = select(Contract).where(
            Contract.date_to < today,
            Contract.is_settled == False
        )
        if user.role != "admin":
            stmt = stmt.where(
                (Contract.branch_id == user.branch_id) |
                (Contract.branch_id.is_(None))
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Contract.date_to.asc()).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        contracts = result.scalars().all()

        # RAO-P0-035: Batch-fetch contractors & salespeople to eliminate N+1 queries
        contractor_ids = {c.contractor_id for c in contracts if not (c.contractor_name or "")}
        salesperson_ids = {c.salesperson_id for c in contracts if c.salesperson_id}

        contractor_map = {}
        if contractor_ids:
            ct_result = await db.execute(
                select(Contractor.id, Contractor.name).where(Contractor.id.in_(contractor_ids))
            )
            contractor_map = dict(ct_result.all())

        sp_map = {}
        if salesperson_ids:
            sp_result = await db.execute(
                select(Salesperson.id, Salesperson.name).where(Salesperson.id.in_(salesperson_ids))
            )
            sp_map = dict(sp_result.all())

        items = []
        for c in contracts:
            contractor_name = c.contractor_name or contractor_map.get(c.contractor_id, "")

            sp_name = sp_map.get(c.salesperson_id) if c.salesperson_id else None

            duration = None
            if c.date_from and c.date_to:
                duration = (c.date_to - c.date_from).days

            is_print_current = False
            if c.print_date and c.updated_at:
                is_print_current = c.print_date >= c.updated_at

            items.append(ContractListItem(
                id=c.id, contractor_id=c.contractor_id,
                contractor_name=contractor_name,
                number=c.number,
                contract_type=c.contract_type,
                type_label="Umowa najmu" if c.contract_type == "S" else "Umowa usługi",
                delivery_address=c.delivery_address,
                postal_code=c.postal_code,
                city=c.city,
                latitude=c.latitude,
                longitude=c.longitude,
                date_from=c.date_from, date_to=c.date_to,
                # RAO-P1-021/P2-033: total_value usunięte
                prepayment_amount=c.prepayment_amount,
                prepayment_document=c.prepayment_document,
                notes=c.notes,
                contact_person1=c.contact_person1,
                contact_phone1=c.contact_phone1,
                show_person1=c.show_person1,
                contact_person2=c.contact_person2,
                contact_phone2=c.contact_phone2,
                show_person2=c.show_person2,
                email=c.email,
                phone=c.phone,
                print_path=c.print_path,
                print_date=c.print_date,
                is_print_current=is_print_current,
                report_without_data=c.report_without_data,
                hide_delivery_address=c.hide_delivery_address,
                signatures_on_page1=c.signatures_on_page1,
                working_days_per_week=c.working_days_per_week,
                position_count=c.position_count,
                is_settled=c.is_settled,
                settled_at=c.settled_at,
                salesperson_name=sp_name,
                duration_days=duration,
                created_at=c.created_at,
                updated_at=c.updated_at,
            ))
        return items, total

    async def get_contract(self, db: AsyncSession, contract_id: int) -> Contract:
        result = await db.execute(select(Contract).where(Contract.id == contract_id))
        contract = result.scalar_one_or_none()
        if not contract:
            raise not_found("Umowa")
        return contract

    async def apply_rate_preset_to_position(
        self,
        db: AsyncSession,
        pos_id: int,
        preset_id: int,
        user: User,
        replace: bool = True,
    ) -> list[PositionCondition]:
        """RAO-P1-001: Skopiuj warunki z cennika (ArticleRatePreset) do pozycji umowy.

        RAO-P0-048: ArticleRatePresetItem ma tylko period_count. Przy kopiowaniu
        do PositionCondition wyliczamy period_from/period_to kaskadowo. Jeśli
        item ma rate1+rate2, generujemy dwa PositionCondition: jeden z rate1, drugi
        z rate2, żeby uniknąć niejednoznaczności w period_from/period_to.
        """
        from settings.models import ArticleRatePreset, ArticleRatePresetItem

        pos_result = await db.execute(
            select(ContractPosition).where(ContractPosition.id == pos_id)
        )
        pos = pos_result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja umowy")

        await self.verify_contract_access(db, pos.contract_id, user, allow_mutation=True)

        preset = await db.get(ArticleRatePreset, preset_id)
        if not preset:
            raise not_found("Cennik")

        if replace:
            await db.execute(delete(PositionCondition).where(PositionCondition.position_id == pos_id))
            await db.flush()

        items_result = await db.execute(
            select(ArticleRatePresetItem)
            .where(ArticleRatePresetItem.preset_id == preset_id)
            .order_by(ArticleRatePresetItem.sort_order)
        )
        items = list(items_result.scalars())

        new_conditions = []
        current_end = 0
        for i, item in enumerate(items):
            pc = item.period_count
            has_rate1 = item.rate1 is not None and item.rate1 > 0
            has_rate2 = item.rate2 is not None and item.rate2 > 0

            next_pc = None
            for j in range(i + 1, len(items)):
                npc = items[j].period_count
                if npc is not None:
                    next_pc = npc
                    break

            # rate1 tier -> [current_end+1, period_count]
            if has_rate1 and pc is not None:
                cond1 = PositionCondition(
                    position_id=pos_id,
                    rate1=item.rate1,
                    rate2=None,
                    billing_label=item.billing_label,
                    period_count=pc,
                    period_from=current_end + 1,
                    period_to=pc,
                )
                db.add(cond1)
                new_conditions.append(cond1)
                current_end = pc

            # rate2 tier -> [pc+1, next_pc-1] or open-ended
            if has_rate2:
                r2_from = (pc + 1) if has_rate1 and pc is not None else (current_end + 1)
                r2_to = (next_pc - 1) if next_pc is not None else None

                if r2_to is None or r2_from <= r2_to:
                    cond2 = PositionCondition(
                        position_id=pos_id,
                        rate1=None,
                        rate2=item.rate2,
                        billing_label=item.billing_label,
                        period_count=r2_to,
                        period_from=r2_from,
                        period_to=r2_to,
                    )
                    db.add(cond2)
                    new_conditions.append(cond2)
                    if r2_to is not None:
                        current_end = r2_to

        await db.commit()
        return new_conditions

    async def get_last_conditions_for_article(
        self, db: AsyncSession, article_id: int, user: User
    ) -> dict | None:
        """RAO-P1-001: Warunki z najnowszej umowy zawierającej tę maszynę."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(ContractPosition)
            .join(Contract)
            .options(selectinload(ContractPosition.conditions))
            .options(selectinload(ContractPosition.contract))
            .where(ContractPosition.article_id == article_id)
            .order_by(Contract.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        pos = result.scalar_one_or_none()
        if not pos:
            return None
        await self.verify_contract_access(db, pos.contract_id, user)
        return {
            "source_contract_number": pos.contract.number,
            "source_contract_date": pos.contract.created_at,
            "source_position_id": pos.id,
            "conditions": pos.conditions,
        }

    async def create_contract(
        self, db: AsyncSession, data: ContractCreate, user: User
    ) -> Contract:
        # RAO-P0-030: Retry on IntegrityError (UNIQUE on contracts.number)
        from sqlalchemy.exc import IntegrityError
        max_retries = 3

        # Admin może nadpisać branch; user/viewer tworzą w swoim branchu.
        branch_id = data.branch_id if user.role == "admin" else user.branch_id

        for attempt in range(max_retries):
            try:
                number, auto_num = await generate_contract_number(db, data.contract_type, branch_id)
                contractor_name = data.contractor_name
                if not contractor_name:
                    from contractors.models import Contractor
                    ct = await db.get(Contractor, data.contractor_id)
                    if not ct:
                        from fastapi import HTTPException
                        raise HTTPException(status_code=422, detail="Kontrahent nie istnieje")
                    contractor_name = ct.name

                contract = Contract(
                    **{k: v for k, v in data.model_dump().items() if k not in ("contractor_name", "branch_id")},
                    contractor_name=contractor_name,
                    branch_id=branch_id,
                    number=number,
                    auto_number=auto_num,
                    created_at=datetime.utcnow(),
                )
                # RAO-P2-028: ustaw postal_code_id z lookupu po PNA string
                # (schema nie ma postal_code_id — ustawiamy ręcznie po create)
                contract.postal_code_id = await resolve_postal_code_id(db, data.postal_code)
                db.add(contract)
                await db.commit()
                await db.refresh(contract)
                await copy_fee_templates(db, contract.id, data.contract_type)
                # RAO-P1-012: Auto-create settlement records for all positions
                from settlements.service import SettlementService
                settlement_service = SettlementService()
                position_ids = [p.id for p in data.positions] if hasattr(data, 'positions') and data.positions else []
                await settlement_service.auto_create_settlements_for_contract(db, contract.id, position_ids)
                return contract
            except IntegrityError as e:
                await db.rollback()
                if attempt == max_retries - 1:
                    raise conflict(
                        "Nie udało się wygenerować unikalnego numeru umowy po "
                        f"{max_retries} próbach. Spróbuj ponownie."
                    ) from e
                # Retry — another concurrent request took our number

    async def update_contract(
        self, db: AsyncSession, contract_id: int, data, user: User
    ) -> Contract:
        contract = await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        # RAO-P0-034: exclude_unset=True — only fields the client explicitly sent
        # are applied. Prevents lost-data bug where omitted fields reset to defaults.
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("contractor_name", None)
        # Tylko admin może zmieniać branch_id.
        if user.role != "admin" and "branch_id" in update_data:
            update_data.pop("branch_id", None)
        for field, value in update_data.items():
            setattr(contract, field, value)
        # RAO-P2-028: gdy aktualizowano postal_code, odśwież FK postal_code_id
        if "postal_code" in update_data:
            contract.postal_code_id = await resolve_postal_code_id(db, update_data.get("postal_code"))
        contract.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contract)
        return contract

    async def settle_contract(
        self, db: AsyncSession, contract_id: int, is_settled: bool, user: User
    ) -> Contract:
        """RAO-P2-022: oznacz umowę jako rozliczoną / cofnij rozliczenie."""
        contract = await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        contract.is_settled = is_settled
        contract.settled_at = datetime.utcnow() if is_settled else None
        contract.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contract)
        return contract

    async def delete_contract(self, db: AsyncSession, contract_id: int, user: User):
        contract = await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        await db.execute(
            delete(PositionCondition).where(
                PositionCondition.position_id.in_(
                    select(ContractPosition.id).where(ContractPosition.contract_id == contract_id)
                )
            )
        )
        await db.execute(delete(ContractPosition).where(ContractPosition.contract_id == contract_id))
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.contract_id == contract_id))
        await db.execute(delete(Contract).where(Contract.id == contract_id))
        await db.commit()

    async def list_positions(self, db: AsyncSession, contract_id: int, user: User):
        await self.verify_contract_access(db, contract_id, user)
        from contracts.schemas import PositionResponse, ConditionResponse
        from settings.models import RateType
        from contractors.models import Contractor

        result = await db.execute(
            select(ContractPosition)
            .options(selectinload(ContractPosition.conditions))
            .where(ContractPosition.contract_id == contract_id)
        )
        positions = result.scalars().all()

        # RAO-P0-035: Batch-fetch RateTypes & Contractors (suppliers) to eliminate N+1
        rate_type_ids = {p.rate_type_id for p in positions if p.rate_type_id}
        supplier_ids = {p.supplier_id for p in positions if p.supplier_id}

        rt_map = {}
        if rate_type_ids:
            rt_result = await db.execute(
                select(RateType.id, RateType.name).where(RateType.id.in_(rate_type_ids))
            )
            rt_map = dict(rt_result.all())

        supplier_map = {}
        if supplier_ids:
            sp_result = await db.execute(
                select(Contractor.id, Contractor.name).where(Contractor.id.in_(supplier_ids))
            )
            supplier_map = dict(sp_result.all())

        out = []
        for p in positions:
            rt_name = rt_map.get(p.rate_type_id) if p.rate_type_id else None
            sp_name = supplier_map.get(p.supplier_id) if p.supplier_id else None
            conditions = []
            for cond in p.conditions:
                conditions.append(ConditionResponse(
                    id=cond.id, position_id=cond.position_id,
                    rate1=cond.rate1, rate2=cond.rate2,
                    billing_label=cond.billing_label, period_count=cond.period_count,
                    period_from=cond.period_from, period_to=cond.period_to,  # RAO-P1-005
                    is_flat_rate=cond.is_flat_rate if cond.is_flat_rate is not None else True,  # P1-101
                ))
            out.append(PositionResponse(
                id=p.id, contract_id=p.contract_id, article_id=p.article_id,
                article_name=p.article_name,
                description=p.description, rental_days=p.rental_days,
                quantity=p.quantity, unit_price=p.unit_price,
                rate_type_id=p.rate_type_id, rate_type_name=rt_name,
                billing_frequency=p.billing_frequency, billing_unit=p.billing_unit,
                supplier_id=p.supplier_id, supplier_name=sp_name,
                delivery_date=p.delivery_date,
                conditions_count=len(p.conditions), conditions=conditions,
            ))
        return out

    async def create_position(
        self, db: AsyncSession, contract_id: int, data: PositionCreate, user: User
    ) -> ContractPosition:
        contract = await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        from articles.models import Article
        article = await db.get(Article, data.article_id)
        if article is None:
            raise not_found("Artykuł")
        if article.is_service:
            raise bad_request("Pozycja umowy musi być maszyną (is_service=False).")
        pos = ContractPosition(
            **data.model_dump(),
            contract_id=contract_id,
            article_name=article.name,
        )
        db.add(pos)
        await db.execute(
            update(Contract).where(Contract.id == contract_id)
            .values(position_count=Contract.position_count + 1, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(pos)
        return pos

    async def update_position(
        self, db: AsyncSession, pos_id: int, data, user: User
    ) -> ContractPosition:
        result = await db.execute(
            select(ContractPosition)
            .options(selectinload(ContractPosition.contract))
            .where(ContractPosition.id == pos_id)
        )
        pos = result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        await self.verify_contract_access(db, pos.contract_id, user, allow_mutation=True)
        if data.article_id is not None:
            from articles.models import Article
            article = await db.get(Article, data.article_id)
            if article is None:
                raise not_found("Artykuł")
            if article.is_service:
                raise bad_request("Pozycja umowy musi być maszyną (is_service=False).")
        # RAO-P0-034: exclude_unset=True — only fields explicitly sent are applied
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pos, field, value)
        await db.commit()
        await db.refresh(pos)
        return pos

    async def delete_position(self, db: AsyncSession, contract_id: int, pos_id: int, user: User):
        await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        await db.execute(delete(PositionCondition).where(PositionCondition.position_id == pos_id))
        await db.execute(delete(ContractPosition).where(ContractPosition.id == pos_id))
        await db.execute(
            update(Contract).where(Contract.id == contract_id)
            .values(updated_at=datetime.utcnow())
        )
        await db.commit()

    async def list_conditions(self, db: AsyncSession, pos_id: int, user: User):
        pos_result = await db.execute(
            select(ContractPosition).where(ContractPosition.id == pos_id)
        )
        pos = pos_result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        await self.verify_contract_access(db, pos.contract_id, user)
        result = await db.execute(
            select(PositionCondition).where(PositionCondition.position_id == pos_id)
        )
        return result.scalars().all()

    async def create_condition(
        self, db: AsyncSession, pos_id: int, data: ConditionCreate, user: User
    ) -> PositionCondition:
        pos_result = await db.execute(select(ContractPosition).where(ContractPosition.id == pos_id))
        pos = pos_result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        await self.verify_contract_access(db, pos.contract_id, user, allow_mutation=True)
        payload = data.model_dump()
        print("[DEBUG] ConditionCreate payload:", payload)
        cond = PositionCondition(**payload, position_id=pos_id)
        _sync_condition_derived_fields(cond)
        db.add(cond)
        await db.commit()
        await db.refresh(cond)
        return cond

    async def update_condition(
        self, db: AsyncSession, cond_id: int, data, user: User
    ) -> PositionCondition:
        result = await db.execute(select(PositionCondition).where(PositionCondition.id == cond_id))
        cond = result.scalar_one_or_none()
        if not cond:
            raise not_found("Warunek")
        pos_result = await db.execute(
            select(ContractPosition).where(ContractPosition.id == cond.position_id)
        )
        pos = pos_result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        await self.verify_contract_access(db, pos.contract_id, user, allow_mutation=True)
        # RAO-P0-034: exclude_unset=True — only fields explicitly sent are applied
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cond, field, value)
        _sync_condition_derived_fields(cond)
        await db.commit()
        await db.refresh(cond)
        return cond

    async def delete_condition(self, db: AsyncSession, cond_id: int, user: User):
        pos_result = await db.execute(
            select(ContractPosition)
            .join(PositionCondition, PositionCondition.position_id == ContractPosition.id)
            .where(PositionCondition.id == cond_id)
        )
        pos = pos_result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        await self.verify_contract_access(db, pos.contract_id, user, allow_mutation=True)
        await db.execute(delete(PositionCondition).where(PositionCondition.id == cond_id))
        await db.commit()

    async def list_service_fees(self, db: AsyncSession, contract_id: int, user: User):
        await self.verify_contract_access(db, contract_id, user)
        result = await db.execute(
            select(ContractServiceFee)
            .where(ContractServiceFee.contract_id == contract_id)
            .order_by(ContractServiceFee.sort_order)
        )
        return result.scalars().all()

    async def create_service_fee(
        self, db: AsyncSession, contract_id: int, data: ContractServiceFeeCreate, user: User
    ) -> ContractServiceFee:
        await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        max_order = await db.execute(
            select(func.max(ContractServiceFee.sort_order))
            .where(ContractServiceFee.contract_id == contract_id)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        payload = data.model_dump()
        # RAO-P1-100: KISS fallback — "Tekst na umowie" pusty → użyj nazwy
        if not payload.get("description") or not str(payload.get("description")).strip():
            payload["description"] = payload.get("name")
        fee = ContractServiceFee(**payload, contract_id=contract_id, sort_order=next_order)
        db.add(fee)
        await db.commit()
        await db.refresh(fee)
        return fee

    async def update_service_fee(
        self, db: AsyncSession, fee_id: int, data: ContractServiceFeeUpdate, user: User
    ) -> ContractServiceFee:
        result = await db.execute(
            select(ContractServiceFee).where(ContractServiceFee.id == fee_id)
        )
        fee = result.scalar_one_or_none()
        if not fee:
            raise not_found("Usługa dodatkowa")
        await self.verify_contract_access(db, fee.contract_id, user, allow_mutation=True)
        # RAO-P0-034: exclude_unset=True — only fields explicitly sent are applied
        payload = data.model_dump(exclude_unset=True)
        # RAO-P1-100: KISS fallback — "Tekst na umowie" pusty → użyj nazwy (nowej lub istniejącej)
        if "description" in payload:
            desc = payload.get("description")
            if not desc or not str(desc).strip():
                payload["description"] = payload.get("name") or fee.name
        for field, value in payload.items():
            setattr(fee, field, value)
        await db.commit()
        await db.refresh(fee)
        return fee

    async def delete_service_fee(self, db: AsyncSession, fee_id: int, user: User):
        result = await db.execute(
            select(ContractServiceFee).where(ContractServiceFee.id == fee_id)
        )
        fee = result.scalar_one_or_none()
        if not fee:
            raise not_found("Usługa dodatkowa")
        await self.verify_contract_access(db, fee.contract_id, user, allow_mutation=True)
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.id == fee_id))
        await db.commit()

    async def reorder_service_fees(
        self, db: AsyncSession, contract_id: int, ids: list[int], user: User
    ):
        await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        for i, fee_id in enumerate(ids):
            await db.execute(
                update(ContractServiceFee)
                .where(ContractServiceFee.id == fee_id, ContractServiceFee.contract_id == contract_id)
                .values(sort_order=i)
            )
        await db.commit()

    async def reset_service_fees(self, db: AsyncSession, contract_id: int, user: User):
        contract = await self.verify_contract_access(db, contract_id, user, allow_mutation=True)
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.contract_id == contract_id))
        await db.commit()
        await copy_fee_templates(db, contract_id, contract.contract_type)

    async def recalculate_total(
        self, db: AsyncSession, contract_id: int, user: User
    ) -> Decimal:
        """Recalculate contract total using the cascading tiered algorithm.

        RAO-P0-033: Previously used SUM(rate1 * period_count) which ignored
        quantity, billing_frequency, rate2 ("powyżej"), and the tiered
        calculation. Now uses calculate_position_value from stats/calc.py
        which is the single source of truth for position value.

        RAO-P1-021/P2-033: Nie zapisuje już do contracts.total_value (kolumna usunięte).
        Zwraca tylko total do wyświetlenia w UI.
        """
        from stats.calc import calculate_position_value
        contract = await self.verify_contract_access(db, contract_id, user)
        # Load all positions with their conditions
        result = await db.execute(
            select(ContractPosition)
            .options(selectinload(ContractPosition.conditions))
            .where(ContractPosition.contract_id == contract_id)
        )
        positions = result.scalars().all()
        is_service = contract.contract_type == "U"
        total = Decimal("0.00")
        for pos in positions:
            # Build conditions dicts in the format calculate_position_value expects
            # Closed-ended tiers first, then open-ended, to match the cascading UI.
            sorted_conds = sorted(
                pos.conditions,
                key=lambda c: (
                    c.period_to is None,
                    c.period_from is None,
                    c.period_from or 0,
                    c.period_to or 0,
                )
            )
            cond_dicts = [
                {
                    "rate1": c.rate1,
                    "rate2": c.rate2,
                    "period_from": c.period_from,
                    "period_to": c.period_to,
                    "period_count": c.period_count,
                }
                for c in sorted_conds
            ]
            qty = pos.quantity or 1
            # calculate_position_value already multiplies by quantity
            # (RAO-P0-033 fix in stats/calc.py) — do NOT multiply again here
            pos_value = calculate_position_value(
                rental_days=pos.rental_days,
                billing_frequency=pos.billing_frequency,
                unit_price=pos.unit_price,
                quantity=qty,
                conditions=cond_dicts,
                is_service=is_service,
            )
            total += pos_value
        # RAO-P1-021/P2-033: nie zapisujemy do DB (total_value usunięte)
        return total

    async def migrate_position_condition_periods(self, db: AsyncSession) -> int:
        """RAO-P0-048: One-time migration fixing period_from/period_to for legacy rows.

        Iterates positions with NULL period_from and recalculates cascading ranges
        based on existing period_count/rate1/rate2 values. rate2 rows become open-ended.
        """
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(ContractPosition)
            .options(selectinload(ContractPosition.conditions))
        )
        positions = result.scalars().all()
        fixed = 0
        for pos in positions:
            conds = sorted(pos.conditions, key=lambda c: (c.period_count is None, c.period_count or 0))
            current_end = 0
            for i, cond in enumerate(conds):
                pc = cond.period_count
                has_rate1 = cond.rate1 is not None and cond.rate1 > 0
                has_rate2 = cond.rate2 is not None and cond.rate2 > 0

                next_pc = None
                for j in range(i + 1, len(conds)):
                    npc = conds[j].period_count
                    if npc is not None:
                        next_pc = npc
                        break

                if has_rate1 and pc is not None:
                    if cond.period_from is None:
                        cond.period_from = current_end + 1
                    if cond.period_to is None:
                        cond.period_to = pc
                    current_end = cond.period_to

                if has_rate2:
                    r2_from = (pc + 1) if has_rate1 and pc is not None else (current_end + 1)
                    r2_to = (next_pc - 1) if next_pc is not None else None
                    if r2_to is None or r2_from <= r2_to:
                        if cond.period_from is None:
                            cond.period_from = r2_from
                        if cond.period_to is None:
                            cond.period_to = r2_to
                        if r2_to is not None:
                            current_end = r2_to
                fixed += 1
        await db.commit()
        return fixed


contract_service = ContractService()
