# Lekcja 03 — Pydantic v2 schemas vs C# DTOs

> Plik bazowy: `backend/articles/schemas.py`
> Odpowiednik .NET: C# records / DTOs + `[Required]` + `System.Text.Json`

Pydantic to biblioteka do walidacji i serializacji w Pythonie. W FastAPI to **serce** — każdy request body i response model to klasa Pydantic. Odpowiednik C# DTO + `[ApiController]` model validation + `System.Text.Json` serializacji, ale znacznie mocniejszy.

## Realny snippet z repo

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/schemas.py" lines="94-123" />

## 1. `BaseModel` — odpowiednik C# record

C# (record, nullable):
```csharp
public record ArticleCreate(
    [Required, MinLength(1), MaxLength(200)] string Name,
    bool IsService = false,
    string? InternalNumber = null,
    decimal? ReplacementValue = null,
    int? CategoryId = null
);
```

Pydantic v2:
```python
class ArticleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    is_service: bool = False
    internal_number: str | None = Field(None, max_length=50)
    replacement_value: Decimal | None = None
    category_id: int | None = None
```

**Kluczowe:**

| C# record | Pydantic v2 |
|-----------|-------------|
| `record ArticleCreate(...)` | `class ArticleCreate(BaseModel)` |
| Konstruktor positional | Konstruktor keyword: `ArticleCreate(name="x")` |
| `[Required]` atrybut | `Field(...)` (ellipsis = required) |
| `[MaxLength(200)]` | `Field(max_length=200)` |
| Default `= false` | Default `= False` |
| `string?` | `str \| None` |
| Brak walidacji runtime (tylko DataAnnotations) | **Walidacja runtime przy konstrukcji** |
| `JsonSerializer` serializuje | Pydantic `.model_dump()` serializuje |

## 2. `Field(...)` — elipsa = required

```python
name: str = Field(..., min_length=1, max_length=200)
```

`...` (trzy kropki, `Ellipsis`) to Python singleton. W Pydantic oznacza **"pole wymagane, brak defaultu"**. Odpowiednik C# `[Required]` + non-nullable.

Bez `...`:
```python
name: str = Field(min_length=1, max_length=200)   # NIE required — wymaga defaultu
```

Z defaultem:
```python
name: str = Field("default", min_length=1)   # default "default"
is_service: bool = False                      # skrót: default False, brak constraintów
internal_number: str | None = Field(None, max_length=50)  # default None, max 50 jeśli podane
```

## 3. Walidacja — runtime, nie tylko compile-time

C# DataAnnotations waliduje w ASP.NET pipeline (ModelState). Pydantic waliduje **przy każdej konstrukcji**:

```python
ArticleCreate(name="")           # → ValidationError: name too short
ArticleCreate(name="x" * 300)    # → ValidationError: name too long
ArticleCreate()                  # → ValidationError: name required
ArticleCreate(name="x")          # OK
```

FastAPI automatycznie waliduje request body — jeśli JSON nie spełnia, zwraca 422 z szczegółami. Nie musisz pisać `if (!ModelState.IsValid)`.

## 4. `class Config: from_attributes = True` — ORM mode

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/schemas.py" lines="45-46" />

```python
class Config:
    from_attributes = True
```

To pozwala konstruować Pydantic model **z obiektu po atrybutach** (np. SQLAlchemy model):

```python
article_orm = await db.get(Article, 1)        # SQLAlchemy Article
detail = ArticleDetail.model_validate(article_orm)   # Pydantic ArticleDetail
```

`model_validate()` czyta atrybuty z `article_orm` (`.id`, `.name`, etc.) i mapuje na pola `ArticleDetail`. Odpowiednik C# AutoMapper `Mapper.Map<ArticleDetailDto>(articleEntity)`.

Bez `from_attributes = True` Pydantic oczekuje dicta, nie obiektu po atrybutach.

**Pydantic v2 note:** `class Config` to stara składnia. Nowsza to `model_config = ConfigDict(from_attributes=True)`. W tym repo widać starszą — działa, ale v2 zalewa nową.

## 5. `model_dump()` — serializacja do dict

```python
data = article_create.model_dump()           # → {"name": "x", "is_service": False, ...}
data = article_create.model_dump(exclude_unset=True)   # tylko pola explicite podane
```

`exclude_unset=True` — **kluczowe dla PATCH/PUT partial update**. Zwraca tylko pola, które klient explicite wysłał. Pola z defaultem (niewysłane) są pomijane.

W `schemas.py:125-130` `ArticleUpdate` jest zaprojektowany pod to:
```python
class ArticleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    is_service: bool | None = None
    ...
```

Wszystko `| None = None`. W service:
```python
update_data = data.model_dump(exclude_unset=True)   # tylko co klient wysłał
for key, value in update_data.items():
    setattr(article, key, value)
```

Odpowiednik C# JSON Patch lub ręcznego `if (dto.Name is not null) entity.Name = dto.Name`.

## 6. `Literal` i `Enum` — ograniczone wartości

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/articles/schemas.py" lines="7-14" />

```python
PowerType = Literal["diesel", "electric", "other"]

class ArticleArchivalFilter(str, Enum):
    ACTIVE = "active"
    ARCHIVAL = "archival"
    ALL = "all"
```

`Literal["a", "b"]` — type alias akceptujący tylko te stringi. Walidacja runtime: `ArticleCreate(power_type="diesel")` OK, `power_type="nuclear"` → ValidationError.

`Enum` — pełnoprawny enum. `(str, Enum)` = "str enum" — wartości są stringami, można porównywać z stringami. Odpowiednik C# `enum`.

W `router.py:72`:
```python
archival_status: ArticleArchivalFilter = Query(ArticleArchivalFilter.ACTIVE)
```

FastAPI waliduje query param `?archival_status=active` → enum. `?archival_status=foo` → 422.

## 7. Nested models — zagnieżdżenie

```python
class AvailabilityConflict(BaseModel):
    contract_id: int
    contract_number: str
    date_from: date | None
    contractor_name: str

class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_contracts: list[AvailabilityConflict]   # ← list of nested models
    conflicting_reservations: list[AvailabilityReservationConflict] = []
```

`list[AvailabilityConflict]` — odpowiednik C# `List<AvailabilityConflictDto>`. Pydantic waliduje każdy element listy.

`list[...]` to Python 3.9+ generic syntax (PEP 585). Starsze: `List[AvailabilityConflict]` z `from typing import List`.

## 8. Response model — FastAPI używa Pydantic do serializacji

W `router.py:66`:
```python
@router.get("", response_model=PaginatedResponse[ArticleListItem])
async def list_articles(...):
    ...
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)
```

`response_model=PaginatedResponse[ArticleListItem]` mówi FastAPI: "zwróć to jako ten typ". FastAPI:
1. Waliduje że zwracana wartość pasuje
2. Serializuje do JSON z odpowiednimi polami
3. **Ukrywa pola nie-w-modelu** (nawet jeśli obiekt ma więcej pól)

To odpowiednik C# `[ProducesResponseType(typeof(PaginatedResponse<ArticleListItem>), 200)]` + `JsonSerializer` z opcjami.

**Generic model:** `PaginatedResponse[ArticleListItem]` — Pydantic wspiera generics (jak C# `PaginatedResponse<T>`). Definiowane raz, używane z dowolnym typem.

## 9. Pydantic v1 vs v2 — migracja

Repo używa **Pydantic v2**. Różnice vs v1 (często widzisz w tutorialach starych):

| v1 | v2 |
|----|-----|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj()` | `.model_validate()` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes = True` |
| `@validator` | `@field_validator` |
| `Optional[T]` | `T \| None` (też działa Optional) |

Jeśli znajdziesz w tutorialu `.dict()` — to v1. W tym repo zawsze v2.

## 10. Walidatory — custom logic

Pydantic v2:
```python
from pydantic import field_validator

class ArticleCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name nie może być puste")
        return v
```

Odpowiednik C# `IValidatableObject.Validate()` lub custom validation attribute. W tym repo walidatory są rzadkie — `Field(...)` constrainty wystarczają.

## Gotchas dla .NET deva

1. **Pydantic waliduje przy konstrukcji.** Nie "przy serialize" jak DataAnnotations. `ArticleCreate(name="")` rzuca od razu.
2. **`...` = required.** Nie myl z `None`. `Field(...)` = wymagane, `Field(None)` = opcjonalne z default None.
3. **`exclude_unset=True` to PATCH-killer.** Najważniejszy idiom dla partial update.
4. **`from_attributes = True` = ORM mode.** Bez tego nie zmapujesz SQLAlchemy → Pydantic.
5. **`model_dump()` zwraca dict, nie JSON.** Do JSON: `model_dump_json()` lub `json.dumps(model_dump())`.
6. **Generic models działają.** `PaginatedResponse[ArticleListItem]` jak C# `PaginatedResponse<T>`.
7. **`Literal` jest lepszy niż `Enum` dla 3 wartości.** Mniej kodu, ale `Enum` daje `.value` i methody.
8. **Pydantic v2 ≠ v1.** Stare tutoriale używają `.dict()`, `orm_mode`. W tym repo v2.
9. **Brak `[JsonIgnore]`.** Ukrywanie pól: `Field(exclude=True)` lub `response_model` bez tego pola.
10. **`Decimal` serializuje do string w JSON.** Nie number. Frontend musi `parseFloat` lub backend `float` (ale traci precyzję). W tym repo `Decimal` → string, frontend parsuje.

## Quiz

1. Co oznacza `Field(...)` w Pydantic? (pole wymagane, brak defaultu)
2. Czym różni się `model_dump()` od `model_dump(exclude_unset=True)`? (wszystko vs tylko explicite wysłane)
3. Co robi `from_attributes = True`? (pozwala konstruować z obiektu po atrybutach — ORM mode)
4. Czym jest `Literal["diesel", "electric", "other"]`? (type alias akceptujący tylko te stringi)
5. Czym różni się Pydantic v1 `.dict()` od v2? (v2: `.model_dump()`)

→ `python learning/quiz/quiz.py --topic pydantic --n 5`
