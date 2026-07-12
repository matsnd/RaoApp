"""Unit tests for salesperson commission calculation from company margin (RAO-P1-130).

Covers the unified commission formula used by both `/stats/commissions` and
`generate_commissions_pdf`:

    commission = base * rate / 100

where base = margin (cost_client - cost_company from complete contract_settlements)
when a complete settlement exists for the salesperson, otherwise falls back to
revenue computed from contract positions. A complete margin equal to zero does
NOT trigger the fallback.
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.dependencies import get_current_user
from database import get_db
from stats.router import router as stats_router


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sp(id_, name, rate):
    return SimpleNamespace(id=id_, name=name, is_active=True, commission_rate=rate)


def _build_stats_app(db):
    app = FastAPI()
    app.include_router(stats_router)

    async def override_db():
        return db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    return app


def _make_db(*, settlement_rows, salespeople_rows, contract_sp_rows, position_rows):
    """Build an AsyncMock db whose `execute` dispatches based on the SQL it runs.

    The /stats/commissions endpoint issues several sequential queries:
      1. settlement margins (group_by salesperson_id)
      2. salespeople list
      3. contract -> salesperson map
    plus the patched _compute_position_revenues helper.
    """
    db = AsyncMock()

    settlement_all = [SimpleNamespace(all=lambda rows=settlement_rows: list(rows))]
    salespeople_all = [SimpleNamespace(all=lambda rows=salespeople_rows: list(rows))]
    contract_sp_all = [SimpleNamespace(all=lambda rows=contract_sp_rows: list(rows))]

    queue = [settlement_all[0], salespeople_all[0], contract_sp_all[0]]

    def _execute(*args, **kwargs):
        return queue.pop(0)

    db.execute.side_effect = _execute
    return db


# ── Tests: /stats/commissions endpoint ───────────────────────────────────────

def test_commission_from_margin_not_revenue():
    """cost_client=1000, cost_company=400, rate=10% → commission=60 (not 100)."""
    db = _make_db(
        settlement_rows=[(7, Decimal("600.00"))],          # (salesperson_id, total_margin)
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
        contract_sp_rows=[(11, 7)],
        position_rows=[{"contract_id": 11, "revenue": Decimal("1000.00")}],
    )
    with patch("stats.router._compute_position_revenues",
               new=AsyncMock(return_value=[{"contract_id": 11, "revenue": Decimal("1000.00")}])):
        resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    body = resp.json()
    item = body["items"][0]
    assert item["salesperson_id"] == 7
    assert item["total_margin"] == "600.00"
    assert item["commission_amount"] == "60.00"          # 600 * 10 / 100
    assert item["total_revenue"] == "1000.00"            # revenue still reported
    assert body["grand_total_margin"] == "600.00"
    assert body["grand_total_commission"] == "60.00"


def test_commission_fallback_to_revenue_when_no_complete_settlement():
    """Brak kompletnego settlementu → fallback do revenue z pozycji umowy."""
    db = _make_db(
        settlement_rows=[],                               # no complete settlement for sp 7
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
        contract_sp_rows=[(11, 7)],
        position_rows=[{"contract_id": 11, "revenue": Decimal("1000.00")}],
    )
    with patch("stats.router._compute_position_revenues",
               new=AsyncMock(return_value=[{"contract_id": 11, "revenue": Decimal("1000.00")}])):
        resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["total_margin"] == "1000.00"             # base = revenue in fallback
    assert item["commission_amount"] == "100.00"         # 1000 * 10 / 100


def test_complete_zero_margin_does_not_trigger_fallback():
    """Kompletna marża zero → commission=0 (nie fallback do revenue)."""
    db = _make_db(
        settlement_rows=[(7, Decimal("0.00"))],           # complete settlement, margin=0
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
        contract_sp_rows=[(11, 7)],
        position_rows=[{"contract_id": 11, "revenue": Decimal("9999.00")}],
    )
    with patch("stats.router._compute_position_revenues",
               new=AsyncMock(return_value=[{"contract_id": 11, "revenue": Decimal("9999.00")}])):
        resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["total_margin"] == "0.00"                # base = margin (0), not revenue
    assert item["commission_amount"] == "0.00"           # 0 * 10 / 100
    assert item["total_revenue"] == "9999.00"            # revenue still reported separately


def test_grand_total_margin_sums_bases():
    """grand_total_margin sums each item's base (margin or revenue in fallback)."""
    db = _make_db(
        settlement_rows=[(7, Decimal("600.00")), (8, Decimal("0.00"))],
        salespeople_rows=[(7, "A", Decimal("10.00")), (8, "B", Decimal("20.00"))],
        contract_sp_rows=[(11, 7), (12, 8)],
        position_rows=[],
    )
    with patch("stats.router._compute_position_revenues",
               new=AsyncMock(return_value=[
                   {"contract_id": 11, "revenue": Decimal("1000.00")},
                   {"contract_id": 12, "revenue": Decimal("500.00")},
               ])):
        resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    body = resp.json()
    # sp 7: base=600 (margin), sp 8: base=0 (complete zero margin, no fallback)
    assert body["grand_total_margin"] == "600.00"
    assert body["grand_total_commission"] == "60.00"
