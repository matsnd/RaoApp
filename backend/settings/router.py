from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from settings.schemas import (
    BranchCreate, BranchResponse, CategoryCreate, CategoryResponse,
    CompanyResponse, CompanyUpdate, RateTypeCreate, RateTypeResponse,
    SalespersonCreate, SalespersonResponse,
    ServiceFeeTemplateCreate, ServiceFeeTemplateReorder, ServiceFeeTemplateResponse,
)
from settings.service import settings_service

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/company", response_model=CompanyResponse)
async def get_company(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.get_company(db)


@router.put("/company", response_model=CompanyResponse)
async def update_company(
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_company(db, data)


@router.get("/service-fee-templates", response_model=list[ServiceFeeTemplateResponse])
async def list_fee_templates(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_fee_templates(db)


@router.post("/service-fee-templates", response_model=ServiceFeeTemplateResponse, status_code=201)
async def create_fee_template(
    data: ServiceFeeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_fee_template(db, data)


@router.put("/service-fee-templates/{template_id}", response_model=ServiceFeeTemplateResponse)
async def update_fee_template(
    template_id: int,
    data: ServiceFeeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_fee_template(db, template_id, data)


@router.delete("/service-fee-templates/{template_id}", status_code=204)
async def delete_fee_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_fee_template(db, template_id)


@router.post("/service-fee-templates/reorder", status_code=200)
async def reorder_fee_templates(
    data: ServiceFeeTemplateReorder,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.reorder_fee_templates(db, data.ids)
    return {"message": "Kolejność zaktualizowana"}


@router.get("/salespeople", response_model=list[SalespersonResponse])
async def list_salespeople(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_salespeople(db)


@router.post("/salespeople", response_model=SalespersonResponse, status_code=201)
async def create_salesperson(
    data: SalespersonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_salesperson(db, data)


@router.put("/salespeople/{sp_id}", response_model=SalespersonResponse)
async def update_salesperson(
    sp_id: int,
    data: SalespersonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_salesperson(db, sp_id, data)


@router.patch("/salespeople/{sp_id}/toggle", response_model=SalespersonResponse)
async def toggle_salesperson(
    sp_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.toggle_salesperson(db, sp_id)


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_categories(db)


@router.post("/categories", response_model=CategoryResponse, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_category(db, data)


@router.get("/branches", response_model=list[BranchResponse])
async def list_branches(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_branches(db)


@router.post("/branches", response_model=BranchResponse, status_code=201)
async def create_branch(
    data: BranchCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_branch(db, data)


@router.get("/rate-types", response_model=list[RateTypeResponse])
async def list_rate_types(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_rate_types(db)


@router.post("/rate-types", response_model=RateTypeResponse, status_code=201)
async def create_rate_type(
    data: RateTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_rate_type(db, data)
