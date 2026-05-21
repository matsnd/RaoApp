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
    content = open('C:/projects/repos/RaoApp/backend/explorer/router.py', encoding='utf-8').read()
    # Sprawdź czy w sekcji search jest filtr is_archival
    assert 'is_archival == False' in content, \
        "explorer/router.py nie zawiera filtra is_archival==False!"


def test_explorer_router_services_has_archival_filter():
    """Endpoint /services w explorer musi mieć filtr is_archival==False."""
    content = open('C:/projects/repos/RaoApp/backend/explorer/router.py', encoding='utf-8').read()
    # is_service == True AND is_archival == False
    assert content.count('is_archival == False') >= 2, \
        "explorer/router.py ma za mało filtrów is_archival==False (expected >=2)"


def test_explorer_router_locations_uses_city_not_delivery_address():
    """Endpoint /locations musi grupować po Contract.city, nie delivery_address (RAO-P1-028)."""
    content = open('C:/projects/repos/RaoApp/backend/explorer/router.py', encoding='utf-8').read()

    # Znajdź sekcję get_locations_summary
    start = content.find('async def get_locations_summary')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    locations_section = content[start:end]

    assert 'Contract.city' in locations_section, \
        "get_locations_summary musi używać Contract.city (nie delivery_address)"
    assert '.group_by(Contract.city)' in locations_section, \
        "get_locations_summary musi grupować po Contract.city"


def test_explorer_router_locations_no_extract_city_call():
    """Po przejściu na Contract.city nie powinno być extract_city() w locations summary."""
    content = open('C:/projects/repos/RaoApp/backend/explorer/router.py', encoding='utf-8').read()

    start = content.find('async def get_locations_summary')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    locations_section = content[start:end]

    assert 'extract_city(row.delivery_address)' not in locations_section, \
        "get_locations_summary nie powinno już używać extract_city(delivery_address) — użyj Contract.city"


# ---------------------------------------------------------------------------
# Testy stats/router.py — fleet filters is_external
# ---------------------------------------------------------------------------

def test_stats_router_fleet_summary_has_external_filter():
    """Endpoint /fleet-summary musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp/backend/stats/router.py', encoding='utf-8').read()

    start = content.find('async def fleet_summary')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "fleet_summary musi filtrować Article.is_external==False"


def test_stats_router_currently_rented_has_external_filter():
    """Endpoint /currently-rented musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp/backend/stats/router.py', encoding='utf-8').read()

    start = content.find('async def currently_rented')
    end = content.find('\n@router.', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "currently_rented musi filtrować Article.is_external==False"


def test_stats_router_compute_revenues_has_external_filter():
    """_compute_position_revenues musi wykluczać maszyny zewnętrzne."""
    content = open('C:/projects/repos/RaoApp/backend/stats/router.py', encoding='utf-8').read()

    start = content.find('async def _compute_position_revenues')
    end = content.find('\nasync def ', start + 1)
    if end == -1:
        end = len(content)
    section = content[start:end]

    assert 'is_external == False' in section, \
        "_compute_position_revenues musi filtrować is_external==False"


# ---------------------------------------------------------------------------
# Testy extract_city (legacy — helper musi nadal działać dla /locations/{city})
# ---------------------------------------------------------------------------

def test_extract_city_warszawa():
    """extract_city rozpoznaje Warszawę."""
    from explorer.router import extract_city
    result = extract_city("ul. Marszałkowska 1, 00-001 Warszawa")
    assert "warszawa" in result.lower() or "Warszawa" in result


def test_extract_city_krakow():
    """extract_city rozpoznaje Kraków."""
    from explorer.router import extract_city
    result = extract_city("30-059 Kraków, al. Mickiewicza 30")
    assert "kraków" in result.lower() or "Kraków" in result


def test_extract_city_empty_returns_nieznane():
    """extract_city dla pustego adresu zwraca 'Nieznane'."""
    from explorer.router import extract_city
    result = extract_city("")
    assert result == "Nieznane"


def test_extract_city_none_like_returns_nieznane():
    """extract_city dla None zwraca 'Nieznane'."""
    from explorer.router import extract_city
    result = extract_city(None)
    assert result == "Nieznane"
