"""RAO-P3-011: testy walidacji Pydantic dla schematów contracts."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from contracts.schemas import (
    ContractCreate,
    PositionCreate,
    ConditionCreate,
)
from contracts.service import generate_contract_number


def test_contract_create_minimal_valid():
    c = ContractCreate(contractor_id=1)
    assert c.contractor_id == 1
    assert c.contract_type == "S"
    assert c.total_value == Decimal("0.00")
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
    cond = ConditionCreate()
    assert cond.rate1 is None
    assert cond.minimum is None


def test_condition_description_max_length():
    with pytest.raises(ValidationError):
        ConditionCreate(description="x" * 401)


# ── generate_contract_number (RAO-P1-022) ───────────────────────────────────

@pytest.mark.asyncio
async def test_generate_contract_number_warsaw_no_suffix():
    """Branch other than Gdańsk (or no branch) → no suffix."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165
    branch_result = MagicMock()
    branch_result.scalar_one_or_none.return_value = "Warszawa"

    db.execute = AsyncMock(side_effect=[company_result, max_result, branch_result])

    number, auto = await generate_contract_number(db, "S", branch_id=1)
    assert auto == 166
    assert number.endswith("/2026")
    assert "G" not in number


@pytest.mark.asyncio
async def test_generate_contract_number_gdansk_suffix():
    """Branch Gdańsk → suffix 'G'."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165
    branch_result = MagicMock()
    branch_result.scalar_one_or_none.return_value = "Gdańsk"

    db.execute = AsyncMock(side_effect=[company_result, max_result, branch_result])

    number, auto = await generate_contract_number(db, "S", branch_id=2)
    assert auto == 166
    assert number.endswith("/2026G")


@pytest.mark.asyncio
async def test_generate_contract_number_gdansk_case_insensitive():
    """Branch name case-insensitive match for GDAŃSK."""
    db = AsyncMock()
    company_result = MagicMock()
    company_result.scalar_one_or_none.return_value = 100
    max_result = MagicMock()
    max_result.scalar_one_or_none.return_value = 165
    branch_result = MagicMock()
    branch_result.scalar_one_or_none.return_value = "GDAŃSK"

    db.execute = AsyncMock(side_effect=[company_result, max_result, branch_result])

    number, auto = await generate_contract_number(db, "U", branch_id=2)
    assert number.endswith("/2026G")


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
    assert db.execute.await_count == 2
