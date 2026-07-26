"""
Jednorazowy skrypt patchujący migrate.py — dodaje step8_csv_categories().
Uruchom raz: python patch_step8.py
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import os, sys

TARGET = os.path.join(os.path.dirname(__file__), "migrate.py")

with open(TARGET, encoding="utf-8") as f:
    src = f.read()

# Sprawdź że nie patched już
if "step8_csv_categories" in src:
    print("SKIP: step8_csv_categories already present")
    sys.exit(0)

# ─── Buduj blok step8 ───
STEP8 = r"""

# =============================================================================
# RAO-P1-017 — CSV → hierarchiczne kategorie → artykuły
# =============================================================================
#
# CSV columns (0-based):
#   0  : artykul3.id  → matchowanie po articles.id
#   7  : Numer wewnętrzny → internal_number
#   8  : Właściwa kategoria główna → level="main"
#   9  : Kategoria I              → level="sub1"
#   10 : Kategoria II             → level="sub2"
#   11 : Kategoria III            → level="sub3"
#   12 : Zasięg   → technical_attributes.zasieg
#   13 : Udźwig   → technical_attributes.udzwig
#   14 : Dodatki  → technical_attributes.dodatki
#
_C_ID = 0; _C_NUMER = 7; _C_CAT_MAIN = 8
_C_CAT_1 = 9; _C_CAT_2 = 10; _C_CAT_3 = 11
_C_ZASIEG = 12; _C_UDZWIG = 13; _C_DODATKI = 14

# Znormalizowane wartości "śmieci" — nie są kategorią (DoD: x, Test, -, '')
_GARBAGE_NORM = frozenset({
    "", "x", "-", "\u2013", "\u2014", "test", "ogolna", "?", "brak", "inne", ".",
})
_TECH_GARBAGE = frozenset({"", "-", "\u2013", "\u2014"})


def normalize_category(name: str) -> str:
    """
    Normalizacja nazwy kategorii do porównań (nie do przechowywania).

    Algorytm:
      1. strip()
      2. NFD decomposition → removes combining diacritical marks (Mn class)
         ó→o, ą→a, ę→e, ś→s, ź→z, ć→c, ń→n, ż→z
      3. Ręczna zamiana ł→l, Ł→L (ł nie ma NFD decomposition)
      4. lowercase + collapse whitespace

    Przykłady:
      "Wózki Widłowe " → "wozki widlowe"
      "Ładowarki Teleskopowe" → "ladowarki teleskopowe"
      "PODNOŚNIKI NOŻYCOWE" → "podnosniki nozycowe"

    Security: brak f-stringów z user input (SQL-INJ-001 safe).
    Stdlib only: unicodedata, re.
    """
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.strip())
    no_dia = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    # ł/Ł nie dekomponują się w NFD — obsługa ręczna
    no_dia = no_dia.replace("\u0142", "l").replace("\u0141", "L")
    return re.sub(r"\s+", " ", no_dia.lower()).strip()


def _is_garbage_cat(val: str) -> bool:
    """True jeśli val to śmieć (x, -, test, ogólna, puste)."""
    return normalize_category(val) in _GARBAGE_NORM


def _clean_cat(val: str) -> "str | None":
    """Stripped lub None dla garbage category values."""
    if not val:
        return None
    s = val.strip()
    return None if _is_garbage_cat(s) else s


def _clean_tech(val: str) -> "str | None":
    """Stripped lub None dla garbage tech values ('-', '–', puste)."""
    if not val:
        return None
    s = val.strip()
    return None if (not s or s in _TECH_GARBAGE) else s


def _parse_csv_file(csv_path: str) -> list:
    """
    Parsowanie CSV Toolsmart.
    CSV-INJ-001 SAFE: csv.reader (NIE eval, NIE f-string z user input).
    Encoding: utf-8-sig obsługuje BOM.
    """
    records = []
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)          # pomiń wiersz nagłówkowy
        for row in reader:
            while len(row) < 15:   # uzupełnij brakujące kolumny
                row.append("")
            id_str = row[_C_ID].strip()
            if not id_str.isdigit():
                continue            # pomiń malformed / powtórzone nagłówki
            records.append({
                "id":              int(id_str),
                "cat_main":        _clean_cat(row[_C_CAT_MAIN]),
                "cat_sub1":        _clean_cat(row[_C_CAT_1]),
                "cat_sub2":        _clean_cat(row[_C_CAT_2]),
                "cat_sub3":        _clean_cat(row[_C_CAT_3]),
                "internal_number": row[_C_NUMER].strip() or None,
                "zasieg":          _clean_tech(row[_C_ZASIEG]),
                "udzwig":          _clean_tech(row[_C_UDZWIG]),
                "dodatki":         _clean_tech(row[_C_DODATKI]),
            })
    return records


async def step8_csv_categories() -> None:
    """
    RAO-P1-017: CSV → hierarchiczne kategorie → UPDATE articles.

    Algorytm:
      1. GET_LOCK('rao_migrate_csv', 0) — ochrona przed race condition
      2. Parsowanie CSV (csv.reader, CSV-INJ-001 safe)
      3. Wczytanie istniejących kategorii → cache w pamięci
         (Python-side diacritic normalization — poprawna obsługa ł)
      4. Budowanie drzewa kategorii (main→sub1→sub2→sub3, sorted):
         - _upsert_cat(): SELECT-or-INSERT → idempotent
         - Kasowanie ON DUPLICATE KEY nie potrzebne (cache gwarantuje 1 SELECT)
      5. UPDATE articles (parametryzowane %s — SQL-INJ-001 safe):
         - category_main/sub1/sub2/sub3  (snapshot nazw z CSV)
         - category_id (FK do najgłębszego poziomu)
         - technical_attributes (JSON: zasieg, udzwig, dodatki)
         - internal_number (COALESCE — ustawia tylko gdy DB=NULL)
      6. Weryfikacja: COUNT queries + stats
      7. RELEASE_LOCK

    Idempotentność (drugi run = 0 zmian):
      - Kategorie: cache hit → brak INSERT
      - Articles: te same wartości → MySQL nie zmienia wiersza

    Security:
      - Wszystkie SQL: parametryzowane %s (SQL-INJ-001 safe)
      - GET_LOCK(name, 0) — nie blokuje wieczności
      - Bez shell=True, bez sekretów w logach
    """
    print("[8] RAO-P1-017: CSV categories → articles ...")

    # ── Znajdź CSV (glob: niezależność od kodowania nazwy pliku na Windows) ──
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    csv_dir      = os.path.join(
        project_root, "spec", "backlog", "archiwum", "refinement"
    )
    csv_matches  = glob.glob(os.path.join(csv_dir, "Asortyment*.csv"))

    if not csv_matches:
        print(f"   WARN: CSV nie znaleziony w {csv_dir!r} — step8 pominieto")
        return

    csv_path = csv_matches[0]
    print(f"   CSV: {os.path.basename(csv_path)}")

    conn = await aiomysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASS, db=DB_NAME,
    )
    cur = await conn.cursor()

    # ── Race-condition guard ──
    await cur.execute("SELECT GET_LOCK(%s, 0)", ("rao_migrate_csv",))
    (lock_acquired,) = await cur.fetchone()
    if lock_acquired != 1:
        print("   WARN: GET_LOCK('rao_migrate_csv') failed — step8 pominieto")
        await cur.close()
        conn.close()
        return

    try:
        # ── Parsuj CSV ──
        records  = _parse_csv_file(csv_path)
        csv_total = len(records)
        print(f"   {csv_total} rekordow z CSV")

        # ── Zaladuj istniejace kategorie do pamieci ──
        # Klucz: (normalize_category(name), level, parent_id) → category_id
        await cur.execute("SELECT id, name, level, parent_id FROM categories")
        cat_cache: dict = {
            (normalize_category(n or ""), lvl, pid): cid
            for cid, n, lvl, pid in await cur.fetchall()
        }
        print(f"   {len(cat_cache)} istniejacych kategorii zaladowanych")

        # ── get-or-insert helper (idempotent) ──
        cats_created = 0

        async def _upsert_cat(canonical: str, level: str, parent_id) -> int:
            """
            SELECT-or-INSERT dla kategorii.
            Idempotent: drugi run → cache hit → brak INSERT.
            SQL-INJ-001: parametryzowane %s.
            """
            nonlocal cats_created
            norm = normalize_category(canonical)
            key  = (norm, level, parent_id)
            if key in cat_cache:
                return cat_cache[key]
            # INSERT nowej kategorii
            await cur.execute(
                "INSERT INTO categories (name, level, parent_id
