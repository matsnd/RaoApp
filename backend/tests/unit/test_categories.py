"""RAO-P2-019: testy dla hierarchicznych kategorii — schematy + service (mockowane DB)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError
from fastapi import HTTPException

# Wymuszamy inicjalizacje wszystkich mapperow SQLAlchemy
# (ServiceFeeTemplate odwoluje sie do Article przez relationship;
#  Contract.postal_code_ref odwoluje sie do PostalCode)
import articles.models  # noqa: F401
import integrations.models  # noqa: F401
import contracts.models  # noqa: F401

from settings.schemas import CategoryCreate, CategoryResponse, CategoryTreeNode
from settings.service import SettingsService


# ── Pydantic schemas ─────────────────────────────────────────────────────────

def test_category_create_requires_name():
    with pytest.raises(ValidationError):
        CategoryCreate()  # brak name


def test_category_create_minimal():
    c = CategoryCreate(name="Koparki")
    assert c.name == "Koparki"
    assert c.parent_id is None
    assert c.level == "main"
    assert c.code is None
    assert c.description is None


def test_category_create_with_parent_and_level():
    c = CategoryCreate(name="Mini", parent_id=1, level="sub1")
    assert c.parent_id == 1
    assert c.level == "sub1"


def test_category_create_invalid_level():
    with pytest.raises(ValidationError):
        CategoryCreate(name="X", level="sub9")  # nie pasuje do patternu


def test_category_create_all_valid_levels():
    for lvl in ("main", "sub1", "sub2", "sub3"):
        c = CategoryCreate(name="Test", level=lvl)
        assert c.level == lvl


def test_category_create_max_length_name():
    with pytest.raises(ValidationError):
        CategoryCreate(name="x" * 201)


def test_category_create_max_length_code():
    with pytest.raises(ValidationError):
        CategoryCreate(name="Test", code="x" * 41)


def test_category_response_has_new_fields():
    resp = CategoryResponse(
        id=1, name="Koparki", code=None, description=None, parent_id=None, level="main"
    )
    assert resp.parent_id is None
    assert resp.level == "main"


def test_category_response_default_level():
    resp = CategoryResponse(id=2, name="Mini", code=None, description=None)
    assert resp.level == "main"


def test_category_tree_node_minimal():
    node = CategoryTreeNode(id=1, name="Koparki", level="main")
    assert node.children == []
    assert node.parent_id is None


def test_category_tree_node_with_children():
    child = CategoryTreeNode(id=2, name="Mini", level="sub1", parent_id=1)
    parent = CategoryTreeNode(id=1, name="Koparki", level="main", children=[child])
    assert len(parent.children) == 1
    assert parent.children[0].name == "Mini"


def test_category_tree_node_model_rebuild_ok():
    """Sprawdza, ze model_rebuild() nie rzuca wyjatku (self-referential)."""
    sub2 = CategoryTreeNode(id=3, name="Sub2", level="sub2", parent_id=2)
    sub1 = CategoryTreeNode(id=2, name="Sub1", level="sub1", parent_id=1, children=[sub2])
    root = CategoryTreeNode(id=1, name="Root", level="main", children=[sub1])
    assert root.children[0].children[0].name == "Sub2"


# ── SettingsService.list_categories_tree ─────────────────────────────────────

@pytest.mark.asyncio
async def test_list_categories_tree_returns_list():
    """Happy path: zwraca liste kategorii glownych."""
    svc = SettingsService()

    cat1 = MagicMock()
    cat1.id = 1
    cat1.name = "Koparki"
    cat1.level = "main"
    cat1.parent_id = None
    cat1.children = []

    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [cat1]
    db.execute = AsyncMock(return_value=result_mock)

    out = await svc.list_categories_tree(db)
    assert len(out) == 1
    assert out[0].name == "Koparki"
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_list_categories_tree_empty():
    """Pusta baza zwraca pusta liste."""
    svc = SettingsService()
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result_mock)

    out = await svc.list_categories_tree(db)
    assert out == []


# ── SettingsService.create_category ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_category_with_parent_id():
    """POST z parent_id i level=sub1 — poprawne tworzenie podkategorii."""
    svc = SettingsService()
    data = CategoryCreate(name="Mini", parent_id=1, level="sub1")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # Mock execute — zwróć pustą listę (brak duplikatów)
    async def mock_execute(stmt):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = []
        result.scalars.return_value = scalars
        return result
    db.execute = mock_execute

    result = await svc.create_category(db, data)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    assert result.parent_id == 1
    assert result.level == "sub1"


@pytest.mark.asyncio
async def test_create_category_main_no_parent():
    """POST bez parent_id — tworzy kategorie glowna."""
    svc = SettingsService()
    data = CategoryCreate(name="Ladowarki")

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def mock_execute(stmt):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = []
        result.scalars.return_value = scalars
        return result
    db.execute = mock_execute

    result = await svc.create_category(db, data)

    assert result.name == "Ladowarki"
    assert result.parent_id is None


# ── SettingsService.delete_category ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_category_not_found():
    """DELETE nieistniejacej kategorii -> 404."""
    svc = SettingsService()
    db = AsyncMock()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc_info:
        await svc.delete_category(db, 999)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_with_children_raises_409():
    """DELETE kategorii z podkategoriami -> 409 Conflict."""
    svc = SettingsService()
    db = AsyncMock()

    cat_mock = MagicMock()
    cat_mock.id = 1

    execute_calls = []

    async def mock_execute(stmt):
        call_num = len(execute_calls)
        execute_calls.append(stmt)
        result = MagicMock()
        if call_num == 0:
            result.scalar_one_or_none.return_value = cat_mock
        else:
            result.scalar_one_or_none.return_value = 2  # child id istnieje
        return result

    db.execute = mock_execute

    with pytest.raises(HTTPException) as exc_info:
        await svc.delete_category(db, 1)
    assert exc_info.value.status_code == 409
    assert "podkategorie" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_category_leaf_ok():
    """DELETE kategorii-liscia (bez dzieci) -> sukces."""
    svc = SettingsService()
    db = AsyncMock()

    cat_mock = MagicMock()
    cat_mock.id = 3

    execute_calls = []

    async def mock_execute(stmt):
        call_num = len(execute_calls)
        execute_calls.append(stmt)
        result = MagicMock()
        if call_num == 0:
            result.scalar_one_or_none.return_value = cat_mock
        elif call_num == 1:
            result.scalar_one_or_none.return_value = None  # brak dzieci
        return result

    db.execute = mock_execute
    db.commit = AsyncMock()

    await svc.delete_category(db, 3)
    db.commit.assert_called_once()
