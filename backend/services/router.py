from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from services.models import Service
from services.schemas import (
    ServiceCreate, ServiceUpdate, ServiceDetail, ServiceListItem,
)
from services.service import service_service

router = APIRouter(prefix="/services", tags=["services"])


async def _verify_service_access(db: AsyncSession, service_id: int, user: User, allow_mutation: bool = False):
    """IDOR guard — single-user mode (stub dla future RBAC)."""
    return await service_service.get_service(db, service_id)


async def _build_detail(db: AsyncSession, s: Service) -> ServiceDetail:
    return ServiceDetail(
        id=s.id, name=s.name, description=s.description, notes=s.notes,
        replacement_value=s.replacement_value,
        fakturownia_product_id=s.fakturownia_product_id,
        fakturownia_tax_rate=s.fakturownia_tax_rate,
        fakturownia_gtu_code=s.fakturownia_gtu_code,
        fakturownia_pkwiu=s.fakturownia_pkwiu,
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.get("", response_model=list[ServiceListItem])
async def list_services(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await service_service.list_services(
        db, search=search, page=page, per_page=per_page,
    )
    return items


@router.get("/{service_id}", response_model=ServiceDetail)
async def get_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = await _verify_service_access(db, service_id, _)
    return await _build_detail(db, s)


@router.post("", response_model=ServiceDetail, status_code=201)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    s = await service_service.create_service(db, data)
    return await _build_detail(db, s)


@router.put("/{service_id}", response_model=ServiceDetail)
async def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    s = await service_service.update_service(db, service_id, data)
    return await _build_detail(db, s)


@router.delete("/{service_id}", status_code=204)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await service_service.delete_service(db, service_id)
