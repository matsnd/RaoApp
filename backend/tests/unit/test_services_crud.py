"""RAO: testy CRUD Service (create/list/get/update/delete) — mockowane DB.

Wzorzec zgodny z tests/unit/test_machines_crud.py (mockowany AsyncSession, Pydantic v2).
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError

# Rejestracja mapperów SQLAlchemy
import services.models  # noqa: F401
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from services.schemas import ServiceCreate, ServiceUpdate, ServiceListItem
from services.service import ServiceService
from services.models import Service


# ── ServiceCreate schema ─────────────────────────────────────────────────────

def test_service_create_minimal():
    s = ServiceCreate(name="Transport")
    assert s.name == "Transport"
    assert s.is_archival is False
    assert s.description is None


def test_service_create_requires_name():
    with pytest.raises(ValidationError):
        ServiceCreate()  # type: ignore[call-arg]


def test_service_create_name_max_length():
    with pytest.raises(ValidationError):
        ServiceCreate(name="x" * 201)


def test_service_create_with_all_fields():
    s = ServiceCreate(
        name="Transport specjalny",
        description="Transport maszyn",
        notes="Notatki",
        replacement_value=10000,
        is_archival=False,
    )
    assert s.description == "Transport maszyn"
    assert s.replacement_value == 10000


# ── ServiceUpdate schema ─────────────────────────────────────────────────────

def test_service_update_all_optional():
    u = ServiceUpdate()
    assert u.name is None
    assert u.description is None
    assert u.is_archival is None


def test_service_update_partial_only_sent_fields():
    u = ServiceUpdate(notes="Nowe notatki")
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"notes": "Nowe notatki"}
    assert "name" not in dumped


# ── ServiceService.create_service ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_service_happy_path():
    svc = ServiceService()
    data = ServiceCreate(name="Transport")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 1
    db.refresh = AsyncMock(side_effect=fake_refresh)

    service = await svc.create_service(db, data)

    assert service.name == "Transport"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_service_sets_created_at():
    svc = ServiceService()
    data = ServiceCreate(name="Test")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 2
    db.refresh = AsyncMock(side_effect=fake_refresh)

    service = await svc.create_service(db, data)
    assert service.created_at is not None


# ── ServiceService.get_service ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_service_not_found_raises_404():
    from fastapi import HTTPException
    svc = ServiceService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.get_service(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_service_found():
    svc = ServiceService()
    db = AsyncMock()
    service = MagicMock(spec=Service)
    service.id = 5
    service.name = "Transport"
    result = MagicMock()
    result.scalar_one_or_none.return_value = service
    db.execute = AsyncMock(return_value=result)

    out = await svc.get_service(db, 5)
    assert out.id == 5
    assert out.name == "Transport"


# ── ServiceService.update_service ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_service_partial():
    svc = ServiceService()

    existing = MagicMock(spec=Service)
    existing.id = 10
    existing.name = "Stary"
    existing.notes = None

    async def fake_get(db_arg, service_id):
        return existing
    svc.get_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    data = ServiceUpdate(notes="Nowe notatki")
    updated = await svc.update_service(db, 10, data)

    assert updated is existing
    assert existing.notes == "Nowe notatki"
    assert existing.name == "Stary"  # nie zmienione
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_service_sets_updated_at():
    svc = ServiceService()

    existing = MagicMock(spec=Service)
    existing.id = 10
    existing.updated_at = None

    async def fake_get(db_arg, service_id):
        return existing
    svc.get_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    await svc.update_service(db, 10, ServiceUpdate(name="Nowa nazwa"))
    assert existing.updated_at is not None


# ── ServiceService.delete_service ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_service_happy_path():
    svc = ServiceService()
    service = MagicMock(spec=Service)
    service.id = 5

    async def fake_get(db_arg, service_id):
        return service
    svc.get_service = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    await svc.delete_service(db, 5)

    db.delete.assert_called_once_with(service)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_service_not_found_raises_404():
    from fastapi import HTTPException
    svc = ServiceService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_service(db, 999)
    assert exc.value.status_code == 404


# ── ServiceService.list_services ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_services_empty():
    svc = ServiceService()
    db = AsyncMock()

    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(side_effect=[count_result, list_result])

    items, total = await svc.list_services(db)
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_services_with_data():
    svc = ServiceService()
    db = AsyncMock()

    s1 = MagicMock(spec=Service)
    s1.id = 1
    s1.name = "Transport A"
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

    items, total = await svc.list_services(db)
    assert total == 1
    assert len(items) == 1
    assert isinstance(items[0], ServiceListItem)
    assert items[0].name == "Transport A"
