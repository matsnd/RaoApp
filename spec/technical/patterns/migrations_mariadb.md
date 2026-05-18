# Migrations Pattern (MariaDB)

## Opis
Wzorzec do migracji bazy danych MariaDB w RAO. Kluczowa zasada: **RAO nie używa Alembic**.

## Architektura migracji

RAO zarządza schema DB przez:
1. Modele SQLAlchemy w `backend/<feature>/models.py`
2. `Base.metadata.create_all` przy starcie (tworzy nowe tabele)
3. Idempotentne `ALTER TABLE ... IF NOT EXISTS` w `backend/main.py` startup
4. DDL w `spec/core/01_database.md` jako single source of truth

## Zasady

### ✅ DO
- Zaktualizuj `spec/core/01_database.md` (finalny DDL)
- Zaktualizuj `backend/<feature>/models.py` (SQLAlchemy)
- Dodaj `ALTER TABLE ... IF NOT EXISTS` w `backend/main.py` startup
- Użyj `IF NOT EXISTS` dla idempotentności
- Weryfikuj przez restart backendu + `DESCRIBE` + drugi restart

### ❌ NIE
- NIE używaj Alembic
- NIE rób ad-hoc `ALTER TABLE` w mariadb CLI bez równoległej zmiany w `main.py`
- NIE używaj `ALTER` bez `IF NOT EXISTS` (drugi restart rzuci "Duplicate column")
- NIE rób `DROP COLUMN` / `DROP TABLE` bez wyraźnej zgody użytkownika i backupu
- NIE modyfikuj typu kolumny przez naked `MODIFY COLUMN` na produkcyjnych danych

## Procedura migracji

### Krok 1: Zaktualizuj spec/core/01_database.md
```sql
-- spec/core/01_database.md
CREATE TABLE contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    number VARCHAR(50) NOT NULL,
    delivery_address VARCHAR(255) NULL,  -- NOWA KOLUMNA
    ...
);
```

### Krok 2: Zaktualizuj backend/<feature>/models.py
```python
# backend/contracts/models.py
class Contract(Base):
    __tablename__ = "contract"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(50), nullable=False)
    delivery_address = Column(String(255), nullable=True)  # NOWE POLE
    ...
```

### Krok 3: Dodaj ALTER w backend/main.py startup
```python
# backend/main.py
@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Idempotentne ADD COLUMN
        await conn.execute(sa.text(
            "ALTER TABLE contract ADD COLUMN IF NOT EXISTS "
            "delivery_address VARCHAR(255) NULL"
        ))
```

### Krok 4: Weryfikacja
```bash
# 1. Restart backendu
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000

# 2. Sprawdź schema w MariaDB
mariadb -u rao_user -p rao_new
DESCRIBE contract;
# Powinno pokazać delivery_address

# 3. Drugi restart (bez błędu = idempotentne)
# Ctrl+C + uruchom ponownie
# Jeśli nie ma błędu "Duplicate column" → OK
```

## Idempotentne ALTER (MariaDB 10.6+)

### MariaDB 10.6+
```sql
ALTER TABLE contract ADD COLUMN IF NOT EXISTS delivery_address VARCHAR(255) NULL;
```

### Starsze wersje MariaDB (<10.6)
```python
# backend/main.py
@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Try-except dla starszych wersji
        try:
            await conn.execute(sa.text(
                "ALTER TABLE contract ADD COLUMN "
                "delivery_address VARCHAR(255) NULL"
            ))
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Column already exists, skipping")
            else:
                raise
```

## Typy zmian

### Dodanie kolumny
```python
await conn.execute(sa.text(
    "ALTER TABLE contract ADD COLUMN IF NOT EXISTS "
    "new_field VARCHAR(255) NULL"
))
```

### Dodanie indeksu
```python
await conn.execute(sa.text(
    "CREATE INDEX IF NOT EXISTS idx_contract_number "
    "ON contract(number)"
))
```

### Dodanie foreign key
```python
await conn.execute(sa.text(
    "ALTER TABLE contract ADD CONSTRAINT IF NOT EXISTS "
    "fk_contract_contractor "
    "FOREIGN KEY (contractor_id) REFERENCES contractor(id)"
))
```

## Backup przed DROP

```bash
# Backup całej bazy
mariadb-dump -u rao_user -p rao_new > backup_$(date +%Y%m%d).sql

# Backup konkretnej tabeli
mariadb-dump -u rao_user -p rao_new contract > contract_backup.sql
```

## Użycie w RAO

### Development
- Każda zmiana DB = 4 pliki (spec, model, main.py, weryfikacja)
- Idempotentne migracje dla łatwego restartu
- Single source of truth w spec/core/01_database.md

### Testing
- Czyste środowisko testowe = automatyczne tworzenie schema
- Idempotentność = brak błędów przy wielokrotnym restartie

### Production
- Forward-only migrations (brak rollbacku)
- Backup przed DROP
- Planowanie maintenance window

## Powiązane
- Spec: `spec/core/01_database.md`
- Process: `spec/process/migrations.md`
- Models: `backend/<feature>/models.py`
- Startup: `backend/main.py`
- AGENTS.md: sekcja "Migracje DB — DETERMINISTYCZNE"

## Wymagania
- MariaDB 10.6+ (dla `IF NOT EXISTS` w ALTER)
- SQLAlchemy async
- AsyncSessionLocal
- Dostęp do mariadb CLI