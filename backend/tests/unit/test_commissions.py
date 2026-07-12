"""Unit tests for salesperson commission calculation from company margin.

Prowizja liczona WYŁĄCZNIE od rzeczywistych rozliczeń (contract_settlements).
Brak fallbacku do szacunkowego przychodu z pozycji umowy.
Umowy bez rozliczeń nie wliczają się do prowizji.

    commission = margin * rate / 100

where margin = sum(cost_client - cost_company) from complete contract_settlements.
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


def _make_db(*, settlement_rows, settled_count_rows, salespeople_rows):
    """Build an AsyncMock db whose `execute` dispatches based on the SQL it runs.

    The /stats/commissions endpoint issues 3 sequential queries:
      1. settlement margins (group_by salesperson_id)
      2. settled contract counts (group_by salesperson_id)
      3. salespeople list
    """
    db = AsyncMock()

    settlement_all = [SimpleNamespace(all=lambda rows=settlement_rows: list(rows))]
    settled_count_all = [SimpleNamespace(all=lambda rows=settled_count_rows: list(rows))]
    salespeople_all = [SimpleNamespace(all=lambda rows=salespeople_rows: list(rows))]

    queue = [settlement_all[0], settled_count_all[0], salespeople_all[0]]

    def _execute(*args, **kwargs):
        return queue.pop(0)

    db.execute.side_effect = _execute
    return db


# ── Tests: /stats/commissions endpoint ───────────────────────────────────────

def test_commission_from_margin_not_revenue():
    """cost_client=1000, cost_company=400, rate=10% → commission=60 (not 100)."""
    db = _make_db(
        settlement_rows=[(7, Decimal("600.00"))],          # (salesperson_id, total_margin)
        settled_count_rows=[(7, 1)],                       # 1 settled contract
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
    )
    resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    body = resp.json()
    item = body["items"][0]
    assert item["salesperson_id"] == 7
    assert item["total_margin"] == "600.00"
    assert item["commission_amount"] == "60.00"          # 600 * 10 / 100
    assert item["contracts_count"] == 1
    assert body["grand_total_margin"] == "600.00"
    assert body["grand_total_commission"] == "60.00"


def test_no_settlement_means_zero_commission():
    """Brak rozliczenia → prowizja=0 (NIE fallback do revenue)."""
    db = _make_db(
        settlement_rows=[],                                # no settlement for sp 7
        settled_count_rows=[],                             # no settled contracts
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
    )
    resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["total_margin"] == "0.00"                 # base = 0, not revenue
    assert item["commission_amount"] == "0.00"            # 0 * 10 / 100
    assert item["contracts_count"] == 0


def test_complete_zero_margin_means_zero_commission():
    """Kompletna marża zero → commission=0 (autorytatywna, nie fallback)."""
    db = _make_db(
        settlement_rows=[(7, Decimal("0.00"))],           # complete settlement, margin=0
        settled_count_rows=[(7, 1)],
        salespeople_rows=[(7, "Handlowiec", Decimal("10.00"))],
    )
    resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    item = resp.json()["items"][0]
    assert item["total_margin"] == "0.00"                # base = margin (0)
    assert item["commission_amount"] == "0.00"           # 0 * 10 / 100
    assert item["contracts_count"] == 1


def test_grand_total_margin_sums_bases():
    """grand_total_margin sums each item's margin from settlements."""
    db = _make_db(
        settlement_rows=[(7, Decimal("600.00")), (8, Decimal("0.00"))],
        settled_count_rows=[(7, 1), (8, 1)],
        salespeople_rows=[(7, "A", Decimal("10.00")), (8, "B", Decimal("20.00"))],
    )
    resp = TestClient(_build_stats_app(db)).get("/stats/commissions")
    assert resp.status_code == 200
    body = resp.json()
    # sp 7: base=600 (margin), sp 8: base=0 (complete zero margin)
    assert body["grand_total_margin"] == "600.00"
    assert body["grand_total_commission"] == "60.00"
