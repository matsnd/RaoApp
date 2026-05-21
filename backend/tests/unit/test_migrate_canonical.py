"""
Testy jednostkowe dla canonical category mapping w migrate.py.
RAO-P1-026 — normalizacja wariantów nazw kategorii z CSV.
"""
import io
import sys
import importlib
import unittest.mock
import pytest

# ── Import migrate.py z zamockowanymi zależnościami DB i stdout ────────────
# migrate.py robi sys.stdout = TextIOWrapper(...) na poziomie modułu —
# patchujemy, żeby nie zepsuć przechwytywania output przez pytest.
_DB_MOCKS = {
    "database":               unittest.mock.MagicMock(),
    "auth.models":            unittest.mock.MagicMock(),
    "contractors.models":     unittest.mock.MagicMock(),
    "articles.models":        unittest.mock.MagicMock(),
    "contracts.models":       unittest.mock.MagicMock(),
    "settings.models":        unittest.mock.MagicMock(),
    "categories.models":      unittest.mock.MagicMock(),
    "integrations.models":    unittest.mock.MagicMock(),
    "aiomysql":               unittest.mock.MagicMock(),
    "bcrypt":                 unittest.mock.MagicMock(),
    "sqlalchemy":             unittest.mock.MagicMock(),
    "sqlalchemy.ext":         unittest.mock.MagicMock(),
    "sqlalchemy.ext.asyncio": unittest.mock.MagicMock(),
}

_orig_stdout = sys.stdout

with unittest.mock.patch.dict("sys.modules", _DB_MOCKS), \
     unittest.mock.patch("io.TextIOWrapper", return_value=_orig_stdout):
    # Upewnij się, że moduł nie jest już w sys.modules z poprzedniego importu
    sys.modules.pop("migrate", None)
    migrate = importlib.import_module("migrate")

# Przywróć stdout w razie gdyby migrate go zmienił
sys.stdout = _orig_stdout

normalize_category       = migrate.normalize_category
_apply_canonical_mapping = migrate._apply_canonical_mapping
_MAIN_CAT_OVERRIDES      = migrate._MAIN_CAT_OVERRIDES
_SUB1_CAT_OVERRIDES      = migrate._SUB1_CAT_OVERRIDES


# ── normalize_category ────────────────────────────────────────────────────────

def test_normalize_strips_whitespace():
    assert normalize_category("  Koparki  ") == "koparki"


def test_normalize_removes_polish_diacritics():
    assert normalize_category("Ładowarka") == "ladowarka"
    assert normalize_category("żuraw") == "zuraw"
    assert normalize_category("Podnośnik") == "podnosnik"


def test_normalize_lowercase():
    assert normalize_category("KOPARKI") == "koparki"


def test_normalize_collapses_whitespace():
    assert normalize_category("Mini  żuraw") == "mini zuraw"


# ── _MAIN_CAT_OVERRIDES keys ──────────────────────────────────────────────────

def test_main_overrides_has_singular_ladowarka():
    assert "ladowarka teleskopowa" in _MAIN_CAT_OVERRIDES


def test_main_overrides_has_lowercase_ladowarki():
    assert "ladowarki teleskopowe" in _MAIN_CAT_OVERRIDES


def test_main_overrides_has_mini_zuraw():
    assert "mini zuraw" in _MAIN_CAT_OVERRIDES


# ── helpers ───────────────────────────────────────────────────────────────────

def _rec(cm=None, cs1=None, cs2=None, cs3=None):
    return {"cat_main": cm, "cat_sub1": cs1, "cat_sub2": cs2, "cat_sub3": cs3}


def _apply(recs):
    _apply_canonical_mapping(recs)
    return recs


# ── main overrides ────────────────────────────────────────────────────────────

def test_singular_ladowarka_teleskopowa_merged():
    recs = _apply([_rec("Ładowarka teleskopowa")])
    assert recs[0]["cat_main"] == "Ładowarki Teleskopowe"


def test_lowercase_variant_ladowarki_teleskopowe_merged():
    recs = _apply([_rec("Ładowarki teleskopowe")])
    assert recs[0]["cat_main"] == "Ładowarki Teleskopowe"


def test_canonical_ladowarki_teleskopowe_unchanged():
    recs = _apply([_rec("Ładowarki Teleskopowe")])
    assert recs[0]["cat_main"] == "Ładowarki Teleskopowe"


def test_mini_zuraw_with_space_merged():
    recs = _apply([_rec("Mini żuraw")])
    assert recs[0]["cat_main"] == "Miniżuraw"


def test_minizuraw_canonical_unchanged():
    recs = _apply([_rec("Miniżuraw")])
    assert recs[0]["cat_main"] == "Miniżuraw"


def test_unrelated_main_not_modified():
    recs = _apply([_rec("Podnośniki Koszowe")])
    assert recs[0]["cat_main"] == "Podnośniki Koszowe"


def test_none_main_not_modified():
    recs = _apply([_rec(None)])
    assert recs[0]["cat_main"] is None


# ── sub1 overrides ────────────────────────────────────────────────────────────

def test_sub1_singular_obrotowa_normalized():
    recs = _apply([_rec("Ładowarka teleskopowa", "Ładowarka teleskopowa obrotowa")])
    assert recs[0]["cat_main"] == "Ładowarki Teleskopowe"
    assert recs[0]["cat_sub1"] == "Ładowarki Teleskopowe Obrotowe"


def test_sub1_lowercase_sztywne_normalized():
    recs = _apply([_rec("Ładowarki teleskopowe", "Ładowarki teleskopowe sztywne")])
    assert recs[0]["cat_main"] == "Ładowarki Teleskopowe"
    assert recs[0]["cat_sub1"] == "Ładowarki Teleskopowe Sztywne"


def test_sub1_already_canonical_obrotowe_unchanged():
    recs = _apply([_rec("Ładowarki Teleskopowe", "Ładowarki Teleskopowe Obrotowe")])
    assert recs[0]["cat_sub1"] == "Ładowarki Teleskopowe Obrotowe"


# ── structural fix 3: pusty main ─────────────────────────────────────────────

def test_structural_fix_empty_main_podnosnik_koszowy():
    recs = _apply([_rec(None, "Podnośnik koszowy na samochodzie")])
    assert recs[0]["cat_main"] == "Podnośnik na samochodzie"
    assert recs[0]["cat_sub1"] == "Podnośnik koszowy na samochodzie"


def test_structural_fix_empty_main_other_sub1_not_touched():
    recs = _apply([_rec(None, "Minikoparki")])
    assert recs[0]["cat_main"] is None


# ── structural fix 4: Akcesoria sub2 → sub1 promote ──────────────────────────

def test_structural_fix_akcesoria_promotes_sub2_to_sub1():
    recs = _apply([_rec("Akcesoria", None, "Przedłużenie wideł")])
    assert recs[0]["cat_sub1"] == "Przedłużenie wideł"
    assert recs[0]["cat_sub2"] is None


def test_structural_fix_akcesoria_promotes_sub3_to_sub2():
    recs = _apply([_rec("Akcesoria", None, "Sub2", "Sub3")])
    assert recs[0]["cat_sub1"] == "Sub2"
    assert recs[0]["cat_sub2"] == "Sub3"
    assert recs[0]["cat_sub3"] is None


def test_structural_fix_akcesoria_with_sub1_not_promoted():
    recs = _apply([_rec("Akcesoria", "Hak obrotowy", "IgnoreMe")])
    assert recs[0]["cat_sub1"] == "Hak obrotowy"
    assert recs[0]["cat_sub2"] == "IgnoreMe"


def test_structural_fix_non_akcesoria_not_promoted():
    recs = _apply([_rec("Inne", None, "Sub2")])
    assert recs[0]["cat_sub1"] is None


# ── idempotentność ────────────────────────────────────────────────────────────

def test_idempotent_double_apply():
    recs = [_rec("Ładowarka teleskopowa", "Ładowarka teleskopowa obrotowa")]
    _apply_canonical_mapping(recs)
    first_main = recs[0]["cat_main"]
    first_sub1 = recs[0]["cat_sub1"]
    _apply_canonical_mapping(recs)
    assert recs[0]["cat_main"] == first_main
    assert recs[0]["cat_sub1"] == first_sub1


# ── _parse_numeric ────────────────────────────────────────────────────────────

def test_parse_numeric_basic():
    pn = migrate._parse_numeric
    assert pn("21m") == 21.0
    assert pn("5t") == 5.0
    assert pn("21.5") == 21.5
    assert pn("21,5") == 21.5
    assert pn("-") is None
    assert pn("") is None
    assert pn(None) is None
    assert pn("x") is None
    assert pn("0") is None   # 0 → None (not a valid measurement)
