"""P1-205 Faza 1: Service dla read-only kalendarza dostaw (źródło: umowy).

Mirror modułu reservations/service.py:list_calendar, ale read-only z umów.
Zwraca dostawy = umowy (S + U) z date_from w zadanym zakresie.
Dla machine_name: LEFT JOIN pierwszej pozycji umowy z machine_id.
"""
import logging
from datetime import date as date_cls
from typing import Optional

from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from deliveries.schemas import DeliveryCalendarEvent

logger = logging.getLogger(__name__)


class DeliveryService:
    """Read-only service dla kalendarza dostaw (dane z umów)."""

    async def list_calendar(
        self,
        db: AsyncSession,
        date_from: date_cls,
        date_to: date_cls,
        machine_id: Optional[int] = None,
        contractor_id: Optional[int] = None,
    ) -> list[DeliveryCalendarEvent]:
        """Zwraca dostawy (z umów) z date_from w zakresie [date_from, date_to].

        - JOIN contractors (nazwa), salespeople (handlowiec)
        - LEFT JOIN contract_positions + machines (nazwa maszyny — pierwsza pozycja z machine_id)
        - Filtr machine_id przez contract_positions.machine_id (EXISTS, jeśli podany)
        - Filtr contractor_id przez contracts.contractor_id (jeśli podany)
        - Umowy bez date_from → pomijane (WHERE date_from IS NOT NULL)
        - Sort po delivery_date (date_from)
        """
        from contracts.models import Contract, ContractPosition
        from machines.models import Machine
        from contractors.models import Contractor
        from settings.models import Salesperson

        # Subquery: pierwsza pozycja (min id) z machine_id dla każdego kontraktu
        first_pos = (
            select(
                ContractPosition.contract_id.label("fp_contract_id"),
                func.min(ContractPosition.id).label("fp_pos_id"),
            )
            .where(ContractPosition.machine_id.isnot(None))
            .group_by(ContractPosition.contract_id)
            .subquery()
        )

        # Alias pozycji do joinu po wybranym pierwszym id
        FirstPosition = ContractPosition  # alias dla czytelności
        fp_alias = ContractPosition  # join target

        stmt = (
            select(
                Contract.id,
                Contract.number,
                Contract.contract_type,
                fp_alias.machine_id,
                Machine.name,
                Machine.internal_number,
                Contract.contractor_id,
                Contractor.name,
                Contract.date_from,
                Contract.delivery_address,
                Contract.city,
                Contract.salesperson_id,
                Salesperson.name,
            )
            .outerjoin(first_pos, first_pos.c.fp_contract_id == Contract.id)
            .outerjoin(
                fp_alias,
                (fp_alias.id == first_pos.c.fp_pos_id),
            )
            .outerjoin(Machine, fp_alias.machine_id == Machine.id)
            .join(Contractor, Contract.contractor_id == Contractor.id)
            .outerjoin(Salesperson, Contract.salesperson_id == Salesperson.id)
            .where(Contract.date_from.isnot(None))
            .where(Contract.date_from >= date_from)
            .where(Contract.date_from <= date_to)
        )

        if contractor_id is not None:
            stmt = stmt.where(Contract.contractor_id == contractor_id)

        if machine_id is not None:
            # Filtruj umowy mające co najmniej jedną pozycję z danym machine_id
            pos_exists = (
                select(ContractPosition.id)
                .where(ContractPosition.contract_id == Contract.id)
                .where(ContractPosition.machine_id == machine_id)
            )
            stmt = stmt.where(exists(pos_exists))

        stmt = stmt.order_by(Contract.date_from)
        result = await db.execute(stmt)

        events: list[DeliveryCalendarEvent] = []
        for r in result.all():
            events.append(
                DeliveryCalendarEvent(
                    source="contract",
                    source_id=r[0],
                    contract_number=r[1],
                    contract_type=r[2],
                    machine_id=r[3],
                    machine_name=r[4],
                    internal_number=r[5],
                    contractor_id=r[6],
                    contractor_name=r[7],
                    delivery_date=r[8],
                    delivery_address=r[9],
                    city=r[10],
                    salesperson_id=r[11],
                    salesperson_name=r[12],
                )
            )

        logger.info(
            "Deliveries calendar: range=%s..%s machine_id=%s contractor_id=%s -> %d events",
            date_from, date_to, machine_id, contractor_id, len(events),
        )
        return events


delivery_service = DeliveryService()
