"""RAO-P2-062 Faza 1 - router archiwum.

Wszystkie endpointy z auth (get_current_user). Write endpointy (POST/PUT/DELETE/PATCH)
z require_admin. Brak POST/PUT/DELETE na umowach archiwum (read-only).
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from archive.schemas import (
    ArchiveArticleCategoryUpdate,
    ArchiveArticleResponse,
    ArchiveCategoryCreate,
    ArchiveCategoryResponse,
    ArchiveCategoryStatItem,
    ArchiveCategoryTreeNode,
    ArchiveCityStatItem,
    ArchiveContractDetail,
    ArchiveContractListItem,
    ArchiveMachineRoiResponse,
    ArchiveStatsSummary,
    ArchiveTopMachineItem,
    PaginatedResponse,
)
from archive import service
from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db

router = APIRouter(prefix="/archive", tags=["archive"])


# ── Umowy archiwum (read-only) ───────────────────────────────────────────────

@router.get("/contracts", response_model=PaginatedResponse[ArchiveContractListItem])
async def list_archive_contracts(
    search: str | None = Query(None),
    contractor_id: int | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    contract_type: str | None = Query(None, pattern="^[SU]$"),
    city: str | None = Query(None, description="Filtr po mieście (exact match) — drill-down Miasta"),
    article_id: int | None = Query(None, description="Filtr po article_id (umowy z tą maszyną) — drill-down Top maszyny"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await service.list_archive_contracts(
        db,
        search=search,
        contractor_id=contractor_id,
        date_from=date_from,
        date_to=date_to,
        contract_type=contract_type,
        city=city,
        article_id=article_id,
        page=page,
        per_page=per_page,
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/contracts/{contract_id}", response_model=ArchiveContractDetail)
async def get_archive_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contract = await service.get_archive_contract(db, contract_id)
    # RAO-SEC-010: IDOR fix — branch check for non-admin users
    if current_user.role != "admin":
        if contract.branch_id is not None and contract.branch_id != current_user.branch_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Umowa archiwalna nie znaleziona")
    return contract


# ── Artykuly archiwum (read + PATCH category_id) ─────────────────────────────

@router.get("/articles", response_model=PaginatedResponse[ArchiveArticleResponse])
async def list_archive_articles(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await service.list_archive_articles(
        db, search=search, category_id=category_id, page=page, per_page=per_page
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/articles/{article_id}", response_model=ArchiveArticleResponse)
async def get_archive_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_archive_article(db, article_id)


@router.patch("/articles/{article_id}/category", response_model=ArchiveArticleResponse)
async def update_archive_article_category(
    article_id: int,
    payload: ArchiveArticleCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await service.update_archive_article_category(db, article_id, payload)


# ── Kategorie archiwum (CRUD) ────────────────────────────────────────────────

@router.get("/categories", response_model=list[ArchiveCategoryResponse])
async def list_archive_categories(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.list_archive_categories(db)


@router.get("/categories/tree", response_model=list[ArchiveCategoryTreeNode])
async def list_archive_categories_tree(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.list_archive_categories_tree(db)


@router.post("/categories", response_model=ArchiveCategoryResponse, status_code=201)
async def create_archive_category(
    data: ArchiveCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await service.create_archive_category(db, data)


@router.put("/categories/{cat_id}", response_model=ArchiveCategoryResponse)
async def update_archive_category(
    cat_id: int,
    data: ArchiveCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await service.update_archive_category(db, cat_id, data)


@router.delete("/categories/{cat_id}", status_code=204)
async def delete_archive_category(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await service.delete_archive_category(db, cat_id)


# ── Stats archiwum ───────────────────────────────────────────────────────────

@router.get("/stats/summary", response_model=ArchiveStatsSummary)
async def archive_stats_summary(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_archive_stats_summary(db, date_from, date_to)


@router.get("/stats/top-machines", response_model=list[ArchiveTopMachineItem])
async def archive_top_machines(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_archive_top_machines(db, date_from, date_to, limit=limit)


@router.get("/stats/by-category", response_model=list[ArchiveCategoryStatItem])
async def archive_stats_by_category(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_archive_stats_by_category(db, date_from, date_to)


@router.get("/stats/machine-roi", response_model=ArchiveMachineRoiResponse)
async def archive_machine_roi(
    article_id: int,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_archive_machine_roi(db, article_id, date_from, date_to)


@router.get("/stats/by-city", response_model=list[ArchiveCityStatItem])
async def archive_stats_by_city(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Statystyki szacunkowe po miastach (z archive_contracts.city)."""
    return await service.get_archive_stats_by_city(db, date_from, date_to, limit=limit)
