from datetime import date
from decimal import Decimal
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
from integrations.models import PostalCode
from shared.revenue import compute_position_revenues  # RAO-P2-028: spójny przychód
from shared.locations import aggregate_by_pna, NO_PNA_BUCKET  # RAO-P2-028: agregacja PNA

router = APIRouter(prefix="/explorer", tags=["explorer"])


# RAO-P2-028: `extract_city` (legacy regex) USUNIĘTE.
# Wszystkie call-site'y przepięte na deterministyczne PNA (postal_code)
# z LEFT JOIN do `postal_codes` (city/woj/pow/gmina).


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
    Get rental summary by location (RAO-P2-028: aggregated by PNA + city
    with rollup po gmina/powiat/wojewodztwo z LEFT JOIN do postal_codes).

    Przychód liczony spójnym algorytmem kaskadowym (`shared.revenue`),
    NIE `rate1 * period_count` — naprawia rozjazd ze statystykami.
    """
    # RAO-P2-028: domyślne daty jak w stats/router.py (None → początek miesiąca / dziś)
    from stats.router import _default_dates
    df, dt = _default_dates(date_from, date_to)
    # Spójny przychód ze shared.revenue (kaskadowy algorytm jak w stats)
    all_pos = await compute_position_revenues(
        db, df, dt, exclude_archival=False  # uwzględnia archiwalne (statystyki historyczne)
    )
    items = await aggregate_by_pna(all_pos, db, limit=limit)

    locations = []
    for i, item in enumerate(items):
        locations.append({
            "rank": i + 1,
            "city": item.city,
            "postal_code": item.postal_code,
            "gmina": item.gmina,
            "powiat": item.powiat,
            "wojewodztwo": item.wojewodztwo,
            "rentals_count": item.rentals_count,
            "total_revenue": float(item.total_revenue),
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

    # Get location breakdown — RAO-P2-028: agregacja po PNA (deterministyczna),
    # NIE legacy regex po delivery_address. Filtrujemy po article_id przez pozycje.
    location_query = (
        select(
            Contract.id,
            Contract.city,
            Contract.postal_code,
            Contract.postal_code_id,
            func.coalesce(func.sum(revenue_subq.c.pos_revenue), 0).label("total_revenue"),
        )
        .select_from(Article)
        .join(ContractPosition, Article.id == ContractPosition.article_id)
        .join(Contract, ContractPosition.contract_id == Contract.id)
        .outerjoin(revenue_subq, ContractPosition.id == revenue_subq.c.position_id)
        .where(Article.id == article_id)
        .group_by(Contract.id, Contract.city, Contract.postal_code, Contract.postal_code_id)
    )

    if date_from:
        location_query = location_query.where(Contract.date_from >= date_from)
    if date_to:
        location_query = location_query.where(Contract.date_to <= date_to)

    location_result = await db.execute(location_query)
    raw_locations = location_result.all()

    # LEFT JOIN do postal_codes dla kanonicznego city/woj/pow/gmina
    pna_ids = {r[3] for r in raw_locations if r[3]}
    pna_dict: dict[int, dict] = {}
    if pna_ids:
        pc_q = await db.execute(
            select(
                PostalCode.id,
                PostalCode.postal_code,
                PostalCode.city,
                PostalCode.wojewodztwo,
                PostalCode.powiat,
                PostalCode.gmina,
            ).where(PostalCode.id.in_(pna_ids))
        )
        pna_dict = {
            r[0]: {
                "postal_code": r[1], "city": r[2], "wojewodztwo": r[3],
                "powiat": r[4], "gmina": r[5],
            }
            for r in pc_q.all()
        }

    # Save service row before we overwrite 'row' variable
    service_row = row

    # Aggregate by (postal_code, city) — NULL PNA → bucket NO_PNA_BUCKET
    loc_data: dict[tuple[str | None, str], dict] = {}
    for r in raw_locations:
        _cid, city, pna_str, pna_id, rev = r
        pna_ref = pna_dict.get(pna_id) if pna_id else None
        if pna_ref:
            postal_code = pna_ref["postal_code"]
            city = pna_ref["city"] or (city or "").strip() or NO_PNA_BUCKET
        else:
            postal_code = (pna_str or "").strip() or None
            city = (city or "").strip() or NO_PNA_BUCKET
        if not city:
            city = NO_PNA_BUCKET
        key = (postal_code, city)
        if key not in loc_data:
            loc_data[key] = {"city": city, "postal_code": postal_code, "contract_count": 0, "total_revenue": 0.0}
        loc_data[key]["contract_count"] += 1
        loc_data[key]["total_revenue"] += float(rev) if rev else 0

    sorted_loc = sorted(loc_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:10]
    location_breakdown = [
        {"city": d["city"], "postal_code": d["postal_code"],
         "contract_count": d["contract_count"], "total_revenue": d["total_revenue"]}
        for _, d in sorted_loc
    ]

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


@router.get("/locations/{postal_code}")
async def get_location_details(
    postal_code: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get detailed metrics for a specific location — RAO-P2-028.

    BC break: dawniej `/locations/{city}` (extract_city regex).
    Teraz `/locations/{postal_code}` — drill-down po PNA (deterministyczny).
    Bucket "(brak PNA)" oznacza umowy bez PNA (NULL/empty postal_code).
    """
    # RAO-P2-028: domyślne daty jak w stats/router.py (None → początek miesiąca / dziś)
    from stats.router import _default_dates
    df, dt = _default_dates(date_from, date_to)
    is_no_pna_bucket = postal_code == NO_PNA_BUCKET

    # Spójny przychód (kaskadowy algorytm ze shared.revenue)
    all_pos = await compute_position_revenues(
        db, df, dt, exclude_archival=False
    )
    if not all_pos:
        return {"error": "Location not found"}

    contract_ids_all = {p["contract_id"] for p in all_pos if p.get("contract_id")}

    # Pobierz contracts.city + postal_code + postal_code_id (FK)
    loc_q = await db.execute(
        select(
            Contract.id,
            Contract.city,
            Contract.postal_code,
            Contract.postal_code_id,
        ).where(Contract.id.in_(contract_ids_all))
    )
    contract_loc = {
        r[0]: {"city": r[1], "pna": r[2], "pna_id": r[3]}
        for r in loc_q.all()
    }

    # LEFT JOIN do postal_codes — mapuj postal_code_id → kanoniczny PNA string
    pna_ids = {v["pna_id"] for v in contract_loc.values() if v["pna_id"]}
    pna_dict: dict[int, str] = {}
    if pna_ids:
        pc_q = await db.execute(
            select(PostalCode.id, PostalCode.postal_code).where(PostalCode.id.in_(pna_ids))
        )
        pna_dict = {r[0]: r[1] for r in pc_q.all()}

    # Filtruj contracts należące do żądanego PNA
    matched_contract_ids: set[int] = set()
    canonical_city: str | None = None
    for cid, loc in contract_loc.items():
        pna_ref = pna_dict.get(loc["pna_id"]) if loc["pna_id"] else None
        if pna_ref:
            contract_pna = pna_ref
        else:
            contract_pna = (loc["pna"] or "").strip() or None

        if is_no_pna_bucket:
            if contract_pna is None:
                matched_contract_ids.add(cid)
        else:
            if contract_pna == postal_code:
                matched_contract_ids.add(cid)
                if canonical_city is None and loc["city"]:
                    canonical_city = loc["city"]

    if not matched_contract_ids:
        return {"error": "Location not found"}

    # Pozycje dla dopasowanych umów
    city_pos = [p for p in all_pos if p["contract_id"] in matched_contract_ids]

    # Agregaty
    unique_contractors = len({p["contractor_id"] for p in city_pos if p.get("contractor_id")})
    total_revenue = float(sum((p["revenue"] for p in city_pos), Decimal(0)))
    contracts_count = len(matched_contract_ids)

    # Top machines w tym PNA — agregacja per article_name
    machine_data: dict[str, dict] = {}
    for p in city_pos:
        name = p["article_name"] or "(bez nazwy)"
        if name not in machine_data:
            machine_data[name] = {"rental_count": 0, "total_revenue": 0.0}
        machine_data[name]["rental_count"] += 1
        machine_data[name]["total_revenue"] += float(p["revenue"])
    top_machines = [
        {"name": k, "rental_count": v["rental_count"], "total_revenue": v["total_revenue"]}
        for k, v in sorted(machine_data.items(), key=lambda x: x[1]["rental_count"], reverse=True)[:10]
    ]

    # Top contractors w tym PNA — agregacja per contractor_name
    contractor_data: dict[str, dict] = {}
    for p in city_pos:
        cname = p["contractor_name"] or "(nieznany kontrahent)"
        if cname not in contractor_data:
            contractor_data[cname] = {"contract_count": 0, "total_revenue": 0.0}
        contractor_data[cname]["contract_count"] += 1
        contractor_data[cname]["total_revenue"] += float(p["revenue"])
    top_contractors = [
        {"contractor_name": k, "contract_count": v["contract_count"], "total_revenue": v["total_revenue"]}
        for k, v in sorted(contractor_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:5]
    ]

    # Monthly trend — puste (zachowane dla kompatybilności odpowiedzi)
    monthly_trend = []

    avg_per_contract = total_revenue / contracts_count if contracts_count else 0

    return {
        "postal_code": postal_code,
        "city": canonical_city or NO_PNA_BUCKET,
        "metrics": {
            "contracts_count": contracts_count,
            "unique_contractors": unique_contractors,
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_contract": round(avg_per_contract, 2),
        },
        "top_machines": top_machines,
        "top_contractors": top_contractors,
        "monthly_trend": monthly_trend,
    }
