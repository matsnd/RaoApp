"""RAO-P2-062 Faza 1 - logika biznesowa archiwum.

Zasada: archiwum = READ-ONLY z wyjatkiem:
  - archive_categories (CRUD z normalizacja nazwy - mirror settings.service)
  - archive_articles.category_id (PATCH)
"""
import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from stats.calc import clamp_days
from sqlalchemy.orm import selectinload

from archive.models import (
    ArchiveArticle,
    ArchiveCategory,
    ArchiveContract,
    ArchiveContractPosition,
    ArchiveContractServiceFee,
    ArchiveContractSettlement,
    ArchivePositionCondition,
)
from archive.schemas import (
    ArchiveArticleCategoryUpdate,
    ArchiveCategoryCreate,
    ArchiveContractListItem,
    ArchiveContractDetail,
)
from shared.exceptions import conflict, not_found
from stats.calc import calculate_position_value

import logging
_logger = logging.getLogger(__name__)


def _compute_roi_pct(revenue, replacement_value) -> float | None:
    """Oblicz ROI (%) dla maszyny — używane tylko w archiwum (szacunkowe).

    Reguły (defensywne):
    - replacement_value is None lub <= 0 → None
    - revenue < 0 (korekta/zwrot) → None
    - revenue == 0 → 0.0
    - revenue > 0 → round(revenue / replacement_value * 100, 2)
    """
    if replacement_value is None or float(replacement_value) <= 0:
        return None
    rev = float(revenue) if revenue is not None else 0.0
    if rev < 0:
        _logger.warning("Negative ROI clamped: revenue=%s, replacement_value=%s", revenue, replacement_value)
        return None
    return round(rev / float(replacement_value) * 100, 2)


# ── Normalizacja nazwy kategorii (mirror settings.service) ───────────────────

def _normalize_category_name(name: str) -> str:
    if not name:
        return ""
    return re.sub(r"\s+", " ", name.strip())


def _normalize_category_key(name: str) -> str:
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.strip())
    no_dia = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    no_dia = no_dia.replace("\u0142", "l").replace("\u0141", "L")
    return re.sub(r"\s+", " ", no_dia.lower()).strip()


# ── Helper: lookup rate_type name ─────────────────────────────────────────────

async def _rate_type_names(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    from settings.models import RateType
    res = await db.execute(select(RateType.id, RateType.name).where(RateType.id.in_(ids)))
    return dict(res.all())


async def _supplier_names(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    from contractors.models import Contractor
    res = await db.execute(select(Contractor.id, Contractor.name).where(Contractor.id.in_(ids)))
    return dict(res.all())


# ── Umowy archiwum ───────────────────────────────────────────────────────────

async def list_archive_contracts(
    db: AsyncSession,
    *,
    search: str | None = None,
    contractor_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    contract_type: str | None = None,
    city: str | None = None,
    article_id: int | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[ArchiveContractListItem], int]:
    stmt = select(ArchiveContract)
    if search:
        stmt = stmt.where(
            (ArchiveContract.number.ilike(f"%{search}%"))
            | (ArchiveContract.contractor_name.ilike(f"%{search}%"))
        )
    if contractor_id:
        stmt = stmt.where(ArchiveContract.contractor_id == contractor_id)
    if date_from:
        stmt = stmt.where(ArchiveContract.date_from >= date_from)
    if date_to:
        stmt = stmt.where(ArchiveContract.date_to <= date_to)
    if contract_type:
        stmt = stmt.where(ArchiveContract.contract_type == contract_type)
    if city:
        # Exact match (case-insensitive) — drill-down Miasta → umowy
        stmt = stmt.where(ArchiveContract.city == city)
    if article_id:
        # Umowy zawierające pozycję z tym article_id — drill-down Top maszyny → umowy
        stmt = stmt.where(
            ArchiveContract.id.in_(
                select(ArchiveContractPosition.contract_id)
                .where(ArchiveContractPosition.article_id == article_id)
            )
        )

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

    stmt = (
        stmt.order_by(ArchiveContract.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rows = (await db.execute(stmt)).scalars().all()

    # Bulk load pozycji z warunkami dla umów na tej stronie — obliczenie revenue_estimate
    contract_ids = [c.id for c in rows]
    revenue_by_contract: dict[int, Decimal] = defaultdict(lambda: Decimal("0.00"))
    if contract_ids:
        pos_stmt = (
            select(ArchiveContractPosition)
            .where(ArchiveContractPosition.contract_id.in_(contract_ids))
            .options(selectinload(ArchiveContractPosition.conditions))
        )
        positions = (await db.execute(pos_stmt)).scalars().all()
        for p in positions:
            revenue_by_contract[p.contract_id] += _estimate_position_value(p)

    items: list[ArchiveContractListItem] = []
    for c in rows:
        duration = (c.date_to - c.date_from).days if c.date_from and c.date_to else None
        items.append(
            ArchiveContractListItem(
                id=c.id,
                contractor_id=c.contractor_id,
                contractor_name=c.contractor_name,
                number=c.number,
                contract_type=c.contract_type,
                type_label="Umowa najmu" if c.contract_type == "S" else "Umowa uslugi",
                delivery_address=c.delivery_address,
                postal_code=c.postal_code,
                city=c.city,
                date_from=c.date_from,
                date_to=c.date_to,
                prepayment_amount=c.prepayment_amount,
                notes=c.notes,
                email=c.email,
                contact_person1=c.contact_person1,
                contact_phone1=c.contact_phone1,
                phone=c.phone,
                is_settled=c.is_settled,
                settled_at=c.settled_at,
                position_count=c.position_count,
                duration_days=duration,
                revenue_estimate=revenue_by_contract.get(c.id, Decimal("0.00")),
                created_at=c.created_at,
            )
        )
    return items, total


async def get_archive_contract(db: AsyncSession, contract_id: int) -> ArchiveContract:
    res = await db.execute(
        select(ArchiveContract)
        .options(
            selectinload(ArchiveContract.positions).selectinload(ArchiveContractPosition.conditions),
            selectinload(ArchiveContract.service_fees),
            selectinload(ArchiveContract.settlements),
        )
        .where(ArchiveContract.id == contract_id)
    )
    c = res.scalar_one_or_none()
    if not c:
        raise not_found("Umowa archiwum")
    return c


# ── Artykuly archiwum ────────────────────────────────────────────────────────

async def list_archive_articles(
    db: AsyncSession,
    *,
    search: str | None = None,
    category_id: int | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[ArchiveArticle], int]:
    stmt = select(ArchiveArticle)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            (ArchiveArticle.name.ilike(like))
            | (ArchiveArticle.internal_number.ilike(like))
            | (ArchiveArticle.registration_no.ilike(like))
        )
    if category_id:
        stmt = stmt.where(ArchiveArticle.category_id == category_id)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

    stmt = stmt.order_by(ArchiveArticle.name).offset((page - 1) * per_page).limit(per_page)
    items = (await db.execute(stmt)).scalars().all()
    return list(items), total


async def get_archive_article(db: AsyncSession, article_id: int) -> ArchiveArticle:
    res = await db.execute(select(ArchiveArticle).where(ArchiveArticle.id == article_id))
    a = res.scalar_one_or_none()
    if not a:
        raise not_found("Artykul archiwum")
    return a


async def update_archive_article_category(
    db: AsyncSession, article_id: int, payload: ArchiveArticleCategoryUpdate
) -> ArchiveArticle:
    article = await get_archive_article(db, article_id)
    new_cat_id = payload.category_id
    if new_cat_id is not None:
        cat = await db.execute(
            select(ArchiveCategory).where(ArchiveCategory.id == new_cat_id)
        )
        if cat.scalar_one_or_none() is None:
            raise not_found("Kategoria archiwum")
    article.category_id = new_cat_id
    await db.commit()
    await db.refresh(article)
    return article


# ── Kategorie archiwum (CRUD) ────────────────────────────────────────────────

async def list_archive_categories(db: AsyncSession) -> list[ArchiveCategory]:
    res = await db.execute(select(ArchiveCategory).order_by(ArchiveCategory.name))
    return list(res.scalars().all())


async def list_archive_categories_tree(db: AsyncSession) -> list[ArchiveCategory]:
    res = await db.execute(
        select(ArchiveCategory)
        .where(ArchiveCategory.parent_id == None)  # noqa: E711
        .options(
            selectinload(ArchiveCategory.children)
            .selectinload(ArchiveCategory.children)
            .selectinload(ArchiveCategory.children)
        )
        .order_by(ArchiveCategory.name)
    )
    return list(res.scalars().all())


async def create_archive_category(
    db: AsyncSession, data: ArchiveCategoryCreate
) -> ArchiveCategory:
    payload = data.model_dump()
    payload["name"] = _normalize_category_name(payload.get("name", ""))
    if not payload["name"]:
        raise conflict("Nazwa kategorii nie moze byc pusta")
    new_key = _normalize_category_key(payload["name"])
    existing = await db.execute(
        select(ArchiveCategory).where(ArchiveCategory.parent_id == payload.get("parent_id"))
    )
    for cat in existing.scalars().all():
        if _normalize_category_key(cat.name) == new_key:
            raise conflict(f"Kategoria '{cat.name}' juz istnieje w tej hierarchii")
    cat = ArchiveCategory(**payload)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def update_archive_category(
    db: AsyncSession, cat_id: int, data: ArchiveCategoryCreate
) -> ArchiveCategory:
    res = await db.execute(select(ArchiveCategory).where(ArchiveCategory.id == cat_id))
    cat = res.scalar_one_or_none()
    if not cat:
        raise not_found("Kategoria archiwum")
    payload = data.model_dump()
    payload["name"] = _normalize_category_name(payload.get("name", ""))
    if not payload["name"]:
        raise conflict("Nazwa kategorii nie moze byc pusta")
    new_key = _normalize_category_key(payload["name"])
    new_parent = payload.get("parent_id")
    dup_check = await db.execute(
        select(ArchiveCategory).where(
            ArchiveCategory.parent_id == new_parent,
            ArchiveCategory.id != cat_id,
        )
    )
    for other in dup_check.scalars().all():
        if _normalize_category_key(other.name) == new_key:
            raise conflict(f"Kategoria '{other.name}' juz istnieje w tej hierarchii")
    for field, value in payload.items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_archive_category(db: AsyncSession, cat_id: int) -> None:
    res = await db.execute(select(ArchiveCategory).where(ArchiveCategory.id == cat_id))
    cat = res.scalar_one_or_none()
    if not cat:
        raise not_found("Kategoria archiwum")
    children = await db.execute(
        select(ArchiveCategory.id).where(ArchiveCategory.parent_id == cat_id).limit(1)
    )
    if children.scalar_one_or_none() is not None:
        raise conflict("Kategoria ma podkategorie - usun je najpierw")
    articles_count = await db.execute(
        select(func.count())
        .select_from(ArchiveArticle)
        .where(ArchiveArticle.category_id == cat_id)
    )
    if (articles_count.scalar_one() or 0) > 0:
        raise conflict("Kategoria jest uzywana przez artykuly archiwum i nie moze byc usunieta")
    try:
        await db.execute(delete(ArchiveCategory).where(ArchiveCategory.id == cat_id))
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise conflict("Kategoria jest uzywana i nie moze byc usunieta")


# ── Stats archiwum ───────────────────────────────────────────────────────────
# Szacunek przychodu = SUM(cennik_pozycji * dni) per pozycja archiwum.
# Cennik = unit_price jesli ustawiony, w przeciwnym razie calculate_position_value
# (kaskadowy algorytm z stats.calc) na warunkach pozycji.

async def _fetch_positions_with_conds(
    db: AsyncSession,
    date_from: date | None,
    date_to: date | None,
):
    """Zwraca listę (position, contract, article, conditions[]) dla archiwum."""
    stmt = (
        select(ArchiveContractPosition)
        .join(ArchiveContract, ArchiveContract.id == ArchiveContractPosition.contract_id)
        .options(
            selectinload(ArchiveContractPosition.conditions),
            selectinload(ArchiveContractPosition.article),
            selectinload(ArchiveContractPosition.contract),
        )
    )
    if date_from:
        stmt = stmt.where(ArchiveContract.date_from >= date_from)
    if date_to:
        stmt = stmt.where(ArchiveContract.date_to <= date_to)
    res = await db.execute(stmt)
    return list(res.scalars().all())


def _estimate_position_value(pos: ArchiveContractPosition) -> Decimal:
    days = pos.rental_days or 0
    qty = pos.quantity or 1
    if pos.unit_price is not None and pos.unit_price > 0:
        return Decimal(str(pos.unit_price)) * Decimal(str(days)) * Decimal(str(qty))
    conds = [
        {
            "rate1": c.rate1,
            "rate2": c.rate2,
            "period_count": c.period_count,
            "minimum": c.minimum,
            "rate_type_id": c.rate_type_id,
        }
        for c in (pos.conditions or [])
    ]
    return calculate_position_value(
        rental_days=days,
        billing_frequency=pos.billing_frequency,
        unit_price=pos.unit_price,
        quantity=qty,
        conditions=conds,
    )


async def get_archive_stats_summary(
    db: AsyncSession, date_from: date | None = None, date_to: date | None = None
):
    from archive.schemas import ArchiveStatsSummary

    positions = await _fetch_positions_with_conds(db, date_from, date_to)
    revenue = sum((_estimate_position_value(p) for p in positions), Decimal("0.00"))
    contracts_count = len({p.contract_id for p in positions})

    return ArchiveStatsSummary(
        date_from=date_from,
        date_to=date_to,
        contracts_count=contracts_count,
        positions_count=len(positions),
        revenue_estimate=revenue,
    )


async def get_archive_top_machines(
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 10,
):
    from archive.schemas import ArchiveTopMachineItem

    positions = await _fetch_positions_with_conds(db, date_from, date_to)
    agg: dict[int, dict] = defaultdict(
        lambda: {
            "article_name": "",
            "internal_number": None,
            "contracts": set(),
            "rented_days": 0,
            "revenue_estimate": Decimal("0.00"),
        }
    )
    for p in positions:
        if not p.article or p.article.is_service:
            continue
        aid = p.article_id
        agg[aid]["article_name"] = p.article.name
        agg[aid]["internal_number"] = p.article.internal_number
        agg[aid]["contracts"].add(p.contract_id)
        agg[aid]["rented_days"] += max(p.rental_days or 0, 0)
        agg[aid]["revenue_estimate"] += _estimate_position_value(p)

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue_estimate"], reverse=True)[:limit]
    return [
        ArchiveTopMachineItem(
            article_id=aid,
            article_name=d["article_name"],
            internal_number=d["internal_number"],
            contracts_count=len(d["contracts"]),
            rented_days=d["rented_days"],
            revenue_estimate=d["revenue_estimate"],
        )
        for aid, d in sorted_items
    ]


async def get_archive_stats_by_category(
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
):
    from archive.schemas import ArchiveCategoryStatItem

    positions = await _fetch_positions_with_conds(db, date_from, date_to)
    agg: dict[tuple[int | None, str], dict] = defaultdict(
        lambda: {"contracts": set(), "positions_count": 0, "revenue_estimate": Decimal("0.00")}
    )
    for p in positions:
        cat_id = p.article.category_id if p.article else None
        cat_name = (
            p.article.category.name
            if p.article and p.article.category
            else (p.article.category_main if p.article else None) or "(bez kategorii)"
        )
        key = (cat_id, cat_name)
        agg[key]["contracts"].add(p.contract_id)
        agg[key]["positions_count"] += 1
        agg[key]["revenue_estimate"] += _estimate_position_value(p)

    items = [
        ArchiveCategoryStatItem(
            category_id=cat_id,
            category_name=cat_name,
            contracts_count=len(d["contracts"]),
            positions_count=d["positions_count"],
            revenue_estimate=d["revenue_estimate"],
        )
        for (cat_id, cat_name), d in agg.items()
    ]
    items.sort(key=lambda x: x.revenue_estimate, reverse=True)
    return items


async def get_archive_machine_roi(
    db: AsyncSession,
    article_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
):
    from archive.schemas import ArchiveMachineRoiResponse

    article = await get_archive_article(db, article_id)
    positions = await _fetch_positions_with_conds(db, date_from, date_to)
    relevant = [p for p in positions if p.article_id == article_id]
    revenue = sum((_estimate_position_value(p) for p in relevant), Decimal("0.00"))
    days = clamp_days(sum((p.rental_days or 0) for p in relevant))
    cnt = len({p.contract_id for p in relevant})

    roi_pct = _compute_roi_pct(revenue, article.replacement_value)

    return ArchiveMachineRoiResponse(
        article_id=article.id,
        name=article.name,
        internal_number=article.internal_number,
        replacement_value=article.replacement_value,
        revenue_estimate=revenue,
        contracts_count=cnt,
        rented_days=days,
        roi_pct=roi_pct,
    )


async def get_archive_stats_by_city(
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 20,
):
    """Statystyki szacunkowe po miastach (z archive_contracts.city)."""
    from archive.schemas import ArchiveCityStatItem

    positions = await _fetch_positions_with_conds(db, date_from, date_to)
    agg: dict[str, dict] = defaultdict(
        lambda: {
            "contracts": set(),
            "positions_count": 0,
            "revenue_estimate": Decimal("0.00"),
            "postal_codes": set(),
        }
    )
    for p in positions:
        contract = p.contract
        if not contract or not contract.city:
            continue
        city = contract.city.strip()
        if not city:
            continue
        agg[city]["contracts"].add(p.contract_id)
        agg[city]["positions_count"] += 1
        agg[city]["revenue_estimate"] += _estimate_position_value(p)
        if contract.postal_code:
            agg[city]["postal_codes"].add(contract.postal_code)

    sorted_items = sorted(agg.items(), key=lambda x: x[1]["revenue_estimate"], reverse=True)[:limit]
    return [
        ArchiveCityStatItem(
            city=city,
            contracts_count=len(d["contracts"]),
            positions_count=d["positions_count"],
            revenue_estimate=d["revenue_estimate"],
            postal_codes_count=len(d["postal_codes"]),
        )
        for city, d in sorted_items
    ]
