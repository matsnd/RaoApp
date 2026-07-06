"""
Unit testy dla RAO-P1-055: statystyki po oddziałach (branch).

Testuje:
- aggregate_by_branch() z calc.py (pure function, bez DB)
- Schematy BranchStatItem / ByBranchStatsResponse (Pydantic v2)
- Sortowanie: malejąco po revenue, wiersz "(bez oddziału)" zawsze na końcu
- Mapowanie branch_id → branch_name z listy branches
- Edge cases: pusta lista, same usługi (rented_days=0), brak mapowania nazwy
"""
from decimal import Decimal
from datetime import date
import pytest

from stats.calc import aggregate_by_branch
from stats.schemas import BranchStatItem, ByBranchStatsResponse


def d(val) -> Decimal:
    return Decimal(str(val))


def mk_pos(contract_id, article_id, revenue, clamped_days, branch_id, is_service=False):
    return {
        "contract_id": contract_id,
        "article_id": article_id,
        "revenue": d(revenue),
        "clamped_days": clamped_days,
        "is_service": is_service,
        "branch_id": branch_id,
    }


# ── aggregate_by_branch ───────────────────────────────────────────────────────

def test_aggregate_groups_by_branch():
    positions = [
        mk_pos(1, 100, 1000, 10, branch_id=3),
        mk_pos(1, 101, 500, 5, branch_id=3),
        mk_pos(2, 200, 2000, 20, branch_id=4),
    ]
    branches = [{"id": 3, "name": "Warszawa"}, {"id": 4, "name": "Gdańsk"}]
    result = aggregate_by_branch(positions, branches=branches)

    assert len(result) == 2
    # Sortowane malejąco po revenue: Gdańsk (2000) przed Warszawą (1500)
    assert result[0]["branch_id"] == 4
    assert result[0]["branch_name"] == "Gdańsk"
    assert result[0]["contracts_count"] == 1
    assert result[0]["positions_count"] == 1
    assert result[0]["articles_count"] == 1
    assert result[0]["rented_days"] == 20
    assert result[0]["revenue"] == d(2000)

    assert result[1]["branch_id"] == 3
    assert result[1]["branch_name"] == "Warszawa"
    assert result[1]["contracts_count"] == 1   # umowa 1
    assert result[1]["positions_count"] == 2
    assert result[1]["articles_count"] == 2     # artykuły 100, 101
    assert result[1]["rented_days"] == 15       # 10 + 5
    assert result[1]["revenue"] == d(1500)


def test_aggregate_multiple_contracts_same_branch():
    positions = [
        mk_pos(1, 100, 1000, 10, branch_id=3),
        mk_pos(2, 101, 500, 5, branch_id=3),
        mk_pos(3, 102, 300, 3, branch_id=3),
    ]
    result = aggregate_by_branch(positions, branches=[{"id": 3, "name": "Warszawa"}])

    assert len(result) == 1
    assert result[0]["branch_id"] == 3
    assert result[0]["contracts_count"] == 3   # 3 unikalne umowy
    assert result[0]["positions_count"] == 3
    assert result[0]["articles_count"] == 3
    assert result[0]["rented_days"] == 18
    assert result[0]["revenue"] == d(1800)


def test_aggregate_empty_list():
    result = aggregate_by_branch([])
    assert result == []


def test_aggregate_unassigned_branch_at_end():
    """Wiersz '(bez oddziału)' (branch_id=None) zawsze na końcu, nawet jeśli revenue wyższy."""
    positions = [
        mk_pos(1, 100, 500, 5, branch_id=3),
        mk_pos(2, 200, 5000, 50, branch_id=None),  # bez oddziału, ale revenue wyższe
    ]
    branches = [{"id": 3, "name": "Warszawa"}]
    result = aggregate_by_branch(positions, branches=branches)

    assert len(result) == 2
    # Warszawa (branch_id=3) pierwsza mimo niższego revenue
    assert result[0]["branch_id"] == 3
    assert result[0]["branch_name"] == "Warszawa"
    # "(bez oddziału)" na końcu
    assert result[1]["branch_id"] is None
    assert result[1]["branch_name"] == "(bez oddziału)"
    assert result[1]["revenue"] == d(5000)


def test_aggregate_no_branches_map_falls_back_to_id_label():
    """Brak mapowania branch_id → nazwa → fallback 'Oddział #{id}'."""
    positions = [mk_pos(1, 100, 1000, 10, branch_id=99)]
    result = aggregate_by_branch(positions, branches=None)

    assert len(result) == 1
    assert result[0]["branch_id"] == 99
    assert result[0]["branch_name"] == "Oddział #99"


def test_aggregate_partial_branches_map():
    """Tylko część branch_id ma mapowanie nazwy — reszta fallback."""
    positions = [
        mk_pos(1, 100, 1000, 10, branch_id=3),
        mk_pos(2, 200, 500, 5, branch_id=99),
    ]
    branches = [{"id": 3, "name": "Warszawa"}]  # brak id=99
    result = aggregate_by_branch(positions, branches=branches)

    assert len(result) == 2
    warsaw = next(r for r in result if r["branch_id"] == 3)
    assert warsaw["branch_name"] == "Warszawa"
    other = next(r for r in result if r["branch_id"] == 99)
    assert other["branch_name"] == "Oddział #99"


def test_aggregate_rented_days_excludes_services():
    """Usługa (is_service=True) nie liczy rented_days nawet jeśli clamped_days > 0."""
    positions = [
        mk_pos(1, 100, 1000, 10, branch_id=3, is_service=False),
        mk_pos(1, 200, 500, 20, branch_id=3, is_service=True),
    ]
    result = aggregate_by_branch(positions, branches=[{"id": 3, "name": "Warszawa"}])
    assert result[0]["rented_days"] == 10  # tylko maszyna
    assert result[0]["revenue"] == d(1500)  # obie pozycje wliczone do przychodu


def test_aggregate_all_unassigned():
    """Wszystkie pozycje bez branch_id → jeden wiersz '(bez oddziału)'."""
    positions = [
        mk_pos(1, 100, 1000, 10, branch_id=None),
        mk_pos(2, 200, 500, 5, branch_id=None),
    ]
    result = aggregate_by_branch(positions, branches=[])
    assert len(result) == 1
    assert result[0]["branch_id"] is None
    assert result[0]["branch_name"] == "(bez oddziału)"
    assert result[0]["contracts_count"] == 2
    assert result[0]["revenue"] == d(1500)


# ── Schematy ──────────────────────────────────────────────────────────────────

def test_branch_stat_item_schema():
    item = BranchStatItem(
        branch_id=3,
        branch_name="RAO Warszawa (HQ)",
        contracts_count=56,
        positions_count=75,
        articles_count=5,
        rented_days=1321,
        revenue=d(786800),
    )
    assert item.branch_id == 3
    assert item.revenue == d(786800)
    assert item.rented_days == 1321


def test_branch_stat_item_none_branch_id():
    """branch_id=None jest poprawne (umowy bez przypisanego oddziału)."""
    item = BranchStatItem(
        branch_id=None,
        branch_name="(bez oddziału)",
        contracts_count=5,
        positions_count=8,
        articles_count=3,
        rented_days=20,
        revenue=d(2500),
    )
    assert item.branch_id is None
    assert item.branch_name == "(bez oddziału)"


def test_by_branch_stats_response_schema():
    resp = ByBranchStatsResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2026, 12, 31),
        total_revenue=d(888450),
        items=[
            BranchStatItem(
                branch_id=3, branch_name="RAO Warszawa (HQ)",
                contracts_count=56, positions_count=75, articles_count=5,
                rented_days=1321, revenue=d(786800),
            ),
            BranchStatItem(
                branch_id=4, branch_name="RAO Gdańsk",
                contracts_count=6, positions_count=8, articles_count=5,
                rented_days=172, revenue=d(101650),
            ),
        ],
    )
    assert resp.total_revenue == d(888450)
    assert len(resp.items) == 2
    assert resp.items[0].branch_name == "RAO Warszawa (HQ)"
    assert resp.items[1].branch_name == "RAO Gdańsk"


def test_by_branch_stats_response_empty_items():
    """Pusta odpowiedź (brak danych w zakresie dat) — items=[]."""
    resp = ByBranchStatsResponse(
        date_from=date(2024, 1, 1),
        date_to=date(2024, 1, 31),
        total_revenue=d(0),
        items=[],
    )
    assert resp.items == []
    assert resp.total_revenue == d(0)
