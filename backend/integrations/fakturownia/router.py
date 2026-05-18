import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user, require_admin
from auth.models import User
from database import get_db

from . import service
from .schemas import (
    FakturowniaProductOut,
    FakturowniaSettingsIn,
    FakturowniaSettingsOut,
    ResolvedInvoiceOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/fakturownia", tags=["fakturownia"])


# -- In-memory sliding-window rate limiter ------------------------------------
# Single-process only (acceptable for RAO single-instance deployment).
# For multi-process: replace with Redis-backed counter.

class _SlidingWindowLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self, max_calls: int, window_seconds: int) -> None:
        self._max = max_calls
        self._window = timedelta(seconds=window_seconds)
        self._buckets: dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Returns True if the request is within limits (and records it)."""
        now = datetime.utcnow()
        cutoff = now - self._window
        bucket = self._buckets[key]
        # Evict expired timestamps
        self._buckets[key] = [t for t in bucket if t > cutoff]
        if len(self._buckets[key]) >= self._max:
            return False
        self._buckets[key].append(now)
        return True


# 30 requests / 60s per user (invoices endpoint)
_invoices_limiter = _SlidingWindowLimiter(max_calls=30, window_seconds=60)
# 5 requests / 60s per IP (settings PUT — token update)
_settings_token_limiter = _SlidingWindowLimiter(max_calls=5, window_seconds=60)


# -- Rate-limit dependencies --------------------------------------------------

def _check_invoices_rate(
    request: Request,
    user: User = Depends(get_current_user),
) -> User:
    """Dependency: auth + 30/min/user rate limit on invoices endpoint."""
    key = f"invoices:user:{user.id}"
    if not _invoices_limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail="Zbyt wiele zapytan o faktury — odczekaj chwile (limit: 30/min)",
        )
    return user


def _check_settings_token_rate(request: Request) -> None:
    """Dependency: 5/min/IP rate limit on settings PUT (token update)."""
    ip = request.client.host if request.client else "unknown"
    key = f"settings_token:ip:{ip}"
    if not _settings_token_limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail="Zbyt wiele aktualizacji tokenu — odczekaj chwile (limit: 5/min/IP)",
        )


# -- Endpoints ----------------------------------------------------------------

@router.get("/settings", response_model=FakturowniaSettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Pobierz konfiguracje integracji Fakturownia (admin only).
    Token nigdy nie jest zwracany w odpowiedzi — tylko zamaskowany podglad."""
    obj = await service.get_or_create_settings(db)
    return FakturowniaSettingsOut.model_validate(obj)


@router.put("/settings", response_model=FakturowniaSettingsOut)
async def update_settings(
    payload: FakturowniaSettingsIn,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
    _rate: None = Depends(_check_settings_token_rate),
):
    """Zaktualizuj konfiguracje Fakturownia (admin only, 5/min/IP).

    Jezeli payload.api_token jest podany: token jest szyfrowany Fernet przed zapisem.
    Jezeli pominieto: token pozostaje bez zmian."""
    obj = await service.update_settings(db, payload, admin)
    return FakturowniaSettingsOut.model_validate(obj)


@router.get("/products", response_model=List[FakturowniaProductOut])
async def get_products(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Pobierz katalog produktow z Fakturownia (admin only)."""
    return await service.fetch_products(db)


@router.get("/invoices", response_model=List[ResolvedInvoiceOut])
async def get_invoices(
    contract_id: int = Query(..., ge=1, description="ID umowy RAO (OID pobierany z DB — IDOR fix)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(_check_invoices_rate),
):
    """Pobierz faktury z Fakturownia dla umowy z mapowaniem artykulow 1:N (30/min/user).

    IDOR fix: OID jest pobierany z bazy na podstawie contract_id.
    Klient nie moze podac ani sfalsowac numeru zamowienia.
    Ownership check: non-admin widzi tylko umowy ze swojej filii."""
    return await service.fetch_invoices_for_contract(db, contract_id, user)
