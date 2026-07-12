"""
Unit testy dla RAO-P1-016: defensive clamp dla dni.

Reprodukuje i fixuje bug P1-016 (statystyki -7 dni):
- date_to < date_from → dni = 0 (nie -7)

Testowane funkcje (stats/calc.py):
- clamp_days(days)

ROI i compute_roi_pct usunięte — statystyki bez szacunkowych wartości.
"""
import logging

import pytest

from stats.calc import clamp_days


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
