"""
Unit testy dla RAO-P3-004: eksport statystyk do CSV.

Testuje:
- build_csv_string() — pure function (bez DB, bez HTTP)
  - UTF-8 BOM obecny
  - Poprawne nagłówki dla każdego typu
  - Poprawne wiersze danych
  - Pusty zestaw danych → tylko nagłówek
  - Delimiter środnik (PL Excel)
"""
import pytest

from stats.service import build_csv_string, _CSV_DELIMITER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(csv_str: str) -> list[str]:
    """Zwraca listę niepustych linii z CSV (bez BOM w pierwszej linii)."""
    # csv.writer dodaje \r\n na Windowsie/Linux (dialect=excel domyslnie)
    lines = [ln for ln in csv_str.replace("\r\n", "\n").split("\n") if ln.strip()]
    return lines


# ---------------------------------------------------------------------------
# BOM — warunek konieczny dla Excela PL
# ---------------------------------------------------------------------------

def test_build_csv_starts_with_bom():
    """UTF-8 BOM musi być pierwszym znakiem — inaczej Excel PL nie rozpozna kodowania."""
    result = build_csv_string("contracts", [])
    assert result.startswith("\ufeff"), "CSV musi zaczynać się od UTF-8 BOM (\\ufeff)"


def test_build_csv_articles_starts_with_bom():
    result = build_csv_string("articles", [])
    assert result.startswith("\ufeff")


def test_build_csv_contractors_starts_with_bom():
    result = build_csv_string("contractors", [])
    assert result.startswith("\ufeff")


# ---------------------------------------------------------------------------
# Nagłówki — poprawne kolumny per typ
# ---------------------------------------------------------------------------

def test_build_csv_contracts_headers():
    result = build_csv_string("contracts", [])
    lines = _lines(result)
    header = lines[0].lstrip("\ufeff")  # usuń BOM z pierwszej linii
    cols = header.split(_CSV_DELIMITER)
    assert "nr_umowy" in cols
    assert "kontrahent" in cols
    assert "data_od" in cols
    assert "data_do" in cols
    assert "status" in cols
    assert "handlowiec" in cols
    assert "wartosc_netto" in cols
    assert len(cols) == 7


def test_build_csv_articles_headers():
    result = build_csv_string("articles", [])
    lines = _lines(result)
    header = lines[0].lstrip("\ufeff")
    cols = header.split(_CSV_DELIMITER)
    assert "nazwa" in cols
    assert "kategoria" in cols
    assert "nr_wewn" in cols
    assert "aktywna_umowa" in cols
    assert len(cols) == 4


def test_build_csv_contractors_headers():
    result = build_csv_string("contractors", [])
    lines = _lines(result)
    header = lines[0].lstrip("\ufeff")
    cols = header.split(_CSV_DELIMITER)
    assert "nazwa" in cols
    assert "nip" in cols
    assert "miasto" in cols
    assert "email" in cols
    assert "telefon" in cols
    assert "aktywna_umowa" in cols
    assert len(cols) == 6


# ---------------------------------------------------------------------------
# Puste dane — tylko nagłówek, bez wierszy
# ---------------------------------------------------------------------------

def test_build_csv_empty_contracts_has_only_header():
    result = build_csv_string("contracts", [])
    lines = _lines(result)
    assert len(lines) == 1, "Przy pustych danych CSV powinien mieć tylko nagłówek"


def test_build_csv_empty_articles_has_only_header():
    result = build_csv_string("articles", [])
    lines = _lines(result)
    assert len(lines) == 1


# ---------------------------------------------------------------------------
# Wiersze danych — zawartość
# ---------------------------------------------------------------------------

def test_build_csv_contracts_data_row():
    rows = [{
        "nr_umowy": "U/2024/001",
        "kontrahent": "Firma ABC",
        "data_od": "01.01.2024",
        "data_do": "31.12.2024",
        "status": "aktywna",
        "handlowiec": "Jan Kowalski",
        "wartosc_netto": "5000,00",
    }]
    result = build_csv_string("contracts", rows)
    assert "U/2024/001" in result
    assert "Firma ABC" in result
    assert "aktywna" in result
    assert "Jan Kowalski" in result
    assert "5000,00" in result
    lines = _lines(result)
    assert len(lines) == 2  # nagłówek + 1 wiersz danych


def test_build_csv_articles_data_row():
    rows = [{
        "nazwa": "Koparka XL",
        "kategoria": "Koparki",
        "nr_wewn": "KOP-001",
        "aktywna_umowa": "tak",
    }]
    result = build_csv_string("articles", rows)
    assert "Koparka XL" in result
    assert "Koparki" in result
    assert "KOP-001" in result
    assert "tak" in result
    lines = _lines(result)
    assert len(lines) == 2


def test_build_csv_contractors_data_row():
    rows = [{
        "nazwa": "Budmix Sp. z o.o.",
        "nip": "1234567890",
        "miasto": "Warszawa",
        "email": "biuro@budmix.pl",
        "telefon": "600123456",
        "aktywna_umowa": "nie",
    }]
    result = build_csv_string("contractors", rows)
    assert "Budmix Sp. z o.o." in result
    assert "1234567890" in result
    assert "Warszawa" in result
    assert "nie" in result


# ---------------------------------------------------------------------------
# Delimiter — środnik dla PL Excel
# ---------------------------------------------------------------------------

def test_build_csv_uses_semicolon_delimiter():
    """Delimiter musi być średnik dla polskiego Excela (decimal separator = przecinek)."""
    rows = [{
        "nr_umowy": "A", "kontrahent": "B", "data_od": "01.01.2024",
        "data_do": "31.12.2024", "status": "aktywna",
        "handlowiec": "", "wartosc_netto": "100,00",
    }]
    result = build_csv_string("contracts", rows)
    lines = _lines(result)
    header = lines[0].lstrip("\ufeff")
    assert ";" in header, f"Delimiter powinien być ';', nagłówek: {header!r}"


# ---------------------------------------------------------------------------
# Brakujące klucze — graceful fallback
# ---------------------------------------------------------------------------

def test_build_csv_missing_key_falls_back_to_empty():
    """Brakujący klucz w dict → pusty string (nie rzuca wyjątku)."""
    rows = [{"nazwa": "Test Maszyna"}]  # brak pozostałych kluczy
    result = build_csv_string("articles", rows)
    assert "Test Maszyna" in result
    # Sprawdź że mamy 4 kolumny (3 puste)
    lines = _lines(result)
    data_line = lines[1]
    cols = data_line.split(";")
    assert len(cols) == 4


# ---------------------------------------------------------------------------
# Wiele wierszy
# ---------------------------------------------------------------------------

def test_build_csv_multiple_rows():
    rows = [
        {"nazwa": "Maszyna A", "kategoria": "Kat1", "nr_wewn": "M-001", "aktywna_umowa": "tak"},
        {"nazwa": "Maszyna B", "kategoria": "Kat2", "nr_wewn": "M-002", "aktywna_umowa": "nie"},
        {"nazwa": "Maszyna C", "kategoria": "Kat1", "nr_wewn": "M-003", "aktywna_umowa": "tak"},
    ]
    result = build_csv_string("articles", rows)
    lines = _lines(result)
    assert len(lines) == 4  # nagłówek + 3 wiersze
    assert "Maszyna A" in result
    assert "Maszyna C" in result
