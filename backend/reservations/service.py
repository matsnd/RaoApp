import logging
from datetime import date as date_cls
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException

from reservations.models import MachineReservation
from reservations.schemas import ReservationCreate, ReservationUpdate, CalendarEvent

logger = logging.getLogger(__name__)


class ReservationService:

    async def list_for_machine(
        self, db: AsyncSession, machine_id: int
    ) -> list[MachineReservation]:
        result = await db.execute(
            select(MachineReservation)
            .where(MachineReservation.machine_id == machine_id)
            .order_by(MachineReservation.reserved_from)
        )
        return result.scalars().all()

    async def list_all(
        self, db: AsyncSession
    ) -> list[MachineReservation]:
        """Return all reservations ordered by date."""
        result = await db.execute(
            select(MachineReservation).order_by(MachineReservation.reserved_from)
        )
        return result.scalars().all()

    async def list_all_with_machines(
        self, db: AsyncSession
    ) -> list[dict]:
        """Return all reservations joined with machine names and contractor names."""
        from machines.models import Machine
        from contractors.models import Contractor
        result = await db.execute(
            select(
                MachineReservation.id,
                MachineReservation.machine_id,
                Machine.name.label("machine_name"),
                Machine.internal_number.label("internal_number"),
                MachineReservation.reserved_from,
                MachineReservation.reserved_to,
                MachineReservation.note,
                MachineReservation.created_by,
                MachineReservation.created_at,
                MachineReservation.contractor_id,
                Contractor.name.label("contractor_name"),
                MachineReservation.status,
            )
            .outerjoin(Machine, MachineReservation.machine_id == Machine.id)
            .outerjoin(Contractor, MachineReservation.contractor_id == Contractor.id)
            .order_by(MachineReservation.reserved_from)
        )
        rows = result.all()
        return [
            {
                "id": r[0],
                "machine_id": r[1],
                "machine_name": r[2],
                "internal_number": r[3],
                "reserved_from": r[4],
                "reserved_to": r[5],
                "note": r[6],
                "created_by": r[7],
                "created_at": r[8],
                "contractor_id": r[9],
                "contractor_name": r[10],
                "status": r[11],
            }
            for r in rows
        ]

    async def check_conflict(
        self,
        db: AsyncSession,
        machine_id: int,
        from_date: date_cls,
        to_date: date_cls,
        exclude_id: int | None = None,
        exclude_contractor_id: int | None = None,
    ) -> bool:
        """Returns True if there is a conflicting reservation (date ranges overlap).

        If ``exclude_contractor_id`` is provided, reservations with the same
        contractor_id are ignored (a contractor's own reservations don't block).
        """
        q = select(MachineReservation).where(
            and_(
                MachineReservation.machine_id == machine_id,
                MachineReservation.reserved_from <= to_date,
                MachineReservation.reserved_to >= from_date,
            )
        )
        if exclude_id:
            q = q.where(MachineReservation.id != exclude_id)
        if exclude_contractor_id is not None:
            q = q.where(
                or_(
                    MachineReservation.contractor_id.is_(None),
                    MachineReservation.contractor_id != exclude_contractor_id,
                )
            )
        result = await db.execute(q)
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, data: ReservationCreate, user_id: int
    ) -> MachineReservation:
        # Pre-validate FK targets exist (avoids 500 IntegrityError → 404)
        from machines.models import Machine
        from contractors.models import Contractor
        machine = await db.get(Machine, data.machine_id)
        if not machine:
            raise HTTPException(404, "Artykuł nie został znaleziony")
        if machine.is_external:
            raise HTTPException(400, "Nie można rezerwować maszyn zewnętrznych")
        if data.contractor_id is not None:
            contractor = await db.get(Contractor, data.contractor_id)
            if not contractor:
                raise HTTPException(404, "Kontrahent nie został znaleziony")
        if await self.check_conflict(
            db, data.machine_id, data.reserved_from, data.reserved_to
        ):
            raise HTTPException(409, "Artykuł jest już zarezerwowany w tym terminie")
        obj = MachineReservation(**data.model_dump(), created_by=user_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        logger.info(
            "Reservation created: id=%s machine_id=%s %s – %s by user_id=%s",
            obj.id, obj.machine_id, obj.reserved_from, obj.reserved_to, user_id,
        )
        return obj

    async def update(
        self,
        db: AsyncSession,
        reservation_id: int,
        data: ReservationUpdate,
        user_id: int,
    ) -> MachineReservation:
        """Update an existing reservation (partial update).

        Only fields explicitly provided in the payload are updated.
        Validates date conflict against other reservations (excluding self).
        """
        obj = await db.get(MachineReservation, reservation_id)
        if not obj:
            raise HTTPException(404, "Rezerwacja nie została znaleziona")

        updates = data.model_dump(exclude_unset=True)

        # Pre-validate FK if contractor_id is being updated
        if "contractor_id" in updates and updates["contractor_id"] is not None:
            from contractors.models import Contractor
            contractor = await db.get(Contractor, updates["contractor_id"])
            if not contractor:
                raise HTTPException(404, "Kontrahent nie został znaleziony")

        # P2-003: walidacja is_external gdy machine_id zmieniana
        if "machine_id" in updates:
            from machines.models import Machine
            machine = await db.get(Machine, updates["machine_id"])
            if not machine:
                raise HTTPException(404, "Artykuł nie został znaleziony")
            if machine.is_external:
                raise HTTPException(400, "Nie można rezerwować maszyn zewnętrznych")

        # Determine effective date range for conflict check
        new_from = updates.get("reserved_from", obj.reserved_from)
        new_to = updates.get("reserved_to", obj.reserved_to)
        if new_from > new_to:
            raise HTTPException(400, "reserved_from must be <= reserved_to")

        if await self.check_conflict(
            db, obj.machine_id, new_from, new_to, exclude_id=reservation_id
        ):
            raise HTTPException(409, "Artykuł jest już zarezerwowany w tym terminie")

        for field, value in updates.items():
            setattr(obj, field, value)
        await db.commit()
        await db.refresh(obj)
        logger.info(
            "Reservation updated: id=%s by user_id=%s fields=%s",
            reservation_id, user_id, list(updates.keys()),
        )
        return obj

    async def list_calendar(
        self,
        db: AsyncSession,
        date_from: date_cls,
        date_to: date_cls,
        machine_id: int | None = None,
    ) -> list[CalendarEvent]:
        """Return calendar events (reservations + contracts) overlapping [date_from, date_to].

        Source 1: machine_reservations where reserved_from <= date_to AND reserved_to >= date_from
        Source 2: contracts (via contract_positions) where date_from <= date_to AND date_to >= date_from
        Optional machine_id filter applies to both sources.
        Results sorted by date_from.
        """
        from machines.models import Machine
        from contractors.models import Contractor
        from contracts.models import Contract, ContractPosition

        events: list[CalendarEvent] = []

        # Source 1: reservations
        res_stmt = (
            select(
                MachineReservation.id,
                MachineReservation.machine_id,
                Machine.name,
                Machine.internal_number,
                MachineReservation.contractor_id,
                Contractor.name,
                MachineReservation.reserved_from,
                MachineReservation.reserved_to,
                MachineReservation.note,
                MachineReservation.status,
            )
            .outerjoin(Machine, MachineReservation.machine_id == Machine.id)
            .outerjoin(Contractor, MachineReservation.contractor_id == Contractor.id)
            .where(MachineReservation.reserved_from <= date_to)
            .where(MachineReservation.reserved_to >= date_from)
        )
        if machine_id is not None:
            res_stmt = res_stmt.where(MachineReservation.machine_id == machine_id)
        res_result = await db.execute(res_stmt.order_by(MachineReservation.reserved_from))
        for r in res_result.all():
            events.append(CalendarEvent(
                source="reservation",
                source_id=r[0],
                machine_id=r[1],
                machine_name=r[2],
                internal_number=r[3],
                contractor_id=r[4],
                contractor_name=r[5],
                date_from=r[6],
                date_to=r[7],
                note=r[8],
                status=r[9],
            ))

        # Source 2: contracts (via contract_positions)
        contract_stmt = (
            select(
                Contract.id,
                ContractPosition.machine_id,
                Machine.name,
                Machine.internal_number,
                Contract.contractor_id,
                Contractor.name,
                Contract.date_from,
                Contract.date_to,
                Contract.number,
            )
            .join(ContractPosition, ContractPosition.contract_id == Contract.id)
            .outerjoin(Machine, ContractPosition.machine_id == Machine.id)
            .join(Contractor, Contract.contractor_id == Contractor.id)
            .where(Contract.date_from <= date_to)
            .where(Contract.date_to >= date_from)
        )
        if machine_id is not None:
            contract_stmt = contract_stmt.where(ContractPosition.machine_id == machine_id)
        contract_result = await db.execute(contract_stmt.order_by(Contract.date_from))
        for r in contract_result.all():
            events.append(CalendarEvent(
                source="contract",
                source_id=r[0],
                machine_id=r[1],
                machine_name=r[2],
                internal_number=r[3],
                contractor_id=r[4],
                contractor_name=r[5],
                date_from=r[6],
                date_to=r[7],
                note=r[8],  # contract number
                status=None,
            ))

        events.sort(key=lambda e: e.date_from)
        return events

    async def delete(self, db: AsyncSession, reservation_id: int) -> None:
        obj = await db.get(MachineReservation, reservation_id)
        if not obj:
            raise HTTPException(404, "Rezerwacja nie została znaleziona")
        await db.delete(obj)
        await db.commit()
        logger.info("Reservation deleted: id=%s", reservation_id)

    async def get_active_for_machine(
        self, db: AsyncSession, machine_id: int, from_date: date_cls | None = None
    ) -> list[MachineReservation]:
        """Return future/current reservations for a machine (reserved_to >= today)."""
        today = from_date or date_cls.today()
        result = await db.execute(
            select(MachineReservation)
            .where(
                and_(
                    MachineReservation.machine_id == machine_id,
                    MachineReservation.reserved_to >= today,
                )
            )
            .order_by(MachineReservation.reserved_from)
        )
        return result.scalars().all()


reservation_service = ReservationService()
