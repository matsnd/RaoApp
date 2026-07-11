"""RAO: testy power_type (typ zasilania maszyny) — schemas + service (mockowane DB).

Pokrywa:
- create article z power_type='diesel' → 200-equivalent (service zwraca article z power_type)
- create article bez power_type → default 'other'
- update article power_type → zmiana widoczna (exclude_unset)
- create article z invalid power_type → ValidationError (422-equivalent)

Wzorzec zgodny z tests/unit/test_categories.py (mockowany AsyncSession, Pydantic v2).
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError

# Rejestracja mapperów SQLAlchemy (Article relationship w ServiceFeeTemplate itp.)
import articles.models  # noqa: F401
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from articles.schemas import ArticleCreate, ArticleUpdate, ArticleDetail
from articles.service import ArticleService


# ── Pydantic schemas ─────────────────────────────────────────────────────────

def test_article_create_default_power_type_is_other():
    """Create bez power_type → default 'other' (backward compat)."""
    a = ArticleCreate(name="Koparka X")
    assert a.power_type == "other"


def test_article_create_with_diesel_power_type():
    """Create z power_type='diesel' → wartość zachowana."""
    a = ArticleCreate(name="Koparka Diesel", power_type="diesel")
    assert a.power_type == "diesel"


def test_article_create_with_electric_power_type():
    a = ArticleCreate(name="Pilarka Elektryczna", power_type="electric")
    assert a.power_type == "electric"


def test_article_create_invalid_power_type_raises_422():
    """Create z niepoprawnym power_type → ValidationError (HTTP 422)."""
    with pytest.raises(ValidationError):
        ArticleCreate(name="Błędna", power_type="steam")  # type: ignore[arg-type]


def test_article_create_invalid_power_type_empty_string():
    with pytest.raises(ValidationError):
        ArticleCreate(name="Błędna", power_type="")  # type: ignore[arg-type]


def test_article_update_power_type_optional():
    """ArticleUpdate — power_type opcjonalny, domyślnie None (partial update)."""
    u = ArticleUpdate()
    assert u.power_type is None


def test_article_update_power_type_diesel():
    u = ArticleUpdate(power_type="diesel")
    assert u.power_type == "diesel"


def test_article_update_invalid_power_type_raises_422():
    with pytest.raises(ValidationError):
        ArticleUpdate(power_type="nuclear")  # type: ignore[arg-type]


def _detail_kwargs(**overrides):
    """Wspólne wymagane pola ArticleDetail (pola nullable bez defaultu są required)."""
    base = dict(
        id=1, name="Koparka", is_service=False,
        internal_number=None, registration_no=None, serial_no=None,
        brand=None, model=None, replacement_value=None,
        category_id=None, category_name=None,
        owner_id=None, owner_name=None, branch_id=None,
        description=None, notes=None, rental_days=None, article_type=None,
        fakturownia_product_id=None,
        fakturownia_tax_rate=None, fakturownia_gtu_code=None, fakturownia_pkwiu=None,
        created_at=datetime.utcnow(), updated_at=None,
    )
    base.update(overrides)
    return base


def test_article_detail_power_type_default_other():
    """ArticleDetail (Out) — power_type ma default 'other' dla backward compat."""
    d = ArticleDetail(**_detail_kwargs())
    assert d.power_type == "other"


def test_article_detail_power_type_from_value():
    d = ArticleDetail(**_detail_kwargs(id=1, power_type="diesel"))
    assert d.power_type == "diesel"


# ── ArticleService.create_article ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_article_diesel_returns_power_type():
    """POST /articles z power_type='diesel' → service zwraca Article z power_type='diesel' (200)."""
    svc = ArticleService()
    data = ArticleCreate(name="Koparka Diesel", power_type="diesel")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    # db.refresh ustawia id + utrzymuje power_type z dumpa
    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 1
    db.refresh = AsyncMock(side_effect=fake_refresh)

    article = await svc.create_article(db, data)

    assert article.power_type == "diesel"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_article_without_power_type_defaults_other():
    """POST /articles bez power_type → service zwraca Article z power_type='other' (200)."""
    svc = ArticleService()
    data = ArticleCreate(name="Koparka Default")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        obj.id = 2
    db.refresh = AsyncMock(side_effect=fake_refresh)

    article = await svc.create_article(db, data)

    assert article.power_type == "other"


# ── ArticleService.update_article ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_article_power_type_change_visible():
    """PUT /articles/{id} z power_type='electric' → zmiana widoczna w zwróconym obiekcie (200)."""
    svc = ArticleService()

    existing = MagicMock()
    existing.id = 10
    existing.name = "Stara maszyna"
    existing.power_type = "other"

    # get_article zwraca existing
    async def fake_get_article(db_arg, article_id):
        return existing
    svc.get_article = AsyncMock(side_effect=fake_get_article)

    db = AsyncMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj, *args, **kwargs):
        # odzwierciedlamy to co setattr ustawił
        return None
    db.refresh = AsyncMock(side_effect=fake_refresh)

    data = ArticleUpdate(power_type="electric")
    updated = await svc.update_article(db, 10, data)

    assert existing.power_type == "electric"
    assert updated is existing
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_article_omit_power_type_keeps_existing():
    """Partial update bez power_type → power_type NIE dotknięte (exclude_unset)."""
    svc = ArticleService()

    existing = MagicMock()
    existing.id = 11
    existing.power_type = "diesel"

    async def fake_get_article(db_arg, article_id):
        return existing
    svc.get_article = AsyncMock(side_effect=fake_get_article)

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # aktualizujemy tylko notes — power_type nie powinien być w exclude_unset
    data = ArticleUpdate(notes="Nowe notatki")
    await svc.update_article(db, 11, data)

    # power_type nie został przekazany do setattr
    assert existing.power_type == "diesel"
