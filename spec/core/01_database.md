# 01 — Nowa baza danych MariaDB (3NF) — Kompletne DDL

> **INSTRUKCJA DLA AGENTA:** Wykonaj poniższe DDL w dokładnej kolejności.
> Każda tabela ma FK constraints, indeksy i komentarze.
> NIE ZMIENIAJ nazw tabel ani kolumn — frontend i backend korzystają z tych nazw.

## Kolejność tworzenia (dependencies-first)

```sql
-- ============================================================
-- 0. BAZA DANYCH
-- ============================================================
CREATE DATABASE IF NOT EXISTS rao_new
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_polish_ci;
USE rao_new;

-- ============================================================
-- 1. TABELE BEZ ZALEŻNOŚCI (leaf tables)
-- ============================================================

-- 1.1 Użytkownicy
CREATE TABLE users (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    login                 VARCHAR(50)  NOT NULL UNIQUE,
    email                 VARCHAR(100) NULL UNIQUE COMMENT 'Email do resetowania hasła i powiadomień',
    password              VARCHAR(255) NOT NULL COMMENT 'bcrypt hash, NIE plaintext',
    first_name            VARCHAR(30)  NULL,
    last_name             VARCHAR(30)  NULL,
    role                  ENUM('admin','user','viewer') NOT NULL DEFAULT 'user',
    branch_id             INT          NULL COMMENT 'FK do branches, dodana po branches',
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE COMMENT 'Czy konto aktywne',
    must_change_password  BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Wymuszenie zmiany hasła przy logowaniu',
    password_reset_token  VARCHAR(255) NULL COMMENT 'Token do resetowania hasła (hash)',
    password_reset_expires DATETIME    NULL COMMENT 'Ważność tokena resetu',
    last_login            DATETIME     NULL COMMENT 'Ostatnie logowanie',
    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_login (login),
    INDEX idx_users_email (email)
) ENGINE=InnoDB COMMENT='Użytkownicy systemu (stara tabela: uzytkownik)';

-- 1.2 Oddziały
CREATE TABLE branches (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    address      VARCHAR(200) NULL,
    postal_code  VARCHAR(20)  NULL,
    city         VARCHAR(100) NULL,
    street       VARCHAR(100) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Oddziały firmy (stara tabela: oddzial)';

-- FK: users.branch_id → branches.id
ALTER TABLE users ADD CONSTRAINT fk_users_branch
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL;

-- 1.3 Kategorie artykułów (RAO-P1-017: hierarchia 3-poziomowa)
-- Drzewo: main → sub1 → sub2 → sub3 (poziom 'main' = root, parent_id = NULL)
CREATE TABLE categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    code        VARCHAR(40)  NULL COMMENT 'Kod kategorii np. KOP, DZW',
    description VARCHAR(400) NULL,
    parent_id   INT          NULL COMMENT 'RAO-P1-017: FK self-ref do categories.id (NULL dla level=main)',
    level       ENUM('main','sub1','sub2','sub3') NOT NULL DEFAULT 'main'
                COMMENT 'RAO-P1-017: poziom w hierarchii kategorii',
    CONSTRAINT fk_category_parent FOREIGN KEY (parent_id)
        REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_categories_name (name),
    INDEX idx_categories_parent (parent_id)
) ENGINE=InnoDB COMMENT='Kategorie maszyn/artykułów - hierarchia 3-poziomowa (stara tabela: kategoria)';

-- 1.4 Handlowcy
CREATE TABLE salespeople (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200)  NOT NULL,
    phone           VARCHAR(100)  NULL,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    commission_rate DECIMAL(5,2)  NULL DEFAULT 0 COMMENT 'Stawka prowizji (%)',
    INDEX idx_salespeople_active (is_active)
) ENGINE=InnoDB COMMENT='Handlowcy (stara tabela: handlowiec)';

-- 1.5 Typy stawek
CREATE TABLE rate_types (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(400) NOT NULL,
    description VARCHAR(800) NULL,
    is_dependent BOOLEAN     NULL DEFAULT FALSE COMMENT 'Czy stawka zależy od okresu'
) ENGINE=InnoDB COMMENT='Typy stawek rozliczeniowych (stara tabela: stawka)';

-- 1.6 Typy kosztów
CREATE TABLE cost_types (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(400) NULL,
    amount1     DECIMAL(18,2) NULL,
    amount2     DECIMAL(18,2) NULL
) ENGINE=InnoDB COMMENT='Typy kosztów dodatkowych (stara tabela: koszt_typ)';

-- 1.7 Firma (singleton - konfiguracja firmy)
CREATE TABLE company (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(200) NULL,
    name_short     VARCHAR(100) NULL,
    nip            VARCHAR(20)  NULL,
    regon          VARCHAR(20)  NULL,
    postal_code    VARCHAR(20)  NULL,
    city           VARCHAR(50)  NULL,
    street         VARCHAR(50)  NULL,
    header_text    TEXT         NULL COMMENT 'Nagłówek raportu (multiline)',
    bank_name      VARCHAR(200) NULL,
    bank_account   VARCHAR(40)  NULL,
    numbering_start INT         NULL DEFAULT 1 COMMENT 'Startowy numer dla auto-numeracji umów',
    increment_step DECIMAL(18,2) NULL DEFAULT 50.00 COMMENT 'Krok opłat +/- w konfiguracji',
    logo_path      VARCHAR(500) NULL COMMENT 'RAO-P3-002: URL do pliku logo (np. /rao/api/static/logos/company_logo.png)',
    -- RAO-TECH-002 (2026-07-11): Usunięto martwe kolumny: logo (LONGBLOB), report_folder, protocol_folder, app_version
    -- UWAGA: Szablony usług dodatkowych przeniesione do tabeli service_fee_templates
) ENGINE=InnoDB COMMENT='Dane firmy - singleton (stara tabela: firma)';

-- 1.7 Grupy szablonów usług dodatkowych (RAO-P1-011)
-- Pozwalają grupować zestawy usług (np. "Standard", "Premium", "Budowa")
CREATE TABLE fee_preset_groups (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT          NOT NULL DEFAULT 1,
    name         VARCHAR(200) NOT NULL COMMENT 'Nazwa grupy np. Standard, Premium',
    contract_type CHAR(1)     NOT NULL COMMENT 'S=najem, U=usługa',
    description  VARCHAR(400) NULL     COMMENT 'Opis grupy szablonów',
    sort_order   INT          NOT NULL DEFAULT 0 COMMENT 'Kolejność wyświetlania',
    is_default   BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Domyślna grupa dla tego typu',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_fpg_company FOREIGN KEY (company_id) REFERENCES company(id),
    INDEX idx_fpg_type (company_id, contract_type, sort_order)
) ENGINE=InnoDB COMMENT='Grupy szablonów usług dodatkowych (RAO-P1-011)';

-- 1.7b Seedowanie presetów Diesel/Elektryk (RAO-P1-100)
-- Startup migration w backend/main.py tworzy dwa zestawy:
-- - "Najem — Diesel": przegląd techniczny 150 zł (maszyny dieslowe)
-- - "Najem — Elektryk": przegląd techniczny 90 zł (maszyny elektryczne)
-- Idempotentne po nazwie — nie tworzy duplikatów przy każdym restarcie.

-- 1.8 Szablony usług dodatkowych (zastępuje firma.uslugi1/2 + firma.oplata_*)
-- Każdy wiersz = jedna pozycja z listy "-" np. "Transport: 400 zł"
-- RAO-P1-011: Zesłownikowanie z artykułami - article_id wskazuje na articles (zwykle usługa, is_service=1)
CREATE TABLE service_fee_templates (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT          NOT NULL DEFAULT 1,
    preset_id    INT          NULL     COMMENT 'Grupa szablonów (fee_preset_groups)',
    contract_type CHAR(1)     NOT NULL COMMENT 'S=najem, U=usługa',
    sort_order   INT          NOT NULL DEFAULT 0 COMMENT 'Kolejność wyświetlania',
    article_id   INT          NULL     COMMENT 'RAO-P1-011: FK do articles (usługi)',
    name         VARCHAR(200) NOT NULL COMMENT 'Nazwa np. Transport, Czyszczenie (snapshot z articles.name jeśli article_id ustawiony)',
    amount_from  DECIMAL(18,2) NULL    COMMENT 'Kwota od (NULL = brak)',
    amount_to    DECIMAL(18,2) NULL    COMMENT 'Kwota do (NULL = jednorazowa)',
    description  VARCHAR(400) NULL     COMMENT 'Opis np. dostawa / odbiór',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_sft_company FOREIGN KEY (company_id) REFERENCES company(id),
    CONSTRAINT fk_sft_preset FOREIGN KEY (preset_id) REFERENCES fee_preset_groups(id) ON DELETE CASCADE,
    CONSTRAINT fk_sft_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL,
    INDEX idx_sft_type (company_id, contract_type, sort_order),
    INDEX idx_sft_article (article_id)
) ENGINE=InnoDB COMMENT='Szablony usług dodatkowych (stare: firma.uslugi1/2, firma.oplata_*)';

-- 1.8b Kody pocztowe (RAO-P1-008, RAO-P2-015)
-- Słownik kodów pocztowych Polski do auto-uzupełniania miast
-- Źródło: GUS TERYT (200+ kodów z głównych miast dla developmentu)
CREATE TABLE postal_codes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    postal_code  VARCHAR(10)  NOT NULL UNIQUE COMMENT 'Kod pocztowy format XX-XXX',
    city         VARCHAR(100) NOT NULL COMMENT 'Nazwa miasta',
    wojewodztwo  VARCHAR(50)  NULL COMMENT 'Województwo',
    powiat       VARCHAR(100) NULL COMMENT 'Powiat',
    gmina        VARCHAR(100) NULL COMMENT 'Gmina',
    INDEX idx_postal_codes_code (postal_code),
    INDEX idx_postal_codes_city (city),
    INDEX idx_postal_codes_wojewodztwo (wojewodztwo),
    INDEX idx_postal_codes_gmina (gmina),
    INDEX idx_postal_codes_powiat (powiat),
    INDEX idx_postal_codes_city_gmina (city, gmina),
    INDEX idx_postal_codes_woj_pow (wojewodztwo, powiat)
) ENGINE=InnoDB COMMENT='Słownik kodów pocztowych Polski (RAO-P1-008, RAO-P2-015, RAO-P2-028: pełny Spis PNA Poczty Polskiej 21,904 kody)';

-- ============================================================
-- 2. KONTRAHENCI (Contractors)
-- ============================================================

CREATE TABLE contractors (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(400) NOT NULL,
    name_short       VARCHAR(200) NULL,
    nip              VARCHAR(20)  NULL,
    regon            VARCHAR(20)  NULL,
    pesel            VARCHAR(20)  NULL,
    postal_code      VARCHAR(20)  NULL,
    city             VARCHAR(50)  NULL,
    street           VARCHAR(50)  NULL,
    unit             VARCHAR(50)  NULL COMMENT 'Numer lokalu',
    notes            TEXT         NULL,
    is_supplier      BOOLEAN      NOT NULL DEFAULT FALSE,
    email            VARCHAR(100) NULL COMMENT 'Email firmy',
    contact_person1  VARCHAR(100) NULL COMMENT 'Imię i nazwisko osoby kontaktowej 1',
    phone1           VARCHAR(100) NULL COMMENT 'Telefon osoby kontaktowej 1',
    contact_person2  VARCHAR(100) NULL COMMENT 'Imię i nazwisko osoby kontaktowej 2',
    phone2           VARCHAR(100) NULL COMMENT 'Telefon osoby kontaktowej 2',
    landline_phone   VARCHAR(20)  NULL COMMENT 'Telefon stacjonarny firmy',
    website          VARCHAR(100) NULL,
    files_folder     VARCHAR(100) NULL COMMENT 'Ścieżka do folderu plików kontrahenta',
    gus_date         DATETIME     NULL COMMENT 'Data ostatniego pobrania z GUS',
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contractors_name (name),
    INDEX idx_contractors_nip (nip),
    INDEX idx_contractors_supplier (is_supplier)
) ENGINE=InnoDB COMMENT='Kontrahenci (stara tabela: kontrahent2)';

-- 2.1 Adresy kontrahentów
CREATE TABLE contractor_addresses (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id   INT          NOT NULL,
    name            VARCHAR(200) NULL COMMENT 'Nazwa adresu np. Siedziba, Magazyn',
    country_code    VARCHAR(3)   NULL DEFAULT 'PL',
    postal_code     VARCHAR(20)  NULL,
    city            VARCHAR(50)  NULL,
    street          VARCHAR(50)  NULL,
    notes           VARCHAR(200) NULL,
    contact_person  VARCHAR(100) NULL,
    phone           VARCHAR(20)  NULL,
    email           VARCHAR(100) NULL,
    is_default_delivery BOOLEAN  NOT NULL DEFAULT FALSE,
    is_headquarters     BOOLEAN  NOT NULL DEFAULT FALSE,
    latitude        DECIMAL(10,7) NULL,
    longitude       DECIMAL(10,7) NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_addr_contractor FOREIGN KEY (contractor_id)
        REFERENCES contractors(id) ON DELETE CASCADE,
    INDEX idx_addr_contractor (contractor_id)
) ENGINE=InnoDB COMMENT='Adresy kontrahentów (stara tabela: adres)';

-- ============================================================
-- 3.2 Artykuły (Maszyny/Usługi)
-- ============================================================

CREATE TABLE articles (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(200) NOT NULL,
    is_service        BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Czy to usługa (np. transport, mycie)',
    internal_number   VARCHAR(50)  NULL COMMENT 'Wewnętrzny numer maszyny w firmie',
    registration_no   VARCHAR(40)  NULL COMMENT 'Numer rejestracyjny',
    serial_no         VARCHAR(40)  NULL COMMENT 'Numer seryjny',
    brand             VARCHAR(100) NULL,
    model             VARCHAR(100) NULL COMMENT 'Model',
    replacement_value DECIMAL(18,2) NULL COMMENT 'Wartość odtworzeniowa',
    category_id       INT          NULL,
    owner_id          INT          NULL COMMENT 'FK do kontrahenta-właściciela (dostawcy)',
    branch_id         INT          NULL COMMENT 'FK do oddziału',
    description       VARCHAR(400) NULL,
    notes             VARCHAR(200) NULL,
    rental_days       INT          NULL COMMENT 'Ile dni wynajmu default',
    article_type      VARCHAR(20)  NULL COMMENT 'Rodzaj - typ artykułu',
    -- RAO-P1-017: kategoryzacja hierarchiczna (snapshot nazw + flaga archiwalna + atrybuty techniczne)
    category_main     VARCHAR(100) NULL COMMENT 'RAO-P1-017: Kategoria główna (snapshot nazwy z categories.name level=main)',
    category_sub1     VARCHAR(100) NULL COMMENT 'RAO-P1-017: Podkategoria 1 (snapshot)',
    category_sub2     VARCHAR(100) NULL COMMENT 'RAO-P1-017: Podkategoria 2 (snapshot)',
    category_sub3     VARCHAR(100) NULL COMMENT 'RAO-P1-017: Podkategoria 3 (snapshot)',
    is_archival       BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'RAO-P1-017: maszyna archiwalna (FALSE domyślnie, użytkownik oznaczy ręcznie w przyszłości)',
    technical_attributes JSON      NULL COMMENT 'RAO-P1-017: dynamiczne atrybuty techniczne (np. waga, moc) - LEGACY, zostawione dla kompatybilności',
    -- RAO: typ zasilania maszyny (VARCHAR dla elastyczności, wartości: 'diesel', 'electric', 'other')
    power_type        VARCHAR(10)  NOT NULL DEFAULT 'other' COMMENT 'Typ zasilania: diesel / electric / other',
    -- RAO: dedykowane kolumny numeryczne dla filtrów statystyk (zastępują string-values w technical_attributes JSON)
    zasieg_m          DECIMAL(8,2) NULL COMMENT 'Zasięg w metrach (filtr >=/<= w statystykach)',
    udzwig_t          DECIMAL(8,2) NULL COMMENT 'Udźwig w tonach (filtr >=/<= w statystykach)',
    dodatki           TEXT         NULL COMMENT 'Dodatkowe akcesoria / wyposażenie (było string w technical_attributes JSON)',
    fakturownia_product_id BIGINT  NULL COMMENT 'RAO-P2-012: ID produktu w Fakturownia (mapping globalny 1:N)',
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_art_category FOREIGN KEY (category_id)
        REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT fk_art_owner FOREIGN KEY (owner_id)
        REFERENCES contractors(id) ON DELETE SET NULL,
    CONSTRAINT fk_art_branch FOREIGN KEY (branch_id)
        REFERENCES branches(id) ON DELETE SET NULL,
    INDEX idx_art_name (name),
    INDEX idx_art_category (category_id),
    INDEX idx_art_owner (owner_id),
    INDEX idx_art_registration (registration_no),
    INDEX idx_articles_category_main (category_main),
    INDEX idx_articles_archival (is_archival),
    INDEX idx_articles_fakturownia_product (fakturownia_product_id),
    INDEX idx_articles_zasieg (zasieg_m),
    INDEX idx_articles_udzwig (udzwig_t)
) ENGINE=InnoDB COMMENT='Artykuły/maszyny (stara tabela: artykul3)';

-- ============================================================
-- 3.3 Integracja Fakturownia (RAO-P2-012) — singleton settings
-- ============================================================
-- Mapping produktu Fakturownia → artykuły RAO realizowany przez articles.fakturownia_product_id
-- (1:N globalny, jeden produkt FA może odpowiadać wielu artykułom RAO).
-- Token API szyfrowany Fernet (api_token_ciphertext VARBINARY).
-- Singleton: zawsze tylko jeden wiersz id=1 (analogicznie do company).

CREATE TABLE fakturownia_settings (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    enabled               BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Czy integracja włączona',
    api_token_ciphertext  VARBINARY(512) NULL COMMENT 'API token zaszyfrowany Fernet',
    api_token_preview     VARCHAR(32)  NULL COMMENT 'Preview tokena np. tk_****1234 (do UI)',
    domain_subdomain      VARCHAR(100) NULL COMMENT 'Subdomena Fakturownia np. toolsmart',
    api_token_updated_at  DATETIME     NULL COMMENT 'Kiedy zaktualizowano token',
    api_token_updated_by  INT          NULL COMMENT 'FK users.id - kto zaktualizował token',
    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_fakturownia_settings_user FOREIGN KEY (api_token_updated_by)
        REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
  COMMENT='RAO-P2-012: Singleton konfiguracji integracji Fakturownia';

-- ============================================================
-- 4. UMOWY (Contracts)
-- ============================================================

CREATE TABLE contracts (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id       INT          NOT NULL,
    branch_id           INT          NULL COMMENT 'Oddział (uproszczone z M:N umowa_oddzial)',
    salesperson_id      INT          NULL,
    number              VARCHAR(40)  NOT NULL COMMENT 'Numer umowy np. S001/2026',
    auto_number         INT          NULL COMMENT 'Auto-numer do sortowania',
    contract_type       CHAR(1)      NOT NULL DEFAULT 'S' COMMENT 'S=najem, U=usługa',
    delivery_address    TEXT         NULL COMMENT 'Snapshot adresu dostawy',
    postal_code         VARCHAR(20)  NULL COMMENT 'RAO-P1-008: Kod pocztowy z adresu dostawy',
    city                VARCHAR(100) NULL COMMENT 'RAO-P1-008: Miasto z adresu dostawy',
    postal_code_id      INT          NULL COMMENT 'RAO-P2-028: FK do postal_codes (deterministyczna lokalizacja PNA)',
    date_from           DATE         NULL,
    date_to             DATE         NULL,
    prepayment_amount   DECIMAL(18,2) NULL DEFAULT 0.00,
    prepayment_document VARCHAR(200) NULL,
    -- RAO-P1-103: invoice_amount + invoice_document usunięte (kwoty faktur z Fakturowni)
    notes               TEXT         NULL,
    -- UWAGA: Usługi dodatkowe w tabeli contract_service_fees (relacyjnie)
    -- Osoby kontaktowe (snapshot z momentu umowy) - tekst w PDF: "reprezentowany przez" i "osoba kontaktowa"
    contact_person1     VARCHAR(100) NULL COMMENT 'Reprezentowany przez (imię i nazwisko)',
    contact_phone1      VARCHAR(100) NULL COMMENT 'Telefon osoby reprezentującej',
    show_person1        BOOLEAN      NOT NULL DEFAULT TRUE COMMENT 'Pokaż osobę reprezentującą w PDF',
    contact_person2     VARCHAR(100) NULL COMMENT 'Osoba kontaktowa (imię i nazwisko)',
    contact_phone2      VARCHAR(100) NULL COMMENT 'Telefon osoby kontaktowej',
    show_person2        BOOLEAN      NOT NULL DEFAULT TRUE COMMENT 'Pokaż osobę kontaktową w PDF',
    email               VARCHAR(100) NULL COMMENT 'Email firmy',
    phone               VARCHAR(40)  NULL COMMENT 'Telefon stacjonarny firmy',
    -- Kontrahent snapshot
    contractor_name     VARCHAR(200) NULL COMMENT 'Snapshot nazwy kontrahenta',
    -- Wydruk
    print_path          VARCHAR(100) NULL,
    print_date          DATETIME     NULL,
    report_without_data BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'PZ bez danych',
    hide_delivery_address BOOLEAN    NOT NULL DEFAULT FALSE COMMENT 'Ukryj adres dostawy na umowie',
    signatures_on_page1 BOOLEAN      NOT NULL DEFAULT FALSE COMMENT 'Podpisy wymagane na stronie 1',
    -- Dni robocze
    working_days_per_week INT       NULL DEFAULT 6,
    position_count      INT          NULL DEFAULT 0,
    -- RAO-P2-022: status rozliczenia
    is_settled          TINYINT(1)   NOT NULL DEFAULT 0 COMMENT 'Umowa rozliczona (manualne oznaczenie)',
    settled_at          DATETIME     NULL COMMENT 'Kiedy oznaczono jako rozliczona',
    -- Timestamps
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_contract_contractor FOREIGN KEY (contractor_id)
        REFERENCES contractors(id),
    CONSTRAINT fk_contract_branch FOREIGN KEY (branch_id)
        REFERENCES branches(id) ON DELETE SET NULL,
    CONSTRAINT fk_contract_sales FOREIGN KEY (salesperson_id)
        REFERENCES salespeople(id) ON DELETE SET NULL,
    INDEX idx_contract_number (number),
    INDEX idx_contract_contractor (contractor_id),
    INDEX idx_contract_dates (date_from, date_to),
    INDEX idx_contract_type (contract_type),
    INDEX idx_contracts_postal_code (postal_code),
    INDEX idx_contracts_city (city)
) ENGINE=InnoDB COMMENT='Umowy (stara tabela: umowa2)';

-- 4.1 Dostawa (geo-location per umowa)
-- RAO-P3-005: zlecenia dostawy / odbioru w ramach umowy
CREATE TABLE deliveries (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contract_id     INT NOT NULL,
    position_id     INT NULL COMMENT 'FK do contract_positions (opcjonalnie konkretna pozycja)',
    delivery_type   ENUM('deliver','collect') NOT NULL DEFAULT 'deliver'
                    COMMENT 'deliver = dostawa do klienta, collect = odbiór od klienta',
    scheduled_date  DATE NULL COMMENT 'Planowana data',
    actual_date     DATE NULL COMMENT 'Faktyczna data realizacji',
    address         VARCHAR(500) NULL COMMENT 'Adres dostawy/odbioru',
    driver          VARCHAR(200) NULL COMMENT 'Kierowca / wykonawca',
    note            VARCHAR(500) NULL,
    status          ENUM('pending','done','cancelled') NOT NULL DEFAULT 'pending',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_delivery_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_delivery_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE SET NULL,
    INDEX idx_deliveries_contract (contract_id),
    INDEX idx_deliveries_position (position_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
  COMMENT='RAO-P3-005: Zlecenia dostaw/odbiorów per umowa';

-- 4.2 Adresy dostawy (reverse geocoding results)
CREATE TABLE delivery_addresses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    contract_id  INT          NOT NULL,
    name         VARCHAR(400) NULL,
    street       VARCHAR(200) NULL,
    number       VARCHAR(100) NULL,
    postal_code  VARCHAR(20)  NULL,
    hamlet       VARCHAR(200) NULL,
    city         VARCHAR(200) NULL,
    town         VARCHAR(200) NULL,
    village      VARCHAR(200) NULL,
    county       VARCHAR(100) NULL COMMENT 'Powiat',
    municipality VARCHAR(100) NULL COMMENT 'Gmina',
    province     VARCHAR(100) NULL COMMENT 'Województwo',
    district     VARCHAR(200) NULL COMMENT 'Dzielnica',
    neighbourhood VARCHAR(200) NULL COMMENT 'Osiedle',
    CONSTRAINT fk_deladdr_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Adresy dostawy z reverse geocoding (stara tabela: adres_dostawy)';

-- ============================================================
-- 5. POZYCJE UMOWY (Contract Positions)
-- ============================================================

CREATE TABLE contract_positions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contract_id     INT          NOT NULL,
    article_id      INT          NOT NULL,
    description     VARCHAR(400) NULL,
    rental_days     INT          NULL,
    quantity        INT          NULL DEFAULT 1,
    unit_price      DECIMAL(18,2) NULL,
    rate_type_id    INT          NULL,
    billing_frequency VARCHAR(20) NULL COMMENT 'tygodniowo/dziennie/godzinowo/miesięcznie/jednorazowo',
    billing_unit    VARCHAR(20)  NULL COMMENT 'tydzień/doba/godzina/miesiąc/sztuka',
    supplier_id     INT          NULL COMMENT 'FK do kontrahenta-dostawcy',
    delivery_date   DATE         NULL,
    article_name    VARCHAR(400) NULL COMMENT 'Snapshot nazwy artykułu',
    CONSTRAINT fk_pos_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_pos_article FOREIGN KEY (article_id)
        REFERENCES articles(id),
    CONSTRAINT fk_pos_rate_type FOREIGN KEY (rate_type_id)
        REFERENCES rate_types(id) ON DELETE SET NULL,
    CONSTRAINT fk_pos_supplier FOREIGN KEY (supplier_id)
        REFERENCES contractors(id) ON DELETE SET NULL,
    INDEX idx_pos_contract (contract_id),
    INDEX idx_pos_article (article_id)
) ENGINE=InnoDB COMMENT='Pozycje umowy (stara tabela: umowa_pozycja3)';

-- 5.1 Warunki rozliczenia per pozycja
CREATE TABLE position_conditions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    position_id     INT          NOT NULL,
    rate1           DECIMAL(18,2) NULL COMMENT 'Opłata 1 (podstawowa)',
    rate2           DECIMAL(18,2) NULL COMMENT 'Opłata 2 (dodatkowa/zmienna)',
    billing_label   VARCHAR(20)  NULL COMMENT 'Nazwa rozliczenia: tygodniowo/dziennie/etc',
    period_count    INT          NULL COMMENT 'RAO-P1-005: backward compatibility',
    period_from     INT          NULL COMMENT 'RAO-P1-005: elastyczne widełki (od)',
    period_to       INT          NULL COMMENT 'RAO-P1-005: elastyczne widełki (do)',
    minimum         INT          NULL COMMENT 'Minimalna liczba okresów',
    CONSTRAINT fk_cond_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    INDEX idx_cond_position (position_id)
) ENGINE=InnoDB COMMENT='Warunki rozliczenia (stara tabela: umowa_pozycja2_warunek)';

-- ============================================================
-- 6. KOSZTY (Costs)
-- ============================================================

CREATE TABLE costs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    cost_type_id INT         NULL,
    position_id  INT         NULL COMMENT 'FK do contract_positions',
    description  VARCHAR(400) NULL,
    amount       DECIMAL(18,2) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cost_type FOREIGN KEY (cost_type_id)
        REFERENCES cost_types(id) ON DELETE SET NULL,
    CONSTRAINT fk_cost_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    INDEX idx_cost_position (position_id)
) ENGINE=InnoDB COMMENT='Koszty (stara tabela: koszty)';

-- RAO-P3-005: koszty dodatkowe per umowa (transport, paliwo, naprawy itd.)
CREATE TABLE contract_costs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    contract_id  INT          NOT NULL,
    position_id  INT          NULL COMMENT 'Opcjonalnie konkretna pozycja umowy',
    cost_type    VARCHAR(100) NOT NULL COMMENT 'Typ kosztu (transport/paliwo/naprawa/...)',
    amount       DECIMAL(10,2) NOT NULL,
    description  VARCHAR(500) NULL,
    cost_date    DATE         NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ccost_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_ccost_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE SET NULL,
    INDEX idx_ccost_contract (contract_id),
    INDEX idx_ccost_position (position_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
  COMMENT='RAO-P3-005: Koszty dodatkowe umowy (księgowanie operacyjne)';

-- ============================================================
-- 7. ROZLICZENIA UMÓW (Contract Settlements) - RAO-P1-012
-- ============================================================

CREATE TABLE contract_settlements (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contract_id     INT          NOT NULL COMMENT 'ID umowy',
    position_id     INT          NULL COMMENT 'ID pozycji umowy (maszyna/usługa); NULL = unmapped settlement (opcja E)',
    service_fee_id  INT          NULL COMMENT 'RAO-P2-012: ID usługi dodatkowej (contract_service_fees); NULL = unmapped',
    cost_client     DECIMAL(18,2) NULL COMMENT 'Koszt dla klienta (na fakturze)',
    cost_company    DECIMAL(18,2) NULL COMMENT 'Koszt dla firmy (narzut/marża)',
    notes           TEXT         NULL COMMENT 'Uwagi do rozliczenia',
    settled_at      DATE         NULL COMMENT 'RAO-P2-032: Data rozliczenia (legacy rozliczenie.data lub import Fakturownia)',
    source          VARCHAR(20)  NULL DEFAULT 'manual' COMMENT 'RAO-P2-032: legacy/fakturownia/manual/fa_unmapped',
    -- RAO Faza 2a (opcja E): unmapped settlements z Fakturownia — pozycje FA nieobecne w umowie
    article_name_snapshot     VARCHAR(255) NULL COMMENT 'Snapshot nazwy pozycji z FA (gdy position_id=NULL)',
    fakturownia_product_id    BIGINT       NULL COMMENT 'ID produktu FA (grupowanie w analytics, identyfikacja duplikatów)',
    fakturownia_invoice_number VARCHAR(50) NULL COMMENT 'Numer faktury FA (wydzielony z notes dla query)',
    -- Generated column: idempotentność importu unmapped (NULL dla mapped → nie blokuje UNIQUE)
    unmapped_key    VARCHAR(100) GENERATED ALWAYS AS (
        CASE WHEN position_id IS NULL AND service_fee_id IS NULL
             THEN CONCAT('unmapped:', IFNULL(fakturownia_product_id,0), ':', IFNULL(fakturownia_invoice_number,''))
             ELSE NULL END
    ) STORED COMMENT 'Klucz deduplikacji unmapped settlements (NULL dla mapped)',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settlement_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_settlement_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    CONSTRAINT fk_settlement_service_fee FOREIGN KEY (service_fee_id)
        REFERENCES contract_service_fees(id) ON DELETE CASCADE,
    INDEX idx_settlement_contract (contract_id),
    INDEX idx_settlement_position (position_id),
    INDEX idx_settlement_service_fee (service_fee_id),
    INDEX idx_settlements_source (source),
    INDEX idx_settlements_settled_at (settled_at),
    -- RAO-P2-032: idempotentny import rozliczenie — UNIQUE zapobiega duplikatom mapped settlements
    UNIQUE INDEX uq_settlements_contract_pos_fee_date (contract_id, position_id, service_fee_id, settled_at),
    -- RAO Faza 2a: idempotentność unmapped — NULL w UNIQUE dozwolony wielokrotnie (mapped nie koliduje)
    UNIQUE INDEX uq_settlements_unmapped_key (unmapped_key)
) ENGINE=InnoDB COMMENT='Rozliczenia umów - koszty klient vs firma (RAO-P1-012, RAO-P2-012, RAO-P2-032, Faza 2a opcja E)';

-- ============================================================
-- 8. USŁUGI DODATKOWE UMOWY (Contract Service Fees)
-- ============================================================
-- Każdy wiersz = jedna pozycja z listy opłat przypisana do konkretnej umowy
-- Kopiowane z service_fee_templates przy tworzeniu umowy, edytowalne per-umowa

CREATE TABLE contract_service_fees (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    contract_id  INT          NOT NULL,
    sort_order   INT          NOT NULL DEFAULT 0 COMMENT 'Kolejność pozycji',
    name         VARCHAR(200) NOT NULL COMMENT 'Nazwa np. Transport',
    amount_from  DECIMAL(18,2) NULL    COMMENT 'Kwota od',
    amount_to    DECIMAL(18,2) NULL    COMMENT 'Kwota do (NULL = jednorazowa)',
    description  VARCHAR(400) NULL     COMMENT 'Opis np. dostawa / odbiór',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE COMMENT 'Pokazuje na PDF',
    CONSTRAINT fk_csf_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    INDEX idx_csf_contract (contract_id, sort_order)
) ENGINE=InnoDB COMMENT='Usługi dodatkowe umowy (stary: umowa2.oplaty, firma.uslugi1/2)';

-- ============================================================
-- 9. AUDIT LOG
-- ============================================================

-- RAO-P3-005: rozszerzony audit_log z JSON snapshot zmian
CREATE TABLE audit_log (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT          NULL COMMENT 'FK users.id - kto wykonał akcję',
    action       VARCHAR(100) NOT NULL COMMENT 'np. create / update / delete / login',
    entity_type  VARCHAR(100) NOT NULL COMMENT 'np. contract / contractor / article',
    entity_id    INT          NULL COMMENT 'ID rekordu którego dotyczy akcja',
    old_data     JSON         NULL COMMENT 'Snapshot przed zmianą',
    new_data     JSON         NULL COMMENT 'Snapshot po zmianie',
    ip_address   VARCHAR(45)  NULL COMMENT 'IPv4/IPv6 klienta',
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_entity (entity_type, entity_id),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
  COMMENT='RAO-P3-005: Dziennik zmian (kto, co, kiedy, JSON diff)';

-- ============================================================
-- 10. REZERWACJE ARTYKUŁÓW (RAO-P1-015 / RAO-L-Phase1)
-- ============================================================

-- Rezerwacja maszyny (article) na okres [reserved_from, reserved_to].
-- Może być dla kontrahenta (contractor_id) lub bez (NULL = blokada wewnętrzna).
-- status: confirmed = potwierdzona (domyślne), provisional = wstępna/proponowana.
CREATE TABLE article_reservations (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    article_id    INT          NOT NULL COMMENT 'FK articles.id — rezerwowana maszyna',
    contractor_id INT          NULL     COMMENT 'RAO-L-Phase1: FK contractors.id (NULL = blokada wewnętrzna)',
    reserved_from DATE         NOT NULL COMMENT 'Początek okresu rezerwacji (włącznie)',
    reserved_to   DATE         NOT NULL COMMENT 'Koniec okresu rezerwacji (włącznie)',
    status        ENUM('confirmed','provisional') NOT NULL DEFAULT 'confirmed'
                  COMMENT 'RAO-L-Phase1: status rezerwacji',
    note          VARCHAR(300) NULL     COMMENT 'Notatka/opis rezerwacji',
    created_by    INT          NULL     COMMENT 'FK users.id — kto utworzył rezerwację',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_article_reservations_article FOREIGN KEY (article_id)
        REFERENCES articles(id) ON DELETE CASCADE,
    CONSTRAINT fk_article_reservations_contractor FOREIGN KEY (contractor_id)
        REFERENCES contractors(id) ON DELETE SET NULL,
    CONSTRAINT fk_article_reservations_created_by FOREIGN KEY (created_by)
        REFERENCES users(id) ON DELETE SET NULL,
    INDEX ix_article_reservations_article_id (article_id),
    INDEX idx_article_reservations_contractor (contractor_id),
    INDEX idx_article_reservations_reserved_from (reserved_from),
    INDEX idx_article_reservations_reserved_to (reserved_to)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
  COMMENT='RAO-P1-015: Rezerwacje maszyn na okres (kalendarz dostępności)';
```

## Tabele archiwum (archive_*) — RAO-P2-062 Faza 0

> **Decyzja użytkownika (2026-07-01):** Legacy dane (742 umów `is_legacy=1` + powiązane)
> zostały przeniesione do tabel `archive_*` w tej samej bazie `rao_new`.
> Kontrahenci (`contractors`), `users`, `branches`, `salespeople`, `rate_types`,
> `postal_codes` są **współdzielone** między archiwum a nową aplikacją.
> `articles` i `categories` są **osobne** — `archive_*` = frozen snapshot z migracji.
>
> **Migracja wykonana:** `backend/migrate_to_archive.py` (idempotentny, INSERT IGNORE).
> **Backup:** `backup_pre_archive_split.sql` (przed migracją).
> **Archiwum = read-only Z WYJĄTKKIEM** edycji kategorii (`archive_categories` CRUD +
> `PATCH archive_articles.category_id`) — implementacja w Fazie 1 (backend).
>
> **FK w archive_*:**
> - `archive_contracts.contractor_id` → `contractors.id` (współdzielone)
> - `archive_contracts.branch_id` → `branches.id` (współdzielone, ON DELETE SET NULL)
> - `archive_contracts.salesperson_id` → `salespeople.id` (współdzielone, ON DELETE SET NULL)
> - `archive_contracts.postal_code_id` → `postal_codes.id` (współdzielone, ON DELETE SET NULL)
> - `archive_articles.category_id` → `archive_categories.id` (archive FK, edytowalne)
> - `archive_articles.owner_id` → `contractors.id` (współdzielone)
> - `archive_articles.branch_id` → `branches.id` (współdzielone)
> - `archive_contract_positions.contract_id` → `archive_contracts.id` (CASCADE)
> - `archive_contract_positions.article_id` → `archive_articles.id`
> - `archive_contract_positions.rate_type_id` → `rate_types.id` (współdzielone, SET NULL)
> - `archive_contract_positions.supplier_id` → `contractors.id` (współdzielone, SET NULL)
> - `archive_position_conditions.position_id` → `archive_contract_positions.id` (CASCADE)
> - `archive_position_conditions.rate_type_id` → `rate_types.id` (SET NULL)
> - `archive_contract_service_fees.contract_id` → `archive_contracts.id` (CASCADE)
> - `archive_contract_service_fees.article_id` — **brak FK** (service article może
>   nie być w `archive_articles`, bo kopiujemy tylko maszyny z legacy pozycji;
>   kolumna z indeksem, wartość pozostaje jako referencja historyczna)
> - `archive_contract_settlements.contract_id` → `archive_contracts.id` (CASCADE)
> - `archive_contract_settlements.position_id` → `archive_contract_positions.id` (CASCADE)
> - `archive_contract_settlements.service_fee_id` → `archive_contract_service_fees.id` (CASCADE)

```sql
-- ============================================================
-- ARCHIVE_* — frozen snapshot legacy (RAO-P2-062 Faza 0)
-- Kolejność: categories → articles → contracts → positions →
--            conditions → service_fees → settlements
-- ============================================================

-- archive_categories — mirror categories (self-ref FK)
CREATE TABLE IF NOT EXISTS archive_categories (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(200) NOT NULL,
  code        VARCHAR(40)  NULL,
  description VARCHAR(400) NULL,
  parent_id   INT NULL,
  level       ENUM('main','sub1','sub2','sub3') NOT NULL DEFAULT 'main',
  CONSTRAINT fk_archive_categories_parent_id
    FOREIGN KEY (parent_id) REFERENCES archive_categories(id) ON DELETE SET NULL,
  INDEX idx_archive_categories_name (name),
  INDEX idx_archive_categories_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_articles — mirror articles, category_id → archive_categories.id
CREATE TABLE IF NOT EXISTS archive_articles (
  id                    INT AUTO_INCREMENT PRIMARY KEY,
  name                  VARCHAR(200) NOT NULL,
  is_service            TINYINT(1) NOT NULL,
  internal_number       VARCHAR(50)  NULL,
  registration_no       VARCHAR(40)  NULL,
  serial_no             VARCHAR(40)  NULL,
  brand                 VARCHAR(100) NULL,
  model                 VARCHAR(100) NULL,
  replacement_value     DECIMAL(18,2) NULL,
  category_id           INT NULL,
  owner_id              INT NULL,
  branch_id             INT NULL,
  description           VARCHAR(400) NULL,
  notes                 VARCHAR(200) NULL,
  rental_days           INT NULL,
  article_type          VARCHAR(20)  NULL,
  category_main         VARCHAR(100) NULL,
  category_sub1         VARCHAR(100) NULL,
  category_sub2         VARCHAR(100) NULL,
  category_sub3         VARCHAR(100) NULL,
  is_archival           TINYINT(1) NOT NULL DEFAULT 0,
  is_external           TINYINT(1) NOT NULL DEFAULT 0,
  technical_attributes  LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NULL
    CHECK (json_valid(technical_attributes)),
  zasieg_m              DECIMAL(8,2) NULL COMMENT 'Zasięg w metrach',
  udzwig_t              DECIMAL(8,2) NULL COMMENT 'Udźwig w tonach',
  dodatki               TEXT NULL COMMENT 'Dodatkowe akcesoria / wyposażenie',
  fakturownia_product_id BIGINT NULL COMMENT 'ID produktu w Fakturownia (mapping 1:N)',
  fakturownia_tax_rate  VARCHAR(10) NULL COMMENT 'Stawka VAT z Fakturownia (snapshot)',
  fakturownia_gtu_code  VARCHAR(20) NULL COMMENT 'Kod GTU z Fakturownia (snapshot)',
  fakturownia_pkwiu     VARCHAR(50) NULL COMMENT 'PKWiU z Fakturownia (snapshot)',
  created_at            DATETIME NOT NULL,
  updated_at            DATETIME NULL,
  CONSTRAINT fk_archive_articles_branch_id
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL,
  CONSTRAINT fk_archive_articles_category_id
    FOREIGN KEY (category_id) REFERENCES archive_categories(id) ON DELETE SET NULL,
  CONSTRAINT fk_archive_articles_owner_id
    FOREIGN KEY (owner_id) REFERENCES contractors(id) ON DELETE SET NULL,
  INDEX idx_archive_art_name (name),
  INDEX idx_archive_art_category (category_id),
  INDEX idx_archive_art_owner (owner_id),
  INDEX idx_archive_art_registration (registration_no),
  INDEX idx_archive_articles_category_main (category_main),
  INDEX idx_archive_articles_archival (is_archival),
  INDEX idx_archive_articles_fakturownia_product (fakturownia_product_id),
  INDEX idx_archive_articles_zasieg (zasieg_m),
  INDEX idx_archive_articles_udzwig (udzwig_t),
  INDEX idx_archive_articles_external (is_external)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_contracts — mirror contracts BEZ is_legacy
CREATE TABLE IF NOT EXISTS archive_contracts (
  id                    INT AUTO_INCREMENT PRIMARY KEY,
  contractor_id         INT NOT NULL,
  branch_id             INT NULL,
  salesperson_id        INT NULL,
  number                VARCHAR(40) NOT NULL,
  oid                   VARCHAR(40) NULL COMMENT 'Numer zamówienia w Fakturownia',
  auto_number           INT NULL,
  contract_type         VARCHAR(1) NOT NULL,
  delivery_address      TEXT NULL,
  postal_code           VARCHAR(20)  NULL,
  city                  VARCHAR(100) NULL,
  postal_code_id        INT NULL COMMENT 'FK do postal_codes',
  latitude              DECIMAL(10,8) NULL,
  longitude             DECIMAL(11,8) NULL,
  date_from             DATE NULL,
  date_to               DATE NULL,
  prepayment_amount     DECIMAL(18,2) NULL,
  prepayment_document   VARCHAR(200) NULL,
  -- RAO-P1-103: invoice_amount + invoice_document usunięte
  notes                 TEXT NULL,
  contact_person1       VARCHAR(100) NULL,
  contact_phone1        VARCHAR(100) NULL,
  show_person1          TINYINT(1) NOT NULL,
  contact_person2       VARCHAR(100) NULL,
  contact_phone2        VARCHAR(100) NULL,
  show_person2          TINYINT(1) NOT NULL,
  email                 VARCHAR(100) NULL,
  phone                 VARCHAR(40)  NULL,
  contractor_name       VARCHAR(200) NULL,
  print_path            VARCHAR(100) NULL,
  print_date            DATETIME NULL,
  report_without_data   TINYINT(1) NOT NULL,
  hide_delivery_address TINYINT(1) NOT NULL,
  signatures_on_page1   TINYINT(1) NOT NULL,
  working_days_per_week INT NULL,
  position_count        INT NULL,
  is_settled            TINYINT(1) NOT NULL,
  settled_at            DATETIME NULL,
  created_at            DATETIME NOT NULL,
  updated_at            DATETIME NULL,
  UNIQUE KEY uq_archive_contracts_number (number),
  CONSTRAINT fk_archive_contracts_branch_id
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL,
  CONSTRAINT fk_archive_contracts_contractor_id
    FOREIGN KEY (contractor_id) REFERENCES contractors(id),
  CONSTRAINT fk_archive_contracts_postal_code_id
    FOREIGN KEY (postal_code_id) REFERENCES postal_codes(id) ON DELETE SET NULL,
  CONSTRAINT fk_archive_contracts_salesperson_id
    FOREIGN KEY (salesperson_id) REFERENCES salespeople(id) ON DELETE SET NULL,
  INDEX fk_archive_contracts_contractor_id (contractor_id),
  INDEX fk_archive_contracts_branch_id (branch_id),
  INDEX idx_archive_contracts_postal_code_id (postal_code_id),
  INDEX idx_archive_contracts_is_settled (is_settled),
  INDEX idx_archive_contracts_created_at (created_at),
  INDEX idx_archive_contracts_salesperson_id (salesperson_id),
  INDEX idx_archive_contracts_print_date (print_date),
  INDEX idx_archive_contracts_delivery_date (date_to),
  INDEX idx_archive_contracts_postal_code (postal_code),
  INDEX idx_archive_contracts_city (city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_contract_positions — contract_id → archive_contracts, article_id → archive_articles
CREATE TABLE IF NOT EXISTS archive_contract_positions (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  contract_id       INT NOT NULL,
  article_id        INT NOT NULL,
  description       VARCHAR(400) NULL,
  rental_days       INT NULL,
  quantity          INT NULL,
  unit_price        DECIMAL(18,2) NULL,
  costs             DECIMAL(18,2) NULL,
  rate_type_id      INT NULL,
  billing_frequency VARCHAR(20)  NULL,
  billing_unit      VARCHAR(20)  NULL,
  supplier_id       INT NULL,
  delivery_date     DATE NULL,
  article_name      VARCHAR(400) NULL,
  CONSTRAINT fk_archive_cp_contract_id
    FOREIGN KEY (contract_id) REFERENCES archive_contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_archive_cp_article_id
    FOREIGN KEY (article_id) REFERENCES archive_articles(id),
  CONSTRAINT fk_archive_cp_rate_type_id
    FOREIGN KEY (rate_type_id) REFERENCES rate_types(id) ON DELETE SET NULL,
  CONSTRAINT fk_archive_cp_supplier_id
    FOREIGN KEY (supplier_id) REFERENCES contractors(id) ON DELETE SET NULL,
  INDEX fk_archive_cp_contract_id (contract_id),
  INDEX fk_archive_cp_article_id (article_id),
  INDEX fk_archive_cp_rate_type_id (rate_type_id),
  INDEX fk_archive_cp_supplier_id (supplier_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_position_conditions — position_id → archive_contract_positions
CREATE TABLE IF NOT EXISTS archive_position_conditions (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  position_id   INT NOT NULL,
  rate_type_id  INT NULL,
  description   VARCHAR(400) NULL,
  rate1         DECIMAL(18,2) NULL,
  rate2         DECIMAL(18,2) NULL,
  billing_label VARCHAR(20)  NULL,
  period_count  INT NULL,
  period_from   INT NULL COMMENT 'RAO-P1-005: elastyczne widełki (od)',
  period_to     INT NULL COMMENT 'RAO-P1-005: elastyczne widełki (do)',
  is_flat_rate  TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'P1-101: ryczałt=TRUE (kwota całkowita), stawka=FALSE (per jednostka)',
  minimum       INT NULL,
  CONSTRAINT fk_archive_pc_position_id
    FOREIGN KEY (position_id) REFERENCES archive_contract_positions(id) ON DELETE CASCADE,
  CONSTRAINT fk_archive_pc_rate_type_id
    FOREIGN KEY (rate_type_id) REFERENCES rate_types(id) ON DELETE SET NULL,
  INDEX fk_archive_pc_position_id (position_id),
  INDEX fk_archive_pc_rate_type_id (rate_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_contract_service_fees — contract_id → archive_contracts
-- article_id: brak FK (service article może nie być w archive_articles)
CREATE TABLE IF NOT EXISTS archive_contract_service_fees (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  contract_id    INT NOT NULL,
  sort_order     INT NOT NULL,
  name           VARCHAR(200) NOT NULL,
  amount_from    DECIMAL(18,2) NULL,
  amount_to      DECIMAL(18,2) NULL,
  description    VARCHAR(400) NULL,
  is_active      TINYINT(1) NOT NULL,
  article_id     INT NULL,
  default_price  DECIMAL(18,2) NULL,
  CONSTRAINT fk_archive_csf_contract_id
    FOREIGN KEY (contract_id) REFERENCES archive_contracts(id) ON DELETE CASCADE,
  INDEX fk_archive_csf_contract_id (contract_id),
  INDEX idx_archive_csf_article_id (article_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;

-- archive_contract_settlements — contract/position/service_fee → archive_*
CREATE TABLE IF NOT EXISTS archive_contract_settlements (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  contract_id    INT NOT NULL,
  position_id    INT NULL,
  service_fee_id INT NULL,
  cost_client    DECIMAL(18,2) NULL,
  cost_company   DECIMAL(18,2) NULL,
  notes          TEXT NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
  settled_at     DATE NULL COMMENT 'Data rozliczenia',
  source         VARCHAR(20) DEFAULT 'manual' COMMENT 'legacy/fakturownia/manual',
  article_name_snapshot VARCHAR(255) NULL COMMENT 'Snapshot nazwy pozycji z FA (gdy position_id=NULL)',
  fakturownia_product_id BIGINT NULL COMMENT 'ID produktu FA (grupowanie w analytics, identyfikacja duplikatów)',
  fakturownia_invoice_number VARCHAR(50) NULL COMMENT 'Numer faktury FA (wydzielony z notes dla query)',
  UNIQUE KEY uq_archive_settlements_contract_pos_fee_date
    (contract_id, position_id, service_fee_id, settled_at),
  CONSTRAINT fk_archive_cs_contract_id
    FOREIGN KEY (contract_id) REFERENCES archive_contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_archive_cs_position_id
    FOREIGN KEY (position_id) REFERENCES archive_contract_positions(id) ON DELETE CASCADE,
  CONSTRAINT fk_archive_cs_service_fee_id
    FOREIGN KEY (service_fee_id) REFERENCES archive_contract_service_fees(id) ON DELETE CASCADE,
  INDEX fk_archive_cs_position_id (position_id),
  INDEX fk_archive_cs_service_fee_id (service_fee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci;
```

**Stan po migracji (2026-07-01, weryfikacja DB):**

| Tabela oryginalna | COUNT po | Tabela archive | COUNT po |
|-------------------|----------|----------------|----------|
| `contracts` | 0 | `archive_contracts` | 742 |
| `contract_positions` | 3 (orphans, pre-existing) | `archive_contract_positions` | 878 |
| `position_conditions` | 0 | `archive_position_conditions` | 1274 |
| `contract_service_fees` | 0 | `archive_contract_service_fees` | 3396 |
| `contract_settlements` | 0 | `archive_contract_settlements` | 1945 |
| `categories` | 64 (nietknięte) | `archive_categories` | 64 |
| `articles` | 419 (nietknięte) | `archive_articles` | 351 |
| `contractors` | 662 (współdzielone) | — | — |

> **Uwaga:** 3 osierocone pozycje (contract_id=9204 nie istnieje w `contracts`)
> to pre-existing data issue z pierwszej migracji (`migrate.py`) — nie są legacy,
> nie zostały zmigrowane do archive ani usunięte. Kolumna `is_legacy` w `contracts`
> zostaje (usunięcie w Fazie 1 razem z modelem SQLAlchemy).

## Mapowanie starych tabel → nowe

| Stara tabela | Nowa tabela | Uwagi |
|-------------|-------------|-------|
| `uzytkownik` | `users` | Dodano role, bcrypt hash |
| `oddzial` | `branches` | Bez zmian strukturalnych |
| `kategoria` | `categories` | Bez zmian |
| `handlowiec` | `salespeople` | `AKTYWNY` → `is_active` BOOLEAN |
| `stawka` | `rate_types` | `ZALEZNA` → `is_dependent` |
| `koszt_typ` | `cost_types` | Bez zmian |
| `firma` | `company` + `service_fee_templates` | `uslugi1/2` i `oplata_*` → wiersze w `service_fee_templates` |
| `firma.uslugi1` + `umowa2.oplaty` (najem) | `service_fee_templates` (S) + `contract_service_fees` | Tekst rozdzielony na relacyjne wiersze |
| `firma.uslugi2` + `umowa2.oplaty` (usługi) | `service_fee_templates` (U) + `contract_service_fees` | Tekst rozdzielony na relacyjne wiersze |
| `kontrahent2` | `contractors` | Połączono 2 osoby kontaktowe, dodano timestamps |
| `adres` | `contractor_addresses` | Dodano FK constraint, precision lat/lng |
| `artykul3` | `articles` | `USLUGA` → `is_service` BOOLEAN, FK constraints |
| `umowa2` | `contracts` | Snapshot kontrahenta zachowany, oddział jako FK |
| `umowa_oddzial` | *(usunięta)* | Zastąpiona przez `contracts.branch_id` |
| `dostawa` | `deliveries` | Bez zmian |
| `adres_dostawy` | `delivery_addresses` | Bez zmian |
| `umowa_pozycja3` | `contract_positions` | Dodano `billing_frequency` enum |
| `umowa_pozycja2_warunek` | `position_conditions` | Bez zmian strukturalnych |
| `koszt` | `costs` | FK constraints dodane |
| `rozliczenie` | `contract_settlements` | Zastąpiona przez RAO-P1-012 (koszty klient vs firma) |
| `zdarzenie` | `audit_log` | Dodano `user_id` |
| `a`, `u` | *(nie migrate)* | Historyczny cache, dane w relacjach |
| `artykul`, `artykul2`, `umowa`, `umowa_pozycja`, `umowa_pozycja2` | *(nie migrate)* | Legacy, zastąpione przez `*3` wersje |
| `kontrahent` | *(nie migrate)* | Legacy, zastąpione przez `kontrahent2` |
| `imp*` | *(nie migrate)* | Tabele importowe, jednorazowe |
| `dane`, `temp`, `lp`, `nr_umowy`, `oddo` | *(nie migrate)* | Tabele pomocnicze/tymczasowe |

## Tabele-widoki (VIEWS) — w NOWYM systemie nie potrzebne

W starym WinForms views (`umowy`, `kontrahenci`, `artykuly`, `artykulyy`, `pozycje`, `pozycje2`, `warunki`, `dane`, `oplaty`, `rao_dshb`, `rozliczenie_rpt`) służyły do odczytu JOIN danych.

W nowym systemie **SQLAlchemy ORM** robi JOIN automatycznie — views nie są potrzebne.
Jeśli jednak agent chce je stworzyć dla kompatybilności z raportami:

```sql
-- Opcjonalnie, do raportów
CREATE OR REPLACE VIEW v_contracts AS
SELECT
    c.id AS idu,
    c.contractor_id AS idk,
    ct.name AS kontrahent,
    c.number AS numer,
    CASE c.contract_type WHEN 'S' THEN 'Umowa najmu' ELSE 'Umowa usługi' END AS typ,
    c.description AS opis,
    c.delivery_address AS adres,
    c.date_from AS poczatek,
    c.date_to AS koniec,
    c.notes AS uwagi,
    c.total_value AS wartosc,
    c.prepayment_amount AS przedplata_kwota,
    c.prepayment_document AS przedplata_dokument,
    -- RAO-P1-103: invoice_amount/invoice_document usunięte (kwoty faktur z Fakturowni)
    c.created_at AS wprowadzona,
    DATEDIFF(c.date_to, c.date_from) AS trwa,
    c.email,
    sp.name AS handlowiec
FROM contracts c
JOIN contractors ct ON c.contractor_id = ct.id
LEFT JOIN salespeople sp ON c.salesperson_id = sp.id;
```

## Procedury — zamienione na logikę Python

W starym systemie:
- `DuplikujArtykul2` → Python service: `ArticleService.duplicate(id)`
- `sprDostepnosc` → Python service: `ArticleService.check_availability(id, date_from, date_to)`
- `sprUmowyArtykulu5/6` → Python service: `ContractService.get_contracts_for_article(id)`
- `getUmowyArtykulu7` → Python service: `ArticleService.get_with_contract_status()`
- `cena_pozycji` (function) → Python: `PositionService.calculate_price(position_id)`
- `rozlicz_pozycje` (function) → Python: `SettlementService.calculate(position_id)`

---

## Uwagi techniczne

**Weryfikacja numeru telefonu (RAO-P1-010):** Wszystkie szablony PDF w repozytorium mają poprawny numer `+48 888 992 015`. W kodzie Pythona i frontendzie nie ma wzmianki o `888 992 017`. Jeśli klient widział błędny numer, prawdopodobną przyczyną był stary deployment na produkcji lub stare dane w polu `company.header_text`. Do weryfikacji na produkcji: `SELECT id, header_text FROM company` oraz sprawdzenie czy deployment ma aktualne szablony. Jeśli `header_text` zawiera stary numer: `UPDATE company SET header_text = REPLACE(header_text, '888 992 017', '888 992 015');`
- `generuj_opis_oplaty` (function) → Python: `FeeService.generate_description()`
