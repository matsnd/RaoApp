"""
Migration: old dump (toolsmart_roa) -> rao_new
Step 5b added: migrate umowa2.OPLATY -> contract_service_fees (free-text parsing).
Step 18 added: service_hours table (new functionality - empty on migration).

Verified source tables from dump:
  firma(41)  kategoria(4)  oddzial(7)  handlowiec(4)  stawka(4)
  kontrahent2(24)  artykul3(17)  uzytkownik(8)
  umowa2(34)  umowa_pozycja3(15)  umowa_pozycja2_warunek(9)
  adres_dostawy(16) - linked to umowa, not kontrahent

Strategy:
  1. DROP+CREATE rao_new
  2. Import dump via mysql CLI  -> old Polish tables appear
  3. CREATE new English tables  -> SQLAlchemy models
  4. INSERT...SELECT old->new      -> deterministic column mapping
  5. Build service_fee_templates from firma.oplata_* columns
  6. DROP old tables + views
  7. Rehash plaintext passwords with bcrypt

Note: service_hours table is NEW (no old data) - will be empty after migration.
      Users will add data through the UI for service contracts.

Usage: python migrate.py
"""
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Get absolute path for dump file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMP_PATH = os.path.join(project_root, "spec", "backlog", "archiwum", "refinement", "toolsmart_roa_1779053066.sql")
import asyncio
import csv
import glob
import json
import re
import secrets
import subprocess
import string
import sys
import unicodedata
from decimal import Decimal, InvalidOperation

import bcrypt
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine

from database import Base
import auth.models         # noqa
import contractors.models  # noqa
import articles.models     # noqa
import contracts.models    # noqa
import settings.models     # noqa
import categories.models   # noqa
import integrations.models # noqa


def generate_temp_password(length: int = 16) -> str:
    """Generate random temporary password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "rao_user"
DB_PASS = "RaoPass2026!"
DB_NAME = "rao_new"
# DUMP_PATH is now defined above as absolute path

# Every object imported from the dump (tables + views) to drop at the end
OLD_OBJECTS = [
    # views first (DROP VIEW)
    "artykuly", "artykulyy", "dane", "imp_kontrahentow", "imp_przedmiotow",
    "kontrahenci", "nr_umowy", "oplaty", "pozycje", "pozycje2",
    "rao_dshb", "rozliczenie_rpt", "umowy", "umowy1", "warunki",
    # tables
    "a", "adres", "adres_dostawy", "artykul", "artykul2", "artykul3",
    "dostawa", "firma", "handlowiec", "imp", "imp_kontrahent",
    "imp_przedmiot", "imp_rozliczenie", "kategoria", "kontakt",
    "kontrahent", "kontrahent2", "koszt", "koszt_typ", "lp", "oddo",
    "oddzial", "rozliczenie", "stawka", "temp", "u",
    "umowa", "umowa2", "umowa_oddzial", "umowa_pozycja", "umowa_pozycja2",
    "umowa_pozycja2_warunek", "umowa_pozycja3", "uzytkownik", "zdarzenie",
]


async def step1_recreate_db():
    print("[1/7] DROP + CREATE rao_new …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS)
    cur = await conn.cursor()
    await cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`")
    await cur.execute(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    await conn.commit()
    await cur.close()
    conn.close()
    print("   OK")


def step2_import_dump():
    print("[2/7] Import dump via mysql CLI …")
    cmd = f'cmd /c "mysql -h {DB_HOST} -P {DB_PORT} -u {DB_USER} -p{DB_PASS} {DB_NAME} < {DUMP_PATH}"'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    if r.returncode != 0:
        stderr_msg = r.stderr[:300] if r.stderr else "No stderr output"
        print(f"   WARN: {stderr_msg}")
    else:
        print("   OK")


async def step3_create_schema():
    print("[3/7] CREATE new tables from SQLAlchemy models …")
    engine = create_async_engine(
        f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        echo=False,
    )
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("   OK")


async def step4_migrate_data():
    """Deterministic column-by-column mapping verified against dump schema."""
    print("[4/7] INSERT … SELECT  old → new …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Diagnostic: show rodzaj distribution to verify is_service mapping
    await cur.execute("SELECT rodzaj, COUNT(*) FROM artykul3 GROUP BY rodzaj ORDER BY COUNT(*) DESC")
    print("   [diag] artykul3.rodzaj distribution:")
    for row in await cur.fetchall():
        print(f"          {row[0]!r}: {row[1]}")

    await cur.execute("SET FOREIGN_KEY_CHECKS = 0")

    # ── firma → company ──
    # firma: id, nazwa, nazwa_krotka, nip, regon, kod_pocztowy, miejscowosc,
    #        ulica_lokal, naglowek, logo, bank, rachunek, numeracja, interwal,
    #        folder, wersja, folder2
    M = [
        ("company", """
            INSERT INTO company
                (id, name, name_short, nip, regon, postal_code, city, street,
                 header_text, logo, bank_name, bank_account,
                 numbering_start, increment_step,
                 report_folder, app_version, protocol_folder)
            SELECT
                id, nazwa, nazwa_krotka, nip, regon, kod_pocztowy, miejscowosc, ulica_lokal,
                naglowek, logo, bank, rachunek,
                numeracja, interwal,
                folder, wersja, folder2
            FROM firma
        """),

        # ── kategoria → categories ──
        ("categories", """
            INSERT INTO categories (id, name, code, description)
            SELECT id, nazwa, kod, opis FROM kategoria
        """),

        # ── oddzial → branches ──
        # oddzial: id, nazwa, adres, kod_pocztowy, miejscowosc, ulica_lokal, haslo
        ("branches", """
            INSERT INTO branches (id, name, address, postal_code, city, street, created_at)
            SELECT id, nazwa, adres, kod_pocztowy, miejscowosc, ulica_lokal, NOW()
            FROM oddzial
        """),

        # ── handlowiec → salespeople ──
        # handlowiec: id, nazwa, telefon, aktywny
        ("salespeople", """
            INSERT INTO salespeople (id, name, phone, is_active)
            SELECT id, nazwa, telefon, aktywny FROM handlowiec
        """),

        # ── stawka → rate_types ──
        # stawka: id, nazwa, opis, zalezna
        ("rate_types", """
            INSERT INTO rate_types (id, name, description, is_dependent)
            SELECT id, nazwa, opis, zalezna FROM stawka
        """),

        # ── kontrahent2 → contractors ──
        # kontrahent2: id, nazwa, nip, regon, pesel, kod_pocztowy, miejscowosc,
        #   ulica, lokal, uwagi, data, dostawca, email, osoba_kontaktowa, telefon,
        #   telefon2, osoba_kontaktowa2, data_gus, data_zakonczenia, nazwa_krotka,
        #   telefon_stac, www, folder, data_modyfikacji
        ("contractors", """
            INSERT INTO contractors
                (id, name, name_short, nip, regon, pesel,
                 postal_code, city, street, unit, notes, is_supplier,
                 email, contact_person1, phone1, contact_person2, phone2,
                 landline_phone, website, files_folder, gus_date,
                 created_at, updated_at)
            SELECT
                id, nazwa, nazwa_krotka, nip, regon, pesel,
                kod_pocztowy, miejscowosc, ulica, lokal, uwagi, dostawca,
                email, osoba_kontaktowa, telefon, osoba_kontaktowa2, telefon2,
                telefon_stac, www, folder, data_gus,
                COALESCE(data, NOW()), COALESCE(data_modyfikacji, NOW())
            FROM kontrahent2
        """),

        # ── adres_dostawy → contractor_addresses ──
        # adres_dostawy: id, id_umowy, nazwa, ulica, numer, kod_pocztowy,
        #   hamlet, miejscowosc, miasto, wioska, powiat, gmina, wojewodztwo, …
        # JOIN umowa2 to get id_kontrahenta → contractor_id
        ("contractor_addresses", """
            INSERT INTO contractor_addresses
                (id, contractor_id, name, country_code, postal_code, city, street,
                 notes, is_default_delivery, is_headquarters, created_at)
            SELECT
                a.id,
                u.id_kontrahenta,
                a.nazwa,
                'PL',
                a.kod_pocztowy,
                COALESCE(a.miejscowosc, a.miasto, a.hamlet, a.wioska),
                CONCAT_WS(' ', a.ulica, a.numer),
                CONCAT_WS(', ', NULLIF(a.powiat,''), NULLIF(a.gmina,''), NULLIF(a.wojewodztwo,'')),
                0, 0, NOW()
            FROM adres_dostawy a
            JOIN umowa2 u ON u.id = a.id_umowy
        """),

        # ── artykul3 → articles ──
        # artykul3: id, nazwa, usluga(varchar), nr_rejestracyjny, id_kategorii,
        #   opis, marka, model, uwagi, data_dodania, id_wlasciciel, wartosc,
        #   nr_seryjny, data_modyfikacji, liczba_dni, rodzaj, id_oddzialu
        ("articles", """
            INSERT INTO articles
                (id, name, is_service, registration_no, category_id,
                 description, brand, model, notes, created_at,
                 owner_id, replacement_value, serial_no, updated_at,
                 rental_days, article_type, branch_id)
            SELECT
                id, nazwa,
                CASE WHEN LOWER(rodzaj) = 'usługa' OR LOWER(rodzaj) = 'usluga' THEN 1 ELSE 0 END,
                nr_rejestracyjny, NULLIF(id_kategorii, 0),
                opis, marka, model, uwagi,
                COALESCE(data_dodania, NOW()),
                NULLIF(id_wlasciciel, 0), wartosc, nr_seryjny,
                COALESCE(data_modyfikacji, NOW()),
                liczba_dni, rodzaj, NULLIF(id_oddzialu, 0)
            FROM artykul3
        """),

        # ── uzytkownik → users ──
        # uzytkownik: id, login, haslo, imie, nazwisko, id_grupy, data, id_oddzialu
        # SECURITY: Generate random bcrypt passwords instead of copying plaintext
        # All users get must_change_password=1 to force password reset on first login
        # Users will need to reset password via email or admin intervention

        # ── umowa2 → contracts ──
        # umowa2: id, id_kontrahenta, numer, opis, adres, data_od, data_do,
        #   wartosc, przedplata_kwota, przedplata_dokument, uwagi,
        #   faktura_kwota, faktura_dokument, data_wprowadzenia, data_modyfikacji,
        #   email, osoba1, telefon2, telefon1, osoba2, id_firmy, oplaty,
        #   nazwa, sciezka_wydruku, data_wydruku, liczba_dni,
        #   pokaz_osobe1, pokaz_osobe2, telefon, typ, ilepoz, pz_bez,
        #   autonumer, id_handlowca
        ("contracts", """
            INSERT INTO contracts
                (id, contractor_id, salesperson_id,
                 number, auto_number, contract_type,
                 delivery_address, date_from, date_to,
                 total_value, prepayment_amount, prepayment_document,
                 invoice_amount, invoice_document,
                 notes, contact_person1, contact_phone1, show_person1,
                 contact_person2, contact_phone2, show_person2,
                 email, phone, contractor_name,
                 print_path, print_date, report_without_data,
                 hide_delivery_address, signatures_on_page1,
                 working_days_per_week, position_count,
                 created_at, updated_at)
            SELECT
                id, id_kontrahenta, NULLIF(id_handlowca, 0),
                numer, autonumer, CASE WHEN typ = 'N' THEN 'S' WHEN typ = 'U' THEN 'U' ELSE 'S' END,
                adres, data_od, data_do,
                wartosc, przedplata_kwota, przedplata_dokument,
                faktura_kwota, faktura_dokument,
                uwagi, osoba1, telefon1, COALESCE(pokaz_osobe1, 1),
                osoba2, telefon2, COALESCE(pokaz_osobe2, 1),
                email, telefon, nazwa,
                sciezka_wydruku, data_wydruku, COALESCE(pz_bez, 0),
                0, 0,
                COALESCE(liczba_dni, 6), ilepoz,
                COALESCE(data_wprowadzenia, NOW()),
                COALESCE(data_modyfikacji, NOW())
            FROM umowa2
        """),

        # ── umowa_pozycja3 → contract_positions ──
        # umowa_pozycja3: id, id_umowy, id_artykulu, typ_wynajmu, koszty, opis,
        #   liczba_dni, id_stawki, rozliczanie, oplataza, ilosc, cena,
        #   id_dostawcy, data_dostawy, nazwa
        ("contract_positions", """
            INSERT INTO contract_positions
                (id, contract_id, article_id, rental_type, costs, description,
                 rental_days, rate_type_id, billing_frequency, billing_unit,
                 quantity, unit_price, supplier_id, delivery_date, article_name)
            SELECT
                id, id_umowy, id_artykulu, typ_wynajmu, koszty, opis,
                liczba_dni, NULLIF(id_stawki, 0), rozliczanie, oplataza,
                ilosc, cena, NULLIF(id_dostawcy, 0), data_dostawy, nazwa
            FROM umowa_pozycja3
        """),

        # ── umowa_pozycja2_warunek → position_conditions ──
        # umowa_pozycja2_warunek: id, id_pozycji, id_stawki, opis,
        #   oplata1, oplata2, rozliczana, liczba_dni, minimum
        # id_pozycji references umowa_pozycja3.id (verified: 875/897 match)
        # Filter to only rows whose id_pozycji exists in contract_positions
        ("position_conditions", """
            INSERT INTO position_conditions
                (id, position_id, rate_type_id, description,
                 rate1, rate2, billing_label, period_count, minimum)
            SELECT
                w.id, w.id_pozycji, NULLIF(w.id_stawki, 0), w.opis,
                w.oplata1, w.oplata2, w.rozliczana, w.liczba_dni, w.minimum
            FROM umowa_pozycja2_warunek w
            WHERE w.id_pozycji IN (SELECT id FROM contract_positions)
        """),
    ]

    for i, (tbl, sql) in enumerate(M, 1):
        try:
            await cur.execute(sql)
            print(f"   [{i:2d}/{len(M)}] {tbl}: {cur.rowcount} rows")
        except Exception as e:
            print(f"   [{i:2d}/{len(M)}] {tbl}: ERROR — {e}")

    await cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    await conn.commit()
    await cur.close()
    conn.close()


async def step4b_migrate_users():
    """Migrate users with random bcrypt passwords (security fix)."""
    print("[4b/7] Migrating users with random bcrypt passwords …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Get all users from old table
    await cur.execute("""
        SELECT id, login, imie, nazwisko, id_grupy, id_oddzialu, data
        FROM uzytkownik
    """)
    users = await cur.fetchall()

    count = 0
    for user_id, login, first_name, last_name, id_grupy, branch_id, created_at in users:
        # Generate random temporary password
        temp_password = generate_temp_password()
        hashed_password = hash_password(temp_password)

        # Determine role
        role = 'admin' if id_grupy == 1 else 'user'

        # Insert with must_change_password=1
        await cur.execute("""
            INSERT INTO users
                (id, login, password, first_name, last_name,
                 role, is_active, must_change_password,
                 branch_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, login, hashed_password, first_name, last_name,
            role, True, True,
            branch_id if branch_id and branch_id != 0 else None,
            created_at if created_at else '2024-01-01 00:00:00'
        ))
        count += 1
        print(f"   [{count}] User {login}: temporary password generated, must_change_password=1")

    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   OK: {count} users migrated with bcrypt passwords")


async def step5_service_fee_templates():
    """Build service_fee_templates from firma.oplata_* columns (5 standard fee types)."""
    print("[5/7] Building service fee templates from firma …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Read firma fees
    await cur.execute("""
        SELECT
            czy_oplata_tankowanie, oplata_tankowanie_od, oplata_tankowanie_do, oplata_tankowanie_opis,
            czy_oplata_transport, oplata_tarnsport_od, oplata_tarnsport_do, oplata_transport_opis,
            czy_oplata_ponadnormatywny, oplata_ponadnormatywny_przestuj_od, oplata_ponadnormatywny_przestuj_do, oplata_ponadnormatywny_przestuj_opis,
            czy_oplata_czyszczenie1, oplata_czyszczenie1_od, oplata_czyszczenie1_do, oplata_czyszczenie1_opis,
            czy_oplata_czyszczenie2, oplata_czyszczenie2_od, oplata_czyszczenie2_do, oplata_czyszczenie2_opis
        FROM firma LIMIT 1
    """)
    row = await cur.fetchone()
    if row:
        fees = [
            ("Tankowanie",                  row[0], row[1], row[2], row[3]),
            ("Transport",                   row[4], row[5], row[6], row[7]),
            ("Ponadnormatywny przestój",    row[8], row[9], row[10], row[11]),
            ("Czyszczenie 1",               row[12], row[13], row[14], row[15]),
            ("Czyszczenie 2",               row[16], row[17], row[18], row[19]),
        ]
        count = 0
        for i, (name, active, amt_from, amt_to, desc) in enumerate(fees):
            await cur.execute("""
                INSERT INTO service_fee_templates
                    (company_id, contract_type, sort_order, name, amount_from, amount_to, description, is_active)
                VALUES (1, 'S', %s, %s, %s, %s, %s, 1)
            """, (i, name, amt_from, amt_to, desc))
            # Also create for U type
            await cur.execute("""
                INSERT INTO service_fee_templates
                    (company_id, contract_type, sort_order, name, amount_from, amount_to, description, is_active)
                VALUES (1, 'U', %s, %s, %s, %s, %s, 1)
            """, (i, name, amt_from, amt_to, desc))
            count += 2
        await conn.commit()
        print(f"   {count} fee templates created (5 × S + 5 × U)")
    else:
        print("   WARN: no firma row found")

    await cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# Fee-text parsing helpers (for step5b)
# ---------------------------------------------------------------------------

_A = r'([\d]+(?:\s[\d]{3})*(?:[,.][\d]+)?)'

_RE_DOSTAWA  = re.compile(rf'^{_A}\s*z[łl]\s*[-–]?\s*(.{{1,30}}?)\s*/\s*{_A}\s*z[łl]\s*[-–]?\s*(odbi[oó]r\S*)', re.I | re.U)
_RE_H_RANGE  = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)\s*[-–]\s*{_A}\s*z[łl]\s*/\s*\S+')
_RE_PER_UNIT = re.compile(rf'^{_A}\s*z[łl]\s*/\s*(\S+)')
_RE_RANGE    = re.compile(rf'^{_A}\s*z[łl]\s*[-–]\s*{_A}\s*z[łl]')
_RE_PARENS   = re.compile(rf'^{_A}\s*z[łl]\s*\(([^)]+)\)')
_RE_SINGLE   = re.compile(rf'^{_A}\s*z[łl](.*)')
_RE_NOCOL    = re.compile(rf'^(.+?)\s+{_A}\s*z[łl]\s*/\s*(\S+)\s*$')
_RE_SKIP     = re.compile(
    r'^(-zedytowane|1[-\s]*2\s*dni|powyżej\s*2|praca do \d|czas trwania|'
    r'opłata w gotówce|do \d+ godzin\s*-)',
    re.I,
)


def _to_dec(s: str) -> Decimal | None:
    if not s:
        return None
    try:
        return Decimal(s.strip().replace(' ', '').replace(',', '.'))
    except InvalidOperation:
        return None


def _parse_fee_line(raw: str) -> dict | None:
    raw_s = raw.strip()
    if not raw_s or _RE_SKIP.match(raw_s):
        return None
    line = raw_s.lstrip('- ').strip()
    if not line:
        return None

    out = dict(name=line[:200], amount_from=None, amount_to=None,
               unit=None, description=None, is_active=True)

    if ':' in line:
        idx = line.index(':')
        name_part = line[:idx].strip()
        value     = line[idx + 1:].strip()
        if not name_part:
            return None
        out['name'] = name_part[:200]
    else:
        m = _RE_NOCOL.match(line)
        if m:
            out['name']        = m.group(1).strip()[:200]
            out['amount_from'] = _to_dec(m.group(2))
            out['unit']        = m.group(3)
        return out

    if not value:
        return out

    m = _RE_DOSTAWA.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['description'] = f"{m.group(2).strip()} / {m.group(4).strip()}"
        return out

    m = _RE_H_RANGE.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['amount_to']   = _to_dec(m.group(3))
        out['unit']        = m.group(2)
        return out

    m = _RE_PER_UNIT.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['unit']        = m.group(2)
        return out

    m = _RE_RANGE.match(value)
    if m and _to_dec(m.group(2)) is not None:
        out['amount_from'] = _to_dec(m.group(1))
        out['amount_to']   = _to_dec(m.group(2))
        return out

    m = _RE_PARENS.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        out['description'] = m.group(2).strip()
        return out

    m = _RE_SINGLE.match(value)
    if m:
        out['amount_from'] = _to_dec(m.group(1))
        trailing = m.group(2).strip().strip('-– ').strip()
        if trailing:
            out['description'] = trailing[:400]
        return out

    out['description'] = value[:400]
    return out


def _parse_text_to_fees(text: str) -> list[dict]:
    result = []
    if not text:
        return result
    sort_order = 0
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').splitlines():
        fee = _parse_fee_line(raw)
        if fee:
            fee['sort_order'] = sort_order
            sort_order += 1
            result.append(fee)
    return result


async def step5d_link_articles_to_templates():
    """RAO-P1-011: Mapowanie service_fee_templates.name → articles.id (FK).

    Strategia:
      1. Dla każdego service_fee_templates z article_id IS NULL, znajdź artykuł
         po nazwie (case-insensitive, dopasowanie zaczynane od name).
      2. Preferuj artykuły z is_service=1 (usługi).
      3. Jeśli artykuł nie istnieje — utwórz go (is_service=1).
      4. Wypełnij default_price = COALESCE(amount_from, amount_to).

    Idempotentne: pomija rekordy z już ustawionym article_id.
    """
    print("[5d] Linking service_fee_templates.name → articles (RAO-P1-011) …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    await cur.execute("""
        SELECT id, name, amount_from, amount_to
        FROM service_fee_templates
        WHERE article_id IS NULL
    """)
    rows = await cur.fetchall()

    linked = 0
    created = 0
    for tpl_id, name, amt_from, amt_to in rows:
        if not name:
            continue
        # Match by exact name (case-insensitive) — preferuj is_service=1
        await cur.execute(
            "SELECT id FROM articles WHERE LOWER(name) = LOWER(%s) "
            "ORDER BY is_service DESC, id ASC LIMIT 1",
            (name,)
        )
        art = await cur.fetchone()
        article_id = art[0] if art else None

        if article_id is None:
            # Spróbuj LIKE (prefix)
            await cur.execute(
                "SELECT id FROM articles WHERE LOWER(name) LIKE LOWER(%s) "
                "ORDER BY is_service DESC, id ASC LIMIT 1",
                (name[:30] + "%",)
            )
            art = await cur.fetchone()
            article_id = art[0] if art else None

        if article_id is None:
            # Utwórz nowy artykuł-usługę
            await cur.execute(
                "INSERT INTO articles (name, is_service, article_type, created_at) "
                "VALUES (%s, 1, 'usluga_dodatkowa', NOW())",
                (name[:200],)
            )
            article_id = cur.lastrowid
            created += 1

        default_price = amt_from if amt_from is not None else amt_to
        await cur.execute(
            "UPDATE service_fee_templates SET article_id = %s, default_price = %s WHERE id = %s",
            (article_id, default_price, tpl_id)
        )
        linked += 1

    await conn.commit()

    # Verification
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates WHERE article_id IS NOT NULL")
    with_fk = (await cur.fetchone())[0]
    pct = (with_fk * 100 // total) if total else 0
    print(f"   linked={linked}, articles_created={created}, FK coverage: {with_fk}/{total} ({pct}%)")

    await cur.close()
    conn.close()


async def step5c_create_preset_groups():
    """Create default fee preset groups and link service_fee_templates to them."""
    print("[5c] Creating fee preset groups and linking templates …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    for sort_order, (ct, label) in enumerate((("S", "Domyślny — najem"), ("U", "Domyślny — usługa"))):
        await cur.execute("""
            INSERT INTO fee_preset_groups (company_id, name, contract_type, is_default, sort_order)
            VALUES (1, %s, %s, 1, %s)
        """, (label, ct, sort_order))
        preset_id = cur.lastrowid
        await cur.execute("""
            UPDATE service_fee_templates
            SET preset_id = %s, is_active = 1
            WHERE contract_type = %s AND preset_id IS NULL
        """, (preset_id, ct))
        print(f"   preset_id={preset_id} ({label}): {cur.rowcount} templates linked")

    await conn.commit()
    await cur.close()
    conn.close()


async def step5b_contract_service_fees():
    """Parse umowa2.OPLATY free-text → contract_service_fees rows."""
    print("[5b] Migrating umowa2.OPLATY → contract_service_fees …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur  = await conn.cursor()

    await cur.execute(
        "SELECT id, OPLATY FROM umowa2 WHERE OPLATY IS NOT NULL AND TRIM(OPLATY) != ''"
    )
    rows = await cur.fetchall()

    inserted = 0
    skipped  = 0
    for contract_id, oplaty in rows:
        fees = _parse_text_to_fees(oplaty)
        for fee in fees:
            await cur.execute(
                """INSERT INTO contract_service_fees
                   (contract_id, sort_order, name,
                    amount_from, amount_to, unit, description, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (contract_id, fee['sort_order'], fee['name'],
                 fee['amount_from'], fee['amount_to'],
                 fee['unit'], fee['description'], fee['is_active'])
            )
            inserted += 1
        if not fees:
            skipped += 1

    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   {inserted} service fee rows from {len(rows)} contracts ({skipped} unparseable skipped)")


async def step6_drop_old():
    print("[6/7] DROP old tables + views …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()
    await cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    dropped = 0
    for obj in OLD_OBJECTS:
        for kind, ttype in (("VIEW", "VIEW"), ("TABLE", "BASE TABLE")):
            try:
                await cur.execute(
                    "SELECT COUNT(*) FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND TABLE_TYPE=%s",
                    (DB_NAME, obj, ttype),
                )
                (exists,) = await cur.fetchone()
                if exists:
                    await cur.execute(f"DROP {kind} `{obj}`")
                    dropped += 1
            except Exception:
                pass
    await cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   dropped {dropped} objects")


# ===========================================================================
# RAO-P1-017 — CSV → hierarchiczne kategorie → artykuły
# ===========================================================================

# Column indices w pliku CSV (0-based, po przecinku)
_C_ID       = 0   # legacy id (int)
_C_NUMER    = 7   # Numer wewnętrzny
_C_CAT_MAIN = 8   # Właściwa kategoria główna
_C_CAT_1    = 9   # Kategoria I
_C_CAT_2    = 10  # Kategoria II
_C_CAT_3    = 11  # Kategoria III
_C_ZASIEG   = 12  # Zasięg
_C_UDZWIG   = 13  # Udźwig (t)
_C_DODATKI  = 14  # Dodatki

# Wartości garbage → category = NULL (DoD: x, Test, -, empty → is_archival=TRUE)
_GARBAGE_NORM: frozenset = frozenset({
    "", "x", "-", "\u2013", "\u2014", "test", "ogolna",
    "?", "brak", "inne", ".",
})
_TECH_GARBAGE: frozenset = frozenset({"", "-", "\u2013", "\u2014"})


def normalize_category(name: str) -> str:
    """
    Normalizacja do porównania (NIE do przechowywania w DB).
    NFD + usunięcie Mn (combining diacritics) + ł→l / Ł→L.
    CSV-INJ-001 safe: brak f-stringów z user input.
    """
    if not name:
        return ""
    nfd = unicodedata.normalize("NFD", name.strip())
    no_dia = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    no_dia = no_dia.replace("\u0142", "l").replace("\u0141", "L")
    return re.sub(r"\s+", " ", no_dia.lower()).strip()


def _is_garbage_cat(val: str) -> bool:
    return normalize_category(val) in _GARBAGE_NORM


def _clean_cat(val: object) -> "str | None":
    if not val:
        return None
    s = str(val).strip()
    return None if _is_garbage_cat(s) else s


def _clean_tech(val: object) -> "str | None":
    if not val:
        return None
    s = str(val).strip()
    return None if (not s or s in _TECH_GARBAGE) else s


def _parse_csv_file(csv_path: str) -> list:
    """CSV-INJ-001 SAFE: csv.reader (NIE eval, NIE f-string z user input)."""
    records = []
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header
        for row in reader:
            while len(row) < 15:
                row.append("")
            id_str = row[_C_ID].strip()
            if not id_str.isdigit():
                continue
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

    1. GET_LOCK(rao_migrate_csv, 0) — race condition guard (session-scoped)
    2. Parsowanie CSV (csv.reader — CSV-INJ-001 safe)
    3. Cache istniejących kategorii w pamięci (Python-side diacritic norm)
    4. Budowanie drzewa (main→sub1→sub2→sub3, sorted dla determinizmu):
       _upsert_cat(): SELECT-or-INSERT — idempotent
    5. UPDATE articles (parametryzowane %s — SQL-INJ-001 safe):
       category_main/sub1/sub2/sub3, category_id (najgłębszy poziom),
       technical_attributes (JSON), internal_number (COALESCE),
       is_archival=TRUE (legacy marker)
    6. Oznacz WSZYSTKIE pozostałe artykuły is_archival=TRUE
    7. Weryfikacja: COUNT + orphan check (gate per migrations.md)
    8. RELEASE_LOCK

    Idempotentność (2nd run = 0 zmian):
      - Kategorie: cache hit → brak INSERT
      - Articles: te same wartości → MySQL pomija wiersz
    Security: SQL-INJ-001 (%s); CSV-INJ-001 (csv.reader).
    """
    print("[8] RAO-P1-017: CSV categories → articles ...")
    script_dir   = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    csv_dir      = os.path.join(project_root, "spec", "backlog", "archiwum", "refinement")
    csv_matches  = glob.glob(os.path.join(csv_dir, "Asortyment*.csv"))
    if not csv_matches:
        print(f"   WARN: CSV nie znaleziony w {csv_dir!r} — step8 pominięto")
        return
    csv_path = csv_matches[0]
    print(f"   CSV: {os.path.basename(csv_path)}")

    conn = await aiomysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASS, db=DB_NAME,
    )
    cur = await conn.cursor()

    # GET_LOCK — guard przed race condition (session-scoped, auto-release on disconnect)
    await cur.execute("SELECT GET_LOCK(%s, 0)", ("rao_migrate_csv",))
    (lock_acquired,) = await cur.fetchone()
    if lock_acquired != 1:
        print("   WARN: GET_LOCK failed — step8 pominięto")
        await cur.close()
        conn.close()
        return

    try:
        records   = _parse_csv_file(csv_path)
        csv_total = len(records)
        print(f"   {csv_total} rekordów z CSV")

        # ── Cache kategorii z DB (Python-side normalizacja) ──────────────────
        await cur.execute("SELECT id, name, level, parent_id FROM categories")
        cat_cache: dict = {
            (normalize_category(n or ""), lvl, pid): cid
            for cid, n, lvl, pid in await cur.fetchall()
        }
        print(f"   {len(cat_cache)} kategorii w DB (przed step8)")
        cats_created = 0

        # ── Idempotent INSERT kategorii ──────────────────────────────────────
        async def _upsert_cat(canonical: str, level: str, parent_id: object) -> int:
            nonlocal cats_created
            norm = normalize_category(canonical)
            key  = (norm, level, parent_id)
            if key in cat_cache:
                return cat_cache[key]
            # SQL-INJ-001 SAFE: %s parametryzowane
            await cur.execute(
                "INSERT INTO categories (name, level, parent_id) VALUES (%s, %s, %s)",
                (canonical.strip(), level, parent_id),
            )
            new_id = cur.lastrowid
            cat_cache[key] = new_id
            cats_created += 1
            return new_id

        # ── Zbierz kanon nazw (pierwsza wystąpienie wygrywa) ─────────────────
        main_canon: dict = {}
        sub1_canon: dict = {}
        sub2_canon: dict = {}
        sub3_canon: dict = {}
        for rec in records:
            cm = rec["cat_main"]
            if cm is None:
                continue
            nm = normalize_category(cm)
            main_canon.setdefault(nm, cm)
            cs1 = rec["cat_sub1"]
            if cs1 is None:
                continue
            ns1 = normalize_category(cs1)
            sub1_canon.setdefault((nm, ns1), cs1)
            cs2 = rec["cat_sub2"]
            if cs2 is None:
                continue
            ns2 = normalize_category(cs2)
            sub2_canon.setdefault((nm, ns1, ns2), cs2)
            cs3 = rec["cat_sub3"]
            if cs3 is None:
                continue
            ns3 = normalize_category(cs3)
            sub3_canon.setdefault((nm, ns1, ns2, ns3), cs3)

        # ── Buduj drzewo (sorted → determinizm dla idempotentności) ──────────
        main_id: dict = {}
        sub1_id: dict = {}
        sub2_id: dict = {}
        sub3_id: dict = {}
        for nm in sorted(main_canon):
            main_id[nm] = await _upsert_cat(main_canon[nm], "main", None)
        for (nm, ns1) in sorted(sub1_canon):
            if nm in main_id:
                sub1_id[(nm, ns1)] = await _upsert_cat(
                    sub1_canon[(nm, ns1)], "sub1", main_id[nm])
        for (nm, ns1, ns2) in sorted(sub2_canon):
            if (nm, ns1) in sub1_id:
                sub2_id[(nm, ns1, ns2)] = await _upsert_cat(
                    sub2_canon[(nm, ns1, ns2)], "sub2", sub1_id[(nm, ns1)])
        for (nm, ns1, ns2, ns3) in sorted(sub3_canon):
            if (nm, ns1, ns2) in sub2_id:
                sub3_id[(nm, ns1, ns2, ns3)] = await _upsert_cat(
                    sub3_canon[(nm, ns1, ns2, ns3)], "sub3", sub2_id[(nm, ns1, ns2)])
        print(f"   Nowe kategorie: {cats_created}")

        # ── UPDATE articles ───────────────────────────────────────────────────
        n_matched   = 0
        n_unmatched = 0
        # SQL-INJ-001 SAFE: tylko %s placeholders, zero f-stringów z user data
        _UPDATE_SQL = (
            "UPDATE articles SET"
            "  is_archival          = TRUE,"
            "  category_main        = %s,"
            "  category_sub1        = %s,"
            "  category_sub2        = %s,"
            "  category_sub3        = %s,"
            "  category_id          = %s,"
            "  technical_attributes = %s,"
            "  internal_number      = COALESCE(NULLIF(internal_number, ''), %s)"
            " WHERE id = %s"
        )
        for rec in records:
            art_id   = rec["id"]
            cat_main = rec["cat_main"]
            cat_sub1 = rec["cat_sub1"]
            cat_sub2 = rec["cat_sub2"]
            cat_sub3 = rec["cat_sub3"]

            # Rozwiąż głębszy poziom → category_id
            cat_id = None
            if cat_main is not None:
                nm  = normalize_category(cat_main)
                ns1 = normalize_category(cat_sub1) if cat_sub1 else None
                ns2 = normalize_category(cat_sub2) if cat_sub2 else None
                ns3 = normalize_category(cat_sub3) if cat_sub3 else None
                if ns1 and ns2 and ns3:
                    cat_id = sub3_id.get((nm, ns1, ns2, ns3))
                if cat_id is None and ns1 and ns2:
                    cat_id = sub2_id.get((nm, ns1, ns2))
                if cat_id is None and ns1:
                    cat_id = sub1_id.get((nm, ns1))
                if cat_id is None:
                    cat_id = main_id.get(nm)

            # technical_attributes (JSON) — tylko niepuste pola
            tech: dict = {}
            if rec["zasieg"]:
                tech["zasieg"] = rec["zasieg"]
            if rec["udzwig"]:
                tech["udzwig"] = rec["udzwig"]
            if rec["dodatki"]:
                tech["dodatki"] = rec["dodatki"]
            tech_json = json.dumps(tech, ensure_ascii=False) if tech else None

            if cat_main is not None:
                n_matched += 1
            else:
                n_unmatched += 1

            await cur.execute(
                _UPDATE_SQL,
                (cat_main, cat_sub1, cat_sub2, cat_sub3, cat_id, tech_json,
                 rec["internal_number"], art_id),
            )

        # ── Oznacz WSZYSTKIE pozostałe artykuły is_archival=TRUE ─────────────
        await cur.execute(
            "UPDATE articles SET is_archival = TRUE WHERE is_archival = FALSE"
        )
        extra = cur.rowcount
        if extra:
            print(f"   {extra} artykułów spoza CSV → is_archival=TRUE")

        await conn.commit()

        # ── Weryfikacja ───────────────────────────────────────────────────────
        await cur.execute("SELECT COUNT(*) FROM articles")
        total_arts = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM articles WHERE is_archival = TRUE")
        archival_ct = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM articles WHERE category_main IS NOT NULL")
        with_cat_main = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM articles WHERE category_id IS NOT NULL")
        with_cat_id = (await cur.fetchone())[0]
        await cur.execute(
            "SELECT COUNT(*) FROM articles"
            " WHERE category_sub1 IS NOT NULL AND category_main IS NULL"
        )
        orphan_subs = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM categories")
        total_cats = (await cur.fetchone())[0]

        pct_match   = round(n_matched   * 100 / csv_total, 1) if csv_total else 0.0
        pct_nomatch = round(n_unmatched * 100 / csv_total, 1) if csv_total else 0.0

        print(f"\n   --- RAO-P1-017 summary ---")
        print(f"   Kategorie w DB:           {total_cats}  (+{cats_created} nowych)")
        print(f"   CSV rekordy:              {csv_total}")
        print(f"     z kategorią:            {n_matched} ({pct_match}%)")
        print(f"     bez kategorii/śmieci:   {n_unmatched} ({pct_nomatch}%)")
        print(f"   is_archival=TRUE:         {archival_ct}/{total_arts}")
        print(f"   category_main ustawiony:  {with_cat_main}/{total_arts}")
        print(f"   category_id ustawiony:    {with_cat_id}/{total_arts}")
        if orphan_subs:
            print(f"   WARN: {orphan_subs} orphan sub-kategorii!")
        else:
            print(f"   OK: brak orphan sub-kategorii")

    finally:
        await cur.execute("SELECT RELEASE_LOCK(%s)", ("rao_migrate_csv",))
        await cur.fetchone()
        await cur.close()
        conn.close()


async def verify():
    """Quick row-count verification + RAO-P1-017 gates."""
    print("\n── Verification ──")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()
    for tbl in ["company","categories","branches","salespeople","rate_types",
                "contractors","contractor_addresses","articles","users",
                "contracts","contract_positions","position_conditions",
                "fee_preset_groups","service_fee_templates","contract_service_fees",
                "service_hours"]:
        await cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
        cnt = (await cur.fetchone())[0]
        print(f"   {tbl}: {cnt}")

    # ── RAO-P1-017 quality gates ───────────────────────────────────────────
    print("\n   [P1-017 gates]")
    await cur.execute("SELECT COUNT(*) FROM articles")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM articles WHERE is_archival = TRUE")
    archival = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM articles WHERE category_main IS NOT NULL")
    with_main = (await cur.fetchone())[0]
    await cur.execute(
        "SELECT COUNT(*) FROM articles"
        " WHERE category_sub1 IS NOT NULL AND category_main IS NULL"
    )
    orphan = (await cur.fetchone())[0]
    print(f"   articles total:          {total}")
    print(f"   is_archival=TRUE:        {archival}/{total}")
    print(f"   category_main set:       {with_main}/{total}")
    if orphan:
        print(f"   GATE FAIL: orphan sub-cats = {orphan}")
    else:
        print("   GATE OK:  no orphan sub-categories")

    await cur.close()
    conn.close()


async def step9_postal_codes_migration():
    """RAO-P1-008: Extract postal_code + city from delivery_address, seed postal_codes table."""
    import re

    print("[9/9] RAO-P1-008: Strukturalizacja adresów (postal_code + city) ...")

    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # 9.1 Seed postal_codes table from CSV
    csv_path = os.path.join(project_root, "backend", "data", "postal_codes.csv")
    if os.path.exists(csv_path):
        print(f"   Seeding postal_codes from {csv_path}...")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            inserted = 0
            for row in reader:
                if len(row) >= 3:  # code, city, voivodeship
                    code, city, voivodeship = row[0].strip(), row[1].strip(), row[2].strip() if len(row) > 2 else None
                    if code and city:
                        await cur.execute(
                            "INSERT IGNORE INTO postal_codes (code, city, voivodeship) VALUES (%s, %s, %s)",
                            (code, city, voivodeship)
                        )
                        inserted += 1
            await conn.commit()
            print(f"   Seeded {inserted} postal codes")
    else:
        print(f"   WARN: postal_codes.csv not found at {csv_path} - skipping seed")

    # 9.2 Extract postal_code + city from delivery_address (idempotent)
    print("   Extracting postal_code + city from delivery_address...")
    await cur.execute("""
        SELECT id, delivery_address
        FROM contracts
        WHERE delivery_address IS NOT NULL
        AND postal_code IS NULL
    """)
    rows = await cur.fetchall()

    # Enhanced regex patterns for postal codes
    # Formats: XX-XXX, XX XXX, XXXXXX, XX-XX-XXX (errors), also handle missing spaces
    postal_patterns = [
        re.compile(r"(\d{2}-\d{3})"),     # Standard: XX-XXX (without word boundary)
        re.compile(r"(\d{2}\s\d{3})"),     # Space: XX XXX
        re.compile(r"(\d{6})"),            # No separator: XXXXXX
        re.compile(r"(\d{2}-\d{2}-\d{3})"), # Error: XX-XX-XXX
    ]

    # Top 200 Polish cities for extraction (expanded coverage)
    polish_cities = [
        "Warszawa", "Kraków", "Łódź", "Wrocław", "Poznań", "Gdańsk", "Szczecin", "Bydgoszcz", "Lublin",
        "Białystok", "Katowice", "Gdynia", "Częstochowa", "Radom", "Sosnowiec", "Toruń", "Kielce", "Rzeszów",
        "Gliwice", "Zabrze", "Olsztyn", "Bielsko-Biała", "Bytom", "Zielona Góra", "Rybnik", "Ruda Śląska",
        "Opole", "Tychy", "Gorzów Wielkopolski", "Dąbrowa Górnicza", "Elbląg", "Płock", "Wałbrzych", "Włocławek",
        "Tarnów", "Chorzów", "Koszalin", "Kalisz", "Legnica", "Jaworzno", "Jastrzębie-Zdrój", "Jelenia Góra",
        "Słupsk", "Malbork", "Grudziądz", "Piła", "Inowrocław", "Lubin", "Ostrów Wielkopolski", "Gniezno",
        "Ostrołęka", "Suwałki", "Głogów", "Stargard", "Pabianice", "Chełm", "Zamość", "Puławy", "Ełk",
        "Pruszcz Gdański", "Włocławek", "Tomaszów Mazowiecki", "Mysłowice", "Piaseczno", "Żory", "Otwock",
        "Radomsko", "Kędzierzyn-Koźle", "Tczew", "Piotrków Trybunalski", "Mielec", "Wałbrzych", "Oława",
        "Siedlce", "Pruszków", "Mysłowice", "Ostrołęka", "Jaworzno", "Jastrzębie-Zdrój", "Jelenia Góra",
        "Słupsk", "Malbork", "Grudziądz", "Piła", "Inowrocław", "Lubin", "Ostrów Wielkopolski", "Gniezno",
        # Additional cities from Mazovia and surrounding regions
        "Grodzisk Mazowiecki", "Marki", "Piastów", "Pruszków", "Radzymin", "Sochaczew", "Sulejówek",
        "Warszawa", "Wołomin", "Ząbki", "Żyrardów", "Łomianki", "Michałowice", "Nadarzyn", "Stare Babice",
        "Nowy Dwór Mazowiecki", "Otwock", "Piaseczno", "Praga-Południe", "Ursus", "Wesoła", "Bemowo",
        "Białołęka", "Mokotów", "Ochota", "Praga-Północ", "Rembertów", "Śródmieście", "Targówek",
        "Ursynów", "Wawer", "Wilanów", "Włochy", "Wola", "Żoliborz",
        # Other major cities
        "Będzin", "Biała Podlaska", "Bielawa", "Bieruń", "Blachownia", "Bochnia", "Boguszów-Gorce",
        "Bolesławiec", "Brzeg", "Braniewo", "Brodnica", "Brzeg Dolny", "Bychawa", "Bystrzyca Kłodzka",
        "Ciechanów", "Ciechocinek", "Cieszyn", "Czerwionka-Leszczyny", "Czarna Woda", "Czechowice-Dziedzice",
        "Czeladź", "Czerwionka", "Człuchów", "Darłowo", "Dąbrowa Górnicza", "Dębica", "Dębogórz",
        "Dzierżoniów", "Działdowo", "Elbląg", "Ełk", "Gdańsk", "Gdynia", "Giżycko", "Głogów",
        "Głogów Małopolski", "Gniezno", "Goleniów", "Gorlice", "Gorzów Wielkopolski", "Gostynin", "Gostyń",
        "Grajewo", "Grodzisk Mazowiecki", "Grudziądz", "Grybów", "Gryfino", "Ilawa", "Iława",
        "Inowrocław", "Iłża", "Jabłonowo Pomorskie", "Jarocin", "Jarosław", "Jasło", "Jastarnia",
        "Jastrzębie-Zdrój", "Jawor", "Jaworzno", "Jaworzno Śląskie", "Jedlina-Zdrój", "Jelenia Góra",
        "Jędrzejów", "Józefów", "Kalisz", "Kalwaria Zebrzydowska", "Kamienna Góra", "Kamień Pomorski",
        "Kamień Pomorski", "Kalety", "Kalisz", "Kalisz Pomorski", "Kalwaria Zebrzydowska", "Karczew",
        "Kargowa", "Karpacz", "Kartuzy", "Katowice", "Kazimierz Dolny", "Kcynia", "Kędzierzyn-Koźle",
        "Kępice", "Kępnice", "Kętrzyn", "Kęty", "Kielce", "Kietrz", "Kluczbork", "Kłodzko",
        "Kłobuck", "Kłodzko", "Knurow", "Kobylin", "Kock", "Kolbuszowa", "Kole", "Kołobrzeg",
        "Koło", "Kolonowskie", "Kołaczyce", "Koluszki", "Konin", "Konskowola", "Końskie",
        "Koprzywnica", "Korfantów", "Kornik", "Korzecko", "Koszalin", "Koszwały", "Kowal",
        "Kowalewo Pomorskie", "Kowary", "Koziegłowy", "Kozienice", "Krapkowice", "Krajenka",
        "Krasnystaw", "Krasnobród", "Krasnik", "Kraśnik", "Kraków", "Krapkowice", "Krzepice",
        "Krzyczki", "Krynica Morska", "Krynica-Zdrój", "Krzynowłoga", "Książ Wielki", "Kudowa-Zdrój",
        "Kutno", "Kuźnica", "Kwidzyn", "Kęty", "Kętrzyn"
    ]

    updated = 0

    for contract_id, address in rows:
        if not address:
            continue

        # Extract postal code (try multiple patterns)
        postal_code = None
        for pattern in postal_patterns:
            match = pattern.search(address)
            if match:
                postal_code = match.group(1)
                # Normalize to XX-XXX format
                if len(postal_code) == 6 and '-' not in postal_code:
                    postal_code = f"{postal_code[:2]}-{postal_code[2:]}"
                elif ' ' in postal_code:
                    postal_code = postal_code.replace(' ', '-')
                elif len(postal_code) == 9 and postal_code.count('-') == 2:
                    # Fix XX-XX-XXX → XX-XXX
                    parts = postal_code.split('-')
                    postal_code = f"{parts[0]}-{parts[2]}"
                break

        # Lookup city from postal_codes
        city = None
        if postal_code:
            await cur.execute(
                "SELECT city FROM postal_codes WHERE code = %s LIMIT 1",
                (postal_code,)
            )
            city_row = await cur.fetchone()
            if city_row:
                city = city_row[0]

        # If no city from postal_codes, try to extract from address
        if not city:
            address_lower = address.lower()
            for polish_city in polish_cities:
                if polish_city.lower() in address_lower:
                    city = polish_city
                    break

        # Normalize city (trim, title case)
        if city:
            city = city.strip().title()

        # Update if found postal_code or city
        if postal_code or city:
            await cur.execute(
                "UPDATE contracts SET postal_code = %s, city = %s WHERE id = %s",
                (postal_code, city, contract_id)
            )
            updated += 1
    
    await conn.commit()
    
    # 9.3 Report
    await cur.execute("SELECT COUNT(*) FROM contracts WHERE postal_code IS NOT NULL")
    with_code = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM contracts WHERE delivery_address IS NOT NULL")
    with_address = (await cur.fetchone())[0]
    
    print(f"   Updated {updated}/{len(rows)} contracts with postal_code")
    print(f"   Coverage: {with_code}/{with_address} ({with_code*100//with_address if with_address else 0}%)")
    print("   OK")

    await cur.close()
    conn.close()


async def main():
    print("=" * 60)
    print("RAO Migration  —  deterministic dump → rao_new")
    print("=" * 60)
    print("DEBUG: Starting migration...")
    try:
        await step1_recreate_db()
        step2_import_dump()
        await step3_create_schema()
        await step4_migrate_data()
        await step4b_migrate_users()  # SECURITY: random bcrypt passwords
        await step5_service_fee_templates()
        await step5c_create_preset_groups()
        await step5d_link_articles_to_templates()  # RAO-P1-011
        await step5b_contract_service_fees()
        await step6_drop_old()
        # step7_rehash removed - passwords already hashed in step4b
        await step8_csv_categories()   # RAO-P1-017
        await step9_postal_codes_migration()  # RAO-P1-008
        await verify()
        print("\n✓ Migration complete!")
        print("⚠ All users have must_change_password=1 and random bcrypt passwords")
        print("⚠ Users must reset passwords via email or admin intervention")
    except Exception as e:
        print(f"\n✗ FATAL: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"ERROR in asyncio.run: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
