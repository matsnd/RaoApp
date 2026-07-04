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


def calculate_position_value(
    rental_days: int | None,
    billing_frequency: str | None,
    unit_price: Decimal | None,
    quantity: int | None,
    conditions: list[dict],
) -> Decimal:
    """
    Calculate the value of a single position.

    Args:
        rental_days: number of rental days from contract_positions
        billing_frequency: e.g. 'dziennie', 'tygodniowo'
        unit_price: fallback if no conditions (usually NULL)
        quantity: fallback multiplier (usually 1)
        conditions: list of dicts with keys:
            rate1 (Decimal), rate2 (Decimal|None),
            period_count (int), minimum (int),
            rate_type_id (int)
    """
    if not conditions:
        if unit_price and quantity:
            return Decimal(str(unit_price)) * int(quantity)
        return Decimal("0.00")

    days = rental_days or 0
    if days <= 0:
        return Decimal("0.00")

    freq = billing_frequency or "dziennie"
    dpp = get_days_per_period(freq)
    total_periods = math.ceil(days / dpp) if dpp > 0 else 0

    # Apply minimum from first condition
    min_periods = conditions[0].get("minimum") or 0
    if total_periods < min_periods:
        total_periods = min_periods

    if total_periods <= 0:
        return Decimal("0.00")

    # Tiered calculation
    total_value = Decimal("0.00")
    remaining = total_periods

    for i, cond in enumerate(conditions):
        if remaining <= 0:
            break

        pc = cond.get("period_count") or remaining
        rate = Decimal(str(cond.get("rate1") or 0))

        if rate <= 0:
            continue

        if i == 0:
            periods_in_tier = min(remaining, pc)
        else:
            prev_pc = conditions[i - 1].get("period_count") or 0
            tier_size = (pc or 999) - prev_pc
            periods_in_tier = min(remaining, tier_size)

        total_value += rate * periods_in_tier
        remaining -= periods_in_tier

    # If remaining periods after all tiers, use last non-zero rate
    if remaining > 0:
        for cond in reversed(conditions):
            rate = Decimal(str(cond.get("rate1") or 0))
            if rate > 0:
                total_value += rate * remaining
                break

    # RAO-P0-033: multiply by quantity consistently (matches no-conditions branch)
    return total_value * int(quantity or 1)


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
        agg[cat_name]["days"] += p.get("clamped_days", 0)
        agg[cat_name]["contracts"].add(p.get("contract_id"))
        agg[cat_name]["articles"].add(p.get("article_id"))

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
        agg[ctype]["articles"].add(p.get("article_id"))
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
        agg[key]["articles"].add(p.get("article_id"))
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
