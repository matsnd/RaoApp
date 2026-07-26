# JWT Auth & E2E Testing Pattern

## Opis
Wzorzec do obsługi JWT autoryzacji i testów E2E w RAO.

## Reset hasła admina

### Skrypt
```bash
cd spec/technical/scripts
python reset_admin_password.py
```

### Implementacja
```python
import asyncio
import bcrypt
from database import AsyncSessionLocal
from sqlalchemy import select, update
from auth.models import User

async def reset_admin_password():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.login == "admin"))
        user = result.scalar_one_or_none()

        if not user:
            print("Nie znaleziono użytkownika 'admin'")
            return

        new_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()

        await db.execute(
            update(User).where(User.id == user.id).values(
                password=new_hash,
                must_change_password=False,
            )
        )
        await db.commit()

        print(f"Hasło dla użytkownika 'admin' (ID: {user.id}) zostało zmienione na 'admin123'")
```

## Uzyskanie JWT tokenu

### Endpoint
```
POST /rao/api/auth/login
Content-Type: application/json

{
  "login": "admin",
  "password": "admin123"
}
```

### Odpowiedź
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Użycie w curl
```bash
curl -X POST http://localhost:8000/rao/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "admin123"}'
```

### Użycie w requests
```python
import requests

response = requests.post(
    "http://localhost:8000/rao/api/auth/login",
    json={"login": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Użycie w kolejnych requestach
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/rao/api/contracts", headers=headers)
```

## Smoke test E2E

### Playwright test
```typescript
// e2e/tests/01-login.spec.ts
test('smoke login', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await page.fill('input[name="login"]', 'admin')
  await page.fill('input[name="password"]', 'admin123')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('http://localhost:5173/dashboard')
})
```

### Uruchomienie
```bash
cd e2e
npx playwright test tests/01-login.spec.ts
```

## Użycie w RAO

### Development
- Reset hasła admina przed testami
- Uzyskanie tokenu do manualnego testowania API
- Weryfikacja endpointów przez curl

### Testing
- Smoke test po każdej zmianie kodu
- Regresja przed merge
- Weryfikacja JWT flow

### CI/CD
- Automatyczny reset hasła w środowisku testowym
- Token do automatycznych testów API
- E2E tests w pipeline

## Powiązane
- Script: `scripts/reset_admin_password.py`
- Script: `scripts/check_admin.py`
- Model: `backend/auth/models.py::User`
- Router: `backend/auth/router.py`
- E2E: `e2e/tests/01-login.spec.ts`

## Wymagania
- Backend musi działać na porcie 8000 (lub innym)
- Frontend musi działać na porcie 5173 (lub innym)
- Użytkownik admin musi istnieć w bazie
- Biblioteki: bcrypt, sqlalchemy, playwright