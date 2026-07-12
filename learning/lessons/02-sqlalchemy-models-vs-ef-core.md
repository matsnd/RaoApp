# Lekcja 02 — SQLAlchemy models vs EF Core

> Plik bazowy: `backend/articles/models.py`
> Odpowiednik .NET: EF Core entities + `DbContext` + Fluent API

SQLAlchemy to ORM Pythona. W tym repo używamy **SQLAlchemy 2.0 async** z MariaDB. Konceptualnie bardzo blisko EF Core, ale inna składnia i kilka ważnych różnic.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/models.py" lines="1-62" />

## 1. Model = klasa dziedzicząca po `Base`

EF Core:
```csharp
public class Article
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public bool IsService { get; set; }
    public decimal? ReplacementValue { get; set; }
    public int? CategoryId { get; set; }
    public Category? Category { get; set; }   // nav property
}
```

SQLAlchemy:
```python
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    is_service = Column(Boolean, nullable=False, default=False)
    replacement_value = Column(Numeric(18, 2), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    # category = relationship("Category")   # nav property (opcjonalne)
```

**Kluczowe różnice:**

| EF Core | SQLAlchemy |
|---------|------------|
| Properties `get;set;` | `Column(...)` jako atrybut klasy |
| Konwencja (Id → PK) | Jawny `primary_key=True` |
| `[MaxLength(200)]` lub Fluent | `String(200)` w `Column` |
| `?` nullable | `nullable=True/False` |
| `decimal` → `decimal(18,2)` Fluent | `Numeric(18, 2)` w `Column` |
| Nav property auto | `relationship()` jawne |
| Migration z `dotnet ef` | **Brak migracji** — `create_all` + ALTER (lekcja 08) |

## 2. `Base` — registry wszystkich modeli

```python
from database import Base

class Article(Base):
    __tablename__ = "articles"
    ...
```

`Base` to wspólna klasa bazowa z `DeclarativeBase`. W `database.py` jest zdefiniowana. Wszystkie modele dziedziczą po niej — to pozwala `Base.metadata.create_all(engine)` stworzyć wszystkie tabele naraz.

Odpowiednik EF Core: `DbContext` z `DbSet<Article>`. Ale w SQLAlchemy **nie ma `DbContext`** — modele są globalne, `Base.metadata` jest singletonem. Sesja (`AsyncSession`) to odpowiednik `DbContext`, ale jest lightweight i tworzona per-request.

## 3. `Column` — typy

Widzisz w `models.py`:

```python
id = Column(Integer, primary_key=True, autoincrement=True)
name = Column(String(200), nullable=False)
is_service = Column(Boolean, nullable=False, default=False)
replacement_value = Column(Numeric(18, 2), nullable=True)
category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
created_at = Column(DateTime, nullable=False)
technical_attributes = Column(JSON, nullable=True)        # MariaDB JSON type
fakturownia_product_id = Column(BigInteger, nullable=True)  # bigint
dodatki = Column(Text, nullable=True, comment="Dodatkowe akcesoria")
```

Mapowanie typów:

| C# / EF Core | SQLAlchemy | MariaDB |
|---|---|---|
| `int` | `Integer` | INT |
| `long` | `BigInteger` | BIGINT |
| `string` (max 200) | `String(200)` | VARCHAR(200) |
| `string` ( unlimited) | `Text` | TEXT |
| `bool` | `Boolean` | TINYINT(1) |
| `decimal` | `Numeric(p, s)` | DECIMAL(p, s) |
| `DateTime` | `DateTime` | DATETIME |
| `Date` | `Date` | DATE |
| `Dictionary<string, object>` | `JSON` | JSON |
| `byte[]` | `LargeBinary` | BLOB |

**Ważne:** `Numeric(18, 2)` to **Decimal**, nie float. Dla pieniędzy ZAWSZE `Numeric`, nigdy `Float`. W C# to `decimal` (nie `double`).

## 4. `ForeignKey` — jawne, nie konwencja

EF Core:
```csharp
public int? CategoryId { get; set; }
public Category? Category { get; set; }   // konwencja: CategoryId → FK
```

SQLAlchemy:
```python
category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
```

**Jawne określenie** kolumny referowanej (`categories.id`). `ondelete="SET NULL"` to odpowiednik EF `.OnDelete(DeleteBehavior.SetNull)`.

Ważne: `ForeignKey("categories.id")` — string z ` tabela.kolumna`. Nie referencja do klasy (bo może być jeszcze niezdefiniowana — circular import).

## 5. `relationship()` — nav property (opcjonalne!)

W `models.py` tego repo **nie ma `relationship()`** w `Article`. To świadome — używają explicit JOIN w service.py zamiast lazy loading.

Gdyby było:
```python
category = relationship("Category", back_populates="articles")
```

Odpowiednik EF Core nav property. **Ale uwaga:** w async SQLAlchemy **lazy loading nie działa** domyślnie (wymaga `selectinload`/`joinedload` jawnie). Dlatego w tym repo wolą explicit JOIN — bezpieczniej i przewidywalniej.

## 6. `__table_args__` — indeksy i constrainty

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/models.py" lines="51-62" />

```python
__table_args__ = (
    Index("idx_art_name", "name"),
    Index("idx_art_category", "category_id"),
    Index("idx_articles_archival", "is_archival"),
    ...
)
```

Tuple z `Index(...)` obiektami. Odpowiednik EF Core:
```csharp
modelBuilder.Entity<Article>()
    .HasIndex(a => a.Name)
    .HasName("idx_art_name");
```

`Index("name", "col1", "col2")` z wieloma kolumnami = composite index.

## 7. `default` vs `server_default` — subtelne!

W `models.py:31`:
```python
is_archival = Column(Boolean, nullable=False, default=False, server_default="0")
```

- **`default=False`** — Python-side default. SQLAlchemy ustawi `False` gdy INSERT bez wartości. **DB nie wie o tym** — jeśli insert z raw SQL, default nie działa.
- **`server_default="0"`** — DB-side default. `DEFAULT 0` w DDL. Działa zawsze, nawet raw SQL.

W tym repo dają **oba** — defensive. `server_default` jako string bo to literal SQL.

## 8. `comment=` — column comment

```python
zasieg_m = Column(Numeric(8, 2), nullable=True, comment="Zasięg w metrach")
```

MariaDB `COMMENT 'Zasięg w metrach'` w DDL. Widoczne w `SHOW FULL COLUMNS`. EF Core nie ma tego bezpośrednio (wymaga Fluent `.HasComment()`).

## 9. Jak to mapuje się do DB?

`Base.metadata.create_all(engine)` generuje DDL z modeli. Dla `Article`:
```sql
CREATE TABLE articles (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    is_service BOOLEAN NOT NULL,
    is_archival BOOLEAN NOT NULL DEFAULT 0,
    category_id INT,
    ...
    PRIMARY KEY (id),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);
CREATE INDEX idx_art_name ON articles (name);
...
```

**Ale uwaga:** `create_all` tworzy tylko tabele które **nie istnieją**. Nie modyfikuje istniejących. Dlatego w tym repo są `ALTER TABLE ... IF NOT EXISTS` w `main.py` startup (lekcja 08).

## 10. Brak migracji — dlaczego?

EF Core ma `dotnet ef migrations add` → generuje `Up`/`Down` metody. SQLAlchemy ma Alembic, ale **to repo go nie używa**. Powody:

1. Single-developer, forward-only
2. `create_all` + `ALTER IF NOT EXISTS` wystarcza
3. Brak konieczności rollbacku
4. Mniej plików do utrzymania

Koszt: brak historii zmian schema. Zysk: prostota. Więcej w lekcji 08.

## Gotchas dla .NET deva

1. **Brak `DbContext` jako singletonu.** `Base.metadata` jest globalne, sesje per-request.
2. **Lazy loading nie działa w async.** Używaj explicit JOIN lub `selectinload`.
3. **`Column` to atrybut klasy, nie instancji.** Definiujesz na poziomie klasy, SQLAlchemy mapuje na kolumnę. Nie myl z polem instancji.
4. **`__tablename__` wymagane.** Bez tego SQLAlchemy zgaduje z nazwy klasy (lowercase), ale w tym repo zawsze jawne.
5. **`Numeric` ≠ `Float`.** Dla pieniędzy ZAWSZE `Numeric`. `Float` to IEEE 754 — błędy zaokrągleń.
6. **`String()` bez długości = TEXT?** Nie. `String` bez długości → VARCHAR bez limitu (MariaDB = TEXT). Zawsze podawaj długość dla pól z max length.
7. **`JSON` column jest mutable-tracking problem.** Mutowanie dict w JSON column nie triggeruje dirty flag. Trzeba `flag_modified(obj, "field")`. W tym repo JSON jest rzadko mutowany.
8. **Brak `DbSet<T>`.** Query zaczyna się od `select(Article)` (lekcja 06).
9. **`relationship()` jest opcjonalne.** Można żyć bez nav properties — explicit JOIN. W tym repo tak robią.
10. **`server_default` jako string.** To literal SQL, nie Python value. `"0"` nie `0`, `"CURRENT_TIMESTAMP"` nie `datetime.now()`.

## Quiz

1. Czym różni się `default` od `server_default` w `Column`? (Python-side vs DB-side default)
2. Dlaczego `Numeric(18, 2)` a nie `Float` dla pieniędzy? (Decimal precision vs IEEE 754)
3. Czym jest `Base.metadata`? (registry wszystkich modeli, generuje DDL)
4. Dlaczego w tym repo nie ma `relationship()` w `Article`? (async lazy loading nie działa, wolą explicit JOIN)
5. Co robi `ForeignKey("categories.id", ondelete="SET NULL")`? (jawny FK z ON DELETE SET NULL)

→ `python learning/quiz/quiz.py --topic sqlalchemy --n 5`
