# Paczka wdrozeniowa RAO — 2026-07-21 23:05

## Zawartosc

deployment/
├── backend/              ← wgraj do /home/ts123/rao_backend/ (nadpisz istniejace)
│   ├── main.py
│   ├── wsgi.py / passenger_wsgi.py   ← entry point WSGI (Passenger)
│   ├── config.py
│   ├── database.py
│   ├── requirements-prod.txt  ← ZMIEN NAZWE na requirements.txt na serwerze!
│   ├── requirements.txt       ← (dev, nie uzywaj na prod)
│   ├── .env.prod              ← WZORZEC — nie wgrywaj, utworz .env na serwerze
│   ├── auth/, contractors/, contracts/, machines/, services/
│   ├── additional_services/, archive/, reports/ (szablony PDF + fonts)
│   ├── reservations/, settings/, settlements/, stats/, integrations/
│   └── shared/, categories/, deliveries/, explorer/
├── frontend/             ← wgraj do /home/ts123/public_html/rao/ (nadpisz istniejace)
│   ├── index.html
│   ├── .htaccess         ← SPA fallback + wykluczenie /rao/api
│   └── assets/           ← zbudowany dist (vue-tsc + vite build)
├── database/             ← (pusty — brak zmian schema w tej paczce)
├── CHANGELOG_2026-07-21.txt   ← lista zmian
├── EMAIL_Klient_2026-07-21.txt ← gotowy email do klienta
└── README_DEPLOY.txt     ← ten plik

## ZMIANY SCHEMA DB W TEJ PACZCE (automatyczne przy starcie backendu)

Wszystkie migracje sa idempotentne (ALTER ... IF NOT EXISTS) i wykonuja sie
automatycznie w `main.py` startup przy restarcie backendu. NIE trzeba
wykonywac recznych SQL-i.

### 1. contracts.notes → notes_contract + notes_protocol (commit 44c3773, P1-202)
- `ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_contract TEXT NULL`
- `ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_protocol TEXT NULL`
- BACKFILL: `UPDATE contracts SET notes_protocol = notes WHERE notes IS NOT NULL AND notes_protocol IS NULL`
- `ALTER TABLE contracts DROP COLUMN notes` (idempotentne — sprawdza information_schema)

### 2. Tabela deliveries (commit b64775a, P1-205)
- Tabela `deliveries` zostala utworzona na prod przy wgraniu paczki
  20260720 (model byl importowany w main.py, `Base.metadata.create_all`).
- W tej paczce dodany router/service/schemas — modul staje sie aktywny w API.
- Brak dodatkowych zmian schema dla deliveries.

### Weryfikacja schema po wdrozeniu
Po restarcie backendu sprawdz:
```sql
DESCRIBE contracts;          -- powinno miec notes_contract, notes_protocol, bez notes
SELECT COUNT(*) FROM deliveries;  -- tabela istnieje (moze byc pusta — kalendarz czyta contracts)
```

## CO ZMIENILO SIE W TEJ PACZCE

### 1. GUS — naprawione pobieranie danych kontrahenta po NIP (commit a1b2f5b)
- Root cause: zly namespace w SOAP body (`http://CIS/BIR/2014/07/DataContract`
  zamiast `http://CIS/BIR/PUBL/2014/07/DataContract`). GUS ignorowal NIP
  i zwracal pusty wynik → ErrorCode 4 "Nie znaleziono wpisu".
- Po naprawie: wpisuje NIP → klika GUS → auto-uzupelnia:
  nazwa, REGON, ulica + nr budynku + nr lokalu (np. "ul. Kłobucka 6B/103"),
  kod pocztowy, miasto, wojewodztwo, powiat, gmina.
- Toast success przy pobraniu, toast warning gdy GUS nie znajdzie NIP.
- Weryfikacja: T-Mobile (5261040567) i Toolsmart (9512598092) — oba dzialaja.

### 2. Dostawy — pozycje umowy w drawerze jak w PDF (commit 9a1936f)
- W drawerze dostawy sekcja "Pozycje umowy" pokazuje tabelke 4-kolumnowa:
  | Przedmiot najmu | Dni | Wartosc odtw. | Rozliczenie |
- Navy naglowek, zebra striping, border-radius, tooltip na hover.
- Nazwa maszyny + nr wewnetrzny (LAD-004), wartosc z separatorem tysiecy
  ("950 000,00 zł"), progi rozliczenia w osobnych liniach:
  "1 - 3 dni - 1560,00 zł / doba", "powyzej 16 dni - 1040,00 zł / doba".
- Format zgodny z PDF umowy.

### 3. Umowy — enrichment contract detail (commit b2c048e, z poprzedniej paczki)
- GET/POST/PUT/PATCH /contracts/{id} zwraca contractor_name i salesperson_name
  (zamiast null/ID). Drawer Dostaw i inne widoki pokazuja nazwe kontrahenta
  i handlowca zamiast pustych pol.

## KROKI WDROZENIA

### 1. Backend
1. Wgraj zawartosc backend/ do /home/ts123/rao_backend/ (nadpisz istniejace)
2. ZMIEN NAZWE: requirements-prod.txt → requirements.txt
3. Sprawdz .env na serwerze — MUSI zawierac:
   - RAO_GUS_API_KEY=d4feaf84608747c1addd  (klucz GUS, ten sam co w starej aplikacji)
   - pozostale ustawienia jak w .env.prod (wzorzec)
4. W panelu: Setup Python App → Run pip install (lub przez SSH:
   `cd /home/ts123/rao_backend && pip install -r requirements.txt`)
5. Restart aplikacji w panelu
6. Sprawdz: curl https://www.toolsmart.pl/rao/api/health → {"status":"ok"}

### 2. Frontend
1. Wgraj zawartosc frontend/ do /home/ts123/public_html/rao/ (nadpisz istniejace)
2. Sprawdz: https://www.toolsmart.pl/rao/ → strona logowania

### 3. Weryfikacja po wdrozeniu
- Login: admin / admin123
- **GUS:** Kontrahenci → Nowy → NIP "5261040567" → guzik GUS
  → pola uzupelnione: "T-MOBILE POLSKA SPÓŁKA AKCYJNA",
  ul. Marynarska 12, 02-674 Warszawa, REGON 011417295
- **GUS z lokalem:** NIP "9512598092" → guzik GUS
  → "TOOLSMART SP. Z O.O.", ul. Kłobucka 6B/103, 02-699 Warszawa
- **Dostawy:** Dostawy → kropka w kalendarzu → dostawa w panelu dnia
  → drawer → sekcja "Pozycje umowy" → tabelka 4-kolumnowa z navy naglowkiem
- **Drawer kontrahent/handlowiec:** drawer Dostaw pokazuje nazwe kontrahenta
  i handlowca (nie null/ID)

## UWAGI
- Migracje schema DB wykonuja sie AUTOMATYCZNIE przy restarcie backendu
  (idempotentne ALTER IF NOT EXISTS w main.py startup). Po wgraniu plikow
  i restarcie sprawdz DESCRIBE contracts (notes_contract + notes_protocol,
  brak notes).
- pypdf (z poprzedniej paczki) nadal wymagany — bez tego protokoly
  multi-maszyna beda ucinane.
- Nie wgrywaj .env z lokalnej maszyny — utworz/utrzymaj .env na serwerze
  z produkcyjnymi danymi (DB, JWT, GUS, SMTP, Fakturownia).
- Klucz GUS (`RAO_GUS_API_KEY`) jest ten sam co w starej aplikacji
  WinForms — nie trzeba generowac nowego.

## ROLLBACK
- W razie problemow: przywroc poprzednia paczke z `rao_deploy_20260720_083500.zip`
  lub z backupu na serwerze.
- Commity do revertu: a1b2f5b (GUS), 9a1936f (deliveries drawer), b2c048e (enrich)
