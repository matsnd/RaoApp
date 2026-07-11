from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from articles.models import Article
from articles.schemas import ArticleCreate, ArticleDetail, ArticleListItem, AvailabilityResponse, ArticleArchivalFilter
from articles.service import article_service
from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from shared.pagination import PaginatedResponse
from shared.exceptions import not_found, forbidden

router = APIRouter(prefix="/articles", tags=["articles"])


async def _verify_article_access(db: AsyncSession, article_id: int, user: User, allow_mutation: bool = False):
    """RAO-SEC-003 fix: IDOR guard for articles.

    - admin: all access
    - user/viewer: only own branch (branch_id match) or NULL branch (legacy)
    - viewer: read-only (allow_mutation=False)

    NOTE (2026-07-11): IDOR WYŁĄCZONY — single-user mode. Branch/viewer checks
    pominięte. Zostaje tylko get_article + not_found. Pełny RBAC wdrożony gdy
    pojawią się wymagania wieloużytkownikowe.
    """
    a = await article_service.get_article(db, article_id)
    if a is None:
        raise not_found("Maszyna")
    return a


async def _build_detail(db: AsyncSession, a: Article) -> ArticleDetail:
    from categories.models import Category
    from contractors.models import Contractor
    cat_name = None
    if a.category_id:
        cat = await db.get(Category, a.category_id)
        cat_name = cat.name if cat else None
    own_name = None
    if a.owner_id:
        own = await db.get(Contractor, a.owner_id)
        own_name = own.name if own else None
    return ArticleDetail(
        id=a.id, name=a.name, is_service=a.is_service,
        internal_number=a.internal_number, registration_no=a.registration_no,
        serial_no=a.serial_no, brand=a.brand, model=a.model,
        replacement_value=a.replacement_value,
        category_id=a.category_id, category_name=cat_name,
        category_main=a.category_main, category_sub1=a.category_sub1,
        category_sub2=a.category_sub2, category_sub3=a.category_sub3,
        owner_id=a.owner_id, owner_name=own_name,
        branch_id=a.branch_id, description=a.description, notes=a.notes,
        rental_days=a.rental_days, article_type=a.article_type,
        is_archival=a.is_archival,
        is_external=a.is_external,  # RAO-P1-027
        zasieg_m=a.zasieg_m, udzwig_t=a.udzwig_t, dodatki=a.dodatki,
        fakturownia_product_id=a.fakturownia_product_id,
        power_type=a.power_type,
        created_at=a.created_at, updated_at=a.updated_at,
    )


@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    owner_id: int | None = Query(None),
    is_service: bool | None = Query(None),
    archival_status: ArticleArchivalFilter = Query(ArticleArchivalFilter.ACTIVE),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await article_service.list_articles(
        db, search, category_id, owner_id, archival_status.value, is_service, page, per_page
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    a = await _verify_article_access(db, article_id, current_user)
    return await _build_detail(db, a)


@router.post("", response_model=ArticleDetail, status_code=201)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "viewer":
        raise forbidden("Tylko odczyt — brak uprawnień do modyfikacji.")
    a = await article_service.create_article(db, data)
    return await _build_detail(db, a)


@router.put("/{article_id}", response_model=ArticleDetail)
async def update_article(
    article_id: int,
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    a = await _verify_article_access(db, article_id, current_user, allow_mutation=True)
    updated = await article_service.update_article(db, article_id, data)
    return await _build_detail(db, updated)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _verify_article_access(db, article_id, current_user, allow_mutation=True)
    await article_service.delete_article(db, article_id)


@router.post("/{article_id}/duplicate", response_model=ArticleDetail, status_code=201)
async def duplicate_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    a = await _verify_article_access(db, article_id, current_user, allow_mutation=True)
    dup = await article_service.duplicate_article(db, article_id)
    return await _build_detail(db, dup)


@router.get("/{article_id}/availability", response_model=AvailabilityResponse)
async def check_availability(
    article_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    exclude_contract_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await article_service.check_availability(
        db, article_id, date_from, date_to, exclude_contract_id=exclude_contract_id
    )


# ----------------------------------------------------------------------
# RAO-P1-001: Auto-prefill — warunki z ostatniej umowy tej maszyny
# ----------------------------------------------------------------------

@router.get(
    "/{article_id}/last-conditions",
    response_model=dict,
    responses={404: {"description": "Brak historii umów dla tej maszyny"}},
)
async def get_last_conditions_for_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Auto-prefill — warunki z najnowszej umowy zawierającej pozycję z tym article_id.

    Response: {
      source_contract_number, source_contract_date, source_position_id, conditions[]
    }
    404 jeśli brak historii.
    """
    from contracts.service import contract_service
    data = await contract_service.get_last_conditions_for_article(db, article_id, user)
    if data is None:
        raise HTTPException(status_code=404, detail="Brak historii umów dla tej maszyny")
    return data
