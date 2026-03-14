# 08 — Plan migracji danych (stara baza → nowa baza)

> **INSTRUKCJA DLA AGENTA:** Wykonaj migrację w dokładnej kolejności.
> Wszystkie dane przenoszone są przez INSERT...SELECT — BEZ procedur.

## Kolejność migracji (dependencies-first)

```
1. company (firma → company + additional_fees)
2. branches (oddzial → branches)
3. users (uzytkownik → users)
4. categories (kategoria → categories)
5. salespeople (handlowiec → salespeople)
6. rate_types (stawka → rate_types)
7. cost_types (koszt_typ → cost_types)
8. contractors (kontrahent2 → contractors)
9. contractor_addresses (adres → contractor_addresses)
10. articles (artykul3 → articles)
11. contracts (umowa2 → contracts)
12. deliveries (dostawa → deliveries)
13. delivery_addresses (adres_dostawy → delivery_addresses)
14. contract_positions (umowa_pozycja3 → contract_positions)
15. position_conditions (umowa_pozycja2_warunek → position_conditions)
16. costs (koszt → costs)
17. settlements (rozliczenie → settlements)
```

## Skrypty migracyjne

```sql
-- ============================================================
-- UWAGA: Uruchom na nowej bazie rao_new AFTER DDL z 01_DATABASE_DDL.md
-- Stara baza: rao (existing)
-- Nowa baza: rao_new
-- ============================================================

-- 1. COMPANY (firma → company)
INSERT INTO rao_new.company (
    id, name, name_short, nip, regon, postal_code, city, street,
    header_text, logo, bank_name, bank_account, numbering_start,
    increment_step, report_folder, protocol_folder, app_version,
    contract_rental_text, contract_service_text
)
SELECT
    ID, NAZWA, NAZWA_KROTKA, NIP, REGON, KOD_POCZTOWY, MIEJSCOWOSC,
    ULICA_LOKAL, NAGLOWEK, LOGO, BANK, RACHUNEK, numeracja,
    INTERWAL, FOLDER, FOLDER2, wersja,
    Uslugi1, Uslugi2
FROM rao.firma;

-- 1b. ADDITIONAL FEES (firma.oplata_* → additional_fees)
INSERT INTO rao_new.additional_fees (company_id, fee_type, is_active, amount_from, amount_to, description)
SELECT 1, 'refueling', COALESCE(czy_oplata_tankowanie, 0),
       oplata_tankowanie_od, oplata_tankowanie_do, oplata_tankowanie_opis
FROM rao.firma WHERE ID = 1;

INSERT INTO rao_new.additional_fees (company_id, fee_type, is_active, amount_from, amount_to, description)
SELECT 1, 'transport', COALESCE(czy_oplata_transport, 0),
       oplata_tarnsport_od, oplata_tarnsport_do, oplata_transport_opis
FROM rao.firma WHERE ID = 1;

INSERT INTO rao_new.additional_fees (company_id, fee_type, is_active, amount_from, amount_to, description)
SELECT 1, 'cleaning1', COALESCE(czy_oplata_czyszczenie1, 0),
       oplata_czyszczenie1_od, oplata_czyszczenie1_do, oplata_czyszczenie1_opis
FROM rao.firma WHERE ID = 1;

INSERT INTO rao_new.additional_fees (company_id, fee_type, is_active, amount_from, amount_to, description)
SELECT 1, 'cleaning2', COALESCE(czy_oplata_czyszczenie2, 0),
       oplata_czyszczenie2_od, oplata_czyszczenie2_do, oplata_czyszczenie2_opis
FROM rao.firma WHERE ID = 1;

INSERT INTO rao_new.additional_fees (company_id, fee_type, is_active, amount_from, amount_to, description)
SELECT 1, 'excess_downtime', COALESCE(czy_oplata_ponadnormatywny, 0),
       oplata_ponadnormatywny_przestuj_od, oplata_ponadnormatywny_przestuj_do,
       oplata_ponadnormatywny_przestuj_opis
FROM rao.firma WHERE ID = 1;

-- 2. BRANCHES (oddzial → branches)
INSERT INTO rao_new.branches (id, name, address, postal_code, city, street)
SELECT ID, NAZWA, ADRES, KOD_POCZTOWY, MIEJSCOWOSC, ULICA_LOKAL
FROM rao.oddzial;

-- 3. USERS (uzytkownik → users)
-- UWAGA: Stare hasła są PLAINTEXT! Trzeba je zahashować bcrypt.
-- Ten skrypt przenosi plaintext, ale aplikacja musi wymóc zmianę hasła
-- przy pierwszym logowaniu lub admin musi zresetować hasła.
INSERT INTO rao_new.users (
    id, login, password, first_name, last_name, role, branch_id, created_at
)
SELECT
    ID, LOGIN,
    CONCAT('$PLAINTEXT$', HASLO),  -- Marker: app musi wykryć i wymusić zmianę
    IMIE, NAZWISKO,
    CASE WHEN ID_GRUPY = 1 THEN 'admin' ELSE 'user' END,
    id_oddzialu,
    COALESCE(DATA, NOW())
FROM rao.uzytkownik;

-- 4. CATEGORIES (kategoria → categories)
INSERT INTO rao_new.categories (id, name, code, description)
SELECT ID, NAZWA, KOD, OPIS
FROM rao.kategoria;

-- 5. SALESPEOPLE (handlowiec → salespeople)
INSERT INTO rao_new.salespeople (id, name, phone, is_active)
SELECT ID, NAZWA, TELEFON, COALESCE(AKTYWNY, 1) = 1
FROM rao.handlowiec;

-- 6. RATE TYPES (stawka → rate_types)
INSERT INTO rao_new.rate_types (id, name, description, is_dependent)
SELECT ID, NAZWA, OPIS, COALESCE(ZALEZNA, 0) = 1
FROM rao.stawka;

-- 7. COST TYPES (koszt_typ → cost_types)
INSERT INTO rao_new.cost_types (id, name, description, amount1, amount2)
SELECT ID, NAZWA, OPIS, kwota1, kwota2
FROM rao.koszt_typ;

-- 8. CONTRACTORS (kontrahent2 → contractors)
INSERT INTO rao_new.contractors (
    id, name, name_short, nip, regon, pesel, postal_code, city, street, unit,
    notes, is_supplier, email, contact_person1, phone1, contact_person2, phone2,
    landline_phone, website, files_folder, gus_date, created_at, updated_at
)
SELECT
    ID, NAZWA, nazwa_krotka, NIP, REGON, PESEL, KOD_POCZTOWY, MIEJSCOWOSC,
    ULICA, LOKAL, UWAGI, COALESCE(DOSTAWCA, 0) = 1, EMAIL,
    OSOBA_KONTAKTOWA, TELEFON, OSOBA_KONTAKTOWA2, TELEFON2,
    telefon_stac, www, FOLDER, DATA_GUS,
    COALESCE(DATA, NOW()), data_modyfikacji
FROM rao.kontrahent2;

-- 9. CONTRACTOR ADDRESSES (adres → contractor_addresses)
INSERT INTO rao_new.contractor_addresses (
    id, contractor_id, name, country_code, postal_code, city, street,
    notes, contact_person, phone, email, is_default_delivery, is_headquarters,
    latitude, longitude
)
SELECT
    ID, ID_KONTRAHENTA, NAZWA, COALESCE(SYM_KRAJU, 'PL'),
    KOD_POCZTOWY, MIEJSCOWOSC, ULICA_LOKAL,
    UWAGI, OSOBA, TELEFON, MAIL,
    COALESCE(DOMYSLNA_DOSTAWA, 0) = 1,
    COALESCE(SIEDZIBA, 0) = 1,
    LTT, LNG
FROM rao.adres;

-- 10. ARTICLES (artykul3 → articles)
INSERT INTO rao_new.articles (
    id, name, is_service, registration_no, serial_no, brand, model,
    replacement_value, category_id, owner_id, branch_id, description,
    notes, rental_days, article_type, created_at, updated_at
)
SELECT
    ID, NAZWA,
    CASE WHEN USLUGA IS NOT NULL AND USLUGA != '' THEN TRUE ELSE FALSE END,
    NR_REJESTRACYJNY, nr_seryjny, MARKA, MODEL,
    wartosc, ID_KATEGORII, ID_WLASCICIEL, ID_ODDZIALU,
    OPIS, UWAGI, LICZBA_DNI, rodzaj,
    COALESCE(DATA_DODANIA, NOW()), DATA_MODYFIKACJI
FROM rao.artykul3;

-- 11. CONTRACTS (umowa2 → contracts)
INSERT INTO rao_new.contracts (
    id, contractor_id, branch_id, salesperson_id, number, auto_number,
    contract_type, description, delivery_address, date_from, date_to,
    total_value, prepayment_amount, prepayment_document,
    invoice_amount, invoice_document, notes, additional_fees_text,
    contact_person1, contact_phone1, show_person1,
    contact_person2, contact_phone2, show_person2,
    email, phone, contractor_name, print_path, print_date,
    report_without_data, working_days_per_week, position_count,
    created_at, updated_at
)
SELECT
    u.ID, u.ID_KONTRAHENTA,
    (SELECT IDO FROM rao.umowa_oddzial WHERE IDU = u.ID LIMIT 1),
    u.id_handlowca,
    u.NUMER, u.AUTONUMER,
    COALESCE(u.typ, 'S'),
    u.OPIS, u.ADRES, u.DATA_OD, u.DATA_DO,
    u.WARTOSC, u.PRZEDPLATA_KWOTA, u.PRZEDPLATA_DOKUMENT,
    u.FAKTURA_KWOTA, u.FAKTURA_DOKUMENT, u.UWAGI, u.OPLATY,
    u.OSOBA1, u.TELEFON1, COALESCE(u.pokaz_osobe1, 1) = 1,
    u.OSOBA2, u.TELEFON2, COALESCE(u.pokaz_osobe2, 1) = 1,
    u.EMAIL, u.TELEFON, u.NAZWA,
    u.SCIEZKA_WYDRUKU, u.DATA_WYDRUKU,
    COALESCE(u.PZ_BEZ, 0) = 1,
    COALESCE(u.LICZBA_DNI, 6),
    COALESCE(u.ilepoz, 0),
    COALESCE(u.DATA_WPROWADZENIA, NOW()), u.DATA_MODYFIKACJI
FROM rao.umowa2 u;

-- 12. DELIVERIES (dostawa → deliveries)
INSERT INTO rao_new.deliveries (id, contract_id, address_id, latitude, longitude)
SELECT ID, ID_UMOWY, ID_ADRES, LTT, LNG
FROM rao.dostawa;

-- 13. DELIVERY ADDRESSES (adres_dostawy → delivery_addresses)
INSERT INTO rao_new.delivery_addresses (
    id, contract_id, name, street, number, postal_code,
    hamlet, city, town, village, county, municipality,
    province, district, neighbourhood
)
SELECT
    ID, ID_UMOWY, NAZWA, ULICA, NUMER, KOD_POCZTOWY,
    HAMLET, MIEJSCOWOSC, MIASTO, WIOSKA, POWIAT, GMINA,
    WOJEWODZTWO, DZIELNICA, OSIEDLE
FROM rao.adres_dostawy;

-- 14. CONTRACT POSITIONS (umowa_pozycja3 → contract_positions)
INSERT INTO rao_new.contract_positions (
    id, contract_id, article_id, rental_type, description, rental_days,
    quantity, unit_price, costs, rate_type_id, billing_frequency,
    billing_unit, supplier_id, delivery_date, article_name
)
SELECT
    p.ID, p.ID_UMOWY, p.ID_ARTYKULU, p.TYP_WYNAJMU, p.OPIS, p.LICZBA_DNI,
    p.ILOSC, p.CENA, p.koszty, p.ID_STAWKI, p.rozliczanie,
    p.oplataza, p.id_dostawcy, p.data_dostawy, p.NAZWA
FROM rao.umowa_pozycja3 p;

-- 15. POSITION CONDITIONS (umowa_pozycja2_warunek → position_conditions)
INSERT INTO rao_new.position_conditions (
    id, position_id, rate_type_id, description, rate1, rate2,
    billing_label, period_count, minimum
)
SELECT
    ID, ID_POZYCJI, ID_STAWKI, OPIS, OPLATA1, OPLATA2,
    ROZLICZANA, LICZBA_DNI, MINIMUM
FROM rao.umowa_pozycja2_warunek;

-- 16. COSTS (koszt → costs)
INSERT INTO rao_new.costs (id, cost_type_id, position_id, description, amount, created_at)
SELECT ID, ID_TYPU, ID_UMOWA_POZYJCA, OPIS, KWOTA, COALESCE(DATA, NOW())
FROM rao.koszt;

-- 17. SETTLEMENTS (rozliczenie → settlements)
INSERT INTO rao_new.settlements (id, position_id, date, amount)
SELECT ID, ID_POZYCJI, DATA, WARTOSC
FROM rao.rozliczenie;

-- ============================================================
-- RESET AUTO_INCREMENT na wszystkich tabelach
-- ============================================================
-- Po migracji ustawiamy auto_increment wyżej niż max(id)
-- aby nowe rekordy nie kolidowały

SET @max_id = (SELECT COALESCE(MAX(id), 0) + 1 FROM rao_new.contractors);
SET @sql = CONCAT('ALTER TABLE rao_new.contractors AUTO_INCREMENT = ', @max_id);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- (powtórz dla każdej tabeli)
```

## Tabele NIE migrowane (legacy/tymczasowe)

| Tabela | Powód |
|--------|-------|
| `a`, `u` | Historyczny cache/log — dane dostępne z relacji |
| `artykul`, `artykul2` | Legacy wersje — zastąpione przez `artykul3` |
| `umowa`, `umowa_pozycja`, `umowa_pozycja2` | Legacy wersje |
| `kontrahent` | Legacy — zastąpione przez `kontrahent2` |
| `kontakt` | Nieużywane w kodzie (brak SELECT/INSERT w .cs) |
| `imp`, `imp_*` | Tabele importowe (jednorazowe) |
| `dane` | View, nie tabela danych |
| `temp`, `lp`, `nr_umowy`, `oddo` | Tabele pomocnicze/tymczasowe |

## Post-migracja: hashowanie haseł

```python
# Skrypt jednorazowy po migracji
import bcrypt
from sqlalchemy import create_engine, text

engine = create_engine("mariadb+mariadbconnector://user:pass@localhost/rao_new")

with engine.begin() as conn:
    users = conn.execute(text("SELECT id, password FROM users")).fetchall()
    for user_id, password in users:
        if password.startswith("$PLAINTEXT$"):
            plain = password.replace("$PLAINTEXT$", "")
            hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                text("UPDATE users SET password = :pwd WHERE id = :id"),
                {"pwd": hashed, "id": user_id}
            )
    print(f"Zaktualizowano {len(users)} haseł")
```

## Weryfikacja migracji

```sql
-- Porównaj liczbę rekordów stare vs nowe
SELECT 'contractors' AS tbl, (SELECT COUNT(*) FROM rao.kontrahent2) AS old_count,
       (SELECT COUNT(*) FROM rao_new.contractors) AS new_count
UNION ALL
SELECT 'addresses', (SELECT COUNT(*) FROM rao.adres),
       (SELECT COUNT(*) FROM rao_new.contractor_addresses)
UNION ALL
SELECT 'articles', (SELECT COUNT(*) FROM rao.artykul3),
       (SELECT COUNT(*) FROM rao_new.articles)
UNION ALL
SELECT 'contracts', (SELECT COUNT(*) FROM rao.umowa2),
       (SELECT COUNT(*) FROM rao_new.contracts)
UNION ALL
SELECT 'positions', (SELECT COUNT(*) FROM rao.umowa_pozycja3),
       (SELECT COUNT(*) FROM rao_new.contract_positions)
UNION ALL
SELECT 'conditions', (SELECT COUNT(*) FROM rao.umowa_pozycja2_warunek),
       (SELECT COUNT(*) FROM rao_new.position_conditions);
-- Wszystkie old_count == new_count → migracja OK
```
