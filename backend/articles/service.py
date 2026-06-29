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
        archival_status: str = "active",
        page: int = 1,
        per_page: int = 50,
    ):
        from categories.models import Category
        from contractors.models import Contractor
        from contracts.models import Contract, ContractPosition
        from articles.schemas import ArticleListItem
        from sqlalchemy.orm import aliased

        stmt = select(Article)
        if archival_status == "active":
            stmt = stmt.where(Article.is_archival == False)  # noqa: E712
        elif archival_status == "archival":
            stmt = stmt.where(Article.is_archival == True)   # noqa: E712
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

        # RAO-P0-035: Batch-fetch categories, owners & active contracts to eliminate N+1
        article_ids = [a.id for a in articles]
        category_ids = {a.category_id for a in articles if a.category_id}
        owner_ids = {a.owner_id for a in articles if a.owner_id}

        cat_map = {}
        if category_ids:
            cat_result = await db.execute(
                select(Category.id, Category.name).where(Category.id.in_(category_ids))
            )
            cat_map = dict(cat_result.all())

        owner_map = {}
        if owner_ids:
            own_result = await db.execute(
                select(Contractor.id, Contractor.name).where(Contractor.id.in_(owner_ids))
            )
            owner_map = dict(own_result.all())

        # Batch-fetch active contract numbers for all articles in one query
        active_map = {}
        if article_ids:
            today = date.today()
            active_result = await db.execute(
                select(ContractPosition.article_id, Contract.number)
                .join(Contract, ContractPosition.contract_id == Contract.id)
                .where(ContractPosition.article_id.in_(article_ids))
                .where(Contract.date_to >= today)
                .distinct()
            )
            for aid, num in active_result.all():
                if aid not in active_map:
                    active_map[aid] = num

        items = []
        for a in articles:
            cat_name = cat_map.get(a.category_id) if a.category_id else None
            own_name = owner_map.get(a.owner_id) if a.owner_id else None
            active_num = active_map.get(a.id)

            cond_count = 0
            items.append(ArticleListItem(
                id=a.id, name=a.name, is_service=a.is_service,
                internal_number=a.internal_number, registration_no=a.registration_no,
                serial_no=a.serial_no, brand=a.brand, model=a.model,
                replacement_value=a.replacement_value,
                category_name=cat_name,
                category_main=a.category_main,
                is_archival=a.is_archival,
                is_external=a.is_external,  # RAO-P1-027
                fakturownia_product_id=a.fakturownia_product_id,
                owner_name=own_name, notes=a.notes,
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
            is_external=original.is_external,  # RAO-P1-027
            zasieg_m=original.zasieg_m,
            udzwig_t=original.udzwig_t,
            dodatki=original.dodatki,
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
