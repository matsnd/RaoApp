import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from config import settings

logger = logging.getLogger("rao.errors")

from auth.router import router as auth_router, admin_router
from contractors.router import router as contractors_router
from articles.router import router as articles_router
from contracts.router import router as contracts_router
from settings.router import router as settings_router
from settlements.router import router as settlements_router
from reports.router import router as reports_router
from integrations.router import router as integrations_router
from integrations.fakturownia.router import router as fakturownia_router
from stats.router import router as stats_router
from explorer.router import router as explorer_router
from reservations.router import router as reservations_router  # RAO-P1-015
from archive.router import router as archive_router  # RAO-P2-062 Faza 1
from database import engine, Base
import auth.models  # Auth tables
import integrations.models  # RAO-P1-008
import reservations.models  # RAO-P1-015
import deliveries.models  # RAO-P3-005
import contract_costs.models  # RAO-P3-005
import audit.models  # RAO-P3-005
import archive.models  # RAO-P2-062 Faza 1 — tabele archive_*

app = FastAPI(
    title="RAO API",
    description="RAO - Wynajem maszyn budowlanych",
    version="1.0.0",
    root_path="/rao/api",
    # RAO-P2-048: wyłącz publiczny Swagger/ReDoc poza dev mode (security hardening)
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
)


# RAO-P0-036: Global exception handler — nie ujawniaj stack trace klientowi
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Błąd serwera"},
    )


@app.on_event("startup")
async def startup_migrations():
    import sqlalchemy as sa
    from database import AsyncSessionLocal
    from settings.models import FeePresetGroup, ServiceFeeTemplate, Company
    import settlements.models  # RAO-P1-012
    import integrations.fakturownia.models  # RAO-P2-012

    # Upewnij się że istnieje domyślna firma (id=1) — FK dla FeePresetGroup
    # Musi być utworzone PRZED seedem presetów (RAO-P2-001 niżej).
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        has_company = (await db.execute(select(func.count()).select_from(Company))).scalar_one()
        if has_company == 0:
            db.add(Company(id=1, name="RAO — Wynajem Maszyn"))
            await db.commit()

    # RAO-P1-100: KISS seed service articles + Diesel/Elektryk/Wspólny presets (idempotent)
    async with AsyncSessionLocal() as db:
        from articles.models import Article
        from decimal import Decimal
        from datetime import datetime

        now = datetime.utcnow()

        # Service articles used by KISS presets
        SERVICE_ARTICLES = {
            "Transport": None,
            "Przegląd Diesel": None,
            "Przegląd Elektryk": None,
            "Czyszczenie": None,
            "Tankowanie": None,
            "Przestój": None,
            "Serwis": None,
        }
        for art_name in SERVICE_ARTICLES:
            result = await db.execute(
                sa.select(Article).where(Article.name == art_name, Article.is_service == True)
            )
            art = result.scalar_one_or_none()
            if not art:
                art = Article(
                    name=art_name,
                    is_service=True,
                    article_type="usluga_dodatkowa",
                    created_at=now,
                    updated_at=now,
                )
                db.add(art)
                await db.flush()
            SERVICE_ARTICLES[art_name] = art.id

        # Common Wspólny fees (name, description, article_name, amount_from, amount_to, unit)
        WSPOLNY_FEES = [
            ("Transport", "1 200,00 zł dostawa / 1 200,00 zł odbiór", "Transport", Decimal("1200.00"), Decimal("1200.00"), "dostawa"),
            ("Czyszczenie maszyny (zabrudzenia ponadnormatywne)", "wycena indywidualna", "Czyszczenie", None, None, None),
            ("Usługa tankowania", "200,00 zł (plus koszt paliwa)", "Tankowanie", Decimal("200.00"), None, "tankowanie"),
            ("Ponadnormatywny przestój transportu", "200,00 zł / h - 300,00 zł / h", "Przestój", Decimal("200.00"), Decimal("300.00"), "h"),
            ("Nieuzasadnione wezwanie serwisowe", "280,00 zł (plus transport)", "Serwis", Decimal("280.00"), None, "wizyta"),
        ]

        PRESETS = [
            ("Najem — Wspólny", "S", True, "Wspólny zestaw usług dla umów najmu", WSPOLNY_FEES),
            ("Najem — Diesel", "S", False, "Wspólny + przegląd maszyny diesla 150,00 zł", [
                ("Transport", "1 200,00 zł dostawa / 1 200,00 zł odbiór", "Transport", Decimal("1200.00"), Decimal("1200.00"), "dostawa"),
                ("Przegląd techniczny i czyszczenie maszyny", "150,00 zł", "Przegląd Diesel", Decimal("150.00"), None, "sztuka"),
            ] + list(WSPOLNY_FEES[1:])),
            ("Najem — Elektryk", "S", False, "Wspólny + przegląd maszyny elektrycznej 90,00 zł", [
                ("Transport", "1 200,00 zł dostawa / 1 200,00 zł odbiór", "Transport", Decimal("1200.00"), Decimal("1200.00"), "dostawa"),
                ("Przegląd techniczny, ładowanie akumulatorów oraz czyszczenie maszyny", "90,00 zł", "Przegląd Elektryk", Decimal("90.00"), None, "sztuka"),
            ] + list(WSPOLNY_FEES[1:])),
            ("Usługa — Wspólny", "U", True, "Wspólny zestaw usług dla umów usługowych", WSPOLNY_FEES),
        ]

        for idx, (group_name, contract_type, is_default, group_desc, fees) in enumerate(PRESETS):
            # Only one default per contract_type
            if is_default:
                await db.execute(
                    sa.update(FeePresetGroup)
                    .where(FeePresetGroup.contract_type == contract_type)
                    .where(FeePresetGroup.name != group_name)
                    .values(is_default=False)
                )
            result = await db.execute(sa.select(FeePresetGroup).where(FeePresetGroup.name == group_name))
            group = result.scalar_one_or_none()
            if not group:
                group = FeePresetGroup(
                    company_id=1,
                    name=group_name,
                    contract_type=contract_type,
                    description=group_desc,
                    is_default=is_default,
                    sort_order=idx,
                )
                db.add(group)
                await db.flush()
            else:
                group.contract_type = contract_type
                group.description = group_desc
                group.is_default = is_default
                group.sort_order = idx

            for sort_order, (fee_name, fee_desc, art_name, amt_from, amt_to, unit) in enumerate(fees, start=1):
                article_id = SERVICE_ARTICLES.get(art_name)
                result = await db.execute(
                    sa.select(ServiceFeeTemplate).where(
                        ServiceFeeTemplate.preset_id == group.id,
                        ServiceFeeTemplate.name == fee_name,
                    )
                )
                tpl = result.scalar_one_or_none()
                if not tpl:
                    tpl = ServiceFeeTemplate(
                        company_id=1,
                        preset_id=group.id,
                        contract_type=contract_type,
                        sort_order=sort_order,
                        name=fee_name,
                        description=fee_desc,
                        amount_from=amt_from,
                        amount_to=amt_to,
                        unit=unit,
                        is_active=True,
                        article_id=article_id,
                    )
                    db.add(tpl)
                else:
                    tpl.sort_order = sort_order
                    tpl.description = fee_desc
                    tpl.amount_from = amt_from
                    tpl.amount_to = amt_to
                    tpl.unit = unit
                    tpl.is_active = True
                    tpl.article_id = article_id
        await db.commit()

    # RAO-P3-002: katalog na logo firmy (startup guard)
    os.makedirs("static/logos", exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sa.text(
            "ALTER TABLE service_fee_templates ADD COLUMN IF NOT EXISTS "
            "preset_id INT NULL REFERENCES fee_preset_groups(id) ON DELETE CASCADE"
        ))
        # RAO-P1-011: zesłownikowanie usług dodatkowych z artykułami
        await conn.execute(sa.text(
            "ALTER TABLE service_fee_templates ADD COLUMN IF NOT EXISTS "
            "article_id INT NULL"
        ))
        # RAO-P1-014: checkbox podpisów na stronie 1
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "signatures_on_page1 BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "hide_delivery_address BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        # RAO-P1-017: hierarchia kategorii 3-poziomowa + flaga archiwalna + atrybuty techniczne
        await conn.execute(sa.text(
            "ALTER TABLE categories ADD COLUMN IF NOT EXISTS "
            "parent_id INT NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE categories ADD COLUMN IF NOT EXISTS "
            "level ENUM('main','sub1','sub2','sub3') NOT NULL DEFAULT 'main'"
        ))
        # RAO-P0-054: Collation polish_ci dla kategorii (normalizacja diakrytyk + spacji)
        try:
            await conn.execute(sa.text(
                "ALTER TABLE categories CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci"
            ))
        except Exception:
            pass  # Już jest polish_ci lub MariaDB nie wspiera — idempotentne
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "category_main VARCHAR(100) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "category_sub1 VARCHAR(100) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "category_sub2 VARCHAR(100) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "category_sub3 VARCHAR(100) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "is_archival BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "technical_attributes JSON NULL"
        ))
        # RAO: dedykowane kolumny numeryczne dla filtrów statystyk (zastępują string-values w technical_attributes JSON)
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "zasieg_m DECIMAL(8,2) NULL COMMENT 'Zasięg w metrach'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "udzwig_t DECIMAL(8,2) NULL COMMENT 'Udźwig w tonach'"
        ))
        # RAO-P1-012: tabela rozliczeń umów (contract_settlements)
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS contract_settlements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_id INT NOT NULL,
                position_id INT NULL,
                service_fee_id INT NULL,
                cost_client DECIMAL(18,2) NULL,
                cost_company DECIMAL(18,2) NULL,
                notes TEXT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
                FOREIGN KEY (position_id) REFERENCES contract_positions(id) ON DELETE CASCADE,
                FOREIGN KEY (service_fee_id) REFERENCES service_fee_templates(id) ON DELETE SET NULL
            )
        """))
        # RAO-P3-014: Fix placeholders $1/$2 in service_fee_templates descriptions
        await conn.execute(sa.text("""
            UPDATE service_fee_templates 
            SET description = REPLACE(
                REPLACE(
                    description,
                    '$1 zł',
                    CONCAT(IFNULL(amount_from, ''), ' zł')
                ),
                '$2 zł',
                CONCAT(IFNULL(amount_to, ''), ' zł')
            )
            WHERE description LIKE '%$1%' OR description LIKE '%$2%'
        """))
        # Fix placeholders $1/$2 in contract_service_fees descriptions (existing contracts)
        await conn.execute(sa.text("""
            UPDATE contract_service_fees 
            SET description = REPLACE(
                REPLACE(
                    description,
                    '$1 zł',
                    CONCAT(IFNULL(amount_from, ''), ' zł')
                ),
                '$2 zł',
                CONCAT(IFNULL(amount_to, ''), ' zł')
            )
            WHERE description LIKE '%$1%' OR description LIKE '%$2%'
        """))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "dodatki TEXT NULL COMMENT 'Dodatkowe akcesoria / wyposażenie'"
        ))
        # RAO-P1-030: maszyna zewnętrzna (nie wliczana do floty własnej)
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "is_external TINYINT(1) NOT NULL DEFAULT 0"
        ))
        # RAO-P2-022: status rozliczenia umowy
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "is_settled TINYINT(1) NOT NULL DEFAULT 0"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "settled_at DATETIME NULL"
        ))
        # RAO-P1-008: strukturalizacja adresów - kod pocztowy + miasto
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "postal_code VARCHAR(20) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "city VARCHAR(100) NULL"
        ))
        # RAO-P2-028: FK do postal_codes (deterministyczna lokalizacja PNA)
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "postal_code_id INT NULL COMMENT 'RAO-P2-028: FK do postal_codes'"
        ))
        # FK + index (try/except bo MariaDB <10.6 nie wspiera IF NOT EXISTS dla CONSTRAINT)
        try:
            await conn.execute(sa.text(
                "ALTER TABLE contracts ADD CONSTRAINT fk_contracts_postal_code "
                "FOREIGN KEY (postal_code_id) REFERENCES postal_codes(id) ON DELETE SET NULL"
            ))
        except Exception:
            pass  # FK już istnieje
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_postal_code_id ON contracts(postal_code_id)"
        ))
        # RAO-P2-060: indeksy dla statystyk rozliczeń (source + settled_at)
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_settlements_source ON contract_settlements(source)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_settlements_settled_at ON contract_settlements(settled_at)"
        ))
        # RAO-P2-015: tabela postal_codes (słownik kodów pocztowych)
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS postal_codes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                postal_code VARCHAR(10) NOT NULL UNIQUE,
                city VARCHAR(100) NOT NULL,
                wojewodztwo VARCHAR(50) NULL,
                powiat VARCHAR(100) NULL,
                gmina VARCHAR(100) NULL,
                INDEX idx_postal_codes_code (postal_code),
                INDEX idx_postal_codes_city (city),
                INDEX idx_postal_codes_wojewodztwo (wojewodztwo)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
              COMMENT='RAO-P2-015: Słownik kodów pocztowych Polski'
        """))
        # Migracja istniejącej tabeli postal_codes (jeśli istnieje ze starym schematem)
        await conn.execute(sa.text(
            "ALTER TABLE postal_codes ADD COLUMN IF NOT EXISTS "
            "powiat VARCHAR(100) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE postal_codes ADD COLUMN IF NOT EXISTS "
            "gmina VARCHAR(100) NULL"
        ))
        # RAO-P2-028: indeksy dla statystyk hierarchicznych
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_postal_codes_gmina ON postal_codes(gmina)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_postal_codes_powiat ON postal_codes(powiat)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_postal_codes_city_gmina ON postal_codes(city, gmina)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_postal_codes_woj_pow ON postal_codes(wojewodztwo, powiat)"
        ))
        # RAO-P2-012: integracja Fakturownia — singleton settings + mapping produktu w articles
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS fakturownia_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                enabled BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Czy integracja włączona',
                api_token_ciphertext VARBINARY(512) NULL COMMENT 'API token zaszyfrowany Fernet',
                api_token_preview VARCHAR(32) NULL COMMENT 'Preview tokena np. tk_****1234',
                domain_subdomain VARCHAR(100) NULL COMMENT 'Subdomena np. toolsmart',
                api_token_updated_at DATETIME NULL COMMENT 'Kiedy zaktualizowano token',
                api_token_updated_by INT NULL COMMENT 'FK users.id - kto zaktualizował',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_fakturownia_settings_user FOREIGN KEY (api_token_updated_by)
                    REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
              COMMENT='RAO-P2-012: Singleton konfiguracji integracji Fakturownia'
        """))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "fakturownia_product_id BIGINT NULL COMMENT 'RAO-P2-012: ID produktu w Fakturownia (1:N globalny)'"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_fakturownia_product "
            "ON articles(fakturownia_product_id)"
        ))
        # RAO-P2-058: snapshot metadanych z Fakturownia na artykułach
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "fakturownia_tax_rate VARCHAR(10) NULL COMMENT 'RAO-P2-058: Stawka VAT z FA (snapshot)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "fakturownia_gtu_code VARCHAR(20) NULL COMMENT 'RAO-P2-058: Kod GTU z FA (snapshot)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS "
            "fakturownia_pkwiu VARCHAR(50) NULL COMMENT 'RAO-P2-058: PKWiU z FA (snapshot)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "oid VARCHAR(40) NULL COMMENT 'RAO-P2-012: Numer zamówienia w Fakturownia'"
        ))
        # C-2 fix: ContractorAddress.email VARCHAR(20)→VARCHAR(100) (audit 2026-05-19)
        await conn.execute(sa.text(
            "ALTER TABLE contractor_addresses MODIFY COLUMN email VARCHAR(100) NULL"
        ))
        # RAO-P2-005: geokodowanie adresów - latitude/longitude
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "latitude DECIMAL(10,8) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "longitude DECIMAL(11,8) NULL"
        ))
        # RAO-P0-030: UNIQUE constraint na contracts.number (zapobiega duplikatom)
        # Idempotentne: CREATE UNIQUE INDEX IF NOT EXISTS
        await conn.execute(sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_contracts_number ON contracts(number)"
        ))
        # RAO-P1-038: indeksy na często filtrowanych kolumnach contracts
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_is_settled ON contracts(is_settled)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_created_at ON contracts(created_at)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_salesperson_id ON contracts(salesperson_id)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_print_date ON contracts(print_date)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_delivery_date ON contracts(date_to)"
        ))
        # RAO-P3-002: logo firmy — ścieżka do pliku statycznego
        await conn.execute(sa.text(
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS logo_path VARCHAR(500) NULL"
        ))
        # RAO-P1-005: elastyczne widełki cenowe - period_from/period_to
        await conn.execute(sa.text(
            "ALTER TABLE position_conditions ADD COLUMN IF NOT EXISTS "
            "period_from INT NULL COMMENT 'RAO-P1-005: elastyczne widełki (od)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE position_conditions ADD COLUMN IF NOT EXISTS "
            "period_to INT NULL COMMENT 'RAO-P1-005: elastyczne widełki (do)'"
        ))
        # Migracja danych: RAO-P0-048 popraw kaskadowe period_from/period_to
        # (zamiast naiwnego period_from=1 dla każdego rekordu)
        async with AsyncSessionLocal() as db:
            from contracts.service import contract_service
            try:
                await contract_service.migrate_position_condition_periods(db)
            except Exception as exc:
                logger.exception("RAO-P0-048 migrate_position_condition_periods failed: %s", exc)
                await db.rollback()
        # RAO Phase 1 (2026-07-05): usuwanie martwych kolumn/tabeli z dev/test DB
        # DROP IF EXISTS w try/except — MariaDB <10.6 wymaga cichego fallbacku

        # service_fee_templates.default_price
        try:
            await conn.execute(sa.text("ALTER TABLE service_fee_templates DROP COLUMN IF EXISTS default_price"))
        except Exception:
            pass

        # contract_service_fees.article_id / default_price
        # FK first — SQLAlchemy autogenerowała różne nazwy FK na przestrzeni czasu
        for fk in ("1", "fk_contract_service_fees_article_id"):
            try:
                await conn.execute(sa.text(f"ALTER TABLE contract_service_fees DROP FOREIGN KEY IF EXISTS `{fk}`"))
            except Exception:
                pass
        try:
            await conn.execute(sa.text("ALTER TABLE contract_service_fees DROP COLUMN IF EXISTS article_id"))
        except Exception:
            pass
        try:
            await conn.execute(sa.text("ALTER TABLE contract_service_fees DROP COLUMN IF EXISTS default_price"))
        except Exception:
            pass

        # contract_positions.costs
        try:
            await conn.execute(sa.text("ALTER TABLE contract_positions DROP COLUMN IF EXISTS costs"))
        except Exception:
            pass

        # position_conditions.rate_type_id / description
        # FK first — SQLAlchemy mogła wygenerować nazwę `fk_position_conditions_rate_type_id` zamiast `fk_cond_rate_type`
        for fk in ("fk_cond_rate_type", "fk_position_conditions_rate_type_id"):
            try:
                await conn.execute(sa.text(f"ALTER TABLE position_conditions DROP FOREIGN KEY IF EXISTS `{fk}`"))
            except Exception:
                pass
        try:
            await conn.execute(sa.text("ALTER TABLE position_conditions DROP COLUMN IF EXISTS rate_type_id"))
        except Exception:
            pass
        try:
            await conn.execute(sa.text("ALTER TABLE position_conditions DROP COLUMN IF EXISTS description"))
        except Exception:
            pass

        # service_fee_template_items
        try:
            await conn.execute(sa.text("DROP TABLE IF EXISTS service_fee_template_items"))
        except Exception:
            pass
        # RAO-P1-012: contract_settlements - rozliczenia umów (koszty klient vs firma)
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS contract_settlements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_id INT NOT NULL COMMENT 'FK contracts.id',
                position_id INT NULL COMMENT 'FK contract_positions.id',
                service_fee_id INT NULL COMMENT 'FK contract_service_fees.id',
                cost_client DECIMAL(18,2) NULL COMMENT 'Koszt dla klienta',
                cost_company DECIMAL(18,2) NULL COMMENT 'Koszt dla firmy',
                notes TEXT NULL COMMENT 'Uwagi do rozliczenia',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_contract_settlements_contract FOREIGN KEY (contract_id)
                    REFERENCES contracts(id) ON DELETE CASCADE,
                CONSTRAINT fk_contract_settlements_position FOREIGN KEY (position_id)
                    REFERENCES contract_positions(id) ON DELETE CASCADE,
                CONSTRAINT fk_contract_settlements_service_fee FOREIGN KEY (service_fee_id)
                    REFERENCES contract_service_fees(id) ON DELETE CASCADE,
                INDEX idx_contract_settlements_contract (contract_id),
                INDEX idx_contract_settlements_position (position_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
              COMMENT='RAO-P1-012: Rozliczenia umów - koszty klient vs firma'
        """))
        # RAO-P2-012: service_fee_id w contract_settlements dla rozliczeń usług dodatkowych
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "service_fee_id INT NULL"
        ))
        # RAO-P2-032: settled_at (data rozliczenia z legacy rozliczenie.data lub Fakturownia)
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "settled_at DATE NULL COMMENT 'RAO-P2-032: Data rozliczenia'"
        ))
        # RAO-P2-032: source (legacy/fakturownia/manual) — identyfikacja pochodzenia kwoty
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "source VARCHAR(20) NULL DEFAULT 'manual' COMMENT 'RAO-P2-032: legacy/fakturownia/manual'"
        ))
        # RAO-P2-032: UNIQUE constraint — idempotentny import rozliczenie (zapobiega duplikatom)
        try:
            await conn.execute(sa.text(
                "ALTER TABLE contract_settlements ADD UNIQUE INDEX IF NOT EXISTS "
                "uq_settlements_contract_pos_fee_date "
                "(contract_id, position_id, service_fee_id, settled_at)"
            ))
        except Exception:
            pass  # MariaDB <10.6 nie wspiera IF NOT EXISTS na UNIQUE INDEX
        # RAO Faza 2a (opcja E): unmapped settlements z Fakturownia — pozycje FA nieobecne w umowie
        # position_id=NULL + service_fee_id=NULL + snapshot nazwy (NIE tworzymy artykułu on-the-fly)
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "article_name_snapshot VARCHAR(255) NULL "
            "COMMENT 'Snapshot nazwy pozycji z FA (gdy position_id=NULL)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "fakturownia_product_id BIGINT NULL "
            "COMMENT 'ID produktu FA (grupowanie w analytics, identyfikacja duplikatów)'"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
            "fakturownia_invoice_number VARCHAR(50) NULL "
            "COMMENT 'Numer faktury FA (wydzielony z notes dla query)'"
        ))
        # Generated column (STORED) — idempotentność unmapped importu.
        # MariaDB 10.2+ wspiera GENERATED ALWAYS AS ... STORED; IF NOT EXISTS od 10.6.
        # try/except — fallback gdy kolumna już istnieje (MariaDB <10.6 bez IF NOT EXISTS).
        try:
            await conn.execute(sa.text(
                "ALTER TABLE contract_settlements ADD COLUMN IF NOT EXISTS "
                "unmapped_key VARCHAR(100) GENERATED ALWAYS AS ("
                "CASE WHEN position_id IS NULL AND service_fee_id IS NULL "
                "THEN CONCAT('unmapped:', IFNULL(fakturownia_product_id,0), ':', IFNULL(fakturownia_invoice_number,'')) "
                "ELSE NULL END) STORED COMMENT 'Klucz deduplikacji unmapped (NULL dla mapped)'"
            ))
        except Exception:
            pass  # kolumna już istnieje (MariaDB <10.6 bez IF NOT EXISTS dla generated)
        # UNIQUE index na unmapped_key — NULL w UNIQUE dozwolony wielokrotnie (mapped nie koliduje)
        try:
            await conn.execute(sa.text(
                "ALTER TABLE contract_settlements ADD UNIQUE INDEX IF NOT EXISTS "
                "uq_settlements_unmapped_key (unmapped_key)"
            ))
        except Exception:
            pass  # MariaDB <10.6 nie wspiera IF NOT EXISTS na UNIQUE INDEX
        # RAO-P2-032: tabela _import_errors — logowanie orphaned settlements (QA edge #1)
        await conn.execute(sa.text(
            "CREATE TABLE IF NOT EXISTS _import_errors ("
            " id INT AUTO_INCREMENT PRIMARY KEY,"
            " source VARCHAR(50) NOT NULL,"
            " raw_data TEXT NOT NULL,"
            " error_message TEXT NOT NULL,"
            " created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci"
            " COMMENT='RAO-P2-032: Log błędów importu (orphaned settlements itp.)'"
        ))
        # RAO-P1-055: Migracja branch_id z suffixu "G" w numerze umowy (Gdańsk).
        # Idempotentna: WHERE branch_id IS NULL — kolejne uruchomienia nie modyfikują.
        # Numer umowy format: "{type}{auto:03d}/{year}{suffix}" gdzie suffix="G" dla GDAŃSK.
        # 1) Umowy z suffixem "G" → przypisz do oddziału GDAŃSK (case-insensitive).
        await conn.execute(sa.text(
            "UPDATE contracts c SET c.branch_id = ("
            "  SELECT b.id FROM branches b WHERE UPPER(b.name) = 'GDAŃSK' LIMIT 1"
            ") WHERE c.number LIKE '%G' AND c.branch_id IS NULL"
            "  AND EXISTS (SELECT 1 FROM branches b WHERE UPPER(b.name) = 'GDAŃSK')"
        ))
        # 2) Umowy BEZ suffixu "G" → przypisz do domyślnego oddziału (najniższe id,
        #    który NIE jest GDAŃSK = oddział główny/siedziba). Idempotentne.
        await conn.execute(sa.text(
            "UPDATE contracts c SET c.branch_id = ("
            "  SELECT b.id FROM branches b WHERE UPPER(b.name) <> 'GDAŃSK' ORDER BY b.id LIMIT 1"
            ") WHERE c.number NOT LIKE '%G' AND c.branch_id IS NULL"
            "  AND EXISTS (SELECT 1 FROM branches b WHERE UPPER(b.name) <> 'GDAŃSK')"
        ))
        # RAO-P1-055: indeks na branch_id dla statystyk /stats/by-branch (WHERE + JOIN)
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_branch_id ON contracts(branch_id)"
        ))

    # FK + index dodawane z IF NOT EXISTS (MariaDB 10.0.2+ dla FK, 10.0.9+ dla indeksów)
    # RAO-P2-012 spike: commented out FK constraints due to MariaDB version compatibility (not in scope)
    async with engine.begin() as conn2:
        # await conn2.execute(sa.text(
        #     "ALTER TABLE service_fee_templates ADD CONSTRAINT IF NOT EXISTS fk_sft_article "
        #     "FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL"
        # ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_sft_article ON service_fee_templates(article_id)"
        ))
        # RAO-P1-017: FK self-ref + indeksy dla hierarchii kategorii i archiwum
        # await conn2.execute(sa.text(
        #     "ALTER TABLE categories ADD CONSTRAINT IF NOT EXISTS fk_category_parent "
        #     "FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL"
        # ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)"
        ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_category_main ON articles(category_main)"
        ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_archival ON articles(is_archival)"
        ))
        # RAO-P1-008: indeksy dla strukturalizacji adresów
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_postal_code ON contracts(postal_code)"
        ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_city ON contracts(city)"
        ))
        # RAO-P2-012: index na mapping FA produktu w artykułach (lookup po fakturownia_product_id)
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_fakturownia_product "
            "ON articles(fakturownia_product_id)"
        ))
        # RAO: indeksy na zasieg_m / udzwig_t dla filtrów >=/<= w statystykach
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_zasieg ON articles(zasieg_m)"
        ))
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_udzwig ON articles(udzwig_t)"
        ))
        # RAO-P1-030: indeks na is_external
        await conn2.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_articles_external ON articles(is_external)"
        ))

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, update, func
        from settings.models import Company
        # Upewnij się że istnieje domyślna firma (id=1) zanim dodamy FeePresetGroup (FK company_id)
        has_company = (await db.execute(select(func.count()).select_from(Company))).scalar_one()
        if has_company == 0:
            db.add(Company(id=1, name="RAO — Wynajem Maszyn"))
            await db.commit()
        has_presets = (await db.execute(select(func.count()).select_from(FeePresetGroup))).scalar_one()
        if has_presets == 0:
            for ct, label in (("S", "Domyślny — najem"), ("U", "Domyślny — usługa")):
                grp = FeePresetGroup(company_id=1, name=label, contract_type=ct, is_default=True, sort_order=0)
                db.add(grp)
                await db.flush()
                await db.execute(
                    update(ServiceFeeTemplate)
                    .where(ServiceFeeTemplate.contract_type == ct)
                    .where(ServiceFeeTemplate.preset_id == None)
                    .values(preset_id=grp.id, is_active=True)
                )
            await db.commit()

        # RAO-P2-028 backfill: ustaw postal_code_id dla umów z NULL FK,
        # gdzie contracts.postal_code istnieje w słowniku postal_codes.
        # Idempotentne — UPDATE tylko wiersze z postal_code_id IS NULL.
        from sqlalchemy import text as sa_text
        backfilled = await db.execute(sa_text(
            "UPDATE contracts c "
            "JOIN postal_codes p ON c.postal_code = p.postal_code "
            "SET c.postal_code_id = p.id "
            "WHERE c.postal_code_id IS NULL "
            "  AND c.postal_code IS NOT NULL "
            "  AND c.postal_code <> ''"
        ))
        if backfilled.rowcount:
            await db.commit()
            print(f"[startup] Backfill postal_code_id: {backfilled.rowcount} umów zaktualizowanych")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(contractors_router)
app.include_router(articles_router)
app.include_router(contracts_router)
app.include_router(settings_router)
app.include_router(settlements_router)
app.include_router(reports_router)
app.include_router(integrations_router)
app.include_router(fakturownia_router)
app.include_router(stats_router)
app.include_router(explorer_router)
app.include_router(reservations_router)  # RAO-P1-015
app.include_router(archive_router)  # RAO-P2-062 Faza 1

# RAO-P3-002: serwowanie statycznych plików (loga firmy itp.)
# Katalog tworzony powyżej (os.makedirs), mount musi być po include_router
os.makedirs("static/logos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static", html=False), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/version")
async def version():
    """Zwraca informacje o wersji aplikacji (git commit hash)."""
    import subprocess
    try:
        # Próba pobrania git hash z repo
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        git_short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        git_branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=os.path.dirname(__file__),
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except Exception:
        # Fallback: czytaj z pliku VERSION w root projektu
        version_file = os.path.join(os.path.dirname(__file__), "..", "VERSION")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Parse simple format
                git_hash = "unknown"
                git_short = "unknown"
                git_branch = "unknown"
                for line in content.split("\n"):
                    if line.startswith("Commit:"):
                        git_hash = line.split(":", 1)[1].strip()
                    elif line.startswith("Short:"):
                        git_short = line.split(":", 1)[1].strip()
                    elif line.startswith("Branch:"):
                        git_branch = line.split(":", 1)[1].strip()
        else:
            git_hash = "unknown"
            git_short = "unknown"
            git_branch = "unknown"
    
    return {
        "app": "RAO API",
        "version": "1.0.0",
        "git_hash": git_hash,
        "git_short": git_short,
        "git_branch": git_branch
    }
