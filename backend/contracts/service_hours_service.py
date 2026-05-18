"""Service hours service - CRUD operations for operator work hours"""

from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.service_hours import ServiceHour
from contracts.schemas import ServiceHourCreate, ServiceHourUpdate
from shared.exceptions import not_found


class ServiceHourService:
    async def list_service_hours(
        self, db: AsyncSession, position_id: int
    ) -> list[ServiceHour]:
        """List all service hours for a position"""
        result = await db.execute(
            select(ServiceHour)
            .where(ServiceHour.position_id == position_id)
            .order_by(ServiceHour.service_date)
        )
        return list(result.scalars().all())

    async def get_service_hour(
        self, db: AsyncSession, hour_id: int
    ) -> ServiceHour:
        """Get a single service hour by ID"""
        result = await db.execute(
            select(ServiceHour).where(ServiceHour.id == hour_id)
        )
        hour = result.scalar_one_or_none()
        if not hour:
            raise not_found("Godzina usługi")
        return hour

    async def create_service_hour(
        self, db: AsyncSession, position_id: int, data: ServiceHourCreate
    ) -> ServiceHour:
        """Create a new service hour entry"""
        hour = ServiceHour(
            position_id=position_id,
            service_date=data.service_date,
            time_from=data.time_from,
            time_to=data.time_to,
            notes=data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(hour)
        await db.commit()
        await db.refresh(hour)
        return hour

    async def update_service_hour(
        self, db: AsyncSession, hour_id: int, data: ServiceHourUpdate
    ) -> ServiceHour:
        """Update an existing service hour"""
        hour = await self.get_service_hour(db, hour_id)

        if data.service_date is not None:
            hour.service_date = data.service_date
        if data.time_from is not None:
            hour.time_from = data.time_from
        if data.time_to is not None:
            hour.time_to = data.time_to
        if data.notes is not None:
            hour.notes = data.notes

        hour.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(hour)
        return hour

    async def delete_service_hour(
        self, db: AsyncSession, hour_id: int
    ) -> None:
        """Delete a service hour"""
        hour = await self.get_service_hour(db, hour_id)
        await db.execute(delete(ServiceHour).where(ServiceHour.id == hour_id))
        await db.commit()

    async def delete_by_position(
        self, db: AsyncSession, position_id: int
    ) -> None:
        """Delete all service hours for a position (cascade on position delete)"""
        await db.execute(
            delete(ServiceHour).where(ServiceHour.position_id == position_id)
        )
        await db.commit()


service_hour_service = ServiceHourService()