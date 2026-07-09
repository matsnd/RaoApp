"""RAO-P3-011: testy walidacji Pydantic dla schematów contracts."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

# Rejestracja wszystkich modeli ORM (PostalCode itp.) — wymagane przez selectinload
# w testach service, które triggerują pełną konfigurację mapperów SQLAlchemy.
import integrations.models  # noqa: F401

from contracts.schemas import (
    ContractCreate,
    ContractUpdate,
    PositionCreate,
    PositionUpdate,
    ConditionCreate,
    ConditionUpdate,
)
from contracts.service import generate_contract_number


def test_contract_create_minimal_valid():
    c = ContractCreate(contractor_id=1)
    assert c.contractor_id == 1
    assert c.contract_type == "S"
    # RAO-P1-021/P2-033: total_value usunięte
    assert c.working_days_per_week == 6


def test_contract_create_requires_contractor_id():
    with pytest.raises(ValidationError):
        ContractCreate()  # type: ignore[call-arg]


def test_contract_create_invalid_contract_type():
    with pytest.raises(ValidationError):
        ContractCreate(contractor_id=1, contract_type="X")  # type: ignore[arg-type]


def test_contract_create_postal_code_pattern():
    # Poprawny
    c = ContractCreate(contractor_id=1, postal_code="00-001")
    assert c.postal_code == "00-001"
    # Niepoprawny
    with pytest.raises(ValidationError):
        ContractCreate(contractor_id=1, postal_code="00001")
    with pytest.raises(ValidationError):
        ContractCreate(contractor_id=1, postal_code="ABCDE")


def test_contract_create_city_validation():
    c = ContractCreate(contractor_id=1, city="Wrocław")
    assert c.city == "Wrocław"
    with pytest.raises(ValidationError):
        # niedozwolone znaki
        ContractCreate(contractor_id=1, city="Bad@City!")


def test_contract_create_dates_optional():
    c = ContractCreate(
        contractor_id=1,
        date_from=date(2026, 1, 1),
        date_to=date(2026, 1, 31),
    )
    assert c.date_from == date(2026, 1, 1)


def test_position_create_defaults():
    p = PositionCreate(article_id=42)
    assert p.article_id == 42
    assert p.quantity == 1


def test_position_create_requires_article_id():
    with pytest.raises(ValidationError):
        PositionCreate()  # type: ignore[call-arg]


def test_condition_create_all_optional():
    # Rate fields are optional individually, but at least one rate is required.
    with pytest.raises(ValidationError):
        ConditionCreate()  # type: ignore[call-arg]
    cond = ConditionCreate(rate1=Decimal("100.00"))
    assert cond.rate2 is None
    assert cond.minimum is None


def test_condition_description_max_length():
    with pytest.raises(ValidationError):
        ConditionCreate(description="x" * 401)


# ── generate_contract_number (RAO-P1-022) ───────────────────────────────────

@pytest.mark.asyncio
async def test_generate_contract_number_warsaw_no_suffix():
    """Branch Warszawa (id=1) → no suffix. RAO-P1-022: branch_id=1 = Warszawa."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165

    db.execute = AsyncMock(side_effect=[company_result, max_result])

    number, auto = await generate_contract_number(db, "S", branch_id=1)
    assert auto == 166
    assert number == "S166/2026"
    assert "G" not in number


@pytest.mark.asyncio
async def test_generate_contract_number_gdansk_suffix():
    """Branch Gdańsk (id≠1) → suffix 'G'. RAO-P1-022: branch_id≠1 = Gdańsk."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165

    db.execute = AsyncMock(side_effect=[company_result, max_result])

    number, auto = await generate_contract_number(db, "S", branch_id=2)
    assert auto == 166
    assert number.endswith("/2026G")


@pytest.mark.asyncio
async def test_generate_contract_number_always_S_prefix():
    """RAO-P1-022: Wszystkie umowy zaczynają się na S, nawet typ U."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165

    db.execute = AsyncMock(side_effect=[company_result, max_result])

    number, auto = await generate_contract_number(db, "U", branch_id=1)
    assert number.startswith("S")  # nie "U" — wszystkie na S
    assert number == "S166/2026"


@pytest.mark.asyncio
async def test_generate_contract_number_no_branch_id():
    """branch_id=None → no suffix, no branch query."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165

    db.execute = AsyncMock(side_effect=[company_result, max_result])

    number, auto = await generate_contract_number(db, "S", branch_id=None)
    assert auto == 166
    assert not number.endswith("G")


# ── RAO-P0-034: exclude_unset=True — partial update must not reset fields ──────

def test_contract_update_exclude_unset_only_sent_fields():
    """PUT with only notes must NOT include working_days_per_week in dump."""
    u = ContractUpdate(notes="test")
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"notes": "test"}
    assert "working_days_per_week" not in dumped
    assert "contract_type" not in dumped
    assert "show_person1" not in dumped

def test_contract_update_all_fields_optional():
    """ContractUpdate with no fields → empty dump (no-op update)."""
    u = ContractUpdate()
    assert u.model_dump(exclude_unset=True) == {}

def test_position_update_exclude_unset():
    u = PositionUpdate(quantity=5)
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"quantity": 5}
    assert "article_id" not in dumped
    assert "rental_days" not in dumped

def test_condition_update_exclude_unset():
    u = ConditionUpdate(rate1=Decimal("150"), period_count=7)
    dumped = u.model_dump(exclude_unset=True)
    assert dumped == {"rate1": Decimal("150"), "period_count": 7}
    assert "minimum" not in dumped

def test_contract_update_full_payload_still_works():
    """Full payload (like frontend sends) → all fields in dump (backward-compat)."""
    u = ContractUpdate(
        contractor_id=1, contract_type="S", working_days_per_week=5,
        notes="abc", show_person1=True,
    )
    dumped = u.model_dump(exclude_unset=True)
    assert "contractor_id" in dumped
    assert "working_days_per_week" in dumped
    assert "notes" in dumped


# ── RAO-P1-039: walidacja date_from > date_to + ujemne kwoty ──────────────────

def test_contract_create_date_from_after_date_to_rejected():
    with pytest.raises(ValidationError):
        ContractCreate(contractor_id=1, date_from=date(2026, 7, 1), date_to=date(2026, 6, 1))

def test_contract_create_negative_prepayment_rejected():
    with pytest.raises(ValidationError):
        ContractCreate(contractor_id=1, prepayment_amount=Decimal("-50"))

def test_contract_create_valid_dates_accepted():
    c = ContractCreate(contractor_id=1, date_from=date(2026, 6, 1), date_to=date(2026, 7, 1))
    assert c.date_from == date(2026, 6, 1)

def test_contract_update_date_from_after_date_to_rejected():
    with pytest.raises(ValidationError):
        ContractUpdate(date_from=date(2026, 7, 1), date_to=date(2026, 6, 1))

def test_contract_update_negative_amount_rejected():
    # RAO-P1-021/P2-033: total_value usunięte — testujemy prepayment_amount
    with pytest.raises(ValidationError):
        ContractUpdate(prepayment_amount=Decimal("-1"))


# ── RAO-P1-041: JWT secret key validation ─────────────────────────────────────

def test_config_rejects_empty_secret_key():
    from config import Settings
    import os
    # Ensure no env override
    old = os.environ.pop("RAO_SECRET_KEY", None)
    try:
        with pytest.raises(ValidationError):
            Settings(RAO_SECRET_KEY="")
    finally:
        if old is not None:
            os.environ["RAO_SECRET_KEY"] = old

def test_config_rejects_change_me_secret_key():
    from config import Settings
    with pytest.raises(ValidationError):
        Settings(RAO_SECRET_KEY="change-me")

def test_config_accepts_real_secret_key():
    from config import Settings
    s = Settings(RAO_SECRET_KEY="a-valid-secret-key-with-sufficient-length-32chars")
    assert s.RAO_SECRET_KEY == "a-valid-secret-key-with-sufficient-length-32chars"


# ── RAO-P1-001: apply_rate_preset_to_position + last-conditions ──────────────

@pytest.mark.asyncio
async def test_apply_rate_preset_position_not_found_raises_404():
    """apply_rate_preset_to_position zwraca 404 gdy pozycja nie istnieje."""
    from fastapi import HTTPException
    from contracts.service import contract_service
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # brak pozycji
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await contract_service.apply_rate_preset_to_position(db, 999, 1, user, replace=True)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_apply_rate_preset_settled_contract_raises_409():
    """apply_rate_preset_to_position zwraca 409 gdy umowa rozliczona."""
    from fastapi import HTTPException
    from contracts.service import contract_service
    from contracts.models import ContractPosition, Contract
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)

    db = AsyncMock()
    pos = MagicMock(spec=ContractPosition)
    pos.contract_id = 5
    pos_result = MagicMock()
    pos_result.scalar_one_or_none.return_value = pos
    contract = MagicMock(spec=Contract)
    contract.is_settled = True
    contract_result = MagicMock()
    contract_result.scalar_one_or_none.return_value = contract

    # First execute → position, second → contract (via get_contract)
    db.execute = AsyncMock(side_effect=[pos_result, contract_result])
    db.get = AsyncMock(return_value=contract)

    with pytest.raises(HTTPException) as exc:
        await contract_service.apply_rate_preset_to_position(db, 1, 1, user, replace=True)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_get_last_conditions_for_article_no_history_returns_none():
    """get_last_conditions_for_article zwraca None gdy brak historii umów."""
    from contracts.service import contract_service
    from auth.models import User
    user = MagicMock(spec=User, role="admin", branch_id=1)
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # brak pozycji
    db.execute = AsyncMock(return_value=result)

    out = await contract_service.get_last_conditions_for_article(db, 999, user)
    assert out is None
