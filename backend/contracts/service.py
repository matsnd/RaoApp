from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from contracts.schemas import ContractCreate, PositionCreate, ConditionCreate, ContractServiceFeeCreate
from shared.exceptions import not_found, conflict


async def generate_contract_number(db: AsyncSession, contract_type: str, branch_id: int | None = None) -> tuple[str, int]:
    """Generate a unique contract number.

    RAO-P0-030: Uses SELECT ... FOR UPDATE on Company row to serialize
    concurrent contract creation. Falls back to retry on IntegrityError
    (defensive — UNIQUE index on contracts.number is the last line of defense).
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

    suffix = ""
    if branch_id:
        branch_result = await db.execute(select(Branch.name).where(Branch.id == branch_id))
        branch_name = branch_result.scalar_one_or_none()
        if branch_name and branch_name.upper() == "GDAŃSK":
            suffix = "G"

    return f"{contract_type}{new_number:03d}/{year}{suffix}", new_number


async def copy_fee_templates(db: AsyncSession, contract_id: int, contract_type: str):
    from settings.models import ServiceFeeTemplate
    templates = await db.execute(
        select(ServiceFeeTemplate)
        .where(ServiceFeeTemplate.contract_type == contract_type)
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


def format_position_conditions_cascading(conditions: list[PositionCondition]) -> str:
    """Buduje opis kaskadowych warunków rozliczenia jak w starej aplikacji WinForms.

    Przykład wyjścia (3 warunki):
      1 - 3 dni - 540,00 / doba
      4 - 16 dni - 410,00 / doba
      powyżej 16 dni - 350,00 / doba

    RAO-P1-020: naprawiono duplikaty warunków + logikę "powyżej" (rate2 z rate1=0).
    """
    if not conditions:
        return ""

    # RAO-P1-020: Deduplikuj warunki po (period_count, rate1, rate2) — migracja mogła stworzyć duplikaty
    seen = set()
    unique_conds = []
    for c in conditions:
        key = (c.period_count, c.rate1, c.rate2)
        if key not in seen:
            seen.add(key)
            unique_conds.append(c)

    # Sortuj warunki rosnąco po period_count (NULL na końcu)
    sorted_conds = sorted(
        unique_conds,
        key=lambda c: (c.period_count is None, c.period_count or 0)
    )
    lines = []
    prev_period = 0
    for i, c in enumerate(sorted_conds):
        label = c.billing_label or 'doba'
        if c.period_count is not None and c.rate1 is not None and c.rate1 > 0:
            # Zakres dni (tier z rate1 > 0)
            start = prev_period + 1
            end = c.period_count
            if start == end:
                range_text = f"{start} {label}"
            else:
                # Uproszczona polska fleksja: użyj "dni" dla zakresu
                range_text = f"{start} - {end} dni"
            # Polski format kwoty (przecinek dziesiętny)
            rate_text = f"{c.rate1:.2f}".replace('.', ',')
            lines.append(f"{range_text} - {rate_text} / {label}")
            prev_period = c.period_count
        elif c.rate2 is not None and c.rate2 > 0 and prev_period > 0:
            # RAO-P1-020: Linia "powyżej" — rate2 > 0, niezależnie od period_count
            # (dane z migracji mają period_count=ostatni zamiast None)
            rate_text = f"{c.rate2:.2f}".replace('.', ',')
            lines.append(f"powyżej {prev_period} dni - {rate_text} / {label}")
    return '\n'.join(lines)


async def apply_preset_to_contract(db: AsyncSession, contract_id: int, preset_id: int, replace: bool = True):
    from settings.models import FeePresetGroup, ServiceFeeTemplate
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
            article_id=t.article_id,
            default_price=t.default_price,
        ))
    await db.commit()


class ContractService:
    async def list_contracts(
        self, db: AsyncSession,
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
                total_value=c.total_value,
                prepayment_amount=c.prepayment_amount,
                prepayment_document=c.prepayment_document,
                invoice_amount=c.invoice_amount,
                invoice_document=c.invoice_document,
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
                total_value=c.total_value,
                prepayment_amount=c.prepayment_amount,
                prepayment_document=c.prepayment_document,
                invoice_amount=c.invoice_amount,
                invoice_document=c.invoice_document,
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

    async def create_contract(self, db: AsyncSession, data: ContractCreate) -> Contract:
        # RAO-P0-030: Retry on IntegrityError (UNIQUE on contracts.number)
        from sqlalchemy.exc import IntegrityError
        max_retries = 3
        for attempt in range(max_retries):
            try:
                number, auto_num = await generate_contract_number(db, data.contract_type, data.branch_id)
                contractor_name = data.contractor_name
                if not contractor_name:
                    from contractors.models import Contractor
                    ct = await db.get(Contractor, data.contractor_id)
                    if not ct:
                        from fastapi import HTTPException
                        raise HTTPException(status_code=422, detail="Kontrahent nie istnieje")
                    contractor_name = ct.name

                contract = Contract(
                    **{k: v for k, v in data.model_dump().items() if k != "contractor_name"},
                    contractor_name=contractor_name,
                    number=number,
                    auto_number=auto_num,
                    created_at=datetime.utcnow(),
                )
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

    async def update_contract(self, db: AsyncSession, contract_id: int, data) -> Contract:
        contract = await self.get_contract(db, contract_id)
        # RAO-P0-034: exclude_unset=True — only fields the client explicitly sent
        # are applied. Prevents lost-data bug where omitted fields reset to defaults.
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("contractor_name", None)
        for field, value in update_data.items():
            setattr(contract, field, value)
        contract.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contract)
        return contract

    async def settle_contract(self, db: AsyncSession, contract_id: int, is_settled: bool) -> Contract:
        """RAO-P2-022: oznacz umowę jako rozliczoną / cofnij rozliczenie."""
        contract = await self.get_contract(db, contract_id)
        contract.is_settled = is_settled
        contract.settled_at = datetime.utcnow() if is_settled else None
        contract.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(contract)
        return contract

    async def delete_contract(self, db: AsyncSession, contract_id: int):
        # RAO-P1-037: Guard — nie pozwól usunąć rozliczonej umowy
        contract = await self.get_contract(db, contract_id)
        if contract.is_settled:
            raise conflict("Nie można usunąć rozliczonej umowy. Najpierw cofnij rozliczenie.")
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

    async def list_positions(self, db: AsyncSession, contract_id: int):
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
        rate_type_ids |= {cond.rate_type_id for p in positions for cond in p.conditions if cond.rate_type_id}
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
                crt_name = rt_map.get(cond.rate_type_id) if cond.rate_type_id else None
                conditions.append(ConditionResponse(
                    id=cond.id, position_id=cond.position_id,
                    rate_type_id=cond.rate_type_id, rate_type_name=crt_name,
                    description=cond.description, rate1=cond.rate1, rate2=cond.rate2,
                    billing_label=cond.billing_label, period_count=cond.period_count,
                    minimum=cond.minimum,
                ))
            out.append(PositionResponse(
                id=p.id, contract_id=p.contract_id, article_id=p.article_id,
                article_name=p.article_name, rental_type=p.rental_type,
                description=p.description, rental_days=p.rental_days,
                quantity=p.quantity, unit_price=p.unit_price, costs=p.costs,
                rate_type_id=p.rate_type_id, rate_type_name=rt_name,
                billing_frequency=p.billing_frequency, billing_unit=p.billing_unit,
                supplier_id=p.supplier_id, supplier_name=sp_name,
                delivery_date=p.delivery_date,
                conditions_count=len(p.conditions), conditions=conditions,
            ))
        return out

    async def create_position(self, db: AsyncSession, contract_id: int, data: PositionCreate) -> ContractPosition:
        from articles.models import Article
        article = await db.get(Article, data.article_id)
        pos = ContractPosition(
            **data.model_dump(),
            contract_id=contract_id,
            article_name=article.name if article else None,
        )
        db.add(pos)
        await db.execute(
            update(Contract).where(Contract.id == contract_id)
            .values(position_count=Contract.position_count + 1, updated_at=datetime.utcnow())
        )
        await db.commit()
        await db.refresh(pos)
        return pos

    async def update_position(self, db: AsyncSession, pos_id: int, data) -> ContractPosition:
        result = await db.execute(select(ContractPosition).where(ContractPosition.id == pos_id))
        pos = result.scalar_one_or_none()
        if not pos:
            raise not_found("Pozycja")
        # RAO-P0-034: exclude_unset=True — only fields explicitly sent are applied
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(pos, field, value)
        await db.commit()
        await db.refresh(pos)
        return pos

    async def delete_position(self, db: AsyncSession, contract_id: int, pos_id: int):
        await db.execute(delete(PositionCondition).where(PositionCondition.position_id == pos_id))
        await db.execute(delete(ContractPosition).where(ContractPosition.id == pos_id))
        await db.execute(
            update(Contract).where(Contract.id == contract_id)
            .values(updated_at=datetime.utcnow())
        )
        await db.commit()

    async def list_conditions(self, db: AsyncSession, pos_id: int):
        result = await db.execute(
            select(PositionCondition).where(PositionCondition.position_id == pos_id)
        )
        return result.scalars().all()

    async def create_condition(self, db: AsyncSession, pos_id: int, data: ConditionCreate) -> PositionCondition:
        cond = PositionCondition(**data.model_dump(), position_id=pos_id)
        db.add(cond)
        await db.commit()
        await db.refresh(cond)
        return cond

    async def update_condition(self, db: AsyncSession, cond_id: int, data) -> PositionCondition:
        result = await db.execute(select(PositionCondition).where(PositionCondition.id == cond_id))
        cond = result.scalar_one_or_none()
        if not cond:
            raise not_found("Warunek")
        # RAO-P0-034: exclude_unset=True — only fields explicitly sent are applied
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cond, field, value)
        await db.commit()
        await db.refresh(cond)
        return cond

    async def delete_condition(self, db: AsyncSession, cond_id: int):
        await db.execute(delete(PositionCondition).where(PositionCondition.id == cond_id))
        await db.commit()

    async def list_service_fees(self, db: AsyncSession, contract_id: int):
        result = await db.execute(
            select(ContractServiceFee)
            .where(ContractServiceFee.contract_id == contract_id)
            .order_by(ContractServiceFee.sort_order)
        )
        return result.scalars().all()

    async def create_service_fee(self, db: AsyncSession, contract_id: int, data: ContractServiceFeeCreate) -> ContractServiceFee:
        max_order = await db.execute(
            select(func.max(ContractServiceFee.sort_order))
            .where(ContractServiceFee.contract_id == contract_id)
        )
        next_order = (max_order.scalar_one_or_none() or 0) + 1
        fee = ContractServiceFee(**data.model_dump(), contract_id=contract_id, sort_order=next_order)
        db.add(fee)
        await db.commit()
        await db.refresh(fee)
        return fee

    async def update_service_fee(self, db: AsyncSession, fee_id: int, data: ContractServiceFeeCreate) -> ContractServiceFee:
        result = await db.execute(select(ContractServiceFee).where(ContractServiceFee.id == fee_id))
        fee = result.scalar_one_or_none()
        if not fee:
            raise not_found("Usługa dodatkowa")
        for field, value in data.model_dump().items():
            setattr(fee, field, value)
        await db.commit()
        await db.refresh(fee)
        return fee

    async def delete_service_fee(self, db: AsyncSession, fee_id: int):
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.id == fee_id))
        await db.commit()

    async def reorder_service_fees(self, db: AsyncSession, contract_id: int, ids: list[int]):
        for i, fee_id in enumerate(ids):
            await db.execute(
                update(ContractServiceFee)
                .where(ContractServiceFee.id == fee_id, ContractServiceFee.contract_id == contract_id)
                .values(sort_order=i)
            )
        await db.commit()

    async def reset_service_fees(self, db: AsyncSession, contract_id: int):
        contract = await self.get_contract(db, contract_id)
        await db.execute(delete(ContractServiceFee).where(ContractServiceFee.contract_id == contract_id))
        await db.commit()
        await copy_fee_templates(db, contract_id, contract.contract_type)

    async def recalculate_total(self, db: AsyncSession, contract_id: int):
        """Recalculate total_value using the cascading tiered algorithm.

        RAO-P0-033: Previously used SUM(rate1 * period_count) which ignored
        quantity, billing_frequency, rate2 ("powyżej"), and the tiered
        calculation. Now uses calculate_position_value from stats/calc.py
        which is the single source of truth for position value.
        """
        from stats.calc import calculate_position_value
        contract = await self.get_contract(db, contract_id)
        # Load all positions with conditions
        result = await db.execute(
            select(ContractPosition)
            .options(selectinload(ContractPosition.conditions))
            .where(ContractPosition.contract_id == contract_id)
        )
        positions = result.scalars().all()
        total = Decimal("0.00")
        for pos in positions:
            # Build conditions dicts in the format calculate_position_value expects
            sorted_conds = sorted(
                [c for c in pos.conditions if c.rate1 and c.rate1 > 0],
                key=lambda c: (c.period_count is None, c.period_count or 0)
            )
            cond_dicts = [
                {
                    "rate1": c.rate1,
                    "rate2": c.rate2,
                    "period_count": c.period_count,
                    "minimum": c.minimum,
                    "rate_type_id": c.rate_type_id,
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
            )
            total += pos_value
        contract.total_value = total
        await db.commit()
        await db.refresh(contract)
        return total


contract_service = ContractService()
