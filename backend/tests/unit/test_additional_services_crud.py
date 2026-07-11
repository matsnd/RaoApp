"""RAO: testy CRUD AdditionalService (create/list/get/update/delete) — mockowane DB.

Wzorzec zgodny z tests/unit/test_services_crud.py (mockowany AsyncSession, Pydantic v2).
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError

# Rejestracja mapperów SQLAlchemy
import additional_services.models  # noqa: F401
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from additional_services.schemas import (
    AdditionalServiceCreate,
    AdditionalServiceUpdate,
    AdditionalServiceListItem,
)
from additional_services.service import AdditionalServiceService
from additional_services.models import AdditionalService


# ── AdditionalServiceCreate schema ───────────────────────────────────────────

def test_additional_service_create_minimal():
    s = AdditionalServiceCreate(name="Ubezpieczenie")
    assert s.name == "Ubezpieczenie"
    assert s.is_archival is False
    assert s.default_amount is None
    assert s.description is None


def test_additional_service_create_requires_name():
    with pytest.raises(ValidationError):
        AdditionalServiceCreate()  # type: ignore[call-arg]


def test_additional_service_create_name_max_length():
    with pytest.raises(ValidationError):
        AdditionalServiceCreate(name="x" * 201)


def test_additional_service_create_with_all_fields():
    s = AdditionalServiceCreate(
        name="Ubezpieczenie OC",
        default_amount=Decimal("150.00"),
        description="Ubezpieczenie maszyny",
        notes="Notatki",
        is_archival=False,
    )
    assert s.description == "Ubezpieczenie maszyny"
    assert s.default_amount == Decimal("150.00")


def test_additional_service_create_negative_amount_rejected():
    with pytest.raises(ValidationError):
        AdditionalServiceCreate(name="Test", default_amount=Decimal("-50"))


# ── AdditionalServiceUpdate schema ───────────────────────────────────────────

def test_additional_service_update_all_optional():
    u = AdditionalServiceUpdate()
    assert u.name is None
    assert u.description is None
    assert u.is_archival is None
    assert u.default_amount is None


def test_additional_service_update_partial_only_sent_fields():
    u = AdditionalServiceUpdate(notes="Nowe notatki")
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"notes": "Nowe notatki"}
    assert "name" not in dumped


# ── AdditionalServiceService.create_additional_service ────────────────────────

@pytest.mark.asyncio
async def test_create_additional_service_happy_path():
    svc = AdditionalServiceService()
    data = AdditionalServiceCreate(name="Ubezpieczenie")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 1
    db.refresh = AsyncMock(side_effect=fake_refresh)

    service = await svc.create_additional_service(db, data)

    assert service.name == "Ubezpieczenie"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_additional_service_sets_created_at():
    svc = AdditionalServiceService()
    data = AdditionalServiceCreate(name="Test")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 2
    db.refresh = AsyncMock(side_effect=fake_refresh)

    service = await svc.create_additional_service(db, data)
    assert service.created_at is not None


# ── AdditionalServiceService.get_additional_service ──────────────────────────

@pytest.mark.asyncio
async def test_get_additional_service_not_found_raises_404():
    from fastapi import HTTPException
    svc = AdditionalServiceService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.get_additional_service(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_additional_service_found():
    svc = AdditionalServiceService()
    db = AsyncMock()
    service = MagicMock(spec=AdditionalService)
    service.id = 5
    service.name = "Ubezpieczenie"
    result = MagicMock()
    result.scalar_one_or_none.return_value = service
    db.execute = AsyncMock(return_value=result)

    out = await svc.get_additional_service(db, 5)
    assert out.id == 5
    assert out.name == "Ubezpieczenie"


# ── AdditionalServiceService.update_additional_service ────────────────────────

@pytest.mark.asyncio
async def test_update_additional_service_partial():
    svc = AdditionalServiceService()

    existing = MagicMock(spec=AdditionalService)
    existing.id = 10
    existing.name = "Stary"
    existing.notes = None

    async def fake_get(db_arg, service_id):
        return existing
    svc.get_additional_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    data = AdditionalServiceUpdate(notes="Nowe notatki")
    updated = await svc.update_additional_service(db, 10, data)

    assert updated is existing
    assert existing.notes == "Nowe notatki"
    assert existing.name == "Stary"  # nie zmienione
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_additional_service_sets_updated_at():
    svc = AdditionalServiceService()

    existing = MagicMock(spec=AdditionalService)
    existing.id = 10
    existing.updated_at = None

    async def fake_get(db_arg, service_id):
        return existing
    svc.get_additional_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    await svc.update_additional_service(db, 10, AdditionalServiceUpdate(name="Nowa nazwa"))
    assert existing.updated_at is not None


# ── AdditionalServiceService.delete_additional_service ────────────────────────

@pytest.mark.asyncio
async def test_delete_additional_service_happy_path():
    svc = AdditionalServiceService()
    service = MagicMock(spec=AdditionalService)
    service.id = 5

    async def fake_get(db_arg, service_id):
        return service
    svc.get_additional_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    await svc.delete_additional_service(db, 5)

    db.delete.assert_called_once_with(service)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_additional_service_not_found_raises_404():
    from fastapi import HTTPException
    svc = AdditionalServiceService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_additional_service(db, 999)
    assert exc.value.status_code == 404


# ── AdditionalServiceService.list_additional_services ────────────────────────

@pytest.mark.asyncio
async def test_list_additional_services_empty():
    svc = AdditionalServiceService()
    db = AsyncMock()

    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(side_effect=[count_result, list_result])

    items, total = await svc.list_additional_services(db)
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_additional_services_with_data():
    svc = AdditionalServiceService()
    db = AsyncMock()

    s1 = MagicMock(spec=AdditionalService)
    s1.id = 1
    s1.name = "Ubezpieczenie A"
    s1.default_amount = Decimal("100.00")
    s1.description = "Opis"
    s1.is_archival = False
    s1.fakturownia_product_id = None
    s1.created_at = datetime.utcnow()
    s1.updated_at = None

    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = [s1]
    db.execute = AsyncMock(side_effect=[count_result, list_result])

    items, total = await svc.list_additional_services(db)
    assert total == 1
    assert len(items) == 1
    assert isinstance(items[0], AdditionalServiceListItem)
    assert items[0].name == "Ubezpieczenie A"
