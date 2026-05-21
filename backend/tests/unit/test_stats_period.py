"""
Unit testy dla RAO-P1-026: aggregate_by_period + schematy ByPeriodItem/ByPeriodResponse/CategoriesListNode.
"""
from decimal import Decimal
from datetime import date
import pytest

from stats.calc import aggregate_by_period, aggregate_by_category, _FALLBACK_CATEGORY
from stats.schemas import ByPeriodItem, ByPeriodResponse, CategoriesListNode


def d(val) -> Decimal:
    return Decimal(str(val))


def mk_pos(dt, revenue, clamped_days, contract_id=1, category_main=None):
    return {
        "contract_date_from": dt,
        "revenue": d(revenue),
        "clamped_days": clamped_days,
        "contract_id": contract_id,
        "category_main": category_main,
    }


# -- aggregate_by_period: granularity=month -----------------------------------

def test_by_period_month_single_period():
    pos = [mk_pos(date(2024, 3, 1), 1000, 10, 1), mk_pos(date(2024, 3, 15), 500, 5, 2)]
    r = aggregate_by_period(pos, granularity="month")
    assert len(r) == 1
    assert r[0]["period"] == "2024-03"
    assert r[0]["category_name"] == "__all__"
    assert r[0]["revenue"] == d(1500)
    assert r[0]["rented_days"] == 15
    assert r[0]["contracts_count"] == 2


def test_by_period_month_two_periods():
    pos = [mk_pos(date(2024, 1, 10), 2000, 20, 1), mk_pos(date(2024, 3, 5), 1000, 10, 2)]
    r = aggregate_by_period(pos, granularity="month")
    assert len(r) == 2
    assert r[0]["period"] == "2024-01"
    assert r[1]["period"] == "2024-03"


def test_by_period_year_granularity():
    pos = [
        mk_pos(date(2023, 6, 1), 3000, 30, 1),
        mk_pos(date(2024, 2, 1), 1500, 15, 2),
        mk_pos(date(2024, 11, 1), 500, 5, 3),
    ]
    r = aggregate_by_period(pos, granularity="year")
    assert len(r) == 2
    assert r[0]["period"] == "2023" and r[0]["revenue"] == d(3000)
    assert r[1]["period"] == "2024" and r[1]["revenue"] == d(2000)


def test_by_period_with_category_filter_series():
    pos = [
        mk_pos(date(2024, 1, 1), 1000, 10, 1, "Koparki"),
        mk_pos(date(2024, 1, 5), 500, 5, 2, "Ladowarki"),
        mk_pos(date(2024, 1, 10), 200, 2, 3, None),
    ]
    r = aggregate_by_period(pos, granularity="month", category_main_filter=["Koparki", "Ladowarki"])
    assert len(r) == 3
    names = {x["category_name"] for x in r}
    assert "Koparki" in names and "Ladowarki" in names and _FALLBACK_CATEGORY in names


def test_by_period_no_filter_all_series():
    pos = [mk_pos(date(2024, 5, 1), 1000, 10, 1, "Koparki"), mk_pos(date(2024, 5, 2), 200, 3, 2, "Ladowarki")]
    r = aggregate_by_period(pos, granularity="month", category_main_filter=None)
    assert len(r) == 1
    assert r[0]["category_name"] == "__all__" and r[0]["revenue"] == d(1200)


def test_by_period_skips_missing_date():
    pos = [
        {"contract_date_from": None, "revenue": d(9999), "clamped_days": 99, "contract_id": 1, "category_main": None},
        mk_pos(date(2024, 4, 1), 100, 1, 2),
    ]
    r = aggregate_by_period(pos, granularity="month")
    assert len(r) == 1 and r[0]["revenue"] == d(100)


def test_by_period_empty_returns_empty():
    assert aggregate_by_period([], granularity="month") == []


def test_by_period_deduplicates_contracts():
    pos = [mk_pos(date(2024, 6, 1), 400, 4, 10), mk_pos(date(2024, 6, 10), 200, 2, 10)]
    r = aggregate_by_period(pos, granularity="month")
    assert r[0]["contracts_count"] == 1 and r[0]["revenue"] == d(600)


def test_by_period_sorted_ascending():
    pos = [mk_pos(date(2024, 3, 1), 300, 3, 3), mk_pos(date(2024, 1, 1), 100, 1, 1), mk_pos(date(2024, 2, 1), 200, 2, 2)]
    r = aggregate_by_period(pos, granularity="month")
    periods = [x["period"] for x in r]
    assert periods == sorted(periods)


# -- aggregate_by_category: poziomy sub2/sub3 ---------------------------------

def test_aggregate_sub2_level():
    pos = [
        {"article_id": 1, "contract_id": 1, "category_main": "K", "category_sub1": "Mini",
         "category_sub2": "Gas", "category_sub3": None, "revenue": d(500), "clamped_days": 5},
        {"article_id": 2, "contract_id": 2, "category_main": "K", "category_sub1": "Mini",
         "category_sub2": "Kol", "category_sub3": None, "revenue": d(300), "clamped_days": 3},
        {"article_id": 3, "contract_id": 3, "category_main": "K", "category_sub1": "Mini",
         "category_sub2": "Gas", "category_sub3": None, "revenue": d(200), "clamped_days": 2},
    ]
    r = aggregate_by_category(pos, level="sub2")
    assert len(r) == 2
    assert r[0]["category_name"] == "Gas" and r[0]["revenue"] == d(700)
    assert r[1]["category_name"] == "Kol"


def test_aggregate_sub3_level():
    pos = [
        {"article_id": 1, "contract_id": 1, "category_main": "K", "category_sub1": "A",
         "category_sub2": "B", "category_sub3": "Hydr", "revenue": d(900), "clamped_days": 9},
        {"article_id": 2, "contract_id": 2, "category_main": "K", "category_sub1": "A",
         "category_sub2": "B", "category_sub3": None, "revenue": d(100), "clamped_days": 1},
    ]
    r = aggregate_by_category(pos, level="sub3")
    assert len(r) == 2
    names = {x["category_name"] for x in r}
    assert "Hydr" in names and _FALLBACK_CATEGORY in names


def test_aggregate_unknown_level_fallback_to_main():
    pos = [{"article_id": 1, "contract_id": 1, "category_main": "X", "category_sub1": "Y",
            "category_sub2": "Z", "category_sub3": None, "revenue": d(100), "clamped_days": 1}]
    r = aggregate_by_category(pos, level="INVALID")
    assert len(r) == 1 and r[0]["category_name"] == "X"


# -- ByPeriodItem schema -------------------------------------------------------

def test_by_period_item_valid():
    item = ByPeriodItem(period="2024-03", category_name="__all__", revenue=d("15000"), contracts_count=5, rented_days=30)
    assert item.period == "2024-03" and item.contracts_count == 5


def test_by_period_item_year_period():
    item = ByPeriodItem(period="2024", category_name="Koparki", revenue=d("5000"), contracts_count=2, rented_days=60)
    assert item.period == "2024" and item.category_name == "Koparki"


# -- ByPeriodResponse schema ---------------------------------------------------

def test_by_period_response_valid():
    resp = ByPeriodResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        granularity="month",
        items=[ByPeriodItem(period="2024-01", category_name="__all__", revenue=d("10000"), contracts_count=3, rented_days=31)],
    )
    assert resp.granularity == "month" and len(resp.items) == 1 and resp.items[0].period == "2024-01"


def test_by_period_response_empty():
    resp = ByPeriodResponse(date_from=date(2024, 1, 1), date_to=date(2024, 3, 31), granularity="year", items=[])
    assert resp.items == []


# -- CategoriesListNode schema -------------------------------------------------

def test_categories_list_node_leaf():
    node = CategoriesListNode(id=1, name="Koparki", level="main")
    assert node.id == 1 and node.articles_count == 0 and node.children == []


def test_categories_list_node_with_children():
    child = CategoriesListNode(id=2, name="Mini", level="sub1", articles_count=3)
    parent = CategoriesListNode(id=1, name="Koparki", level="main", children=[child])
    assert len(parent.children) == 1 and parent.children[0].articles_count == 3


def test_categories_list_node_nested():
    grand = CategoriesListNode(id=3, name="Gas", level="sub2", articles_count=5)
    child = CategoriesListNode(id=2, name="Mini", level="sub1", children=[grand])
    root = CategoriesListNode(id=1, name="Koparki", level="main", children=[child])
    data = root.model_dump()
    assert data["children"][0]["children"][0]["name"] == "Gas"
    assert data["children"][0]["children"][0]["articles_count"] == 5
