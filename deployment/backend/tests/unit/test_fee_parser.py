"""Unit tests for migrate.py fee-line parser (_parse_fee_line, _parse_text_to_fees)"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from decimal import Decimal
from migrate import _parse_fee_line, _parse_text_to_fees


# ── _parse_fee_line ───────────────────────────────────────────────────────────

def test_transport_dostawa_odbior():
    r = _parse_fee_line("- Transport: 400.00 zł dostawa / 400.00 zł odbiór")
    assert r['name'] == 'Transport'
    assert r['amount_from'] == Decimal('400.00')
    assert 'dostawa' in (r['description'] or '')

def test_czyszczenie_range():
    r = _parse_fee_line("- Czyszcz.: 150.00 zł - 400.00 zł")
    assert r['name'] == 'Czyszcz.'
    assert r['amount_from'] == Decimal('150.00')
    assert r['amount_to'] == Decimal('400.00')

def test_hourly_range():
    r = _parse_fee_line("- Ponadnorm.: 200.00 zł / h - 300.00 zł / h")
    assert r['name'] == 'Ponadnorm.'
    assert r['amount_from'] == Decimal('200.00')
    assert r['amount_to'] == Decimal('300.00')
    assert r['unit'] == 'h'

def test_per_unit_doba():
    r = _parse_fee_line("- Zawiesia: 50,00 zł / doba")
    assert r['name'] == 'Zawiesia'
    assert r['amount_from'] == Decimal('50.00')
    assert r['unit'] == 'doba'

def test_parens_description():
    r = _parse_fee_line("- Tankowanie: 200.00 zł (plus koszt paliwa)")
    assert r['name'] == 'Tankowanie'
    assert r['amount_from'] == Decimal('200.00')
    assert r['description'] == 'plus koszt paliwa'

def test_simple_amount():
    r = _parse_fee_line("- Transport: 400.00 zł")
    assert r['name'] == 'Transport'
    assert r['amount_from'] == Decimal('400.00')

def test_trailing_text():
    r = _parse_fee_line("- Transport: 950.00 zł - zamiana Ładowarek")
    assert r['name'] == 'Transport'
    assert r['amount_from'] == Decimal('950.00')
    assert 'Ładowarek' in (r['description'] or '')

def test_no_amount_text_only():
    r = _parse_fee_line("- Transport: odbiór własny")
    assert r['name'] == 'Transport'
    assert r['amount_from'] is None

def test_no_colon_kwota_per_unit():
    r = _parse_fee_line("- Ładowarka - wynajem 900,00 zł / doba")
    assert r is not None
    assert r['amount_from'] == Decimal('900.00')
    assert r['unit'] == 'doba'

def test_skip_header_line():
    assert _parse_fee_line("-zedytowane") is None

def test_skip_empty():
    assert _parse_fee_line("") is None
    assert _parse_fee_line("   ") is None

def test_comma_decimal():
    r = _parse_fee_line("- Dostawa: 1 200,00 zł")
    assert r['name'] == 'Dostawa'
    assert r['amount_from'] == Decimal('1200.00')

def test_is_active_default():
    r = _parse_fee_line("- Transport: 400 zł")
    assert r['is_active'] is True


# ── _parse_text_to_fees ───────────────────────────────────────────────────────

def test_multiline_block():
    text = (
        "- Transport: 400.00 zł\n"
        "- Czyszcz.: 150.00 zł - 400.00 zł\n"
        "- Tankowanie: 200.00 zł (plus koszt paliwa)\n"
    )
    fees = _parse_text_to_fees(text)
    assert len(fees) == 3
    assert fees[0]['name'] == 'Transport'
    assert fees[1]['name'] == 'Czyszcz.'
    assert fees[2]['name'] == 'Tankowanie'

def test_sort_order_increments():
    text = "- A: 100 zł\n- B: 200 zł\n- C: 300 zł\n"
    fees = _parse_text_to_fees(text)
    assert [f['sort_order'] for f in fees] == [0, 1, 2]

def test_empty_text():
    assert _parse_text_to_fees("") == []
    assert _parse_text_to_fees(None) == []

def test_skips_noise_lines():
    text = (
        "-zedytowane\n"
        "1-2 dni\n"
        "- Transport: 400.00 zł\n"
        "czas trwania:\n"
    )
    fees = _parse_text_to_fees(text)
    assert len(fees) == 1
    assert fees[0]['name'] == 'Transport'

def test_windows_line_endings():
    text = "- Transport: 400.00 zł\r\n- Czyszcz.: 150.00 zł\r\n"
    fees = _parse_text_to_fees(text)
    assert len(fees) == 2
