# reset_admin_password.py

## Opis
Skrypt do resetowania hasła użytkownika admin na `admin123`. Używany podczas testów E2E i developmentu.

## Użycie

```bash
cd spec/technical/scripts
python reset_admin_password.py
```

## Wymagania
- Backend musi być skonfigurowany (`.env` z DB connection)
- Biblioteki: `bcrypt`, `sqlalchemy`, `asyncmy`

## Działanie
1. Łączy się z bazą danych przez `AsyncSessionLocal`
2. Znajduje użytkownika `admin`
3. Hashuje nowe hasło `admin123` używając bcrypt
4. Aktualizuje hasło w bazie i ustawia `must_change_password=False`

## Wynik
```
Hasło dla użytkownika 'admin' (ID: 1) zostało zmienione na 'admin123'
```

## Użycie w RAO
- Testy E2E — reset hasła przed testami
- Development — szybki reset gdy hasło jest nieznane
- JWT Auth — uzyskanie tokenu przez POST `/rao/api/auth/login`

## Powiązane
- Pattern: `spec/technical/patterns/jwt_auth_e2e.md`
- AGENTS.md: sekcja "JWT Auth i testy E2E"