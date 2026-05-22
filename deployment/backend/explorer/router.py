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
    """Extract city name from a Polish delivery address with enhanced logic."""
    if not address:
        return "Nieznane"
    address = address.strip()

    # Common Polish city names for better matching
    common_cities = {
        'warszawa', 'kraków', 'łódź', 'wrocław', 'poznań', 'gdańsk', 'szczecin', 'bydgoszcz',
        'lublin', 'katowice', 'białystok', 'gdynia', 'częstochowa', 'radom', 'sosnowiec',
        'toruń', 'kielce', 'gliwice', 'zabrze', 'bytom', 'rzeszów', 'olsztyn', 'bielsko-biała',
        'ruda śląska', 'rybnik', 'tarnów', 'dąbrowa górnicza', 'płock', 'opole', 'elbląg',
        'gorzów wielkopolski', 'włocławek', 'zielona góra', 'legnica', 'kalisz', 'grudziądz',
        'tarnowskie góry', 'nowy sącz', 'konin', 'piła', 'radomsko', 'suwałki', 'koszalin',
        'jelenia góra', 'słupsk', 'przemyśl', 'stargard', 'wałbrzych', 'włocławek'
    }

    def normalize_city(city: str) -> str:
        """Normalize city name for consistency."""
        if not city:
            return ""
        
        # Remove common prefixes/suffixes
        city = re.sub(r'^(m\.|gm\.|gmina|miasto)\s+', '', city, flags=re.IGNORECASE)
        
        # Handle special cases
        city = city.replace('Warszawa-', 'Warszawa ')
        city = city.replace('-Warszawa', ' Warszawa')
        
        # Clean up extra spaces and punctuation
        city = re.sub(r'\s+', ' ', city).strip()
        city = city.rstrip(',.;')
        
        # Capitalize properly (first letter uppercase, rest lowercase)
        if city.lower() in common_cities:
            return city.title()
        
        # For multi-word cities, capitalize each word
        return ' '.join(word.capitalize() for word in city.split())

    # 0. Priority: Look for known city names first (most reliable)
    address_lower = address.lower()
    for city in sorted(common_cities, key=len, reverse=True):  # Check longer names first
        if city in address_lower:
            return city.title()

    # 1. Postal code XX-XXX followed by city name (most reliable)
    m = re.search(r'\d{2}-\d{3}\s+([A-ZĄŁŃÓŚŻŹĆ][a-ząłęóśżźć\s-]+)', address)
    if m:
        city = normalize_city(m.group(1))
        if city:
            return city

    # 2. City at the beginning before street indicators
    m = re.search(r'^([A-ZĄŁŃÓŚŻŹĆ][a-ząłęóśżźć\s-]+?)\s+(?:ul\.|al\.|pl\.|os\.|dw\.|skw\.)', address, re.IGNORECASE)
    if m:
        city = normalize_city(m.group(1))
        if city and len(city) > 1:
            return city

    # 3. Split by common separators and analyze parts
    parts = re.split(r'[,;]', address)
    for i, part in enumerate(reversed(parts)):
        part = part.strip()
        
        # Skip if it's clearly a street address
        if re.match(r'^(ul\.|al\.|pl\.|os\.|dw\.|skw\.|budynek|lok|mieszkanie)', part, re.IGNORECASE):
            continue
        if re.match(r'^\d+[A-Z]?', part):  # House numbers
            continue
        if re.search(r'\d+/\d+', part):  # Flat numbers
            continue
        
        # Skip common street patterns
        if re.search(r'\b(ul|al|pl|os|dw|skw)\b', part, re.IGNORECASE):
            continue
        
        # Remove parentheses content and numbers
        part = re.sub(r'\(.*?\)', '', part)
        part = re.sub(r'\b\d+\b', '', part)
        part = re.sub(r'\s+', ' ', part).strip()
        
        if len(part) < 2:
            continue
            
        # Check if it looks like a city name
        if re.match(r'^[A-ZĄŁŃÓŚŻŹĆ]', part):
            city = normalize_city(part)
            if city:
                return city

    # 4. Final fallback: first reasonable word
    words = address.split()
    for word in words:
        word = re.sub(r'[^\w\s-]', '', word)
        if len(word) > 2 and not re.match(r'^\d', word):
            return normalize_city(word)

    return "Nieznane"


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
        .where(Article.is_archival == False)  # RAO-P1-028: tylko niearchiwalne
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
        conditions.append(or_(Contract.city.like(f"%{city}%"), Contract.delivery_address.like(f"%{city}%")))  # RAO-P1-028
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
        .where(Article.is_archival == False)  # RAO-P1-028: tylko niearchiwalne
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
        .where(Article.is_archival == False)  # RAO-P1-028: tylko niearchiwalne
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
    Get rental summary by location (Contract.city — RAO-P1-028: grouped by city, not raw address).
    """
    query = (
        select(
            Contract.city,
            func.count(Contract.id).label("rentals_count"),
            func.sum(
                func.coalesce(PositionCondition.rate1, 0) * func.coalesce(PositionCondition.period_count, 1)
            ).label("total_revenue"),
        )
        .join(ContractPosition, ContractPosition.contract_id == Contract.id)
        .outerjoin(PositionCondition, PositionCondition.position_id == ContractPosition.id)
        .where(Contract.city.isnot(None))
        .where(Contract.city != "")
        .group_by(Contract.city)
    )

    if date_from:
        query = query.where(Contract.date_from >= date_from)
    if date_to:
        query = query.where(Contract.date_to <= date_to)

    result = await db.execute(query)
    rows = result.mappings().all()

    # Aggregate by city (already clean, no extract_city needed — RAO-P1-028)
    city_data: dict = {}
    for row in rows:
        city = row.city
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


@router.get("/services/{article_id}")
async def get_service_details(
    article_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get detailed metrics for a specific service."""
    # Revenue subquery
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

    # Get service details with revenue
    query = (
        select(
            Article.id,
            Article.name,
            func.count(ContractPosition.id).label("times_billed"),
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Article)
        .outerjoin(ContractPosition, Article.id == ContractPosition.article_id)
        .outerjoin(Contract, ContractPosition.contract_id == Contract.id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Article.id == article_id)
        .where(Article.is_service == True)
    )

    if date_from:
        query = query.where(Contract.date_from >= date_from)
    if date_to:
        query = query.where(Contract.date_to <= date_to)

    query = query.group_by(Article.id, Article.name)

    result = await db.execute(query)
    row = result.mappings().first()

    if not row:
        return {"error": "Service not found - no row", "debug": f"article_id={article_id}, date_from={date_from}, date_to={date_to}"}
    
    # Use dictionary-style access to avoid AttributeError
    if 'id' not in row or not row['id']:
        return {"error": "Service not found - no id", "debug": f"article_id={article_id}, row_keys={list(row.keys()) if row else 'none'}"}
    contractors_query = (
        select(
            Contractor.name.label("contractor_name"),
            func.count(Contract.id).label("contract_count"),
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Article)
        .join(ContractPosition, Article.id == ContractPosition.article_id)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .join(Contractor, Contract.contractor_id == Contractor.id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Article.id == article_id)
    )

    if date_from:
        contractors_query = contractors_query.where(Contract.date_from >= date_from)
    if date_to:
        contractors_query = contractors_query.where(Contract.date_to <= date_to)

    contractors_query = contractors_query.group_by(Contractor.name).order_by(func.sum(revenue_subq.c.pos_revenue).desc()).limit(5)

    contractors_result = await db.execute(contractors_query)
    top_contractors = [dict(row) for row in contractors_result.mappings().all()]

    # Get location breakdown - fetch raw addresses and extract city in Python
    location_query = (
        select(
            Contract.delivery_address,
            func.count(Contract.id).label("contract_count"),
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Article)
        .join(ContractPosition, Article.id == ContractPosition.article_id)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Article.id == article_id)
        .where(Contract.delivery_address != "")
    )

    if date_from:
        location_query = location_query.where(Contract.date_from >= date_from)
    if date_to:
        location_query = location_query.where(Contract.date_to <= date_to)

    location_query = location_query.group_by(Contract.delivery_address).order_by(func.sum(revenue_subq.c.pos_revenue).desc()).limit(20)

    location_result = await db.execute(location_query)
    raw_locations = location_result.mappings().all()
    
    # Save service row before we overwrite 'row' variable
    service_row = row
    
    # Aggregate by city in Python
    city_data = {}
    for row in raw_locations:
        city = extract_city(row.delivery_address)
        if city not in city_data:
            city_data[city] = {"contract_count": 0, "total_revenue": 0.0}
        city_data[city]["contract_count"] += row.contract_count
        city_data[city]["total_revenue"] += float(row.total_revenue) if row.total_revenue else 0
    
    sorted_cities = sorted(city_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:10]
    location_breakdown = [{"city": c, "contract_count": d["contract_count"], "total_revenue": d["total_revenue"]} for c, d in sorted_cities]

    try:
        return {
            "service": {
                "id": service_row['id'],
                "name": service_row['name'],
            },
            "metrics": {
                "times_billed": service_row['times_billed'] or 0,
                "total_revenue": float(service_row['total_revenue']) if service_row['total_revenue'] else 0,
            },
            "top_contractors": top_contractors,
            "location_breakdown": location_breakdown,
        }
    except (KeyError, AttributeError) as e:
        return {"error": f"Error accessing row data: {str(e)}", "debug": f"row_keys={list(service_row.keys())}"}


@router.get("/locations/{city}")
async def get_location_details(
    city: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get detailed metrics for a specific city/location."""
    # Revenue subquery
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

    # Get city summary - fetch raw data and filter in Python
    base_query = (
        select(
            Contract.id,
            Contract.delivery_address,
            Contract.contractor_id,
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Contract)
        .join(ContractPosition, Contract.id == ContractPosition.contract_id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Contract.delivery_address != "")
    )

    if date_from:
        base_query = base_query.where(Contract.date_from >= date_from)
    if date_to:
        base_query = base_query.where(Contract.date_to <= date_to)

    base_query = base_query.group_by(Contract.id, Contract.delivery_address, Contract.contractor_id)

    result = await db.execute(base_query)
    rows = result.mappings().all()
    
    # Filter by city in Python
    city_rows = [r for r in rows if extract_city(r.delivery_address) == city]
    
    if not city_rows:
        return {"error": "City not found"}
    
    contract_ids = set(r.id for r in rows if extract_city(r.delivery_address) == city)
    unique_contractors = len(set(r.contractor_id for r in city_rows if r.contractor_id))
    total_revenue = sum(float(r.total_revenue) for r in city_rows)
    contracts_count = len(city_rows)

    # Get top machines in this city
    machines_query = (
        select(
            Article.name,
            func.count(ContractPosition.id).label("rental_count"),
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Contract)
        .join(ContractPosition, Contract.id == ContractPosition.contract_id)
        .join(Article, ContractPosition.article_id == Article.id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Contract.delivery_address != "")
    )

    if date_from:
        machines_query = machines_query.where(Contract.date_from >= date_from)
    if date_to:
        machines_query = machines_query.where(Contract.date_to <= date_to)

    machines_query = machines_query.group_by(Article.name).order_by(func.count(ContractPosition.id).desc()).limit(10)

    machines_result = await db.execute(machines_query)
    all_machines = machines_result.mappings().all()
    # Filter by city in Python
    top_machines = []
    machine_data = {}
    for m in all_machines:
        # Get contracts for this machine
        machine_contracts_query = (
            select(Contract.delivery_address)
            .select_from(Contract)
            .join(ContractPosition, Contract.id == ContractPosition.contract_id)
            .where(ContractPosition.article_id == Article.id)
            .where(Contract.delivery_address != "")
        )
        if date_from:
            machine_contracts_query = machine_contracts_query.where(Contract.date_from >= date_from)
        if date_to:
            machine_contracts_query = machine_contracts_query.where(Contract.date_to <= date_to)
        
        mc_result = await db.execute(machine_contracts_query)
        mc_rows = mc_result.mappings().all()
        
        # Check if any contract is in our city
        in_city = any(extract_city(r.delivery_address) == city for r in mc_rows)
        if in_city:
            if m.name not in machine_data:
                machine_data[m.name] = {"rental_count": 0, "total_revenue": 0}
            machine_data[m.name]["rental_count"] += m.rental_count or 0
            machine_data[m.name]["total_revenue"] += float(m.total_revenue) if m.total_revenue else 0
    
    top_machines = [{"name": k, "rental_count": v["rental_count"], "total_revenue": v["total_revenue"]} for k, v in sorted(machine_data.items(), key=lambda x: x[1]["rental_count"], reverse=True)[:10]]

    # Get top contractors in this city
    contractors_query = (
        select(
            Contractor.name.label("contractor_name"),
            func.count(Contract.id).label("contract_count"),
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Contract)
        .join(Contractor, Contract.contractor_id == Contractor.id)
        .join(ContractPosition, Contract.id == ContractPosition.contract_id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Contract.delivery_address != "")
    )

    if date_from:
        contractors_query = contractors_query.where(Contract.date_from >= date_from)
    if date_to:
        contractors_query = contractors_query.where(Contract.date_to <= date_to)

    contractors_query = contractors_query.group_by(Contractor.name).order_by(func.sum(revenue_subq.c.pos_revenue).desc()).limit(5)

    contractors_result = await db.execute(contractors_query)
    all_contractors = contractors_result.mappings().all()
    # Filter contractors by city in Python
    contractor_data = {}
    for c in all_contractors:
        # Get contracts for this contractor
        contr_contracts_query = (
            select(Contract.delivery_address)
            .select_from(Contract)
            .where(Contract.contractor_id == Contractor.id)
            .where(Contract.delivery_address != "")
        )
        if date_from:
            contr_contracts_query = contr_contracts_query.where(Contract.date_from >= date_from)
        if date_to:
            contr_contracts_query = contr_contracts_query.where(Contract.date_to <= date_to)
        
        cc_result = await db.execute(contr_contracts_query)
        cc_rows = cc_result.mappings().all()
        
        in_city = any(extract_city(r.delivery_address) == city for r in cc_rows)
        if in_city:
            contractor_data[c.contractor_name] = {
                "contract_count": c.contract_count or 0,
                "total_revenue": float(c.total_revenue) if c.total_revenue else 0
            }
    
    top_contractors = [{"contractor_name": k, "contract_count": v["contract_count"], "total_revenue": v["total_revenue"]} for k, v in sorted(contractor_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:5]]

    # Get monthly trend - simplified, just return empty for now
    monthly_trend = []

    avg_per_contract = total_revenue / contracts_count if contracts_count else 0

    return {
        "city": city,
        "metrics": {
            "contracts_count": contracts_count,
            "unique_contractors": unique_contractors,
            "total_revenue": total_revenue,
            "avg_revenue_per_contract": round(avg_per_contract, 2),
        },
        "top_machines": top_machines,
        "top_contractors": top_contractors,
        "monthly_trend": monthly_trend,
    }
