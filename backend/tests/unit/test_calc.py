"""Unit tests for stats/calc.py — calculate_position_value"""
import pytest
from decimal import Decimal
from stats.calc import calculate_position_value


def d(val) -> Decimal:
    return Decimal(str(val))


# ── no conditions ────────────────────────────────────────────────────────────

def test_no_conditions_unit_price():
    assert calculate_position_value(1, "dziennie", d(100), 1, []) == d(100)

def test_no_conditions_quantity():
    assert calculate_position_value(1, "dziennie", d(50), 3, []) == d(150)

def test_no_conditions_no_unit_price():
    assert calculate_position_value(5, "dziennie", None, 1, []) == d(0)

def test_zero_days():
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 0}]
    assert calculate_position_value(0, "dziennie", None, 1, conds) == d(0)


# ── single flat-rate condition ────────────────────────────────────────────────

def test_single_daily_rate():
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 0}]
    result = calculate_position_value(5, "dziennie", None, 1, conds)
    assert result == d(500)

def test_weekly_rate():
    conds = [{"rate1": d(700), "period_from": 1, "period_to": None, "minimum": 0}]
    result = calculate_position_value(14, "tygodniowo", None, 1, conds)
    assert result == d(1400)  # ceil(14/7)=2 periods × 700

def test_monthly_rate():
    conds = [{"rate1": d(3000), "period_from": 1, "period_to": None, "minimum": 0}]
    result = calculate_position_value(30, "miesięcznie", None, 1, conds)
    assert result == d(3000)


# ── minimum enforcement ───────────────────────────────────────────────────────

def test_minimum_enforced():
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 5}]
    result = calculate_position_value(2, "dziennie", None, 1, conds)
    assert result == d(500)  # minimum 5 days × 100

def test_minimum_not_needed():
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 3}]
    result = calculate_position_value(7, "dziennie", None, 1, conds)
    assert result == d(700)  # 7 days > minimum 3


# ── tiered conditions (new source fields) ─────────────────────────────────────

def test_two_tier_stays_in_first():
    conds = [
        {"rate1": d(100), "period_from": 1, "period_to": 7, "minimum": 0},
        {"rate1": d(80),  "period_from": 8, "period_to": 14, "minimum": 0},
    ]
    result = calculate_position_value(5, "dziennie", None, 1, conds)
    assert result == d(500)  # 5 days × 100

def test_two_tier_crosses_boundary():
    conds = [
        {"rate1": d(100), "period_from": 1, "period_to": 7, "minimum": 0},
        {"rate1": d(80),  "period_from": 8, "period_to": None, "minimum": 0},
    ]
    result = calculate_position_value(10, "dziennie", None, 1, conds)
    assert result == d(7*100 + 3*80)  # 700 + 240 = 940

def test_three_tier_overflow_uses_last():
    conds = [
        {"rate1": d(200), "period_from": 1, "period_to": 3, "minimum": 0},
        {"rate1": d(150), "period_from": 4, "period_to": 7, "minimum": 0},
        {"rate1": d(100), "period_from": 8, "period_to": None, "minimum": 0},
    ]
    result = calculate_position_value(12, "dziennie", None, 1, conds)
    # tier1: 3×200=600, tier2: 4×150=600, tier3: 5×100=500 → 1700
    assert result == d(1700)


def test_service_flat_rate_uses_quantity():
    """Service (U) uses quantity as the period value, not rental_days."""
    conds = [{"rate1": d(100), "period_from": 0, "period_to": None, "minimum": 0}]
    result = calculate_position_value(0, "godzinowo", None, 8, conds, is_service=True)
    assert result == d(800)  # 8 hours × 100


def test_service_tiered():
    """Service tiered pricing uses hours (quantity) for tier lookup."""
    conds = [
        {"rate1": d(100), "period_from": 0, "period_to": 8, "minimum": 0},
        {"rate1": d(80),  "period_from": 9, "period_to": None, "minimum": 0},
    ]
    # 10 hours: first 8 × 100 + next 2 × 80 = 960
    result = calculate_position_value(0, "godzinowo", None, 10, conds, is_service=True)
    assert result == d(960)


def test_service_minimum():
    """Service minimum applies to quantity (hours)."""
    conds = [{"rate1": d(100), "period_from": 0, "period_to": None, "minimum": 8}]
    result = calculate_position_value(0, "godzinowo", None, 5, conds, is_service=True)
    assert result == d(800)  # minimum 8 hours × 100


# ── edge cases ────────────────────────────────────────────────────────────────

def test_ceil_rounding():
    conds = [{"rate1": d(700), "period_from": 1, "period_to": None, "minimum": 0}]
    # 8 days / 7 = ceil(1.14) = 2 periods
    result = calculate_position_value(8, "tygodniowo", None, 1, conds)
    assert result == d(1400)

def test_unknown_frequency_defaults_to_daily():
    conds = [{"rate1": d(50), "period_from": 1, "period_to": None, "minimum": 0}]
    result = calculate_position_value(3, "nieznane_rozliczanie", None, 1, conds)
    assert result == d(150)


# ── RAO-P0-033: quantity multiplication with conditions ──────────────────────

def test_quantity_with_conditions_multiplies_once():
    """Regression: calculate_position_value must multiply by quantity exactly once."""
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 0}]
    # 5 days × 100 = 500 per unit; quantity 3 → 1500 (NOT 4500)
    result = calculate_position_value(5, "dziennie", None, 3, conds)
    assert result == d(1500)

def test_quantity_two_tier():
    conds = [
        {"rate1": d(100), "period_from": 1, "period_to": 7, "minimum": 0},
        {"rate1": d(80),  "period_from": 8, "period_to": None, "minimum": 0},
    ]
    # 10 days: 7×100 + 3×80 = 940 per unit; quantity 2 → 1880
    result = calculate_position_value(10, "dziennie", None, 2, conds)
    assert result == d(1880)

def test_quantity_null_defaults_to_one():
    conds = [{"rate1": d(100), "period_from": 1, "period_to": None, "minimum": 0}]
    # None quantity → defaults to 1 (defensive, matches `or 1` pattern)
    result = calculate_position_value(5, "dziennie", None, None, conds)
    assert result == d(500)


def test_legacy_period_count_still_works():
    """Backward compatibility: old period_count/rate2 conditions still work."""
    conds = [
        {"rate1": d(100), "rate2": None, "period_count": 7, "minimum": 0},
        {"rate1": d(80), "rate2": None, "period_count": 0, "minimum": 0},
    ]
    result = calculate_position_value(10, "dziennie", None, 1, conds)
    assert result == d(940)
