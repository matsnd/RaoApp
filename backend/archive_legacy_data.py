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

# Dodaj backend do path (gdy uruchamiane z backend/)
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from categories.models import Category
from articles.models import Article
from contracts.models import Contract, ContractPosition, PositionCondition, ContractServiceFee
from settlements.models import ContractSettlement
from archive.models import (
    ArchiveCategory, ArchiveArticle, ArchiveContract, ArchiveContractPosition,
    ArchivePositionCondition, ArchiveContractServiceFee, ArchiveContractSettlement,
)

# Import wszystkich modeli żeby SQLAlchemy skonfigurowało relacje
import auth.models  # noqa: F401
import contractors.models  # noqa: F401
import articles.models  # noqa: F401
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
    db: AsyncSession, source_model, archive_model, label: str, batch_size: int = 500
):
    """Idempotentna archiwizacja: czyta batch z source, INSERT IGNORE do archive.

    Sprawdza istnienie po id (PK) — jeśli rekord o tym id już istnieje w archive,
    pomija go (idempotentność). Mapuje TYLKO wspólne kolumny (ignoruje drift typów).
    """
    total = await db.scalar(select(func.count()).select_from(source_model))
    if total is None:
        total = 0
    archived = 0
    offset = 0
    while offset < total:
        result = await db.execute(
            select(source_model).order_by(source_model.id).offset(offset).limit(batch_size)
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
        print("\n[1/7] Kategorie → archive_categories...")
        await archive_table(db, Category, ArchiveCategory, "Kategorie")

        print("\n[2/7] Artykuły → archive_articles...")
        await archive_table(db, Article, ArchiveArticle, "Artykuły")

        print("\n[3/7] Umowy → archive_contracts...")
        await archive_table(db, Contract, ArchiveContract, "Umowy")

        print("\n[4/7] Pozycje → archive_contract_positions...")
        await archive_table(db, ContractPosition, ArchiveContractPosition, "Pozycje")

        print("\n[5/7] Warunki → archive_position_conditions...")
        await archive_table(db, PositionCondition, ArchivePositionCondition, "Warunki")

        print("\n[6/7] Usługi dodatkowe → archive_contract_service_fees...")
        await archive_table(db, ContractServiceFee, ArchiveContractServiceFee, "Usługi")

        print("\n[7/7] Rozliczenia → archive_contract_settlements...")
        await archive_table(db, ContractSettlement, ArchiveContractSettlement, "Rozliczenia")

    print("\n" + "=" * 60)
    print("DONE — archiwizacja zakończona")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
