"""
RAO-P2-067: migrate_all.py — orchestrator pełnej migracji + środowiska demo.

Kroki (uruchamiane wybiórczo przez --steps):
  1  legacy      Migracja legacy dump → rao_new (migrate.py — DROPUJE i odtwarza bazę!)
  2  archive     Archive split — legacy umowy → tabele archive_* (migrate_to_archive.py)
  3  demo        Seed danych demo (seed_demo_data.py): kontrahenci, maszyny, umowy
                 2025+2026 z lokalizacjami (PNA), zestawy usług "jak od klienta",
                 pula FA-pending (nierozliczone — do demo integracji FA)
  4  fa          Faktury w Fakturowni (seed_fa_invoices.py): backfill invoice_id dla
                 rozliczonych + faktury czekające dla FA-pending (OID = numer umowy)
  5  verify      Weryfikacja stanu demo (liczby, lokalizacje, gruba krecha)

Użycie:
    python migrate_all.py --list                 # pokaż kroki
    python migrate_all.py --steps 3-5            # typowe odświeżenie demo (bez dropu bazy)
    python migrate_all.py --steps 1-5            # PEŁNA migracja od zera (wymaga dumpa!)
    python migrate_all.py --steps 4              # tylko faktury FA

Bezpieczeństwo:
    - Krok 1 DROPUJE bazę — wymaga jawnego --confirm-drop.
    - Krok 4 wymaga tokenu FA w env (FA_TOKEN lub FAKTUROWNIA_API_TOKEN).
    - Kroki 3-5 są idempotentne (re-run bezpieczny).
"""
import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# Windows: konsola cp1250 nie zna ✓/✗ — wymuś UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).parent
PYTHON = sys.executable


def _run_script(name: str) -> int:
    """Uruchom skrypt backendu w subprocessie (izolacja event-loopów/state)."""
    print(f"\n>>> {name}")
    proc = subprocess.run([PYTHON, str(BACKEND / name)], cwd=str(BACKEND))
    return proc.returncode


def step1_legacy(args) -> int:
    if not args.confirm_drop:
        print("POMINIĘTO krok 1 (legacy): wymaga --confirm-drop (DROPUJE bazę rao_new!)")
        return 0
    return _run_script("migrate.py")


def step2_archive(args) -> int:
    return _run_script("migrate_to_archive.py")


def step3_demo(args) -> int:
    return _run_script("seed_demo_data.py")


def step4_fa(args) -> int:
    import os
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
    return _run_script("seed_fa_invoices.py")


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
        n_tpl = await one("SELECT COUNT(*) FROM service_fee_templates WHERE article_id IS NOT NULL")
        print(f"Zestawy usług: {n_groups} grup, {n_tpl} szablonów z article_id")

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
    ("3", "demo", "Seed danych demo (umowy+lokalizacje+zestawy usług+cenniki kaskadowe+FA-pending)", step3_demo),
    ("4", "fa", "Faktury w Fakturowni (backfill + FA-pending)", step4_fa),
    ("5", "verify", "Weryfikacja środowiska demo", step5_verify),
]


def parse_steps(spec: str) -> list[str]:
    """'3-5' → ['3','4','5']; '1,3' → ['1','3']; '4' → ['4']."""
    out: list[str] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.extend(str(x) for x in range(int(lo), int(hi) + 1))
        elif part:
            out.append(part)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="RAO — orchestrator migracji i środowiska demo")
    ap.add_argument("--steps", default="3-5", help="Kroki do wykonania, np. '3-5', '1,4' (domyślnie 3-5)")
    ap.add_argument("--list", action="store_true", help="Pokaż listę kroków i wyjdź")
    ap.add_argument("--confirm-drop", action="store_true", help="Potwierdź DROP bazy dla kroku 1")
    ap.add_argument("--demo", action="store_true", help="Flaga demo: pomija step 1 (legacy dump), tylko step 2-5 (dla szybkiego refresha demo)")
    args = ap.parse_args()

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
