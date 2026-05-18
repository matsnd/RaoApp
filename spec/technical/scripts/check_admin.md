# check_admin.py

## Opis
Skrypt do weryfikacji istnienia użytkownika admin w bazie danych. Używany podczas developmentu i testów.

## Użycie

```bash
cd spec/technical/scripts
python check_admin.py
```

## Wymagania
- Backend musi być skonfigurowany (`.env` z DB connection)
- Tabela `user` musi istnieć w bazie

## Działanie
1. Łączy się z bazą danych przez `AsyncSessionLocal`
2. Szuka użytkownika z loginem `admin`
3. Wyświetla informacje o użytkowniku

## Wynik
```
Admin exists: True
ID: 1, Login: admin, Role: admin
```

Lub:
```
Admin exists: False
No admin user found in database
```

## Użycie w RAO
- Development — weryfikacja czy admin został utworzony
- Testing — sprawdzenie przed testami E2E
- Debugging — diagnoza problemów z logowaniem

## Powiązane
- Script: `reset_admin_password.py`
- Model: `backend/auth/models.py::User`
- Endpoint: `POST /rao/api/auth/login`