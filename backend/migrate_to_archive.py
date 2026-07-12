"""
RAO-P2-062 Faza 0 — Migracja legacy danych do tabel archive_* w bazie rao_new.

Decyzje użytkownika (2026-07-01):
  1. Tabele archive_* w jednej bazie rao_new (nie osobna DB)
  2. Kontrahenci współdzielone (jedna tabela contractors)
  3. Artykuły osobne: articles (nowe) + archive_articles (frozen snapshot)
  4. Kategorie osobne: categories (nowe) + archive_categories (frozen snapshot, edytowalne)
  5. Archiwum read-only Z WYJĄTKIEM edycji kategorii

Scope (TYLKO migracja danych, NIE backend):
  1. Backup przed migracją (mariadb-dump)
  2. CREATE TABLE IF NOT EXISTS archive_* (mirror schema)
  3. INSERT IGNORE legacy danych do archive_*
  4. DELETE legacy danych z tabel oryginalnych (kolejność cascade-safe)
  5. Weryfikacja COUNT

NIE modyfikuje:
  - modeli SQLAlchemy (to Faza 1)
  - main.py (to Faza 1)
  - kolumny is_legacy (to Faza 1)
  - tabel articles, categories, contractors (współdzielone/zostają)

Idempotentny: można re-run. CREATE TABLE IF NOT EXISTS + INSERT IGNORE +
DELETE (no-op po pierwszym uruchomieniu bo nie ma już legacy wierszy).

Usage:
  cd backend
  .venv/Scripts/python.exe migrate_to_archive.py
"""
import asyncio
import io
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import aiomysql

# --- Konfiguracja (z .env) ---------------------------------------------------
from urllib.parse import urlparse
from config import settings

# RAO_DATABASE_URL = mysql+aiomysql://rao_user:pass@host:3306/rao_new
_url = urlparse(settings.RAO_DATABASE_URL.replace("+aiomysql", "").replace("+asyncmy", ""))
DB_NAME = _url.path.lstrip("/")
DB_USER = _url.username
DB_PASSWORD = _url.password
DB_HOST = _url.hostname or "localhost"
DB_PORT = _url.port or 3306

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_FILE = PROJECT_ROOT / "backup_pre_archive_split.sql"

# --- DDL: archive_* tabele (mirror oryginalnych) ----------------------------
# archive_categories — mirror categories (self-ref FK do archive_categories)
DDL_ARCHIVE_CATEGORIES = """
CREATE TABLE IF NOT EXISTS `archive_categories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `code` varchar(40) DEFAULT NULL,
  `description` varchar(400) DEFAULT NULL,
  `parent_id` int(11) DEFAULT NULL,
  `level` enum('main','sub1','sub2','sub3') NOT NULL DEFAULT 'main',
  PRIMARY KEY (`id`),
  KEY `idx_archive_categories_name` (`name`),
  KEY `idx_archive_categories_parent` (`parent_id`),
  CONSTRAINT `fk_archive_categories_parent_id`
    FOREIGN KEY (`parent_id`) REFERENCES `archive_categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_articles — mirror articles, category_id -> archive_categories.id
# (owner_id, branch_id zostają jako kolumny z FK do współdzielonych contractors/branches)
DDL_ARCHIVE_ARTICLES = """
CREATE TABLE IF NOT EXISTS `archive_articles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `is_service` tinyint(1) NOT NULL,
  `internal_number` varchar(50) DEFAULT NULL,
  `registration_no` varchar(40) DEFAULT NULL,
  `serial_no` varchar(40) DEFAULT NULL,
  `brand` varchar(100) DEFAULT NULL,
  `model` varchar(100) DEFAULT NULL,
  `replacement_value` decimal(18,2) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `owner_id` int(11) DEFAULT NULL,
  `branch_id` int(11) DEFAULT NULL,
  `description` varchar(400) DEFAULT NULL,
  `notes` varchar(200) DEFAULT NULL,
  `rental_days` int(11) DEFAULT NULL,
  `article_type` varchar(20) DEFAULT NULL,
  `category_main` varchar(100) DEFAULT NULL,
  `category_sub1` varchar(100) DEFAULT NULL,
  `category_sub2` varchar(100) DEFAULT NULL,
  `category_sub3` varchar(100) DEFAULT NULL,
  `is_external` tinyint(1) NOT NULL DEFAULT 0,
  `technical_attributes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL
    CHECK (json_valid(`technical_attributes`)),
  `zasieg_m` decimal(8,2) DEFAULT NULL COMMENT 'Zasięg w metrach',
  `udzwig_t` decimal(8,2) DEFAULT NULL COMMENT 'Udźwig w tonach',
  `dodatki` text DEFAULT NULL COMMENT 'Dodatkowe akcesoria / wyposażenie',
  `fakturownia_product_id` bigint(20) DEFAULT NULL
    COMMENT 'ID produktu w Fakturownia (mapping globalny 1:N)',
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_archive_art_name` (`name`),
  KEY `idx_archive_art_category` (`category_id`),
  KEY `idx_archive_art_owner` (`owner_id`),
  KEY `idx_archive_art_registration` (`registration_no`),
  KEY `idx_archive_articles_category_main` (`category_main`),
  KEY `idx_archive_articles_fakturownia_product` (`fakturownia_product_id`),
  KEY `idx_archive_articles_zasieg` (`zasieg_m`),
  KEY `idx_archive_articles_udzwig` (`udzwig_t`),
  KEY `idx_archive_articles_external` (`is_external`),
  KEY `fk_archive_articles_branch_id` (`branch_id`),
  CONSTRAINT `fk_archive_articles_branch_id`
    FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_archive_articles_category_id`
    FOREIGN KEY (`category_id`) REFERENCES `archive_categories` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_archive_articles_owner_id`
    FOREIGN KEY (`owner_id`) REFERENCES `contractors` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_contracts — mirror contracts BEZ is_legacy
# (contractor_id, branch_id, salesperson_id, postal_code_id -> współdzielone tabele)
DDL_ARCHIVE_CONTRACTS = """
CREATE TABLE IF NOT EXISTS `archive_contracts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contractor_id` int(11) NOT NULL,
  `branch_id` int(11) DEFAULT NULL,
  `salesperson_id` int(11) DEFAULT NULL,
  `number` varchar(40) NOT NULL,
  `oid` varchar(40) DEFAULT NULL COMMENT 'Numer zamówienia w Fakturownia',
  `auto_number` int(11) DEFAULT NULL,
  `contract_type` varchar(1) NOT NULL,
  `delivery_address` text DEFAULT NULL,
  `postal_code` varchar(20) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `postal_code_id` int(11) DEFAULT NULL COMMENT 'FK do postal_codes',
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `date_from` date DEFAULT NULL,
  `date_to` date DEFAULT NULL,
  `prepayment_amount` decimal(18,2) DEFAULT NULL,
  `prepayment_document` varchar(200) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `contact_person1` varchar(100) DEFAULT NULL,
  `contact_phone1` varchar(100) DEFAULT NULL,
  `show_person1` tinyint(1) NOT NULL,
  `contact_person2` varchar(100) DEFAULT NULL,
  `contact_phone2` varchar(100) DEFAULT NULL,
  `show_person2` tinyint(1) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(40) DEFAULT NULL,
  `contractor_name` varchar(200) DEFAULT NULL,
  `print_path` varchar(100) DEFAULT NULL,
  `print_date` datetime DEFAULT NULL,
  `report_without_data` tinyint(1) NOT NULL,
  `hide_delivery_address` tinyint(1) NOT NULL,
  `signatures_on_page1` tinyint(1) NOT NULL,
  `working_days_per_week` int(11) DEFAULT NULL,
  `position_count` int(11) DEFAULT NULL,
  `is_settled` tinyint(1) NOT NULL,
  `settled_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_archive_contracts_number` (`number`),
  KEY `fk_archive_contracts_contractor_id` (`contractor_id`),
  KEY `fk_archive_contracts_branch_id` (`branch_id`),
  KEY `idx_archive_contracts_postal_code_id` (`postal_code_id`),
  KEY `idx_archive_contracts_is_settled` (`is_settled`),
  KEY `idx_archive_contracts_created_at` (`created_at`),
  KEY `idx_archive_contracts_salesperson_id` (`salesperson_id`),
  KEY `idx_archive_contracts_print_date` (`print_date`),
  KEY `idx_archive_contracts_delivery_date` (`date_to`),
  KEY `idx_archive_contracts_postal_code` (`postal_code`),
  KEY `idx_archive_contracts_city` (`city`),
  CONSTRAINT `fk_archive_contracts_branch_id`
    FOREIGN KEY (`branch_id`) REFERENCES `branches` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_archive_contracts_contractor_id`
    FOREIGN KEY (`contractor_id`) REFERENCES `contractors` (`id`),
  CONSTRAINT `fk_archive_contracts_postal_code_id`
    FOREIGN KEY (`postal_code_id`) REFERENCES `postal_codes` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_archive_contracts_salesperson_id`
    FOREIGN KEY (`salesperson_id`) REFERENCES `salespeople` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_contract_positions — mirror contract_positions
# contract_id -> archive_contracts.id, article_id -> archive_articles.id
DDL_ARCHIVE_POSITIONS = """
CREATE TABLE IF NOT EXISTS `archive_contract_positions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contract_id` int(11) NOT NULL,
  `article_id` int(11) NOT NULL,
  `description` varchar(400) DEFAULT NULL,
  `rental_days` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `unit_price` decimal(18,2) DEFAULT NULL,
  `costs` decimal(18,2) DEFAULT NULL,
  `rate_type_id` int(11) DEFAULT NULL,
  `billing_frequency` varchar(20) DEFAULT NULL,
  `billing_unit` varchar(20) DEFAULT NULL,
  `supplier_id` int(11) DEFAULT NULL,
  `delivery_date` date DEFAULT NULL,
  `article_name` varchar(400) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_archive_cp_contract_id` (`contract_id`),
  KEY `fk_archive_cp_article_id` (`article_id`),
  KEY `fk_archive_cp_rate_type_id` (`rate_type_id`),
  KEY `fk_archive_cp_supplier_id` (`supplier_id`),
  CONSTRAINT `fk_archive_cp_article_id`
    FOREIGN KEY (`article_id`) REFERENCES `archive_articles` (`id`),
  CONSTRAINT `fk_archive_cp_contract_id`
    FOREIGN KEY (`contract_id`) REFERENCES `archive_contracts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_archive_cp_rate_type_id`
    FOREIGN KEY (`rate_type_id`) REFERENCES `rate_types` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_archive_cp_supplier_id`
    FOREIGN KEY (`supplier_id`) REFERENCES `contractors` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_position_conditions — mirror position_conditions
# position_id -> archive_contract_positions.id
DDL_ARCHIVE_CONDITIONS = """
CREATE TABLE IF NOT EXISTS `archive_position_conditions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position_id` int(11) NOT NULL,
  `rate_type_id` int(11) DEFAULT NULL,
  `description` varchar(400) DEFAULT NULL,
  `rate1` decimal(18,2) DEFAULT NULL,
  `rate2` decimal(18,2) DEFAULT NULL,
  `billing_label` varchar(20) DEFAULT NULL,
  `period_count` int(11) DEFAULT NULL,
  `minimum` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_archive_pc_position_id` (`position_id`),
  KEY `fk_archive_pc_rate_type_id` (`rate_type_id`),
  CONSTRAINT `fk_archive_pc_position_id`
    FOREIGN KEY (`position_id`) REFERENCES `archive_contract_positions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_archive_pc_rate_type_id`
    FOREIGN KEY (`rate_type_id`) REFERENCES `rate_types` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_contract_service_fees — mirror contract_service_fees
# contract_id -> archive_contracts.id
# article_id: brak FK (artykuł-usługa może nie być w archive_articles — tylko
# maszyny z legacy pozycji są kopiowane; service articles zostają w articles)
DDL_ARCHIVE_SERVICE_FEES = """
CREATE TABLE IF NOT EXISTS `archive_contract_service_fees` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contract_id` int(11) NOT NULL,
  `sort_order` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `amount_from` decimal(18,2) DEFAULT NULL,
  `amount_to` decimal(18,2) DEFAULT NULL,
  `unit` varchar(50) DEFAULT NULL,
  `description` varchar(400) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `article_id` int(11) DEFAULT NULL,
  `default_price` decimal(18,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_archive_csf_contract_id` (`contract_id`),
  KEY `idx_archive_csf_article_id` (`article_id`),
  CONSTRAINT `fk_archive_csf_contract_id`
    FOREIGN KEY (`contract_id`) REFERENCES `archive_contracts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

# archive_contract_settlements — mirror contract_settlements
# contract_id -> archive_contracts.id
# position_id -> archive_contract_positions.id (nullable)
# service_fee_id -> archive_contract_service_fees.id (nullable)
DDL_ARCHIVE_SETTLEMENTS = """
CREATE TABLE IF NOT EXISTS `archive_contract_settlements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `contract_id` int(11) NOT NULL,
  `position_id` int(11) DEFAULT NULL,
  `service_fee_id` int(11) DEFAULT NULL,
  `cost_client` decimal(18,2) DEFAULT NULL,
  `cost_company` decimal(18,2) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL DEFAULT current_timestamp(),
  `settled_at` date DEFAULT NULL COMMENT 'Data rozliczenia',
  `source` varchar(20) DEFAULT 'manual' COMMENT 'legacy/fakturownia/manual',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_archive_settlements_contract_pos_fee_date`
    (`contract_id`,`position_id`,`service_fee_id`,`settled_at`),
  KEY `fk_archive_cs_position_id` (`position_id`),
  KEY `fk_archive_cs_service_fee_id` (`service_fee_id`),
  CONSTRAINT `fk_archive_cs_contract_id`
    FOREIGN KEY (`contract_id`) REFERENCES `archive_contracts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_archive_cs_position_id`
    FOREIGN KEY (`position_id`) REFERENCES `archive_contract_positions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_archive_cs_service_fee_id`
    FOREIGN KEY (`service_fee_id`) REFERENCES `archive_contract_service_fees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
"""

ALL_DDL = [
    ("archive_categories", DDL_ARCHIVE_CATEGORIES),
    ("archive_articles", DDL_ARCHIVE_ARTICLES),
    ("archive_contracts", DDL_ARCHIVE_CONTRACTS),
    ("archive_contract_positions", DDL_ARCHIVE_POSITIONS),
    ("archive_position_conditions", DDL_ARCHIVE_CONDITIONS),
    ("archive_contract_service_fees", DDL_ARCHIVE_SERVICE_FEES),
    ("archive_contract_settlements", DDL_ARCHIVE_SETTLEMENTS),
]


# --- INSERT...SELECT (idempotent przez INSERT IGNORE) -----------------------
# Kolejność zgodna z FK: parents przed children.
# Wszystkie INSERT-y używają INSERT IGNORE — re-run nie duplikuje.

# archive_categories: WSZYSTKIE kategorie (bo wszystkie używane przez legacy maszyny)
INS_CATEGORIES = """
INSERT IGNORE INTO `archive_categories`
  (id, name, code, description, parent_id, level)
SELECT id, name, code, description, parent_id, level
FROM `categories`
"""

# archive_articles: tylko te używane w legacy pozycjach
# category_id przemapowany 1:1 (ta sama ID bo archive_categories = kopia categories)
INS_ARTICLES = """
INSERT IGNORE INTO `archive_articles`
  (id, name, is_service, internal_number, registration_no, serial_no, brand, model,
   replacement_value, category_id, owner_id, branch_id, description, notes,
   rental_days, article_type, category_main, category_sub1, category_sub2, category_sub3,
   is_external, technical_attributes, zasieg_m, udzwig_t, dodatki,
   fakturownia_product_id, created_at, updated_at)
SELECT a.id, a.name, a.is_service, a.internal_number, a.registration_no, a.serial_no,
       a.brand, a.model, a.replacement_value, a.category_id, a.owner_id, a.branch_id,
       a.description, a.notes, a.rental_days, a.article_type, a.category_main,
       a.category_sub1, a.category_sub2, a.category_sub3, a.is_external,
       a.technical_attributes, a.zasieg_m, a.udzwig_t, a.dodatki,
       a.fakturownia_product_id, a.created_at, a.updated_at
FROM `articles` a
WHERE a.id IN (
  SELECT DISTINCT cp.article_id
  FROM `contract_positions` cp
  WHERE cp.contract_id IN (SELECT id FROM `contracts` )
)
"""

# archive_contracts: legacy umowy bez is_legacy
INS_CONTRACTS = """
INSERT IGNORE INTO `archive_contracts`
  (id, contractor_id, branch_id, salesperson_id, number, oid, auto_number, contract_type,
   delivery_address, postal_code, city, postal_code_id, latitude, longitude,
   date_from, date_to, prepayment_amount, prepayment_document,
   notes, contact_person1, contact_phone1, show_person1,
   contact_person2, contact_phone2, show_person2, email, phone, contractor_name,
   print_path, print_date, report_without_data, hide_delivery_address,
   signatures_on_page1, working_days_per_week, position_count, is_settled, settled_at,
   created_at, updated_at)
SELECT id, contractor_id, branch_id, salesperson_id, number, oid, auto_number,
       contract_type, delivery_address, postal_code, city, postal_code_id, latitude,
       longitude, date_from, date_to, prepayment_amount, prepayment_document,
       notes, contact_person1, contact_phone1,
       show_person1, contact_person2, contact_phone2, show_person2, email, phone,
       contractor_name, print_path, print_date, report_without_data,
       hide_delivery_address, signatures_on_page1, working_days_per_week,
       position_count, is_settled, settled_at, created_at, updated_at
FROM `contracts`
"""

# archive_contract_positions: pozycje dla legacy umów
INS_POSITIONS = """
INSERT IGNORE INTO `archive_contract_positions`
  (id, contract_id, article_id, description, rental_days, quantity,
   unit_price, costs, rate_type_id, billing_frequency, billing_unit, supplier_id,
   delivery_date, article_name)
SELECT cp.id, cp.contract_id, cp.article_id, cp.description,
       cp.rental_days, cp.quantity, cp.unit_price, cp.costs, cp.rate_type_id,
       cp.billing_frequency, cp.billing_unit, cp.supplier_id, cp.delivery_date,
       cp.article_name
FROM `contract_positions` cp
WHERE cp.contract_id IN (SELECT id FROM `contracts`)
"""

# archive_position_conditions: warunki dla legacy pozycji
INS_CONDITIONS = """
INSERT IGNORE INTO `archive_position_conditions`
  (id, position_id, rate_type_id, description, rate1, rate2, billing_label,
   period_count, minimum)
SELECT pc.id, pc.position_id, pc.rate_type_id, pc.description, pc.rate1, pc.rate2,
       pc.billing_label, pc.period_count, pc.minimum
FROM `position_conditions` pc
WHERE pc.position_id IN (
  SELECT cp.id FROM `contract_positions` cp
  WHERE cp.contract_id IN (SELECT id FROM `contracts`)
)
"""

# archive_contract_service_fees: usługi dla legacy umów
INS_SERVICE_FEES = """
INSERT IGNORE INTO `archive_contract_service_fees`
  (id, contract_id, sort_order, name, amount_from, amount_to, unit, description,
   is_active, article_id, default_price)
SELECT id, contract_id, sort_order, name, amount_from, amount_to, unit, description,
       is_active, article_id, default_price
FROM `contract_service_fees`
WHERE contract_id IN (SELECT id FROM `contracts` )
"""

# archive_contract_settlements: rozliczenia dla legacy umów
INS_SETTLEMENTS = """
INSERT IGNORE INTO `archive_contract_settlements`
  (id, contract_id, position_id, service_fee_id, cost_client, cost_company, notes,
   created_at, updated_at, settled_at, source)
SELECT id, contract_id, position_id, service_fee_id, cost_client, cost_company, notes,
       created_at, updated_at, settled_at, source
FROM `contract_settlements`
WHERE contract_id IN (SELECT id FROM `contracts` )
"""

ALL_INSERTS = [
    ("archive_categories", INS_CATEGORIES),
    ("archive_articles", INS_ARTICLES),
    ("archive_contracts", INS_CONTRACTS),
    ("archive_contract_positions", INS_POSITIONS),
    ("archive_position_conditions", INS_CONDITIONS),
    ("archive_contract_service_fees", INS_SERVICE_FEES),
    ("archive_contract_settlements", INS_SETTLEMENTS),
]


# --- DELETE legacy z tabel oryginalnych (kolejność cascade-safe) -----------
# Dzieci przed rodzicami. Używamy subquery z contracts .
# Po pierwszym uruchomieniu nie ma już legacy wierszy -> DELETE = no-op (idempotentne).
DEL_SETTLEMENTS = (
    "DELETE FROM `contract_settlements` "
    "WHERE contract_id IN (SELECT id FROM `contracts`)"
)
DEL_SERVICE_FEES = (
    "DELETE FROM `contract_service_fees` "
    "WHERE contract_id IN (SELECT id FROM `contracts`)"
)
DEL_CONDITIONS = (
    "DELETE FROM `position_conditions` "
    "WHERE position_id IN ("
    "  SELECT cp.id FROM `contract_positions` cp "
    "  WHERE cp.contract_id IN (SELECT id FROM `contracts`)"
    ")"
)
DEL_POSITIONS = (
    "DELETE FROM `contract_positions` "
    "WHERE contract_id IN (SELECT id FROM `contracts`)"
)
DEL_CONTRACTS = "DELETE FROM `contracts`"

ALL_DELETES = [
    ("contract_settlements", DEL_SETTLEMENTS),
    ("contract_service_fees", DEL_SERVICE_FEES),
    ("position_conditions", DEL_CONDITIONS),
    ("contract_positions", DEL_POSITIONS),
    ("contracts", DEL_CONTRACTS),
]


# --- Weryfikacja ------------------------------------------------------------
VERIFY_QUERIES = [
    ("contracts (oczekiwane 0)", "SELECT COUNT(*) FROM `contracts`"),
    ("archive_contracts (oczekiwane 742)", "SELECT COUNT(*) FROM `archive_contracts`"),
    ("contract_settlements (oczekiwane 0)", "SELECT COUNT(*) FROM `contract_settlements`"),
    ("archive_contract_settlements (oczekiwane 1945)", "SELECT COUNT(*) FROM `archive_contract_settlements`"),
    ("contract_positions (oczekiwane 0 lub 3 orphans)", "SELECT COUNT(*) FROM `contract_positions`"),
    ("archive_contract_positions (oczekiwane 878)", "SELECT COUNT(*) FROM `archive_contract_positions`"),
    ("position_conditions (oczekiwane 0)", "SELECT COUNT(*) FROM `position_conditions`"),
    ("archive_position_conditions", "SELECT COUNT(*) FROM `archive_position_conditions`"),
    ("contract_service_fees (oczekiwane 0)", "SELECT COUNT(*) FROM `contract_service_fees`"),
    ("archive_contract_service_fees (oczekiwane 3396)", "SELECT COUNT(*) FROM `archive_contract_service_fees`"),
    ("archive_categories (oczekiwane 64)", "SELECT COUNT(*) FROM `archive_categories`"),
    ("archive_articles (oczekiwane 351)", "SELECT COUNT(*) FROM `archive_articles`"),
    ("categories (nietknięte, 64)", "SELECT COUNT(*) FROM `categories`"),
    ("articles (nietknięte, 419)", "SELECT COUNT(*) FROM `articles`"),
    ("contractors (nietknięte)", "SELECT COUNT(*) FROM `contractors`"),
]


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def make_backup() -> None:
    """Backup rao_new do backup_pre_archive_split.sql przed migracją."""
    if BACKUP_FILE.exists() and BACKUP_FILE.stat().st_size > 0:
        log(f"BACKUP: pomijam (już istnieje, {BACKUP_FILE.stat().st_size} B): {BACKUP_FILE}")
        return
    log(f"BACKUP: mariadb-dump {DB_NAME} -> {BACKUP_FILE}")
    cmd = [
        "mariadb-dump",
        f"--user={DB_USER}",
        f"--password={DB_PASSWORD}",
        f"--host={DB_HOST}",
        f"--port={str(DB_PORT)}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--default-character-set=utf8mb4",
        DB_NAME,
    ]
    try:
        with open(BACKUP_FILE, "wb") as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, check=True)
        size = BACKUP_FILE.stat().st_size
        if size < 1000:
            raise RuntimeError(f"Backup zbyt mały ({size} B) — prawdopodobnie błąd")
        log(f"BACKUP: OK ({size} B)")
    except FileNotFoundError:
        raise RuntimeError("mariadb-dump nie znaleziony w PATH — zainstaluj MariaDB client")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mariadb-dump failed: {e.stderr.decode('utf-8', errors='replace')}")


async def pre_check_counts(conn) -> dict:
    """Zlicz legacy dane PRZED migracją (do raportu)."""
    counts = {}
    queries = {
        "contracts_total": "SELECT COUNT(*) FROM `contracts`",
        "positions_legacy": (
            "SELECT COUNT(*) FROM `contract_positions` "
            "WHERE contract_id IN (SELECT id FROM `contracts`)"
        ),
        "conditions_legacy": (
            "SELECT COUNT(*) FROM `position_conditions` "
            "WHERE position_id IN (SELECT cp.id FROM `contract_positions` cp "
            "WHERE cp.contract_id IN (SELECT id FROM `contracts`))"
        ),
        "service_fees_legacy": (
            "SELECT COUNT(*) FROM `contract_service_fees` "
            "WHERE contract_id IN (SELECT id FROM `contracts`)"
        ),
        "settlements_legacy": (
            "SELECT COUNT(*) FROM `contract_settlements` "
            "WHERE contract_id IN (SELECT id FROM `contracts`)"
        ),
        "articles_legacy": (
            "SELECT COUNT(*) FROM `articles` a WHERE a.id IN ("
            "SELECT DISTINCT cp.article_id FROM `contract_positions` cp "
            "WHERE cp.contract_id IN (SELECT id FROM `contracts`))"
        ),
        "categories_total": "SELECT COUNT(*) FROM `categories`",
        "orphan_positions": (
            "SELECT COUNT(*) FROM `contract_positions` cp "
            "LEFT JOIN `contracts` c ON cp.contract_id=c.id WHERE c.id IS NULL"
        ),
    }
    for name, q in queries.items():
        async with conn.cursor() as cur:
            await cur.execute(q)
            row = await cur.fetchone()
            counts[name] = row[0]
    return counts


async def run_statement(conn, label: str, sql: str) -> int:
    """Wykonaj statement, zwróć rowcount (dla INSERT/DELETE)."""
    async with conn.cursor() as cur:
        await cur.execute(sql)
        rc = cur.rowcount
    log(f"  {label}: rowcount={rc}")
    return rc


async def verify(conn) -> list:
    """Uruchom wszystkie weryfikacyjne COUNT-y."""
    results = []
    for label, q in VERIFY_QUERIES:
        async with conn.cursor() as cur:
            await cur.execute(q)
            row = await cur.fetchone()
            results.append((label, int(row[0])))
    return results


async def main(force: bool = False) -> int:
    log("=" * 72)
    log("RAO-P2-062 Faza 0 — Migracja legacy do archive_*" + (" [--force]" if force else ""))
    log("=" * 72)

    # 1. Backup (PRZED migracją — krytyczne)
    if not force:
        make_backup()

    # Połączenie bezpośrednio przez aiomysql (pełna kontrola nad transakcją)
    log(f"Łączenie z DB: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    conn = await aiomysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
    )

    pre_counts = {}
    inserted = {}
    deleted = {}
    results = []
    try:
        # 1. CREATE TABLE IF NOT EXISTS archive_* (DDL) — PRZED pre-check
        log("--- KROK 1/3: CREATE TABLE IF NOT EXISTS archive_* ---")
        for name, ddl in ALL_DDL:
            async with conn.cursor() as cur:
                await cur.execute(ddl)
            log(f"  CREATE TABLE IF NOT EXISTS {name}: OK")

        # Pre-check: zlicz legacy dane
        log("--- PRE-CHECK: zliczanie legacy danych ---")
        pre_counts = await pre_check_counts(conn)
        for k, v in pre_counts.items():
            log(f"  {k} = {v}")

        # Skip jeśli archiwum już ma dane (re-run po sukcesie lub --demo)
        # --force: zawsze archiwizuj aktualne contracts + usuń z demo tabel
        async with conn.cursor() as cur:
            await cur.execute("SELECT COUNT(*) FROM `archive_contracts`")
            ac = (await cur.fetchone())[0]
        if ac > 0 and not force:
            log(f"archive_contracts ma {ac} rekordów — migracja już wykonana. Weryfikuję...")
            results = await verify(conn)
            for label, val in results:
                log(f"  {label} = {val}")
            await conn.commit()
            return 0
        if ac > 0 and force:
            log(f"archive_contracts ma {ac} rekordów (--force: archiwizuję aktualne contracts)")

        if pre_counts["contracts_total"] == 0:
            log("Brak umów w bazie i archiwum puste — brak danych do migracji. Kończę.")
            await conn.commit()
            return 0

        # 2. INSERT IGNORE legacy -> archive_*
        log("--- KROK 2/3: INSERT IGNORE legacy -> archive_* ---")
        for name, sql in ALL_INSERTS:
            inserted[name] = await run_statement(conn, f"INSERT {name}", sql)

        # 3. DELETE legacy z tabel oryginalnych (kolejność cascade-safe)
        log("--- KROK 3/3: DELETE legacy z tabel oryginalnych ---")
        for name, sql in ALL_DELETES:
            deleted[name] = await run_statement(conn, f"DELETE {name}", sql)

        # 5. Weryfikacja (w tej samej transakcji, przed commit)
        log("--- WERYFIKACJA (przed commit) ---")
        results = await verify(conn)
        for label, val in results:
            log(f"  {label} = {val}")

        # Commit
        await conn.commit()
        log("COMMIT: migracja zatwierdzona.")

    except Exception as e:
        await conn.rollback()
        log(f"ROLLBACK: błąd migracji — {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

    # Raport
    log("")
    log("=" * 72)
    log("RAPORT MIGRACJI RAO-P2-062 FAZA 0")
    log("=" * 72)
    log(f"Backup: {BACKUP_FILE} ({BACKUP_FILE.stat().st_size} B)")
    log("")
    log("PRZED migracją (legacy dane w oryginalnych tabelach):")
    for k, v in pre_counts.items():
        log(f"  {k:30s} = {v}")
    log("")
    log("SKOPIOWANO do archive_* (INSERT IGNORE rowcount):")
    for name, rc in inserted.items():
        log(f"  {name:35s} = {rc}")
    log("")
    log("USUNIĘTO z oryginalnych (DELETE rowcount):")
    for name, rc in deleted.items():
        log(f"  {name:35s} = {rc}")
    log("")
    log("WERYFIKACJA PO MIGRACJI:")
    for label, val in results:
        log(f"  {label:50s} = {val}")
    log("")
    log("UWAGA: 3 osierocone pozycje (contract_id=9204 nie istnieje w contracts)")
    log("  pozostają w contract_positions — to pre-existing data issue, nie legacy.")
    log("  Nie zostały zmigrowane (poza scope) ani usunięte.")
    log("")
    log("NIE TKNIĘTE (współdzielone/zostają): articles, categories, contractors.")
    log("NIE USUNIĘTO kolumny is_legacy z contracts (to Faza 1 — backend).")
    log("=" * 72)
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="RAO — migracja legacy do archive_*")
    ap.add_argument("--force", action="store_true",
                    help="Wymuś archiwizację aktualnych contracts + DELETE z demo tabel (re-seed)")
    args = ap.parse_args()
    rc = asyncio.run(main(force=args.force))
    sys.exit(rc)
