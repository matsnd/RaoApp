"""RAO-P3-011: testy walidacji Pydantic dla schematów contracts."""
import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from contracts.schemas import (
    ContractCreate,
    PositionCreate,
    ConditionCreate,
)


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
