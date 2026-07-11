"""RAO: testy CRUD Machine (create/list/get/update/delete/duplicate) — mockowane DB.

Wzorzec zgodny z tests/unit/test_categories.py (mockowany AsyncSession, Pydantic v2).
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError

# Rejestracja mapperów SQLAlchemy
import machines.models  # noqa: F401
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from machines.schemas import MachineCreate, MachineUpdate, MachineListItem
from machines.service import MachineService
from machines.models import Machine


# ── MachineCreate schema ─────────────────────────────────────────────────────

def test_machine_create_minimal():
    m = MachineCreate(name="Koparka X")
    assert m.name == "Koparka X"
    assert m.is_archival is False
    assert m.is_external is False
    assert m.power_type == "other"


def test_machine_create_requires_name():
    with pytest.raises(ValidationError):
        MachineCreate()  # type: ignore[call-arg]


def test_machine_create_name_max_length():
    with pytest.raises(ValidationError):
        MachineCreate(name="x" * 201)


def test_machine_create_with_all_fields():
    m = MachineCreate(
        name="Koparka Diesel",
        internal_number="K001",
        registration_no="WX12345",
        serial_no="SN-001",
        brand="JCB",
        model="8035",
        replacement_value=500000,
        power_type="diesel",
        is_external=False,
    )
    assert m.brand == "JCB"
    assert m.power_type == "diesel"


# ── MachineUpdate schema ─────────────────────────────────────────────────────

def test_machine_update_all_optional():
    u = MachineUpdate()
    assert u.name is None
    assert u.power_type is None
    assert u.is_archival is None


def test_machine_update_partial_only_sent_fields():
    u = MachineUpdate(notes="Nowe notatki")
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"notes": "Nowe notatki"}
    assert "name" not in dumped
    assert "power_type" not in dumped


# ── MachineService.create_machine ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_machine_happy_path():
    svc = MachineService()
    data = MachineCreate(name="Koparka", power_type="diesel")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 1
    db.refresh = AsyncMock(side_effect=fake_refresh)

    machine = await svc.create_machine(db, data)

    assert machine.name == "Koparka"
    assert machine.power_type == "diesel"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_machine_sets_created_at():
    svc = MachineService()
    data = MachineCreate(name="Test")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 2
    db.refresh = AsyncMock(side_effect=fake_refresh)

    machine = await svc.create_machine(db, data)
    assert machine.created_at is not None


# ── MachineService.get_machine ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_machine_not_found_raises_404():
    from fastapi import HTTPException
    svc = MachineService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.get_machine(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_machine_found():
    svc = MachineService()
    db = AsyncMock()
    machine = MagicMock(spec=Machine)
    machine.id = 5
    machine.name = "Koparka"
    result = MagicMock()
    result.scalar_one_or_none.return_value = machine
    db.execute = AsyncMock(return_value=result)

    out = await svc.get_machine(db, 5)
    assert out.id == 5
    assert out.name == "Koparka"


# ── MachineService.update_machine ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_machine_partial():
    svc = MachineService()

    existing = MagicMock(spec=Machine)
    existing.id = 10
    existing.name = "Stara"
    existing.notes = None

    async def fake_get(db_arg, machine_id):
        return existing
    svc.get_machine = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    data = MachineUpdate(notes="Nowe notatki")
    updated = await svc.update_machine(db, 10, data)

    assert updated is existing
    assert existing.notes == "Nowe notatki"
    assert existing.name == "Stara"  # nie zmienione
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_machine_sets_updated_at():
    svc = MachineService()

    existing = MagicMock(spec=Machine)
    existing.id = 10
    existing.updated_at = None

    async def fake_get(db_arg, machine_id):
        return existing
    svc.get_machine = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    await svc.update_machine(db, 10, MachineUpdate(name="Nowa nazwa"))
    assert existing.updated_at is not None


# ── MachineService.delete_machine ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_machine_happy_path():
    svc = MachineService()
    machine = MagicMock(spec=Machine)
    machine.id = 5

    async def fake_get(db_arg, machine_id):
        return machine
    svc.get_machine = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    await svc.delete_machine(db, 5)

    db.delete.assert_called_once_with(machine)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_machine_not_found_raises_404():
    from fastapi import HTTPException
    svc = MachineService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_machine(db, 999)
    assert exc.value.status_code == 404


# ── MachineService.duplicate_machine ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_machine_copies_fields():
    svc = MachineService()

    original = MagicMock(spec=Machine)
    original.id = 10
    original.name = "Koparka"
    original.internal_number = "K001"
    original.registration_no = "WX123"
    original.serial_no = "SN-001"
    original.brand = "JCB"
    original.model = "8035"
    original.replacement_value = 500000
    original.category_id = 1
    original.owner_id = 2
    original.branch_id = 1
    original.description = "Opis"
    original.notes = "Notatki"
    original.rental_days = 30
    original.is_external = False
    original.is_archival = False
    original.power_type = "diesel"
    original.technical_attributes = {"foo": "bar"}
    original.reach_m = 10
    original.capacity_t = 5
    original.accessories = "akcesoria"

    async def fake_get(db_arg, machine_id):
        return original
    svc.get_machine = AsyncMock(side_effect=fake_get)

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 20
    db.refresh = AsyncMock(side_effect=fake_refresh)

    copy = await svc.duplicate_machine(db, 10)

    assert copy.name == "Koparka (kopia)"
    assert copy.brand == "JCB"
    assert copy.power_type == "diesel"
    # registration_no and serial_no should be cleared
    assert copy.registration_no is None
    assert copy.serial_no is None
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ── MachineService.list_machines ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_machines_empty():
    svc = MachineService()
    db = AsyncMock()

    # 1 execute = count, 2 = list
    count_result = MagicMock()
    count_result.scalar_one.return_value = 0
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(side_effect=[count_result, list_result])

    items, total = await svc.list_machines(db)
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_machines_with_data():
    svc = MachineService()
    db = AsyncMock()

    m1 = MagicMock(spec=Machine)
    m1.id = 1
    m1.name = "Koparka A"
    m1.internal_number = "K001"
    m1.registration_no = None
    m1.serial_no = None
    m1.brand = None
    m1.model = None
    m1.replacement_value = None
    m1.category_id = None
    m1.owner_id = None
    m1.is_archival = False
    m1.is_external = False
    m1.category_main = None
    m1.fakturownia_product_id = None
    m1.notes = None
    m1.created_at = datetime.utcnow()
    m1.updated_at = None

    count_result = MagicMock()
    count_result.scalar_one.return_value = 1
    list_result = MagicMock()
    list_result.scalars.return_value.all.return_value = [m1]
    db.execute = AsyncMock(side_effect=[count_result, list_result])

    items, total = await svc.list_machines(db)
    assert total == 1
    assert len(items) == 1
    assert isinstance(items[0], MachineListItem)
    assert items[0].name == "Koparka A"
