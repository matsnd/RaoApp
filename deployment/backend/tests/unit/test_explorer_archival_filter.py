"""
Unit testy dla RAO-P1-028: Eksplorator — filtrowanie archiwalnych + lokalizacje po Contract.city.
"""
import pytest
from datetime import date
from decimal import Decimal


# ---------------------------------------------------------------------------
# Testy explorer/router.py — is_archival filter w SQL expressions
# ---------------------------------------------------------------------------

def test_explorer_router_search_has_archival_filter():
    """Endpoint /search w explorer musi mieć filtr is_archival==False."""
    import ast
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()
    # Sprawdź czy w sekcji search jest filtr is_archival
    assert 'is_archival == False' in content, \
        "explorer/router.py nie zawiera filtra is_archival==False!"


def test_explorer_router_services_has_archival_filter():
    """Endpoint /services w explorer musi mieć filtr is_archival==False."""
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()
    # is_service == True AND is_archival == False
    assert content.count('is_archival == False') >= 2, \
        "explorer/router.py ma za mało filtrów is_archival==False (expected >=2)"


def test_explorer_router_locations_uses_city_not_delivery_address():
    """Endpoint /locations musi używać Contract.city (RAO-P2-028: przez shared/locations)."""
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()

    # Znajdź sekcję get_locations_summary
    start = content.find('async def get_locations_summary')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    locations_section = content[start:end]

    # RAO-P2-028: agregacja przez shared.locations.aggregate_by_pna
    # (które wewnętrznie używa Contract.city + Contract.postal_code_id)
    assert 'aggregate_by_pna' in locations_section, \
        "get_locations_summary musi używać shared.locations.aggregate_by_pna"


def test_explorer_router_locations_no_extract_city_call():
    """Po przejściu na PNA nie powinno być wywołań extract_city() w explorer/router.py."""
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()

    # Funkcja usunięta — sprawdzamy brak definicji i brak wywołań (z nawiasami)
    assert 'def extract_city' not in content, \
        "explorer/router.py nie powinien definiować extract_city"
    assert 'extract_city(' not in content, \
        "explorer/router.py nie powinien wywoływać extract_city() — użyj PNA (postal_code)"


# ---------------------------------------------------------------------------
# Testy stats/router.py — fleet filters is_external
# ---------------------------------------------------------------------------

def test_stats_router_fleet_summary_has_external_filter():
    """Endpoint /fleet-summary musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp_new/backend/stats/router.py', encoding='utf-8').read()

    start = content.find('async def fleet_summary')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "fleet_summary musi filtrować Article.is_external==False"


def test_stats_router_currently_rented_has_external_filter():
    """Endpoint /currently-rented musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp_new/backend/stats/router.py', encoding='utf-8').read()

    start = content.find('async def currently_rented')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "currently_rented musi filtrować Article.is_external==False"


def test_stats_router_compute_revenues_has_external_filter():
    """_compute_position_revenues (RAO-P2-028: w shared/revenue.py) musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp_new/backend/shared/revenue.py', encoding='utf-8').read()

    start = content.find('async def compute_position_revenues')
    end = content.find('\nasync def ', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "compute_position_revenues musi filtrować is_external==False"


# ---------------------------------------------------------------------------
# RAO-P2-028: extract_city USUNIĘTE — drill-down po PNA (postal_code)
# ---------------------------------------------------------------------------

def test_explorer_router_has_no_extract_city_function():
    """RAO-P2-028: extract_city zostało usunięte z explorer/router.py."""
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()
    assert 'def extract_city' not in content, \
        "extract_city powinno być usunięte (legacy regex → PNA deterministyczne)"


def test_explorer_router_location_details_uses_postal_code_path():
    """Endpoint /locations/{postal_code} — drill-down po PNA (BC break z /locations/{city})."""
    content = open('C:/projects/repos/RaoApp_new/backend/explorer/router.py', encoding='utf-8').read()
    assert '@router.get("/locations/{postal_code}")' in content, \
        "endpoint powinien być /locations/{postal_code} (nie /{city})"


def test_shared_locations_module_exists():
    """RAO-P2-028: backend/shared/locations.py istnieje i eksportuje aggregate_by_pna."""
    from shared.locations import aggregate_by_pna, NO_PNA_BUCKET
    assert callable(aggregate_by_pna)
    assert NO_PNA_BUCKET == "(brak PNA)"


def test_shared_revenue_module_exists():
    """RAO-P2-028: backend/shared/revenue.py istnieje i eksportuje compute_position_revenues."""
    from shared.revenue import compute_position_revenues
    assert callable(compute_position_revenues)


def test_location_stat_item_has_rollup_fields():
    """RAO-P2-028: LocationStatItem musi mieć gmina/powiat/wojewodztwo (rollup z postal_codes)."""
    from stats.schemas import LocationStatItem
    fields = LocationStatItem.model_fields
    assert "gmina" in fields, "LocationStatItem musi mieć pole gmina"
    assert "powiat" in fields, "LocationStatItem musi mieć pole powiat"
    assert "wojewodztwo" in fields, "LocationStatItem musi mieć pole wojewodztwo"
