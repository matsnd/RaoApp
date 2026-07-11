from datetime import datetime, date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from machines.models import Machine
from machines.schemas import MachineCreate, MachineUpdate
from shared.exceptions import not_found


class MachineService:
    async def list_machines(
        self, db: AsyncSession,
        search: str | None = None,
        category_id: int | None = None,
        owner_id: int | None = None,
        archival_status: str = "active",
        page: int = 1,
        per_page: int = 50,
    ):
        from categories.models import Category
        from contractors.models import Contractor
        from contracts.models import Contract, ContractPosition
        from machines.schemas import MachineListItem

        stmt = select(Machine)
        if archival_status == "active":
            stmt = stmt.where(Machine.is_archival == False)  # noqa: E712
        elif archival_status == "archival":
            stmt = stmt.where(Machine.is_archival == True)   # noqa: E712
        if search:
            stmt = stmt.where(Machine.name.ilike(f"%{search}%"))
        if category_id:
            stmt = stmt.where(Machine.category_id == category_id)
        if owner_id:
            stmt = stmt.where(Machine.owner_id == owner_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Machine.name).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        machines = result.scalars().all()

        machine_ids = [m.id for m in machines]
        category_ids = {m.category_id for m in machines if m.category_id}
        owner_ids = {m.owner_id for m in machines if m.owner_id}

        cat_map = {}
        if category_ids:
            cat_result = await db.execute(
                select(Category.id, Category.name).where(Category.id.in_(category_ids))
            )
            cat_map = dict(cat_result.all())

        owner_map = {}
        if owner_ids:
            own_result = await db.execute(
                select(Contractor.id, Contractor.name).where(Contractor.id.in_(owner_ids))
            )
            owner_map = dict(own_result.all())

        active_map = {}
        if machine_ids:
            today = date.today()
            active_result = await db.execute(
                select(ContractPosition.machine_id, Contract.number)
                .join(Contract, ContractPosition.contract_id == Contract.id)
                .where(ContractPosition.machine_id.in_(machine_ids))
                .where(Contract.date_to >= today)
                .distinct()
            )
            for mid, num in active_result.all():
                if mid not in active_map:
                    active_map[mid] = num

        items = []
        for m in machines:
            cat_name = cat_map.get(m.category_id) if m.category_id else None
            own_name = owner_map.get(m.owner_id) if m.owner_id else None
            active_num = active_map.get(m.id)
            items.append(MachineListItem(
                id=m.id, name=m.name,
                internal_number=m.internal_number, registration_no=m.registration_no,
                serial_no=m.serial_no, brand=m.brand, model=m.model,
                replacement_value=m.replacement_value,
                category_name=cat_name,
                category_main=m.category_main,
                is_archival=m.is_archival,
                is_external=m.is_external,
                fakturownia_product_id=m.fakturownia_product_id,
                owner_name=own_name, notes=m.notes,
                active_contract_number=active_num,
                created_at=m.created_at, updated_at=m.updated_at,
                conditions_count=0,
            ))
        return items, total

    async def get_machine(self, db: AsyncSession, machine_id: int) -> Machine:
        result = await db.execute(select(Machine).where(Machine.id == machine_id))
        machine = result.scalar_one_or_none()
        if not machine:
            raise not_found("Maszyna")
        return machine

    async def create_machine(self, db: AsyncSession, data: MachineCreate) -> Machine:
        machine = Machine(**data.model_dump(), created_at=datetime.utcnow())
        db.add(machine)
        await db.commit()
        await db.refresh(machine)
        return machine

    async def update_machine(self, db: AsyncSession, machine_id: int, data: MachineUpdate) -> Machine:
        machine = await self.get_machine(db, machine_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(machine, field, value)
        machine.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(machine)
        return machine

    async def delete_machine(self, db: AsyncSession, machine_id: int):
        machine = await self.get_machine(db, machine_id)
        await db.delete(machine)
        await db.commit()

    async def duplicate_machine(self, db: AsyncSession, machine_id: int) -> Machine:
        original = await self.get_machine(db, machine_id)
        copy = Machine(
            name=f"{original.name} (kopia)",
            internal_number=original.internal_number,
            registration_no=None,
            serial_no=None,
            brand=original.brand,
            model=original.model,
            replacement_value=original.replacement_value,
            category_id=original.category_id,
            owner_id=original.owner_id,
            branch_id=original.branch_id,
            description=original.description,
            notes=original.notes,
            rental_days=original.rental_days,
            is_external=original.is_external,
            is_archival=original.is_archival,
            power_type=original.power_type,
            technical_attributes=original.technical_attributes,
            reach_m=original.reach_m,
            capacity_t=original.capacity_t,
            accessories=original.accessories,
            created_at=datetime.utcnow(),
        )
        db.add(copy)
        await db.commit()
        await db.refresh(copy)
        return copy

    async def check_availability(
        self, db: AsyncSession, machine_id: int, date_from: date, date_to: date,
        exclude_contract_id: int | None = None,
    ):
        from contracts.models import Contract, ContractPosition
        from contractors.models import Contractor
        from reservations.models import MachineReservation
        from machines.schemas import (
            AvailabilityConflict,
            AvailabilityResponse,
            AvailabilityReservationConflict,
        )

        machine = await db.get(Machine, machine_id)
        if machine and machine.is_external:
            return AvailabilityResponse(
                is_available=True,
                conflicting_contracts=[],
                conflicting_reservations=[],
            )

        stmt = (
            select(Contract.id, Contract.number, Contract.date_from, Contract.date_to, Contractor.name)
            .join(ContractPosition, ContractPosition.contract_id == Contract.id)
            .join(Contractor, Contract.contractor_id == Contractor.id)
            .where(ContractPosition.machine_id == machine_id)
            .where(Contract.date_from <= date_to)
            .where(Contract.date_to >= date_from)
        )
        if exclude_contract_id is not None:
            stmt = stmt.where(Contract.id != exclude_contract_id)
        result = await db.execute(stmt)
        rows = result.all()
        conflicts = [
            AvailabilityConflict(
                contract_id=r[0], contract_number=r[1],
                date_from=r[2], date_to=r[3], contractor_name=r[4],
            )
            for r in rows
        ]

        res_stmt = (
            select(MachineReservation, Contractor.name)
            .outerjoin(Contractor, MachineReservation.contractor_id == Contractor.id)
            .where(MachineReservation.machine_id == machine_id)
            .where(MachineReservation.reserved_from <= date_to)
            .where(MachineReservation.reserved_to >= date_from)
            .order_by(MachineReservation.reserved_from)
        )
        res_result = await db.execute(res_stmt)
        res_rows = res_result.all()
        res_conflicts = [
            AvailabilityReservationConflict(
                reservation_id=r.id,
                reserved_from=r.reserved_from,
                reserved_to=r.reserved_to,
                note=r.note,
                available_from=r.reserved_to + timedelta(days=1),
                contractor_id=r.contractor_id,
                contractor_name=contractor_name,
            )
            for r, contractor_name in res_rows
        ]

        is_available = len(conflicts) == 0 and len(res_conflicts) == 0
        return AvailabilityResponse(
            is_available=is_available,
            conflicting_contracts=conflicts,
            conflicting_reservations=res_conflicts,
        )


machine_service = MachineService()
