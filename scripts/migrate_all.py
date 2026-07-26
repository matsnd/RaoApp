"""
RAO-P2-067: migrate_all.py — orchestrator pełnej migracji + środowiska demo.

Kroki (uruchamiane wybiórczo przez --steps):
  1   legacy     Migracja legacy dump → rao_new (migrate.py — DROPUJE i odtwarza bazę!)
  2   archive    Archive split — legacy umowy → tabele archive_* (archive_legacy_data.py)
  2b  clean      Czyszczenie tabel demo (bez archiwizacji — dla --reseed)
  2c  postal     Seed postal_codes z CSV (wymagane przed demo — umowy referencjuja PNA)
  3   demo       Seed danych demo (seed_demo_data.py): kontrahenci, maszyny, umowy
                 2025+2026 z lokalizacjami (PNA), zestawy usług "jak od klienta",
                 pula FA-pending (nierozliczone — do demo integracji FA)
  4   fa         Faktury w Fakturowni (seed_fa_invoices.py): utworz klienci+produkty w FA
                 (jeśli puste), backfill invoice_id dla rozliczonych + faktury czekające
                 dla FA-pending (OID = numer umowy)
  5   verify     Weryfikacja stanu demo (liczby, lokalizacje, gruba krecha)

Użycie:
    python migrate_all.py --list                 # pokaż kroki
    python migrate_all.py --steps 2c-5           # fresh seed bez legacy (schema z modeli)
    python migrate_all.py --steps 3-5            # odświeżenie demo (bez postal_codes)
    python migrate_all.py --steps 1-5            # PEŁNA migracja od zera (wymaga dumpa!)
    python migrate_all.py --steps 4              # tylko faktury FA

Bezpieczeństwo:
    - Krok 1 DROPUJE bazę — wymaga jawnego --confirm-drop.
    - Krok 4 wymaga tokenu FA w env (FA_TOKEN lub FAKTUROWNIA_API_TOKEN).
    - Kroki 3-5 są idempotentne (re-run bezpieczny).
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# Windows: konsola cp1250 nie zna ✓/✗ — wymuś UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).parent.parent / "backend"
SCRIPTS = Path(__file__).parent
PYTHON = sys.executable


def _run_script(name: str) -> int:
    """Uruchom skrypt z scripts/ w subprocessie (izolacja event-loopów/state).

    Skrypty helper żyją w scripts/ (root-level), nie w backend/.
    Skrypty aplikacji (migrate.py) żyją w backend/.
    """
    print(f"\n>>> {name}")
    # Najpierw scripts/ (helpery), potem backend/ (migrate.py)
    candidates = [SCRIPTS / name, BACKEND / name]
    target = next((c for c in candidates if c.exists()), None)
    if target is None:
        print(f"  BŁĄD: nie znaleziono {name} ani w scripts/ ani w backend/")
        return 2
    cwd = target.parent
    proc = subprocess.run([PYTHON, str(target)], cwd=str(cwd))
    return proc.returncode


def step1_legacy(args) -> int:
    if not args.confirm_drop:
        print("POMINIĘTO krok 1 (legacy): wymaga --confirm-drop (DROPUJE bazę rao_new!)")
        return 0
    return _run_script("migrate.py")


def step2_archive(args) -> int:
    cmd = [PYTHON, str(SCRIPTS / "archive_legacy_data.py")]
    if getattr(args, "reseed", False):
        cmd.append("--force")
    proc = subprocess.run(cmd, cwd=str(SCRIPTS))
    return proc.returncode


def step2b_clean_demo(args) -> int:
    """Wyczyść tabele demo (bez archiwizacji) — dla --reseed.

    Demo dane z seeda NIE idą do archiwum (archiwum = tylko legacy WinForms).
    Usuwa: contracts, contract_positions, position_conditions,
    contract_service_fees, contract_settlements.
    """
    import sqlalchemy as sa
    from database import AsyncSessionLocal
    import contracts.models, settlements.models  # noqa: F401

    async def _clean():
        async with AsyncSessionLocal() as db:
            print("Czyszczenie tabel demo (bez archiwizacji)...")
            for sql in [
                "DELETE FROM contract_settlements",
                "DELETE FROM contract_service_fees",
                "DELETE FROM position_conditions",
                "DELETE FROM contract_positions",
                "DELETE FROM contracts",
                "DELETE FROM machine_reservations",
                "DELETE FROM machine_rate_preset_items",
                "DELETE FROM machine_rate_presets",
                "DELETE FROM contract_costs",
                "DELETE FROM deliveries",
                "DELETE FROM additional_services",
                "DELETE FROM services",
                "DELETE FROM machines",
                "DELETE FROM service_fee_templates",
                "DELETE FROM fee_preset_groups",
                "ALTER TABLE contracts AUTO_INCREMENT = 1",
                "ALTER TABLE contract_positions AUTO_INCREMENT = 1",
                "ALTER TABLE position_conditions AUTO_INCREMENT = 1",
                "ALTER TABLE contract_service_fees AUTO_INCREMENT = 1",
                "ALTER TABLE contract_settlements AUTO_INCREMENT = 1",
                "ALTER TABLE machines AUTO_INCREMENT = 1",
                "ALTER TABLE services AUTO_INCREMENT = 1",
                "ALTER TABLE additional_services AUTO_INCREMENT = 1",
            ]:
                result = await db.execute(sa.text(sql))
                if result.rowcount:
                    print(f"  {sql.split(' FROM ')[-1].split(' AUTO')[0]}: {result.rowcount} usuniętych")
            await db.commit()
            print("  OK — tabele demo wyczyszczone.")
        return 0

    return asyncio.run(_clean())


def step2c_postal(args) -> int:
    """Seed postal_codes from CSV — musi biec PRZED demo (umowy referencjuja postal_code_id)."""
    return _run_script("seed_postal_codes.py")


def step3_demo(args) -> int:
    return _run_script("seed_demo_data.py")


def step4_fa(args) -> int:
    import os
    import asyncio
    if not (os.environ.get("FA_TOKEN") or os.environ.get("FAKTUROWNIA_API_TOKEN")):
        # Spróbuj załadować z root .env (FAKTUROWNIA_API_TOKEN)
        root_env = BACKEND.parent / ".env"
        if root_env.exists():
            for line in root_env.read_text(encoding="utf-8").splitlines():
                if line.startswith("FAKTUROWNIA_API_TOKEN="):
                    os.environ["FAKTUROWNIA_API_TOKEN"] = line.split("=", 1)[1].strip()
                    break
    if not (os.environ.get("FA_TOKEN") or os.environ.get("FAKTUROWNIA_API_TOKEN")):
        print("POMINIĘTO krok 4 (fa): brak tokenu FA_TOKEN/FAKTUROWNIA_API_TOKEN w env")
        return 0

    # RAO-P1-005 fix: sync FA token w DB z env (bootstrap tylko gdy NULL,
    # ale env moze sie zmienic — np. nowe konto FA testowe).
    asyncio.run(_sync_fa_token_from_env())

    return _run_script("seed_fa_invoices.py")


async def _sync_fa_token_from_env() -> None:
    """Aktualizuj fakturownia_settings.api_token_ciphertext z env (idempotentny).

    Bootstrap w service.py działa tylko gdy ciphertext IS NULL. Ta funkcja
    wymusza update z env na każdym runie migrate_all — żeby zmiana tokenu
    w .env od razu była widoczna w DB (bez ręcznego NULLowania).
    """
    from database import AsyncSessionLocal
    from config import settings as app_settings
    from integrations.fakturownia.crypto import encrypt_token, mask_token
    from sqlalchemy import text
    from datetime import datetime, timezone

    token = app_settings.RAO_FAKTUROWNIA_API_TOKEN
    enc_key = app_settings.RAO_FAKTUROWNIA_ENC_KEY
    if not token or not enc_key:
        print("  [fa-token] POMINIĘTO: brak RAO_FAKTUROWNIA_API_TOKEN lub ENC_KEY w env")
        return

    ciphertext = encrypt_token(token, enc_key)
    preview = mask_token(token)

    async with AsyncSessionLocal() as db:
        # Sprawdź czy token się zmienił
        result = await db.execute(text("SELECT api_token_preview FROM fakturownia_settings WHERE id=1"))
        row = result.fetchone()
        if row and row[0] == preview:
            print(f"  [fa-token] Token aktualny (preview={preview}) — skip")
            return

        await db.execute(text(
            "UPDATE fakturownia_settings SET "
            "api_token_ciphertext = :ct, api_token_preview = :pv, "
            "enabled = 1, domain_subdomain = :dom, "
            "api_token_updated_at = :ts WHERE id = 1"
        ), {
            "ct": ciphertext, "pv": preview,
            "dom": app_settings.RAO_FAKTUROWNIA_DOMAIN_SUBDOMAIN,
            "ts": datetime.now(timezone.utc).replace(tzinfo=None),
        })
        await db.commit()
        print(f"  [fa-token] Token zaktualizowany w DB (preview={preview})")


async def _verify() -> int:
    import sqlalchemy as sa
    from database import AsyncSessionLocal
    import contracts.models, articles.models, settings.models, settlements.models  # noqa
    import integrations.fakturownia.models, audit.models, contract_costs.models  # noqa
    import archive.models, reservations.models  # noqa

    ok = True
    async with AsyncSessionLocal() as db:
        async def one(sql: str):
            return (await db.execute(sa.text(sql))).scalar()

        print("\n── Weryfikacja środowiska demo ──────────────────────────")
        n_contracts = await one("SELECT COUNT(*) FROM contracts")
        n_arch = await one("SELECT COUNT(*) FROM archive_contracts")
        print(f"Umowy (nowe): {n_contracts} | Archiwum (gruba krecha): {n_arch}")

        n_loc = await one("SELECT COUNT(*) FROM contracts WHERE postal_code_id IS NOT NULL")
        print(f"Umowy z lokalizacją (FK postal_codes): {n_loc}/{n_contracts}")
        if n_contracts and n_loc == 0:
            print("  ✗ BRAK lokalizacji — zakładka Lokalizacje będzie pusta!")
            ok = False

        cities = (await db.execute(sa.text(
            "SELECT c.city, COUNT(*) FROM contracts c WHERE c.city IS NOT NULL GROUP BY c.city ORDER BY 2 DESC LIMIT 5"
        ))).fetchall()
        print("Top miasta umów: " + ", ".join(f"{r[0]} ({r[1]})" for r in cities))

        rows = (await db.execute(sa.text(
            "SELECT source, COUNT(*) FROM contract_settlements GROUP BY source"
        ))).fetchall()
        print("Rozliczenia: " + ", ".join(f"{r[0]}={r[1]}" for r in rows))

        n_pending = await one(
            "SELECT COUNT(*) FROM contracts c WHERE c.is_settled = 0 AND c.date_to < CURDATE() "
            "AND NOT EXISTS (SELECT 1 FROM contract_settlements cs WHERE cs.contract_id = c.id)"
        )
        print(f"FA-pending (nierozliczone, do demo 'Pobierz z Fakturowni'): {n_pending}")
        if n_pending == 0:
            print("  ⚠ Brak umów FA-pending — demo integracji FA nie zadziała")

        n_groups = await one("SELECT COUNT(*) FROM fee_preset_groups")
        n_tpl = await one("SELECT COUNT(*) FROM service_fee_templates WHERE additional_service_id IS NOT NULL")
        print(f"Zestawy usług: {n_groups} grup, {n_tpl} szablonów z additional_service_id")

        fa_enabled = await one("SELECT enabled FROM fakturownia_settings WHERE id=1")
        print(f"Integracja FA w RAO: {'WŁĄCZONA' if fa_enabled else 'WYŁĄCZONA (skonfiguruj w Ustawieniach!)'}")
        if not fa_enabled:
            ok = False

    print("──────────────────────────────────────────────────────────")
    print("✓ Środowisko demo OK" if ok else "✗ Środowisko demo NIEKOMPLETNE (szczegóły wyżej)")
    return 0 if ok else 1


def step5_verify(args) -> int:
    return asyncio.run(_verify())


STEPS = [
    ("1", "legacy", "Migracja legacy dump → rao_new (DROP bazy! wymaga --confirm-drop)", step1_legacy),
    ("2", "archive", "Archive split: legacy → archive_* (gruba krecha)", step2_archive),
    ("2b", "clean", "Czyszczenie tabel demo (bez archiwizacji — dla --reseed)", step2b_clean_demo),
    ("2c", "postal", "Seed postal_codes z CSV (wymagane przed demo — umowy referencjuja PNA)", step2c_postal),
    ("3", "demo", "Seed danych demo (umowy+lokalizacje+zestawy usług+cenniki kaskadowe+FA-pending)", step3_demo),
    ("4", "fa", "Faktury w Fakturowni (backfill + FA-pending)", step4_fa),
    ("5", "verify", "Weryfikacja środowiska demo", step5_verify),
]


def parse_steps(spec: str) -> list[str]:
    """'3-5' → ['3','4','5']; '1,3' → ['1','3']; '4' → ['4']; '2b-5' → ['2b','3','4','5']."""
    # Mapa kroków w kolejności (obsługa alfanumerycznych jak '2b')
    step_order = [s[0] for s in STEPS]
    out: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            try:
                lo_idx = step_order.index(lo)
                hi_idx = step_order.index(hi)
                out.extend(step_order[lo_idx:hi_idx + 1])
            except ValueError:
                print(f"Nieznany krok w zakresie '{part}' — dostępne: {step_order}")
        elif part:
            out.append(part)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="RAO — orchestrator migracji i środowiska demo")
    ap.add_argument("--steps", default=None, help="Kroki do wykonania, np. '3-5', '1,4' (domyślnie 3-5, z --reseed: 2-5)")
    ap.add_argument("--list", action="store_true", help="Pokaż listę kroków i wyjdź")
    ap.add_argument("--confirm-drop", action="store_true", help="Potwierdź DROP bazy dla kroku 1")
    ap.add_argument("--demo", action="store_true", help="Flaga demo: pomija step 1 (legacy dump), tylko step 2-5 (dla szybkiego refresha demo)")
    ap.add_argument("--reseed", action="store_true",
                    help="Re-seed demo: archiwizuj aktualne contracts (--force) + seed + FA + verify. Skrót: --steps 2-5 --reseed")
    args = ap.parse_args()

    # Domyślny zestaw kroków: --reseed → 2b-5 (clean+seed+fa+verify, bez archiwizacji),
    # w przeciwnym razie 3-5 (tylko seed+fa+verify)
    if args.steps is None:
        args.steps = "2b-5" if args.reseed else "3-5"

    if args.list:
        print("Kroki migrate_all.py:")
        for num, key, desc, _ in STEPS:
            print(f"  {num}  {key:<8} {desc}")
        return 0

    wanted = parse_steps(args.steps)
    plan = [s for s in STEPS if s[0] in wanted]
    if not plan:
        print(f"Brak pasujących kroków dla --steps={args.steps!r}. Użyj --list.")
        return 2

    # --demo: pomiń step 1 (legacy dump) jeśli user używa --demo
    if args.demo and "1" in wanted:
        print("⚠️ --demo: pomijam krok 1 (legacy dump) — baza musi już mieć dane z dumpa")
        plan = [s for s in plan if s[0] != "1"]
        if not plan:
            print("Brak pozostałych kroków do wykonania po pominięciu kroku 1.")
            return 0

    print("=" * 60)
    print("RAO migrate_all — plan: " + ", ".join(f"{s[0]}:{s[1]}" for s in plan))
    print("=" * 60)

    for num, key, desc, fn in plan:
        print(f"\n[KROK {num}] {desc}")
        rc = fn(args)
        if rc != 0:
            print(f"\n✗ Krok {num} ({key}) zakończony błędem (rc={rc}) — przerywam.")
            return rc

    print("\n✓ migrate_all: wszystkie kroki zakończone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
