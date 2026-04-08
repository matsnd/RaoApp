import re
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import aliased

from auth.dependencies import get_current_user
from auth.models import User
from database import get_db
from contracts.models import Contract, ContractPosition, PositionCondition
from articles.models import Article
from contractors.models import Contractor
from categories.models import Category

router = APIRouter(prefix="/explorer", tags=["explorer"])


def extract_city(address: str) -> str:
    """Extract city name from a Polish delivery address."""
    if not address:
        return "Nieznane"
    address = address.strip()

    # 1. Postal code XX-XXX followed by city name
    m = re.search(r'\d{2}-\d{3}\s+([A-Z\u0141\u015a\u0179\u017b\u0106\u0143\u00d3\u0118\u0104][a-z\u0142\u015b\u017a\u017c\u0107\u0144\u00f3\u0119\u0105A-Z\u0141\u015a\u0179\u017b\u0106\u0143\u00d3\u0118\u0104\s-]+)', address)
    if m:
        city = m.group(1).strip()
        city = re.split(r'\s*[,;]\s*', city)[0].strip()
        if city:
            return city

    # 2. City before "ul." / "al." / "pl."
    m = re.search(r'^(.+?)\s+(?:ul\.|al\.|pl\.)', address, re.IGNORECASE)
    if m:
        city = m.group(1).strip().rstrip(',;')
        city = re.sub(r'\s+\d+.*$', '', city).strip()
        if city and len(city) > 1:
            return city

    # 3. Split by , or ; and find city-like part (last non-street part)
    parts = re.split(r'[;,]', address)
    for part in reversed(parts):
        part = part.strip()
        part = re.sub(r'\(.*?\)', '', part).strip()
        if re.match(r'^(ul\.|al\.|pl\.)', part, re.IGNORECASE):
            continue
        if re.match(r'^\d', part):
            continue
        clean = re.sub(r'\d+', '', part).strip()
        clean = re.sub(r'\s+', ' ', clean).strip()
        if clean and len(clean) > 1 and not re.match(r'^(ul |al |pl )', clean, re.IGNORECASE):
            return clean

    return address[:50]


@router.options("/{path:path}")
async def explorer_preflight(path: str):
    """Handle CORS preflight requests for all explorer endpoints."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        },
    )


@router.get("/search")
async def explorer_search(
    q: Optional[str] = Query(None, description="Search query"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    contractor_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Universal search across machines, services, contractors, and locations.
    Returns mixed results with type indicator.
    """
    results = []

    # Subquery: revenue per position from position_conditions
    revenue_subq = (
        select(
            PositionCondition.position_id,
            func.sum(
                func.coalesce(PositionCondition.rate1, 0) * func.coalesce(PositionCondition.period_count, 1)
            ).label("pos_revenue"),
        )
        .group_by(PositionCondition.position_id)
        .subquery()
    )

    # Base query for contract positions with all joins
    query = (
        select(
            ContractPosition.id,
            Article.id.label("article_id"),
            Article.name.label("article_name"),
            Article.internal_number,
            Article.is_service,
            Category.name.label("category_name"),
            Contract.number.label("contract_number"),
            Contract.date_from,
            Contract.date_to,
            Contractor.name.label("contractor_name"),
            Contract.delivery_address,
            func.coalesce(revenue_subq.c.pos_revenue, 0).label("revenue"),
        )
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .join(Article, ContractPosition.article_id == Article.id)
        .outerjoin(Category, Article.category_id == Category.id)
        .outerjoin(Contractor, Contract.contractor_id == Contractor.id)
        .outerjoin(revenue_subq, revenue_subq.c.position_id == ContractPosition.id)
    )
    
    # Apply filters
    conditions = []
    
    if date_from:
        conditions.append(Contract.date_from >= date_from)
    if date_to:
        conditions.append(Contract.date_to <= date_to)
    if contractor_id:
        conditions.append(Contract.contractor_id == contractor_id)
    if city:
        conditions.append(Contract.delivery_address.like(f"%{city}%"))
    if category:
        conditions.append(Category.name == category)
    
    if q:
        # MySQL uses case-insensitive collation by default, so LIKE is case-insensitive
        search_filter = or_(
            Article.name.like(f"%{q}%"),
            Article.internal_number.like(f"%{q}%"),
            Contractor.name.like(f"%{q}%"),
            Contract.number.like(f"%{q}%"),
            Contract.delivery_address.like(f"%{q}%"),
        )
        conditions.append(search_filter)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(Contract.date_from.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    rows = result.mappings().all()
    
    # Format results with type indicator
    for row in rows:
        item_type = "🏗️"  # Machine default
        if row.is_service:
            item_type = "🛠️"  # Service
        
        results.append({
            "type": item_type,
            "type_label": "Maszyna" if item_type == "🏗️" else "Usługa",
            "id": row.id,
            "article_id": row.article_id,
            "name": f"{row.article_name} ({row.internal_number})" if row.internal_number else row.article_name,
            "internal_number": row.internal_number,
            "contract_number": row.contract_number,
            "contractor_name": row.contractor_name,
            "date": row.date_from.isoformat() if row.date_from else None,
            "city": row.delivery_address,
            "amount": float(row.revenue) if row.revenue else 0,
        })
    
    # Get summary metrics
    summary_query = (
        select(
            func.count(ContractPosition.id).label("total_count"),
            func.sum(func.coalesce(revenue_subq.c.pos_revenue, 0)).label("total_revenue"),
        )
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .join(Article, ContractPosition.article_id == Article.id)
        .outerjoin(Category, Article.category_id == Category.id)
        .outerjoin(Contractor, Contract.contractor_id == Contractor.id)
        .outerjoin(revenue_subq, revenue_subq.c.position_id == ContractPosition.id)
    )
    
    if conditions:
        summary_query = summary_query.where(and_(*conditions))
    
    summary_result = await db.execute(summary_query)
    summary = summary_result.mappings().first()
    
    return {
        "items": results,
        "total": len(results),
        "summary": {
            "count": summary.total_count if summary else 0,
            "revenue": float(summary.total_revenue) if summary and summary.total_revenue else 0,
        },
        "offset": offset,
        "limit": limit,
    }


@router.get("/machines/{article_id}")
async def get_machine_details(
    article_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get detailed metrics for a specific machine.
    """
    # Get article details
    article_result = await db.execute(
        select(Article, Category.name.label("category_name"))
        .outerjoin(Category, Article.category_id == Category.id)
        .where(Article.id == article_id)
    )
    article_row = article_result.mappings().first()
    
    if not article_row:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    article = article_row.Article
    
    # Build date filter
    date_conditions = []
    if date_from:
        date_conditions.append(Contract.date_from >= date_from)
    if date_to:
        date_conditions.append(Contract.date_to <= date_to)
    
    # Subquery: revenue per position from position_conditions
    rev_subq = (
        select(
            PositionCondition.position_id,
            func.sum(
                func.coalesce(PositionCondition.rate1, 0) * func.coalesce(PositionCondition.period_count, 1)
            ).label("pos_revenue"),
        )
        .group_by(PositionCondition.position_id)
        .subquery()
    )

    # Get rental history
    history_query = (
        select(
            Contract.id,
            Contract.number,
            Contract.date_from,
            Contract.date_to,
            Contractor.name.label("contractor_name"),
            func.coalesce(rev_subq.c.pos_revenue, 0).label("revenue"),
        )
        .select_from(ContractPosition)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .outerjoin(Contractor, Contract.contractor_id == Contractor.id)
        .outerjoin(rev_subq, rev_subq.c.position_id == ContractPosition.id)
        .where(ContractPosition.article_id == article_id)
        .order_by(Contract.date_from.desc())
    )
    
    if date_conditions:
        history_query = history_query.where(and_(*date_conditions))
    
    history_result = await db.execute(history_query)
    history_rows = history_result.mappings().all()
    
    # Calculate metrics
    total_revenue = 0
    total_days = 0
    rental_count = len(history_rows)
    
    rentals = []
    for row in history_rows:
        days = 0
        if row.date_from and row.date_to:
            days = (row.date_to - row.date_from).days + 1
        
        revenue = float(row.revenue) if row.revenue else 0
        total_revenue += revenue
        total_days += days
        
        rentals.append({
            "contract_id": row.id,
            "contract_number": row.number,
            "date_from": row.date_from.isoformat() if row.date_from else None,
            "date_to": row.date_to.isoformat() if row.date_to else None,
            "days": days,
            "contractor_name": row.contractor_name,
            "revenue": revenue,
        })
    
    avg_daily = total_revenue / total_days if total_days > 0 else 0
    
    # Calculate utilization (requires period to be specified)
    utilization_pct = None
    if date_from and date_to:
        period_days = (date_to - date_from).days + 1
        utilization_pct = round((total_days / period_days) * 100, 1) if period_days > 0 else 0
    
    return {
        "machine": {
            "id": article.id,
            "name": article.name,
            "internal_number": article.internal_number,
            "category": article_row.category_name,
        },
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
        "metrics": {
            "total_revenue": round(total_revenue, 2),
            "total_days": total_days,
            "rental_count": rental_count,
            "avg_daily_revenue": round(avg_daily, 2),
            "utilization_percentage": utilization_pct,
        },
        "rentals": rentals,
    }


@router.get("/services")
async def get_services_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get summary of additional services (transport, cleaning, etc.).
    """
    # Subquery: revenue per position from position_conditions
    svc_rev_subq = (
        select(
            PositionCondition.position_id,
            func.sum(
                func.coalesce(PositionCondition.rate1, 0) * func.coalesce(PositionCondition.period_count, 1)
            ).label("pos_revenue"),
        )
        .group_by(PositionCondition.position_id)
        .subquery()
    )

    # Base query for service positions
    query = (
        select(
            Article.id,
            Article.name,
            func.count(ContractPosition.id).label("times_billed"),
            func.sum(func.coalesce(svc_rev_subq.c.pos_revenue, 0)).label("total_revenue"),
        )
        .join(ContractPosition, ContractPosition.article_id == Article.id)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .outerjoin(svc_rev_subq, svc_rev_subq.c.position_id == ContractPosition.id)
        .where(Article.is_service == True)
        .group_by(Article.id, Article.name)
        .order_by(func.sum(func.coalesce(svc_rev_subq.c.pos_revenue, 0)).desc())
    )
    
    # Apply date filters
    if date_from:
        query = query.where(Contract.date_from >= date_from)
    if date_to:
        query = query.where(Contract.date_to <= date_to)
    if service_type:
        query = query.where(Article.name.like(f"%{service_type}%"))
    
    result = await db.execute(query)
    rows = result.mappings().all()
    
    # Calculate total for percentages
    total_revenue = sum(float(row.total_revenue) for row in rows)
    
    services = []
    for row in rows:
        revenue = float(row.total_revenue)
        services.append({
            "article_id": row.id,
            "service_name": row.name,
            "times_billed": row.times_billed,
            "total_revenue": round(revenue, 2),
            "percentage": round((revenue / total_revenue) * 100, 1) if total_revenue > 0 else 0,
        })
    
    return {
        "services": services,
        "total_revenue": round(total_revenue, 2),
        "count": len(services),
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
    }


@router.get("/locations")
async def get_locations_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get rental summary by location (city extracted from delivery_address).
    """
    query = (
        select(
            Contract.delivery_address,
            func.count(Contract.id).label("rentals_count"),
            func.sum(
                func.coalesce(PositionCondition.rate1, 0) * func.coalesce(PositionCondition.period_count, 1)
            ).label("total_revenue"),
        )
        .join(ContractPosition, ContractPosition.contract_id == Contract.id)
        .outerjoin(PositionCondition, PositionCondition.position_id == ContractPosition.id)
        .where(Contract.delivery_address.isnot(None))
        .where(Contract.delivery_address != "")
        .group_by(Contract.delivery_address)
    )

    if date_from:
        query = query.where(Contract.date_from >= date_from)
    if date_to:
        query = query.where(Contract.date_to <= date_to)

    result = await db.execute(query)
    rows = result.mappings().all()

    # Extract cities from addresses and re-aggregate
    city_data: dict = {}
    for row in rows:
        city = extract_city(row.delivery_address)
        if city not in city_data:
            city_data[city] = {"rentals_count": 0, "total_revenue": 0.0}
        city_data[city]["rentals_count"] += row.rentals_count
        city_data[city]["total_revenue"] += float(row.total_revenue) if row.total_revenue else 0

    sorted_cities = sorted(city_data.items(), key=lambda x: x[1]["rentals_count"], reverse=True)[:limit]

    locations = []
    for i, (city, data) in enumerate(sorted_cities):
        locations.append({
            "rank": i + 1,
            "city": city,
            "rentals_count": data["rentals_count"],
            "total_revenue": round(data["total_revenue"], 2),
        })

    return {
        "locations": locations,
        "count": len(locations),
        "period": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        },
    }
