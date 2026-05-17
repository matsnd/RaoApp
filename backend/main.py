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
        # service_fee_template_items utworzone przez Base.metadata.create_all (nowa tabela)

    # FK + index dodawane w osobnych transakcjach (MariaDB nie wspiera ADD CONSTRAINT IF NOT EXISTS / CREATE INDEX IF NOT EXISTS)
    for ddl in [
        "ALTER TABLE service_fee_templates ADD CONSTRAINT fk_sft_article "
        "FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL",
        "CREATE INDEX idx_sft_article ON service_fee_templates(article_id)",
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
