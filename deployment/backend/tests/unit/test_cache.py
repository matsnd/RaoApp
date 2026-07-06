"""Unit testy dla RAO-P2-051: TTLCache (shared/cache.py).

Testuje:
- get/set z TTL
- wygasanie po TTL (lazy eviction)
- invalidate(prefix) — usuwa po prefiksie
- clear() — czyści cały cache
- stats() — liczba wpisów
- make_key() — deterministyczne klucze z hashem parametrów
- cached_or_compute() — helper async (cache hit/miss)
- Thread safety (podstawowa)
"""
import asyncio
import time
import threading
import pytest

from shared.cache import TTLCache, TTL_STATS, TTL_DICTIONARY, cache, cached_or_compute


# ── get/set + TTL ─────────────────────────────────────────────────────────────

def test_set_and_get():
    c = TTLCache()
    c.set("k1", "value1", ttl=60)
    assert c.get("k1") == "value1"


def test_get_missing_key_returns_none():
    c = TTLCache()
    assert c.get("nonexistent") is None


def test_set_ttl_zero_does_not_cache():
    """ttl=0 to bezpieczny wyłącznik — nie cacheuj."""
    c = TTLCache()
    c.set("k1", "value", ttl=0)
    assert c.get("k1") is None


def test_expired_entry_evicted_on_get():
    """Entry po TTL → get() zwraca None i usuwa (lazy eviction)."""
    c = TTLCache()
    c.set("k1", "value", ttl=1)
    time.sleep(1.1)  # poczekaj > TTL (1s)
    assert c.get("k1") is None


def test_default_ttl_stats_5min():
    assert TTL_STATS == 300


def test_default_ttl_dictionary_1h():
    assert TTL_DICTIONARY == 3600


# ── invalidate(prefix) ────────────────────────────────────────────────────────

def test_invalidate_by_prefix():
    c = TTLCache()
    c.set("stats:ep1:1:abc", "v1", ttl=60)
    c.set("stats:ep2:1:def", "v2", ttl=60)
    c.set("rate_types:all", "v3", ttl=60)

    removed = c.invalidate("stats:")
    assert removed == 2
    assert c.get("stats:ep1:1:abc") is None
    assert c.get("stats:ep2:1:def") is None
    assert c.get("rate_types:all") == "v3"  # nie ruszony


def test_invalidate_empty_prefix_returns_zero():
    c = TTLCache()
    c.set("k1", "v", ttl=60)
    assert c.invalidate("") == 0
    assert c.get("k1") == "v"


def test_invalidate_nonexistent_prefix_returns_zero():
    c = TTLCache()
    c.set("k1", "v", ttl=60)
    assert c.invalidate("nonexistent:") == 0


# ── clear() ───────────────────────────────────────────────────────────────────

def test_clear_removes_all():
    c = TTLCache()
    c.set("k1", "v1", ttl=60)
    c.set("k2", "v2", ttl=60)
    removed = c.clear()
    assert removed == 2
    assert c.get("k1") is None
    assert c.get("k2") is None


def test_clear_empty_returns_zero():
    c = TTLCache()
    assert c.clear() == 0


# ── stats() ───────────────────────────────────────────────────────────────────

def test_stats_counts_entries():
    c = TTLCache()
    c.set("k1", "v1", ttl=60)
    c.set("k2", "v2", ttl=60)
    assert c.stats()["entries"] == 2


def test_stats_empty():
    c = TTLCache()
    assert c.stats()["entries"] == 0


# ── make_key() ────────────────────────────────────────────────────────────────

def test_make_key_deterministic():
    """Ten sam prefix + user_id + params → ten sam klucz."""
    k1 = TTLCache.make_key("stats:ep", 1, {"df": "2024-01-01", "dt": "2024-12-31"})
    k2 = TTLCache.make_key("stats:ep", 1, {"df": "2024-01-01", "dt": "2024-12-31"})
    assert k1 == k2


def test_make_key_order_independent():
    """Kolejność kluczy w params nie wpływa na hash (sort_keys=True)."""
    k1 = TTLCache.make_key("stats:ep", 1, {"a": 1, "b": 2})
    k2 = TTLCache.make_key("stats:ep", 1, {"b": 2, "a": 1})
    assert k1 == k2


def test_make_key_different_user():
    k1 = TTLCache.make_key("stats:ep", 1, {"df": "2024-01-01"})
    k2 = TTLCache.make_key("stats:ep", 2, {"df": "2024-01-01"})
    assert k1 != k2


def test_make_key_different_params():
    k1 = TTLCache.make_key("stats:ep", 1, {"df": "2024-01-01"})
    k2 = TTLCache.make_key("stats:ep", 1, {"df": "2024-06-01"})
    assert k1 != k2


def test_make_key_none_params():
    k = TTLCache.make_key("stats:ep", 1, None)
    assert k == "stats:ep:1:0"


def test_make_key_none_user():
    k = TTLCache.make_key("stats:ep", None, {"x": 1})
    assert ":0:" in k  # user_id=0 dla None


# ── cached_or_compute (async helper) ──────────────────────────────────────────

def test_cached_or_compute_miss_then_hit():
    """Pierwsze wywołanie → compute + cache; drugie → hit z cache."""
    cache.clear()
    calls = []

    async def compute():
        calls.append(1)
        return {"revenue": 1000}

    key = "test:cached_or_compute:1:abc"
    r1 = asyncio.run(cached_or_compute(key, compute, ttl=60))
    r2 = asyncio.run(cached_or_compute(key, compute, ttl=60))

    assert r1 == {"revenue": 1000}
    assert r2 == {"revenue": 1000}
    assert len(calls) == 1  # compute wywołane raz


def test_cached_or_compute_none_not_cached():
    """Jeśli compute zwraca None → nie cacheuj (None = brak danych)."""
    cache.clear()
    calls = []

    async def compute():
        calls.append(1)
        return None

    key = "test:none_not_cached:1:x"
    r1 = asyncio.run(cached_or_compute(key, compute, ttl=60))
    r2 = asyncio.run(cached_or_compute(key, compute, ttl=60))

    assert r1 is None
    assert r2 is None
    assert len(calls) == 2  # compute wywołane 2× (None nie cacheowany)


# ── Thread safety (podstawowa) ────────────────────────────────────────────────

def test_concurrent_set_and_get():
    """100 wątków set + get — bez deadlock/crash."""
    c = TTLCache()
    errors = []

    def worker(i):
        try:
            c.set(f"k{i}", f"v{i}", ttl=60)
            v = c.get(f"k{i}")
            assert v == f"v{i}"
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert c.stats()["entries"] == 100


# ── Cleanup ───────────────────────────────────────────────────────────────────

def teardown_module():
    """Wyczyść singleton po testach (nie wpływaj na inne testy)."""
    cache.clear()
