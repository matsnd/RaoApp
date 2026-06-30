"""
Shared location aggregation by PNA — RAO-P2-028.

Strategia PNA (deterministyczna):
- Klucz grupowania: postal_code (PNA) — UNIQUE w `postal_codes`.
- Rollup po (city, wojewodztwo, powiat, gmina) z LEFT JOIN do `postal_codes`.
- NULL PNA → bucket "(brak PNA)" z city z `contracts.city` (NIE regex fallback).
- Przychód z `shared.revenue.compute_position_revenues` (kaskadowy algorytm).

Public API:
    aggregate_by_pna(positions, db, *, limit=None) -> list[LocationStatItem]
"""
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.models import Contract
from integrations.models import PostalCode
from stats.schemas import LocationStatItem


NO_PNA_BUCKET = "(brak PNA)"


async def aggregate_by_pna(
    positions: list[dict],
    db: AsyncSession,
    *,
    limit: int | None = None,
) -> list[LocationStatItem]:
    """
    Zagreguj pozycje po PNA (postal_code) z rollup po city/woj/pow/gmina.

    Args:
        positions: lista dictów z `compute_position_revenues`
                   (wymaga `contract_id`, `revenue`).
        db: AsyncSession — do LEFT JOIN z `postal_codes`.
        limit: opcjonalnie uciąć wynik (top-N po rentals_count).

    Returns:
        list[LocationStatItem] posortowany po rentals_count desc.
    """
    contract_ids = {p["contract_id"] for p in positions if p.get("contract_id")}
    if not contract_ids:
        return []

    # Pobierz contracts.city + postal_code + postal_code_id (FK)
    loc_q = await db.execute(
        select(
            Contract.id,
            Contract.city,
            Contract.postal_code,
            Contract.postal_code_id,
        ).where(Contract.id.in_(contract_ids))
    )
    contract_loc = {
        r[0]: {"city": r[1], "pna": r[2], "pna_id": r[3]}
        for r in loc_q.all()
    }

    # LEFT JOIN do postal_codes dla gmina/powiat/wojewodztwo (po FK postal_code_id)
    pna_ids = {v["pna_id"] for v in contract_loc.values() if v["pna_id"]}
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
                "postal_code": r[1],
                "city": r[2],
                "wojewodztwo": r[3],
                "powiat": r[4],
                "gmina": r[5],
            }
            for r in pc_q.all()
        }

    # Agregacja: klucz = (postal_code, city)
    # NULL PNA → bucket NO_PNA_BUCKET, city z contracts.city
    agg: dict[tuple[str | None, str], dict] = defaultdict(
        lambda: {
            "rev": Decimal(0),
            "contracts": set(),
            "city": "",
            "postal_code": None,
            "gmina": None,
            "powiat": None,
            "wojewodztwo": None,
        }
    )

    for p in positions:
        cid = p.get("contract_id")
        if cid is None:
            continue
        loc = contract_loc.get(cid)
        if not loc:
            continue

        city = (loc["city"] or "").strip()
        pna_id = loc["pna_id"]
        pna_ref = pna_dict.get(pna_id) if pna_id else None

        if pna_ref:
            # Deterministyczny PNA ze słownika
            postal_code = pna_ref["postal_code"]
            # city ze słownika PNA (kanoniczne), fallback na contracts.city
            city = pna_ref["city"] or city or NO_PNA_BUCKET
            gmina = pna_ref["gmina"]
            powiat = pna_ref["powiat"]
            wojewodztwo = pna_ref["wojewodztwo"]
        else:
            # Brak FK — fallback na contracts.postal_code (legacy) lub bucket NO_PNA
            postal_code = (loc["pna"] or "").strip() or None
            if not city:
                city = NO_PNA_BUCKET
            gmina = None
            powiat = None
            wojewodztwo = None

        if not city:
            city = NO_PNA_BUCKET

        key = (postal_code, city)
        bucket = agg[key]
        bucket["rev"] += p["revenue"]
        bucket["contracts"].add(cid)
        bucket["city"] = city
        bucket["postal_code"] = postal_code
        bucket["gmina"] = gmina
        bucket["powiat"] = powiat
        bucket["wojewodztwo"] = wojewodztwo

    items: list[LocationStatItem] = []
    for (_, _city), d in agg.items():
        items.append(
            LocationStatItem(
                city=d["city"],
                postal_code=d["postal_code"],
                gmina=d["gmina"],
                powiat=d["powiat"],
                wojewodztwo=d["wojewodztwo"],
                rentals_count=len(d["contracts"]),
                total_revenue=d["rev"],
            )
        )

    items.sort(key=lambda x: x.rentals_count, reverse=True)
    if limit is not None:
        items = items[:limit]
    return items
