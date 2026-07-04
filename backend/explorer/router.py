from collections import defaultdict
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

    RAO-P2-031: Używa shared.revenue.compute_position_revenues (3 źródła przychodu)
    zamiast rate1 × period_count — eliminuje rozjazd 41% ze statystykami.
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

    # RAO-P2-031: Użyj shared.revenue zamiast rate1 × period_count
    # Pobierz wszystkie pozycje dla tego artykułu w okresie
    df = date_from or date(2000, 1, 1)
    dt = date_to or date(2100, 1, 1)
    from shared.revenue import compute_position_revenues
    all_positions = await compute_position_revenues(
        db, df, dt, exclude_archival=False
    )
    # Filtruj po article_id
    machine_positions = [p for p in all_positions if p["article_id"] == article_id]

    # Grupuj po contract_id (jeden wiersz historii per umowa)
    from collections import defaultdict
    by_contract = defaultdict(lambda: {
        "contract_id": None, "contract_number": None,
        "date_from": None, "date_to": None,
        "contractor_name": None, "revenue": 0, "days": 0,
        "revenue_source": None,
    })
    for p in machine_positions:
        c = by_contract[p["contract_id"]]
        c["contract_id"] = p["contract_id"]
        c["contract_number"] = p["contract_number"]
        c["date_from"] = p["date_from"]
        c["date_to"] = p["date_to"]
        c["contractor_name"] = p["contractor_name"]
        c["revenue"] += float(p["revenue"])
        c["days"] += p["clamped_days"]
        c["revenue_source"] = p["revenue_source"]

    # Sortuj po date_from desc
    rentals = []
    total_revenue = 0
    total_days = 0
    for cid, info in sorted(by_contract.items(),
                            key=lambda x: x[1]["date_from"] or date(2000, 1, 1),
                            reverse=True):
        days = info["days"]
        revenue = info["revenue"]
        total_revenue += revenue
        total_days += days
        rentals.append({
            "contract_id": info["contract_id"],
            "contract_number": info["contract_number"],
            "date_from": info["date_from"].isoformat() if info["date_from"] else None,
            "date_to": info["date_to"].isoformat() if info["date_to"] else None,
            "days": days,
            "contractor_name": info["contractor_name"],
            "revenue": round(revenue, 2),
            "revenue_source": info["revenue_source"],
        })

    rental_count = len(rentals)
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

    RAO-P2-031: Używa shared.revenue zamiast rate1 × period_count.
    """
    # RAO-P2-031: Użyj shared.revenue
    df = date_from or date(2000, 1, 1)
    dt = date_to or date(2100, 1, 1)
    from shared.revenue import compute_position_revenues
    all_positions = await compute_position_revenues(
        db, df, dt, service_filter=True, exclude_archival=False
    )
    # Filtruj po service_type (name LIKE)
    if service_type:
        all_positions = [p for p in all_positions
                         if p["article_name"] and service_type.lower() in p["article_name"].lower()]

    # Grupuj po article_id
    from collections import defaultdict
    by_article = defaultdict(lambda: {
        "article_id": None, "service_name": None,
        "times_billed": 0, "total_revenue": 0,
    })
    for p in all_positions:
        a = by_article[p["article_id"]]
        a["article_id"] = p["article_id"]
        a["service_name"] = p["article_name"]
        a["times_billed"] += 1
        a["total_revenue"] += float(p["revenue"])

    # Sortuj po revenue desc
    services_list = sorted(by_article.values(), key=lambda x: x["total_revenue"], reverse=True)
    total_revenue = sum(s["total_revenue"] for s in services_list)

    services = []
    for s in services_list:
        revenue = s["total_revenue"]
        services.append({
            "article_id": s["article_id"],
            "service_name": s["service_name"],
            "times_billed": s["times_billed"],
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
    group_by: str = Query("city", pattern="^(city|pna)$",
                          description="Grupowanie: 'city' (1 wiersz per miasto, domyślnie) lub 'pna' (1 wiersz per PNA)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get rental summary by location (RAO-P2-028/069).

    - group_by='city' (domyślnie, RAO-P2-069): 1 wiersz per miasto — sumuje
      wszystkie PNA w tym mieście. Warszawa (3978 PNA) → 1 wiersz.
    - group_by='pna' (legacy RAO-P2-028): 1 wiersz per PNA — rozbicie miasta
      na kody pocztowe.

    Rollup po gmina/powiat/wojewodztwo z LEFT JOIN do postal_codes.
    Przychód liczony spójnym algorytmem kaskadowym (`shared.revenue`).
    """
    # RAO-P2-028: domyślne daty jak w stats/router.py (None → początek miesiąca / dziś)
    from stats.router import _default_dates
    df, dt = _default_dates(date_from, date_to)
    # Spójny przychód ze shared.revenue (kaskadowy algorytm jak w stats)
    all_pos = await compute_position_revenues(
        db, df, dt, exclude_archival=False  # uwzględnia archiwalne (statystyki historyczne)
    )
    items = await aggregate_by_pna(all_pos, db, limit=limit, group_by=group_by)

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
        "group_by": group_by,
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
    """Get detailed metrics for a specific service.

    RAO-P2-031: Używa shared.revenue zamiast rate1 × period_count.
    """
    # RAO-P2-031: Użyj shared.revenue
    df = date_from or date(2000, 1, 1)
    dt = date_to or date(2100, 1, 1)
    from shared.revenue import compute_position_revenues
    all_positions = await compute_position_revenues(
        db, df, dt, service_filter=True, exclude_archival=False
    )
    # Filtruj po article_id
    service_positions = [p for p in all_positions if p["article_id"] == article_id]

    if not service_positions:
        # Sprawdź czy artykuł istnieje
        art_result = await db.execute(
            select(Article).where(Article.id == article_id).where(Article.is_service == True)
        )
        art = art_result.scalars().first()
        if not art:
            return {"error": "Service not found", "debug": f"article_id={article_id}"}
        return {
            "service": {"id": art.id, "name": art.name},
            "metrics": {"times_billed": 0, "total_revenue": 0},
            "top_contractors": [],
            "location_breakdown": [],
        }

    # Pobierz nazwę artykułu
    service_name = service_positions[0]["article_name"]

    # Top contractors (grupuj po contractor_name)
    from collections import defaultdict
    by_contractor = defaultdict(lambda: {"contractor_name": None, "contract_count": 0, "total_revenue": 0})
    for p in service_positions:
        c = by_contractor[p["contractor_name"]]
        c["contractor_name"] = p["contractor_name"]
        c["contract_count"] += 1
        c["total_revenue"] += float(p["revenue"])
    top_contractors = sorted(by_contractor.values(), key=lambda x: x["total_revenue"], reverse=True)[:5]
    top_contractors = [{"contractor_name": c["contractor_name"],
                        "contract_count": c["contract_count"],
                        "total_revenue": round(c["total_revenue"], 2)} for c in top_contractors]

    # Location breakdown — potrzebuję postal_code_id per contract
    contract_ids = list({p["contract_id"] for p in service_positions})
    contract_loc = {}
    if contract_ids:
        loc_result = await db.execute(
            select(
                Contract.id, Contract.city, Contract.postal_code,
                Contract.postal_code_id,
            ).where(Contract.id.in_(contract_ids))
        )
        contract_loc = {r[0]: {"city": r[1], "postal_code": r[2], "postal_code_id": r[3]}
                        for r in loc_result.all()}

    # PNA dict
    pna_ids = {c["postal_code_id"] for c in contract_loc.values() if c["postal_code_id"]}
    pna_dict: dict[int, dict] = {}
    if pna_ids:
        pc_q = await db.execute(
            select(
                PostalCode.id, PostalCode.postal_code, PostalCode.city,
                PostalCode.wojewodztwo, PostalCode.powiat, PostalCode.gmina,
            ).where(PostalCode.id.in_(pna_ids))
        )
        pna_dict = {r[0]: {"postal_code": r[1], "city": r[2], "wojewodztwo": r[3],
                           "powiat": r[4], "gmina": r[5]} for r in pc_q.all()}

    # Agreguj po (postal_code, city)
    loc_data: dict[tuple[str | None, str], dict] = {}
    for p in service_positions:
        cinfo = contract_loc.get(p["contract_id"], {})
        pna_id = cinfo.get("postal_code_id")
        pna_ref = pna_dict.get(pna_id) if pna_id else None
        if pna_ref:
            postal_code = pna_ref["postal_code"]
            city = pna_ref["city"] or (cinfo.get("city") or "").strip() or NO_PNA_BUCKET
        else:
            postal_code = (cinfo.get("postal_code") or "").strip() or None
            city = (cinfo.get("city") or "").strip() or NO_PNA_BUCKET
        if not city:
            city = NO_PNA_BUCKET
        key = (postal_code, city)
        if key not in loc_data:
            loc_data[key] = {"city": city, "postal_code": postal_code,
                             "contract_count": 0, "total_revenue": 0.0}
        loc_data[key]["contract_count"] += 1
        loc_data[key]["total_revenue"] += float(p["revenue"])

    sorted_loc = sorted(loc_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:10]
    location_breakdown = [
        {"city": d["city"], "postal_code": d["postal_code"],
         "contract_count": d["contract_count"], "total_revenue": round(d["total_revenue"], 2)}
        for _, d in sorted_loc
    ]

    total_revenue = sum(float(p["revenue"]) for p in service_positions)
    return {
        "service": {"id": article_id, "name": service_name},
        "metrics": {
            "times_billed": len(service_positions),
            "total_revenue": round(total_revenue, 2),
        },
        "top_contractors": top_contractors,
        "location_breakdown": location_breakdown,
    }


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


@router.get("/locations/city/{city}")
async def get_city_details(
    city: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Get detailed metrics for a specific city — RAO-P2-069.

    RAO-P2-052: Filtrowanie po mieście w SQL (WHERE clause) zamiast w Pythonie.
    Najpierw jedno zapytanie SQL (LEFT JOIN postal_codes + WHERE city = :city)
    znajduje kontrakty należące do żądanego miasta, następnie
    `compute_position_revenues(contract_ids=...)` pobiera pozycje tylko dla
    tych kontraktów (SQL filter, nie pobiera wszystkich pozycji).

    Drill-down po mieście (zamiast PNA) — sumuje wszystkie PNA w tym mieście.
    Pokazuje rozbicie na PNA w obrębie miasta (top PNA per rentals_count).
    """
    from stats.router import _default_dates
    from urllib.parse import unquote
    city = unquote(city)
    df, dt = _default_dates(date_from, date_to)

    # RAO-P2-052: Znajdź kontrakty należące do żądanego miasta W SQL.
    # City z postal_codes.city ma priorytet (deterministyczne PNA),
    # fallback na contracts.city. MariaDB utf8mb4_polish_ci = case-insensitive,
    # LOWER() dla jawności i bezpieczeństwa collation.
    city_norm = city.strip()
    match_q = (
        select(
            Contract.id.label("cid"),
            Contract.city.label("contract_city"),
            Contract.postal_code.label("contract_pna"),
            Contract.postal_code_id.label("pna_id"),
            PostalCode.postal_code.label("pc_postal_code"),
            PostalCode.city.label("pc_city"),
            PostalCode.wojewodztwo.label("pc_woj"),
            PostalCode.powiat.label("pc_pow"),
            PostalCode.gmina.label("pc_gmina"),
        )
        .outerjoin(PostalCode, PostalCode.id == Contract.postal_code_id)
        .where(
            func.lower(func.coalesce(PostalCode.city, Contract.city))
            == func.lower(city_norm)
        )
    )
    match_result = await db.execute(match_q)
    match_rows = match_result.mappings().all()

    if not match_rows:
        return {"error": "City not found"}

    # Zbuduj mapowanie cid -> pna_key oraz kanoniczne woj/pow/gmina z wyników SQL
    cid_to_pna_key: dict[int, str] = {}
    canonical_woj = canonical_pow = canonical_gmina = None
    for row in match_rows:
        cid = row["cid"]
        # PNA postal_code: z postal_codes (priorytet) lub contracts.postal_code (fallback)
        if row["pc_postal_code"] is not None:
            contract_pna = row["pc_postal_code"]
        else:
            contract_pna = (row["contract_pna"] or "").strip() or None
        cid_to_pna_key[cid] = contract_pna or NO_PNA_BUCKET

        # Kanoniczne woj/pow/gmina z pierwszego dopasowania z PNA
        if canonical_woj is None and row["pc_woj"]:
            canonical_woj = row["pc_woj"]
        if canonical_pow is None and row["pc_pow"]:
            canonical_pow = row["pc_pow"]
        if canonical_gmina is None and row["pc_gmina"]:
            canonical_gmina = row["pc_gmina"]

    matched_contract_ids = set(cid_to_pna_key.keys())

    # RAO-P2-052: Pobierz pozycje tylko dla dopasowanych kontraktów (SQL filter
    # w compute_position_revenues — nie pobiera wszystkich pozycji).
    all_pos = await compute_position_revenues(
        db, df, dt, exclude_archival=False, contract_ids=matched_contract_ids
    )
    if not all_pos:
        return {"error": "City not found"}

    # pna_breakdown i contracts_count z all_pos — zachowuje oryginalne
    # zachowanie (tylko kontrakty z pozycjami w zakresie dat są liczone).
    pna_breakdown: dict[str, dict] = defaultdict(
        lambda: {"contracts": set(), "revenue": Decimal(0)}
    )
    for p in all_pos:
        cid = p["contract_id"]
        pna_key = cid_to_pna_key.get(cid, NO_PNA_BUCKET)
        pna_breakdown[pna_key]["contracts"].add(cid)
        pna_breakdown[pna_key]["revenue"] += p["revenue"]

    contracts_count = len({p["contract_id"] for p in all_pos})
    unique_contractors = len({p["contractor_id"] for p in all_pos if p.get("contractor_id")})
    total_revenue = float(sum((p["revenue"] for p in all_pos), Decimal(0)))

    # Top machines w tym mieście
    machine_data: dict[str, dict] = {}
    for p in all_pos:
        name = p["article_name"] or "(bez nazwy)"
        if name not in machine_data:
            machine_data[name] = {"rental_count": 0, "total_revenue": 0.0}
        machine_data[name]["rental_count"] += 1
        machine_data[name]["total_revenue"] += float(p["revenue"])
    top_machines = [
        {"name": k, "rental_count": v["rental_count"], "total_revenue": v["total_revenue"]}
        for k, v in sorted(machine_data.items(), key=lambda x: x[1]["rental_count"], reverse=True)[:10]
    ]

    # Top contractors
    contractor_data: dict[str, dict] = {}
    for p in all_pos:
        cname = p["contractor_name"] or "(nieznany kontrahent)"
        if cname not in contractor_data:
            contractor_data[cname] = {"contract_count": 0, "total_revenue": 0.0}
        contractor_data[cname]["contract_count"] += 1
        contractor_data[cname]["total_revenue"] += float(p["revenue"])
    top_contractors = [
        {"contractor_name": k, "contract_count": v["contract_count"], "total_revenue": v["total_revenue"]}
        for k, v in sorted(contractor_data.items(), key=lambda x: x[1]["total_revenue"], reverse=True)[:5]
    ]

    # PNA breakdown (rozbicie miasta na kody pocztowe)
    pna_list = [
        {
            "postal_code": k,
            "rentals_count": len(v["contracts"]),
            "total_revenue": float(v["revenue"]),
        }
        for k, v in sorted(pna_breakdown.items(), key=lambda x: x[1]["revenue"], reverse=True)
    ]

    avg_per_contract = total_revenue / contracts_count if contracts_count else 0

    return {
        "city": city,
        "postal_code": None,  # miasto = suma wielu PNA
        "gmina": canonical_gmina,
        "powiat": canonical_pow,
        "wojewodztwo": canonical_woj,
        "metrics": {
            "contracts_count": contracts_count,
            "unique_contractors": unique_contractors,
            "total_revenue": round(total_revenue, 2),
            "avg_revenue_per_contract": round(avg_per_contract, 2),
            "pna_count": len(pna_list),
        },
        "pna_breakdown": pna_list,
        "top_machines": top_machines,
        "top_contractors": top_contractors,
        "monthly_trend": [],
    }
