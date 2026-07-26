"""
P1-114: Skrypt do odtworzenia bazy od zera (DROP + CREATE + schema + seed).

DESTRUKCYJNE: usuwa wszystkie dane w `rao_new`.
Użycie:
    cd backend && python reset_db.py
    cd backend && python reset_db.py --skip-seed   # tylko DROP + CREATE + schema

Procedura:
1. DROP DATABASE rao_new (jeśli istnieje)
2. CREATE DATABASE rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci
3. Base.metadata.create_all (schema z modeli SQLAlchemy)
4. (opcjonalnie) seed_demo_data.py — pełny seed
5. (opcjonalnie) seed_fa_invoices.py — faktury FA dla rozliczonych umów
"""
import asyncio
import sys
from pathlib import Path

# Windows: cp1250 crashuje przy polskich znakach — wymuś UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

# Załaduj root .env
_root_env = Path(__file__).parent.parent / ".env"
if _root_env.exists():
    from dotenv import load_dotenv
    load_dotenv(_root_env)

import aiomysql
from config import settings as cfg
from database import Base, engine

# Import wszystkich modeli aby create_all je znalazł (mirror z main.py)
import auth.models  # noqa: F401
import integrations.models  # noqa: F401
import reservations.models  # noqa: F401
import deliveries.models  # noqa: F401
import contract_costs.models  # noqa: F401
import audit.models  # noqa: F401
import archive.models  # noqa: F401
import machines.models  # noqa: F401
import services.models  # noqa: F401
import additional_services.models  # noqa: F401
import articles.models  # noqa: F401
import contractors.models  # noqa: F401
import contracts.models  # noqa: F401
import settings.models  # noqa: F401
import categories.models  # noqa: F401
import settlements.models  # noqa: F401
import integrations.fakturownia.models  # noqa: F401


def _parse_db_url(url: str) -> dict:
    """Parsuje mysql+aiomysql://user:pass@host:port/db → komponenty."""
    # mysql+aiomysql://rao_user:RaoPass2026!@localhost:3306/rao_new
    import re
    m = re.match(r"mysql\+aiomysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url)
    if not m:
        raise ValueError(f"Nie udało się sparsować DB URL: {url}")
    return {
        "user": m.group(1),
        "password": m.group(2),
        "host": m.group(3),
        "port": int(m.group(4)),
        "db": m.group(5),
    }


async def drop_and_create_db():
    """DROP + CREATE bazy rao_new (bezpośrednio przez aiomysql, bez SQLAlchemy)."""
    db_info = _parse_db_url(cfg.RAO_DATABASE_URL)
    db_name = db_info["db"]

    print(f"[1/4] Łączenie z MySQL ({db_info['host']}:{db_info['port']}) jako {db_info['user']}...")
    conn = await aiomysql.connect(
        host=db_info["host"],
        port=db_info["port"],
        user=db_info["user"],
        password=db_info["password"],
        autocommit=True,
    )

    try:
        print(f"[2/4] DROP DATABASE IF EXISTS {db_name}...")
        async with conn.cursor() as cur:
            await cur.execute(f"DROP DATABASE IF EXISTS {db_name}")

        print(f"[3/4] CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci...")
        async with conn.cursor() as cur:
            await cur.execute(
                f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci"
            )
        print(f"  ✓ Baza {db_name} odtworzona od zera")
    finally:
        conn.close()


async def create_schema():
    """Base.metadata.create_all — schema z modeli SQLAlchemy."""
    print("[4/4] create_all (schema z modeli SQLAlchemy)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ Schema utworzona")
    await engine.dispose()


async def run_seed():
    """Uruchom seed_demo_data.py — pełny seed."""
    print("\n[SEED] Uruchamianie seed_demo_data.py...")
    # Import main z seed_demo_data
    import seed_demo_data
    await seed_demo_data.main()


async def run_fa_invoices():
    """Uruchom seed_fa_invoices.py — faktury FA dla rozliczonych umów."""
    print("\n[FA] Uruchamianie seed_fa_invoices.py...")
    import seed_fa_invoices
    await seed_fa_invoices.main()


async def main(skip_seed: bool = False, skip_fa: bool = False):
    print("=" * 60)
    print("P1-114: RESET BAZY — DROP + CREATE + schema + seed")
    print("=" * 60)
    print(f"DB: {cfg.RAO_DATABASE_URL.split('@')[-1]}")
    print()

    # 1-3: DROP + CREATE
    await drop_and_create_db()

    # 4: Schema
    await create_schema()

    if skip_seed:
        print("\n[--skip-seed] Pominięto seed")
    else:
        await run_seed()

        if skip_fa:
            print("\n[--skip-fa] Pominięto FA invoices")
        else:
            try:
                await run_fa_invoices()
            except Exception as e:
                print(f"\n[FA] UWAGA: seed_fa_invoices zakończone błędem: {e}")
                print("  (może być OK jeśli Fakturownia API niedostępne)")

    print("\n" + "=" * 60)
    print("DONE — baza odtworzona od zera")
    print("=" * 60)


if __name__ == "__main__":
    skip_seed = "--skip-seed" in sys.argv
    skip_fa = "--skip-fa" in sys.argv
    asyncio.run(main(skip_seed=skip_seed, skip_fa=skip_fa))
