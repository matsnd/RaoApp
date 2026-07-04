"""Unit tests for RAO-P2-058 Faza 1: sync_products + search_products (cache).

Tests cover:
- sync_products: happy path (paginated fetch + atomic upsert), empty catalogue, FA disabled
- search_products: LIKE %q% on name/code, empty query, no results, limit clamp
"""
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from integrations.fakturownia.schemas import (
    FakturowniaProductOut,
    SyncProductsResultOut,
)
from integrations.fakturownia import service


def _make_product(pid: int, name: str = "Koparka", code: str = "KOP-1") -> FakturowniaProductOut:
    return FakturowniaProductOut(
        id=pid,
        name=name,
        code=code,
        price_net=Decimal("100.00"),
        currency="PLN",
        tax="23",
        gtu_code="GTU_01",
        pkwiu="43.99.20.0",
    )


def _make_db() -> MagicMock:
    """Mock AsyncSession with execute/commit."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


# -- sync_products -------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_products_happy_path():
    """Sync 3 products from FA -> upsert called once with 3 rows."""
    db = _make_db()
    products = [_make_product(1), _make_product(2), _make_product(3)]

    with patch.object(service, "get_or_create_settings", new=AsyncMock()), \
         patch.object(service, "_build_client") as mock_build:
        mock_client = MagicMock()
        mock_client.get_all_products = AsyncMock(return_value=(products, 1))
        mock_build.return_value = mock_client

        result = await service.sync_products(db)

    assert isinstance(result, SyncProductsResultOut)
    assert result.fetched == 3
    assert result.upserted == 3
    assert result.pages == 1
    assert db.execute.await_count == 1
    assert db.commit.await_count == 1


@pytest.mark.asyncio
async def test_sync_products_empty_catalogue():
    """FA returns 0 products -> no upsert, returns zeros."""
    db = _make_db()

    with patch.object(service, "get_or_create_settings", new=AsyncMock()), \
         patch.object(service, "_build_client") as mock_build:
        mock_client = MagicMock()
        mock_client.get_all_products = AsyncMock(return_value=([], 0))
        mock_build.return_value = mock_client

        result = await service.sync_products(db)

    assert result.fetched == 0
    assert result.upserted == 0
    assert result.pages == 0
    db.execute.assert_not_awaited()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_sync_products_fa_disabled_raises_503():
    """_build_client raises 503 when integration disabled -> propagates."""
    db = _make_db()
    from fastapi import HTTPException

    with patch.object(service, "get_or_create_settings", new=AsyncMock()), \
         patch.object(service, "_build_client", side_effect=HTTPException(status_code=503, detail="off")):
        with pytest.raises(HTTPException) as exc:
            await service.sync_products(db)
        assert exc.value.status_code == 503


# -- search_products -----------------------------------------------------------


def _make_cache_row(pid: int, name: str, code: str = "KOP-1") -> SimpleNamespace:
    """Mimic a FakturowniaProductCache ORM row (avoids SQLAlchemy mapper config)."""
    return SimpleNamespace(
        id=pid,
        product_id=pid,
        code=code,
        name=name,
        price_net=Decimal("100.00"),
        currency="PLN",
        tax_rate="23",
        gtu_code="GTU_01",
        pkwiu="43.99.20.0",
        synced_at=datetime(2026, 7, 1, 12, 0, 0),
    )


@pytest.mark.asyncio
async def test_search_products_happy_path():
    """Search 'kop' -> returns 2 matching products from cache."""
    db = MagicMock()
    rows = [_make_cache_row(1, "Koparka gasienicowa"), _make_cache_row(2, "Kopiarka")]
    scalars_result = MagicMock()
    scalars_result.scalars.return_value.all.return_value = rows
    db.execute = AsyncMock(return_value=scalars_result)

    out = await service.search_products(db, "kop")

    assert len(out) == 2
    assert out[0].product_id == 1
    assert out[0].name == "Koparka gasienicowa"
    assert out[0].tax_rate == "23"
    assert out[0].gtu_code == "GTU_01"


@pytest.mark.asyncio
async def test_search_products_empty_query_returns_empty():
    """Empty/whitespace query -> returns [] without DB call."""
    db = MagicMock()
    db.execute = AsyncMock()

    out = await service.search_products(db, "   ")

    assert out == []
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_products_no_results():
    """Query matches nothing -> returns empty list."""
    db = MagicMock()
    scalars_result = MagicMock()
    scalars_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=scalars_result)

    out = await service.search_products(db, "nieistniejacy")

    assert out == []


@pytest.mark.asyncio
async def test_search_products_respects_limit():
    """Limit param passed to query - verify execute called (limit applied in SQL)."""
    db = MagicMock()
    scalars_result = MagicMock()
    scalars_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=scalars_result)

    await service.search_products(db, "test", limit=10)

    db.execute.assert_awaited_once()
