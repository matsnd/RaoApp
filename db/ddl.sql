-- RAO App — DDL (wg spec/01_DATABASE_DDL.md)
USE rao_new;

-- 1.1 Użytkownicy
CREATE TABLE IF NOT EXISTS users (
    id                    INT AUTO_INCREMENT PRIMARY KEY,
    login                 VARCHAR(50)  NOT NULL UNIQUE,
    email                 VARCHAR(100) NULL UNIQUE,
    password              VARCHAR(255) NOT NULL,
    first_name            VARCHAR(30)  NULL,
    last_name             VARCHAR(30)  NULL,
    role                  ENUM('admin','user','viewer') NOT NULL DEFAULT 'user',
    branch_id             INT          NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    must_change_password  BOOLEAN      NOT NULL DEFAULT FALSE,
    password_reset_token  VARCHAR(255) NULL,
    password_reset_expires DATETIME    NULL,
    last_login            DATETIME     NULL,
    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_login (login),
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

-- 1.2 Oddziały
CREATE TABLE IF NOT EXISTS branches (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    address      VARCHAR(200) NULL,
    postal_code  VARCHAR(20)  NULL,
    city         VARCHAR(100) NULL,
    street       VARCHAR(100) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- FK users → branches (po created branches)
ALTER TABLE users ADD CONSTRAINT fk_users_branch
    FOREIGN KEY (branch_id) REFERENCES branches(id) ON DELETE SET NULL;

-- 1.3 Kategorie
CREATE TABLE IF NOT EXISTS categories (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    name  VARCHAR(200) NOT NULL,
    code  VARCHAR(40)  NULL,
    description VARCHAR(400) NULL,
    INDEX idx_categories_name (name)
) ENGINE=InnoDB;

-- 1.4 Handlowcy
CREATE TABLE IF NOT EXISTS salespeople (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(200) NOT NULL,
    phone     VARCHAR(100) NULL,
    is_active BOOLEAN      NOT NULL DEFAULT TRUE,
    INDEX idx_salespeople_active (is_active)
) ENGINE=InnoDB;

-- 1.5 Typy stawek
CREATE TABLE IF NOT EXISTS rate_types (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(400) NOT NULL,
    description VARCHAR(800) NULL,
    is_dependent BOOLEAN     NULL DEFAULT FALSE
) ENGINE=InnoDB;

-- 1.6 Typy kosztów
CREATE TABLE IF NOT EXISTS cost_types (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description VARCHAR(400) NULL,
    amount1     DECIMAL(18,2) NULL,
    amount2     DECIMAL(18,2) NULL
) ENGINE=InnoDB;

-- 1.7 Firma (singleton)
CREATE TABLE IF NOT EXISTS company (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(200) NULL,
    name_short     VARCHAR(100) NULL,
    nip            VARCHAR(20)  NULL,
    regon          VARCHAR(20)  NULL,
    postal_code    VARCHAR(20)  NULL,
    city           VARCHAR(50)  NULL,
    street         VARCHAR(50)  NULL,
    header_text    TEXT         NULL,
    logo           LONGBLOB     NULL,
    bank_name      VARCHAR(200) NULL,
    bank_account   VARCHAR(40)  NULL,
    numbering_start INT         NULL DEFAULT 1,
    increment_step DECIMAL(18,2) NULL DEFAULT 50.00,
    report_folder  VARCHAR(200) NULL,
    protocol_folder VARCHAR(200) NULL,
    app_version    VARCHAR(20)  NULL
) ENGINE=InnoDB;

-- 1.8 Szablony usług dodatkowych
CREATE TABLE IF NOT EXISTS service_fee_templates (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    company_id   INT          NOT NULL DEFAULT 1,
    contract_type CHAR(1)     NOT NULL,
    sort_order   INT          NOT NULL DEFAULT 0,
    name         VARCHAR(200) NOT NULL,
    amount_from  DECIMAL(18,2) NULL,
    amount_to    DECIMAL(18,2) NULL,
    unit         VARCHAR(50)  NULL,
    description  VARCHAR(400) NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_sft_company FOREIGN KEY (company_id) REFERENCES company(id),
    INDEX idx_sft_type (company_id, contract_type, sort_order)
) ENGINE=InnoDB;

-- 2. Kontrahenci
CREATE TABLE IF NOT EXISTS contractors (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(400) NOT NULL,
    name_short       VARCHAR(200) NULL,
    nip              VARCHAR(20)  NULL,
    regon            VARCHAR(20)  NULL,
    pesel            VARCHAR(20)  NULL,
    postal_code      VARCHAR(20)  NULL,
    city             VARCHAR(50)  NULL,
    street           VARCHAR(50)  NULL,
    unit             VARCHAR(50)  NULL,
    notes            TEXT         NULL,
    is_supplier      BOOLEAN      NOT NULL DEFAULT FALSE,
    email            VARCHAR(100) NULL,
    contact_person1  VARCHAR(100) NULL,
    phone1           VARCHAR(100) NULL,
    contact_person2  VARCHAR(100) NULL,
    phone2           VARCHAR(100) NULL,
    landline_phone   VARCHAR(20)  NULL,
    website          VARCHAR(100) NULL,
    files_folder     VARCHAR(100) NULL,
    gus_date         DATETIME     NULL,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contractors_name (name),
    INDEX idx_contractors_nip (nip),
    INDEX idx_contractors_supplier (is_supplier)
) ENGINE=InnoDB;

-- 2.1 Adresy kontrahentów
CREATE TABLE IF NOT EXISTS contractor_addresses (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id   INT          NOT NULL,
    name            VARCHAR(200) NULL,
    country_code    VARCHAR(3)   NULL DEFAULT 'PL',
    postal_code     VARCHAR(20)  NULL,
    city            VARCHAR(50)  NULL,
    street          VARCHAR(50)  NULL,
    notes           VARCHAR(200) NULL,
    contact_person  VARCHAR(100) NULL,
    phone           VARCHAR(20)  NULL,
    email           VARCHAR(20)  NULL,
    is_default_delivery BOOLEAN  NOT NULL DEFAULT FALSE,
    is_headquarters     BOOLEAN  NOT NULL DEFAULT FALSE,
    latitude        DECIMAL(10,7) NULL,
    longitude       DECIMAL(10,7) NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_addr_contractor FOREIGN KEY (contractor_id)
        REFERENCES contractors(id) ON DELETE CASCADE,
    INDEX idx_addr_contractor (contractor_id)
) ENGINE=InnoDB;

-- 3. Artykuły
CREATE TABLE IF NOT EXISTS articles (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(200) NOT NULL,
    is_service        BOOLEAN      NOT NULL DEFAULT FALSE,
    internal_number   VARCHAR(50)  NULL,
    registration_no   VARCHAR(40)  NULL,
    serial_no         VARCHAR(40)  NULL,
    brand             VARCHAR(100) NULL,
    model             VARCHAR(100) NULL,
    replacement_value DECIMAL(18,2) NULL,
    category_id       INT          NULL,
    owner_id          INT          NULL,
    branch_id         INT          NULL,
    description       VARCHAR(400) NULL,
    notes             VARCHAR(200) NULL,
    rental_days       INT          NULL,
    article_type      VARCHAR(20)  NULL,
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
    INDEX idx_art_registration (registration_no)
) ENGINE=InnoDB;

-- 4. Umowy
CREATE TABLE IF NOT EXISTS contracts (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id       INT          NOT NULL,
    branch_id           INT          NULL,
    salesperson_id      INT          NULL,
    number              VARCHAR(40)  NOT NULL,
    auto_number         INT          NULL,
    contract_type       CHAR(1)      NOT NULL DEFAULT 'S',
    delivery_address    TEXT         NULL,
    date_from           DATE         NULL,
    date_to             DATE         NULL,
    total_value         DECIMAL(18,2) NULL DEFAULT 0.00,
    prepayment_amount   DECIMAL(18,2) NULL DEFAULT 0.00,
    prepayment_document VARCHAR(200) NULL,
    invoice_amount      DECIMAL(18,2) NULL DEFAULT 0.00,
    invoice_document    VARCHAR(40)  NULL,
    notes               TEXT         NULL,
    contact_person1     VARCHAR(100) NULL,
    contact_phone1      VARCHAR(100) NULL,
    show_person1        BOOLEAN      NOT NULL DEFAULT TRUE,
    contact_person2     VARCHAR(100) NULL,
    contact_phone2      VARCHAR(100) NULL,
    show_person2        BOOLEAN      NOT NULL DEFAULT TRUE,
    email               VARCHAR(100) NULL,
    phone               VARCHAR(40)  NULL,
    contractor_name     VARCHAR(200) NULL,
    print_path          VARCHAR(100) NULL,
    print_date          DATETIME     NULL,
    report_without_data BOOLEAN      NOT NULL DEFAULT FALSE,
    working_days_per_week INT        NULL DEFAULT 6,
    position_count      INT          NULL DEFAULT 0,
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
    INDEX idx_contract_type (contract_type)
) ENGINE=InnoDB;

-- 4.1 Dostawa
CREATE TABLE IF NOT EXISTS deliveries (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    contract_id INT NOT NULL,
    address_id  INT NULL,
    latitude    DECIMAL(10,7) NULL,
    longitude   DECIMAL(10,7) NULL,
    CONSTRAINT fk_delivery_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    CONSTRAINT fk_delivery_address FOREIGN KEY (address_id)
        REFERENCES contractor_addresses(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 4.2 Adresy dostawy (reverse geocoding)
CREATE TABLE IF NOT EXISTS delivery_addresses (
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
    county       VARCHAR(100) NULL,
    municipality VARCHAR(100) NULL,
    province     VARCHAR(100) NULL,
    district     VARCHAR(200) NULL,
    neighbourhood VARCHAR(200) NULL,
    CONSTRAINT fk_deladdr_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Pozycje umowy
CREATE TABLE IF NOT EXISTS contract_positions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contract_id     INT          NOT NULL,
    article_id      INT          NOT NULL,
    rental_type     VARCHAR(20)  NULL,
    description     VARCHAR(400) NULL,
    rental_days     INT          NULL,
    quantity        INT          NULL DEFAULT 1,
    unit_price      DECIMAL(18,2) NULL,
    costs           DECIMAL(18,2) NULL DEFAULT 0.00,
    rate_type_id    INT          NULL,
    billing_frequency VARCHAR(20) NULL,
    billing_unit    VARCHAR(20)  NULL,
    supplier_id     INT          NULL,
    delivery_date   DATE         NULL,
    article_name    VARCHAR(400) NULL,
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
) ENGINE=InnoDB;

-- 5.1 Warunki rozliczenia
CREATE TABLE IF NOT EXISTS position_conditions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    position_id     INT          NOT NULL,
    rate_type_id    INT          NULL,
    description     VARCHAR(400) NULL,
    rate1           DECIMAL(18,2) NULL,
    rate2           DECIMAL(18,2) NULL,
    billing_label   VARCHAR(20)  NULL,
    period_count    INT          NULL,
    minimum         INT          NULL,
    CONSTRAINT fk_cond_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    CONSTRAINT fk_cond_rate_type FOREIGN KEY (rate_type_id)
        REFERENCES rate_types(id) ON DELETE SET NULL,
    INDEX idx_cond_position (position_id)
) ENGINE=InnoDB;

-- 6. Koszty
CREATE TABLE IF NOT EXISTS costs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    cost_type_id INT         NULL,
    position_id  INT         NULL,
    description  VARCHAR(400) NULL,
    amount       DECIMAL(18,2) NULL,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cost_type FOREIGN KEY (cost_type_id)
        REFERENCES cost_types(id) ON DELETE SET NULL,
    CONSTRAINT fk_cost_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Usługi dodatkowe umowy
CREATE TABLE IF NOT EXISTS contract_service_fees (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    contract_id  INT          NOT NULL,
    sort_order   INT          NOT NULL DEFAULT 0,
    name         VARCHAR(200) NOT NULL,
    amount_from  DECIMAL(18,2) NULL,
    amount_to    DECIMAL(18,2) NULL,
    unit         VARCHAR(50)  NULL,
    description  VARCHAR(400) NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_csf_contract FOREIGN KEY (contract_id)
        REFERENCES contracts(id) ON DELETE CASCADE,
    INDEX idx_csf_contract (contract_id, sort_order)
) ENGINE=InnoDB;

-- 8. Rozliczenia (cache techniczny — deprecated)
CREATE TABLE IF NOT EXISTS settlements (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    position_id INT          NOT NULL,
    date        DATETIME     NULL,
    amount      DECIMAL(18,2) NULL,
    CONSTRAINT fk_settlement_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    INDEX idx_settlement_position (position_id)
) ENGINE=InnoDB;

-- 8.1 Ewidencja godzin usługi (protokół U)
CREATE TABLE IF NOT EXISTS service_hours (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    position_id INT          NOT NULL,
    work_date   DATE         NOT NULL,
    time_from   VARCHAR(10)  NULL,
    time_to     VARCHAR(10)  NULL,
    notes       VARCHAR(200) NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_service_hours_position FOREIGN KEY (position_id)
        REFERENCES contract_positions(id) ON DELETE CASCADE,
    INDEX idx_sh_position (position_id),
    INDEX idx_sh_date (work_date)
) ENGINE=InnoDB;

-- 9. Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    session_id  INT          NULL,
    event_date  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_text  VARCHAR(500) NULL,
    user_id     INT          NULL,
    INDEX idx_audit_date (event_date)
) ENGINE=InnoDB;

-- Widok v_contracts (opcjonalny, dla raportów)
CREATE OR REPLACE VIEW v_contracts AS
SELECT
    c.id AS idu, c.contractor_id AS idk,
    ct.name AS kontrahent, c.number AS numer,
    CASE c.contract_type WHEN 'S' THEN 'Umowa najmu' ELSE 'Umowa usługi' END AS typ,
    c.delivery_address AS adres, c.date_from AS poczatek, c.date_to AS koniec,
    c.notes AS uwagi, c.total_value AS wartosc,
    c.prepayment_amount AS przedplata_kwota, c.prepayment_document AS przedplata_dokument,
    c.invoice_amount AS faktura_kwota, c.invoice_document AS faktura_dokument,
    c.created_at AS wprowadzona, DATEDIFF(c.date_to, c.date_from) AS trwa,
    c.email, sp.name AS handlowiec
FROM contracts c
JOIN contractors ct ON c.contractor_id = ct.id
LEFT JOIN salespeople sp ON c.salesperson_id = sp.id;

-- Seed: domyślny admin (hasło zmienić po pierwszym logowaniu)
INSERT IGNORE INTO company (id, name, name_short) VALUES (1, 'Toolsmart', 'TS');
INSERT IGNORE INTO users (login, email, password, role, first_name)
VALUES ('admin', 'admin@rao.local',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TqxDXMDFmBbNGMZQkEh4w4fBqrCq',
        'admin', 'Admin');

SELECT CONCAT('Tabele: ', COUNT(*)) AS wynik FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'rao_new' AND TABLE_TYPE = 'BASE TABLE';
