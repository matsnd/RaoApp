# 02 — Backend API (FastAPI) — Kompletna specyfikacja

> **INSTRUKCJA DLA AGENTA:** Zaimplementuj dokładnie te endpointy, modele i logikę.
> Każdy endpoint ma dokładną sygnaturę, request/response body, i algorytm.
> Architektura: Vertical Slice — każda feature w osobnym folderze.

## Struktura projektu

```
backend/
├── main.py                          # FastAPI app, CORS, lifespan
├── config.py                        # Settings (pydantic-settings, env vars)
├── database.py                      # AsyncEngine, AsyncSession, get_db()
├── auth/
│   ├── __init__.py
│   ├── router.py                    # /auth/login, register, reset-password, change-password, profile
│   ├── service.py                   # AuthService: verify, create_token, reset_password, send_email
│   ├── schemas.py                   # LoginRequest, TokenResponse, ResetRequest, ProfileUpdate
│   ├── models.py                    # User SQLAlchemy model
│   ├── dependencies.py              # get_current_user dependency
│   └── email_service.py             # SMTP email sending (reset password, notifications)
├── contractors/
│   ├── __init__.py
│   ├── router.py                    # CRUD /contractors, /contractors/{id}/addresses
│   ├── service.py                   # ContractorService
│   ├── schemas.py                   # Pydantic models
│   └── models.py                    # Contractor, ContractorAddress SQLAlchemy
├── articles/
│   ├── __init__.py
│   ├── router.py                    # CRUD /articles, /articles/{id}/duplicate
│   ├── service.py                   # ArticleService (incl. duplicate, availability)
│   ├── schemas.py
│   └── models.py
├── contracts/
│   ├── __init__.py
│   ├── router.py                    # CRUD /contracts
│   ├── service.py                   # ContractService (incl. numbering, value calc)
│   ├── schemas.py
│   └── models.py
├── positions/
│   ├── __init__.py
│   ├── router.py                    # CRUD /positions
│   ├── service.py                   # PositionService
│   ├── schemas.py
│   └── models.py
├── conditions/
│   ├── __init__.py
│   ├── router.py                    # CRUD /conditions
│   ├── service.py
│   ├── schemas.py
│   └── models.py
├── settings/
│   ├── __init__.py
│   ├── router.py                    # GET/PUT /settings/company, /settings/fees, /settings/salespeople
│   ├── service.py
│   ├── schemas.py
│   └── models.py
├── reports/
│   ├── __init__.py
│   ├── router.py                    # GET /reports/{type}
│   ├── service.py                   # PDF generation
│   └── templates/                   # Jinja2 HTML templates
│       ├── contract.html
│       ├── protocol_zo.html
│       └── protocol_zo_nodata.html
├── integrations/
│   ├── __init__.py
│   ├── gus.py                       # GUS REGON API client
│   └── nominatim.py                 # Nominatim reverse geocoding
└── shared/
    ├── __init__.py
    ├── pagination.py                # PaginatedResponse[T]
    └── exceptions.py                # HTTPException handlers
```

---

## config.py — Konfiguracja

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAO_")

    database_url: str  # mariadb+asyncmy://user:pass@host/rao_new
    secret_key: str    # JWT secret
    access_token_expire_minutes: int = 480  # 8h jak sesja WinForms
    cors_origins: list[str] = ["http://localhost:5173"]
    gus_api_key: str = ""
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@rao-app.pl"
    smtp_tls: bool = True
    # Frontend URL (for password reset links)
    frontend_url: str = "http://localhost:5173"
    password_reset_expire_minutes: int = 60  # Token ważny 1h
```

---

## AUTH & USER MANAGEMENT — Endpointy

### `POST /auth/login`

```python
# Request
class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

# Response 200
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    must_change_password: bool = False  # True → frontend wymusza zmianę

class UserResponse(BaseModel):
    id: int
    login: str
    email: str | None
    first_name: str | None
    last_name: str | None
    role: str
    branch_id: int | None
    is_active: bool
    last_login: datetime | None
```

**Algorytm:**
1. `SELECT * FROM users WHERE login = :login AND is_active = TRUE`
2. Jeśli user nie istnieje lub nieaktywny → 401 "Nieprawidłowy login lub hasło"
3. `bcrypt.checkpw(password, user.password)` → jeśli false → 401
4. Zapisz `last_login = now()`
5. `jwt.encode({"sub": user.id, "role": user.role, "exp": now + 8h}, SECRET_KEY)`
6. Return `TokenResponse` z `must_change_password = user.must_change_password`

> **UWAGA:** Jeśli `must_change_password == True`, frontend musi przekierować
> na `/change-password` i NIE POZWOLIĆ na żadną inną akcję do momentu zmiany hasła.
> Dotyczy użytkowników migrowanych ze starego systemu (plaintext → bcrypt).

### `POST /auth/register` (admin only)

```python
class RegisterRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., max_length=100)  # Wymagany do resetu hasła
    password: str = Field(..., min_length=6, max_length=100)
    first_name: str | None = None
    last_name: str | None = None
    role: Literal["admin", "user", "viewer"] = "user"
    branch_id: int | None = None
```

**Walidacja:**
1. Login unikalny: `SELECT count(*) FROM users WHERE login = :login`
2. Email unikalny: `SELECT count(*) FROM users WHERE email = :email`
3. Hasło → `bcrypt.hashpw(password, bcrypt.gensalt())`

### `PUT /auth/change-password`

```python
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, description="Min 6 znaków")
    confirm_password: str
```

**Algorytm:**
1. Sprawdź `current_password` vs `user.password` (bcrypt)
2. Sprawdź `new_password == confirm_password`
3. Sprawdź że `new_password != current_password`
4. Hash nowe hasło: `bcrypt.hashpw(new_password, bcrypt.gensalt())`
5. `UPDATE users SET password = :hash, must_change_password = FALSE WHERE id = :id`
6. Return 200 `{"message": "Hasło zmienione pomyślnie"}`

### `POST /auth/forgot-password`

> **Nowy endpoint** — resetowanie hasła przez email.

```python
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=100)
```

**Algorytm:**
1. `SELECT * FROM users WHERE email = :email AND is_active = TRUE`
2. Jeśli nie znaleziono → **ZAWSZE** zwróć 200 (nie ujawniaj czy email istnieje)
3. Wygeneruj token: `secrets.token_urlsafe(32)`
4. Hash token: `hashlib.sha256(token.encode()).hexdigest()`
5. Zapisz: `UPDATE users SET password_reset_token = :hash, password_reset_expires = now() + 1h WHERE id = :id`
6. Wyślij email z linkiem: `{frontend_url}/reset-password?token={token}`
7. Return 200 `{"message": "Jeśli email istnieje w systemie, wysłaliśmy link do resetu hasła"}`

**Email template (Jinja2):**
```
Temat: RAO — Resetowanie hasła

Cześć {{ user.first_name or user.login }},

Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w systemie RAO.

Kliknij poniższy link, aby ustawić nowe hasło:
{{ reset_link }}

Link jest ważny przez 1 godzinę.

Jeśli nie prosiłeś o reset hasła, zignoruj tę wiadomość.

Pozdrawiamy,
Zespół RAO
```

### `POST /auth/reset-password`

```python
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str
```

**Algorytm:**
1. Hash token: `hashlib.sha256(token.encode()).hexdigest()`
2. `SELECT * FROM users WHERE password_reset_token = :hash AND password_reset_expires > NOW()`
3. Jeśli nie znaleziono → 400 "Token nieprawidłowy lub wygasł"
4. Sprawdź `new_password == confirm_password`
5. `UPDATE users SET password = bcrypt(:new_password), password_reset_token = NULL, password_reset_expires = NULL, must_change_password = FALSE`
6. Return 200 `{"message": "Hasło zostało ustawione. Możesz się zalogować."}`

### `GET /auth/profile`

> Zalogowany użytkownik pobiera swoje dane.

```python
# Response 200 → UserResponse (jak wyżej)
```

### `PUT /auth/profile`

> Zalogowany użytkownik edytuje swoje dane (nie login/role).

```python
class ProfileUpdate(BaseModel):
    email: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=30)
    last_name: str | None = Field(None, max_length=30)
```

**Walidacja:** email unikalny (z wyłączeniem current user)

### `GET /admin/users` (admin only)

> Lista wszystkich użytkowników.

```python
class UserListItem(BaseModel):
    id: int
    login: str
    email: str | None
    first_name: str | None
    last_name: str | None
    role: str
    branch_id: int | None
    branch_name: str | None  # JOIN
    is_active: bool
    last_login: datetime | None
    created_at: datetime
```

### `POST /admin/users` (admin only)
Identyczny jak `POST /auth/register`.

### `PUT /admin/users/{id}` (admin only)

```python
class UserUpdate(BaseModel):
    email: str | None = Field(None, max_length=100)
    first_name: str | None = Field(None, max_length=30)
    last_name: str | None = Field(None, max_length=30)
    role: Literal["admin", "user", "viewer"] | None = None
    branch_id: int | None = None
    is_active: bool | None = None
```

### `PATCH /admin/users/{id}/deactivate` (admin only)

**Algorytm:**
1. `UPDATE users SET is_active = FALSE WHERE id = :id`
2. Admin nie może deaktywować samego siebie
3. Return 200

### `PATCH /admin/users/{id}/activate` (admin only)

**Algorytm:**
1. `UPDATE users SET is_active = TRUE WHERE id = :id`
2. Return 200

### `POST /admin/users/{id}/force-password-reset` (admin only)

> Admin wymusza reset hasła — użytkownik musi zmienić hasło przy następnym logowaniu.

**Algorytm:**
1. `UPDATE users SET must_change_password = TRUE WHERE id = :id`
2. Return 200

### Email Service (SMTP)

```python
# auth/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self, settings: Settings):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_addr = settings.smtp_from
        self.use_tls = settings.smtp_tls

    async def send_password_reset(
        self, to_email: str, reset_link: str, user_name: str
    ):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "RAO — Resetowanie hasła"
        msg["From"] = self.from_addr
        msg["To"] = to_email

        html = f"""
        <html><body style="font-family: Montserrat, sans-serif; color: #1D2B53;">
        <h2>Resetowanie hasła</h2>
        <p>Cześć {user_name},</p>
        <p>Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w systemie RAO.</p>
        <p><a href="{reset_link}"
           style="background: #1D2B53; color: white; padding: 12px 32px;
                  border-radius: 24px; text-decoration: none; display: inline-block;">
           Ustaw nowe hasło
        </a></p>
        <p style="color: #718096; font-size: 13px;">Link jest ważny przez 1 godzinę.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
```

---

## CONTRACTORS — Endpointy

### `GET /contractors`

```python
# Query params
# ?search=firma&supplier=true&page=1&per_page=50

# Response 200
class ContractorListItem(BaseModel):
    id: int
    name: str
    name_short: str | None
    nip: str | None
    city: str | None
    street: str | None
    is_supplier: bool
    phone1: str | None
    email: str | None
    # Computed:
    active_contract_number: str | None  # numer trwającej umowy (z VIEW)
    created_at: datetime
    updated_at: datetime | None

# class PaginatedResponse[T]:
#     items: list[T]
#     total: int
#     page: int
#     per_page: int
```

**Algorytm (zastępuje VIEW `kontrahenci`):**
```sql
SELECT c.*,
  (SELECT u.number FROM contracts u
   WHERE u.contractor_id = c.id AND u.date_to >= CURDATE()
   ORDER BY u.date_to DESC LIMIT 1) AS active_contract_number
FROM contractors c
WHERE (:search IS NULL OR c.name LIKE :search OR c.nip LIKE :search)
  AND (:supplier IS NULL OR c.is_supplier = :supplier)
ORDER BY c.name
LIMIT :per_page OFFSET :offset
```

### `GET /contractors/{id}`

```python
class ContractorDetail(BaseModel):
    id: int
    name: str
    name_short: str | None
    nip: str | None
    regon: str | None
    pesel: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    unit: str | None
    notes: str | None
    is_supplier: bool
    email: str | None
    contact_person1: str | None
    phone1: str | None
    contact_person2: str | None
    phone2: str | None
    landline_phone: str | None
    website: str | None
    files_folder: str | None
    gus_date: datetime | None
    created_at: datetime
    updated_at: datetime | None
    addresses: list[AddressResponse]
```

### `POST /contractors`

```python
class ContractorCreate(BaseModel):
    name: str = Field(..., max_length=400)
    name_short: str | None = Field(None, max_length=200)
    nip: str | None = Field(None, max_length=20)
    regon: str | None = Field(None, max_length=20)
    pesel: str | None = Field(None, max_length=20)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=50)
    street: str | None = Field(None, max_length=50)
    unit: str | None = Field(None, max_length=50)
    notes: str | None = None
    is_supplier: bool = False
    email: str | None = Field(None, max_length=100)
    contact_person1: str | None = Field(None, max_length=100)
    phone1: str | None = Field(None, max_length=100)
    contact_person2: str | None = Field(None, max_length=100)
    phone2: str | None = Field(None, max_length=100)
    landline_phone: str | None = Field(None, max_length=20)
    website: str | None = Field(None, max_length=100)
```

**Walidacja biznesowa:**
1. Jeśli `nip` podany → sprawdź unikalność: `SELECT count(*) FROM contractors WHERE nip = :nip`
2. Jeśli count > 0 → 409 "Kontrahent z tym NIP-em już istnieje"

### `PUT /contractors/{id}`
Identyczny model jak `ContractorCreate`, walidacja NIP z wyłączeniem current ID.

### `DELETE /contractors/{id}`
1. Sprawdź czy ma aktywne umowy: `SELECT count(*) FROM contracts WHERE contractor_id = :id AND date_to >= CURDATE()`
2. Jeśli ma → 409 "Nie można usunąć—kontrahent ma aktywne umowy"
3. Usunięcie kaskadowe: adresy usunięte automatycznie (ON DELETE CASCADE)

### `GET /contractors/{id}/addresses`

```python
class AddressResponse(BaseModel):
    id: int
    contractor_id: int
    name: str | None
    country_code: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    notes: str | None
    contact_person: str | None
    phone: str | None
    email: str | None
    is_default_delivery: bool
    is_headquarters: bool
    latitude: Decimal | None
    longitude: Decimal | None
```

### `POST /contractors/{id}/addresses`
### `PUT /contractors/{contractor_id}/addresses/{id}`
### `DELETE /contractors/{contractor_id}/addresses/{id}`

```python
class AddressCreate(BaseModel):
    name: str | None = Field(None, max_length=200)
    country_code: str = Field("PL", max_length=3)
    postal_code: str | None = Field(None, max_length=20)
    city: str | None = Field(None, max_length=50)
    street: str | None = Field(None, max_length=50)
    notes: str | None = Field(None, max_length=200)
    contact_person: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=20)
    is_default_delivery: bool = False
    is_headquarters: bool = False
    latitude: Decimal | None = None
    longitude: Decimal | None = None
```

### `POST /contractors/gus-lookup`

```python
class GusLookupRequest(BaseModel):
    nip: str = Field(..., pattern=r"^\d{10}$")

class GusLookupResponse(BaseModel):
    name: str | None
    street: str | None
    building_number: str | None
    apartment_number: str | None
    postal_code: str | None
    city: str | None
    regon: str | None
    province: str | None  # województwo
    county: str | None    # powiat
    community: str | None # gmina
    status: str | None    # status firmy
```

**Algorytm GUS:**
1. SOAP call: `Zaloguj` → pSID (session key)
2. SOAP call: `DaneSzukajPodmioty` z NIP
3. SOAP call: `DanePobierzPelnyRaport` z REGON
4. Parse XML → `GusLookupResponse`
5. SOAP call: `Wyloguj`

---

## ARTICLES — Endpointy

### `GET /articles`

```python
# Query: ?search=koparka&category_id=1&owner_id=5&page=1&per_page=50

class ArticleListItem(BaseModel):
    id: int
    name: str
    is_service: bool
    internal_number: str | None
    registration_no: str | None
    serial_no: str | None
    brand: str | None
    model: str | None
    replacement_value: Decimal | None
    category_name: str | None          # JOIN categories
    category_main: str | None          # RAO-P1-026: denorm kategoria główna
    owner_name: str | None             # JOIN contractors
    notes: str | None
    is_archival: bool                  # RAO-P1-026
    active_contract_number: str | None  # computed
    created_at: datetime
    updated_at: datetime | None
    conditions_count: int              # ile rozliczeń (computed)
```

**Algorytm (zastępuje VIEW `artykuly`/`artykulyy`):**
```sql
SELECT a.*,
  cat.name AS category_name,
  own.name AS owner_name,
  (SELECT u.number FROM contracts u
   JOIN contract_positions cp ON cp.contract_id = u.id
   WHERE cp.article_id = a.id AND u.date_to >= CURDATE()
   LIMIT 1) AS active_contract_number,
  (SELECT COUNT(*) FROM contract_positions cp2
   JOIN position_conditions pc ON pc.position_id = cp2.id
   WHERE cp2.article_id = a.id) AS conditions_count
FROM articles a
LEFT JOIN categories cat ON a.category_id = cat.id
LEFT JOIN contractors own ON a.owner_id = own.id
```

### `POST /articles`

```python
class ArticleCreate(BaseModel):
    name: str = Field(..., max_length=200)
    is_service: bool = False
    internal_number: str | None = Field(None, max_length=50)
    registration_no: str | None = Field(None, max_length=40)
    serial_no: str | None = Field(None, max_length=40)
    brand: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    replacement_value: Decimal | None = None
    category_id: int | None = None
    owner_id: int | None = None
    branch_id: int | None = None
    description: str | None = Field(None, max_length=400)
    notes: str | None = Field(None, max_length=200)
    article_type: str | None = Field(None, max_length=20)
    zasieg_m: Decimal | None = None    # RAO-P1-026: zasięg roboczy [m]
    udzwig_t: Decimal | None = None    # RAO-P1-026: udźwig [t]
    dodatki: str | None = None         # RAO-P1-026: wyposażenie dodatkowe
```

### `GET /articles/{id}` (RAO-P1-026)

Response: `ArticleDetail` — rozszerzony obiekt artykułu z hierarchią kategorii i polami technicznymi:
- Wszystkie pola z `ArticleListItem`
- `category_main`, `category_sub1`, `category_sub2`, `category_sub3` — denorm z `articles`
- `zasieg_m: Decimal | None` — zasięg roboczy [m]
- `udzwig_t: Decimal | None` — udźwig [t]
- `dodatki: str | None` — wyposażenie dodatkowe

HTTP: 200 | 401 | 404

### `POST /articles/{id}/duplicate`

**Algorytm (zastępuje procedurę `DuplikujArtykul2`):**
1. `SELECT * FROM articles WHERE id = :id`
2. `INSERT INTO articles (...) VALUES (...)` — kopia, ale:
   - `name` += " (kopia)"
   - `registration_no` = NULL
   - `serial_no` = NULL
   - `created_at` = now()
3. Return new article ID

### `GET /articles/{id}/availability`

```python
# Query: ?date_from=2026-01-01&date_to=2026-12-31

class AvailabilityResponse(BaseModel):
    is_available: bool
    conflicting_contracts: list[ConflictingContract]

class ConflictingContract(BaseModel):
    contract_id: int
    contract_number: str
    date_from: date
    date_to: date
    contractor_name: str
```

**Algorytm (zastępuje procedurę `sprDostepnosc`):**
```sql
SELECT c.id, c.number, c.date_from, c.date_to, ct.name AS contractor_name
FROM contract_positions cp
JOIN contracts c ON cp.contract_id = c.id
JOIN contractors ct ON c.contractor_id = ct.id
WHERE cp.article_id = :article_id
  AND c.date_from <= :date_to
  AND c.date_to >= :date_from
```

---

## CONTRACTS — Endpointy

### `GET /contracts`

```python
# Query: ?search=S001&date_from=2026-01-01&date_to=2026-12-31&type=S&page=1&per_page=50

class ContractListItem(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str        # JOIN
    number: str
    contract_type: str          # 'S' lub 'U'
    type_label: str             # 'Umowa najmu' / 'Umowa usługi'
    description: str | None
    delivery_address: str | None
    date_from: date | None
    date_to: date | None
    total_value: Decimal | None
    prepayment_amount: Decimal | None
    invoice_amount: Decimal | None
    notes: str | None
    email: str | None
    salesperson_name: str | None # JOIN
    print_date: datetime | None
    is_print_current: bool       # computed: print_date > updated_at
    duration_days: int | None    # computed: DATEDIFF
    created_at: datetime
```

### `POST /contracts`

```python
class ContractCreate(BaseModel):
    contractor_id: int
    branch_id: int | None = None
    salesperson_id: int | None = None
    contract_type: Literal["S", "U"] = "S"
    delivery_address: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    total_value: Decimal = Decimal("0.00")
    prepayment_amount: Decimal = Decimal("0.00")
    prepayment_document: str | None = None
    invoice_amount: Decimal = Decimal("0.00")
    invoice_document: str | None = None
    notes: str | None = None
    # UWAGA: Usługi dodatkowe tworzone automatycznie z service_fee_templates
    # Endpoint: POST /contracts/{id}/service-fees do późniejszej edycji
    contact_person1: str | None = None
    contact_phone1: str | None = None
    show_person1: bool = True
    contact_person2: str | None = None
    contact_phone2: str | None = None
    show_person2: bool = True
    email: str | None = None
    phone: str | None = None
    contractor_name: str | None = None
    working_days_per_week: int = 6
    report_without_data: bool = False
    hide_delivery_address: bool = False
    signatures_on_page1: bool = False
    # Auto:
    # number → generated by service
    # auto_number → generated by service
```

**Algorytm tworzenia numeru (kluczowa logika biznesowa):**
```python
async def generate_contract_number(
    db: AsyncSession,
    contract_type: str  # "S" lub "U"
) -> tuple[str, int]:
    """
    Generuje numer w formacie: S001/2026 lub U001/2026
    1. Pobierz numerację startową z company
    2. Pobierz max(auto_number) z contracts
    3. Nowy auto_number = max(numeracja, max_auto) + 1
    4. Prefix = "S" dla najem, "U" dla usługa
    5. Format: {prefix}{auto_number:03d}/{rok}
    """
    company = await db.execute(select(Company.numbering_start).where(Company.id == 1))
    start = company.scalar_one_or_none() or 1

    max_auto = await db.execute(
        select(func.max(Contract.auto_number))
    )
    current_max = max_auto.scalar_one_or_none() or 0

    new_number = max(start, current_max) + 1
    year = datetime.now().year
    prefix = contract_type  # "S" or "U"

    return f"{prefix}{new_number:03d}/{year}", new_number
```

### `PUT /contracts/{id}`
Identyczny model, ale `number` i `auto_number` nie mogą być zmienione.

### `DELETE /contracts/{id}`

**Algorytm kaskadowego usuwania (identyczny z WinForms):**
```python
async def delete_contract(db: AsyncSession, contract_id: int):
    # Kolejność identyczna z WinForms:
    # 1. Usuń warunki rozliczenia per pozycja
    await db.execute(
        delete(PositionCondition).where(
            PositionCondition.position_id.in_(
                select(ContractPosition.id).where(
                    ContractPosition.contract_id == contract_id
                )
            )
        )
    )
    # 2. Usuń pozycje
    await db.execute(
        delete(ContractPosition).where(
            ContractPosition.contract_id == contract_id
        )
    )
    # 3. Usuń oddział umowy (w nowym schemacie to pole FK, więc auto)
    # 4. Usuń dostawę
    await db.execute(
        delete(Delivery).where(Delivery.contract_id == contract_id)
    )
    # 5. Usuń umowę
    await db.execute(
        delete(Contract).where(Contract.id == contract_id)
    )
    await db.commit()
```

### `GET /contracts/{id}/positions`

```python
class PositionResponse(BaseModel):
    id: int
    contract_id: int
    article_id: int
    article_name: str | None     # snapshot lub JOIN
    rental_type: str | None
    description: str | None
    rental_days: int | None
    quantity: int | None
    unit_price: Decimal | None
    costs: Decimal | None
    rate_type_id: int | None
    rate_type_name: str | None   # JOIN
    billing_frequency: str | None
    billing_unit: str | None
    supplier_id: int | None
    supplier_name: str | None    # JOIN
    delivery_date: date | None
    conditions_count: int        # computed
    conditions: list[ConditionResponse]
```

### `POST /contracts/{id}/positions`

```python
class PositionCreate(BaseModel):
    article_id: int
    rental_type: str | None = None
    description: str | None = Field(None, max_length=400)
    rental_days: int | None = None
    quantity: int = 1
    unit_price: Decimal | None = None
    rate_type_id: int | None = None
    billing_frequency: str | None = None
    billing_unit: str | None = None
    supplier_id: int | None = None
    delivery_date: date | None = None
```

### `GET /contracts/{id}/positions/{pos_id}/conditions`

```python
class ConditionResponse(BaseModel):
    id: int
    position_id: int
    rate_type_id: int | None
    rate_type_name: str | None   # JOIN
    description: str | None
    rate1: Decimal | None
    rate2: Decimal | None
    billing_label: str | None
    period_count: int | None
    minimum: int | None
```

### `POST /contracts/{id}/positions/{pos_id}/conditions`

```python
class ConditionCreate(BaseModel):
    rate_type_id: int | None = None
    description: str | None = Field(None, max_length=400)
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = None
    period_count: int | None = None
    minimum: int | None = None
```

### `PUT /contracts/{id}/value`

**Algorytm kalkulacji wartości umowy:**
```python
async def recalculate_contract_value(db: AsyncSession, contract_id: int):
    """
    Algorytm identyczny z WinForms FormU4:
    1. Pobierz wszystkie pozycje umowy
    2. Dla każdej pozycji pobierz warunki
    3. Oblicz wartość pozycji na basis warunków i liczby dni
    4. Suma = total_value
    5. Remaining = total_value - prepayment_amount - invoice_amount
    """
    positions = await db.execute(
        select(ContractPosition)
        .where(ContractPosition.contract_id == contract_id)
    )
    total = Decimal("0.00")
    for pos in positions.scalars():
        conditions = await db.execute(
            select(PositionCondition)
            .where(PositionCondition.position_id == pos.id)
            .order_by(PositionCondition.period_count)
        )
        pos_value = calculate_position_value(
            pos.rental_days, pos.billing_frequency, conditions.scalars().all()
        )
        total += pos_value

    await db.execute(
        update(Contract)
        .where(Contract.id == contract_id)
        .values(total_value=total)
    )
```

### `GET /contracts/{id}/service-fees`
### `POST /contracts/{id}/service-fees`
### `PUT /contracts/{id}/service-fees/{fee_id}`
### `DELETE /contracts/{id}/service-fees/{fee_id}`
### `POST /contracts/{id}/service-fees/reorder`
### `POST /contracts/{id}/service-fees/reset`

### `POST /contracts/{contract_id}/service-fees/apply-preset`

**Opis:** Zastosuj gotowy szablon usług dodatkowych (`fee_preset_groups`) do umowy.

**Query:**
- `preset_id` (int, required): ID szablonu (`fee_preset_groups.id`)
- `replace` (bool, optional, default=true): `true` = usuń istniejące usługi przed dodaniem; `false` = dołącz

**Response:** `{ "message": "Zestaw zastosowany" }`
**HTTP:** 200 | 401 | 404 (umowa lub szablon nie istnieje)

### `GET /contracts/positions/{position_id}/service-hours` (RAO-P1-014)

**Response:**
```python
class ServiceHourResponse(BaseModel):
    id: int
    position_id: int
    service_date: date
    time_from: time | None
    time_to: time | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None
```

### `POST /contracts/positions/{position_id}/service-hours` (RAO-P1-014)

**Request:**
```python
class ServiceHourCreate(BaseModel):
    service_date: date
    time_from: time | None = None
    time_to: time | None = None
    notes: str | None = Field(None, max_length=500)
```

### `PUT /contracts/positions/{position_id}/service-hours/{hour_id}` (RAO-P1-014)

**Request:**
```python
class ServiceHourUpdate(BaseModel):
    service_date: date | None = None
    time_from: time | None = None
    time_to: time | None = None
    notes: str | None = Field(None, max_length=500)
```

### `DELETE /contracts/positions/{position_id}/service-hours/{hour_id}` (RAO-P1-014)

```python
class ContractServiceFeeResponse(BaseModel):
    id: int
    sort_order: int
    name: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    unit: str | None
    description: str | None
    is_active: bool

class ContractServiceFeeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=400)
    is_active: bool = True

class ContractServiceFeeReorder(BaseModel):
    ids: list[int]
```

**Algorytm POST /contracts (tworzenie umowy):**
```python
# Po zapisaniu umowy ZAWSZE kopiuj szablony:
async def copy_fee_templates_to_contract(
    db: AsyncSession, contract_id: int, contract_type: str
):
    templates = await db.execute(
        select(ServiceFeeTemplate)
        .where(ServiceFeeTemplate.contract_type == contract_type)
        .where(ServiceFeeTemplate.is_active == True)
        .order_by(ServiceFeeTemplate.sort_order)
    )
    for t in templates.scalars():
        db.add(ContractServiceFee(
            contract_id=contract_id,
            sort_order=t.sort_order,
            name=t.name,
            amount_from=t.amount_from,
            amount_to=t.amount_to,
            unit=t.unit,
            description=t.description,
            is_active=t.is_active,
        ))
    await db.commit()
```

**Algorytm POST /reset:** Usuwa wszystkie istniejące opłaty i kopiuje z szablonu od nowa.

**Logika PDF (service.py):** Generuje tekst z aktywnych pozycji:
```python
def generate_fees_text(fees: list[ContractServiceFee]) -> str:
    lines = []
    for f in sorted(fees, key=lambda x: x.sort_order):
        if not f.is_active:
            continue
        if f.amount_from and f.amount_to:
            kwota = f"{f.amount_from:.2f} zł - {f.amount_to:.2f} zł"
        elif f.amount_from:
            kwota = f"{f.amount_from:.2f} zł"
        else:
            kwota = ""
        unit = f" / {f.unit}" if f.unit else ""
        desc = f" ({f.description})" if f.description else ""
        lines.append(f"- {f.name}: {kwota}{unit}{desc}".strip())
    return "\n".join(lines)
```

---

## SETTINGS — Endpointy

### `GET /settings/company`
### `PUT /settings/company`

```python
class CompanyResponse(BaseModel):
    id: int
    name: str | None
    name_short: str | None
    nip: str | None
    regon: str | None
    postal_code: str | None
    city: str | None
    street: str | None
    header_text: str | None
    bank_name: str | None
    bank_account: str | None
    numbering_start: int | None
    increment_step: Decimal | None
    report_folder: str | None
    protocol_folder: str | None
    # UWAGA: Szablony usług dodatkowych → GET /settings/service-fee-templates
```

### `GET /settings/service-fee-templates`
### `POST /settings/service-fee-templates`
### `PUT /settings/service-fee-templates/{id}`
### `DELETE /settings/service-fee-templates/{id}`
### `POST /settings/service-fee-templates/reorder`

```python
class ServiceFeeTemplateResponse(BaseModel):
    id: int
    preset_id: int | None = None
    contract_type: Literal['S', 'U']
    sort_order: int
    # RAO-P1-011: FK do articles + nazwa z articles (jeśli article_id ustawiony)
    article_id: int | None = None
    article_name: str | None = None
    default_price: Decimal | None = None
    name: str
    amount_from: Decimal | None
    amount_to: Decimal | None
    unit: str | None
    description: str | None
    is_active: bool

class ServiceFeeTemplateCreate(BaseModel):
    contract_type: Literal['S', 'U']
    preset_id: int | None = None
    # RAO-P1-011: opcjonalna referencja do artykułu (gdy ustawiona, nazwa derive z articles)
    article_id: int | None = None
    default_price: Decimal | None = None
    name: str = Field(..., max_length=200)
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    unit: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=400)
    is_active: bool = True

class ServiceFeeTemplateReorder(BaseModel):
    ids: list[int]  # kolejność wierszy dla danego contract_type
```

**Logika GET:** Zwraca wszystkie templates dla company_id=1, posortowane po `(contract_type, sort_order)`.
**Logika POST /reorder:** Przyjmuje listę id w nowej kolejności, aktualizuje `sort_order` wszystkich.

### `GET /settlements/contract/{contract_id}` - RAO-P1-012
### `GET /settlements/{settlement_id}`
### `POST /settlements`
### `PUT /settlements/{settlement_id}`
### `DELETE /settlements/{settlement_id}`

```python
class ContractSettlementResponse(BaseModel):
    id: int
    contract_id: int
    position_id: int | None = None
    cost_client: Decimal | None = None
    cost_company: Decimal | None = None
    margin: Decimal | None = None  # auto-calculated: cost_client - cost_company
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

class ContractSettlementCreate(BaseModel):
    contract_id: int
    position_id: int | None = None
    cost_client: Decimal | None = Field(None, ge=0)
    cost_company: Decimal | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)

class ContractSettlementUpdate(BaseModel):
    cost_client: Decimal | None = Field(None, ge=0)
    cost_company: Decimal | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)
```

**Logika:**
- GET /contract/{contract_id}: Zwraca wszystkie rozliczenia dla umowy
- Auto-creowanie: Po utworzeniu umowy, automatycznie tworzy rekordy settlement dla wszystkich pozycji (cost_client/cost_company = NULL)
- Margin: Automatycznie obliczane jako cost_client - cost_company

### `GET /settings/salespeople`
### `POST /settings/salespeople`
### `PUT /settings/salespeople/{id}`
### `PATCH /settings/salespeople/{id}/toggle`

```python
class SalespersonResponse(BaseModel):
    id: int
    name: str
    phone: str | None
    is_active: bool

class SalespersonCreate(BaseModel):
    name: str = Field(..., max_length=200)
    phone: str | None = Field(None, max_length=100)
```

### `GET /settings/categories/tree` (RAO-P2-019, NOWY)

Zwraca hierarchiczne drzewo kategorii (główne + zagnieżdżone children do 3 poziomów).
Używa explicit `selectinload` — bez lazy-load w async.

**Auth:** Bearer token wymagany  
**Response:** `200 list[CategoryTreeNode]`

```python
class CategoryTreeNode(BaseModel):
    id: int
    name: str
    level: str                         # "main" | "sub1" | "sub2" | "sub3"
    code: str | None = None
    parent_id: int | None = None
    children: list['CategoryTreeNode'] = []
    # from_attributes = True
```

**Przykład response:**
```json
[
  {
    "id": 1, "name": "Koparki", "level": "main", "code": null, "parent_id": null,
    "children": [
      { "id": 5, "name": "Mini", "level": "sub1", "code": "KOP-MINI", "parent_id": 1, "children": [] }
    ]
  }
]
```

---

### `GET /settings/categories`
### `POST /settings/categories`
### `PUT /settings/categories/{cat_id}`
### `DELETE /settings/categories/{cat_id}`

`DELETE` zwraca **409** gdy kategoria ma podkategorie — usuń je najpierw.

```python
class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=200)
    code: str | None = Field(None, max_length=40)
    description: str | None = Field(None, max_length=400)
    parent_id: int | None = None      # RAO-P2-019: hierarchia
    level: str = Field("main", pattern="^(main|sub1|sub2|sub3)$")

class CategoryResponse(BaseModel):
    id: int
    name: str
    code: str | None = None
    description: str | None = None
    parent_id: int | None = None      # RAO-P2-019
    level: str = "main"               # RAO-P2-019
```

### `GET /settings/branches`

```python
class BranchResponse(BaseModel):
    id: int
    name: str
    address: str | None
    postal_code: str | None
    city: str | None
    street: str | None
```

### `GET /settings/rate-types`

```python
class RateTypeResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_dependent: bool
```

---

## REPORTS — Endpointy

> **RAO-P2-018 (backend done):** Ujednolicono nazwy plików PDF + RFC 5987 `Content-Disposition`.

### `POST /reports/contract/{id}`

```
Query: ?type=contract|protocol_zo_s|protocol_zo_u|protocol_zo_nodata_s
Response: application/pdf (binary)
HTTP: 200 | 401 | 404 (umowa nie istnieje) | 500
```

**Content-Disposition (RFC 5987):**
```
Content-Disposition: attachment; filename="<ascii_safe>"; filename*=UTF-8''<url_encoded>
```

**Konwencja nazw plików** (`numer_clean = contract.number.replace('/', '_')`):

| `type` | Wzorzec | Przykład |
|--------|---------|---------|
| `contract` | `{numer_clean}.pdf` | `S129_2026.pdf` |
| `protocol_zo_s` / `protocol_zo_u` / `protocol_zo_nodata_s` | `PZO_{numer_clean}.pdf` | `PZO_S129_2026.pdf` |

### `GET /reports/summary/contractors`

```
Response: application/pdf (binary)
HTTP: 200 | 401
Content-Disposition: attachment; filename="Kontrahenci_YYYY-MM-DD.pdf"; filename*=UTF-8''...
```

### `GET /reports/summary/machines`

```
Response: application/pdf (binary)
HTTP: 200 | 401
Content-Disposition: attachment; filename="Maszyny_YYYY-MM-DD.pdf"; filename*=UTF-8''...
```

### `GET /reports/summary/commissions`

```
Query: ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD  (domyślnie: bieżący miesiąc)
Response: application/pdf (binary)
HTTP: 200 | 401
Content-Disposition: attachment; filename="Prowizje_YYYY-MM-DD_YYYY-MM-DD.pdf"; filename*=UTF-8''...
```

### `GET /reports/summary/stats`

```
Query: ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD  (domyślnie: bieżący miesiąc)
Response: application/pdf (binary)
HTTP: 200 | 401
Content-Disposition: attachment; filename="Statystyki_YYYY-MM-DD_YYYY-MM-DD.pdf"; filename*=UTF-8''...
```

### `GET /stats/machine-roi`
Query: `?article_id=<int>&date_from&date_to&include_archival=false`
Response: `MachineRoiResponse` (zawiera `category_main` — RAO-P1-017)

### `GET /stats/currently-rented`
Response: `CurrentlyRentedResponse` (items zawierają `category_main` — RAO-P1-017)
Filtr: domyślnie `is_archival=FALSE`

### `GET /stats/additional-fees`
Query: `?date_from&date_to&internal_number=<str>` (RAO-P2-008)
Response: `AdditionalFeesResponse`

### `GET /stats/locations`
Query: `?date_from&date_to&internal_number=<str>` (RAO-P2-008)
Response: `list[LocationStatItem]`

### `GET /stats/by-category` (RAO-P1-017, RAO-P1-026)
Query:
- `level=main|sub1|sub2|sub3` (default: `main`) — poziom hierarchii kategorii
- `date_from`, `date_to` — zakres dat (default: bieżący miesiąc)
- `include_archival=false` — uwzględnij maszyny archiwalne
- `category_main=<str>` — filtr kategorii głównych (multi-value, opcjonalny)
- `category_sub1=<str>` — filtr sub1 (opcjonalny)
- `category_sub2=<str>` — filtr sub2 (opcjonalny)
- `article_type=all|machine|service` (default: `all`) — filtr rodzaju

Response: `CategoryStatsResponse` (`date_from`, `date_to`, `level`, `total_revenue`, `items[]`)
HTTP: 200 | 401 | 422 (nieprawidłowy `level` lub `article_type`)

### `GET /stats/by-period` (RAO-P1-026, NOWY)
Query:
- `granularity=month|year` (default: `month`) — granulacja czasowa
- `date_from`, `date_to` — zakres dat
- `category_main=<str>` — filtr/seria kategorii (multi-value; gdy podany → osobna seria per kategorię)
- `article_type=all|machine|service` (default: `all`)
- `include_archival=false`

Response: `ByPeriodResponse`:
```json
{
  "date_from": "2024-01-01",
  "date_to": "2024-12-31",
  "granularity": "month",
  "items": [
    { "period": "2024-01", "category_name": "__all__", "revenue": 15000.00, "contracts_count": 3, "rented_days": 31 }
  ]
}
```
HTTP: 200 | 401 | 422

### `GET /stats/categories-list` (RAO-P1-026, NOWY)
Query: brak

Response: `list[CategoriesListNode]` — pełne drzewo kategorii:
```json
[
  {
    "id": 1, "name": "Koparki", "level": "main", "articles_count": 12,
    "children": [
      { "id": 2, "name": "Mini", "level": "sub1", "articles_count": 5, "children": [] }
    ]
  }
]
```
Zlicza tylko aktywne (nie-archiwalne) artykuły (`is_archival=false`) przypisane do danej kategorii.
HTTP: 200 | 401

### `GET /stats/positions` (RAO-P2-010, NOWY)
Query: `?type=machines|services|all&date_from&date_to`
Response: `PositionStatsResponse` with:
- date_from, date_to, type (applied filter)
- total_revenue, total_machines_revenue, total_services_revenue
- items[]: list[PositionStatItem] (article_id, article_name, internal_number, is_service, category_main, revenue, rented_days, contracts_count, times_billed)
HTTP: 200 | 401 | 422 (nieprawidłowy `type`)

### `GET /explorer/machines/{article_id}` (RAO-P2-009)
Query: `?date_from&date_to`
Response: Machine metrics object with:
- total_revenue, total_days, avg_daily, utilization_pct
- rentals[]: historia wynajmów (contract_number, contractor_name, date_from, date_to, days, revenue)
HTTP: 200 | 404 (machine not found)

---

### `GET /stats/expiring-contracts`

**Opis:** Umowy kończące się w ciągu N dni.

**Query:** `?days=14` (opcjonalny, zakres 1-90, default=14)

**Response:** `list[ExpiringContractItem]`
```python
class ExpiringContractItem(BaseModel):
    id: int
    number: str
    contractor_name: str | None
    date_from: date | None
    date_to: date | None
    days_left: int
    delivery_address: str | None
    contact_person1: str | None
    contact_phone1: str | None
    salesperson_name: str | None
```
**HTTP:** 200 | 401

---

### `GET /stats/overdue-contracts`

**Opis:** Umowy przeterminowane (date_to < dziś).

**Response:** `list[OverdueContractItem]` (pola jak ExpiringContractItem + `days_overdue: int`)
**HTTP:** 200 | 401

---

### `GET /stats/deliveries-today`

**Opis:** Pozycje umów z datą dostawy przypadającą w ciągu N dni.

**Query:** `?lookahead=1` (opcjonalny, zakres 1-7, default=1)

**Response:** `list[DeliveryTodayItem]`
```python
class DeliveryTodayItem(BaseModel):
    contract_id: int
    contract_number: str
    contractor_name: str | None
    article_name: str | None
    delivery_date: date | None
    delivery_address: str | None
    contact_person1: str | None
    contact_phone1: str | None
```
**HTTP:** 200 | 401

---

### `GET /stats/unprinted-contracts`

**Opis:** Umowy nigdy nie wydrukowane (print_date IS NULL), aktywne lub utworzone w ostatnich 60 dniach.

**Response:** `list[UnprintedContractItem]` (id, number, contractor_name, date_from, date_to, created_at)
**HTTP:** 200 | 401

---

### `GET /stats/stale-print-contracts`

**Opis:** Umowy edytowane po wydruku (print_date < updated_at), aktywne lub zmodyfikowane w ostatnich 30 dniach.

**Response:** `list[StalePrintContractItem]` (id, number, contractor_name, date_from, date_to, print_date, updated_at)
**HTTP:** 200 | 401

---

### `GET /stats/commissions`

**Opis:** Raport prowizji handlowców za okres. Prowizja obliczana z marży (contract_settlements).

**Query:** `?date_from&date_to` (opcjonalne, default: bieżący miesiąc)

**Response:** `CommissionReportResponse`
```python
class SalespersonCommissionItem(BaseModel):
    salesperson_id: int
    salesperson_name: str
    commission_rate: Decimal | None
    contracts_count: int
    total_revenue: Decimal
    commission_amount: Decimal         # margin × rate / 100

class CommissionReportResponse(BaseModel):
    date_from: date
    date_to: date
    items: list[SalespersonCommissionItem]
    grand_total_revenue: Decimal
    grand_total_commission: Decimal
```
**HTTP:** 200 | 401

---

### `GET /explorer/search`

**Opis:** Uniwersalne wyszukiwanie po pozycjach umów (maszyny + usługi).

**Query:** `?q=&date_from=&date_to=&category=&city=&contractor_id=&limit=50&offset=0`

**Response:**
```python
{
    "items": [{"type": str, "type_label": str, "id": int, "article_id": int,
               "name": str, "internal_number": str|None, "contract_number": str,
               "contractor_name": str|None, "date": str, "city": str, "amount": float}],
    "total": int,
    "summary": {"count": int, "revenue": float},
    "offset": int,
    "limit": int,
}
```
**HTTP:** 200 | 401

---

### `GET /explorer/services`

**Opis:** Podsumowanie usług dodatkowych (is_service=True) — liczba rozliczeń i przychód.

**Query:** `?date_from=&date_to=&service_type=`

**Response:** `{"services": [{article_id, service_name, times_billed, total_revenue, percentage}], "total_revenue": float, "count": int, "period": {...}}`
**HTTP:** 200 | 401

---

### `GET /explorer/locations`

**Opis:** Podsumowanie wynajmów po miastach (city z delivery_address).

**Query:** `?date_from=&date_to=&limit=50`

**Response:** `{"locations": [{rank, city, rentals_count, total_revenue}], "count": int, "period": {...}}`
**HTTP:** 200 | 401

---

### `GET /explorer/services/{article_id}`

**Opis:** Szczegóły usługi: metryki, top kontrahenci (5), rozkład geograficzny (10 miast).

**Query:** `?date_from=&date_to=`

**Response:** `{service: {id, name}, metrics: {times_billed, total_revenue}, top_contractors: [...], location_breakdown: [...]}`
**HTTP:** 200 | 401 | 404

---

### `GET /explorer/locations/{city}`

**Opis:** Szczegóły lokalizacji: metryki, top maszyny (10), top kontrahenci (5).

**Query:** `?date_from=&date_to=`

**Response:** `{city, metrics: {contracts_count, unique_contractors, total_revenue, avg_revenue_per_contract}, top_machines: [...], top_contractors: [...]}`
**HTTP:** 200 | 401 | 404

---

> Pełna specyfikacja raportów z obrazkami i endpointów statystyk znajduje się w pliku **[11_reports_stats.md](./11_reports_stats.md)**.

---

## INTEGRATIONS

### `POST /integrations/gus-lookup`
→ Zobacz: `GusLookupRequest`/`GusLookupResponse` w sekcji CONTRACTORS

### `POST /integrations/reverse-geocode`

```python
class ReverseGeocodeRequest(BaseModel):
    latitude: Decimal
    longitude: Decimal

class ReverseGeocodeResponse(BaseModel):
    street: str | None
    house_number: str | None
    postal_code: str | None
    hamlet: str | None
    city: str | None
    town: str | None
    village: str | None
    county: str | None
    municipality: str | None
    province: str | None
    district: str | None
    neighbourhood: str | None
```

**Algorytm:**
```python
async def reverse_geocode(lat: Decimal, lng: Decimal) -> dict:
    url = f"{NOMINATIM_URL}/reverse?lat={lat}&lon={lng}&format=json&addressdetails=1"
    headers = {"User-Agent": "RAO-App/1.0", "Accept-Language": "pl"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        data = resp.json()
        return data.get("address", {})
```

### `GET /integrations/postal-codes/{code}` (RAO-P1-008)

**Opis:** Auto-uzupełnianie miasta po kodzie pocztowym

**Request:**
- `code` (path): Kod pocztowy w formacie XX-XXX (np. "00-001")

**Response:**
```python
class PostalCodeLookupResponse(BaseModel):
    code: str
    city: str | None
    voivodeship: str | None
```

**Algorytm:**
```python
async def lookup_postal_code(code: str, db: AsyncSession) -> dict:
    # Walidacja formatu kodu pocztowego
    if not re.match(r"^\d{2}-\d{3}$", code):
        raise HTTPException(422, "Invalid postal code format (expected XX-XXX)")

    # Lookup w tabeli postal_codes
    result = await db.execute(
        select(PostalCode).where(PostalCode.code == code)
    )
    postal_code = result.scalar_one_or_none()

    if not postal_code:
        return {"code": code, "city": None, "voivodeship": None}

    return {
        "code": postal_code.code,
        "city": postal_code.city,
        "voivodeship": postal_code.voivodeship
    }
```

### `POST /integrations/teryt/sync` (RAO-P2-015)

**Opis:** Synchronizuj słownik kodów pocztowych z pre-generowanego pliku SQL. Ładuje dane z `backend/integrations/teryt/postal_codes_inserts.sql`.

**Request Body:** brak
**Response:** `TerytSyncResponse`
```python
class TerytSyncResponse(BaseModel):
    success: bool
    message: str
    count: int    # Liczba zsynchronizowanych rekordów
```
**HTTP:** 200 | 401 | 404 (plik SQL nie znaleziony) | 500 (błąd synchronizacji)

---

## Integracja Fakturownia (RAO-P2-012)

### Endpointy

```
GET /integrations/fakturownia/settings
  Response: FakturowniaSettingsOut
  RBAC: admin-only
  Opis: Pobierz konfigurację integracji (token preview tylko)

PUT /integrations/fakturownia/settings
  Request: FakturowniaSettingsIn
  Response: FakturowniaSettingsOut
  RBAC: admin-only, rate limit 5/min/IP
  Opis: Zaktualizuj konfigurację (token szyfrowany Fernet przed zapisem)

GET /integrations/fakturownia/products
  Response: List[FakturowniaProductOut]
  RBAC: admin-only
  Opis: Pobierz katalog produktów z Fakturownia API

GET /integrations/fakturownia/invoices?contract_id={id}
  Response: List[ResolvedInvoiceOut]
  RBAC: authenticated, ownership check (tylko własne umowy), rate limit 30/min/user
  Opis: Pobierz faktury dla umowy z 1:N mapping artykułów
  IDOR fix: contract_id zamiast oid, OID pobierany z DB
```

### Schemas

```python
# Settings
class FakturowniaSettingsIn(BaseModel):
    enabled: bool
    api_token: Optional[str]  # plaintext, szyfrowany przed DB
    domain_subdomain: Optional[str]  # validated ^[a-z0-9-]+$

class FakturowniaSettingsOut(BaseModel):
    id: int
    enabled: bool
    api_token_preview: Optional[str]  # np. "tk_****1234"
    domain_subdomain: Optional[str]
    api_token_updated_at: Optional[datetime]
    api_token_updated_by: Optional[int]

# Products
class FakturowniaProductOut(BaseModel):
    id: int
    name: str
    code: Optional[str]
    price_net: Optional[Decimal]
    currency: Optional[str]

# Invoices (resolved z 1:N mapping)
class ResolvedInvoiceOut(BaseModel):
    invoice_number: str
    lines: List[ResolvedInvoiceLine]
    total_net: Decimal
    mapped_total_net: Decimal  # sum z multiplikacji 1:N
    unmapped_count: int
```

### Security

- Fernet encryption tokenów at-rest (api_token_ciphertext VARBINARY)
- Token preview tylko w responses (api_token_preview)
- SSRF protection na domain_subdomain (whitelist regex)
- IDOR fix przez contract_id + ownership check
- RBAC admin-only na settings/products
- Rate limiting (sliding window)
- Pydantic extra='forbid' na wszystkich input schemas

---

## Middleware & Dependencies

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Uwaga:** Przy zmianie portu frontend (np. gdy 5173 jest zajęty i Vite używa 5174), 
należy zaktualizować `RAO_CORS_ORIGINS` w `.env` aby zawierał nowy port:
```bash
RAO_CORS_ORIGINS=["http://localhost:5173","http://localhost:5174","http://localhost:3000"]
```

### Auth Dependency

```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401, "User not found")
    return user
```

### Pagination

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
```

---

## HEALTH CHECK & VERSION

### `GET /health`

**Opis:** Sprawdzenie stanu aplikacji. Endpoint publiczny (bez autentykacji).

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```
**HTTP:** 200

---

### `GET /version`

**Opis:** Zwraca informacje o wersji aplikacji (git commit hash). Endpoint publiczny (bez autentykacji). Używany do weryfikacji wersji deploymentu na produkcji vs. branch lokalny.

**Response:**
```json
{
  "app": "RAO API",
  "version": "1.0.0",
  "git_hash": "37dd754867cf85482596bc43f9da1081249a8b3d",
  "git_short": "37dd754",
  "git_branch": "main"
}
```

**Pola:**
- `app` — nazwa aplikacji
- `version` — wersja API (semantic versioning)
- `git_hash` — pełny SHA-1 commit hash (40 znaków)
- `git_short` — skrócony commit hash (7 znaków)
- `git_branch` — nazwa brancha git

**Logika:**
1. Próba pobrania hashu z `git rev-parse HEAD` (jeśli `.git` dostępny)
2. Fallback: czytanie z pliku `VERSION` w root projektu (jeśli git niedostępny na prodzie)
3. Fallback: `"unknown"` jeśli obie metody zawiodą

**Weryfikacja deploymentu:**
```bash
# Produkcja
curl https://toolsmart.pl/rao/api/version

# Lokalnie
git rev-parse HEAD
git log -1 --oneline
```

**HTTP:** 200

---

## Znane problemy i naprawy

### Problem: Błąd CORS przy zmianie portu frontend
**Symptom:** `Access to XMLHttpRequest at 'http://localhost:8000/...' from origin 'http://localhost:5174' has been blocked by CORS policy`

**Rozwiązanie:** Zaktualizuj `RAO_CORS_ORIGINS` w `.env` aby zawierał aktualny port frontendu:
```bash
RAO_CORS_ORIGINS=["http://localhost:5173","http://localhost:5174","http://localhost:3000"]
```

**Pliki do zmiany:** `.env`

---

### Problem: TypeError w /stats/fleet-summary (backend/stats/router.py:202)
**Symptom:** `TypeError: unsupported operand type(s) for /: 'int' and 'Article'`

**Przyczyna:** Zapytanie `select(Article)` zwraca obiekty Article zamiast liczby.

**Rozwiązanie:** Użyj `func.count(Article.id)`:
```python
# Błędne:
machines_query = select(Article).where(...)

# Poprawne:
machines_query = select(func.count(Article.id)).where(...)
```

**Pliki do zmiany:** `backend/stats/router.py` (linia ~172)

---

### Problem: Nieprawidłowe hasło admin po migracji
**Symptom:** Logowanie jako admin z hasłem `admin123` nie działa

**Rozwiązanie:** Uruchom skrypt resetujący hasło:
```bash
cd backend
. .venv/bin/activate
python reset_admin_password.py
```

**Pliki:** `backend/reset_admin_password.py`

---

### Problem: Brakujące zależności npm po czystej instalacji
**Symptom:** `Failed to run dependency scan... vue-draggable-plus`, `@vuepic/vue-datepicker`

**Rozwiązanie:** Zainstaluj brakujące pakiety:
```bash
cd frontend
npm install vue-draggable-plus @vuepic/vue-datepicker
```

**Pliki:** `frontend/package.json`
