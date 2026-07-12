from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from services.models import Service
from services.schemas import ServiceCreate, ServiceUpdate
from shared.exceptions import not_found


class ServiceService:
    async def list_services(
        self, db: AsyncSession,
        search: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        from services.schemas import ServiceListItem

        stmt = select(Service)
        if search:
            stmt = stmt.where(Service.name.ilike(f"%{search}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Service.name).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        services = result.scalars().all()

        items = [
            ServiceListItem(
                id=s.id, name=s.name, description=s.description,
                fakturownia_product_id=s.fakturownia_product_id,
                created_at=s.created_at, updated_at=s.updated_at,
                # P1-126: align shape with MachineListItem for unified frontend picker
                is_service=True, brand=None, registration_no=None, is_external=False,
            )
            for s in services
        ]
        return items, total

    async def get_service(self, db: AsyncSession, service_id: int) -> Service:
        result = await db.execute(select(Service).where(Service.id == service_id))
        service = result.scalar_one_or_none()
        if not service:
            raise not_found("Usługa")
        return service

    async def create_service(self, db: AsyncSession, data: ServiceCreate) -> Service:
        service = Service(**data.model_dump(), created_at=datetime.utcnow())
        db.add(service)
        await db.commit()
        await db.refresh(service)
        return service

    async def update_service(self, db: AsyncSession, service_id: int, data: ServiceUpdate) -> Service:
        service = await self.get_service(db, service_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        service.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(service)
        return service

    async def delete_service(self, db: AsyncSession, service_id: int):
        service = await self.get_service(db, service_id)
        await db.delete(service)
        await db.commit()


service_service = ServiceService()
