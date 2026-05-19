"""RAO-P3-011: testy dla settings — schematy + service (mockowane DB)."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from settings.schemas import (
    CompanyUpdate,
    ServiceFeeTemplateCreate,
    FeePresetGroupCreate,
)
from settings.service import SettingsService


# ── Pydantic schemas ────────────────────────────────────────────────────────

def test_company_update_all_fields_optional():
    upd = CompanyUpdate()
    assert upd.name is None


def test_company_update_max_lengths():
    with pytest.raises(ValidationError):
        CompanyUpdate(name="x" * 201)
    with pytest.raises(ValidationError):
        CompanyUpdate(nip="x" * 21)


def test_service_fee_template_create_requires_name_and_type():
    with pytest.raises(ValidationError):
        ServiceFeeTemplateCreate(contract_type="S")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ServiceFeeTemplateCreate(name="Transport")  # type: ignore[call-arg]


def test_service_fee_template_invalid_contract_type():
    with pytest.raises(ValidationError):
        ServiceFeeTemplateCreate(contract_type="X", name="Transport")  # type: ignore[arg-type]


def test_service_fee_template_minimal_valid():
    t = ServiceFeeTemplateCreate(contract_type="S", name="Transport")
    assert t.is_active is True
    assert t.amount_from is None


def test_service_fee_template_with_amounts():
    t = ServiceFeeTemplateCreate(
        contract_type="U",
        name="Praca operatora",
        amount_from=Decimal("100.00"),
        amount_to=Decimal("500.00"),
        unit="zł/h",
    )
    assert t.amount_from == Decimal("100.00")
    assert t.unit == "zł/h"


def test_fee_preset_group_create_valid():
    g = FeePresetGroupCreate(name="Standard", contract_type="S")
    assert g.is_default is False


# ── SettingsService.seed_fee_templates ──────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_fee_templates_skips_when_records_exist():
    """force=False, count > 0 → seed nic nie robi."""
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one.return_value = 5  # już są wpisy
    db.execute = AsyncMock(return_value=result)
    db.add = MagicMock()
    db.commit = AsyncMock()

    out = await svc.seed_fee_templates(db, force=False)
    assert out == 0
    db.add.assert_not_called()


# ── SettingsService.get_company ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_company_returns_existing():
    svc = SettingsService()
    company_obj = MagicMock(id=1, name="Toolsmart")

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = company_obj
    db.execute = AsyncMock(return_value=result)

    out = await svc.get_company(db)
    assert out is company_obj
    assert out.id == 1
