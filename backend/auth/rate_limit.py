"""RAO-P2-047: Rate limiting na endpointy auth (login + forgot-password).

Samowystarczalny, in-memory limiter (IP -> lista timestampow).
- max 5 prob / 60s na IP
- zwraca 429 Too Many Requests z headerm Retry-After

In-memory wybrany swiadomie: slowapi wymaga app.state.limiter + globalnego
exception handlera rejestrowanego w main.py (poza uprawnieniami backend-dev).
Ten modul jest zaleznoscia FastAPI - dziala bez modyfikacji main.py.

Nie jest to dystrybuowany limiter (po restarcie licznik sie resetuje, per-proces).
Dla instancji single-process uvicorn (RAO) jest wystarczajacy.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List

from fastapi import HTTPException, Request

MAX_REQUESTS: int = 5
WINDOW_SECONDS: int = 60

_hits: Dict[str, List[float]] = defaultdict(list)
_lock = Lock()


def _client_ip(request: Request) -> str:
    """IP klienta - honoruje X-Forwarded-For (pierwszy hop) dla reverse proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _cleanup(bucket: List[float], now: float) -> None:
    """Usun timestampy starsze niz WINDOW_SECONDS (mutuje liste in-place)."""
    cutoff = now - WINDOW_SECONDS
    while bucket and bucket[0] < cutoff:
        bucket.pop(0)


def _retry_after(bucket: List[float], now: float) -> int:
    """Sekundy do momentu, gdy najstarszy hit wygasnie (okno sie zwolni)."""
    if not bucket:
        return 1
    oldest = bucket[0]
    wait = oldest + WINDOW_SECONDS - now
    return max(1, int(wait) + 1)


async def enforce_auth_rate_limit(request: Request) -> None:
    """Zaleznosc FastAPI: rzuca 429 gdy IP przekroczylo limit w oknie.

    Uzywana jako Depends na endpointach /auth/login i /auth/forgot-password.
    """
    ip = _client_ip(request)
    now = time.monotonic()

    with _lock:
        bucket = _hits[ip]
        _cleanup(bucket, now)
        if len(bucket) >= MAX_REQUESTS:
            retry = _retry_after(bucket, now)
            raise HTTPException(
                status_code=429,
                detail={
                    "message": "Zbyt wiele prob. Sprobuj ponownie za chwile.",
                    "retry_after": retry,
                },
                headers={"Retry-After": str(retry)},
            )
        bucket.append(now)


def reset_rate_limit(ip: str | None = None) -> None:
    """Test helper: czysci licznik dla IP (lub caly stan gdy ip=None)."""
    with _lock:
        if ip is None:
            _hits.clear()
        else:
            _hits.pop(ip, None)
