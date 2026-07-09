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
# Query: ?search=koparka&category_id=1&owner_id=5&is_service=true&archival_status=active&page=1&per_page=50
# is_service: bool | None (optional filter for services vs machines)

class ArticleArchivalFilter(str, Enum):
    ACTIVE = "active"      # domyślnie — tylko aktywne (backward compatible)
    ARCHIVAL = "archival"  # tylko archiwalne

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
    is_external: bool                  # RAO-P1-027: maszyna zewnętrzna
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
# Query: ?search=S001&date_from=2026-01-01&date_to=2026-12-31&type=S&is_settled=false&page=1&per_page=50
# is_settled: None=wszystkie, false=aktywne (is_settled=false AND date_to >= dzisiaj), true=rozliczone

class ContractListItem(BaseModel):
    id: int
    contractor_id: int
    contractor_name: str        # JOIN
    number: str
    contract_type: str          # 'S' lub 'U'
    type_label: str             # 'Umowa najmu' / 'Umowa usługi'
    delivery_address: str | None
    postal_code: str | None
    city: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    date_from: date | None
    date_to: date | None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None
    invoice_amount: Decimal | None
    notes: str | None
    email: str | None
    phone: str | None
    contact_person1: str | None = None
    contact_phone1: str | None = None
    salesperson_name: str | None # JOIN
    print_date: datetime | None
    is_print_current: bool       # computed: print_date > updated_at
    duration_days: int | None    # computed: DATEDIFF
    is_settled: bool = False
    settled_at: datetime | None = None
    created_at: datetime
```

### `POST /contracts`

```python
class ContractCreate(BaseModel):
    contractor_id: int
    branch_id: int | None = 1  # RAO-P1-022: domyślnie Warszawa (id=1)
    salesperson_id: int | None = None
    contract_type: Literal["S", "U"] = "S"
    oid: str | None = None  # RAO-P2-058: Fakturownia OID (pusty = użyj number)
    delivery_address: str | None = Field(None, max_length=255)
    postal_code: str | None = None
    city: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    date_from: date | None = None
    date_to: date | None = None
    # RAO-P1-021/P2-033: total_value usunięte
    prepayment_amount: Decimal | None = None
    prepayment_document: str | None = None
    invoice_amount: Decimal | None = None
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
    contract_type: str,  # "S" lub "U"
    branch_id: int | None = None
) -> tuple[str, int]:
    """
    Generuje numer w formacie: S001/2026, S001/2026G (Gdańsk), U001/2026, U001/2026G
    1. Pobierz numerację startową z company
    2. Pobierz max(auto_number) z contracts
    3. Nowy auto_number = max(numeracja, max_auto) + 1
    4. Prefix = "S" dla najem, "U" dla usługa
    5. Jeśli branch_id wskazuje na oddział GDAŃSK (case-insensitive) → suffix = "G"
    6. Format: {prefix}{auto_number:03d}/{rok}{suffix}
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

    suffix = ""
    if branch_id:
        branch = await db.execute(select(Branch.name).where(Branch.id == branch_id))
        branch_name = branch.scalar_one_or_none()
        if branch_name and branch_name.upper() == "GDAŃSK":
            suffix = "G"

    return f"{prefix}{new_number:03d}/{year}{suffix}", new_number
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
    rate1: Decimal | None
    rate2: Decimal | None
    billing_label: str | None
    period_count: int | None  # RAO-P1-005: backward compatibility
    period_from: int | None  # RAO-P1-005: elastyczne widełki (od)
    period_to: int | None    # RAO-P1-005: elastyczne widełki (do)
    minimum: int | None
```

### `POST /contracts/{id}/positions/{pos_id}/conditions`

```python
class ConditionCreate(BaseModel):
    rate1: Decimal | None = Field(None, ge=0, decimal_places=2)
    rate2: Decimal | None = Field(None, ge=0, decimal_places=2)
    billing_label: str | None = Field(None, max_length=50)
    period_count: int | None = Field(None, ge=0)  # backward compatibility
    period_from: int | None = Field(None, ge=0)  # RAO-P1-005: elastyczne widełki (od)
    period_to: int | None = Field(None, ge=0)    # RAO-P1-005: elastyczne widełki (do)
    minimum: int | None = Field(None, ge=0)

    @model_validator(mode='after')
    def check_condition(self):
        # At least one rate must be provided
        if not (self.rate1 is not None or self.rate2 is not None):
            raise ValueError("Przynajmniej jedna stawka (rate1 lub rate2) jest wymagana.")
        if self.period_from is not None and self.period_to is not None and self.period_to <= self.period_from:
            raise ValueError("period_to musi być większe od period_from.")
        return self
```

### `PUT /contracts/{id}/value`

**Algorytm kalkulacji wartości umowy (RAO-P0-033):**
```python
async def recalculate_contract_value(db: AsyncSession, contract_id: int, user: User):
    """
    Algorytm kaskadowy (tiered) — identyczny z WinForms FormU4:
    1. Sprawdź ownership (branch_id) i status rozliczenia (allow read-only)
    2. Pobierz wszystkie pozycje umowy z załadowanymi warunkami
    3. Dla każdej pozycji posortuj warunki po period_count
    4. Przekaż quantity do calculate_position_value (mnożenie już wew.)
    5. rate2 („powyżej”) jest aktywny dla dni spoza period_to
    6. Suma = total (zwracana, total_value usunięte)
    """
    contract = await contract_service.verify_contract_access(db, contract_id, user)
    positions = await db.execute(
        select(ContractPosition)
        .options(selectinload(ContractPosition.conditions))
        .where(ContractPosition.contract_id == contract_id)
    )
    total = Decimal("0.00")
    for pos in positions.scalars():
        sorted_conds = sorted(
            pos.conditions,
            key=lambda c: (c.period_count is None, c.period_count or 0)
        )
        cond_dicts = [
            {
                "rate1": c.rate1,
                "rate2": c.rate2,
                "period_count": c.period_count,
                "minimum": c.minimum,
            }
            for c in sorted_conds
        ]
        pos_value = calculate_position_value(
            rental_days=pos.rental_days,
            billing_frequency=pos.billing_frequency,
            unit_price=pos.unit_price,
            quantity=pos.quantity or 1,
            conditions=cond_dicts,
        )
        total += pos_value
    return total
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

### `DELETE /contracts/positions/{position_id}/service-hours/{hour_id}` (RAO-P1-014) — USUNIĘTE (Faza 1b)

> **Faza 1b (RAO-P1-014):** Endpointy ewidencji godzin operatora (`GET/POST/PUT/DELETE /contracts/positions/{position_id}/service-hours[/{hour_id}]`) oraz schema `ServiceHourResponse/Create/Update` zostały usunięte z backendu. Klient wybrał formularz papierowy — tabela DB `service_hours` została DROPnięta (db-architect), a model/service/router/schemas usunięte w tej fazie. PDF protokołu usługi renderuje 5 pustych wierszy do ręcznego wypełnienia (fallback w `protocol_zo_u.html`).

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
    name: SafeName
    amount_from: Decimal | None = Field(None, ge=0, decimal_places=2)
    amount_to: Decimal | None = Field(None, ge=0, decimal_places=2)
    unit: SafeName | None = None
    description: SafeDescription = None  # RAO-P1-100: "Tekst na umowie"; pusty → auto name
    is_active: bool = True

    @model_validator(mode='after')
    def check_and_fill_description(self):
        if self.amount_from is not None and self.amount_to is not None and self.amount_to < self.amount_from:
            raise ValueError("amount_to nie może być mniejsze od amount_from.")
        # RAO-P1-100: KISS — "Tekst na umowie" zawsze wypełniony (fallback do nazwy)
        if not self.description or not self.description.strip():
            self.description = self.name
        return self

class ContractServiceFeeUpdate(BaseModel):
    """RAO-P0-034: Partial update — only fields explicitly sent are applied."""
    name: SafeName | None = None
    amount_from: Decimal | None = Field(None, ge=0, decimal_places=2)
    amount_to: Decimal | None = Field(None, ge=0, decimal_places=2)
    unit: SafeName | None = None
    description: SafeDescription = None
    is_active: bool | None = None

    @model_validator(mode='after')
    def check_amounts(self):
        if self.amount_from is not None and self.amount_to is not None and self.amount_to < self.amount_from:
            raise ValueError("amount_to nie może być mniejsze od amount_from.")
        return self

class ContractServiceFeeReorder(BaseModel):
    ids: list[int]
```

**Algorytm POST /contracts (tworzenie umowy):**
```python
# RAO-P1-100: Po zapisaniu umowy kopiuj DOMYŚLNY preset dla danego contract_type.
# Dla 'S' domyślnym jest "Najem — Wspólny"; dla 'U' — "Usługa — Wspólny".
async def copy_fee_templates_to_contract(
    db: AsyncSession, contract_id: int, contract_type: str
):
    # Prefer default preset for this contract type; fallback to all active templates
    default_group = await db.execute(
        select(FeePresetGroup)
        .where(FeePresetGroup.contract_type == contract_type)
        .where(FeePresetGroup.is_default == True)
    )
    group = default_group.scalar_one_or_none()
    if group:
        stmt = (
            select(ServiceFeeTemplate)
            .where(ServiceFeeTemplate.preset_id == group.id)
            .where(ServiceFeeTemplate.is_active == True)
            .order_by(ServiceFeeTemplate.sort_order)
        )
    else:
        stmt = (
            select(ServiceFeeTemplate)
            .where(ServiceFeeTemplate.contract_type == contract_type)
            .where(ServiceFeeTemplate.is_active == True)
            .order_by(ServiceFeeTemplate.sort_order)
        )
    templates = await db.execute(stmt)
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

**Algorytm POST /contracts/{id}/service-fees/apply-preset:**
- 404: umowa lub preset nie istnieje
- 409: umowa rozliczona (`is_settled=true`)
- `replace=true` (default): usuń istniejące `contract_service_fees`, wstaw szablony z grupy
- `replace=false`: dołącz szablony z grupy

**Algorytm POST /reset:** Usuwa wszystkie istniejące opłaty i kopiuje z domyślnego szablonu od nowa.

**Logika PDF (service.py):** Generuje tekst z aktywnych pozycji. KISS: `description` jest "Tekst na umowie" i drukowany bezpośrednio; fallback do kwoty/jednostki gdy `description` pusty. Kwoty formatowane polskimi separatorami (`1 200,00 zł`).
```python
def generate_fees_text(fees: list) -> str:
    lines = []
    for f in sorted(fees, key=lambda x: x.sort_order):
        if not f.is_active:
            continue
        desc = (f.description or "").strip()
        if desc:
            lines.append(f"- {f.name}: {desc}")
        else:
            amount_line = _build_fee_amount_line(f)
            if amount_line:
                lines.append(f"- {f.name}: {amount_line}")
            else:
                lines.append(f"- {f.name}")
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
### `DELETE /settlements/contract/{contract_id}/all` - P0-013
- Auth: Bearer JWT (operator)
- Bulk DELETE wszystkich wpisów `contract_settlements` dla `contract_id`
- Response 200: `{"message": "Usunięto N rozliczeń", "deleted_count": N}`
- Idempotentny: brak wpisów → `deleted_count: 0`, status 200
### `POST /settlements/contract/{contract_id}/init` - RAO-P1-012
### `POST /settlements/contract/{contract_id}/init-from-fakturownia` - RAO-P2-012

```python
class ContractSettlementResponse(BaseModel):
    id: int
    contract_id: int
    position_id: int | None = None
    service_fee_id: int | None = None  # RAO-P2-012
    service_fee_name: str | None = None  # RAO-P2-012: nazwa usługi dodatkowej dla UI (2026-05-21)
    cost_client: Decimal | None = None
    cost_company: Decimal | None = None
    margin: Decimal | None = None  # auto-calculated: cost_client - cost_company
    notes: str | None = None
    # RAO Faza 2a (opcja E): pola unmapped settlements z Fakturownia
    article_name_snapshot: str | None = None       # snapshot nazwy pozycji FA (gdy position_id=NULL)
    fakturownia_product_id: int | None = None       # ID produktu FA (grupowanie w analytics)
    fakturownia_invoice_number: str | None = None   # numer faktury FA (dla query)
    source: str | None = None                        # 'legacy' / 'fakturownia' / 'manual' / 'fa_unmapped'
    settled_at: date | None = None                   # data rozliczenia (z FA issue_date)
    created_at: datetime
    updated_at: datetime

class ContractSettlementCreate(BaseModel):
    contract_id: int
    position_id: int | None = None
    service_fee_id: int | None = None  # RAO-P2-012
    cost_client: Decimal | None = Field(None, ge=0)
    cost_company: Decimal | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)

class ContractSettlementUpdate(BaseModel):
    cost_client: Decimal | None = Field(None, ge=0)
    cost_company: Decimal | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)
```

**Logika:**
- GET /contract/{contract_id}: Zwraca wszystkie rozliczenia dla umowy (pozycje + usługi dodatkowe + unmapped)
- POST /contract/{contract_id}/init: Inicjalizuje rozliczenia z umowy - oblicza cost_client z pozycji umowy (unit_price * rental_days * quantity)
- POST /contract/{contract_id}/init-from-fakturownia: Inicjalizuje rozliczenia z Fakturownia - pobiera faktury z Fakturownia i mapuje:
  - Pozycje umowy przez fakturownia_product_id (1:N mapping) → settlement z `source='fakturownia'`, `settled_at=invoice.issue_date`
  - Usługi dodatkowe przez service_fee_templates.article_id → articles.fakturownia_product_id (1:N mapping)
  - **RAO Faza 2a (opcja E):** Pozycje FA nieobecne w umowie (brak mapowania) → settlement z `position_id=NULL`, `service_fee_id=NULL`, `source='fa_unmapped'`, `article_name_snapshot=<nazwa z FA>`, `fakturownia_product_id`, `fakturownia_invoice_number`, `settled_at=invoice.issue_date`. NIE tworzy artykułu on-the-fly — tylko snapshot nazwy. Idempotentność: UNIQUE(`unmapped_key`) chroni przed duplikatem (klucz = `unmapped:<pid>:<invoice_number>`).
  - Bug fix bonus (QA 1.7): mapped settlements dostają `source='fakturownia'` (nie domyślne `'manual'`) i `settled_at=invoice.issue_date`
- Auto-creowanie: Po utworzeniu umowy, automatycznie tworzy rekordy settlement dla wszystkich pozycji (cost_client/cost_company = NULL)
- Margin: Automatycznie obliczane jako cost_client - cost_company
- RAO-P2-012: service_fee_id pozwala na rozliczanie usług dodatkowych (contract_service_fees)

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

## RAO-P1-001 — Predefiniowane cenniki warunków rozliczenia maszyn

> Modele DB: `article_rate_presets` + `article_rate_preset_items` (per-maszyna,
> 1:N z items, snapshot copy do `position_conditions` przy apply).
> Mutacje wymagają `require_admin` (DELETE/PATCH set-default) lub `get_current_user` (GET).
> Apply-preset + last-conditions są w contracts/articles routerach.

### Schemas (Pydantic v2)

```python
class ArticleRatePresetItemCreate(BaseModel):
    rate_type_id: int | None = None
    description: str | None = Field(None, max_length=400)
    rate1: Decimal | None = None
    rate2: Decimal | None = None
    billing_label: str | None = Field(None, max_length=20)
    period_count: int | None = None
    minimum: int | None = None

class ArticleRatePresetItemUpdate(BaseModel):  # partial (exclude_unset)
    # te same pola, wszystkie opcjonalne

class ArticleRatePresetItemResponse(ArticleRatePresetItemCreate):
    id: int
    preset_id: int
    sort_order: int
    class Config: from_attributes = True

class ArticleRatePresetCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str | None = Field(None, max_length=400)
    is_default: bool = False
    items: list[ArticleRatePresetItemCreate] = []

class ArticleRatePresetUpdate(BaseModel):  # partial (exclude_unset)
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=400)
    is_default: bool | None = None

class ArticleRatePresetResponse(BaseModel):
    id: int
    article_id: int
    name: str
    description: str | None
    is_default: bool
    sort_order: int
    items: list[ArticleRatePresetItemResponse] = []
    class Config: from_attributes = True
```

### Endpointy — SETTINGS (prefix `/settings`)

| Method | Path | Auth | Status | Opis |
|--------|------|------|--------|------|
| GET    | `/settings/articles/{article_id}/rate-presets` | user | 200 | Lista cenników maszyny (z items, order by sort_order) |
| GET    | `/settings/articles/{article_id}/rate-presets/default` | user | 200 | Domyślny cennik maszyny (body=null jeśli brak) |
| POST   | `/settings/articles/{article_id}/rate-presets` | admin | 201 | Utwórz cennik (z items, set_default jeśli is_default) |
| GET    | `/settings/rate-presets/{preset_id}` | user | 200 \| 404 | Cennik z items |
| PUT    | `/settings/rate-presets/{preset_id}` | admin | 200 \| 404 | Edytuj cennik (partial update) |
| DELETE | `/settings/rate-presets/{preset_id}` | admin | 204 \| 404 | Usuń cennik (cascade items) |
| PATCH  | `/settings/rate-presets/{preset_id}/set-default` | admin | 200 \| 404 | Ustaw jako domyślny (atomowo unset innych) |
| POST   | `/settings/rate-presets/{preset_id}/items` | admin | 201 \| 404 | Dodaj warunek do cennika |
| PUT    | `/settings/rate-presets/items/{item_id}` | admin | 200 \| 404 | Edytuj warunek (partial) |
| DELETE | `/settings/rate-presets/items/{item_id}` | admin | 204 \| 404 | Usuń warunek |

**`set_default_preset` logika (atomowa transakcja):**
1. `UPDATE article_rate_presets SET is_default=0 WHERE article_id=:aid AND id<>:pid`
2. `UPDATE article_rate_presets SET is_default=1 WHERE id=:pid`

### Endpoint — CONTRACTS: apply preset do pozycji (snapshot)

```
POST /contracts/{contract_id}/positions/{pos_id}/conditions/apply-preset
Auth: user
Body: { preset_id: int, replace: bool = true }
Response 200: { applied_count: int, conditions: [ConditionResponse] }
  404: pozycja lub cennik nie istnieje
  409: umowa rozliczona (is_settled=true)
```

Logika `ContractService.apply_rate_preset_to_position`:
1. Guard: ownership (`branch_id`) + `contract.is_settled` → 409
2. If `replace`: `DELETE FROM position_conditions WHERE position_id=:pos_id`
3. Bulk copy: dla każdego `ArticleRatePresetItem` → `PositionCondition(position_id, **pola)`
4. Wylicz kaskadowo `period_from`/`period_to`:
   - rate1: [poprzedni `period_to` + 1, `period_count`]
   - rate2: [period_count + 1, następny `period_count` - 1] lub open-ended
5. `commit` + `refresh` + bump `contract.updated_at`
6. Brak FK z `PositionCondition` do cennika (snapshot — edycja cennika nie wpływa na umowy)

### Endpoint — ARTICLES: auto-prefill z ostatniej umowy

```
GET /articles/{article_id}/last-conditions
Auth: user
Response 200: {
  source_contract_number: str,
  source_contract_date: datetime | None,
  source_position_id: int,
  conditions: [ConditionResponse]
}
  404: brak historii umów dla tej maszyny
```

Logika `ContractService.get_last_conditions_for_article`:
- `SELECT ContractPosition JOIN Contract WHERE article_id=:aid ORDER BY Contract.created_at DESC LIMIT 1`
- Sprawdź ownership (`branch_id`) — IDOR guard.
- Zwraca warunki (`PositionCondition`) z tej pozycji + metadane umowy (number, created_at).
- Batch-fetch `RateType.name` (eliminacja N+1).

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
Filtr: domyślnie `is_archival=FALSE AND is_external=FALSE` (RAO-P1-027)

### `GET /stats/iddatiolal-f-ef-efees`
Query: `?date_from&date_to&internal_number=<str># (multi-value, opcjonalny)
- `category_sub2=<str>` — filtr sub2 (opcjonalny)
- `article_type=all|machine|service` (default: `all`) — filtr rodzaju

Response: `CategoryStatsResponse` (`date_from`  `total_revenue`, `items[]`)

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
---

### `GET /stats/expiring-contracts`

**Opis:** Umowy kończące się w ciągu N dni

**Query:** `?days=14` (opcjonalny, zakres 1-90, default=14)

**Response:** `list[ExpiringContractItem]`h 
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

### `GET /explorer/search` (RAO-P1-028: only non-archival articles)

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

**Opis:** Podsumowanie wynajmów po lokalizacji (RAO-P2-028/069).
- `group_by=city` (domyślnie, RAO-P2-069): 1 wiersz per miasto — sumuje wszystkie PNA
  w tym mieście. Warszawa (3978 PNA) → 1 wiersz. `postal_code=null`.
- `group_by=pna` (legacy RAO-P2-028): 1 wiersz per PNA — rozbicie miasta na kody pocztowe.
Rollup po `city`/`gmina`/`powiat`/`wojewodztwo` z LEFT JOIN do `postal_codes`.
NULL PNA → bucket `"(brak PNA)"`. Przychód ze `shared.revenue` (kaskadowy algorytm).
Helper: `shared.locations.aggregate_by_pna`.

**Query:** `?date_from=&date_to=&limit=50&group_by=city|pna`

**Response:** `{"locations": [{rank, city, postal_code, gmina, powiat, wojewodztwo, rentals_count, total_revenue}], "count": int, "group_by": "city"|"pna", "period": {...}}`
**HTTP:** 200 | 401

---

### `GET /explorer/services/{article_id}`

**Opis:** Szczegóły usługi: metryki, top kontrahenci (5), rozkład geograficzny (10 lokalizacji po PNA — RAO-P2-028).

**Query:** `?date_from=&date_to=`

**Response:** `{service: {id, name}, metrics: {times_billed, total_revenue}, top_contractors: [...], location_breakdown: [{city, postal_code, contract_count, total_revenue}]}`
**HTTP:** 200 | 401 | 404

---

### `GET /explorer/locations/{postal_code}`

**Opis:** Szczegóły lokalizacji — RAO-P2-028: drill-down po PNA (`postal_code`), NIE po mieście.
**BC break:** dawniej `/locations/{city}` (legacy regex `extract_city` — USUNIĘTE).
Bucket `"(brak PNA)"` oznacza umowy bez PNA (NULL/empty `postal_code`).
Top maszyny (10) i top kontrahenci (5) filtrowani po PNA. Przychód ze `shared.revenue`.

**Query:** `?date_from=&date_to=`

**Response:** `{postal_code, city, metrics: {contracts_count, unique_contractors, total_revenue, avg_revenue_per_contract}, top_machines: [...], top_contractors: [...], monthly_trend: []}`
**HTTP:** 200 | 401 | 404

---

### `GET /explorer/locations/city/{city}`

**Opis:** Szczegóły lokalizacji — RAO-P2-069: drill-down po mieście (sumuje wszystkie PNA).
Klik w wiersz miasta w trybie `group_by=city` wywołuje ten endpoint.
Zwraca `pna_breakdown` — rozbicie miasta na kody pocztowe (top PNA per rentals_count).
Top maszyny (10) i top kontrahenci (5) filtrowani po mieście (case-insensitive).

**Query:** `?date_from=&date_to=`

**Response:** `{city, postal_code: null, gmina, powiat, wojewodztwo, metrics: {contracts_count, unique_contractors, total_revenue, avg_revenue_per_contract, pna_count}, pna_breakdown: [{postal_code, rentals_count, total_revenue}], top_machines: [...], top_contractors: [...], monthly_trend: []}`
**HTTP:** 200 | 401 | 404

---

## ARCHIVE — Endpointy (RAO-P2-062 Faza 1)

> Moduł `backend/archive/` — read-only dostęp do danych historycznych
> (legacy umowy przeniesione z `contracts` do `archive_*` w Fazie 0).
>
> **Zasada:** archiwum = READ-ONLY z WYJĄTKIEM:
>   - `archive_categories` (CRUD — edycja kategorii archiwum)
>   - `archive_articles.category_id` (PATCH — przypisanie maszyny do kategorii)
>
> **Brak POST/PUT/DELETE** na umowach archiwum (read-only).
> Wszystkie endpointy wymagają auth (`get_current_user`).
> Write endpointy (POST/PUT/DELETE/PATCH) wymagają `require_admin`.
>
> **RAO-P2-062 Faza 1:** kolumna `contracts.is_legacy` USUNIĘTA —
> `contracts` zawiera tylko nowe umowy; legacy dane wyłącznie w `archive_*`.

### `GET /archive/contracts`

**Opis:** Lista umów archiwum z paginacją i filtrami.

**Query:** `?search=&contractor_id=<int>&date_from=&date_to=&contract_type=S|U&city=<str>&article_id=<int>&page=1&per_page=50`

**Filtry drill-down** (RAO-P2-062 Faza 3): `city` + `article_id` — używane przez drawer w statystykach (klik wiersz Top maszyny → `article_id`, klik wiersz Miasta → `city`).

**Response:** `PaginatedResponse[ArchiveContractListItem]` (bez `is_legacy`)
**HTTP:** 200 | 401

### `GET /archive/contracts/{contract_id}`

**Opis:** Szczegóły umowy archiwum z pozycjami, warunkami, opłatami i rozliczeniami.

**Response:** `ArchiveContractDetail` (positions[], service_fees[], settlements[])
**HTTP:** 200 | 401 | 404

### `GET /archive/articles`

**Query:** `?search=&category_id=<int>&page=1&per_page=50`
**Response:** `PaginatedResponse[ArchiveArticleResponse]`
**HTTP:** 200 | 401

### `GET /archive/articles/{article_id}`

**Response:** `ArchiveArticleResponse`
**HTTP:** 200 | 401 | 404

### `PATCH /archive/articles/{article_id}/category` (admin only)

**Opis:** Jedyny write na `archive_articles` — zmiana `category_id` (FK do `archive_categories`).

**Body:** `{"category_id": int | null}`

**Response:** `ArchiveArticleResponse`
**HTTP:** 200 | 401 | 403 | 404

### `GET /archive/categories`

**Response:** `list[ArchiveCategoryResponse]` (flat)
**HTTP:** 200 | 401

### `GET /archive/categories/tree`

**Response:** `list[ArchiveCategoryTreeNode]` (drzewo 3-poziomowe)
**HTTP:** 200 | 401

### `POST /archive/categories` (admin only)

**Body:** `ArchiveCategoryCreate` (`{name, code?, description?, parent_id?, level}`)
**Response:** `ArchiveCategoryResponse` (201)
**HTTP:** 201 | 401 | 403 | 409 (duplikat w hierarchii — case/diakrytyki-insensitive)

### `PUT /archive/categories/{cat_id}` (admin only)

**Body:** `ArchiveCategoryCreate`
**Response:** `ArchiveCategoryResponse`
**HTTP:** 200 | 401 | 403 | 404 | 409

### `DELETE /archive/categories/{cat_id}` (admin only)

**HTTP:** 204 | 401 | 403 | 404 | 409 (ma podkategorie / używana przez artykuły archiwum)

### `GET /archive/stats/summary`

**Query:** `?date_from=&date_to=`

**Response:** `ArchiveStatsSummary` (`{date_from, date_to, contracts_count, positions_count, revenue_estimate}`)
- `revenue_estimate` = SUM(unit_price × rental_days × quantity) per pozycja
  (fallback: kaskadowy `calculate_position_value` z `stats.calc` gdy brak `unit_price`)
**HTTP:** 200 | 401

### `GET /archive/stats/top-machines`

**Query:** `?date_from=&date_to=&limit=10` (max 50)
**Response:** `list[ArchiveTopMachineItem]` (`{article_id, article_name, internal_number, contracts_count, rented_days, revenue_estimate}`)
**HTTP:** 200 | 401

### `GET /archive/stats/by-category`

**Query:** `?date_from=&date_to=`
**Response:** `list[ArchiveCategoryStatItem]` (`{category_id, category_name, contracts_count, positions_count, revenue_estimate}`)
**HTTP:** 200 | 401

### `GET /archive/stats/machine-roi`

**Query:** `?article_id=<int>&date_from=&date_to=`
**Response:** `ArchiveMachineRoiResponse` (`{article_id, name, internal_number, replacement_value, revenue_estimate, contracts_count, rented_days, roi_pct}`)
- `roi_pct` = `revenue_estimate / replacement_value × 100` (null gdy brak `replacement_value`)
**HTTP:** 200 | 401 | 404

---

## Zmiany RAO-P2-062 Faza 1 — usunięcie `is_legacy`

- **`contracts.is_legacy`** — kolumna USUNIĘTA (idempotentny `ALTER TABLE contracts DROP COLUMN IF EXISTS is_legacy` w `main.py` startup).
- **`shared/revenue.py`** — parametr `is_legacy` usunięty z `compute_position_revenues`; dict wynikowy nie zawiera klucza `is_legacy`. `revenue_source` = tylko `actual` / `estimate_lookup` / `estimate_tiered`.
- **`stats/router.py`** — 9 endpointów (fleet-summary, top-machines, additional-fees, locations, by-category, by-period, positions, + unfiltered w positions) nie przyjmuje już parametru `is_legacy`. Wariant `"mieszane"` w `revenue_source_label` usunięty (archiwum osobno).
- **Statystyki historyczne** — obsługiwane przez moduł `archive` (osobne endpointy `/archive/stats/*`), NIE przez filter `is_legacy` na `contracts`.

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

### Contract Access Control (RAO-P0-049)

```python
async def verify_contract_access(
    db: AsyncSession,
    contract_id: int,
    user: User,
    allow_mutation: bool = False,
) -> Contract:
    """
    IDOR guard for all contract-scoped resources.
    - admin: full access (still blocked if allow_mutation and contract.is_settled)
    - user/viewer: see only contracts where branch_id equals user's branch_id
                   (or NULL branch_id for legacy data)
    - viewer: cannot mutate even with ownership
    - settled contracts: mutation is blocked for all roles
    Returns the contract (or raises 404/403/409).
    """
```

Every `/contracts/{contract_id}/...` endpoint and `/articles/{id}/last-conditions`
uses `verify_contract_access` to enforce ownership.

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
