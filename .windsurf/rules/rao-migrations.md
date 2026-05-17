---
trigger: glob
description: Deterministyczne idempotentne migracje DB w RAO — aktywne przy edycji models/main.py/DDL
globs: backend/main.py, backend/**/models.py, backend/database.py, spec/01_DATABASE_DDL.md, backend/migrate.py
---

# Deterministyczne migracje DB w RAO

RAO **nie używa Alembic** (jest w `requirements.txt` ale nieskonfigurowany). Schema zarządzane przez:
- `Base.metadata.create_all` — tworzenie nowych tabel z modeli SQLAlchemy
- **Idempotentne `ALTER TABLE ... IF NOT EXISTS`** w `@app.on_event("startup")` w `backend/main.py`
- DDL w `spec/01_DATABASE_DDL.md` jako single source of truth

## ⚠️ Każda zmiana DB MUSI przejść przez 4 warstwy w tej kolejności

```
1. spec/01_DATABASE_DDL.md
   → Zaktualizuj DDL tabeli — finalny stan po migracji
   → To jest dokumentacja dla następnego dewelopera/agenta

2. backend/<feature>/models.py
   → Dodaj/zmień kolumnę w SQLAlchemy modelu (Column, ForeignKey, relationship)
   → Pilnuj zgodności typów Python ↔ MariaDB (Decimal, DateTime, Enum, String(N))

3. backend/main.py — @app.on_event("startup")
   → Dodaj idempotentny ALTER (przykłady niżej)

4. Weryfikacja: restart backend + DESCRIBE + drugi restart bez błędu
```

## Wzorce idempotentnych migracji (kopiuj z tych)

```python
import sqlalchemy as sa

@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Wzorzec A: nowa kolumna (MariaDB 10.6+)
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "delivery_address VARCHAR(255) NULL"
        ))

        # Wzorzec B: indeks
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD INDEX IF NOT EXISTS "
            "idx_contracts_delivery (delivery_address)"
        ))

        # Wzorzec C: nowa tabela
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS deliveries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_id INT NOT NULL,
                delivered_at DATETIME NOT NULL,
                FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
            )
        """))

        # Wzorzec D: fallback dla MariaDB <10.6 (bez ADD COLUMN IF NOT EXISTS)
        try:
            await conn.execute(sa.text(
                "ALTER TABLE articles ADD COLUMN duplicated_from INT NULL"
            ))
        except Exception as e:
            if "Duplicate column" not in str(e) and "exists" not in str(e):
                raise

        # Wzorzec E: oznacz większą migrację komentarzem z datą/zadaniem
        # --- Migration 2026-05-17: dostawy do umów (B9 backlog) ---
        # ...
```

## 🚫 ZAKAZANE praktyki

- ❌ Wpisywanie `ALTER TABLE` ręcznie w mariadb CLI **bez** dodania go do `main.py`
  → następny agent na czystym środowisku dostanie schema mismatch
- ❌ ALTER bez `IF NOT EXISTS` ani try/except → drugi restart rzuci "Duplicate column"
- ❌ DROP COLUMN / DROP TABLE bez **wyraźnej zgody user-a** i backupu (`mariadb-dump`)
  → migracje są **forward-only**, brak rollbacku
- ❌ `MODIFY COLUMN` typu na produkcyjnych danych → najpierw nowa kolumna → backfill → swap
- ❌ Aktualizacja `models.py` bez aktualizacji DDL w `spec/01_DATABASE_DDL.md`
  → spec staje się kłamstwem, niszczy single source of truth

## ✅ Migration checklist (sprawdź PRZED zakończeniem zadania)

- [ ] `spec/01_DATABASE_DDL.md` zaktualizowany — finalny DDL widoczny
- [ ] `backend/<feature>/models.py` ma nowe pole/relację
- [ ] `backend/main.py` startup ma idempotentny ALTER/CREATE z `IF NOT EXISTS` (lub try/except)
- [ ] Restart backendu nie rzuca błędów (sprawdź logi uvicorn)
- [ ] `DESCRIBE <table>` pokazuje oczekiwany stan
- [ ] Drugi restart też się udaje (test idempotentności)

## Komendy weryfikacyjne

```pwsh
# Stan tabeli
mariadb -u rao_user -pRaoPass2026! rao_new -e "DESCRIBE contracts;"

# Lista wszystkich tabel
mariadb -u rao_user -pRaoPass2026! rao_new -e "SHOW TABLES;"

# Backup przed destruktywną zmianą
mariadb-dump -u rao_user -pRaoPass2026! rao_new > backup-$(Get-Date -Format yyyy-MM-dd-HHmm).sql
```

## Plik `backend/migrate.py` to NIE migrator schema

To jednorazowy skrypt migracji **danych** ze starej bazy (`toolsmart_roa_fake` → `rao_new`). Nie używaj go jako referencji dla zmian schema — używaj wzorców z `main.py` startup event.
