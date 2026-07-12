# Lekcja 07 — Service layer pattern

> Plik bazowy: `backend/articles/service.py`, `backend/auth/service.py`
> Odpowiednik .NET: Application Service / CQRS handler

RAO używa **service layer** — logika biznesowa w `service.py`, router jest cienki. To ten sam wzorzec co w .NET (Application Service), ale bez interfejsów i DI kontenera — singleton instancja na poziomie modułu.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="1-46" />

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/service.py" lines="142-142" />

## 1. Service = klasa z metodami async

```python
class ArticleService:
    async def list_articles(self, db: AsyncSession, ...) -> tuple[list[ArticleListItem], int]:
        ...

    async def get_article(self, db: AsyncSession, article_id: int) -> Article:
        ...

    async def create_article(self, db: AsyncSession, data: ArticleCreate) -> Article:
        ...

# Singleton instancja na poziomie modułu
article_service = ArticleService()
```

Odpowiednik C#:
```csharp
public class ArticleService
{
    public async Task<(List<ArticleListItem> Items, int Total)> ListAsync(RaoDbContext db, ...) { ... }
    public async Task<Article> GetAsync(RaoDbContext db, int id) { ... }
}

// W DI:
services.AddScoped<ArticleService>();
```

**Kluczowa różnica:** w C# service rejestrujesz w DI i wstrzykujesz przez konstruktor. W Pythonie **tworzysz instancję na poziomie modułu** (`article_service = ArticleService()`) i importujesz.

## 2. `db` jako parametr metody, nie pole klasy

```python
class ArticleService:
    async def list_articles(self, db: AsyncSession, ...):
        ...
```

`db` przekazywane jako parametr, nie wstrzyknięte w konstruktorze. **Dlaczego?** Bo sesja jest per-request, a service jest singleton. Jeśli service trzymałby sesję jako pole, byłaby współdzielona między requestami (race condition).

W C# `AddScoped<ArticleService>` + `RaoDbContext` scoped — DI kontener zarządza cyklem życia. W Pythonie **nie ma scoped DI** — service jest singleton, sesja przekazywana jawnie.

**Zalety:**
- Explicit — widzisz że metoda potrzebuje DB
- Testowanie — przekaż mock `AsyncSession` w teście
- Brak "ukrytych" zależności

**Wady:**
- Powtarzanie `db` w każdej metodzie
- Łatwo zapomnieć przekazać

## 3. Singleton instancja — `article_service = ArticleService()`

```python
# na końcu service.py
article_service = ArticleService()
```

Instancja tworzona raz przy imporcie modułu. Wszyscy importują tę samą instancję:
```python
from articles.service import article_service
await article_service.list_articles(db, ...)
```

**Czy to thread-safe?** Tak — service nie ma stanu (brak pól instancji). Wszystkie dane w parametrach. Współdzielona instancja jest OK bo metody są pure (poza DB side-effects).

Odpowiednik C# `services.AddSingleton<ArticleService>()` — ale w C# service zwykle scoped bo trzyma `DbContext`. Tu service jest stateless, więc singleton OK.

## 4. Router → service → model

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/router.py" lines="66-81" />

```python
@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(..., db: AsyncSession = Depends(get_db), ...):
    items, total = await article_service.list_articles(
        db, search, category_id, owner_id, archival_status.value, is_service, page, per_page
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)
```

Router:
1. Waliduje input (FastAPI via Pydantic)
2. Wywołuje service
3. Komponuje response DTO
4. Zwraca (FastAPI serializuje)

Service:
1. Query DB
2. Logika biznesowa (filtry, sortowanie, batch fetch)
3. Zwraca entity lub DTO

**Cienki router, gruby service.** Logika biznesowa NIGDY w routerze. Jeśli widzisz `if` z logiką biznesową w routerze — to antywzorzec (w tym repo czasem się zdarza w `_build_detail`, ale to view concern).

## 5. Return type — entity vs DTO

Service zwraca **entity** (SQLAlchemy `Article`), router komponuje DTO (`ArticleDetail`). Czasem service zwraca gotowe DTO (`ArticleListItem`) — gdy query projekuje konkretne kolumny.

```python
# service: zwraca entity
async def get_article(self, db, article_id) -> Article:
    ...
    return article

# router: komponuje DTO
async def get_article(...):
    a = await _verify_article_access(...)
    return await _build_detail(db, a)   # Article → ArticleDetail
```

```python
# service: zwraca DTO (projekcja)
async def list_articles(self, db, ...) -> tuple[list[ArticleListItem], int]:
    ...
    items.append(ArticleListItem(id=a.id, name=a.name, ...))
    return items, total
```

Odpowiednik C# — service zwraca entity, controller mapuje na DTO przez AutoMapper. Albo service zwraca DTO (CQRS-style).

## 6. `not_found` — exception jako flow control

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="106-111" />

```python
async def get_article(self, db: AsyncSession, article_id: int) -> Article:
    result = await db.execute(select(Article).where(Article.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise not_found("Artykuł")
    return article
```

`not_found("Artykuł")` z `shared/exceptions.py` — zwraca `HTTPException(404, "Artykuł nie istnieje")`. Service rzuca HTTP exception, FastAPI przechwytuje.

**Czy to czyste?** Service rzucanie HTTP exception to **nieszczególnie** — service powinien rząć domain exception, router mapować na HTTP. Ale w tym repo jest pragmatyczne — service wie że jest w kontekście HTTP.

Odpowiednik C# `throw new NotFoundException("Artykuł")` + middleware mapujące na 404. Tu service rzuca od razu HTTPException — mniej warstw, ale service jest coupled z HTTP.

## 7. `**data.model_dump()` — rozpakowanie dicta do kwargs

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/service.py" lines="113-119" />

```python
article = Article(**data.model_dump(), created_at=datetime.utcnow())
```

`data.model_dump()` → `{"name": "x", "is_service": False, ...}`. `Article(**dict)` → `Article(name="x", is_service=False, ..., created_at=...)`. `**` rozpakowuje dict jako keyword args.

Odpowiednik C# — nie ma bezpośredniego. Najbliższe: reflection lub record `with` expression. W Pythonie to idiom — mapuje Pydantic → SQLAlchemy model jeśli pola się zgadzają.

**Uwaga:** jeśli `ArticleCreate` ma pole którego `Article` nie ma → `TypeError`. Jeśli `Article` ma required pole którego `ArticleCreate` nie ma → `TypeError`. Tu `created_at` dodawane jawnie (bo `ArticleCreate` go nie ma, a `Article` wymaga).

## 8. Cross-feature import — `from contracts.service import ...`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/router.py" lines="174-177" />

```python
from contracts.service import contract_service
data = await contract_service.get_last_conditions_for_article(db, article_id, user)
```

Service może wołać inny service. Import **wewnątrz funkcji** (nie na górze pliku) — **unika circular import**. Python importuje moduł raz (cache), ale jeśli `articles/router.py` importuje `contracts/service.py` na górze, a `contracts/service.py` importuje `articles/...` → circular.

Wewnątrz funkcji: import wykonuje się przy wywołaniu, po tym jak moduły są już załadowane. Bez circular.

Odpowiednik C# — nie ma tego problemu (kompilowane). W Pythonie to realny problem, idiom to "import w funkcji dla cross-feature".

## 9. Testowanie service

Service jest testowalny bo `db` jest parametrem:
```python
async def test_list_articles():
    db = MockAsyncSession()       # mock lub in-memory SQLite
    items, total = await article_service.list_articles(db, search="foo")
    assert total >= 0
```

W C# testowałbyś z `TestContainers` + real DB albo EF Core InMemory provider. W Pythonie analogicznie — `pytest-asyncio` + SQLite in-memory albo mock.

## Gotchas dla .NET deva

1. **Service to singleton, `db` przekazywane jawnie.** Brak scoped DI w Pythonie.
2. **`article_service = ArticleService()` na końcu pliku.** Instancja per moduł, współdzielona.
3. **Service rzuca `HTTPException`.** Pragmatyczne, ale couples service z HTTP.
4. **`**data.model_dump()` rozpakowuje dict do kwargs.** Idiom mapowania Pydantic → SQLAlchemy.
5. **Cross-feature import wewnątrz funkcji.** Unika circular import.
6. **Brak interfejsów.** Service to klasa, mock przez `unittest.mock` lub dependency injection ręcznie.
7. **`self` jawny.** Pierwszy parametr każdej metody.
8. **Brak overloadingu.** Default args zamiast: `def foo(self, db, search=None, page=1)`.
9. **Logika w service, nie w router.** Router cienki — walidacja + wywołanie service + kompozycja DTO.
10. **Return entity lub DTO.** Service decyduje — entity dla "get by id", DTO dla list z projekcją.

## Quiz

1. Dlaczego `db` jest parametrem metody, nie pole klasy? (sesja per-request, service singleton — współdzielenie = race)
2. Czym jest `article_service = ArticleService()` na końcu pliku? (singleton instancja per moduł)
3. Co robi `Article(**data.model_dump())`? (rozpakowuje dict Pydantic jako kwargs konstruktora SQLAlchemy)
4. Dlaczego cross-feature import wewnątrz funkcji? (unika circular import)
5. Gdzie powinna być logika biznesowa — router czy service? (service, router cienki)

→ `python learning/quiz/quiz.py --topic service --n 5`
