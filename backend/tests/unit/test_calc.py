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
    conds = [{"rate1": d(100), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    assert calculate_position_value(0, "dziennie", None, 1, conds) == d(0)


# ── single flat-rate condition ────────────────────────────────────────────────

def test_single_daily_rate():
    conds = [{"rate1": d(100), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    result = calculate_position_value(5, "dziennie", None, 1, conds)
    assert result == d(500)

def test_weekly_rate():
    conds = [{"rate1": d(700), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    result = calculate_position_value(14, "tygodniowo", None, 1, conds)
    assert result == d(1400)  # ceil(14/7)=2 periods × 700

def test_monthly_rate():
    conds = [{"rate1": d(3000), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    result = calculate_position_value(30, "miesięcznie", None, 1, conds)
    assert result == d(3000)


# ── minimum enforcement ───────────────────────────────────────────────────────

def test_minimum_enforced():
    conds = [{"rate1": d(100), "rate2": None, "period_count": 0, "minimum": 5, "rate_type_id": 1}]
    result = calculate_position_value(2, "dziennie", None, 1, conds)
    assert result == d(500)  # minimum 5 days × 100

def test_minimum_not_needed():
    conds = [{"rate1": d(100), "rate2": None, "period_count": 0, "minimum": 3, "rate_type_id": 1}]
    result = calculate_position_value(7, "dziennie", None, 1, conds)
    assert result == d(700)  # 7 days > minimum 3


# ── tiered conditions ─────────────────────────────────────────────────────────

def test_two_tier_stays_in_first():
    conds = [
        {"rate1": d(100), "rate2": None, "period_count": 7, "minimum": 0, "rate_type_id": 1},
        {"rate1": d(80),  "rate2": None, "period_count": 14, "minimum": 0, "rate_type_id": 1},
    ]
    result = calculate_position_value(5, "dziennie", None, 1, conds)
    assert result == d(500)  # 5 days × 100

def test_two_tier_crosses_boundary():
    conds = [
        {"rate1": d(100), "rate2": None, "period_count": 7, "minimum": 0, "rate_type_id": 1},
        {"rate1": d(80),  "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1},
    ]
    result = calculate_position_value(10, "dziennie", None, 1, conds)
    assert result == d(7*100 + 3*80)  # 700 + 240 = 940

def test_three_tier_overflow_uses_last():
    conds = [
        {"rate1": d(200), "rate2": None, "period_count": 3, "minimum": 0, "rate_type_id": 1},
        {"rate1": d(150), "rate2": None, "period_count": 7, "minimum": 0, "rate_type_id": 1},
        {"rate1": d(100), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1},
    ]
    result = calculate_position_value(12, "dziennie", None, 1, conds)
    # tier1: 3×200=600, tier2: 4×150=600, tier3: 5×100=500 → 1700
    assert result == d(1700)


# ── edge cases ────────────────────────────────────────────────────────────────

def test_ceil_rounding():
    conds = [{"rate1": d(700), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    # 8 days / 7 = ceil(1.14) = 2 periods
    result = calculate_position_value(8, "tygodniowo", None, 1, conds)
    assert result == d(1400)

def test_unknown_frequency_defaults_to_daily():
    conds = [{"rate1": d(50), "rate2": None, "period_count": 0, "minimum": 0, "rate_type_id": 1}]
    result = calculate_position_value(3, "nieznane_rozliczanie", None, 1, conds)
    assert result == d(150)
