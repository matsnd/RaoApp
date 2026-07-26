"""
Unit testy dla RAO-P1-017: statystyki po kategoriach.

Testuje:
- aggregate_by_category() z calc.py (pure function, bez DB)
- Schematy CategoryStatItem / CategoryStatsResponse (Pydantic v2)
"""
from decimal import Decimal
from datetime import date
import pytest

from stats.calc import aggregate_by_category, _FALLBACK_CATEGORY
from stats.schemas import CategoryStatItem, CategoryStatsResponse


def d(val) -> Decimal:
    return Decimal(str(val))


# ── aggregate_by_category — level=main ────────────────────────────────────────

def test_aggregate_main_groups_two_categories():
    positions = [
        {"article_id": 1, "contract_id": 10, "category_main": "Koparki",  "category_sub1": "Mini",      "revenue": d(1000), "clamped_days": 10},
        {"article_id": 2, "contract_id": 11, "category_main": "Koparki",  "category_sub1": "Kołowe",    "revenue": d(500),  "clamped_days": 5},
        {"article_id": 3, "contract_id": 12, "category_main": "Ładowarki","category_sub1": "Telesk.",   "revenue": d(2000), "clamped_days": 20},
    ]
    result = aggregate_by_category(positions, level="main")

    assert len(result) == 2
    # Posortowane malejąco po revenue: Ładowarki (2000) przed Koparki (1500)
    assert result[0]["category_name"] == "Ładowarki"
    assert result[0]["revenue"] == d(2000)
    assert result[0]["articles_count"] == 1
    assert result[0]["rented_days"] == 20
    assert result[0]["contracts_count"] == 1

    assert result[1]["category_name"] == "Koparki"
    assert result[1]["revenue"] == d(1500)
    assert result[1]["articles_count"] == 2
    assert result[1]["rented_days"] == 15
    assert result[1]["contracts_count"] == 2


def test_aggregate_sub1_groups_by_subcategory():
    positions = [
        {"article_id": 1, "contract_id": 10, "category_main": "Koparki", "category_sub1": "Mini",   "revenue": d(300), "clamped_days": 3},
        {"article_id": 2, "contract_id": 11, "category_main": "Koparki", "category_sub1": "Mini",   "revenue": d(200), "clamped_days": 2},
        {"article_id": 3, "contract_id": 12, "category_main": "Koparki", "category_sub1": "Kołowe", "revenue": d(700), "clamped_days": 7},
    ]
    result = aggregate_by_category(positions, level="sub1")

    assert len(result) == 2
    # Kołowe 700 > Mini 500 → Kołowe pierwsze
    assert result[0]["category_name"] == "Kołowe"
    assert result[0]["revenue"] == d(700)
    assert result[1]["category_name"] == "Mini"
    assert result[1]["revenue"] == d(500)


def test_aggregate_none_category_falls_back():
    positions = [
        {"article_id": 1, "contract_id": 10, "category_main": None, "category_sub1": None, "revenue": d(100), "clamped_days": 1},
    ]
    result = aggregate_by_category(positions, level="main")
    assert len(result) == 1
    assert result[0]["category_name"] == _FALLBACK_CATEGORY


def test_aggregate_empty_positions_returns_empty():
    result = aggregate_by_category([], level="main")
    assert result == []


def test_aggregate_deduplicates_articles_within_category():
    """Ta sama maszyna w dwóch umowach w tej samej kategorii → articles_count=1, contracts_count=2."""
    positions = [
        {"article_id": 5, "contract_id": 10, "category_main": "Koparki", "category_sub1": "Mini", "revenue": d(1000), "clamped_days": 10},
        {"article_id": 5, "contract_id": 11, "category_main": "Koparki", "category_sub1": "Mini", "revenue": d(500),  "clamped_days": 5},
    ]
    result = aggregate_by_category(positions, level="main")
    assert result[0]["articles_count"] == 1    # ten sam article_id
    assert result[0]["contracts_count"] == 2   # dwa różne kontrakty


def test_aggregate_deduplicates_contracts_per_category():
    """Dwie pozycje tej samej umowy w tej samej kategorii → contracts_count=1."""
    positions = [
        {"article_id": 1, "contract_id": 10, "category_main": "Koparki", "category_sub1": "Mini", "revenue": d(400), "clamped_days": 4},
        {"article_id": 2, "contract_id": 10, "category_main": "Koparki", "category_sub1": "Mini", "revenue": d(300), "clamped_days": 3},
    ]
    result = aggregate_by_category(positions, level="main")
    assert result[0]["contracts_count"] == 1
    assert result[0]["articles_count"] == 2
    assert result[0]["revenue"] == d(700)


def test_aggregate_mixed_none_and_named_categories():
    """Mix kategorii nazwanej i None → dwie osobne grupy."""
    positions = [
        {"article_id": 1, "contract_id": 1, "category_main": "Koparki", "category_sub1": "A", "revenue": d(500), "clamped_days": 5},
        {"article_id": 2, "contract_id": 2, "category_main": None,       "category_sub1": None,"revenue": d(100), "clamped_days": 1},
    ]
    result = aggregate_by_category(positions, level="main")
    names = {r["category_name"] for r in result}
    assert "Koparki" in names
    assert _FALLBACK_CATEGORY in names
    assert len(result) == 2


def test_aggregate_revenue_sum_correctness():
    """Trzy pozycje w jednej kategorii → suma revenue."""
    positions = [
        {"article_id": i, "contract_id": i, "category_main": "X", "category_sub1": "Y",
         "revenue": d(100 * i), "clamped_days": i}
        for i in range(1, 4)
    ]
    result = aggregate_by_category(positions, level="main")
    assert len(result) == 1
    assert result[0]["revenue"] == d(600)   # 100+200+300
    assert result[0]["rented_days"] == 6    # 1+2+3


# ── CategoryStatItem schema ────────────────────────────────────────────────────

def test_category_stat_item_valid():
    item = CategoryStatItem(
        category_name="Koparki",
        articles_count=5,
        rented_days=120,
        revenue=d("15000.00"),
        contracts_count=10,
    )
    assert item.category_name == "Koparki"
    assert item.articles_count == 5
    assert item.revenue == d("15000.00")


def test_category_stat_item_zero_revenue():
    item = CategoryStatItem(
        category_name="Puste",
        articles_count=0,
        rented_days=0,
        revenue=d("0"),
        contracts_count=0,
    )
    assert item.revenue == Decimal("0")


# ── CategoryStatsResponse schema ──────────────────────────────────────────────

def test_category_stats_response_valid():
    resp = CategoryStatsResponse(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 12, 31),
        level="main",
        total_revenue=d("50000.00"),
        items=[
            CategoryStatItem(
                category_name="Koparki",
                articles_count=3,
                rented_days=90,
                revenue=d("30000.00"),
                contracts_count=5,
            ),
            CategoryStatItem(
                category_name="Ładowarki",
                articles_count=2,
                rented_days=60,
                revenue=d("20000.00"),
                contracts_count=3,
            ),
        ],
    )
    assert resp.level == "main"
    assert len(resp.items) == 2
    assert resp.total_revenue == d("50000.00")
    assert resp.items[0].category_name == "Koparki"


def test_category_stats_response_empty_items():
    resp = CategoryStatsResponse(
        date_from=date(2026, 1, 1),
        date_to=date(2026, 3, 31),
        level="sub1",
        total_revenue=d("0"),
        items=[],
    )
    assert resp.items == []
    assert resp.total_revenue == Decimal("0")
