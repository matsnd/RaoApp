from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from articles.models import Article
from articles.schemas import ArticleCreate, ArticleDetail, ArticleListItem, AvailabilityResponse
from articles.service import article_service
from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from shared.pagination import PaginatedResponse

router = APIRouter(prefix="/articles", tags=["articles"])


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
        owner_id=a.owner_id, owner_name=own_name,
        branch_id=a.branch_id, description=a.description, notes=a.notes,
        rental_days=a.rental_days, article_type=a.article_type,
        fakturownia_product_id=a.fakturownia_product_id,
        created_at=a.created_at, updated_at=a.updated_at,
    )


@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    owner_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = await article_service.list_articles(db, search, category_id, owner_id, page, per_page)
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = await article_service.get_article(db, article_id)
    return await _build_detail(db, a)


@router.post("", response_model=ArticleDetail, status_code=201)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = await article_service.create_article(db, data)
    return await _build_detail(db, a)


@router.put("/{article_id}", response_model=ArticleDetail)
async def update_article(
    article_id: int,
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = await article_service.update_article(db, article_id, data)
    return await _build_detail(db, a)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await article_service.delete_article(db, article_id)


@router.post("/{article_id}/duplicate", response_model=ArticleDetail, status_code=201)
async def duplicate_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    a = await article_service.duplicate_article(db, article_id)
    return await _build_detail(db, a)


@router.get("/{article_id}/availability", response_model=AvailabilityResponse)
async def check_availability(
    article_id: int,
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await article_service.check_availability(db, article_id, date_from, date_to)
