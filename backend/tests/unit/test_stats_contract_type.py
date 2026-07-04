"""
Unit testy dla RAO-P2-056: statystyki po contract_type (S=najem, U=usługa).

Testuje:
- aggregate_by_contract_type() z calc.py (pure function, bez DB)
- Schematy ContractTypeStatItem / ContractTypeStatsResponse (Pydantic v2)
- RAO-P2-053: pola paginacji w PositionStatsResponse (total_count, limit, offset)
"""
from decimal import Decimal
from datetime import date
import pytest

from stats.calc import aggregate_by_contract_type
from stats.schemas import (
    ContractTypeStatItem,
    ContractTypeStatsResponse,
    PositionStatsResponse,
    PositionStatItem,
)


def d(val) -> Decimal:
    return Decimal(str(val))


def mk_pos(contract_id, article_id, revenue, clamped_days, contract_type="S", is_service=False):
    return {
        "contract_id": contract_id,
        "article_id": article_id,
        "revenue": d(revenue),
        "clamped_days": clamped_days,
        "contract_type": contract_type,
        "is_service": is_service,
    }


# ── aggregate_by_contract_type ────────────────────────────────────────────────

def test_aggregate_groups_S_and_U():
    positions = [
        mk_pos(1, 100, 1000, 10, "S"),
        mk_pos(1, 101, 500, 5, "S"),
        mk_pos(2, 200, 2000, 20, "U", is_service=True),
    ]
    result = aggregate_by_contract_type(positions)

    assert len(result) == 2
    # Sortowane rosnąco po contract_type: "S" przed "U"
    assert result[0]["contract_type"] == "S"
    assert result[0]["contract_type_label"] == "najem"
    assert result[0]["contracts_count"] == 1   # umowa 1
    assert result[0]["positions_count"] == 2
    assert result[0]["articles_count"] == 2     # artykuły 100, 101
    assert result[0]["rented_days"] == 15       # 10 + 5
    assert result[0]["revenue"] == d(1500)

    assert result[1]["contract_type"] == "U"
    assert result[1]["contract_type_label"] == "usługa"
    assert result[1]["contracts_count"] == 1   # umowa 2
    assert result[1]["positions_count"] == 1
    assert result[1]["revenue"] == d(2000)
    # rented_days = 0 dla usług (is_service=True)
    assert result[1]["rented_days"] == 0


def test_aggregate_multiple_contracts_same_type():
    positions = [
        mk_pos(1, 100, 1000, 10, "S"),
        mk_pos(2, 101, 500, 5, "S"),
        mk_pos(3, 102, 300, 3, "S"),
    ]
    result = aggregate_by_contract_type(positions)

    assert len(result) == 1
    assert result[0]["contract_type"] == "S"
    assert result[0]["contracts_count"] == 3   # 3 unikalne umowy
    assert result[0]["positions_count"] == 3
    assert result[0]["articles_count"] == 3
    assert result[0]["rented_days"] == 18
    assert result[0]["revenue"] == d(1800)


def test_aggregate_empty_list():
    result = aggregate_by_contract_type([])
    assert result == []


def test_aggregate_falls_back_to_S_when_contract_type_missing():
    # Pozycja bez contract_type (np. stare dane) → fallback "S"
    positions = [mk_pos(1, 100, 1000, 10, contract_type=None)]
    result = aggregate_by_contract_type(positions)
    assert len(result) == 1
    assert result[0]["contract_type"] == "S"


def test_aggregate_unknown_type_label_falls_back_to_code():
    # Nieznany contract_type → label = kod (nie crash)
    positions = [mk_pos(1, 100, 1000, 10, contract_type="X")]
    result = aggregate_by_contract_type(positions)
    assert len(result) == 1
    assert result[0]["contract_type"] == "X"
    assert result[0]["contract_type_label"] == "X"


def test_aggregate_rented_days_excludes_services():
    # Usługa (is_service=True) nie liczy rented_days nawet jeśli clamped_days > 0
    positions = [
        mk_pos(1, 100, 1000, 10, "S", is_service=False),
        mk_pos(1, 200, 500, 20, "S", is_service=True),
    ]
    result = aggregate_by_contract_type(positions)
    assert result[0]["rented_days"] == 10  # tylko maszyna
    assert result[0]["revenue"] == d(1500)  # obie pozycje wliczone do przychodu


# ── Schematy ──────────────────────────────────────────────────────────────────

def test_contract_type_stat_item_schema():
    item = ContractTypeStatItem(
        contract_type="S",
        contract_type_label="najem",
        contracts_count=5,
        positions_count=12,
        articles_count=8,
        rented_days=120,
        revenue=d(15000),
    )
    assert item.contract_type == "S"
    assert item.revenue == d(15000)


def test_contract_type_stats_response_schema():
    resp = ContractTypeStatsResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        total_revenue=d(30000),
        items=[
            ContractTypeStatItem(
                contract_type="S", contract_type_label="najem",
                contracts_count=5, positions_count=12, articles_count=8,
                rented_days=120, revenue=d(20000),
            ),
            ContractTypeStatItem(
                contract_type="U", contract_type_label="usługa",
                contracts_count=3, positions_count=6, articles_count=4,
                rented_days=0, revenue=d(10000),
            ),
        ],
    )
    assert resp.total_revenue == d(30000)
    assert len(resp.items) == 2


# ── RAO-P2-053: pola paginacji w PositionStatsResponse ────────────────────────

def test_position_stats_response_has_pagination_fields():
    """RAO-P2-053: PositionStatsResponse musi mieć total_count, limit, offset."""
    resp = PositionStatsResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        type="all",
        total_revenue=d(10000),
        total_machines_revenue=d(8000),
        total_services_revenue=d(2000),
        total_count=150,
        limit=50,
        offset=0,
        items=[
            PositionStatItem(
                article_id=1, article_name="Koparka", internal_number="K001",
                is_service=False, category_main="Koparki",
                revenue=d(1000), rented_days=10, contracts_count=2, times_billed=3,
            ),
        ],
    )
    assert resp.total_count == 150
    assert resp.limit == 50
    assert resp.offset == 0


def test_position_stats_response_pagination_fields_optional():
    """RAO-P2-053: brak limitu (backward compat) — limit=None, total_count default 0."""
    resp = PositionStatsResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2024, 12, 31),
        type="all",
        total_revenue=d(10000),
        total_machines_revenue=d(8000),
        total_services_revenue=d(2000),
        items=[],
    )
    # total_count ma default 0, limit ma default None, offset ma default 0
    assert resp.total_count == 0
    assert resp.limit is None
    assert resp.offset == 0
