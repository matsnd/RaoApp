"""Unit and router tests for salesperson commission contract drill-down."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth.dependencies import get_current_user
from database import get_db
from stats.router import router as stats_router
from stats.service import calculate_commission_base, get_salesperson_commission_contracts


@pytest.fixture
def salesperson():
    return SimpleNamespace(id=7, name="Handlowiec", is_active=True, commission_rate=Decimal("10.00"))


def _settlement_row(*, client, company):
    return SimpleNamespace(
        contract_id=11,
        number="S/11",
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
        contractor_name_from_table=None,
        contractor_name_snapshot="ACME",
        commission_rate=Decimal("10.00"),
        settlement_client=client,
        settlement_company=company,
    )


def test_commission_is_based_on_company_earnings():
    _, _, base = calculate_commission_base(
        settlement_client=Decimal("1000.00"),
        settlement_company=Decimal("400.00"),
        fallback_revenue=Decimal("9999.00"),
    )
    assert base == Decimal("600.00")
    assert base * Decimal("10") / Decimal("100") == Decimal("60.00")


def test_complete_zero_margin_does_not_use_fallback():
    client, company, base = calculate_commission_base(
        settlement_client=Decimal("1000.00"),
        settlement_company=Decimal("1000.00"),
        fallback_revenue=Decimal("9999.00"),
    )
    assert (client, company, base) == (
        Decimal("1000.00"),
        Decimal("1000.00"),
        Decimal("0.00"),
    )


@pytest.mark.asyncio
async def test_drilldown_aggregates_two_complete_and_one_partial_settlement(salesperson):
    db = AsyncMock()
    db.scalar.return_value = salesperson
    db.execute.return_value = SimpleNamespace(all=lambda: [
        _settlement_row(client=Decimal("1000.00"), company=Decimal("400.00")),
        _settlement_row(client=Decimal("500.00"), company=Decimal("200.00")),
        _settlement_row(client=Decimal("900.00"), company=None),
    ])
    with patch("stats.service.compute_position_revenues", new=AsyncMock(return_value=[])):
        items = await get_salesperson_commission_contracts(
            db, 7, date(2026, 1, 1), date(2026, 1, 31)
        )
    assert items[0]["total_revenue"] == Decimal("1500.00")
    assert items[0]["total_company_cost"] == Decimal("600.00")
    assert items[0]["earnings"] == Decimal("900.00")
    assert items[0]["commission_amount"] == Decimal("90.00")
    assert items[0]["fallback_applied"] is False


@pytest.mark.asyncio
async def test_drilldown_complete_zero_margin_does_not_fallback(salesperson):
    db = AsyncMock()
    db.scalar.return_value = salesperson
    db.execute.return_value = SimpleNamespace(all=lambda: [
        _settlement_row(client=Decimal("1000.00"), company=Decimal("1000.00")),
    ])
    with patch("stats.service.compute_position_revenues", new=AsyncMock(return_value=[
        {"contract_id": 11, "revenue": Decimal("5000.00")},
    ])):
        items = await get_salesperson_commission_contracts(db, 7, None, date(2026, 1, 31))
    assert items[0]["earnings"] == Decimal("0.00")
    assert items[0]["commission_amount"] == Decimal("0.00")
    assert items[0]["fallback_applied"] is False


@pytest.mark.asyncio
async def test_drilldown_marks_revenue_fallback_when_no_complete_settlement(salesperson):
    db = AsyncMock()
    db.scalar.return_value = salesperson
    db.execute.return_value = SimpleNamespace(all=lambda: [
        _settlement_row(client=Decimal("500.00"), company=None),
    ])
    with patch("stats.service.compute_position_revenues", new=AsyncMock(return_value=[
        {"contract_id": 11, "revenue": Decimal("500.00")}
    ])):
        items = await get_salesperson_commission_contracts(db, 7, None, date(2026, 1, 31))
    assert items[0]["total_revenue"] == Decimal("500.00")
    assert items[0]["total_company_cost"] == Decimal("0.00")
    assert items[0]["earnings"] == Decimal("500.00")
    assert items[0]["commission_amount"] == Decimal("50.00")
    assert items[0]["fallback_applied"] is True


@pytest.mark.asyncio
async def test_drilldown_rejects_missing_salesperson():
    db = AsyncMock()
    db.scalar.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_salesperson_commission_contracts(db, 999, None, date(2026, 1, 31))
    assert exc.value.status_code == 404


def _build_stats_app(db, *, authenticated=True):
    app = FastAPI()
    app.include_router(stats_router)

    async def override_db():
        return db

    app.dependency_overrides[get_db] = override_db
    if authenticated:
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    return app


def test_endpoint_returns_contract_items_and_totals(salesperson):
    db = AsyncMock()
    db.scalar.return_value = salesperson
    db.execute.return_value = SimpleNamespace(all=lambda: [
        _settlement_row(client=Decimal("1000.00"), company=Decimal("400.00")),
        _settlement_row(client=Decimal("500.00"), company=Decimal("200.00")),
        _settlement_row(client=Decimal("900.00"), company=None),
    ])
    with patch("stats.service.compute_position_revenues", new=AsyncMock(return_value=[])):
        response = TestClient(_build_stats_app(db)).get(
            "/stats/commissions/7/contracts?date_from=2026-01-01&date_to=2026-01-31"
        )
    assert response.status_code == 200
    body = response.json()
    assert body["salesperson_id"] == 7
    assert body["salesperson_name"] == "Handlowiec"
    assert body["items"][0]["earnings"] == "900.00"
    assert body["items"][0]["fallback_applied"] is False
    assert body["total_revenue"] == "1500.00"
    assert body["total_company_cost"] == "600.00"
    assert body["total_earnings"] == "900.00"
    assert body["total_commission"] == "90.00"


@pytest.mark.parametrize("salesperson_value", [
    None,
    SimpleNamespace(id=7, name="Nieaktywny", is_active=False),
])
def test_endpoint_returns_404_for_missing_or_inactive_salesperson(salesperson_value):
    db = AsyncMock()
    db.scalar.return_value = salesperson_value
    response = TestClient(_build_stats_app(db)).get("/stats/commissions/999/contracts")
    assert response.status_code == 404
    assert response.json()["detail"] == "Handlowiec nie istnieje"


def test_endpoint_returns_401_without_authentication():
    response = TestClient(_build_stats_app(AsyncMock(), authenticated=False)).get(
        "/stats/commissions/7/contracts"
    )
    assert response.status_code == 401
