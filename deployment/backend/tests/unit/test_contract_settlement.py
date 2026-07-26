"""RAO-P1-133: testy cofania rozliczenia umowy i edycji pól kontaktowych."""
import pytest
from unittest.mock import AsyncMock, MagicMock

# Rejestracja wszystkich modeli ORM (PostalCode itp.) — wymagane przez selectinload
import integrations.models  # noqa: F401

from fastapi import HTTPException
from auth.models import User
from contracts.models import Contract
from contracts.service import contract_service


def _make_user() -> MagicMock:
    return MagicMock(spec=User, role="admin", branch_id=1)


def _make_contract(is_settled: bool = False) -> MagicMock:
    """Zwraca mock umowy z polami ustawianymi przez service."""
    contract = MagicMock(spec=Contract)
    contract.is_settled = is_settled
    contract.settled_at = None
    contract.updated_at = None
    return contract


def _db_with_contract(contract: MagicMock) -> AsyncMock:
    """DB mock: get_contract zwraca `contract` przez db.execute + scalar_one_or_none."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = contract
    db.execute = AsyncMock(return_value=result)
    db.get = AsyncMock(return_value=contract)
    # commit/refresh niech nie podnoszą — refresh zwraca ten sam obiekt
    db.refresh = AsyncMock(return_value=contract)
    return db


# ── settle_contract: cofnięcie rozliczenia ────────────────────────────────────

@pytest.mark.asyncio
async def test_settle_contract_unset_from_settled_works():
    """Cofnięcie rozliczenia (True → False) działa bez błędu 409."""
    user = _make_user()
    contract = _make_contract(is_settled=True)
    db = _db_with_contract(contract)

    out = await contract_service.settle_contract(db, 1, is_settled=False, user=user)

    assert out is contract
    assert contract.is_settled is False
    assert contract.settled_at is None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_settle_contract_set_from_unset_works():
    """Ponowne oznaczenie (False → True) działa i ustawia settled_at."""
    user = _make_user()
    contract = _make_contract(is_settled=False)
    db = _db_with_contract(contract)

    out = await contract_service.settle_contract(db, 1, is_settled=True, user=user)

    assert out is contract
    assert contract.is_settled is True
    assert contract.settled_at is not None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_settle_contract_set_on_already_settled_raises_409():
    """Oznaczenie już rozliczonej umowy nadal blokuje guard (409)."""
    user = _make_user()
    contract = _make_contract(is_settled=True)
    db = _db_with_contract(contract)

    with pytest.raises(HTTPException) as exc:
        await contract_service.settle_contract(db, 1, is_settled=True, user=user)
    assert exc.value.status_code == 409


# ── update_contract: pola kontaktowe na rozliczonej umowie ─────────────────────

def _update_payload(**fields):
    from contracts.schemas import ContractUpdate
    return ContractUpdate(**fields)


@pytest.mark.asyncio
async def test_update_contact_fields_on_settled_contract_allowed():
    """Edycja pól kontaktowych na rozliczonej umowie działa bez cofania."""
    user = _make_user()
    contract = _make_contract(is_settled=True)
    db = _db_with_contract(contract)

    data = _update_payload(contact_person1="Jan Kowalski", contact_phone1="500-100-200")

    out = await contract_service.update_contract(db, 1, data, user)

    assert out is contract
    assert contract.contact_person1 == "Jan Kowalski"
    assert contract.contact_phone1 == "500-100-200"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_disallowed_field_on_settled_contract_raises_403():
    """Zmiana niedozwolonego pola (np. city) na rozliczonej umowie → 403."""
    user = _make_user()
    contract = _make_contract(is_settled=True)
    db = _db_with_contract(contract)

    data = _update_payload(city="Warszawa")

    with pytest.raises(HTTPException) as exc:
        await contract_service.update_contract(db, 1, data, user)
    assert exc.value.status_code == 403
    assert "rozliczona" in exc.value.detail.lower()
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_any_field_on_active_contract_allowed():
    """Na aktywnej (nierozliczonej) umowie wszystkie pola są dozwolone."""
    user = _make_user()
    contract = _make_contract(is_settled=False)
    db = _db_with_contract(contract)

    data = _update_payload(city="Warszawa", contact_person1="Jan Kowalski")

    out = await contract_service.update_contract(db, 1, data, user)

    assert out is contract
    assert contract.city == "Warszawa"
    db.commit.assert_awaited_once()
