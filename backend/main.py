import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings

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
from database import engine, Base
import auth.models  # Auth tables
import integrations.models  # RAO-P1-008
import reservations.models  # RAO-P1-015
import deliveries.models  # RAO-P3-005
import contract_costs.models  # RAO-P3-005
import audit.models  # RAO-P3-005

app = FastAPI(
    title="RAO API",
    description="RAO - Wynajem maszyn budowlanych",
    version="1.0.0",
    root_path="/rao/api",
)


@app.on_event("startup")
async def startup_migrations():
    import sqlalchemy as sa
    from database import AsyncSessionLocal
    from settings.models import FeePresetGroup, ServiceFeeTemplate
    import settlements.models  # RAO-P1-012
    import integrations.fakturownia.models  # RAO-P2-012

    # RAO-P2-001: seed default fees for contract type S (najmu)
    async with AsyncSessionLocal() as db:
        # Check if default preset for type S exists
        existing = await db.execute(
            sa.select(FeePresetGroup).where(
                FeePresetGroup.contract_type == 'S',
                FeePresetGroup.is_default == True
            )
        )
        if not existing.scalar_one_or_none():
            # Create default preset for type S
            default_preset = FeePresetGroup(
                company_id=1,
                name="Domyślne usługi dodatkowe (najmu)",
                contract_type='S',
                description="Transport, czyszczenie, tankowanie - domyślne dla umów najmu",
                is_default=True,
                sort_order=0
            )
            db.add(default_preset)
            await db.flush()

            # Add default fees in specified order
            default_fees = [
                {"name": "Transport", "amount_from": 500.00, "amount_to": None, "unit": "dostawa", "description": "500.00 zł / dostawa / 500.00 zł odbiór", "sort_order": 1},
                {"name": "Czyszczenie maszyny po wynajmie (zabrudzenia drobne)", "amount_from": 150.00, "amount_to": 400.00, "unit": "sztuka", "description": None, "sort_order": 2},
                {"name": "Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne)", "amount_from": 400.00, "amount_to": 1500.00, "unit": "sztuka", "description": None, "sort_order": 3},
                {"name": "Usługa tankowania", "amount_from": 200.00, "amount_to": None, "unit": "tankowanie", "description": "plus koszt paliwa", "sort_order": 4},
                {"name": "Ponadnormatywny przestój transportu", "amount_from": 200.00, "amount_to": 300.00, "unit": "godzina", "description": None, "sort_order": 5},
                {"name": "Nieuzasadnione wezwanie serwisowe", "amount_from": 280.00, "amount_to": None, "unit": "wizyta", "description": "plus transport", "sort_order": 6},
            ]
            for fee_data in default_fees:
                db.add(ServiceFeeTemplate(
                    company_id=1,
                    preset_id=default_preset.id,
                    contract_type='S',
                    name=fee_data["name"],
                    amount_from=fee_data["amount_from"],
                    amount_to=fee_data["amount_to"],
                    unit=fee_data["unit"],
                    description=fee_data["description"],
                    is_active=True,
                    sort_order=fee_data["sort_order"]
                ))
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
        await conn.execute(sa.text(
            "ALTER TABLE service_fee_templates ADD COLUMN IF NOT EXISTS "
            "default_price DECIMAL(18,2) NULL"
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
                FOREIGN KEY (service_fee_id) REFERENCES contract_service_fees(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_polish_ci
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
        # RAO-P3-002: logo firmy — ścieżka do pliku statycznego
        await conn.execute(sa.text(
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS logo_path VARCHAR(500) NULL"
        ))
        # service_fee_template_items utworzone przez Base.metadata.create_all (nowa tabela)
        # RAO-P1-014: tabela service_hours dla ewidencji godzin operatora
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS service_hours (
                id INT AUTO_INCREMENT PRIMARY KEY,
                position_id INT NOT NULL COMMENT 'Pozycja umowy (dla umów typu U)',
                service_date DATE NOT NULL COMMENT 'Data wykonania usługi',
                time_from TIME NULL COMMENT 'Godzina rozpoczęcia',
                time_to TIME NULL COMMENT 'Godzina zakończenia',
                notes VARCHAR(500) NULL COMMENT 'Uwagi',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_service_hours_position FOREIGN KEY (position_id)
                    REFERENCES contract_positions(id) ON DELETE CASCADE,
                INDEX idx_service_hours_position (position_id),
                INDEX idx_service_hours_date (service_date)
            ) ENGINE=InnoDB COMMENT='Godziny pracy operatora dla umów usługowych'
        """))
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
        # RAO-P1-011: article_id i default_price w contract_service_fees (kopia z szablonu)
        await conn.execute(sa.text(
            "ALTER TABLE contract_service_fees ADD COLUMN IF NOT EXISTS "
            "article_id INT NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contract_service_fees ADD COLUMN IF NOT EXISTS "
            "default_price DECIMAL(18,2) NULL"
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
