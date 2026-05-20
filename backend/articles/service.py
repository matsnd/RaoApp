from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from articles.models import Article
from articles.schemas import ArticleCreate
from shared.exceptions import not_found


class ArticleService:
    async def list_articles(
        self, db: AsyncSession,
        search: str | None = None,
        category_id: int | None = None,
        owner_id: int | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        from categories.models import Category
        from contractors.models import Contractor
        from contracts.models import Contract, ContractPosition
        from articles.schemas import ArticleListItem
        from sqlalchemy.orm import aliased

        stmt = select(Article)
        if search:
            stmt = stmt.where(Article.name.ilike(f"%{search}%"))
        if category_id:
            stmt = stmt.where(Article.category_id == category_id)
        if owner_id:
            stmt = stmt.where(Article.owner_id == owner_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(Article.name).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(stmt)
        articles = result.scalars().all()

        items = []
        for a in articles:
            cat_name = None
            if a.category_id:
                cat = await db.get(Category, a.category_id)
                cat_name = cat.name if cat else None

            own_name = None
            if a.owner_id:
                own = await db.get(Contractor, a.owner_id)
                own_name = own.name if own else None

            active_num = None
            try:
                active = await db.execute(
                    select(Contract.number)
                    .join(ContractPosition, ContractPosition.contract_id == Contract.id)
                    .where(ContractPosition.article_id == a.id)
                    .where(Contract.date_to >= date.today())
                    .limit(1)
                )
                active_num = active.scalar_one_or_none()
            except Exception:
                pass

            cond_count = 0
            items.append(ArticleListItem(
                id=a.id, name=a.name, is_service=a.is_service,
                internal_number=a.internal_number, registration_no=a.registration_no,
                serial_no=a.serial_no, brand=a.brand, model=a.model,
                replacement_value=a.replacement_value,
                category_name=cat_name, owner_name=own_name, notes=a.notes,
                active_contract_number=active_num,
                created_at=a.created_at, updated_at=a.updated_at,
                conditions_count=cond_count,
            ))
        return items, total

    async def get_article(self, db: AsyncSession, article_id: int) -> Article:
        result = await db.execute(select(Article).where(Article.id == article_id))
        article = result.scalar_one_or_none()
        if not article:
            raise not_found("Artykuł")
        return article

    async def create_article(self, db: AsyncSession, data: ArticleCreate) -> Article:
        article = Article(**data.model_dump(), created_at=datetime.utcnow())
        db.add(article)
        await db.commit()
        await db.refresh(article)
        return article

    async def update_article(self, db: AsyncSession, article_id: int, data: ArticleCreate) -> Article:
        article = await self.get_article(db, article_id)
        for field, value in data.model_dump().items():
            setattr(article, field, value)
        article.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(article)
        return article

    async def delete_article(self, db: AsyncSession, article_id: int):
        article = await self.get_article(db, article_id)
        await db.delete(article)
        await db.commit()

    async def duplicate_article(self, db: AsyncSession, article_id: int) -> Article:
        original = await self.get_article(db, article_id)
        copy = Article(
            name=f"{original.name} (kopia)",
            is_service=original.is_service,
            internal_number=original.internal_number,
            registration_no=None,
            serial_no=None,
            brand=original.brand,
            model=original.model,
            replacement_value=original.replacement_value,
            category_id=original.category_id,
            owner_id=original.owner_id,
            branch_id=original.branch_id,
            description=original.description,
            notes=original.notes,
            rental_days=original.rental_days,
            article_type=original.article_type,
            created_at=datetime.utcnow(),
        )
        db.add(copy)
        await db.commit()
        await db.refresh(copy)
        return copy

    async def check_availability(
        self, db: AsyncSession, article_id: int, date_from: date, date_to: date,
        exclude_contract_id: int | None = None,
    ):
        from contracts.models import Contract, ContractPosition
        from contractors.models import Contractor
        from articles.schemas import AvailabilityConflict, AvailabilityResponse

        stmt = (
            select(Contract.id, Contract.number, Contract.date_from, Contract.date_to, Contractor.name)
            .join(ContractPosition, ContractPosition.contract_id == Contract.id)
            .join(Contractor, Contract.contractor_id == Contractor.id)
            .where(ContractPosition.article_id == article_id)
            .where(Contract.date_from <= date_to)
            .where(Contract.date_to >= date_from)
        )
        if exclude_contract_id is not None:
            stmt = stmt.where(Contract.id != exclude_contract_id)
        result = await db.execute(stmt)
        rows = result.all()
        conflicts = [
            AvailabilityConflict(
                contract_id=r[0], contract_number=r[1],
                date_from=r[2], date_to=r[3], contractor_name=r[4],
            )
            for r in rows
        ]
        return AvailabilityResponse(is_available=len(conflicts) == 0, conflicting_contracts=conflicts)


article_service = ArticleService()
