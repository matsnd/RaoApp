"""
Position value calculation engine.

Implements the algorithm from spec 04_BUSINESS_LOGIC.md:
- Type 1: one-time fee (unit_price × quantity)
- Type 2: tiered pricing (conditions sorted by period_count)
- Type 3: simple rate (rate1 × total_periods)

Source of truth: position_conditions.rate1 + contract_positions.rental_days
Old WinForms: FormU4.cs spaghetti → rozliczenie table (1 row/day)

RAO-P1-017: dodano aggregate_by_category() dla statystyk po kategoriach
RAO-P1-026: dodano aggregate_by_period() + rozszerzono poziomy sub2/sub3
RAO-P2-071: usunięto legacy extract_city() + KNOWN_CITIES + IGNORE_PATTERNS (zastąpione
            deterministycznym PNA dictionary w shared/locations.py — RAO-P2-028).
"""
import math
from collections import defaultdict
from decimal import Decimal


DAYS_PER_PERIOD = {
    "dziennie": 1,
    "dzienna": 1,
    "tygodniowo": 7,
    "dwutygodniowo": 14,
    "miesięcznie": 30,
    "miesieczne": 30,
    "godzinowo": 1,
    "jednorazowo": 1,
}


def get_days_per_period(billing_frequency: str | None) -> int:
    return DAYS_PER_PERIOD.get(billing_frequency or "dziennie", 1)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


def _condition_has_new_periods(cond: dict) -> bool:
    """RAO-P2-071: condition uses the new source-of-truth period fields."""
    return (
        cond.get("period_from") is not None
        or cond.get("period_to") is not None
    )


def _extract_rate_tiers(conditions: list[dict]) -> list[tuple[int, int | None, Decimal]]:
    """
    Build a list of logical rate tiers from conditions.

    Phase 2: primary source is period_from/period_to/rate1. If a condition
    has the new fields (period_from or rate1), we use them directly.
    Legacy rows still relying on period_count/rate2 are converted back into
    ranges for compatibility.

    Returns list of (tier_start, tier_end, rate). `tier_end` = None means
    open-ended (continues for all remaining periods).
    """
    if not conditions:
        return []

    # Detect whether the conditions have the new source-of-truth fields.
    if any(_condition_has_new_periods(c) for c in conditions):
        return _extract_rate_tiers_from_new_fields(conditions)
    return _extract_rate_tiers_from_legacy(conditions)


def _extract_rate_tiers_from_new_fields(
    conditions: list[dict],
) -> list[tuple[int, int | None, Decimal]]:
    """
    New source of truth: period_from/period_to/rate1.

    - period_from is inclusive. If period_from is 0, the first chargeable
      period is 1, but the rate starts at 0 so the overlap is correct.
    - period_to is inclusive. None means open-ended.
    - rate1 is the rate for the whole range. rate2 is treated as legacy fallback
      when rate1 is missing (open-ended tier generated from a legacy preset).
    """
    conds: list[dict] = []
    for c in conditions:
        rate = _to_decimal(c.get("rate1"))
        if rate <= 0:
            rate = _to_decimal(c.get("rate2"))
        if rate <= 0:
            continue
        period_from = c.get("period_from")
        period_to = c.get("period_to")
        if period_from is None and period_to is None:
            # Single open-ended rate with no explicit from; default to 1.
            period_from = 1
        conds.append({
            "period_from": period_from,
            "period_to": period_to,
            "rate": rate,
        })

    if not conds:
        return []

    # Sort by start period. NULL (open-ended) at the end.
    conds.sort(key=lambda c: (c["period_from"] is None, c["period_from"] or 0))

    tiers: list[tuple[int, int | None, Decimal]] = []
    for c in conds:
        start = c["period_from"] or 1
        end = c["period_to"]
        if start < 1:
            start = 1
        if end is not None and end < start:
            continue
        tiers.append((start, end, c["rate"]))

    return tiers


def _extract_rate_tiers_from_legacy(
    conditions: list[dict],
) -> list[tuple[int, int | None, Decimal]]:
    """
    Legacy compatibility: builds tiers from period_count/rate1/rate2.
    Kept for stats/calc.py and shared/revenue.py callers using old data.
    """
    conds = sorted(
        conditions,
        key=lambda c: (c.get("period_count") is None, c.get("period_count") or 0),
    )

    tiers: list[tuple[int, int | None, Decimal]] = []
    current_end = 0

    for i, cond in enumerate(conds):
        pc = cond.get("period_count")
        rate1 = _to_decimal(cond.get("rate1"))
        rate2 = _to_decimal(cond.get("rate2"))

        next_pc = None
        for j in range(i + 1, len(conds)):
            npc = conds[j].get("period_count")
            if npc is not None:
                next_pc = npc
                break

        if rate1 > 0 and pc is not None:
            start = current_end + 1
            end = pc
            if start <= end:
                tiers.append((start, end, rate1))
                current_end = end

        if rate2 > 0:
            if rate1 > 0 and pc is not None:
                start = pc + 1
            else:
                start = current_end + 1

            if next_pc is not None:
                end = next_pc - 1
            else:
                end = None

            if end is None or start <= end:
                if start > current_end or end is None:
                    tiers.append((start, end, rate2))
                    if end is not None:
                        current_end = end

    return tiers


def _quantity_multiplier(quantity: int | None, is_service: bool) -> int:
    """
    For rental (S) `quantity` is the number of machines and multiplies the
    per-day total. For service (U) `quantity` is already the hour count and
    is used as the period value, so no extra multiplier is applied.
    """
    if is_service:
        return 1
    return int(quantity or 1)


def calculate_position_value(
    rental_days: int | None,
    billing_frequency: str | None,
    unit_price: Decimal | None,
    quantity: int | None,
    conditions: list[dict],
    is_service: bool = False,
) -> Decimal:
    """
    Calculate the value of a single position.

    Args:
        rental_days: number of rental days from contract_positions (S)
        billing_frequency: e.g. 'dziennie', 'tygodniowo', 'godzinowo'
        unit_price: fallback if no conditions (usually NULL)
        quantity: number of machines (S) or hours (U)
        conditions: list of dicts with keys:
            rate1 (Decimal), rate2 (Decimal|None),
            period_from (int), period_to (int),
            period_count (int), minimum (int)
        is_service: True for service contracts (U) where `quantity` is hours
    """
    if not conditions:
        if unit_price and quantity:
            return Decimal(str(unit_price)) * int(quantity)
        return Decimal("0.00")

    # Phase 2: service uses quantity (hours) as the period value;
    # rental uses rental_days (converted by billing_frequency).
    if is_service:
        periods_raw = quantity or 0
    else:
        days = rental_days or 0
        if days <= 0:
            return Decimal("0.00")
        freq = billing_frequency or "dziennie"
        dpp = get_days_per_period(freq)
        periods_raw = math.ceil(days / dpp) if dpp > 0 else 0

    if periods_raw <= 0:
        return Decimal("0.00")

    # Apply global minimum (taken from any condition; first is the legacy source).
    min_periods = max((c.get("minimum") or 0 for c in conditions), default=0)
    total_periods = max(periods_raw, min_periods)

    if total_periods <= 0:
        return Decimal("0.00")

    tiers = _extract_rate_tiers(conditions)

    total_value = Decimal("0.00")
    remaining = total_periods

    for start, end, rate in tiers:
        if remaining <= 0:
            break
        if start > total_periods:
            continue

        effective_end = end if end is not None else total_periods
        # Clamp to the total number of periods and remaining budget
        periods = min(effective_end, total_periods) - start + 1
        periods = max(0, periods)
        if periods > remaining:
            periods = remaining
        if periods <= 0:
            continue

        total_value += rate * periods
        remaining -= periods

    # Fallback: if no condition covered all periods, use the last non-zero rate
    if remaining > 0:
        last_rate = Decimal("0.00")
        for cond in reversed(conditions):
            rate1 = _to_decimal(cond.get("rate1"))
            rate2 = _to_decimal(cond.get("rate2"))
            if rate1 > 0 or rate2 > 0:
                last_rate = rate1 if rate1 > 0 else rate2
                if last_rate > 0:
                    break
        if last_rate > 0:
            total_value += last_rate * remaining

    # RAO-P0-033: multiply by quantity for rental; service is already counted
    return total_value * _quantity_multiplier(quantity, is_service)


# ── RAO-P1-017: Agregacja po kategoriach ─────────────────────────────────────

_FALLBACK_CATEGORY = "(bez kategorii)"


_LEVEL_FIELDS = {
    "main": "category_main",
    "sub1": "category_sub1",
    "sub2": "category_sub2",
    "sub3": "category_sub3",
}


def aggregate_by_category(
    positions: list[dict],
    level: str = "main",
) -> list[dict]:
    """
    Agreguje dane pozycji wynajmu według poziomu kategorii (RAO-P1-017).

    Args:
        positions: lista dict-ów z _compute_position_revenues
                   (wymagane klucze: article_id, contract_id, revenue,
                    clamped_days, category_main, category_sub1,
                    category_sub2, category_sub3)
        level: "main"  → grupuje po category_main
               "sub1"  → grupuje po category_sub1
               "sub2"  → grupuje po category_sub2  (RAO-P1-026)
               "sub3"  → grupuje po category_sub3  (RAO-P1-026)

    Returns:
        lista dict-ów posortowanych malejąco po revenue:
            category_name, articles_count, rented_days, revenue, contracts_count
    """
    agg: dict[str, dict] = defaultdict(lambda: {
        "revenue": Decimal("0"),
        "days": 0,
        "contracts": set(),
        "articles": set(),
    })

    field = _LEVEL_FIELDS.get(level, "category_main")

    for p in positions:
        cat_name = p.get(field) or _FALLBACK_CATEGORY
        agg[cat_name]["revenue"] += p.get("revenue", Decimal("0"))
        # RAO-P1-BUG-7: rented_days liczone tylko dla maszyn (usługi mają billing != DAILY)
        if not p.get("is_service"):
            agg[cat_name]["days"] += p.get("clamped_days", 0)
        agg[cat_name]["contracts"].add(p.get("contract_id"))
        # RAO Faza 2a (opcja E): unmapped (article_id=None) nie liczy się jako artykuł
        art_id = p.get("article_id")
        if art_id is not None:
            agg[cat_name]["articles"].add(art_id)

    return sorted(
        [
            {
                "category_name": cat,
                "articles_count": len(d["articles"]),
                "rented_days": d["days"],
                "revenue": d["revenue"],
                "contracts_count": len(d["contracts"]),
            }
            for cat, d in agg.items()
        ],
        key=lambda x: x["revenue"],
        reverse=True,
    )


# ── RAO-P1-026: Agregacja po okresach ────────────────────────────────────────

def aggregate_by_period(
    positions: list[dict],
    granularity: str = "month",
    category_main_filter: list[str] | None = None,
) -> list[dict]:
    """
    Agreguje pozycje per (period, category_name) (RAO-P1-026).

    Args:
        positions: lista dict-ów z _compute_position_revenues
                   (wymagane klucze: contract_date_from, revenue,
                    clamped_days, contract_id, category_main)
        granularity: "month" → period = "YYYY-MM"
                     "year"  → period = "YYYY"
        category_main_filter: gdy podany → osobna seria per kategorię;
                              gdy None/pusty → jedna seria "__all__"

    Returns:
        lista dict-ów posortowanych rosnąco po (period, category_name):
            period, category_name, revenue, rented_days, contracts_count
    """
    _FALLBACK = "(bez kategorii)"

    agg: dict[tuple, dict] = defaultdict(lambda: {
        "revenue": Decimal("0"),
        "days": 0,
        "contracts": set(),
    })

    for p in positions:
        dt = p.get("contract_date_from")
        if not dt:
            continue
        period = f"{dt.year}-{dt.month:02d}" if granularity == "month" else str(dt.year)

        if category_main_filter:
            cat = p.get("category_main") or _FALLBACK
        else:
            cat = "__all__"

        key = (period, cat)
        agg[key]["revenue"] += p.get("revenue", Decimal("0"))
        # RAO-P1-BUG-7: rented_days liczone tylko dla maszyn (usługi mają billing != DAILY)
        if not p.get("is_service"):
            agg[key]["days"] += p.get("clamped_days", 0)
        agg[key]["contracts"].add(p.get("contract_id"))

    return sorted(
        [
            {
                "period": k[0],
                "category_name": k[1],
                "revenue": v["revenue"],
                "rented_days": v["days"],
                "contracts_count": len(v["contracts"]),
            }
            for k, v in agg.items()
        ],
        key=lambda x: (x["period"], x["category_name"]),
    )


# ── RAO-P2-056: Agregacja po contract_type (S=najem, U=usługa) ───────────────

_CONTRACT_TYPE_LABELS = {"S": "najem", "U": "usługa"}


def aggregate_by_contract_type(positions: list[dict]) -> list[dict]:
    """
    Agreguje pozycje umów po contract_type umowy nadrzędnej (RAO-P2-056).

    Args:
        positions: lista dict-ów z compute_position_revenues
                   (wymagane klucze: contract_id, article_id, revenue,
                    clamped_days, is_service, contract_type)

    Returns:
        lista dict-ów posortowanych rosnąco po contract_type ("S" przed "U"):
            contract_type, contract_type_label, contracts_count,
            positions_count, articles_count, rented_days, revenue
    """
    agg: dict[str, dict] = defaultdict(lambda: {
        "contracts": set(),
        "positions": 0,
        "articles": set(),
        "rented_days": 0,
        "revenue": Decimal("0"),
    })

    for p in positions:
        ctype = p.get("contract_type") or "S"
        agg[ctype]["contracts"].add(p.get("contract_id"))
        agg[ctype]["positions"] += 1
        # RAO Faza 2a (opcja E): unmapped (article_id=None) nie liczy się jako artykuł
        art_id = p.get("article_id")
        if art_id is not None:
            agg[ctype]["articles"].add(art_id)
        # rented_days liczone tylko dla maszyn (usługi mają billing != DAILY)
        if not p.get("is_service"):
            agg[ctype]["rented_days"] += p.get("clamped_days", 0)
        agg[ctype]["revenue"] += p.get("revenue", Decimal("0"))

    return sorted(
        [
            {
                "contract_type": ctype,
                "contract_type_label": _CONTRACT_TYPE_LABELS.get(ctype, ctype),
                "contracts_count": len(d["contracts"]),
                "positions_count": d["positions"],
                "articles_count": len(d["articles"]),
                "rented_days": d["rented_days"],
                "revenue": d["revenue"],
            }
            for ctype, d in agg.items()
        ],
        key=lambda x: x["contract_type"],
    )


# ── RAO-P1-055: Agregacja po oddziale (branch) ────────────────────────────────

_UNASSIGNED_BRANCH_KEY = "__none__"
_UNASSIGNED_BRANCH_LABEL = "(bez oddziału)"


def aggregate_by_branch(
    positions: list[dict],
    branches: list[dict] | None = None,
) -> list[dict]:
    """
    Agreguje pozycje umów po oddziale (branch_id) umowy nadrzędnej (RAO-P1-055).

    Args:
        positions: lista dict-ów z compute_position_revenues
                   (wymagane klucze: contract_id, article_id, revenue,
                    clamped_days, is_service, branch_id)
        branches: opcjonalna lista dict-ów {id, name} z tabeli branches
                  (do mapowania branch_id → branch_name). Gdy None lub
                  brak mapowania → etykieta "(bez oddziału)".

    Returns:
        lista dict-ów posortowana malejąco po revenue:
            branch_id, branch_name, contracts_count, positions_count,
            articles_count, rented_days, revenue
        Wiersz "bez oddziału" (branch_id=None) zawsze na końcu.
    """
    branch_name_map: dict[int, str] = {}
    if branches:
        for b in branches:
            bid = b.get("id")
            if bid is not None:
                branch_name_map[int(bid)] = b.get("name") or f"Oddział #{bid}"

    agg: dict[object, dict] = defaultdict(lambda: {
        "contracts": set(),
        "positions": 0,
        "articles": set(),
        "rented_days": 0,
        "revenue": Decimal("0"),
    })

    for p in positions:
        bid = p.get("branch_id")
        key = bid if bid is not None else _UNASSIGNED_BRANCH_KEY
        agg[key]["contracts"].add(p.get("contract_id"))
        agg[key]["positions"] += 1
        # RAO Faza 2a (opcja E): unmapped (article_id=None) nie liczy się jako artykuł
        art_id = p.get("article_id")
        if art_id is not None:
            agg[key]["articles"].add(art_id)
        if not p.get("is_service"):
            agg[key]["rented_days"] += p.get("clamped_days", 0)
        agg[key]["revenue"] += p.get("revenue", Decimal("0"))

    items = []
    for key, d in agg.items():
        if key == _UNASSIGNED_BRANCH_KEY:
            branch_id = None
            branch_name = _UNASSIGNED_BRANCH_LABEL
        else:
            branch_id = int(key)
            branch_name = branch_name_map.get(branch_id, f"Oddział #{branch_id}")
        items.append({
            "branch_id": branch_id,
            "branch_name": branch_name,
            "contracts_count": len(d["contracts"]),
            "positions_count": d["positions"],
            "articles_count": len(d["articles"]),
            "rented_days": d["rented_days"],
            "revenue": d["revenue"],
        })

    # Sortuj malejąco po revenue; wiersz "bez oddziału" zawsze na końcu
    items.sort(key=lambda x: (x["branch_id"] is None, -x["revenue"]))
    return items
