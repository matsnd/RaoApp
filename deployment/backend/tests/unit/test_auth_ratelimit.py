"""RAO-P2-047: testy rate limitingu na /auth/login + /auth/forgot-password.

Testy uzywaja FastAPI TestClient na izolowanej mini-aplikacji z routerem auth,
aby nie wymagac realnej bazy danych (login/forgot-password mockowane).

Pokrycie:
- happy path: <5 prob przechodzi
- edge case: 6. proba -> 429 + header Retry-After
- header X-Forwarded-For honorowany
- reset_rate_limit czyści stan
- RAO-P2-048: docs_url=None gdy environment != development
"""
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _build_app(monkeypatch_env: str = "development") -> FastAPI:
    """Izolowana app z routerem auth (bez DB startup, bez root_path)."""
    # Wymuszamy environment przed importem config (modul jest juz zaladowany,
    # wiec nadpisujemy pole bezposrednio na instancji settings).
    from config import settings
    settings.RAO_ENV = monkeypatch_env

    # Reset licznika rate-limit przed kazdym testem
    from auth import rate_limit
    rate_limit.reset_rate_limit()

    app = FastAPI(
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
        openapi_url="/openapi.json" if settings.environment == "development" else None,
    )
    app.include_router(__import__("auth.router", fromlist=["router"]).router)
    return app


@pytest.fixture
def client():
    app = _build_app("development")
    # Mockujemy serwis auth aby nie dotykac DB
    from auth import service as svc

    async def fake_login(db, login, password):
        from auth.models import User
        from fastapi import HTTPException
        if password == "bad":
            raise HTTPException(401, "Nieprawidlowy login lub haslo")
        user = User()
        user.id = 1
        user.login = login
        user.email = "x@x.pl"
        user.role = "admin"
        user.is_active = True
        user.must_change_password = False
        return "tok", user

    async def fake_forgot(db, email):
        return None

    svc.auth_service.login = fake_login  # type: ignore[attr-defined]
    svc.auth_service.forgot_password = fake_forgot  # type: ignore[attr-defined]
    return TestClient(app)


# ── Rate limiting ────────────────────────────────────────────────────────────

def test_login_under_limit_passes(client):
    """Happy path: 5 prob (limit) przechodzi, 6. -> 429."""
    payload = {"login": "admin", "password": "good"}
    for i in range(5):
        r = client.post("/auth/login", json=payload)
        assert r.status_code == 200, f"prob {i+1}: {r.status_code} {r.text}"
    # 6. proba -> 429
    r = client.post("/auth/login", json=payload)
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    assert int(r.headers["Retry-After"]) >= 1


def test_login_429_has_retry_after(client):
    r = client.post("/auth/login", json={"login": "admin", "password": "bad"})
    assert r.status_code == 401  # bad password -> 401 (ale liczone do limitu)
    # zapelnij limit
    for _ in range(4):
        client.post("/auth/login", json={"login": "admin", "password": "bad"})
    r = client.post("/auth/login", json={"login": "admin", "password": "bad"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    body = r.json()
    assert "retry_after" in body.get("detail", body) or "message" in str(body)


def test_forgot_password_rate_limited(client):
    payload = {"email": "x@x.pl"}
    for i in range(5):
        r = client.post("/auth/forgot-password", json=payload)
        assert r.status_code == 200, f"prob {i+1}: {r.status_code}"
    r = client.post("/auth/forgot-password", json=payload)
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_rate_limit_per_ip(client):
    """Rozne IP maja osobne liczniki."""
    # IP A: 5 prob OK
    for _ in range(5):
        r = client.post("/auth/login", json={"login": "admin", "password": "good"},
                        headers={"X-Forwarded-For": "10.0.0.1"})
        assert r.status_code == 200
    # IP A: 6. -> 429
    r = client.post("/auth/login", json={"login": "admin", "password": "good"},
                    headers={"X-Forwarded-For": "10.0.0.1"})
    assert r.status_code == 429
    # IP B: 1. proba -> 200 (osobny licznik)
    r = client.post("/auth/login", json={"login": "admin", "password": "good"},
                    headers={"X-Forwarded-For": "10.0.0.2"})
    assert r.status_code == 200


def test_reset_rate_limit_clears_state(client):
    from auth import rate_limit
    for _ in range(5):
        client.post("/auth/login", json={"login": "admin", "password": "good"})
    assert client.post("/auth/login", json={"login": "admin", "password": "good"}).status_code == 429
    rate_limit.reset_rate_limit()
    # Po resecie znów przechodzi
    r = client.post("/auth/login", json={"login": "admin", "password": "good"})
    assert r.status_code == 200


# ── RAO-P2-048: docs_url warunkowe ───────────────────────────────────────────

def test_docs_disabled_in_production():
    app = _build_app("production")
    c = TestClient(app)
    # /docs -> 404 gdy wylaczone
    r = c.get("/docs")
    assert r.status_code == 404
    r = c.get("/redoc")
    assert r.status_code == 404


def test_docs_enabled_in_development():
    app = _build_app("development")
    c = TestClient(app)
    r = c.get("/docs")
    assert r.status_code == 200


def test_environment_property_normalizes():
    from config import settings
    settings.RAO_ENV = "  Production  "
    assert settings.environment == "production"
    settings.RAO_ENV = "development"  # przywroc
    assert settings.environment == "development"
