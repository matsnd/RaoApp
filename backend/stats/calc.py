"""
Position value calculation engine.

Implements the algorithm from spec 04_BUSINESS_LOGIC.md:
- Type 1: one-time fee (unit_price × quantity)
- Type 2: tiered pricing (conditions sorted by period_count)
- Type 3: simple rate (rate1 × total_periods)

Source of truth: position_conditions.rate1 + contract_positions.rental_days
Old WinForms: FormU4.cs spaghetti → rozliczenie table (1 row/day)
"""
import math
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

    return total_value
