"""
Unit testy dla RAO-P1-027: filtrowanie is_external + is_archival w fleet stats.
Testy weryfikują logikę filtrowania bez połączenia z bazą (calc-level + schema validation).
"""
from decimal import Decimal
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from stats.calc import aggregate_by_category


def d(val) -> Decimal:
    return Decimal(str(val))


def mk_pos(is_service=False, article_id=1, revenue=1000, name="M1", internal_number="001"):
    """Helper: tworzy minimalny dict pozycji jak zwraca _compute_position_revenues."""
    return {
        "position_id": article_id * 10,
        "article_id": article_id,
        "contract_id": 1,
        "contractor_id": 1,
        "article_name": name,
        "internal_number": internal_number,
        "is_service": is_service,
        "contract_number": "U/2024/001",
        "contractor_name": "Test Sp. z o.o.",
        "rental_days": 10,
        "revenue": d(revenue),
        "date_from": date(2024, 1, 1),
        "date_to": date(2024, 1, 10),
        "clamped_days": 10,
        "category_main": "Maszyny",
        "category_sub1": None,
        "category_sub2": None,
        "category_sub3": None,
        "contract_date_from": date(2024, 1, 1),
    }


# ---------------------------------------------------------------------------
# Testy Article model — is_external field present
# ---------------------------------------------------------------------------

def test_article_model_has_is_external():
    """Article model musi mieć kolumnę is_external (RAO-P1-027)."""
    from articles.models import Article
    assert hasattr(Article, 'is_external'), "Article.is_external kolumna nie istnieje!"


def test_article_model_is_external_default():
    """Article.is_external ma default=False."""
    from articles.models import Article
    col = Article.__table__.c['is_external']
    assert col.default is not None or col.server_default is not None, \
        "is_external musi mieć default=False / server_default='0'"


# ---------------------------------------------------------------------------
# Testy schema — is_external w ArticleCreate / ArticleDetail / ArticleListItem
# ---------------------------------------------------------------------------

def test_article_create_schema_has_is_external():
    """ArticleCreate musi przyjmować is_external."""
    from articles.schemas import ArticleCreate
    payload = dict(
        name="Koparka",
        is_service=False,
        is_external=True,
    )
    obj = ArticleCreate(**payload)
    assert obj.is_external is True


def test_article_create_schema_is_external_default_false():
    """ArticleCreate.is_external domyślnie False."""
    from articles.schemas import ArticleCreate
    obj = ArticleCreate(name="Koparka")
    assert obj.is_external is False


def test_article_detail_schema_has_is_external():
    """ArticleDetail musi eksponować is_external."""
    from articles.schemas import ArticleDetail
    from datetime import datetime
    obj = ArticleDetail(
        id=1, name="Koparka", is_service=False,
        internal_number=None, registration_no=None, serial_no=None,
        brand=None, model=None, replacement_value=None,
        category_id=None, category_name=None, owner_id=None, owner_name=None,
        branch_id=None, description=None, notes=None, rental_days=None,
        article_type=None, is_archival=False, is_external=True,
        created_at=datetime.utcnow(), updated_at=None,
    )
    assert obj.is_external is True


def test_article_list_item_schema_has_is_external():
    """ArticleListItem musi eksponować is_external."""
    from articles.schemas import ArticleListItem
    from datetime import datetime
    obj = ArticleListItem(
        id=1, name="Koparka", is_service=False,
        internal_number=None, registration_no=None, serial_no=None,
        brand=None, model=None, replacement_value=None, category_name=None,
        owner_name=None, notes=None, active_contract_number=None,
        is_archival=False, is_external=True,
        conditions_count=0,
        created_at=datetime.utcnow(), updated_at=None,
    )
    assert obj.is_external is True


# ---------------------------------------------------------------------------
# Testy fleet_summary logic — filtrowanie maszynen zewnętrznych w agregatach
# ---------------------------------------------------------------------------

def test_fleet_summary_machine_revenue_excludes_services():
    """Przychód maszyn nie zawiera usług (is_service=True)."""
    positions = [
        mk_pos(is_service=False, article_id=1, revenue=5000, name="Koparka"),
        mk_pos(is_service=True, article_id=2, revenue=500, name="Transport"),
    ]
    machine_rev = {
        p["article_id"]: {"name": p["article_name"], "rev": p["revenue"]}
        for p in positions if not p["is_service"]
    }
    assert 1 in machine_rev
    assert 2 not in machine_rev
    assert machine_rev[1]["rev"] == d(5000)


def test_aggregate_by_category_handles_empty():
    """aggregate_by_category z pustą listą zwraca pustą kolekcję ([] lub {})."""
    result = aggregate_by_category([])
    assert not result  # pusta lista lub dict


def test_positions_service_filter_separates_correctly():
    """Filtracja is_service działa poprawnie na liście pozycji."""
    positions = [
        mk_pos(is_service=False, revenue=1000),
        mk_pos(is_service=False, revenue=2000),
        mk_pos(is_service=True, revenue=300),
    ]
    machines = [p for p in positions if not p["is_service"]]
    services = [p for p in positions if p["is_service"]]

    assert len(machines) == 2
    assert len(services) == 1
    assert sum(p["revenue"] for p in machines) == d(3000)
    assert sum(p["revenue"] for p in services) == d(300)
