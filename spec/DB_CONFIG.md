# DB_CONFIG — Konfiguracja połączenia do starej bazy danych

> **UWAGA:** Wypełnij poniższe dane przed rozpoczęciem budowy aplikacji.

```env
# === STARA BAZA (do weryfikacji) ===
OLD_DB_HOST=localhost
OLD_DB_PORT=3306
OLD_DB_USER=
OLD_DB_PASSWORD=
OLD_DB_NAME=rao
```

### Jak zdobyć credentials:

1. Sprawdź w `c:\projects\repos\AppRao\rao\App.config` — klucz `OdbcDsn`
2. LUB sprawdź w MariaDB konfigurację użytkownika `rao`
3. LUB zapytaj administratora bazy danych

### Do czego używać:

- Weryfikacja danych ze starej aplikacji
- Sprawdzanie starych VIEW i tabel
- Porównywanie wyników nowych endpointów ze starym systemem
