# NEW_DB_CONFIG — Konfiguracja połączenia do nowej bazy danych

> **UWAGA:** Wypełnij poniższe dane przed rozpoczęciem budowy aplikacji.

```env
# === NOWA BAZA (rao_new) ===
NEW_DB_HOST=localhost
NEW_DB_PORT=3306
NEW_DB_USER=rao_user
NEW_DB_PASSWORD=<<DB_PASSWORD_PLACEHOLDER>>
NEW_DB_NAME=rao_new
NEW_DB_ROOT_PASSWORD=USOjtYTpJaxyhT2q5PnI

# URL dla SQLAlchemy
RAO_DATABASE_URL=mariadb+asyncmy://rao_user:<<DB_PASSWORD_PLACEHOLDER>>@localhost:3306/rao_new
```

### Jak uruchomić bazę:

```bash
# Utwórz bazę i użytkownika
mariadb -u root -p$NEW_DB_ROOT_PASSWORD -e "
CREATE DATABASE IF NOT EXISTS rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;
CREATE USER IF NOT EXISTS 'rao_user'@'localhost' IDENTIFIED BY '<<DB_PASSWORD_PLACEHOLDER>>';
GRANT ALL PRIVILEGES ON rao_new.* TO 'rao_user'@'localhost';
FLUSH PRIVILEGES;
"

# Wykonaj DDL z 01_DATABASE_DDL.md
mariadb -u rao_user -p<<DB_PASSWORD_PLACEHOLDER>> rao_new < spec/01_DATABASE_DDL.md
```
