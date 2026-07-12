# Lekcja 08 — Migrations without Alembic

> Plik bazowy: `backend/main.py` (startup), `backend/database.py`
> Odpowiednik .NET: EF Core Migrations (`dotnet ef migrations add`)

RAO **nie używa Alembic** (odpowiednik EF Migrations dla SQLAlchemy). Schema zarządzane przez `Base.metadata.create_all` + idempotentne `ALTER TABLE ... IF NOT EXISTS`. To świadoma decyzja — prostota kosztem historii.

## Realny snippet z repo — startup migrations

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/main.py" lines="62-95" />

## 1. Trzy warstwy "migracji" w RAO

### Warstwa 1: `Base.metadata.create_all`

```python
@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

`Base.metadata.create_all` — generuje DDL z modeli SQLAlchemy i wykonuje `CREATE TABLE IF NOT EXISTS` dla **każdej** tabeli. Tworzy tylko tabele które **nie istnieją**. Nie modyfikuje istniejących.

Odpowiednik EF Core `Database.Migrate()` albo `EnsureCreated()` — ale `EnsureCreated` nie robi migracji, tylko tworzy schema z modelu. `create_all` jest jak `EnsureCreated`.

**Limitacja:** jeśli dodasz kolumnę do modelu, `create_all` **nie doda jej** do istniejącej tabeli. Tabela już istnieje → skip. Dlatego warstwa 2.

### Warstwa 2: `ALTER TABLE ... IF NOT EXISTS`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/main.py" lines="79-95" />

```python
await conn.execute(sa.text(
    "ALTER TABLE machines ADD COLUMN IF NOT EXISTS "
    "zasieg_m DECIMAL(8,2) NULL COMMENT 'Zasięg w metrach'"
))
```

Ręczne ALTER-y w startup. `IF NOT EXISTS` (MariaDB 10.5+) — idempotentne. Drugi restart nie rzuci "Duplicate column".

**Workflow dodawania kolumny:**
1. Dodaj `Column(...)` do `models.py`
2. Dodaj `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` w `main.py` startup
3. Zaktualizuj `spec/core/01_database.md` (DDL mirror)
4. Restart backendu → kolumna dodana
5. Drugi restart → `IF NOT EXISTS` skip, bez błędu

Odpowiednik EF Core: `dotnet ef migrations add AddColumn` → generuje `Up` method z `AddColumn`. Tu robisz to ręcznie w SQL.

### Warstwa 3: `spec/core/01_database.md` — DDL mirror

Plik z **finalnym DDL** (nie inkrementalne ALTER-y). Single source of truth dla schema. Każda zmiana = update tego pliku. To nie jest wykonywane, to dokumentacja.

Odpowiednik EF Core `__MigrationSnapshot` — model snapshot w migracjach. Tu ręczny markdown.

## 2. `@app.on_event("startup")` — hook na start

```python
@app.on_event("startup")
async def startup_migrations():
    ...
```

FastAPI wywołuje to przy starcie aplikacji (po `uvicorn main:app`). Jednorazowo. Odpowiednik C# `Program.cs` `app.Services.Initialize()` albo `IHostedService.StartAsync`.

**Nowsze FastAPI** (0.93+) zaleca `lifespan` context manager zamiast `on_event`. W tym repo jeszcze `on_event` (działa, deprecated).

## 3. `engine.begin()` — transactional DDL

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
    await conn.execute(sa.text("ALTER TABLE ..."))
```

`engine.begin()` — otwiera connection w transakcji. Wszystko w bloku commituje się razem. Jeśli ALTER rzuci → rollback, `create_all` też cofnięte.

**MariaDB** wspiera transactional DDL (od 10.3+). MySQL nie do końca. W praktyce ALTER jest auto-commit, ale `begin()` nie zaszkodzi.

## 4. `run_sync` — sync function w async context

```python
await conn.run_sync(Base.metadata.create_all)
```

`Base.metadata.create_all` to **sync** function (SQLAlchemy core jest sync). `run_sync` uruchamia ją w threadpool, awaituje wynik. To bridge między sync SQLAlchemy core a async engine.

W async nie można wywołać sync function bezpośrednio (zablokuje event loop). `run_sync` to wrapper.

## 5. Dlaczego nie Alembic?

Alembic to pełnoprawny migration tool (jak EF Migrations):
- Generuje migration files z `alembic revision --autogenerate`
- `Up`/`Down` methods
- `alembic upgrade head` / `downgrade`
- Historia zmian w tabeli `alembic_version`

**RAO go nie używa bo:**
1. **Single developer, forward-only.** Brak potrzeby rollbacku.
2. **Brak multi-env.** Jeden dev DB, jeden prod.
3. **Prostota.** Mniej plików, mniej narzędzi.
4. **`create_all` + ALTER wystarcza.** Schema nie jest skomplikowane.

**Koszty:**
1. **Brak historii schema.** Nie widać co się zmieniało w czasie.
2. **Ręczne ALTER.** Łatwo zapomnieć dodać ALTER w `main.py` po zmianie modelu.
3. **Brak downgrade.** Jeśli coś pójdzie źle, ręczny SQL.
4. **Brak multi-env sync.** Trzeba pamiętać uruchomić backend na nowym env, żeby migracje się zrobiły.

**Kiedy Alembic by był lepszy:**
- Zespół >1 deva
- Multi-env (dev/staging/prod)
- Potrzebny rollback
- Schema zmienia się często

## 6. `IF NOT EXISTS` — idempotentność kluczowa

```python
"ALTER TABLE machines ADD COLUMN IF NOT EXISTS zasieg_m DECIMAL(8,2) NULL"
```

`IF NOT EXISTS` (MariaDB 10.5+, MySQL 8.0+) — skip jeśli kolumna istnieje. Bez tego drugi restart rzuci `Duplicate column name`. Z `IF NOT EXISTS` — idempotentne.

**Stara MariaDB** (<10.5) nie wspiera `IF NOT EXISTS` na `ADD COLUMN`. Wtedy try/except:
```python
try:
    await conn.execute(sa.text("ALTER TABLE machines ADD COLUMN zasieg_m DECIMAL(8,2) NULL"))
except Exception:
    pass   # kolumna już istnieje
```

W tym repo zakładają MariaDB 10.5+ — `IF NOT EXISTS` wszędzie.

## 7. `sa.text()` — raw SQL

```python
await conn.execute(sa.text("ALTER TABLE ..."))
```

`sa.text("SQL")` — wrapper na raw SQL. SQLAlchemy nie próbuje parse'ować, wysyła jak jest. Odpowiednik EF Core `Database.ExecuteSqlRawAsync`.

**Uwaga:** `sa.text` z f-stringiem i user input = SQL injection. Tu ALTER-y są hardcoded (bez user input), bezpieczne. Nigdy `sa.text(f"ALTER TABLE {user_input}")`.

## 8. 4-plikowa reguła zmiany DB

Z `AGENTS.md` — każda zmiana DB = 4 pliki:

1. `spec/core/01_database.md` — finalny DDL (mirror)
2. `backend/<feature>/models.py` — SQLAlchemy model
3. `backend/main.py` startup — `ALTER ... IF NOT EXISTS`
4. Weryfikacja: restart + `DESCRIBE` + drugi restart

Bez #1 → nie widać schema w spec. Bez #3 → nowy env (czysty DB) dostanie tabelę bez kolumny. Bez #4 → nie wiadomo czy idempotentne.

## 9. Brak `DROP COLUMN` / `DROP TABLE`

RAO polityka: **forward-only, bez dropów**. Jeśli kolumna niepotrzebna → zostaje (lub rename na `_deprecated_*`). Drop wymaga zgody usera + backupu.

Odpowiednik EF Core `Down` method — tu nie ma. Jeśli coś zepsute, ręczny SQL po backupie.

**Powód:** prod data jest cenne. Drop kolumny = utrata danych. Forward-only wymusza myślenie przed zmianą.

## 10. `MODIFY COLUMN` — nie na prod

Zmiana typu kolumny (np. `VARCHAR(50)` → `VARCHAR(100)`) przez `ALTER TABLE ... MODIFY COLUMN` na prod danych = ryzyko. RAO tego unika. Jeśli trzeba → backup + test na kopii + zgoda usera.

Odpowiednik EF Core `AlterColumn` migration — tu robione ostrożnie.

## Gotchas dla .NET deva

1. **Brak migracji.** `create_all` + `ALTER IF NOT EXISTS` zamiast `dotnet ef migrations add`.
2. **`create_all` nie modyfikuje istniejących tabel.** Nowe kolumny wymagają ręcznego ALTER w `main.py`.
3. **`IF NOT EXISTS` obowiązkowe.** Bez tego drugi restart rzuci Duplicate column.
4. **4-plikowa reguła.** models.py + main.py + spec + weryfikacja.
5. **Brak downgrade.** Forward-only. Drop wymaga zgody.
6. **`sa.text()` = raw SQL.** Hardcoded OK, user input = injection.
7. **`run_sync` bridge.** Sync SQLAlchemy core w async engine.
8. **`@app.on_event("startup")` deprecated.** Nowszy: `lifespan` context manager.
9. **`engine.begin()` transactional.** Ale ALTER auto-commit na MySQL — nie polegaj.
10. **Spec `01_database.md` to DDL mirror.** Nie wykonywane, dokumentacja. Single source of truth.

## Quiz

1. Dlaczego RAO nie używa Alembic? (prostota, single-dev, forward-only)
2. Czym różni się `create_all` od ALTER w main.py? (create_all tworzy nowe tabele, ALTER dodaje kolumny do istniejących)
3. Dlaczego `IF NOT EXISTS` jest obowiązkowe? (idempotentność — drugi restart bez Duplicate column)
4. Co to "4-plikowa reguła"? (models.py + main.py + spec + weryfikacja)
5. Czym jest `sa.text()`? (wrapper na raw SQL — hardcoded OK, user input = injection)

→ `python learning/quiz/quiz.py --topic migrations --n 5`
