import logging
from datetime import date as date_cls
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from reservations.models import ArticleReservation
from reservations.schemas import ReservationCreate

logger = logging.getLogger(__name__)


class ReservationService:

    async def list_for_article(
        self, db: AsyncSession, article_id: int
    ) -> list[ArticleReservation]:
        result = await db.execute(
            select(ArticleReservation)
            .where(ArticleReservation.article_id == article_id)
            .order_by(ArticleReservation.reserved_from)
        )
        return result.scalars().all()

    async def list_all(
        self, db: AsyncSession
    ) -> list[ArticleReservation]:
        """Return all reservations ordered by date."""
        result = await db.execute(
            select(ArticleReservation).order_by(ArticleReservation.reserved_from)
        )
        return result.scalars().all()

    async def list_all_with_articles(
        self, db: AsyncSession
    ) -> list[dict]:
        """Return all reservations joined with article names."""
        from articles.models import Article
        result = await db.execute(
            select(
                ArticleReservation.id,
                ArticleReservation.article_id,
                Article.name.label("article_name"),
                Article.internal_number.label("internal_number"),
                ArticleReservation.reserved_from,
                ArticleReservation.reserved_to,
                ArticleReservation.note,
                ArticleReservation.created_by,
                ArticleReservation.created_at,
            )
            .outerjoin(Article, ArticleReservation.article_id == Article.id)
            .order_by(ArticleReservation.reserved_from)
        )
        rows = result.all()
        return [
            {
                "id": r[0],
                "article_id": r[1],
                "article_name": r[2],
                "internal_number": r[3],
                "reserved_from": r[4],
                "reserved_to": r[5],
                "note": r[6],
                "created_by": r[7],
                "created_at": r[8],
            }
            for r in rows
        ]

    async def check_conflict(
        self,
        db: AsyncSession,
        article_id: int,
        from_date: date_cls,
        to_date: date_cls,
        exclude_id: int | None = None,
    ) -> bool:
        """Returns True if there is a conflicting reservation (date ranges overlap)."""
        q = select(ArticleReservation).where(
            and_(
                ArticleReservation.article_id == article_id,
                ArticleReservation.reserved_from <= to_date,
                ArticleReservation.reserved_to >= from_date,
            )
        )
        if exclude_id:
            q = q.where(ArticleReservation.id != exclude_id)
        result = await db.execute(q)
        return result.scalar_one_or_none() is not None

    async def create(
        self, db: AsyncSession, data: ReservationCreate, user_id: int
    ) -> ArticleReservation:
        if await self.check_conflict(
            db, data.article_id, data.reserved_from, data.reserved_to
        ):
            raise HTTPException(409, "Artykuł jest już zarezerwowany w tym terminie")
        obj = ArticleReservation(**data.model_dump(), created_by=user_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        logger.info(
            "Reservation created: id=%s article_id=%s %s – %s by user_id=%s",
            obj.id, obj.article_id, obj.reserved_from, obj.reserved_to, user_id,
        )
        return obj

    async def delete(self, db: AsyncSession, reservation_id: int) -> None:
        obj = await db.get(ArticleReservation, reservation_id)
        if not obj:
            raise HTTPException(404, "Rezerwacja nie została znaleziona")
        await db.delete(obj)
        await db.commit()
        logger.info("Reservation deleted: id=%s", reservation_id)

    async def get_active_for_article(
        self, db: AsyncSession, article_id: int, from_date: date_cls | None = None
    ) -> list[ArticleReservation]:
        """Return future/current reservations for an article (reserved_to >= today)."""
        today = from_date or date_cls.today()
        result = await db.execute(
            select(ArticleReservation)
            .where(
                and_(
                    ArticleReservation.article_id == article_id,
                    ArticleReservation.reserved_to >= today,
                )
            )
            .order_by(ArticleReservation.reserved_from)
        )
        return result.scalars().all()


reservation_service = ReservationService()
