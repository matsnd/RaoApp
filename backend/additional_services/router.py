from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from additional_services.models import AdditionalService
from additional_services.schemas import (
    AdditionalServiceCreate, AdditionalServiceUpdate, AdditionalServiceDetail, AdditionalServiceListItem,
)
from additional_services.service import additional_service_service

router = APIRouter(prefix="/additional-services", tags=["additional-services"])


async def _verify_additional_service_access(db: AsyncSession, service_id: int, user: User, allow_mutation: bool = False):
    """IDOR guard — single-user mode (stub dla future RBAC)."""
    return await additional_service_service.get_additional_service(db, service_id)


async def _build_detail(db: AsyncSession, s: AdditionalService) -> AdditionalServiceDetail:
    return AdditionalServiceDetail(
        id=s.id, name=s.name, display_name=s.display_name,
        default_amount=s.default_amount,
        description=s.description, notes=s.notes,
        is_archival=s.is_archival,
        fakturownia_product_id=s.fakturownia_product_id,
        fakturownia_tax_rate=s.fakturownia_tax_rate,
        fakturownia_gtu_code=s.fakturownia_gtu_code,
        fakturownia_pkwiu=s.fakturownia_pkwiu,
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.get("", response_model=list[AdditionalServiceListItem])
async def list_additional_services(
    search: str | None = Query(None),
    archival: str = Query("active"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await additional_service_service.list_additional_services(
        db, search=search, archival_status=archival, page=page, per_page=per_page,
    )
    return items


@router.get("/{service_id}", response_model=AdditionalServiceDetail)
async def get_additional_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    s = await _verify_additional_service_access(db, service_id, _)
    return await _build_detail(db, s)


@router.post("", response_model=AdditionalServiceDetail, status_code=201)
async def create_additional_service(
    data: AdditionalServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    s = await additional_service_service.create_additional_service(db, data)
    return await _build_detail(db, s)


@router.put("/{service_id}", response_model=AdditionalServiceDetail)
async def update_additional_service(
    service_id: int,
    data: AdditionalServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    s = await additional_service_service.update_additional_service(db, service_id, data)
    return await _build_detail(db, s)


@router.delete("/{service_id}", status_code=204)
async def delete_additional_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await additional_service_service.delete_additional_service(db, service_id)
