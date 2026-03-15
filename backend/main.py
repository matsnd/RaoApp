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

app = FastAPI(
    title="RAO API",
    description="RAO - Wynajem maszyn budowlanych",
    version="1.0.0",
)

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


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
