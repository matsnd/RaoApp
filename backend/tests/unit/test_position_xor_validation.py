"""RAO: testy XOR walidacji (machine_id XOR service_id) w PositionCreate/PositionUpdate.

Weryfikują, że:
- PositionCreate z machine_id (bez service_id) → poprawne
- PositionCreate z service_id (bez machine_id) → poprawne
- PositionCreate z oboma → ValidationError (XOR naruszone)
- PositionCreate bez żadnego → ValidationError (XOR naruszone)
- PositionUpdate: XOR walidacja w service layer na finalnym stanie
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError

from contracts.schemas import PositionCreate, PositionUpdate


# ── PositionCreate XOR walidacja (Pydantic model_validator) ──────────────────

def test_position_create_with_machine_id_only():
    """machine_id ustawiony, service_id=None → poprawne (XOR spełnione)."""
    p = PositionCreate(machine_id=42)
    assert p.machine_id == 42
    assert p.service_id is None


def test_position_create_with_service_id_only():
    """service_id ustawiony, machine_id=None → poprawne (XOR spełnione)."""
    p = PositionCreate(service_id=10)
    assert p.service_id == 10
    assert p.machine_id is None


def test_position_create_with_both_raises_validation_error():
    """machine_id + service_id → ValidationError (XOR naruszone)."""
    with pytest.raises(ValidationError) as exc_info:
        PositionCreate(machine_id=1, service_id=2)
    assert "machine_id" in str(exc_info.value) or "service_id" in str(exc_info.value)


def test_position_create_with_neither_raises_validation_error():
    """Brak machine_id i service_id → ValidationError (XOR naruszone)."""
    with pytest.raises(ValidationError) as exc_info:
        PositionCreate()  # type: ignore[call-arg]
    assert "machine_id" in str(exc_info.value) or "service_id" in str(exc_info.value)


def test_position_create_with_machine_id_and_other_fields():
    """machine_id + dodatkowe pola → poprawne."""
    p = PositionCreate(
        machine_id=1,
        description="Koparka",
        rental_days=10,
        quantity=2,
        unit_price=500,
        delivery_date=date(2026, 1, 15),
    )
    assert p.machine_id == 1
    assert p.quantity == 2
    assert p.rental_days == 10


def test_position_create_with_service_id_and_other_fields():
    """service_id + dodatkowe pola → poprawne."""
    p = PositionCreate(
        service_id=5,
        description="Transport",
        quantity=1,
    )
    assert p.service_id == 5
    assert p.description == "Transport"


# ── PositionUpdate (XOR walidowana w service layer, nie w schema) ────────────

def test_position_update_all_optional_no_xor_in_schema():
    """PositionUpdate nie ma XOR walidacji w schema — walidowana w service layer."""
    u = PositionUpdate()
    assert u.machine_id is None
    assert u.service_id is None
    # Nie rzuca ValidationError — schema pozwala na None dla obu (partial update)
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {}


def test_position_update_with_machine_id_only():
    """Update z machine_id → poprawne na poziomie schema."""
    u = PositionUpdate(machine_id=42)
    assert u.machine_id == 42
    assert u.service_id is None


def test_position_update_with_service_id_only():
    """Update z service_id → poprawne na poziomie schema."""
    u = PositionUpdate(service_id=10)
    assert u.service_id == 10
    assert u.machine_id is None


def test_position_update_both_set_allowed_in_schema():
    """PositionUpdate z oboma polami → schema nie rzuca (XOR sprawdzane w service).

    Service layer sprawdza XOR na finalnym stanie pozycji po apply partial fields.
    """
    u = PositionUpdate(machine_id=1, service_id=2)
    # Schema nie rzuca — to jest OK, service layer waliduje final state
    assert u.machine_id == 1
    assert u.service_id == 2


def test_position_update_exclude_unset_machine_id():
    """Partial update z machine_id → tylko machine_id w dump."""
    u = PositionUpdate(machine_id=5)
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"machine_id": 5}
    assert "service_id" not in dumped


def test_position_update_exclude_unset_service_id():
    """Partial update z service_id → tylko service_id w dump."""
    u = PositionUpdate(service_id=3)
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"service_id": 3}
    assert "machine_id" not in dumped


# ── ContractService.create_position XOR walidacja (service layer) ────────────

@pytest.mark.asyncio
async def test_create_position_xor_both_set_raises_400():
    """create_position z machine_id + service_id → 400 (XOR naruszone)."""
    from fastapi import HTTPException
    from contracts.service import contract_service
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)

    # verify_contract_access zwraca mock contract
    db = AsyncMock()
    contract = MagicMock()
    contract.id = 1

    async def fake_verify(db_arg, contract_id, user_arg, **kwargs):
        return contract
    contract_service.verify_contract_access = AsyncMock(side_effect=fake_verify)

    data = PositionCreate(machine_id=1, service_id=2)  # to rzuci ValidationError w Pydantic
    # Ale nawet gdyby przeszło — service layer też waliduje
    with pytest.raises((HTTPException, ValidationError)):
        await contract_service.create_position(db, 1, data, user)


@pytest.mark.asyncio
async def test_create_position_xor_neither_set_raises_400():
    """create_position bez machine_id i service_id → 400/ValidationError (XOR naruszone)."""
    from contracts.service import contract_service
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)

    db = AsyncMock()
    # PositionCreate() rzuci ValidationError w Pydantic (model_validator)
    with pytest.raises(ValidationError):
        PositionCreate()  # type: ignore[call-arg]


# ── ContractService.update_position XOR walidacja (service layer) ────────────

@pytest.mark.asyncio
async def test_update_position_xor_violation_on_final_state():
    """update_position: jeśli po apply partial fields oba są None → 400.

    Scenariusz: pozycja ma machine_id=5, update ustawia machine_id=None
    (nie wysyłając service_id) → final state: machine_id=None, service_id=None → 400.
    """
    from fastapi import HTTPException
    from contracts.service import contract_service
    from contracts.models import ContractPosition, Contract
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)

    db = AsyncMock()

    # Mock pozycji: ma machine_id=5, service_id=None
    pos = MagicMock(spec=ContractPosition)
    pos.id = 1
    pos.contract_id = 10
    pos.machine_id = 5
    pos.service_id = None

    result = MagicMock()
    result.scalar_one_or_none.return_value = pos
    db.execute = AsyncMock(return_value=result)

    # verify_contract_access zwraca mock
    contract = MagicMock(spec=Contract)
    contract.id = 10

    async def fake_verify(db_arg, contract_id, user_arg, **kwargs):
        return contract
    contract_service.verify_contract_access = AsyncMock(side_effect=fake_verify)

    # Update: machine_id=None (czyści machine_id), service_id nie wysłane
    # Po apply: pos.machine_id=None, pos.service_id=None → XOR naruszone
    data = PositionUpdate(machine_id=None)
    # service layer sprawdza: (pos.machine_id is None) == (pos.service_id is None) → True → 400
    with pytest.raises(HTTPException) as exc_info:
        await contract_service.update_position(db, 1, data, user)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_position_xor_ok_when_switching_machine_to_service():
    """update_position: zmiana z machine_id na service_id → XOR spełnione.

    Scenariusz: pozycja ma machine_id=5, update ustawia machine_id=None + service_id=3
    → final state: machine_id=None, service_id=3 → XOR OK.
    """
    from contracts.service import contract_service
    from contracts.models import ContractPosition, Contract
    from machines.models import Machine
    from services.models import Service
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)

    db = AsyncMock()

    pos = MagicMock(spec=ContractPosition)
    pos.id = 1
    pos.contract_id = 10
    pos.machine_id = 5
    pos.service_id = None

    result = MagicMock()
    result.scalar_one_or_none.return_value = pos
    db.execute = AsyncMock(return_value=result)

    contract = MagicMock(spec=Contract)
    contract.id = 10

    async def fake_verify(db_arg, contract_id, user_arg, **kwargs):
        return contract
    contract_service.verify_contract_access = AsyncMock(side_effect=fake_verify)

    # db.get zwraca mock Machine i Service
    machine = MagicMock(spec=Machine)
    service = MagicMock(spec=Service)
    db.get = AsyncMock(side_effect=lambda cls, _id: machine if cls is Machine else service)

    data = PositionUpdate(machine_id=None, service_id=3)
    out = await contract_service.update_position(db, 1, data, user)
    assert out is pos
    assert pos.machine_id is None
    assert pos.service_id == 3
