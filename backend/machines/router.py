from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from machines.models import Machine
from machines.schemas import (
    MachineCreate, MachineUpdate, MachineDetail, MachineListItem,
    AvailabilityResponse, MachineArchivalFilter,
)
from machines.service import machine_service
from shared.exceptions import not_found

router = APIRouter(prefix="/machines", tags=["machines"])


async def _verify_machine_access(db: AsyncSession, machine_id: int, user: User, allow_mutation: bool = False):
    """IDOR guard — single-user mode (stub dla future RBAC)."""
    return await machine_service.get_machine(db, machine_id)


async def _build_detail(db: AsyncSession, m: Machine) -> MachineDetail:
    from categories.models import Category
    from contractors.models import Contractor
    from sqlalchemy import select

    cat_name = None
    if m.category_id:
        result = await db.execute(select(Category.name).where(Category.id == m.category_id))
        cat_name = result.scalar_one_or_none()
    own_name = None
    if m.owner_id:
        result = await db.execute(select(Contractor.name).where(Contractor.id == m.owner_id))
        own_name = result.scalar_one_or_none()
    return MachineDetail(
        id=m.id, name=m.name,
        internal_number=m.internal_number, registration_no=m.registration_no,
        serial_no=m.serial_no, brand=m.brand, model=m.model,
        replacement_value=m.replacement_value,
        category_id=m.category_id, category_name=cat_name,
        category_main=m.category_main, category_sub1=m.category_sub1,
        category_sub2=m.category_sub2, category_sub3=m.category_sub3,
        owner_id=m.owner_id, owner_name=own_name, branch_id=m.branch_id,
        description=m.description, notes=m.notes, rental_days=m.rental_days,
        is_archival=m.is_archival, is_external=m.is_external,
        reach_m=m.reach_m, capacity_t=m.capacity_t, accessories=m.accessories,
        technical_attributes=m.technical_attributes,
        fakturownia_product_id=m.fakturownia_product_id,
        fakturownia_tax_rate=m.fakturownia_tax_rate,
        fakturownia_gtu_code=m.fakturownia_gtu_code,
        fakturownia_pkwiu=m.fakturownia_pkwiu,
        power_type=m.power_type,
        created_at=m.created_at, updated_at=m.updated_at,
    )


@router.get("", response_model=list[MachineListItem])
async def list_machines(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    owner_id: int | None = Query(None),
    archival: MachineArchivalFilter = Query(MachineArchivalFilter.ACTIVE),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await machine_service.list_machines(
        db, search=search, category_id=category_id, owner_id=owner_id,
        archival_status=archival.value, page=page, per_page=per_page,
    )
    return items


@router.get("/{machine_id}", response_model=MachineDetail)
async def get_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    m = await _verify_machine_access(db, machine_id, _)
    return await _build_detail(db, m)


@router.post("", response_model=MachineDetail, status_code=201)
async def create_machine(
    data: MachineCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    m = await machine_service.create_machine(db, data)
    return await _build_detail(db, m)


@router.put("/{machine_id}", response_model=MachineDetail)
async def update_machine(
    machine_id: int,
    data: MachineUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    m = await machine_service.update_machine(db, machine_id, data)
    return await _build_detail(db, m)


@router.delete("/{machine_id}", status_code=204)
async def delete_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await machine_service.delete_machine(db, machine_id)


@router.post("/{machine_id}/duplicate", response_model=MachineDetail, status_code=201)
async def duplicate_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    dup = await machine_service.duplicate_machine(db, machine_id)
    return await _build_detail(db, dup)


@router.get("/{machine_id}/availability", response_model=AvailabilityResponse)
async def check_availability(
    machine_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    exclude_contract_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await machine_service.check_availability(
        db, machine_id, date_from, date_to, exclude_contract_id=exclude_contract_id
    )


@router.get(
    "/{machine_id}/last-conditions",
    response_model=dict,
    responses={404: {"description": "Brak historii umów dla tej maszyny"}},
)
async def get_last_conditions_for_machine(
    machine_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Auto-prefill — warunki z najnowszej umowy zawierającej pozycję z tym machine_id."""
    from contracts.service import contract_service
    data = await contract_service.get_last_conditions_for_machine(db, machine_id, user)
    if data is None:
        raise HTTPException(status_code=404, detail="Brak historii umów dla tej maszyny")
    return data
