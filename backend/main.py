from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from auth.router import router as auth_router, admin_router
from contractors.router import router as contractors_router
from articles.router import router as articles_router
from contracts.router import router as contracts_router
from settings.router import router as settings_router
from settlements.router import router as settlements_router
from reports.router import router as reports_router
from integrations.router import router as integrations_router
from stats.router import router as stats_router
from explorer.router import router as explorer_router
from database import engine, Base
import integrations.models  # RAO-P1-008

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
        # RAO-P1-008: strukturalizacja adresów - kod pocztowy + miasto
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "postal_code VARCHAR(20) NULL"
        ))
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "city VARCHAR(100) NULL"
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

    # FK + index dodawane w osobnych transakcjach (MariaDB nie wspiera ADD CONSTRAINT IF NOT EXISTS / CREATE INDEX IF NOT EXISTS)
    for ddl in [
        "ALTER TABLE service_fee_templates ADD CONSTRAINT fk_sft_article "
        "FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL",
        "CREATE INDEX idx_sft_article ON service_fee_templates(article_id)",
        # RAO-P1-017: FK self-ref + indeksy dla hierarchii kategorii i archiwum
        "ALTER TABLE categories ADD CONSTRAINT fk_category_parent "
        "FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL",
        "CREATE INDEX idx_categories_parent ON categories(parent_id)",
        "CREATE INDEX idx_articles_category_main ON articles(category_main)",
        "CREATE INDEX idx_articles_archival ON articles(is_archival)",
        # RAO-P1-008: indeksy dla strukturalizacji adresów
        "CREATE INDEX idx_contracts_postal_code ON contracts(postal_code)",
        "CREATE INDEX idx_contracts_city ON contracts(city)",
    ]:
        try:
            async with engine.begin() as conn2:
                await conn2.execute(sa.text(ddl))
        except Exception:
            pass  # constraint/index już istnieje

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, update, func
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
app.include_router(stats_router)
app.include_router(explorer_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
