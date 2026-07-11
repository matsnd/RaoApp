"""
Unit testy dla RAO-P1-016: defensive clamps dla ROI i dni.

Reprodukuje i fixuje bug P1-016 (statystyki -300%, -7):
- revenue < 0 (korekta/zwrot) + replacement_value > 0 → ROI = None (nie -300%)
- date_to < date_from → dni = 0 (nie -7)
- replacement_value = 0 → ROI = None (dzielenie przez zero — już obsłużone)
- replacement_value = None → ROI = None
- revenue = 0 → ROI = 0.0 (nie None — maszyna wynajęta bez przychodu)

Testowane funkcje (stats/calc.py):
- compute_roi_pct(revenue, replacement_value)
- clamp_days(days)
"""
import logging
from decimal import Decimal

import pytest

from stats.calc import compute_roi_pct, clamp_days


def d(val) -> Decimal:
    return Decimal(str(val))


# ── compute_roi_pct: scenariusze P1-016 ───────────────────────────────────────

def test_roi_negative_revenue_returns_none():
    """P1-016: revenue=-1500, replacement_value=500 → None (nie -300%)."""
    assert compute_roi_pct(d(-1500), d(500)) is None


def test_roi_negative_revenue_does_not_return_negative():
    """P1-016: żadna kombinacja ujemnego revenue nie daje ujemnego ROI."""
    assert compute_roi_pct(d(-1), d(500)) is None
    assert compute_roi_pct(d(-999999), d(1)) is None


def test_roi_zero_revenue_returns_zero():
    """P1-016: revenue=0, replacement_value=500 → 0.0 (nie None)."""
    result = compute_roi_pct(d(0), d(500))
    assert result == 0.0


def test_roi_positive_revenue_normal():
    """POPRAWNE: revenue=1500, replacement_value=500 → 300.0."""
    assert compute_roi_pct(d(1500), d(500)) == 300.0


def test_roi_replacement_value_zero_returns_none():
    """P1-016: replacement_value=0 → None (dzielenie przez zero)."""
    assert compute_roi_pct(d(1500), d(0)) is None


def test_roi_replacement_value_none_returns_none():
    """P1-016: replacement_value=None → None."""
    assert compute_roi_pct(d(1500), None) is None


def test_roi_both_none_returns_none():
    assert compute_roi_pct(None, None) is None


def test_roi_revenue_none_with_positive_rv_returns_zero():
    """revenue=None traktowane jak 0 → ROI=0.0."""
    assert compute_roi_pct(None, d(500)) == 0.0


def test_roi_negative_replacement_value_returns_none():
    """replacement_value<0 (anomalia) → None."""
    assert compute_roi_pct(d(1500), d(-500)) is None


def test_roi_rounding_two_decimals():
    """ROI zaokrąglone do 2 miejsców po przecinku."""
    # 1000 / 3 * 100 = 33333.333...
    assert compute_roi_pct(d(1000), d(3)) == 33333.33


def test_roi_negative_revenue_logs_warning(caplog):
    """P1-016: ujemny revenue loguje warning (audyt anomalii)."""
    with caplog.at_level(logging.WARNING, logger="stats.calc"):
        compute_roi_pct(d(-1500), d(500))
    assert any("Negative ROI clamped" in r.message for r in caplog.records)


# ── clamp_days: scenariusze P1-016 (date_to < date_from) ──────────────────────

def test_clamp_days_negative_returns_zero():
    """P1-016: days=-7 (date_to < date_from) → 0 (nie -7)."""
    assert clamp_days(-7) == 0


def test_clamp_days_negative_five_returns_zero():
    """P1-016: date_to=2026-01-10, date_from=2026-01-15 → -5 dni → 0."""
    assert clamp_days(-5) == 0


def test_clamp_days_zero_returns_zero():
    assert clamp_days(0) == 0


def test_clamp_days_positive_unchanged():
    assert clamp_days(30) == 30


def test_clamp_days_none_returns_zero():
    assert clamp_days(None) == 0


def test_clamp_days_negative_logs_warning(caplog):
    """P1-016: ujemne dni loguje warning."""
    with caplog.at_level(logging.WARNING, logger="stats.calc"):
        clamp_days(-7)
    assert any("Negative days clamped" in r.message for r in caplog.records)


# ── Integracja: machine_roi używa compute_roi_pct (source-level guard) ────────

def test_machine_roi_uses_compute_roi_pct():
    """Guard: stats/router.py machine_roi używa compute_roi_pct (nie inline)."""
    from pathlib import Path
    src = Path(__file__).resolve().parents[2].joinpath("stats", "router.py").read_text(encoding="utf-8")
    assert "compute_roi_pct" in src
    # stary inline pattern nie powinien już występować w machine_roi
    assert "round(float(revenue) / float(art.replacement_value) * 100, 2)" not in src


def test_machine_roi_clamps_days_sum():
    """Guard: stats/router.py machine_roi używa clamp_days w sumie dni."""
    from pathlib import Path
    src = Path(__file__).resolve().parents[2].joinpath("stats", "router.py").read_text(encoding="utf-8")
    assert "clamp_days" in src
