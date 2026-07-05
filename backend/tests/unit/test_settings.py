"""RAO-P3-011: testy dla settings — schematy + service (mockowane DB)."""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

# Rejestracja wszystkich modeli ORM (PostalCode itp.) — wymagane przez selectinload
# w testach service, które triggerują pełną konfigurację mapperów SQLAlchemy.
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from settings.schemas import (
    CompanyUpdate,
    ServiceFeeTemplateCreate,
    FeePresetGroupCreate,
    ArticleRatePresetCreate,
    ArticleRatePresetUpdate,
    ArticleRatePresetItemCreate,
    ArticleRatePresetItemUpdate,
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


# ── RAO-P1-001: ArticleRatePreset schemas ───────────────────────────────────

def test_article_rate_preset_create_minimal():
    p = ArticleRatePresetCreate(name="Standard")
    assert p.is_default is False
    assert p.items == []


def test_article_rate_preset_create_requires_name():
    with pytest.raises(ValidationError):
        ArticleRatePresetCreate()  # type: ignore[call-arg]


def test_article_rate_preset_create_name_max_length():
    with pytest.raises(ValidationError):
        ArticleRatePresetCreate(name="x" * 201)


def test_article_rate_preset_create_with_items():
    p = ArticleRatePresetCreate(
        name="Promo",
        is_default=True,
        items=[
            ArticleRatePresetItemCreate(rate1=Decimal("540.00"), period_count=3, billing_label="doba"),
            ArticleRatePresetItemCreate(rate2=Decimal("350.00"), billing_label="doba"),
        ],
    )
    assert p.is_default is True
    assert len(p.items) == 2
    assert p.items[0].rate1 == Decimal("540.00")


def test_article_rate_preset_update_all_optional():
    u = ArticleRatePresetUpdate()
    assert u.name is None
    assert u.is_default is None


def test_article_rate_preset_item_billing_label_max_length():
    with pytest.raises(ValidationError):
        ArticleRatePresetItemCreate(billing_label="x" * 21)


def test_article_rate_preset_item_description_max_length():
    with pytest.raises(ValidationError):
        ArticleRatePresetItemCreate(description="x" * 401)


def test_article_rate_preset_item_update_all_optional():
    u = ArticleRatePresetItemUpdate()
    assert u.rate1 is None
    assert u.period_count is None


# ── RAO-P1-001: SettingsService rate-preset methods (mocked DB) ──────────────

@pytest.mark.asyncio
async def test_get_article_rate_preset_not_found_raises_404():
    """get_article_rate_preset zwraca 404 gdy preset nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.get_article_rate_preset(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_article_rate_preset_not_found_raises_404():
    """delete_article_rate_preset zwraca 404 gdy preset nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_article_rate_preset(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_preset_item_not_found_raises_404():
    """update_preset_item zwraca 404 gdy item nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.update_preset_item(db, 999, ArticleRatePresetItemUpdate())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_preset_item_not_found_raises_404():
    """delete_preset_item zwraca 404 gdy item nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_preset_item(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_set_default_preset_not_found_raises_404():
    """set_default_preset zwraca 404 gdy preset nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as exc:
        await svc.set_default_preset(db, 999)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_article_rate_preset_article_not_found_raises_404():
    """create_article_rate_preset zwraca 404 gdy artykuł nie istnieje."""
    from fastapi import HTTPException
    svc = SettingsService()
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)  # artykuł nie istnieje

    with pytest.raises(HTTPException) as exc:
        await svc.create_article_rate_preset(db, 999, ArticleRatePresetCreate(name="X"))
    assert exc.value.status_code == 404
