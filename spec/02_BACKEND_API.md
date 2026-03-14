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
    owner_name: str | None             # JOIN contractors
    notes: str | None
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
```

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
    description: str | None = None
    delivery_address: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    total_value: Decimal = Decimal("0.00")
    prepayment_amount: Decimal = Decimal("0.00")
    prepayment_document: str | None = None
    invoice_amount: Decimal = Decimal("0.00")
    invoice_document: str | None = None
    notes: str | None = None
    additional_fees_text: str | None = None
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
    contract_rental_text: str | None
    contract_service_text: str | None
```

### `GET /settings/fees`
### `PUT /settings/fees`

```python
class FeeResponse(BaseModel):
    id: int
    fee_type: str
    is_active: bool
    amount_from: Decimal | None
    amount_to: Decimal | None
    description: str | None

class FeeUpdate(BaseModel):
    fees: list[FeeItem]

class FeeItem(BaseModel):
    fee_type: Literal[
        "refueling", "transport", "cleaning1", "cleaning2", "excess_downtime"
    ]
    is_active: bool
    amount_from: Decimal | None = None
    amount_to: Decimal | None = None
    description: str | None = None
```

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

### `GET /settings/categories`
### `POST /settings/categories`

```python
class CategoryResponse(BaseModel):
    id: int
    name: str
    code: str | None
    description: str | None
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

### `POST /reports/contract/{id}`

```python
# Query: ?type=contract|protocol_zo|protocol_zo_nodata

class ReportResponse(BaseModel):
    file_url: str       # URL to download PDF
    generated_at: datetime
```

**Algorytm:**
1. Pobierz dane umowy z pozycjami i warunkami
2. Render Jinja2 HTML template
3. WeasyPrint → PDF
4. Zapisz w `report_folder`
5. Zwróć URL do pobrania

### `GET /reports/summary/contractors`
### `GET /reports/summary/machines`

Raporty zbiorczych — generują PDF z danymi zagregowanymi.

### `GET /stats/machine-roi` (Nowość)
### `GET /stats/currently-rented` (Nowość)
### `GET /stats/additional-fees` (Nowość)
### `GET /stats/locations` (Nowość)

> Pełna specyfikacja raportów z obrazkami i endpointów statystyk znajduje się w pliku **[11_REPORTS_AND_STATS.md](./11_REPORTS_AND_STATS.md)**.

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
