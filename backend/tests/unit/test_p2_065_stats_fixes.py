"""
Unit testy dla RAO-P2-065: poprawki statystyk po full-team review.

Testy (source-inspection + pure-function):
- #2: /stats/currently-rented uzywa coalesce(Contractor.name, Contract.contractor_name) + LEFT JOIN
- #4: /stats/currently-rented ma warunki is_settled==False + date_to IS NULL
- #8: /explorer/search total = summary.total_count (nie len(results)); city z Contract.city
- #10: walidacja date_from > date_to -> 422 (_validate_date_range)
- #3: /contractors per_page le=500
- #9: shared.locations fallback city z delivery_address
"""
import inspect
from datetime import date

import pytest


def _read_section(path: str, fn_name: str) -> str:
    content = open(path, encoding="utf-8").read()
    start = content.find("async def " + fn_name)
    end = content.find("\n@router.", start + 1)
    if end == -1:
        end = len(content)
    return content[start:end]


# -- #2 + #4: /stats/currently-rented -----------------------------------------


def test_currently_rented_uses_coalesce_with_contractor_join():
    """#2: coalesce(Contractor.name, Contract.contractor_name) + LEFT JOIN."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/stats/router.py", "currently_rented")
    assert "func.coalesce(Contractor.name, Contract.contractor_name)" in s
    assert "outerjoin(Contractor" in s


def test_currently_rented_has_is_settled_false_filter():
    """#4: is_settled==False wyklucza rozliczone umowy."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/stats/router.py", "currently_rented")
    assert "is_settled == False" in s


def test_currently_rented_handles_date_to_null():
    """#4: date_to IS NULL traktowane jako wciaz wynajeta."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/stats/router.py", "currently_rented")
    assert "Contract.date_to.is_(None)" in s


# -- #8: /explorer/search total + city ----------------------------------------


def test_explorer_search_total_uses_summary_count():
    """#8: total = summary.total_count (paginacja)."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/explorer/router.py", "explorer_search")
    assert '"total": summary.total_count' in s


def test_explorer_search_city_uses_contract_city():
    """#8: city z Contract.city (nie delivery_address)."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/explorer/router.py", "explorer_search")
    assert "Contract.city" in s
    assert '"city": row.delivery_address' not in s


# -- #10: walidacja date_from > date_to -> 422 --------------------------------


def test_validate_date_range_raises_422_when_from_after_to():
    from fastapi import HTTPException
    from stats.router import _validate_date_range
    with pytest.raises(HTTPException) as exc_info:
        _validate_date_range(date(2026, 6, 1), date(2026, 1, 1))
    assert exc_info.value.status_code == 422


def test_validate_date_range_passes_when_from_before_to():
    from stats.router import _validate_date_range
    _validate_date_range(date(2026, 1, 1), date(2026, 6, 1))


def test_validate_date_range_passes_when_both_none():
    from stats.router import _validate_date_range
    _validate_date_range(None, None)


def test_validate_date_range_passes_when_equal():
    from stats.router import _validate_date_range
    _validate_date_range(date(2026, 1, 1), date(2026, 1, 1))


def test_validate_date_range_called_in_fleet_summary():
    import stats.router as mod
    src = inspect.getsource(mod.fleet_summary)
    assert "_validate_date_range" in src or "_default_dates" in src


def test_validate_date_range_called_in_top_machines():
    import stats.router as mod
    src = inspect.getsource(mod.top_machines)
    assert "_validate_date_range" in src or "_default_dates" in src


def test_explorer_search_validates_date_range():
    s = _read_section("C:/projects/repos/RaoApp_new/backend/explorer/router.py", "explorer_search")
    assert "date_from > date_to" in s
    assert "422" in s


# -- #3: /contractors per_page limit ------------------------------------------


def test_contractors_per_page_limit_is_500():
    """#3: per_page le=500 (podniesiono z 200)."""
    content = open("C:/projects/repos/RaoApp_new/backend/contractors/router.py", encoding="utf-8").read()
    assert "le=500" in content


# -- #9: shared.locations fallback city z delivery_address --------------------


def test_shared_locations_fetches_delivery_address():
    content = open("C:/projects/repos/RaoApp_new/backend/shared/locations.py", encoding="utf-8").read()
    assert "Contract.delivery_address" in content


def test_shared_locations_fallback_from_delivery_address():
    content = open("C:/projects/repos/RaoApp_new/backend/shared/locations.py", encoding="utf-8").read()
    assert "delivery_address" in content
    assert "re.sub" in content


# -- #11: KPI "Przychód w okresie" label "razem (rzecz.+szac.)" -----------------


def test_fleet_summary_revenue_source_label_mixed_when_both_sources():
    """#11: gdy revenue_actual>0 && revenue_estimate>0 → 'razem (rzecz.+szac.)'."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/stats/router.py", "fleet_summary")
    assert "razem (rzecz.+szac.)" in s
    # warunek: oba źródła > 0
    assert "revenue_actual > 0 and revenue_estimate > 0" in s


# -- #16: explorer/router.py emoji zastąpione wartościami tekstowymi ------------


def test_explorer_search_type_field_is_text_not_emoji():
    """#16: type = 'machine'|'service' (nie emoji 🏗️/🛠️)."""
    s = _read_section("C:/projects/repos/RaoApp_new/backend/explorer/router.py", "explorer_search")
    assert '"service"' in s
    assert '"machine"' in s
    # brak emoji w sekcji
    assert "🏗️" not in s
    assert "🛠️" not in s


# -- #12: get_current_user cache per-request -----------------------------------


def test_get_current_user_caches_per_request():
    """#12: get_current_user używa request.state do cache per-request."""
    content = open("C:/projects/repos/RaoApp_new/backend/auth/dependencies.py", encoding="utf-8").read()
    assert "request.state" in content
    assert "Request" in content