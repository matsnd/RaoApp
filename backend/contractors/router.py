from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from auth.models import User
from contractors.schemas import (
    AddressCreate, AddressResponse, ContractorCreate, ContractorDetail,
    ContractorListItem, GusLookupRequest, GusLookupResponse,
)
from contractors.service import contractor_service
from database import get_db
from shared.pagination import PaginatedResponse

router = APIRouter(prefix="/contractors", tags=["contractors"])


@router.get("", response_model=PaginatedResponse[ContractorListItem])
async def list_contractors(
    search: str | None = Query(None),
    supplier: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await contractor_service.list_contractors(db, search, supplier, page, per_page)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{contractor_id}", response_model=ContractorDetail)
async def get_contractor(
    contractor_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contractor_service.get_contractor(db, contractor_id)
    return ContractorDetail.model_validate(c)


@router.post("", response_model=ContractorDetail, status_code=201)
async def create_contractor(
    data: ContractorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contractor_service.create_contractor(db, data)
    return ContractorDetail.model_validate(c)


@router.put("/{contractor_id}", response_model=ContractorDetail)
async def update_contractor(
    contractor_id: int,
    data: ContractorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    c = await contractor_service.update_contractor(db, contractor_id, data)
    return ContractorDetail.model_validate(c)


@router.delete("/{contractor_id}", status_code=204)
async def delete_contractor(
    contractor_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contractor_service.delete_contractor(db, contractor_id)


@router.get("/{contractor_id}/addresses", response_model=list[AddressResponse])
async def list_addresses(
    contractor_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await contractor_service.list_addresses(db, contractor_id)


@router.post("/{contractor_id}/addresses", response_model=AddressResponse, status_code=201)
async def create_address(
    contractor_id: int,
    data: AddressCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await contractor_service.create_address(db, contractor_id, data)


@router.put("/{contractor_id}/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    contractor_id: int,
    address_id: int,
    data: AddressCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await contractor_service.update_address(db, contractor_id, address_id, data)


@router.delete("/{contractor_id}/addresses/{address_id}", status_code=204)
async def delete_address(
    contractor_id: int,
    address_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await contractor_service.delete_address(db, contractor_id, address_id)


@router.post("/gus-lookup", response_model=GusLookupResponse)
async def gus_lookup(
    data: GusLookupRequest,
    _: User = Depends(get_current_user),
):
    from integrations.gus import gus_client
    return await gus_client.lookup(data.nip)
