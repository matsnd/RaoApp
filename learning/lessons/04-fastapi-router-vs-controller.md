# Lekcja 04 — FastAPI router vs ASP.NET Controller

> Plik bazowy: `backend/articles/router.py`
> Odpowiednik .NET: `[ApiController]` + routing + model binding + filters

FastAPI nie ma "kontrolerów" w sensie klas. Endpoint to **funkcja** dekorowana `@router.get/post/...`. `APIRouter` to grupa endpointów z prefixem. To zmiana mentalna: nie ma klasy ze stanem, są funkcje z DI przez parametry.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/router.py" lines="1-104" />

## 1. `APIRouter` — odpowiednik `[ApiController]`

C#:
```csharp
[ApiController]
[Route("api/[controller]")]
public class ArticlesController : ControllerBase
{
    [HttpGet]
    public async Task<PagedResult<ArticleListItem>> List(...) { ... }

    [HttpGet("{id}")]
    public async Task<ArticleDetail> Get(int id) { ... }
}
```

FastAPI:
```python
router = APIRouter(prefix="/articles", tags=["articles"])

@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(...): ...

@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: int, ...): ...
```

**Kluczowe różnice:**

| ASP.NET | FastAPI |
|---------|---------|
| Klasa `ControllerBase` | Moduł z `APIRouter` |
| `[Route("api/[controller]")]` | `APIRouter(prefix="/articles")` |
| Metody w klasie | Funkcje w module |
| `[HttpGet]`, `[HttpPost]` | `@router.get`, `@router.post` |
| `[HttpGet("{id}")]` | `@router.get("/{article_id}")` |
| `Task<T>` return | `async def` return (lub sync) |
| `[FromBody]`, `[FromRoute]`, `[FromQuery]` | **Typ parametru + default** rozstrzyga |
| `ControllerBase.User` | `Depends(get_current_user)` |

## 2. Routing — path params z typami

```python
@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(article_id: int, ...):
```

`{article_id}` w path → parametr `article_id`. **Typ `int`** w sygnaturze = FastAPI waliduje i konwertuje. `?article_id=abc` → 422. Odpowiednik C# route constraint `{id:int}`.

W C# musisz jawnie `[FromRoute] int id`. W FastAPI **typ i nazwa parametru** rozstrzygają:
- Parametr w path (`{article_id}`) → path param
- Parametr z defaultem `Query(...)` → query param
- Parametr typu Pydantic model → body
- Parametr `Depends(...)` → DI

## 3. Query params — `Query(...)`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/router.py" lines="66-81" />

```python
@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    is_service: bool | None = Query(None),
    archival_status: ArticleArchivalFilter = Query(ArticleArchivalFilter.ACTIVE),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
```

`Query(None)` = opcjonalny query param z default None. `Query(1, ge=1)` = default 1, must be >= 1. `Query(50, ge=1, le=200)` = default 50, between 1 and 200.

Odpowiednik C#:
```csharp
[HttpGet]
public async Task<PagedResult<ArticleListItem>> List(
    [FromQuery] string? search,
    [FromQuery] int? categoryId,
    [FromQuery] int page = 1,
    [FromQuery] [Range(1, int.MaxValue)] int perPage = 50,
    [FromQuery] [Range(1, 200)] int perPage = 50)
```

FastAPI `ge`, `le`, `gt`, `lt` = `>=`, `<=`, `>`, `<`. To constrainty Pydantic `Field`, ale dla query params.

`archival_status: ArticleArchivalFilter = Query(...)` — enum jako query param. `?archival_status=active` → enum. Nieprawidłowa wartość → 422.

## 4. Body — Pydantic model automatycznie

```python
@router.post("", response_model=ArticleDetail, status_code=201)
async def create_article(
    data: ArticleCreate,    # ← Pydantic model = body
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
```

`data: ArticleCreate` — typ to Pydantic `BaseModel`, więc FastAPI wie: to body. Waliduje JSON → `ArticleCreate`. Odpowiednik C# `[FromBody] ArticleCreate dto`.

Nie ma atrybutu `[FromBody]` — typ parametru rozstrzyga. Pydantic model = body, primitive = query/path, `Depends` = DI.

## 5. `Depends` — DI zamiast konstruktora

```python
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user),
```

`Depends(get_db)` — FastAPI wywoła `get_db()`, wynik wstrzyknie jako `db`. To **DI przez parametr funkcji**, nie przez konstruktor klasy.

Odpowiednik C#:
```csharp
public class ArticlesController : ControllerBase
{
    private readonly IDbContextFactory<RaoDbContext> _dbFactory;
    private readonly ICurrentUserService _currentUser;

    public ArticlesController(IDbContextFactory<RaoDbContext> dbFactory, ICurrentUserService currentUser)
    {
        _dbFactory = dbFactory;
        _currentUser = currentUser;
    }
}
```

W FastAPI nie ma konstruktora — każdy endpoint jawnie deklaruje co potrzebuje. **Zalety:**
- Explicit dependencies per endpoint (nie wszystkie endpointy potrzebują `current_user`)
- Łatwe testowanie — przekaż mock w `Depends`
- Nie ma "god class" z 10 wstrzyknięciami

**Wady:**
- Powtarzanie `Depends(get_db)` w każdym endpoincie
- Brak "shared state" kontrolera (ale to dobrze — endpointy są stateless)

Więcej w lekcji 05.

## 6. `response_model` — ukrywa pola, waliduje output

```python
@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article(...):
    a = await _verify_article_access(...)
    return await _build_detail(db, a)   # zwraca ArticleDetail
```

`response_model=ArticleDetail` — FastAPI:
1. Waliduje że return pasuje do `ArticleDetail`
2. Serializuje do JSON
3. **Ukrywa pola nie-w-modelu** (nawet jeśli zwrócono więcej)

Odpowiednik C# `[ProducesResponseType<ArticleDetail>(200)]` + `JsonSerializer` z `TypeInfo`. Ale w FastAPI to **egzekwowane** — jeśli zwrócisz obiekt z polem nie w `ArticleDetail`, to pole zniknie z JSON.

## 7. Status codes

```python
@router.post("", response_model=ArticleDetail, status_code=201)
@router.delete("/{article_id}", status_code=204)
```

`status_code=201` dla POST create, `204` dla DELETE. Odpowiednik C# `[ProducesResponseType(201)]` / `return NoContent()`.

Default: `200` dla GET/POST/PUT, ale POST create powinien być 201. FastAPI nie zgaduje — musisz jawnie.

## 8. `HTTPException` — odpowiednik `throw new NotFoundException()`

W `router.py:177`:
```python
raise HTTPException(status_code=404, detail="Brak historii umów dla tej maszyny")
```

FastAPI przechwytuje `HTTPException` i zwraca JSON `{"detail": "..."}` z podanym statusem. Odpowiednik C#:
```csharp
throw new NotFoundException("Brak historii umów dla tej maszyny");
```

W repo jest też `shared/exceptions.py` z helperami `not_found("Maszyna")`, `forbidden("...")` — zwracają `HTTPException` z polskimi wiadomościami. Widzisz w `router.py:31`:
```python
raise not_found("Maszyna")
```

## 9. Rejestracja routera w `main.py`

W `backend/main.py` (nie cytuję, ale):
```python
from articles.router import router as articles_router
app.include_router(articles_router)
```

`app.include_router(router)` — rejestruje wszystkie endpointy z `articles_router` pod jej prefixem. Finalny URL: `/rao/api/articles/...` (`root_path="/rao/api"` + `prefix="/articles"`).

Odpowiednik C# `AddControllers()` + attribute routing — ale w FastAPI **jawny import i rejestracja** każdego routera.

## 10. Helpery prywatne — `_verify_article_access`, `_build_detail`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/router.py" lines="18-63" />

Funkcje z `_` prefix (konwencja Python: "prywatne"). Nie są endpointami (nie dekorowane `@router`). To helpery używane przez endpointy.

W C# byłyby private methods w kontrolerze. Tutaj — funkcje w module. **Czysta separacja:** endpointy są cienkie, logika w `service.py`, helpery w routerze tylko dla rzeczy specyficznych dla HTTP (np. budowanie response DTO).

`_build_detail` — buduje `ArticleDetail` z SQLAlchemy `Article` + JOIN category/owner. Tu w routerze, nie w service, bo to "view concern" (jak złożyć DTO pod HTTP). Service zwraca entity, router komponuje response.

## Gotchas dla .NET deva

1. **Nie ma klasy kontrolera.** Funkcje w module. Stan endpointu = parametry funkcji.
2. **`Depends` per endpoint, nie konstruktor.** Explicit, ale powtarzalne.
3. **Typ parametru rozstrzyga binding.** Pydantic = body, primitive z `Query` = query, w path = path, `Depends` = DI.
4. **`response_model` ukrywa pola.** Nie musisz `JsonIgnore` — po prostu nie włączaj pola w response model.
5. **`status_code` jawnie.** FastAPI nie zgaduje 201 dla POST.
6. **`HTTPException` to exception.** `raise`, nie `return`. FastAPI ma global handler.
7. **`@router.get("")` vs `@router.get("/")`.** W tym repo `""` — pod prefixem `/articles` daje `/articles`. `/` dałoby `/articles/`.
8. **Brak `[Authorize]`.** Auth przez `Depends(get_current_user)` w parametrach. Każdy endpoint explicite.
9. **`_` jako nazwa parametru** = "nie używam tego". `_: User = Depends(get_current_user)` — wymusza auth, ale nie używa usera. Konwencja Python.
10. **Router jest modułem, nie instancją.** `router = APIRouter(...)` na poziomie modułu, importowane raz. Endpointy rejestrowane przy imporcie.

## Quiz

1. Czym różni się FastAPI endpoint od C# controller method? (funkcja w module vs metoda w klasie)
2. Jak FastAPI wie czy parametr to body, query, czy path? (typ: Pydantic=body, primitive z Query=query, w path=path, Depends=DI)
3. Co robi `response_model=ArticleDetail`? (waliduje + serializuje + ukrywa pola nie-w-modelu)
4. Czym jest `Depends(get_db)`? (DI — FastAPI wywoła get_db() i wstrzyknie wynik)
5. Dlaczego `_: User = Depends(get_current_user)` z `_`? (wymusza auth, nie używa usera — konwencja "nieużywane")

→ `python learning/quiz/quiz.py --topic fastapi --n 5`
