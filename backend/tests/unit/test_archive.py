"""RAO-P2-062 Faza 1 - testy unit dla archive service (mockowane DB).

Pokrycie:
  - list_archive_contracts z filtrami (search, contractor_id, contract_type, date range)
  - get_archive_contract z positions/conditions/service_fees/settlements
  - CRUD archive_categories (create, update, delete, duplikat detection, children guard)
  - update_archive_article_category (PATCH + walidacja FK category)
  - stats summary (revenue_estimate = unit_price * days * qty)
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

import archive.models  # noqa: F401 - inicjalizacja mapperow
from archive.schemas import (
    ArchiveArticleCategoryUpdate,
    ArchiveCategoryCreate,
    ArchiveContractListItem,
)
from archive import service


# ── Pydantic schemas ─────────────────────────────────────────────────────────

def test_archive_category_create_minimal():
    c = ArchiveCategoryCreate(name="Koparki")
    assert c.name == "Koparki"
    assert c.parent_id is None
    assert c.level == "main"


def test_archive_category_create_invalid_level():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ArchiveCategoryCreate(name="X", level="sub9")


def test_archive_article_category_update_accepts_none():
    p = ArchiveArticleCategoryUpdate(category_id=None)
    assert p.category_id is None


def test_archive_article_category_update_accepts_int():
    p = ArchiveArticleCategoryUpdate(category_id=42)
    assert p.category_id == 42


# ── list_archive_contracts ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_archive_contracts_returns_items_and_total():
    contract = MagicMock()
    contract.id = 1
    contract.contractor_id = 10
    contract.contractor_name = "Firma XYZ"
    contract.number = "S001/2026"
    contract.contract_type = "S"
    contract.delivery_address = None
    contract.postal_code = None
    contract.city = None
    contract.date_from = date(2026, 1, 1)
    contract.date_to = date(2026, 1, 10)
    contract.prepayment_amount = None
    contract.notes = None
    contract.email = None
    contract.contact_person1 = None
    contract.contact_phone1 = None
    contract.phone = None
    contract.is_settled = False
    contract.settled_at = None
    contract.position_count = 2
    contract.created_at = datetime(2026, 1, 1)

    db = AsyncMock()
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        # 1 = count, 2 = lista kontraktow, 3 = pozycje (puste — brak revenue_estimate)
        if len(calls) == 1:
            result.scalar_one.return_value = 1
        elif len(calls) == 2:
            scalars = MagicMock()
            scalars.all.return_value = [contract]
            result.scalars.return_value = scalars
        else:
            scalars = MagicMock()
            scalars.all.return_value = []  # brak pozycji
            result.scalars.return_value = scalars
        return result

    db.execute = mock_execute

    items, total = await service.list_archive_contracts(
        db, search="Firma", contractor_id=10, contract_type="S",
        date_from=date(2026, 1, 1), date_to=date(2026, 1, 31),
        page=1, per_page=50,
    )
    assert total == 1
    assert len(items) == 1
    assert isinstance(items[0], ArchiveContractListItem)
    assert items[0].number == "S001/2026"
    assert items[0].type_label == "Umowa najmu"
    assert items[0].duration_days == 9


@pytest.mark.asyncio
async def test_list_archive_contracts_empty():
    db = AsyncMock()
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one.return_value = 0
        else:
            scalars = MagicMock()
            scalars.all.return_value = []
            result.scalars.return_value = scalars
        return result

    db.execute = mock_execute
    items, total = await service.list_archive_contracts(db)
    assert items == []
    assert total == 0


# ── get_archive_contract ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_archive_contract_not_found():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    with pytest.raises(HTTPException) as exc:
        await service.get_archive_contract(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_archive_contract_found():
    contract = MagicMock()
    contract.id = 5
    contract.positions = []
    contract.service_fees = []
    contract.settlements = []
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = contract
    db.execute = AsyncMock(return_value=result_mock)
    out = await service.get_archive_contract(db, 5)
    assert out.id == 5


# ── create_archive_category ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_archive_category_normalizes_name():
    svc_data = ArchiveCategoryCreate(name="  Koparki  gąsienicowe ")
    db = AsyncMock()
    added = []

    def mock_add(obj):
        # Symulacja nadania id przez DB
        obj.id = 7
        added.append(obj)

    db.add = MagicMock(side_effect=mock_add)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    existing_result = MagicMock()
    existing_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=existing_result)

    result = await service.create_archive_category(db, svc_data)

    # Nazwa znormalizowana (collapse whitespace, trim)
    assert len(added) == 1
    assert added[0].name == "Koparki gąsienicowe"
    assert result.id == 7
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_archive_category_rejects_empty_name():
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        await service.create_archive_category(db, ArchiveCategoryCreate(name="   "))
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_archive_category_detects_duplicate():
    db = AsyncMock()
    existing = MagicMock()
    existing.name = "Koparki"
    existing_result = MagicMock()
    existing_result.scalars.return_value.all.return_value = [existing]
    db.execute = AsyncMock(return_value=existing_result)

    with pytest.raises(HTTPException) as exc:
        await service.create_archive_category(db, ArchiveCategoryCreate(name="koparki"))
    assert exc.value.status_code == 409
    assert "istnieje" in exc.value.detail


# ── update_archive_category ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_archive_category_not_found():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    with pytest.raises(HTTPException) as exc:
        await service.update_archive_category(db, 999, ArchiveCategoryCreate(name="X"))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_archive_category_duplicate_in_hierarchy():
    cat = MagicMock()
    cat.id = 1
    other = MagicMock()
    other.name = "Ladowarki"
    db = AsyncMock()

    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = cat
        else:
            result.scalars.return_value.all.return_value = [other]
        return result

    db.execute = mock_execute
    with pytest.raises(HTTPException) as exc:
        await service.update_archive_category(db, 1, ArchiveCategoryCreate(name="ladowarki"))
    assert exc.value.status_code == 409


# ── delete_archive_category ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_archive_category_not_found():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    with pytest.raises(HTTPException) as exc:
        await service.delete_archive_category(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_archive_category_with_children_409():
    db = AsyncMock()
    cat = MagicMock()
    cat.id = 1
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = cat
        elif len(calls) == 2:
            result.scalar_one_or_none.return_value = 99  # child id
        return result

    db.execute = mock_execute
    with pytest.raises(HTTPException) as exc:
        await service.delete_archive_category(db, 1)
    assert exc.value.status_code == 409
    assert "podkategorie" in exc.value.detail


@pytest.mark.asyncio
async def test_delete_archive_category_with_articles_409():
    db = AsyncMock()
    cat = MagicMock()
    cat.id = 1
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = cat
        elif len(calls) == 2:
            result.scalar_one_or_none.return_value = None  # brak dzieci
        else:
            result.scalar_one.return_value = 3  # 3 artykuly
        return result

    db.execute = mock_execute
    with pytest.raises(HTTPException) as exc:
        await service.delete_archive_category(db, 1)
    assert exc.value.status_code == 409
    assert "artykuly" in exc.value.detail


@pytest.mark.asyncio
async def test_delete_archive_category_leaf_ok():
    db = AsyncMock()
    cat = MagicMock()
    cat.id = 1
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = cat
        elif len(calls) == 2:
            result.scalar_one_or_none.return_value = None
        else:
            result.scalar_one.return_value = 0  # 0 artykulow
        return result

    db.execute = mock_execute
    db.commit = AsyncMock()
    await service.delete_archive_category(db, 1)
    db.commit.assert_called_once()


# ── update_archive_article_category ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_archive_article_category_not_found():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)
    with pytest.raises(HTTPException) as exc:
        await service.update_archive_article_category(db, 999, ArchiveArticleCategoryUpdate(category_id=1))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_archive_article_category_invalid_category_404():
    article = MagicMock()
    article.id = 1
    article.category_id = None
    db = AsyncMock()
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = article
        else:
            result.scalar_one_or_none.return_value = None  # kategoria nie istnieje
        return result

    db.execute = mock_execute
    with pytest.raises(HTTPException) as exc:
        await service.update_archive_article_category(db, 1, ArchiveArticleCategoryUpdate(category_id=999))
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_archive_article_category_ok():
    article = MagicMock()
    article.id = 1
    article.category_id = 5
    db = AsyncMock()
    calls = []

    async def mock_execute(stmt):
        calls.append(stmt)
        result = MagicMock()
        if len(calls) == 1:
            result.scalar_one_or_none.return_value = article
        else:
            result.scalar_one_or_none.return_value = MagicMock()  # kategoria istnieje
        return result

    db.execute = mock_execute
    db.commit = AsyncMock()

    async def mock_refresh(a):
        a.category_id = 5
    db.refresh = AsyncMock(side_effect=mock_refresh)

    out = await service.update_archive_article_category(db, 1, ArchiveArticleCategoryUpdate(category_id=5))
    assert out.category_id == 5
    db.commit.assert_called_once()


# ── get_archive_stats_summary ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_stats_summary_empty():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result_mock)

    summary = await service.get_archive_stats_summary(db)
    assert summary.contracts_count == 0
    assert summary.positions_count == 0
    assert summary.revenue_estimate == Decimal("0.00")


@pytest.mark.asyncio
async def test_archive_stats_summary_with_unit_price():
    """Pozycja z unit_price=100, days=5, qty=2 -> revenue = 100*5*2 = 1000."""
    article = MagicMock()
    article.is_service = False
    pos = MagicMock()
    pos.contract_id = 1
    pos.article_id = 1
    pos.rental_days = 5
    pos.quantity = 2
    pos.unit_price = Decimal("100.00")
    pos.billing_frequency = "dziennie"
    pos.conditions = []
    pos.article = article

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [pos]
    db.execute = AsyncMock(return_value=result_mock)

    summary = await service.get_archive_stats_summary(db)
    assert summary.positions_count == 1
    assert summary.contracts_count == 1
    assert summary.revenue_estimate == Decimal("1000.00")
