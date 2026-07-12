# Lekcja 06 — Async SQLAlchemy session

> Plik bazowy: `backend/articles/service.py`, `backend/database.py`
> Odpowiednik .NET: `DbContext` + async + LINQ

SQLAlchemy 2.0 async to odpowiednik EF Core async. Sesja = unit of work, query = LINQ. Składnia inna, koncept ten sam.

## Realny snippet z repo — engine + session factory

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/database.py" lines="1-33" />

## Realny snippet z repo — query w service

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="27-46" />

## 1. Engine — odpowiednik `DbContextOptions`

```python
engine = create_async_engine(
    settings.RAO_DATABASE_URL,    # mysql+asyncmy://rao_user:pass@localhost/rao_new
    echo=False,
    poolclass=NullPool,
)
```

`create_async_engine` — async driver (`asyncmy` dla MariaDB/MySQL). `NullPool` — brak poolingu połączeń (każde połączenie świeże). W produkcji z wieloma req/s używa się `QueuePool`, ale tu NullPool dla prostoty.

Odpowiednik C#:
```csharp
options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString));
```

`RAO_DATABASE_URL` — URL stylu `mysql+asyncmy://user:pass@host/db`. `+asyncmy` to driver. SQLAlchemy wspiera też `+aiomysql`.

## 2. `async_sessionmaker` — factory sesji

```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

Factory sesji. `expire_on_commit=False` — **kluczowe** — po `commit()` obiekty nie są "expired" (nie triggerują refetch z DB). Default to `True`, co w async jest problemem (lazy refetch po commit rzuca `MissingGreenlet`).

Odpowiednik C# `IDbContextFactory<RaoDbContext>` — factory, nie singleton. Każdy request dostaje świeżą sesję.

## 3. `get_db` — sesja per request

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

`async with` — context manager, zamknie sesję po końcu. `yield` — FastAPI wstrzykuje sesję do endpointu, po końcu wraca do generatora (cleanup).

Sesja = unit of work. Wszystkie zmiany (`add`, `delete`, modyfikacje pól) są trackowane. `commit()` flushuje do DB. Odpowiednik C# `DbContext.SaveChanges()`.

## 4. `select()` — odpowiednik LINQ

EF Core:
```csharp
var article = await _db.Articles
    .Where(a => a.Id == id)
    .FirstOrDefaultAsync();
```

SQLAlchemy:
```python
stmt = select(Article).where(Article.id == article_id)
result = await db.execute(stmt)
article = result.scalar_one_or_none()
```

**Różnice:**

| EF Core LINQ | SQLAlchemy |
|--------------|------------|
| `_db.Articles.Where(...)` | `select(Article).where(...)` |
| `a => a.Id == id` | `Article.id == article_id` |
| `.FirstOrDefaultAsync()` | `result.scalar_one_or_none()` |
| `.ToListAsync()` | `result.scalars().all()` |
| `.CountAsync()` | `select(func.count())` + `scalar_one()` |
| `.OrderBy(a => a.Name)` | `.order_by(Article.name)` |
| `.Skip(n).Take(m)` | `.offset(n).limit(m)` |
| `.Include(a => a.Category)` | `selectinload(Article.category)` lub explicit JOIN |

## 5. `scalar_one_or_none()` vs `scalars().all()`

```python
result = await db.execute(stmt)
article = result.scalar_one_or_none()   # 1 lub 0, jeśli >1 → exception
articles = result.scalars().all()       # lista
```

`scalar_one_or_none()` — zwraca pojedynczy obiekt lub None. Jeśli query zwraca >1 wiersz → `MultipleResultsFound` exception. Odpowiednik C# `SingleOrDefault` (ale rzuca na >1, jak `Single` z tolerance dla 0).

`scalars().all()` — lista wszystkich. `.scalars()` "odpakowuje" tuple (SQLAlchemy zwraca wiersze jako tuple, `.scalars()` bierze pierwszą kolumnę).

`scalar_one()` — dokładnie 1, rzuca jeśli 0 lub >1. Odpowiednik `Single`.

## 6. `db.get(Model, id)` — fetch by PK

```python
article = await db.get(Article, article_id)
```

Skrót dla `select(Article).where(Article.id == id)`. Odpowiednik EF Core `FindAsync(id)`. **Cacheuje w sesji** — jeśli ten sam obiekt już załadowany, zwraca z sesji bez DB query.

## 7. `db.add()`, `db.commit()`, `db.refresh()`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="113-119" />

```python
article = Article(**data.model_dump(), created_at=datetime.utcnow())
db.add(article)          # track w sesji (INSERT pending)
await db.commit()        # flush do DB
await db.refresh(article)  # reload z DB (np. dla autoincrement id)
return article
```

`db.add(obj)` — dodaje do sesji (track). Nie wykonuje SQL. `await db.commit()` — flush + commit transaction. `await db.refresh(obj)` — reload z DB (żeby dostać `id` po autoincrement, defaults z DB, etc.).

Odpowiednik C# `_db.Articles.Add(entity); await _db.SaveChangesAsync();`. EF Core automatycznie refreshuje autoincrement po SaveChanges — SQLAlchemy wymaga jawnego `refresh()`.

## 8. `db.execute(update(...))` — bulk update

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/service.py" lines="42-45" />

```python
await db.execute(
    update(User).where(User.id == user.id).values(last_login=datetime.utcnow())
)
await db.commit()
await db.refresh(user)
```

`update(User).where(...).values(...)` — UPDATE statement. Wykonuje jedno UPDATE SQL, nie ładuje entity. Odpowiednik EF Core `ExecuteUpdateAsync` (EF 7+).

**Ważne:** po `db.execute(update(...))`, obiekt `user` w sesji jest **stale** (ma stare wartości). `db.refresh(user)` reloaduje. Albo `expire_on_commit=False` + commit.

## 9. `setattr` — dynamiczne ustawianie pola

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="121-130" />

```python
for field, value in data.model_dump(exclude_unset=True).items():
    setattr(article, field, value)
article.updated_at = datetime.utcnow()
await db.commit()
```

`setattr(obj, "name", "x")` = `obj.name = "x"` ale z dynamiczną nazwą. Używane do partial update — iteruj po polach wysłanych przez klienta, ustaw na entity.

Odpowiednik C#:
```csharp
foreach (var (field, value) in updateDict)
    typeof(Article).GetProperty(field).SetValue(entity, value);
```

Albo EF Core `EntityEntry.CurrentValues.AssignValues`. W Pythonie `setattr` jest idiomatyczne i bezpieczne (jeśli `field` pochodzi z `model_dump`, nie ma ryzyka wstrzyknięcia nazwy).

## 10. Explicit JOIN — zamiast `Include`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="190-197" />

```python
stmt = (
    select(Contract.id, Contract.number, Contract.date_from, Contract.date_to, Contractor.name)
    .join(ContractPosition, ContractPosition.contract_id == Contract.id)
    .join(Contractor, Contract.contractor_id == Contractor.id)
    .where(ContractPosition.article_id == article_id)
    .where(Contract.date_from <= date_to)
    .where(Contract.date_to >= date_from)
)
```

`select(Contract.id, Contract.number, ...)` — wybiera konkretne kolumny (nie całe entity). `.join(ContractPosition, onclause)` — JOIN. Wynik to tuple, nie entity.

Odpowiednik EF Core:
```csharp
var q = from c in _db.Contracts
        join cp in _db.ContractPositions on c.Id equals cp.ContractId
        join con in _db.Contractors on c.ContractorId equals con.Id
        where cp.ArticleId == articleId
        select new { c.Id, c.Number, c.DateFrom, c.DateTo, con.Name };
```

**Dlaczego explicit JOIN zamiast `Include`?** W async SQLAlchemy lazy loading nie działa. `selectinload` działa ale dodaje osobne query. Explicit JOIN jest przewidywalny — jedno query, konkretne kolumny, brak N+1.

## 11. N+1 — batch fetch

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="48-65" />

```python
article_ids = [a.id for a in articles]
category_ids = {a.category_id for a in articles if a.category_id}

cat_map = {}
if category_ids:
    cat_result = await db.execute(
        select(Category.id, Category.name).where(Category.id.in_(category_ids))
    )
    cat_map = dict(cat_result.all())
```

Zamiast dla każdego article fetchować category (N+1), batch: zbierz wszystkie `category_id`, jedno query `WHERE id IN (...)`, zbuduj dict `{id: name}`. Odpowiednik EF Core `Include` + `Select` z projekcją, albo ręczny batch.

`dict(cat_result.all())` — `cat_result.all()` zwraca listę tuple `[(id, name), ...]`, `dict()` konwertuje na `{id: name}`. Sprytny idiom.

## Gotchas dla .NET deva

1. **`expire_on_commit=False` jest obowiązkowe w async.** Inaczej lazy refetch po commit rzuca `MissingGreenlet`.
2. **`scalar_one_or_none()` rzuca na >1.** Nie jak `FirstOrDefault` — jak `SingleOrDefault` z strict checking.
3. **`db.refresh()` po `commit()`.** EF Core robi to automatycznie, SQLAlchemy nie.
4. **Lazy loading nie działa w async.** Używaj explicit JOIN lub `selectinload`.
5. **`select(Col1, Col2)` zwraca tuple, nie entity.** `select(Entity)` zwraca entity.
6. **`scalars().all()` vs `.all()`.** `.all()` zwraca tuple, `.scalars().all()` obiekty.
7. **`setattr` dla partial update.** Idiomatyczne, bezpieczne jeśli field z `model_dump`.
8. **`db.execute(update(...))` nie odświeża entity.** Trzeba `refresh()` lub `expire_on_commit=False`.
9. **`NullPool` = brak poolingu.** OK dla dev, w prod `QueuePool` z `pool_size`, `max_overflow`.
10. **`asyncmy` driver, nie `pymysql`.** Async wymaga async drivera. `pymysql` jest sync.

## Quiz

1. Czym jest `AsyncSession`? (unit of work, odpowiednik DbContext, per-request)
2. Dlaczego `expire_on_commit=False`? (lazy refetch po commit rzuca MissingGreenlet w async)
3. Czym różni się `scalar_one_or_none()` od `scalars().all()`? (1 lub 0 vs lista)
4. Co robi `db.refresh(article)` po `commit()`? (reload z DB — autoincrement id, defaults)
5. Dlaczego explicit JOIN zamiast `Include`? (lazy loading nie działa w async, JOIN jest przewidywalny)

→ `python learning/quiz/quiz.py --topic async --n 5`
