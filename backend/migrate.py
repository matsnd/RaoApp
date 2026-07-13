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
DUMP_PATH = os.path.join(project_root, "temp", "toolsmart_roa_1781033626.sql")
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
import pymysql  # RAO-P2-062: IntegrityError catch dla orphaned OPLATY
from sqlalchemy.ext.asyncio import create_async_engine

from database import Base
import auth.models         # noqa
import contractors.models  # noqa
import machines.models     # noqa
import services.models     # noqa
import additional_services.models  # noqa
import contracts.models    # noqa
import settings.models     # noqa
import categories.models   # noqa
import integrations.models # noqa
import settlements.models  # noqa  # RAO-P1-012: contract_settlements
import audit.models        # noqa  # RAO-P3-005: audit_log
import contract_costs.models  # noqa  # RAO-P3-005: contract_costs
import deliveries.models  # noqa  # RAO-P3-005: deliveries
import reservations.models  # noqa  # RAO-P3-005: reservations
import integrations.fakturownia.models  # noqa  # RAO-P2-012: fakturownia
import archive.models  # noqa  # RAO-P2-062: archive_* tabele (create_all)


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
DB_NAME = "rao_new"
# DUMP_PATH is now defined above as absolute path


def _load_db_password() -> str:
    """P0 security: load DB password from env or .env, never hardcode."""
    for env_var in ("DB_PASSWORD", "RAO_DB_PASSWORD"):
        pw = os.environ.get(env_var)
        if pw:
            return pw
    # Fallback to .env file in project root (manual parse, no extra dependency)
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                key, _, value = line.partition("=")
                if key.strip() == "RAO_DB_PASSWORD":
                    return value.strip().strip('"').strip("'")
    raise RuntimeError(
        "DB password not found. Set DB_PASSWORD or RAO_DB_PASSWORD env var, "
        "or RAO_DB_PASSWORD in .env"
    )


DB_PASS = _load_db_password()

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

    # Diagnostic: show rodzaj distribution to verify machine/service/additional_service split
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
                 header_text, bank_name, bank_account,
                 numbering_start, increment_step)
            SELECT
                id, nazwa, nazwa_krotka, nip, regon, kod_pocztowy, miejscowosc, ulica_lokal,
                naglowek, bank, rachunek,
                numeracja, interwal
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

        # ── artykul3 → machines / services / additional_services ──
        # artykul3: id, nazwa, usluga(varchar), nr_rejestracyjny, id_kategorii,
        #   opis, marka, model, uwagi, data_dodania, id_wlasciciel, wartosc,
        #   nr_seryjny, data_modyfikacji, liczba_dni, rodzaj, id_oddzialu
        # Split po kolumnie rodzaj (col[3]):
        #   "Usługa" → services
        #   "artykuł" / puste → machines
        #   inne → additional_services
        ("machines", """
            INSERT INTO machines
                (id, name, registration_no, category_id,
                 description, brand, model, notes, created_at,
                 owner_id, replacement_value, serial_no, updated_at,
                 rental_days, branch_id)
            SELECT
                id, nazwa,
                nr_rejestracyjny, NULLIF(id_kategorii, 0),
                opis, marka, model, uwagi,
                COALESCE(data_dodania, NOW()),
                NULLIF(id_wlasciciel, 0), wartosc, nr_seryjny,
                COALESCE(data_modyfikacji, NOW()),
                liczba_dni, NULLIF(id_oddzialu, 0)
            FROM artykul3
            WHERE LOWER(rodzaj) IN ('artykuł', 'artykul', '')
               OR rodzaj IS NULL
        """),
        ("services", """
            INSERT INTO services
                (id, name, description, notes, replacement_value,
                 created_at, updated_at)
            SELECT
                id, nazwa, opis, uwagi, wartosc,
                COALESCE(data_dodania, NOW()),
                COALESCE(data_modyfikacji, NOW())
            FROM artykul3
            WHERE LOWER(rodzaj) IN ('usługa', 'usluga')
        """),
        ("additional_services", """
            INSERT INTO additional_services
                (id, name, description, notes, default_amount,
                 created_at, updated_at)
            SELECT
                id, nazwa, opis, uwagi, wartosc,
                COALESCE(data_dodania, NOW()),
                COALESCE(data_modyfikacji, NOW())
            FROM artykul3
            WHERE LOWER(rodzaj) NOT IN ('usługa', 'usluga', 'artykuł', 'artykul', '')
              AND rodzaj IS NOT NULL
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
            INSERT IGNORE INTO contracts
                (id, contractor_id, salesperson_id,
                 number, auto_number, contract_type,
                 delivery_address, date_from, date_to,
                 prepayment_amount, prepayment_document,
                 notes, contact_person1, contact_phone1, show_person1,
                 contact_person2, contact_phone2, show_person2,
                 email, phone, contractor_name,
                 print_path, print_date, report_without_data,
                 hide_delivery_address, signatures_on_page1,
                 working_days_per_week, position_count, is_settled, settled_at,
                 created_at, updated_at)
            SELECT
                id, id_kontrahenta, NULLIF(id_handlowca, 0),
                numer, autonumer, CASE WHEN typ = 'N' THEN 'S' WHEN typ = 'U' THEN 'U' ELSE 'S' END,
                adres, data_od, data_do,
                przedplata_kwota, przedplata_dokument,
                uwagi, osoba1, telefon1, COALESCE(pokaz_osobe1, 1),
                osoba2, telefon2, COALESCE(pokaz_osobe2, 1),
                email, telefon, nazwa,
                sciezka_wydruku, data_wydruku, COALESCE(pz_bez, 0),
                0, 0,
                COALESCE(liczba_dni, 6), ilepoz, 1, data_do,
                COALESCE(data_wprowadzenia, NOW()),
                COALESCE(data_modyfikacji, NOW())
            FROM umowa2
        """),

        # ── umowa_pozycja3 → contract_positions ──
        # umowa_pozycja3: id, id_umowy, id_artykulu, typ_wynajmu, opis,
        #   liczba_dni, id_stawki, rozliczanie, oplataza, ilosc, cena,
        #   id_dostawcy, data_dostawy, nazwa
        # article_id → machine_id (maszyny) lub service_id (usługi) zależnie od rodzaj
        ("contract_positions", """
            INSERT INTO contract_positions
                (id, contract_id, machine_id, service_id, description, rental_days,
                 quantity, unit_price, rate_type_id, billing_frequency, billing_unit,
                 supplier_id, delivery_date, article_name)
            SELECT
                p.id, p.id_umowy,
                CASE WHEN LOWER(a.rodzaj) IN ('usługa', 'usluga') THEN NULL
                     ELSE p.id_artykulu END,
                CASE WHEN LOWER(a.rodzaj) IN ('usługa', 'usluga') THEN p.id_artykulu
                     ELSE NULL END,
                p.opis, p.liczba_dni,
                p.ilosc, p.cena, NULLIF(p.id_stawki, 0), p.rozliczanie, p.oplataza,
                NULLIF(p.id_dostawcy, 0), p.data_dostawy, p.nazwa
            FROM umowa_pozycja3 p
            LEFT JOIN artykul3 a ON a.id = p.id_artykulu
        """),

        # ── umowa_pozycja2_warunek → position_conditions ──
        # umowa_pozycja2_warunek: id, id_pozycji, id_stawki, opis,
        #   oplata1, oplata2, rozliczana, liczba_dni, minimum
        # id_pozycji references umowa_pozycja3.id (verified: 875/897 match)
        # Filter to only rows whose id_pozycji exists in contract_positions
        # Note: rate_type_id and description columns removed in KISS refactor.
        ("position_conditions", """
            INSERT INTO position_conditions
                (id, position_id, rate1, rate2, billing_label, period_count)
            SELECT
                w.id, w.id_pozycji, w.oplata1, w.oplata2, w.rozliczana, w.liczba_dni
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

    # RAO-P2-028: Deduplikacja numerów umów (legacy miał duplikaty — np. "111", "S142/2026")
    # Dodajemy suffix _DUP{N} do duplikatów aby UNIQUE INDEX uq_contracts_number nie zawiesił startup
    await cur.execute("""
        UPDATE contracts c
        JOIN (
            SELECT id, number,
                   ROW_NUMBER() OVER (PARTITION BY number ORDER BY id) as rn
            FROM contracts
        ) ranked ON c.id = ranked.id
        SET c.number = CONCAT(ranked.number, '_DUP', ranked.rn)
        WHERE ranked.rn > 1
    """)
    dup_fixed = cur.rowcount
    if dup_fixed:
        print(f"   [dedup] contracts.number: {dup_fixed} duplicates renamed with _DUP suffix")

    await conn.commit()
    await cur.close()
    conn.close()


async def step4c_fix_category_duplicates():
    """Zunifikowanie duplikatów kategorii (2026-05-21)."""
    print("[4c/7] Fixing category duplicates …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # 1. Ladowarki teleskopowe → Ładowarki Teleskopowe
    await cur.execute(
        "UPDATE machines SET category_main = 'Ładowarki Teleskopowe' "
        "WHERE category_main = 'Ladowarki teleskopowe'"
    )
    rows1 = cur.rowcount
    print(f"   Ladowarki teleskopowe → Ładowarki Teleskopowe: {rows1} rows")

    # 2. Wózek widłowy → Wózki widłowe w podkategoriach Wozidła (category_sub1)
    await cur.execute(
        "UPDATE machines SET category_sub1 = 'Wózki widłowe' "
        "WHERE category_main = 'Wozidła' AND category_sub1 = 'Wózek widłowy'"
    )
    rows2 = cur.rowcount
    print(f"   Wózek widłowy → Wózki widłowe (sub1): {rows2} rows")

    # 3. Wózek widłowy elektryczny → Wózki widłowe elektryczne (category_sub2)
    await cur.execute(
        "UPDATE machines SET category_sub2 = 'Wózki widłowe elektryczne' "
        "WHERE category_main = 'Wozidła' AND category_sub2 = 'Wózek widłowy elektryczny'"
    )
    rows3 = cur.rowcount
    print(f"   Wózek widłowy elektryczny → Wózki widłowe elektryczne (sub2): {rows3} rows")

    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   OK: {rows1 + rows2 + rows3} category fixes applied")


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

        # Lowercase login for consistency
        login_lower = login.lower() if login else login

        # Insert with must_change_password=1
        await cur.execute("""
            INSERT INTO users
                (id, login, password, first_name, last_name,
                 role, is_active, must_change_password,
                 branch_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, login_lower, hashed_password, first_name, last_name,
            role, True, True,
            branch_id if branch_id and branch_id != 0 else None,
            created_at if created_at else '2024-01-01 00:00:00'
        ))
        count += 1
        print(f"   [{count}] User {login_lower}: temporary password generated, must_change_password=1")

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
    """RAO-P1-011: Mapowanie service_fee_templates.name → additional_services.id (FK).

    Strategia:
      1. Dla każdego service_fee_templates z additional_service_id IS NULL, znajdź
         usługę dodatkową po nazwie (case-insensitive, dopasowanie zaczynane od name).
      2. Jeśli usługa dodatkowa nie istnieje — utwórz ją w additional_services.

    Idempotentne: pomija rekordy z już ustawionym additional_service_id.
    """
    print("[5d] Linking service_fee_templates.name → additional_services (RAO-P1-011) …")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    await cur.execute("""
        SELECT id, name, amount_from, amount_to
        FROM service_fee_templates
        WHERE additional_service_id IS NULL
    """)
    rows = await cur.fetchall()

    linked = 0
    created = 0
    for tpl_id, name, amt_from, amt_to in rows:
        if not name:
            continue
        # Match by exact name (case-insensitive)
        await cur.execute(
            "SELECT id FROM additional_services WHERE LOWER(name) = LOWER(%s) "
            "ORDER BY id ASC LIMIT 1",
            (name,)
        )
        art = await cur.fetchone()
        addsvc_id = art[0] if art else None

        if addsvc_id is None:
            # Spróbuj LIKE (prefix)
            await cur.execute(
                "SELECT id FROM additional_services WHERE LOWER(name) LIKE LOWER(%s) "
                "ORDER BY id ASC LIMIT 1",
                (name[:30] + "%",)
            )
            art = await cur.fetchone()
            addsvc_id = art[0] if art else None

        if addsvc_id is None:
            # Utwórz nową usługę dodatkową
            await cur.execute(
                "INSERT INTO additional_services (name, created_at, updated_at) "
                "VALUES (%s, NOW(), NOW())",
                (name[:200],)
            )
            addsvc_id = cur.lastrowid
            created += 1

        await cur.execute(
            "UPDATE service_fee_templates SET additional_service_id = %s WHERE id = %s",
            (addsvc_id, tpl_id)
        )
        linked += 1

    await conn.commit()

    # Verification
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM service_fee_templates WHERE additional_service_id IS NOT NULL")
    with_fk = (await cur.fetchone())[0]
    pct = (with_fk * 100 // total) if total else 0
    print(f"   linked={linked}, additional_services_created={created}, FK coverage: {with_fk}/{total} ({pct}%)")

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
    orphaned = 0
    for contract_id, oplaty in rows:
        fees = _parse_text_to_fees(oplaty)
        for fee in fees:
            try:
                await cur.execute(
                    """INSERT INTO contract_service_fees
                       (contract_id, sort_order, name,
                        amount_from, amount_to, description, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (contract_id, fee['sort_order'], fee['name'],
                     fee['amount_from'], fee['amount_to'],
                     fee['description'], fee['is_active'])
                )
                inserted += 1
            except pymysql.err.IntegrityError:
                # RAO-P2-062: contract_id nie istnieje (INSERT IGNORE w contracts pominął duplikaty)
                orphaned += 1
        if not fees:
            skipped += 1

    await conn.commit()
    await cur.close()
    conn.close()
    print(f"   {inserted} service fee rows from {len(rows)} contracts ({skipped} unparseable, {orphaned} orphaned skipped)")


async def step5e_fix_placeholders():
    """P1-113/P1-127: Zachowaj placeholdery $1/$2 w opisach opłat dodatkowych.

    WCZEŚNIEJ: ten krok zamieniał $1/$2 na sztywne kwoty (np. "$1" → "150,00 zł").
    TERAZ: placeholdery $1/$2 są zachowywane i podmieniane dynamicznie w locie
    przez formatFeeDescription (frontend) i _resolve_fee_description (backend PDF).
    Umowy zapisane z placeholderami pozwalają na zmianę kwoty w gridzie bez
    ręcznej edycji tekstu opisu.

    Ten krok jest no-op — placeholdery nie są modyfikowane.
    """
    print("[5e] Placeholdery $1/$2 zachowane (dynamiczna podmiana w locie) — no-op")


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
_C_RODZAJ   = 3   # "Usługa" / "artykuł" → split machines / services / additional_services
_C_MODEL    = 6   # Model urządzenia (tylko ~7 wierszy ma wartości)
_C_NUMER    = 7   # Numer wewnętrzny
_C_CAT_MAIN = 8   # Właściwa kategoria główna
_C_CAT_1    = 9   # Kategoria I
_C_CAT_2    = 10  # Kategoria II
_C_CAT_3    = 11  # Kategoria III
_C_ZASIEG   = 12  # Zasięg
_C_UDZWIG   = 13  # Udźwig (t)
_C_DODATKI  = 14  # Dodatki

# Wartości garbage → category = NULL (DoD: x, Test, -, empty)
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


def _parse_numeric(val: "str | None") -> "float | None":
    """
    Parsuje string do float — obsługuje "21m", "21.5", "5", "-", "" → None.
    Używane do zasieg_m i udzwig_t (DECIMAL kolumny w articles).
    """
    if not val or val.strip() in ("-", "x", ""):
        return None
    cleaned = val.strip().lower()
    cleaned = re.sub(r"[a-z\s]+$", "", cleaned)   # usuń sufiks: "21m"→"21"
    cleaned = cleaned.replace(",", ".")              # polska dziesiętna: "21,5"→"21.5"
    cleaned = cleaned.strip()
    if not cleaned:
        return None
    try:
        result = float(cleaned)
        return result if result > 0 else None
    except ValueError:
        return None


# ─── Canonical category overrides (CSV analysis 2026-05) ─────────────────────
# Zapobiega tworzeniu zdublowanych kategorii z wariantów nazw w CSV.
# key: normalize_category(raw_main) → canonical display name
_MAIN_CAT_OVERRIDES: dict = {
    "ladowarka teleskopowa":  "Ładowarki Teleskopowe",  # singular→plural (26 artykułów)
    "ladowarki teleskopowe":  "Ładowarki Teleskopowe",  # wariant lowercase + force display
    "mini zuraw":             "Miniżuraw",               # "Mini żuraw"×2 → scalenie
}

# key: (norm_canonical_main, norm_raw_sub1) → canonical sub1 display name
# norm_canonical_main to norma PO zastosowaniu _MAIN_CAT_OVERRIDES
_SUB1_CAT_OVERRIDES: dict = {
    ("ladowarki teleskopowe", "ladowarka teleskopowa obrotowa"): "Ładowarki Teleskopowe Obrotowe",
    ("ladowarki teleskopowe", "ladowarki teleskopowe sztywne"):  "Ładowarki Teleskopowe Sztywne",
}


def _apply_canonical_mapping(records: list) -> None:
    """
    Normalizuje nazwy kategorii w rekordach CSV — scalanie wariantów, korekty strukturalne.
    Modyfikuje rekordy in-place. Wywoływana RAZ po _parse_csv_file(), przed budowaniem drzewa.

    Przypadki:
    1. main override:  "Ładowarka teleskopowa" (singular) → "Ładowarki Teleskopowe"
                       "Mini żuraw" (2 wiersze) → "Miniżuraw"
    2. sub1 override:  singular/lowercase warianty sub1 → kanoniczne display names
    3. Structural fix: pusty main + sub1="Podnośnik koszowy na samochodzie"
                       → main="Podnośnik na samochodzie" (ID=11128)
    4. Structural fix: Akcesoria + pusty sub1 + niepuste sub2
                       → promote sub2→sub1, sub3→sub2 (ID=5064, 4059)
    """
    for rec in records:
        # ── 1. Main override ───────────────────────────────────────────────
        cm = rec["cat_main"]
        if cm:
            nm = normalize_category(cm)
            if nm in _MAIN_CAT_OVERRIDES:
                rec["cat_main"] = _MAIN_CAT_OVERRIDES[nm]

        # ── 2. Sub1 override ───────────────────────────────────────────────
        cm_final = rec["cat_main"]
        cs1 = rec["cat_sub1"]
        if cm_final and cs1:
            key = (normalize_category(cm_final), normalize_category(cs1))
            if key in _SUB1_CAT_OVERRIDES:
                rec["cat_sub1"] = _SUB1_CAT_OVERRIDES[key]

        # ── 3. Structural: pusty main → przypisz wg sub1 ──────────────────
        if rec["cat_main"] is None and rec["cat_sub1"] and (
            normalize_category(rec["cat_sub1"])
            == normalize_category("Podnośnik koszowy na samochodzie")
        ):
            rec["cat_main"] = "Podnośnik na samochodzie"

        # ── 4. Structural: Akcesoria + pusty sub1 + niepuste sub2 → promote ─
        if (
            rec["cat_main"]
            and normalize_category(rec["cat_main"]) == "akcesoria"
            and rec["cat_sub1"] is None
            and rec["cat_sub2"]
        ):
            rec["cat_sub1"] = rec["cat_sub2"]
            rec["cat_sub2"] = rec["cat_sub3"]
            rec["cat_sub3"] = None


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
                "rodzaj":          row[_C_RODZAJ].strip(),
                "model":           row[_C_MODEL].strip() or None,
                "cat_main":        _clean_cat(row[_C_CAT_MAIN]),
                "cat_sub1":        _clean_cat(row[_C_CAT_1]),
                "cat_sub2":        _clean_cat(row[_C_CAT_2]),
                "cat_sub3":        _clean_cat(row[_C_CAT_3]),
                "internal_number": row[_C_NUMER].strip() or None,
                "zasieg":          _clean_tech(row[_C_ZASIEG]),
                "udzwig":          _clean_tech(row[_C_UDZWIG]),
                "dodatki":         _clean_tech(row[_C_DODATKI]),
                # numeric kolumny (zasieg_m / udzwig_t / dodatki TEXT)
                "zasieg_m":        _parse_numeric(row[_C_ZASIEG]),
                "udzwig_m":        _parse_numeric(row[_C_UDZWIG]),
                "dodatki_txt":     _clean_tech(row[_C_DODATKI]),
            })
    return records


async def step8_csv_categories() -> None:
    """
    RAO-P1-017: CSV → hierarchiczne kategorie + klasyfikacja → UPDATE machines.

    1. GET_LOCK(rao_migrate_csv, 0) — race condition guard (session-scoped)
    2. Parsowanie CSV (csv.reader — CSV-INJ-001 safe)
       Kolumny: [0]=id, [3]=rodzaj, [6]=model, [7]=numer_wewn, [8-14]=kategorie+tech
    2a. _apply_canonical_mapping(): scal warianty nazw (_MAIN_CAT_OVERRIDES, _SUB1_CAT_OVERRIDES)
        + korekty strukturalne (pusty main→inferred, Akcesoria sub2→sub1 promote)
    3. Cache istniejących kategorii w pamięci (Python-side diacritic norm)
    4. Budowanie drzewa (main→sub1→sub2→sub3, sorted dla determinizmu):
       _upsert_cat(): SELECT-or-INSERT — idempotent
    5. UPDATE machines (parametryzowane %s — SQL-INJ-001 safe):
       category_main/sub1/sub2/sub3, category_id (najgłębszy poziom),
       technical_attributes (JSON — kompatybilność wsteczna, zachowany),
       zasieg_m DECIMAL — zasięg sparsowany z col[12] ("21m"→21.0, "-"→NULL),
       udzwig_t DECIMAL — udźwig sparsowany z col[13] ("5t"→5.0, "-"→NULL),
       dodatki  TEXT    — surowy string z col[14] (dodatki/wyposażenie),
       model (COALESCE — nie nadpisuje istniejących wartości),
       internal_number (COALESCE — nie nadpisuje istniejących wartości)
    6. Weryfikacja: COUNT + orphan check (gate per migrations.md)
    7. RELEASE_LOCK

    Idempotentność (2nd run = 0 zmian):
      - Kategorie: cache hit → brak INSERT
      - Articles: te same wartości → MySQL pomija wiersz
      - model / internal_number: COALESCE(NULLIF(..., ''), %s) — nie nadpisuje
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
        _apply_canonical_mapping(records)   # scal warianty nazw + korekty strukturalne
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

        # ── UPDATE machines ───────────────────────────────────────────────────
        n_matched   = 0
        n_unmatched = 0
        # SQL-INJ-001 SAFE: tylko %s placeholders, zero f-stringów z user data
        _UPDATE_SQL = (
            "UPDATE machines SET"
            "  category_main        = %s,"
            "  category_sub1        = %s,"
            "  category_sub2        = %s,"
            "  category_sub3        = %s,"
            "  category_id          = %s,"
            "  technical_attributes = %s,"
            "  model                = COALESCE(NULLIF(model, ''), %s),"
            "  internal_number      = COALESCE(NULLIF(internal_number, ''), %s),"
            "  reach_m              = %s,"
            "  capacity_t           = %s,"
            "  accessories          = %s"
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
                 rec["model"],
                 rec["internal_number"],
                 rec["zasieg_m"], rec["udzwig_m"], rec["dodatki_txt"],
                 art_id),
            )

        # ── Backfill category_main/sub1 z category_id (RAO-P1-029) ───────────
        # Maszyny które mają category_id (ze starego SQL dump) ale brak category_main
        # (bo step8 CSV nie trafił w nie) → deterministyczny backfill po hierarchii.
        #
        # Krok 1: category_id wskazuje bezpośrednio na poziom 'main'
        await cur.execute(
            "UPDATE machines a"
            " JOIN categories c ON a.category_id = c.id AND c.level = 'main'"
            " SET a.category_main = c.name"
            " WHERE a.category_main IS NULL AND a.category_id IS NOT NULL"
        )
        bf_main = cur.rowcount

        # Krok 2: category_id wskazuje na poziom 'sub1' → category_main = parent.name
        await cur.execute(
            "UPDATE machines a"
            " JOIN categories c  ON a.category_id = c.id   AND c.level = 'sub1'"
            " JOIN categories p  ON c.parent_id   = p.id   AND p.level = 'main'"
            " SET a.category_main = p.name, a.category_sub1 = c.name"
            " WHERE a.category_main IS NULL AND a.category_id IS NOT NULL"
        )
        bf_sub1 = cur.rowcount

        # Krok 3: category_id wskazuje na poziom 'sub2' → 2 poziomy wyżej = main
        await cur.execute(
            "UPDATE machines a"
            " JOIN categories c  ON a.category_id = c.id   AND c.level = 'sub2'"
            " JOIN categories s1 ON c.parent_id   = s1.id  AND s1.level = 'sub1'"
            " JOIN categories p  ON s1.parent_id  = p.id   AND p.level = 'main'"
            " SET a.category_main = p.name, a.category_sub1 = s1.name,"
            "     a.category_sub2 = c.name"
            " WHERE a.category_main IS NULL AND a.category_id IS NOT NULL"
        )
        bf_sub2 = cur.rowcount

        # Krok 4: category_id wskazuje na poziom 'sub3'
        await cur.execute(
            "UPDATE machines a"
            " JOIN categories c  ON a.category_id = c.id   AND c.level = 'sub3'"
            " JOIN categories s2 ON c.parent_id   = s2.id  AND s2.level = 'sub2'"
            " JOIN categories s1 ON s2.parent_id  = s1.id  AND s1.level = 'sub1'"
            " JOIN categories p  ON s1.parent_id  = p.id   AND p.level = 'main'"
            " SET a.category_main = p.name, a.category_sub1 = s1.name,"
            "     a.category_sub2 = s2.name, a.category_sub3 = c.name"
            " WHERE a.category_main IS NULL AND a.category_id IS NOT NULL"
        )
        bf_sub3 = cur.rowcount

        total_bf = bf_main + bf_sub1 + bf_sub2 + bf_sub3
        if total_bf:
            print(f"   RAO-P1-029 backfill: {total_bf} maszyn"
                  f" (main={bf_main} sub1={bf_sub1} sub2={bf_sub2} sub3={bf_sub3})")

        # Weryfikacja gate: czy coś zostało bez kategorii mimo posiadania category_id?
        await cur.execute(
            "SELECT COUNT(*) FROM machines"
            " WHERE category_main IS NULL AND category_id IS NOT NULL"
        )
        gap = (await cur.fetchone())[0]
        if gap:
            print(f"   WARN RAO-P1-029: {gap} maszyn ma category_id"
                  " ale nadal brak category_main (sprawdź hierarchię kategorii!)")

        await conn.commit()

        # ── Weryfikacja ───────────────────────────────────────────────────────
        await cur.execute("SELECT COUNT(*) FROM machines")
        total_arts = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM machines WHERE category_main IS NOT NULL")
        with_cat_main = (await cur.fetchone())[0]
        await cur.execute("SELECT COUNT(*) FROM machines WHERE category_id IS NOT NULL")
        with_cat_id = (await cur.fetchone())[0]
        await cur.execute(
            "SELECT COUNT(*) FROM machines"
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
                "contractors","contractor_addresses","machines","services","additional_services","users",
                "contracts","contract_positions","position_conditions",
                "fee_preset_groups","service_fee_templates","contract_service_fees"]:
        await cur.execute(f"SELECT COUNT(*) FROM `{tbl}`")
        cnt = (await cur.fetchone())[0]
        print(f"   {tbl}: {cnt}")

    # ── RAO-P1-017 quality gates ───────────────────────────────────────────
    print("\n   [P1-017 gates]")
    await cur.execute("SELECT COUNT(*) FROM machines")
    total = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM machines WHERE category_main IS NOT NULL")
    with_main = (await cur.fetchone())[0]
    await cur.execute(
        "SELECT COUNT(*) FROM machines"
        " WHERE category_sub1 IS NOT NULL AND category_main IS NULL"
    )
    orphan = (await cur.fetchone())[0]
    print(f"   machines total:          {total}")
    print(f"   category_main set:       {with_main}/{total}")
    if orphan:
        print(f"   GATE FAIL: orphan sub-cats = {orphan}")
    else:
        print("   GATE OK:  no orphan sub-categories")

    await cur.close()
    conn.close()


async def step8b_category_sub2_heuristic() -> None:
    """RAO-P1-017: Uzupełnij category_sub2 na podstawie nazwy maszyny.

    Po step8 (backfill z category_id) niektóre maszyny nadal mają category_sub2=NULL
    albo starą nazwę z legacy. Ta heurystyka mapuje nazwę maszyny → sub2 według
    kanonicznej hierarchii 3-poziomowej (main → sub1 → sub2).

    Idempotentne — aktualizuje tylko gdy category_sub2 IS NULL OR = ''.
    """
    print("[8b/9] RAO-P1-017: Heurystyka category_sub2 z nazwy maszyny ...")
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # Mapa: wzorzec nazwy LIKE → kanoniczna nazwa sub2
    # (zgodna z main.py startup_migrations — single source of truth)
    sub2_updates = [
        # Ładowarki teleskopowe proste
        ("Ładowarka teleskopowa prosta 6m%", "Ładowarka teleskopowa 6 m"),
        ("Ładowarka teleskopowa prosta 7m%", "Ładowarka teleskopowa 7 m"),
        ("Ładowarka teleskopowa prosta 9m%", "Ładowarka teleskopowa 9 m"),
        ("Ładowarka teleskopowa prosta 10m%", "Ładowarka teleskopowa 10 m"),
        ("Ładowarka teleskopowa prosta 12m%", "Ładowarka teleskopowa 12 m"),
        ("Ładowarka teleskopowa prosta 13m%", "Ładowarka teleskopowa 13 m"),
        ("Ładowarka teleskopowa prosta 14m%", "Ładowarka teleskopowa 14 m"),
        ("Ładowarka teleskopowa prosta 17m%", "Ładowarka teleskopowa 17 m"),
        ("Ładowarka teleskopowa prosta 18m%", "Ładowarka teleskopowa 18 m"),
        # Ładowarki teleskopowe obrotowe
        ("Ładowarka teleskopowa obrotowa 14m%", "Ładowarka teleskopowa obrotowa 14 m"),
        ("Ładowarka teleskopowa obrotowa 16m%", "Ładowarka teleskopowa obrotowa 16 m"),
        ("Ładowarka teleskopowa obrotowa 18m%", "Ładowarka teleskopowa obrotowa 18 m"),
        ("Ładowarka teleskopowa obrotowa 20m%", "Ładowarka teleskopowa obrotowa 20 m"),
        ("Ładowarka teleskopowa obrotowa 21m%", "Ładowarka teleskopowa obrotowa 21 m"),
        ("Ładowarka teleskopowa obrotowa 25m%", "Ładowarka teleskopowa obrotowa 25 m"),
        ("Ładowarka teleskopowa obrotowa 26m%", "Ładowarka teleskopowa obrotowa 26 m"),
        ("Ładowarka teleskopowa obrotowa 30m%", "Ładowarka teleskopowa obrotowa 30 m"),
        ("Ładowarka teleskopowa obrotowa 35m%", "Ładowarka teleskopowa obrotowa 35 m"),
        # Podnośniki nożycowe elektryczne
        ("Podnośnik nożycowy elektryczny 6m%", "Podnośnik nożycowy elektryczny 6 m"),
        ("Podnośnik nożycowy elektryczny 6.5m%", "Podnośnik nożycowy elektryczny 6,5 m"),
        ("Podnośnik nożycowy elektryczny 7.5m%", "Podnośnik nożycowy elektryczny 7,5 m"),
        ("Podnośnik nożycowy elektryczny 8m%", "Podnośnik nożycowy elektryczny 8 m"),
        ("Podnośnik nożycowy elektryczny 10m%", "Podnośnik nożycowy elektryczny 10 m"),
        ("Podnośnik nożycowy elektryczny 12m%", "Podnośnik nożycowy elektryczny 12 m"),
        ("Podnośnik nożycowy elektryczny 14m%", "Podnośnik nożycowy elektryczny 14 m"),
        ("Podnośnik nożycowy elektryczny 16m%", "Podnośnik nożycowy elektryczny 16 m"),
        ("Podnośnik nożycowy elektryczny 18m%", "Podnośnik nożycowy elektryczny 18 m"),
        ("Podnośnik nożycowy elektryczny 21m%", "Podnośnik nożycowy elektryczny 21 m"),
        # Podnośniki nożycowe spalinowe
        ("Podnośnik nożycowy spalinowy 10m%", "Podnośnik nożycowy spalinowy 10 m"),
        ("Podnośnik nożycowy spalinowy 12m%", "Podnośnik nożycowy spalinowy 12 m"),
        ("Podnośnik nożycowy spalinowy 15m%", "Podnośnik nożycowy spalinowy 15 m"),
        ("Podnośnik nożycowy spalinowy 18m%", "Podnośnik nożycowy spalinowy 18 m"),
        ("Podnośnik nożycowy spalinowy 22m%", "Podnośnik nożycowy spalinowy 22 m"),
        # Podnośniki przegubowo-teleskopowe elektryczne
        ("Podnośnik przegubowo-teleskopowy elektryczny 10m%", "Podnośnik przegubowo-teleskopowy elektryczny 10 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 12m%", "Podnośnik przegubowo-teleskopowy elektryczny 12 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 15m%", "Podnośnik przegubowo-teleskopowy elektryczny 15 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 16m%", "Podnośnik przegubowo-teleskopowy elektryczny 16 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 18m%", "Podnośnik przegubowo-teleskopowy elektryczny 18 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 20m%", "Podnośnik przegubowo-teleskopowy elektryczny 20 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 21m%", "Podnośnik przegubowo-teleskopowy elektryczny 21 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 22m%", "Podnośnik przegubowo-teleskopowy elektryczny 22 m"),
        ("Podnośnik przegubowo-teleskopowy elektryczny 25m%", "Podnośnik przegubowo-teleskopowy elektryczny 25 m"),
        # Podnośniki przegubowo-teleskopowe spalinowe
        ("Podnośnik przegubowo-teleskopowy spalinowy 12m%", "Podnośnik przegubowo-teleskopowy spalinowy 12 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 14m%", "Podnośnik przegubowo-teleskopowy spalinowy 14 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 16m%", "Podnośnik przegubowo-teleskopowy spalinowy 16 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 18m%", "Podnośnik przegubowo-teleskopowy spalinowy 18 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 20m%", "Podnośnik przegubowo-teleskopowy spalinowy 20 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 21m%", "Podnośnik przegubowo-teleskopowy spalinowy 21 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 22m%", "Podnośnik przegubowo-teleskopowy spalinowy 22 m"),
        ("Podnośnik przegubowo-teleskopowy spalinowy 26m%", "Podnośnik przegubowo-teleskopowy spalinowy 26 m"),
        # Podnośniki teleskopowe spalinowe
        ("Podnośnik teleskopowy spalinowy 16m%", "Podnośnik teleskopowy spalinowy 16 m"),
        ("Podnośnik teleskopowy spalinowy 18m%", "Podnośnik teleskopowy spalinowy 18 m"),
        ("Podnośnik teleskopowy spalinowy 20m%", "Podnośnik teleskopowy spalinowy 20 m"),
        ("Podnośnik teleskopowy spalinowy 21m%", "Podnośnik teleskopowy spalinowy 21 m"),
        ("Podnośnik teleskopowy spalinowy 22m%", "Podnośnik teleskopowy spalinowy 22 m"),
        ("Podnośnik teleskopowy spalinowy 24m%", "Podnośnik teleskopowy spalinowy 24 m"),
        ("Podnośnik teleskopowy spalinowy 26m%", "Podnośnik teleskopowy spalinowy 26 m"),
        # Podnośniki gąsienicowe
        ("Podnośnik gąsienicowy 22m%", "Podnośnik gąsienicowy 22 m"),
        ("Podnośnik gąsienicowy 23m%", "Podnośnik gąsienicowy 23 m"),
        ("Podnośnik gąsienicowy 24m%", "Podnośnik gąsienicowy 24 m"),
        ("Podnośnik gąsienicowy 25m%", "Podnośnik gąsienicowy 25 m"),
        # Podnośniki przyczepowe
        ("Podnośnik przyczepowy 12m%", "Podnośnik przyczepowy 12 m"),
        ("Podnośnik przyczepowy 15m%", "Podnośnik przyczepowy 15 m"),
        ("Podnośnik przyczepowy 17m%", "Podnośnik przyczepowy 17 m"),
        # Wózki widłowe elektryczne
        ("Wózek widłowy elektryczny 1.5t%", "Wózek widłowy elektryczny 1,5t"),
        ("Wózek widłowy elektryczny 1.8t%", "Wózek widłowy elektryczny 1,8t"),
        ("Wózek widłowy elektryczny 2t%", "Wózek widłowy elektryczny 2t"),
        ("Wózek widłowy elektryczny 2.5t%", "Wózek widłowy elektryczny 2,5t"),
        ("Wózek widłowy elektryczny 3t%", "Wózek widłowy elektryczny 3t"),
        ("Wózek widłowy elektryczny 3.5t%", "Wózek widłowy elektryczny 3,5t"),
        ("Wózek widłowy elektryczny 4t%", "Wózek widłowy elektryczny 4t"),
        ("Wózek widłowy elektryczny 4.5t%", "Wózek widłowy elektryczny 4,5t"),
        ("Wózek widłowy elektryczny 5t%", "Wózek widłowy elektryczny 5t"),
        ("Wózek widłowy elektryczny 6t%", "Wózek widłowy elektryczny 6t"),
        ("Wózek widłowy elektryczny 7t%", "Wózek widłowy elektryczny 7t"),
        ("Wózek widłowy elektryczny 8t%", "Wózek widłowy elektryczny 8t"),
        ("Wózek widłowy elektryczny 10t%", "Wózek widłowy elektryczny 10t"),
        # Wózki widłowe LPG
        ("Wózek widłowy LPG 1.5t%", "Wózek widłowy LPG 1,5t"),
        ("Wózek widłowy LPG 1.8t%", "Wózek widłowy LPG 1,8t"),
        ("Wózek widłowy LPG 2t%", "Wózek widłowy LPG 2t"),
        ("Wózek widłowy LPG 2.5t%", "Wózek widłowy LPG 2,5t"),
        ("Wózek widłowy LPG 3t%", "Wózek widłowy LPG 3t"),
        ("Wózek widłowy LPG 3.5t%", "Wózek widłowy LPG 3,5t"),
        ("Wózek widłowy LPG 4t%", "Wózek widłowy LPG 4t"),
        ("Wózek widłowy LPG 4.5t%", "Wózek widłowy LPG 4,5t"),
        ("Wózek widłowy LPG 5t%", "Wózek widłowy LPG 5t"),
        ("Wózek widłowy LPG 6t%", "Wózek widłowy LPG 6t"),
        ("Wózek widłowy LPG 7t%", "Wózek widłowy LPG 7t"),
        ("Wózek widłowy LPG 8t%", "Wózek widłowy LPG 8t"),
        ("Wózek widłowy LPG 10t%", "Wózek widłowy LPG 10t"),
        # Wózki widłowe Diesel
        ("Wózek widłowy Diesel 1.5t%", "Wózek widłowy Diesel 1,5t"),
        ("Wózek widłowy Diesel 1.8t%", "Wózek widłowy Diesel 1,8t"),
        ("Wózek widłowy Diesel 2t%", "Wózek widłowy Diesel 2t"),
        ("Wózek widłowy Diesel 2.5t%", "Wózek widłowy Diesel 2,5t"),
        ("Wózek widłowy Diesel 3t%", "Wózek widłowy Diesel 3t"),
        ("Wózek widłowy Diesel 3.5t%", "Wózek widłowy Diesel 3,5t"),
        ("Wózek widłowy Diesel 4t%", "Wózek widłowy Diesel 4t"),
        ("Wózek widłowy Diesel 4.5t%", "Wózek widłowy Diesel 4,5t"),
        ("Wózek widłowy Diesel 5t%", "Wózek widłowy Diesel 5t"),
        ("Wózek widłowy Diesel 6t%", "Wózek widłowy Diesel 6t"),
        ("Wózek widłowy Diesel 7t%", "Wózek widłowy Diesel 7t"),
        ("Wózek widłowy Diesel 8t%", "Wózek widłowy Diesel 8t"),
        ("Wózek widłowy Diesel 10t%", "Wózek widłowy Diesel 10t"),
        ("Wózek widłowy Diesel 12t%", "Wózek widłowy Diesel 12t"),
        # Akcesoria (category_sub1 = NULL → sub2 = nazwa akcesorium)
        ("Kosz osobowy%", "Kosz osobowy"),
        ("Chwytak do płyt%", "Chwytak do płyt"),
        ("Łyżka%", "Łyżka"),
        ("Wciągarka typu żuraw%", "Wciągarka typu żuraw"),
        ("Wciągarka%", "Wciągarka"),
        ("Żuraw z hakiem%", "Żuraw z hakiem"),
        ("Hak obrotowy%", "Hak obrotowy"),
        ("Zawiesia łańcuchowe%", "Zawiesia łańcuchowe"),
        ("Zawiesia pasowe%", "Zawiesia pasowe"),
        ("Przedłużenie wideł%", "Przedłużenie wideł"),
        ("Kosz narzędziowy%", "Kosz narzędziowy"),
        ("Szelki bezpieczeństwa%", "Szelki bezpieczeństwa"),
        ("Kanister%", "Kanister"),
    ]

    total_updated = 0
    for pattern, sub2 in sub2_updates:
        await cur.execute(
            "UPDATE machines SET category_sub2 = %s "
            "WHERE name LIKE %s "
            "AND (category_sub2 IS NULL OR category_sub2 = '')",
            (sub2, pattern),
        )
        if cur.rowcount > 0:
            total_updated += cur.rowcount

    await conn.commit()

    # Weryfikacja: ile maszyn nadal nie ma category_sub2?
    await cur.execute(
        "SELECT COUNT(*) FROM machines "
        "WHERE category_main IS NOT NULL AND category_sub1 IS NOT NULL "
        "AND (category_sub2 IS NULL OR category_sub2 = '')"
    )
    missing = (await cur.fetchone())[0]
    if missing:
        print(f"   WARN: {missing} maszyn z main+sub1 nadal bez sub2 (nie matchuje wzorce)")

    await cur.close()
    conn.close()
    print(f"   OK: {total_updated} maszyn uzupelnionych category_sub2")


async def step9_postal_codes_migration():
    """RAO-P1-008: Extract postal_code + city from delivery_address, seed postal_codes table."""
    import re

    print("[9/9] RAO-P1-008: Strukturalizacja adresów (postal_code + city) ...")

    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, db=DB_NAME)
    cur = await conn.cursor()

    # 9.1 Seed postal_codes table from CSV (RAO-P2-028: full Spis PNA Poczty Polskiej, 5 kolumn)
    csv_path = os.path.join(project_root, "backend", "data", "postal_codes.csv")
    if os.path.exists(csv_path):
        print(f"   Seeding postal_codes from {csv_path}...")
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            inserted = 0
            for row in reader:
                # CSV: postal_code, city, gmina, powiat, wojewodztwo (5 kolumn z oficjalnego Spisu PNA)
                if len(row) >= 2:
                    code = row[0].strip()
                    city = row[1].strip()
                    gmina = row[2].strip() if len(row) > 2 and row[2].strip() else None
                    powiat = row[3].strip() if len(row) > 3 and row[3].strip() else None
                    wojewodztwo = row[4].strip() if len(row) > 4 and row[4].strip() else None
                    if code and city:
                        await cur.execute(
                            "INSERT IGNORE INTO postal_codes (postal_code, city, gmina, powiat, wojewodztwo) VALUES (%s, %s, %s, %s, %s)",
                            (code, city, gmina, powiat, wojewodztwo)
                        )
                        inserted += 1
            await conn.commit()
            print(f"   Seeded {inserted} postal codes (full Spis PNA: 5 kolumn)")
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
                "SELECT city FROM postal_codes WHERE postal_code = %s LIMIT 1",
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

    # 9.3 Backfill postal_code_id (RAO-P2-028: FK do postal_codes dla deterministycznych statystyk)
    print("   Backfilling postal_code_id from postal_codes dictionary...")
    await cur.execute("""
        UPDATE contracts c
        JOIN postal_codes p ON c.postal_code = p.postal_code
        SET c.postal_code_id = p.id
        WHERE c.postal_code IS NOT NULL AND c.postal_code != '' AND c.postal_code_id IS NULL
    """)
    await conn.commit()
    await cur.execute("SELECT COUNT(*) FROM contracts WHERE postal_code_id IS NOT NULL")
    with_fk = (await cur.fetchone())[0]
    print(f"   Backfilled postal_code_id: {with_fk} contracts")

    # 9.4 Report
    await cur.execute("SELECT COUNT(*) FROM contracts WHERE postal_code IS NOT NULL")
    with_code = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM contracts WHERE delivery_address IS NOT NULL")
    with_address = (await cur.fetchone())[0]
    # RAO-P2-062: is_legacy column removed — all migrated contracts are legacy by definition
    legacy_ct = await cur.execute("SELECT COUNT(*) FROM contracts")
    legacy_ct = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM postal_codes")
    pna_total = (await cur.fetchone())[0]

    print(f"   Updated {updated}/{len(rows)} contracts with postal_code")
    print(f"   Coverage: {with_code}/{with_address} ({with_code*100//with_address if with_address else 0}%)")
    print(f"   postal_code_id FK: {with_fk} contracts")
    print(f"   total contracts: {legacy_ct} (all legacy — migrated from dump)")
    print(f"   postal_codes dict: {pna_total} entries (full Spis PNA Poczty Polskiej)")
    print("   OK")

    await cur.close()
    conn.close()


async def step10_import_rozliczenie() -> None:
    """
    RAO-P2-032: Import rzeczywistych rozliczeń z dumpa starej bazy (rozliczenie table).

    Source: spec/backlog/archiwum/refinement/toolsmart_roa_*.sql
    Tabela: rozliczenie (id, data, id_pozycji, wartosc)
    Target: contract_settlements (contract_id, position_id, cost_client, settled_at, source='legacy')

    Algorytm:
    1. Parsuj INSERT INTO rozliczenie VALUES z dumpa SQL (regex)
    2. Dla każdego wiersza: mapuj id_pozycji → contract_positions.id (zachowane w migracji)
    3. Pobierz contract_id z contract_positions
    4. INSERT IGNORE do contract_settlements (idempotentny — UNIQUE constraint)
    5. Orphaned (id_pozycji nie istnieje) → _import_errors

    Determinizm: sortowanie po id_pozycji, data — reproducible.
    Idempotentność: INSERT IGNORE + UNIQUE (contract_id, position_id, service_fee_id=NULL, settled_at)
    """
    import re
    import glob

    print("\n── step10: Import rozliczenie → contract_settlements ──")

    # Znajdź dump SQL
    csv_dir = os.path.join(project_root, "spec", "backlog", "archiwum", "refinement")
    sql_matches = glob.glob(os.path.join(csv_dir, "toolsmart_roa_*.sql"))
    if not sql_matches:
        print("   WARN: toolsmart_roa_*.sql not found — skipping rozliczenie import")
        return
    sql_path = sql_matches[0]
    print(f"   Source: {os.path.basename(sql_path)}")

    # Parsuj rozliczenie VALUES z dumpa
    rozliczenia = []  # (id, data, id_pozycji, wartosc)
    in_rozliczenie = False
    with open(sql_path, "r", encoding="utf-8") as f:
        for line in f:
            if "INSERT INTO `rozliczenie` VALUES" in line:
                in_rozliczenie = True
                continue
            if in_rozliczenie:
                if line.startswith("("):
                    # (27815,'2025-08-19',10220,300.0000),
                    m = re.match(r"\((\d+),'([^']*)',(\d+),([\d.]+)\)", line.strip().rstrip(","))
                    if m:
                        rozliczenia.append({
                            "legacy_id": int(m.group(1)),
                            "data": m.group(2),
                            "id_pozycji": int(m.group(3)),
                            "wartosc": float(m.group(4)),
                        })
                elif "/*!40000 ALTER TABLE `rozliczenie` ENABLE KEYS" in line:
                    break

    print(f"   Parsed: {len(rozliczenia)} rozliczenie rows")
    if not rozliczenia:
        print("   WARN: no rozliczenie rows found — skipping")
        return

    # Połącz z DB
    conn = await aiomysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
                                   db=DB_NAME, autocommit=False)
    cur = await conn.cursor()

    # RAO-P2-062: tabela na logowanie orphaned rows (brakowała — CREATE IF NOT EXISTS)
    await cur.execute("""
        CREATE TABLE IF NOT EXISTS _import_errors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source VARCHAR(50) NOT NULL,
            raw_data TEXT,
            error_message VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # Pobierz mapowanie: contract_positions.id → contract_id
    await cur.execute("SELECT id, contract_id FROM contract_positions")
    pos_to_contract = {r[0]: r[1] for r in await cur.fetchall()}

    # Grupuj rozliczenia po (id_pozycji, data) — suma wartosc per dzień
    # (stara aplikacja insertowała 1 wiersz/dzień, ale mogą być duplikaty)
    from collections import defaultdict
    grouped = defaultdict(lambda: {"wartosc": 0.0, "contract_id": None})
    for r in rozliczenia:
        pid = r["id_pozycji"]
        if pid not in pos_to_contract:
            # Orphaned — log do _import_errors
            await cur.execute(
                "INSERT INTO _import_errors (source, raw_data, error_message) VALUES (%s, %s, %s)",
                ("rozliczenie", str(r), f"id_pozycji={pid} not found in contract_positions"),
            )
            continue
        contract_id = pos_to_contract[pid]
        key = (pid, r["data"])
        grouped[key]["wartosc"] += r["wartosc"]
        grouped[key]["contract_id"] = contract_id

    # INSERT IGNORE (idempotentny — UNIQUE constraint zapobiega duplikatom)
    inserted = 0
    skipped = 0
    orphaned = sum(1 for r in rozliczenia if r["id_pozycji"] not in pos_to_contract)

    for (pid, data), info in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1])):
        contract_id = info["contract_id"]
        wartosc = round(info["wartosc"], 2)
        try:
            await cur.execute(
                """INSERT IGNORE INTO contract_settlements
                   (contract_id, position_id, service_fee_id, cost_client, settled_at, source, notes)
                   VALUES (%s, %s, NULL, %s, %s, 'legacy', 'Import z rozliczenie (RAO-P2-032)')""",
                (contract_id, pid, wartosc, data),
            )
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            await cur.execute(
                "INSERT INTO _import_errors (source, raw_data, error_message) VALUES (%s, %s, %s)",
                ("rozliczenie", f"pid={pid} data={data} wartosc={wartosc}", str(e)),
            )
            skipped += 1

    await conn.commit()

    # Weryfikacja
    await cur.execute("SELECT COUNT(*) FROM contract_settlements WHERE source='legacy'")
    total_settlements = (await cur.fetchone())[0]
    await cur.execute("SELECT SUM(cost_client) FROM contract_settlements WHERE source='legacy'")
    total_revenue = (await cur.fetchone())[0]
    await cur.execute("SELECT COUNT(*) FROM _import_errors WHERE source='rozliczenie'")
    errors = (await cur.fetchone())[0]

    print(f"   Inserted: {inserted} settlements")
    print(f"   Skipped (duplicates): {skipped}")
    print(f"   Orphaned (logged): {orphaned}")
    print(f"   Total legacy settlements: {total_settlements}")
    print(f"   Total legacy revenue: {total_revenue:.2f} zl")
    print(f"   Import errors: {errors}")
    print("   OK")

    await cur.close()
    conn.close()


async def step11_fix_position_condition_periods() -> None:
    """RAO-P0-048: backfill period_from/period_to for migrated position_conditions."""
    print("[11/11] RAO-P0-048: Poprawa period_from/period_to dla warunków ...")
    from database import AsyncSessionLocal
    from contracts.service import contract_service
    async with AsyncSessionLocal() as db:
        try:
            fixed = await contract_service.migrate_position_condition_periods(db)
            print(f"   Fixed {fixed} conditions")
        except Exception as e:
            print(f"   WARN: failed to fix periods: {e}")


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
        await step4c_fix_category_duplicates()  # Zunifikowanie duplikatów kategorii (2026-05-21)
        await step4b_migrate_users()  # SECURITY: random bcrypt passwords
        await step5_service_fee_templates()
        await step5c_create_preset_groups()
        await step5d_link_articles_to_templates()  # RAO-P1-011
        await step5b_contract_service_fees()
        await step5e_fix_placeholders()  # Fix placeholder hotfix (RAO-P3-014)
        await step6_drop_old()
        # step7_rehash removed - passwords already hashed in step4b
        await step8_csv_categories()   # RAO-P1-017
        await step8b_category_sub2_heuristic()  # RAO-P1-017: heurystyka sub2 z nazwy
        await step9_postal_codes_migration()  # RAO-P1-008
        await step10_import_rozliczenie()  # RAO-P2-032: rzeczywiste rozliczenia z legacy
        await step11_fix_position_condition_periods()  # RAO-P0-048
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
