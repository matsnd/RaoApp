import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db
from settings.schemas import (
    BranchCreate, BranchResponse, CategoryCreate, CategoryResponse, CategoryTreeNode,
    CompanyResponse, CompanyUpdate, FeePresetGroupCreate, FeePresetGroupResponse,
    RateTypeCreate, RateTypeResponse, ReorderRequest, SalespersonCreate, SalespersonResponse,
    ServiceFeeTemplateCreate, ServiceFeeTemplateResponse,
    ArticleRatePresetCreate, ArticleRatePresetUpdate, ArticleRatePresetResponse,
    ArticleRatePresetItemCreate, ArticleRatePresetItemUpdate, ArticleRatePresetItemResponse,
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


# RAO-P3-002: Upload logo firmy
@router.post("/company/logo", status_code=200)
async def upload_company_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "svg"}
    MAX_SIZE = 2 * 1024 * 1024  # 2 MB

    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Dozwolone formaty: PNG, JPG, JPEG, SVG")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Plik za duży (max 2 MB)")

    os.makedirs("static/logos", exist_ok=True)
    filename = f"company_logo.{ext}"
    with open(f"static/logos/{filename}", "wb") as fh:
        fh.write(content)

    logo_url = f"/rao/api/static/logos/{filename}"

    company = await settings_service.get_company(db)
    company.logo_path = logo_url
    await db.commit()

    return {"logo_url": logo_url}


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


@router.get("/categories/tree", response_model=list[CategoryTreeNode])
async def list_categories_tree(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await settings_service.list_categories_tree(db)


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


@router.put("/categories/{cat_id}", response_model=CategoryResponse)
async def update_category(
    cat_id: int,
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_category(db, cat_id, data)


@router.delete("/categories/{cat_id}", status_code=204)
async def delete_category(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_category(db, cat_id)


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


@router.put("/rate-types/{rt_id}", response_model=RateTypeResponse)
async def update_rate_type(
    rt_id: int,
    data: RateTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_rate_type(db, rt_id, data)


@router.delete("/rate-types/{rt_id}", status_code=204)
async def delete_rate_type(
    rt_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_rate_type(db, rt_id)


@router.delete("/salespeople/{sp_id}", status_code=204)
async def delete_salesperson(
    sp_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_salesperson(db, sp_id)


@router.get("/fee-preset-groups", response_model=list[FeePresetGroupResponse])
async def list_fee_preset_groups(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return await settings_service.list_fee_preset_groups(db)


@router.post("/fee-preset-groups", response_model=FeePresetGroupResponse, status_code=201)
async def create_fee_preset_group(
    data: FeePresetGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_fee_preset_group(db, data)


@router.put("/fee-preset-groups/{preset_id}", response_model=FeePresetGroupResponse)
async def update_fee_preset_group(
    preset_id: int,
    data: FeePresetGroupCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_fee_preset_group(db, preset_id, data)


@router.delete("/fee-preset-groups/{preset_id}", status_code=204)
async def delete_fee_preset_group(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_fee_preset_group(db, preset_id)


@router.post("/fee-preset-groups/{preset_id}/templates", response_model=ServiceFeeTemplateResponse, status_code=201)
async def add_template_to_preset(
    preset_id: int,
    data: ServiceFeeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.add_template_to_preset(db, preset_id, data)


@router.patch("/fee-preset-groups/{preset_id}/templates/reorder", status_code=204)
async def reorder_preset_templates(
    preset_id: int,
    data: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.reorder_preset_templates(db, preset_id, data.order)


@router.put("/fee-preset-groups/{preset_id}/templates/{template_id}", response_model=ServiceFeeTemplateResponse)
async def update_preset_template(
    preset_id: int,
    template_id: int,
    data: ServiceFeeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_preset_template(db, template_id, data)


@router.delete("/fee-preset-groups/{preset_id}/templates/{template_id}", status_code=204)
async def delete_preset_template(
    preset_id: int,
    template_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_preset_template(db, template_id)


# ----------------------------------------------------------------------
# RAO-P1-001: Predefiniowane cenniki warunków rozliczenia maszyn
# ----------------------------------------------------------------------

@router.get("/articles/{article_id}/rate-presets", response_model=list[ArticleRatePresetResponse])
async def list_article_rate_presets(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await settings_service.list_article_rate_presets(db, article_id)


@router.get("/articles/{article_id}/rate-presets/default", response_model=ArticleRatePresetResponse | None)
async def get_default_rate_preset(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Zwraca domyślny cennik maszyny lub null (200 z body null)."""
    return await settings_service.get_default_preset(db, article_id)


@router.post("/articles/{article_id}/rate-presets", response_model=ArticleRatePresetResponse, status_code=201)
async def create_article_rate_preset(
    article_id: int,
    data: ArticleRatePresetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.create_article_rate_preset(db, article_id, data)


@router.get("/rate-presets/{preset_id}", response_model=ArticleRatePresetResponse)
async def get_article_rate_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await settings_service.get_article_rate_preset(db, preset_id)


@router.put("/rate-presets/{preset_id}", response_model=ArticleRatePresetResponse)
async def update_article_rate_preset(
    preset_id: int,
    data: ArticleRatePresetUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_article_rate_preset(db, preset_id, data)


@router.delete("/rate-presets/{preset_id}", status_code=204)
async def delete_article_rate_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_article_rate_preset(db, preset_id)


@router.patch("/rate-presets/{preset_id}/set-default", response_model=ArticleRatePresetResponse)
async def set_default_rate_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.set_default_preset(db, preset_id)


@router.post("/rate-presets/{preset_id}/items", response_model=ArticleRatePresetItemResponse, status_code=201)
async def add_rate_preset_item(
    preset_id: int,
    data: ArticleRatePresetItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.add_preset_item(db, preset_id, data)


@router.put("/rate-presets/items/{item_id}", response_model=ArticleRatePresetItemResponse)
async def update_rate_preset_item(
    item_id: int,
    data: ArticleRatePresetItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await settings_service.update_preset_item(db, item_id, data)


@router.delete("/rate-presets/items/{item_id}", status_code=204)
async def delete_rate_preset_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await settings_service.delete_preset_item(db, item_id)
