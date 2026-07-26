"""
RAO-P2-071: Archive legacy data — przenosi wszystkie stare dane do archive_* tabel.

Idempotentny: INSERT IGNORE (nie duplikuje jeśli już istnieje).
Deterministyczny: kolejność parents-first, batch 500 rekordów.

Użycie:
    cd backend && python archive_legacy_data.py

Wymaga:
    - Backend NIE musi działać (skrypt łączy się bezpośrednio z DB)
    - .env z DB credentials
"""
import asyncio
import sys
from pathlib import Path

# Windows: konsola cp1250 nie zna ✓/✗/Polish chars — wymuś UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Dodaj backend do path (gdy uruchamiane z backend/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from categories.models import Category
from machines.models import Machine
from services.models import Service
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from settlements.models import ContractSettlement
from archive.models import (
    ArchiveCategory, ArchiveArticle, ArchiveContract, ArchiveContractPosition,
    ArchivePositionCondition, ArchiveContractServiceFee, ArchiveContractSettlement,
)

# Import wszystkich modeli żeby SQLAlchemy skonfigurowało relacje
import auth.models  # noqa: F401
import contractors.models  # noqa: F401
import machines.models  # noqa: F401
import services.models  # noqa: F401
import additional_services.models  # noqa: F401
import contracts.models  # noqa: F401
import settings.models  # noqa: F401
import categories.models  # noqa: F401
import settlements.models  # noqa: F401
import archive.models  # noqa: F401
import audit.models  # noqa: F401
import contract_costs.models  # noqa: F401
import deliveries.models  # noqa: F401
import reservations.models  # noqa: F401
import integrations.fakturownia.models  # noqa: F401
import integrations.models  # noqa: F401


async def archive_table(
    db: AsyncSession, source_model, archive_model, label: str, batch_size: int = 500,
    parent_model=None, parent_fk: str = None,
):
    """Idempotentna archiwizacja: czyta batch z source, INSERT IGNORE do archive.

    Sprawdza istnienie po id (PK) — jeśli rekord o tym id już istnieje w archive,
    pomija go (idempotentność). Mapuje TYLKO wspólne kolumny (ignoruje drift typów).

    parent_model + parent_fk: jeśli podane, filtruje source po FK istniejącym w parent
    (pomija orphan rekordy — np. pozycje bez umowy).
    """
    stmt = select(source_model)
    if parent_model is not None and parent_fk:
        # Filtruj: tylko rekordy których FK parent istnieje w parent_model
        stmt = stmt.where(
            getattr(source_model, parent_fk).in_(
                select(parent_model.id)
            )
        )
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    if total is None:
        total = 0
    archived = 0
    offset = 0
    while offset < total:
        result = await db.execute(
            stmt.order_by(source_model.id).offset(offset).limit(batch_size)
        )
        rows = result.scalars().all()
        for row in rows:
            # Mapuj kolumny — tylko te które istnieją w obu modelach
            data = _map_row(row, archive_model)
            # Idempotent: sprawdź czy rekord o tym id już istnieje w archive
            existing = await db.execute(
                select(archive_model.id).where(archive_model.id == row.id)
            )
            if existing.scalar_one_or_none():
                continue
            obj = archive_model(**data)
            db.add(obj)
            archived += 1
        await db.commit()
        offset += batch_size
        print(f"  {label}: {archived}/{total} (offset {offset})")
    print(f"  {label}: DONE — {archived} nowych, {total} total")
    return archived


def _map_row(row, archive_model):
    """Mapuje kolumny z source do archive (tylko wspólne kolumny).

    Ignoruje kolumny występujące tylko w jednym modelu (drift typów między
    live a archive tabelami). Pomija Computed columns (unmapped_key w settlements).
    """
    data = {}
    source_cols = {c.name: c for c in row.__table__.columns}
    archive_cols = {c.name: c for c in archive_model.__table__.columns}
    for name, col in archive_cols.items():
        if name in source_cols:
            data[name] = getattr(row, name)
    return data


async def main():
    print("=" * 60)
    print("RAO-P2-071: Archive legacy data")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        print("\n[1/7] Kategorie -> archive_categories...")
        await archive_table(db, Category, ArchiveCategory, "Kategorie")

        print("\n[2/7] Maszyny+Usługi -> archive_articles...")
        await archive_table(db, Machine, ArchiveArticle, "Maszyny")
        await archive_table(db, Service, ArchiveArticle, "Usługi")

        print("\n[3/7] Umowy -> archive_contracts...")
        await archive_table(db, Contract, ArchiveContract, "Umowy")

        print("\n[4/7] Pozycje -> archive_contract_positions...")
        await archive_table(db, ContractPosition, ArchiveContractPosition, "Pozycje",
                            parent_model=ArchiveContract, parent_fk="contract_id")

        print("\n[5/7] Warunki -> archive_position_conditions...")
        await archive_table(db, PositionCondition, ArchivePositionCondition, "Warunki",
                            parent_model=ArchiveContractPosition, parent_fk="position_id")

        print("\n[6/7] Uslugi dodatkowe -> archive_contract_service_fees...")
        await archive_table(db, ContractServiceFee, ArchiveContractServiceFee, "Uslugi",
                            parent_model=ArchiveContract, parent_fk="contract_id")

        print("\n[7/7] Rozliczenia -> archive_contract_settlements...")
        await archive_table(db, ContractSettlement, ArchiveContractSettlement, "Rozliczenia",
                            parent_model=ArchiveContract, parent_fk="contract_id")

    print("\n" + "=" * 60)
    print("DONE — archiwizacja zakończona")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
