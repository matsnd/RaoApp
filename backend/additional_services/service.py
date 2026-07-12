from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from additional_services.models import AdditionalService
from additional_services.schemas import AdditionalServiceCreate, AdditionalServiceUpdate
from shared.exceptions import not_found


class AdditionalServiceService:
    async def list_additional_services(
        self, db: AsyncSession,
        search: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        from additional_services.schemas import AdditionalServiceListItem

        stmt = select(AdditionalService)
        if search:
            stmt = stmt.where(AdditionalService.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(AdditionalService.name).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        services = result.scalars().all()

        items = [
            AdditionalServiceListItem(
                id=s.id, name=s.name, display_name=s.display_name,
                default_amount=s.default_amount,
                description=s.description,
                fakturownia_product_id=s.fakturownia_product_id,
                created_at=s.created_at, updated_at=s.updated_at,
            )
            for s in services
        ]
        return items, total

    async def get_additional_service(self, db: AsyncSession, service_id: int) -> AdditionalService:
        result = await db.execute(select(AdditionalService).where(AdditionalService.id == service_id))
        service = result.scalar_one_or_none()
        if not service:
            raise not_found("Usługa dodatkowa")
        return service

    async def create_additional_service(self, db: AsyncSession, data: AdditionalServiceCreate) -> AdditionalService:
        service = AdditionalService(**data.model_dump(), created_at=datetime.utcnow())
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

    async def update_additional_service(
        self, db: AsyncSession, service_id: int, data: AdditionalServiceUpdate
    ) -> AdditionalService:
        service = await self.get_additional_service(db, service_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        service.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(service)
        return service

    async def delete_additional_service(self, db: AsyncSession, service_id: int):
        service = await self.get_additional_service(db, service_id)
        await db.delete(service)
        await db.commit()


additional_service_service = AdditionalServiceService()
