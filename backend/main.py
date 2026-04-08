from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from auth.router import router as auth_router, admin_router
from contractors.router import router as contractors_router
from articles.router import router as articles_router
from contracts.router import router as contracts_router
from settings.router import router as settings_router
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

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sa.text(
            "ALTER TABLE service_fee_templates ADD COLUMN IF NOT EXISTS "
            "preset_id INT NULL REFERENCES fee_preset_groups(id) ON DELETE CASCADE"
        ))

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
app.include_router(reports_router)
app.include_router(integrations_router)
app.include_router(stats_router)
app.include_router(explorer_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
