"""RAO-P2-051: Prosty in-memory cache TTL dla endpointow read-heavy (stats, slowniki).

Wlasna implementacja (bez Redis / cachetools) — wystarcza dla single-instance FastAPI.
- Thread-safe (threading.Lock) — bezpieczny rowniez w kontekscie async (operacje atomowe).
- Automatyczne usuwanie expired entries przy get() oraz w invalidate().
- Cache jest opcjonalny: gdy entry expired lub brak -> fallback do DB (caller oblicza).

Konwencja kluczy:
    stats:    f"stats:{endpoint}:{user_id}:{params_hash}"   TTL 300s (5 min)
    slowniki: "rate_types:all", "categories:all"            TTL 3600s (1h)

Invalidate po prefiksie (np. cache.invalidate("stats:")) lub clear() calosci.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger("rao.cache")

# Domyslne TTL (sekundy)
TTL_STATS = 300        # 5 minut — statystyki read-heavy
TTL_DICTIONARY = 3600  # 1 godzina — slowniki (RateType, Category) rzadko sie zmieniaja


class TTLCache:
    """In-memory cache z TTL, thread-safe.

    Struktura wewnetrzna:
        _store: dict[str, tuple[value, expires_at: float]]
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Podstawowe operacje
    # ------------------------------------------------------------------
    def get(self, key: str) -> Any | None:
        """Zwroc wartosc jesli istnieje i nie wygasla, wpp. None (i usun jesli wygasla)."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                # Lazy eviction
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = TTL_STATS) -> None:
        """Wstaw wartosc z TTL (sekundy)."""
        if ttl <= 0:
            # ttl=0 -> nie cacheuj (bezpieczny wylacznik)
            return
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._store[key] = (value, expires_at)

    # ------------------------------------------------------------------
    # Invalidation
    # ------------------------------------------------------------------
    def invalidate(self, prefix: str) -> int:
        """Usun wszystkie klucze zaczynajace sie od `prefix`. Zwraca liczbe usunietych."""
        if not prefix:
            return 0
        now = time.monotonic()
        removed = 0
        with self._lock:
            # Iterujemy po kopii kluczy (mutacja w trakcie iteracji)
            for key in list(self._store.keys()):
                if key.startswith(prefix):
                    self._store.pop(key, None)
                    removed += 1
                else:
                    # Przy okazji posprzataj expired
                    entry = self._store.get(key)
                    if entry and now > entry[1]:
                        self._store.pop(key, None)
        if removed:
            logger.debug("cache.invalidate prefix=%s removed=%d", prefix, removed)
        return removed

    def clear(self) -> int:
        """Wyczysc caly cache. Zwraca liczbe usunietych wpisow."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
        logger.info("cache.clear removed=%d", count)
        return count

    # ------------------------------------------------------------------
    # Diagnostyka
    # ------------------------------------------------------------------
    def stats(self) -> dict[str, int]:
        """Zwroc liczbe wpisow (w tym potencjalnie wygaslych — bez czyszczenia)."""
        with self._lock:
            return {"entries": len(self._store)}

    # ------------------------------------------------------------------
    # Helper do budowania klucza z parametrow requestu
    # ------------------------------------------------------------------
    @staticmethod
    def make_key(prefix: str, user_id: int | None, params: dict | None) -> str:
        """Zbuduj stabilny klucz cache: f"{prefix}:{user_id}:{params_hash}".

        params_hash = md5(json.dumps(params, sort_keys, default=str)) — deterministyczny.
        """
        if params:
            try:
                params_str = json.dumps(
                    params, sort_keys=True, default=str, ensure_ascii=False
                )
            except (TypeError, ValueError):
                params_str = str(params)
            params_hash = hashlib.md5(params_str.encode("utf-8")).hexdigest()[:12]
        else:
            params_hash = "0"
        return f"{prefix}:{user_id or 0}:{params_hash}"


# Singleton — wspoldzielony przez wszystkie routery w procesie
cache = TTLCache()


async def cached_or_compute(
    key: str,
    compute: Callable[[], Any],
    ttl: int = TTL_STATS,
) -> Any:
    """Helper: zwroc z cache jesli jest, wpp. oblicz (await jesli coroutine) i zapamietaj.

    Uzycie w routerze:
        key = cache.make_key("stats:fleet-summary", user.id, {"df": df, "dt": dt})
        return await cached_or_compute(key, lambda: _compute_fleet_summary(db, df, dt), ttl=TTL_STATS)
    """
    cached = cache.get(key)
    if cached is not None:
        return cached

    result = compute()
    if inspect.isawaitable(result):
        result = await result

    # Cacheuj tylko jesli wynik nie jest None (None traktujemy jako "brak cache")
    if result is not None:
        cache.set(key, result, ttl=ttl)
    return result
