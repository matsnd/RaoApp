# Lekcja 05 — DI & auth — JWT

> Plik bazowy: `backend/auth/dependencies.py`, `backend/auth/service.py`, `backend/database.py`
> Odpowiednik .NET: `[FromServices]` + JWT middleware + `ICurrentUserService`

FastAPI nie ma kontenera DI w sensie ASP.NET (`IServiceCollection`). Ma **`Depends`** — deklaratywne wstrzykiwanie przez parametry funkcji. To prostsze i bardziej explicit, ale wymaga zmiany mentalu.

## Realny snippet z repo — `get_db`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/database.py" lines="31-33" />

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

## Realny snippet z repo — `get_current_user`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/dependencies.py" lines="1-50" />

## 1. `Depends` — DI przez parametr funkcji

C# (constructor injection):
```csharp
public class ArticlesController : ControllerBase
{
    private readonly RaoDbContext _db;
    private readonly ICurrentUserService _currentUser;

    public ArticlesController(RaoDbContext db, ICurrentUserService currentUser)
    {
        _db = db;
        _currentUser = currentUser;
    }

    [HttpGet]
    public async Task<IActionResult> List() {
        var user = _currentUser.User;   // z middleware
        ...
    }
}
```

FastAPI (parameter injection):
```python
@router.get("")
async def list_articles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # db i current_user gotowe do użycia
    ...
```

**Jak to działa:**
1. FastAPI widzi `Depends(get_db)` w sygnaturze
2. Wywołuje `get_db()` — to generator (ma `yield`)
3. Pobiera wartość z `yield` → wstrzykuje jako `db`
4. Endpoint się wykonuje
5. Po końcu endpointu, FastAPI wznawia generator (po `yield`) — cleanup (zamknięcie sesji)

`get_db` to **generator function** (ma `yield`). FastAPI obsługuje cleanup — jeśli endpoint rzuci exception, generator i tak się zamknie (sesja zamyka się czysto).

## 2. `Depends` chain — zależności zależności

`get_current_user` zależy od `oauth2_scheme` i `get_db`:

```python
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),     # ← zależy od OAuth2
    db: AsyncSession = Depends(get_db),      # ← zależy od get_db
) -> User:
    ...
```

FastAPI rozwiązuje **rekurencyjnie**:
1. `get_current_user` potrzebuje `token` → wywołaj `oauth2_scheme(tokenUrl=...)` (wydobądź token z `Authorization: Bearer ...`)
2. `get_current_user` potrzebuje `db` → wywołaj `get_db()`
3. Jak masz te zależności, wywołaj `get_current_user(request, token, db)`

To odpowiednik C# middleware pipeline + constructor injection chain. FastAPI buduje graf zależności z sygnatur funkcji.

**Cacheowanie zależności w reqście:** FastAPI cacheuje wynik `Depends` **per request**. Jeśli dwa parametry w endpoincie mają `Depends(get_db)`, `get_db` wywoła się **raz**. To kluczowe — `get_current_user` i endpoint oba mają `Depends(get_db)`, ale sesja jest jedna.

## 3. `OAuth2PasswordBearer` — wyciąga token z nagłówka

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
```

To dependency, które:
1. Czyta `Authorization: Bearer <token>` z nagłówka
2. Zwraca token jako string
3. Jeśli brak nagłówka → 401 automatycznie

`tokenUrl="/auth/login"` — używane do generowania OpenAPI docs (Swagger UI "Authorize" button wie gdzie się zalogować).

Odpowiednik C# `JwtBearerMiddleware` — ale w FastAPI to **dependency**, nie middleware. Każdy endpoint explicite decyduje czy potrzebuje auth.

## 4. JWT decode — `jose`

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/service.py" lines="26-29" />

```python
def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.RAO_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.RAO_SECRET_KEY, algorithm="HS256")
```

W `dependencies.py:31`:
```python
payload = jwt.decode(token, settings.RAO_SECRET_KEY, algorithms=["HS256"])
user_id: int = int(payload.get("sub"))
```

`jose` to biblioteka JWT (odpowiednik C# `System.IdentityModel.Tokens.Jwt`). HS256 = HMAC SHA-256 (symetryczny).

**Claims:**
- `sub` — subject (user ID jako string)
- `role` — rola użytkownika
- `exp` — expiration time (UTC datetime)

`jwt.decode` weryfikuje `exp` automatycznie — jeśli token wygasł, rzuca `JWTError`. Odpowiednik C# `TokenValidationParameters` z `ValidateLifetime = true`.

## 5. `request.state` — per-request cache

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/dependencies.py" lines="13-44" />

```python
_USER_CACHE_ATTR = "_rao_cached_user"

async def get_current_user(request: Request, ...):
    cached = getattr(request.state, _USER_CACHE_ATTR, None)
    if cached is not None:
        return cached
    # ... resolve user ...
    setattr(request.state, _USER_CACHE_ATTR, user)
    return user
```

`request.state` to namespace per-request (jak `HttpContext.Items` w C#). Tu używane do **cacheowania usera per request** — jeśli ten sam token używany przez kilka `Depends` w łańcuchu, DB query robi się raz.

**Dlaczego nie polegać na cache FastAPI?** FastAPI cacheuje `Depends` wynik per request automatycznie (patrz pkt 2). Ale ten kod jest **defensywny** — jeśli ktoś zrobi `Depends(get_current_user)` w sub-dependency z innym `Depends` chainem, cache FastAPI może nie zadziałać. `request.state` to belt-and-suspenders.

Odpowiednik C# `HttpContext.Items["_cached_user"] = user`.

## 6. `require_admin` — guard dependency

```python
async def require_admin(user: User = Depends(get_current_user)) -> User:
    return user   # NOTE: IDOR wyłączone, no-op
```

To dependency, które **wymaga** `get_current_user` (czyli wymaga auth) i dodatkowo sprawdza rolę. Używane jako:
```python
@router.delete("/...")
async def delete_thing(..., admin: User = Depends(require_admin)):
    ...
```

Odpowiednik C# `[Authorize(Roles = "admin")]` — ale w FastAPI to **dependency**, nie atrybut. W tym repo `require_admin` jest no-opem (IDOR wyłączony, single-user mode), ale pattern jest pokazany.

## 7. `settings` — konfiguracja z `.env`

```python
from config import settings
settings.RAO_SECRET_KEY
settings.RAO_ACCESS_TOKEN_EXPIRE_MINUTES
settings.RAO_DATABASE_URL
```

`config.py` używa `pydantic-settings` (Pydantic Settings) — czyta `.env` i env vars. Odpowiednik C# `IOptions<JwtSettings>` + `appsettings.json`.

Wszystkie sekrety w `.env` (gitignored). `RAO_SECRET_KEY` to klucz HMAC — jeśli wyciekie, ktoś może podpisywać tokeny. **Nigdy** w kodzie.

## 8. bcrypt — hashowanie haseł

<ref_snippet file="C:/projects/repos/RaoApp_new/backend/auth/service.py" lines="15-23" />

```python
def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())
```

bcrypt — adaptacyjny hash z solą. Odpowiednik C# `BCrypt.Net.BCrypt.HashPassword`.

`.encode()` — string → bytes (bcrypt wymaga bytes). `.decode()` — bytes → string (do zapisu w DB jako VARCHAR).

**Nigdy** nie hashuj MD5/SHA1 dla haseł — bcrypt/PBKDF2/Argon2 tylko.

## 9. Brak middleware — wszystko przez `Depends`

W C# masz middleware pipeline (`app.UseAuthentication()`, `app.UseAuthorization()`). W FastAPI **nie ma globalnego auth middleware** w tym repo — każdy endpoint explicite `Depends(get_current_user)`.

Zalety: explicit, łatwe testowanie (przekaż mock).
Wady: łatwo zapomnieć `Depends` w nowym endpoincie → endpoint publiczny bez auth.

FastAPI **ma** middleware (`@app.middleware("http")`), ale w tym repo używają tylko dla CORS i logowania. Auth przez `Depends`.

## Gotchas dla .NET deva

1. **`Depends` per endpoint, nie konstruktor.** Explicit, ale powtarzalne.
2. **`Depends` cache per request.** Ten sam dependency wywoła się raz, nawet użyty 3x.
3. **`get_db` to generator (yield).** FastAPI cleanupuje po końcu endpointu.
4. **`request.state` = `HttpContext.Items`.** Per-request storage.
5. **Brak `[Authorize]`.** Auth przez `Depends(get_current_user)`. Łatwo zapomnieć.
6. **`OAuth2PasswordBearer` to dependency, nie middleware.** Wyciąga token z nagłówka.
7. **`jose` ≠ `PyJWT`.** Inna biblioteka, ale podobna API. Repo używa `jose`.
8. **`exp` sprawdzane automatycznie.** `jwt.decode` rzuca jeśli wygasł.
9. **`settings` z pydantic-settings.** Czyta `.env`, typed. Jak `IOptions<T>`.
10. **`require_admin` to dependency, nie atrybut.** Można chainować: `Depends(require_admin)` wymusza auth + admin.

## Quiz

1. Czym jest `Depends(get_db)`? (DI — FastAPI wywołuje get_db() i wstrzykuje wynik)
2. Dlaczego `get_db` ma `yield` a nie `return`? (generator — FastAPI cleanupuje sesję po końcu endpointu)
3. Co robi `OAuth2PasswordBearer`? (wyciąga token z `Authorization: Bearer` nagłówka)
4. Czym jest `request.state`? (per-request storage, odpowiednik HttpContext.Items)
5. Dlaczego `Depends` cache per request jest ważne? (get_db wywoła się raz, nawet użyte 3x w chainie)

→ `python learning/quiz/quiz.py --topic di --n 5`
