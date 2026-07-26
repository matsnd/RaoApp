# 24 — Export danych do ujednolicenia (mapowanie kolumn → DB)

**Data:** 2026-04-22
**Status:** Plik wygenerowany — `temp/Export_do_ujednolicenia.xlsx`
**Skrypt:** `spec/technical/scripts/export_to_unify.py`
**Audyt ekipą:** Tech Lead / DB Architect / Backend / QA / Product Owner

---

## 1. Cel biznesowy

Klient (Toolsmart) będzie porządkować słowniki systemu:
- **ujednolicać nazewnictwo** artykułów (np. „Usługa ładowarką obrotową" → „Usługa ładowarką teleskopową obrotową")
- **uzupełniać brakujące metadane** (numery wewnętrzne, rejestracyjne, seryjne, marki, modele, kategorie, e-maile kontrahentów)
- **reorganizować kategorie** (płaska struktura → hierarchia)
- **czyścić śmieci** (np. `id=8065 "test usługi"`, 69 artykułów nieużywanych w żadnej umowie)

Zakres: **słowniki referencyjne**, nie dane transakcyjne (umów, pozycji, warunków nie eksportujemy).

---

## 2. Diagnoza braków (baza lokalna `rao_new` po migracji 2026-04-22)

### Artykuły (`articles`, 397 rekordów)

| Pole | Braki | % |
|---|---|---|
| `internal_number` | **397** | **100%** |
| `registration_no` | **397** | **100%** |
| `description` | **397** | **100%** |
| `brand` | 386 | 97% |
| `model` | 390 | 98% |
| `serial_no` | 390 | 98% |
| `category_id` | 0 | 0% |
| `replacement_value` | 0 | 0% |

**69 artykułów** nigdy nie użytych w `contract_positions` — kandydaci do usunięcia.

### Kontrahenci (`contractors`, 581 rekordów)

| Pole | Braki | % |
|---|---|---|
| `email` | **567** | **98%** |
| `phone1` | 348 | 60% |
| `street` | 51 | 9% |
| `city` | 31 | 5% |
| `nip` | 8 | 1% |
| `is_supplier=1` | **0** | **0%** (wszyscy to najemcy — dostawców brak w systemie!) |

### Kategorie (`categories`, 22 rekordy)

Model **płaski**: `id, name, code, description`. Klient sygnalizuje w `Arkusz1` potrzebę hierarchii 3-poziomowej:

```
Właściwa kategoria główna → Kategoria II → Kategoria III
(Podnośniki Nożycowe)     → (Elektryczne) → (...)
```

⚠ **Wymaga zmiany schematu DB** (dodanie `parent_id`, może `level`) — nie rozwiązuje tego ten eksport.

---

## 3. Struktura pliku `Export_do_ujednolicenia.xlsx`

Plik jest kopią `Asortyment - Produkty - Maszyny - Toolsmart.xlsx` (oryginał klienta nietknięty) + 11 nowych arkuszy.

| # | Arkusz | Tabela DB | Wierszy | Komentarz |
|---|---|---|---|---|
| 0 | `00_Instrukcja` | — | — | Legenda, konwencje, spis treści |
| — | `Arkusz1` | — | 268 | Oryginalny arkusz klienta (nieruszany) |
| 1 | `01_Artykuly` | `articles` | 397 | Główny słownik do ujednolicenia |
| 2 | `02_Kategorie` | `categories` | 22 | Do reorganizacji |
| 3 | `03_Kontrahenci` | `contractors` | 581 | Uzupełnienie e-maili, telefonów |
| 4 | `04_Adresy_dostawy` | `contractor_addresses` | 280 | Magazyny, place budowy |
| 5 | `05_Oddzialy` | `branches` | 2 | Oddziały własnej firmy |
| 6 | `06_Handlowcy` | `salespeople` | 3 | Wystawcy umów |
| 7 | `07_Typy_stawek` | `rate_types` | 3 | Dobowa/godzinowa/… |
| 8 | `08_Presety_oplat` | `fee_preset_groups` | 2 | Grupy presetów |
| 9 | `09_Szablony_oplat` | `service_fee_templates` | 10 | Wzorce opłat serwisowych |
| 10 | `10_Firma` | `company` | 1 | Nagłówek dokumentów |

**Pominięte (dane transakcyjne / wrażliwe):** `contracts`, `contract_positions`, `position_conditions`, `contract_service_fees`, `users`.

---

## 4. Konwencje w każdym arkuszu

Każdy arkusz ma strukturę:

```
Rząd 1   : tytuł arkusza (scalony, ciemny)
Rząd 2-N : legenda specyficzna dla tego arkusza (żółty)
Rząd 5-6 : nagłówek kolumn (granat, biały font, zamrożony)
Rząd 6+  : dane
```

### Kolumny systemowe (w każdym arkuszu)

| Kolumna | Rola | Kolor |
|---|---|---|
| `ID (nie zmieniac)` | Klucz główny DB. **Nie dotykać** dla UPDATE/DELETE. Puste dla NEW. | szary |
| `Akcja` | Dropdown: `(puste)` / `UPDATE` / `DELETE` / `NEW` | żółty |
| … kolumny danych … | Do edycji | biały |
| (statystyki — `usage_count`, `contract_count`, `created_at`) | **Tylko do odczytu** | zielony |
| `Uwagi klienta` | Komentarz tekstowy dla dewelopera | biały |

### Semantyka `Akcja`

| Wartość | Znaczenie przy imporcie |
|---|---|
| (puste) | Wiersz ignorowany |
| `UPDATE` | `UPDATE WHERE id=<ID>` wg wpisanych wartości (tylko zmienione) |
| `DELETE` | `DELETE WHERE id=<ID>` — wymaga sprawdzenia FK (pozycje umów itp.) |
| `NEW` | `INSERT` z pustym ID → autoincrement; wszystkie wymagane pola muszą być wypełnione |

### Typy danych

- **Boolean:** `1` lub `0` (nie TRUE/FALSE, nie tak/nie)
- **Decimal/kwota:** liczby z kropką, bez waluty (`1234.56`)
- **Data:** `YYYY-MM-DD`
- **Referencja FK:** ID liczbowe z odpowiedniego arkusza (np. `ID kategorii` → arkusz `02_Kategorie`)

---

## 5. Mapowanie kolumn → DB

### 5.1. `01_Artykuly` → `articles`

| Kolumna Excel | Pole DB | Typ | Uwagi |
|---|---|---|---|
| ID (nie zmieniac) | `id` | INT | PK |
| Akcja | — | enum | (`UPDATE`/`DELETE`/`NEW`) |
| Nazwa | `name` | VARCHAR(200) | NOT NULL |
| Rodzaj (artykul/usluga) | `is_service` | BOOL | `"usluga"` → 1, `"artykul"` → 0 |
| Numer wewnetrzny | `internal_number` | VARCHAR(50) | nullable, klient będzie uzupełniał |
| Numer rejestracyjny | `registration_no` | VARCHAR(40) | nullable |
| Numer seryjny | `serial_no` | VARCHAR(40) | nullable |
| Marka | `brand` | VARCHAR(100) | nullable |
| Model | `model` | VARCHAR(100) | nullable |
| Wartosc odtworzeniowa (PLN) | `replacement_value` | DECIMAL(18,2) | do wyliczania szkód |
| Kategoria | `categories.name` | — | tylko pokaz (JOIN) |
| ID kategorii | `category_id` | INT FK | → `categories.id` |
| Wlasciciel | `contractors.name` | — | tylko pokaz (JOIN) |
| ID wlasciciela | `owner_id` | INT FK | → `contractors.id` (nullable) |
| Oddzial | `branches.name` | — | tylko pokaz (JOIN) |
| ID oddzialu | `branch_id` | INT FK | → `branches.id` |
| Opis | `description` | VARCHAR(400) | nullable |
| Notatki wewnetrzne | `notes` | VARCHAR(200) | nullable |
| Domyslna liczba dni wynajmu | `rental_days` | INT | używane do wycen |
| Typ artykulu (tag) | `article_type` | VARCHAR(20) | swobodny tag |
| **Ile razy uzyty w umowach** | *(wyliczane)* | — | **read-only** statystyka |
| **Data utworzenia** | `created_at` | DATE | **read-only** |
| Uwagi klienta | — | — | komentarz dla dewelopera (nie zapisywane) |

### 5.2. `02_Kategorie` → `categories`

| Kolumna Excel | Pole DB | Typ |
|---|---|---|
| ID (nie zmieniac) | `id` | INT PK |
| Akcja | — | enum |
| Nazwa kategorii | `name` | VARCHAR(200) NOT NULL |
| Kod (skrot) | `code` | VARCHAR(40) |
| Opis | `description` | VARCHAR(400) |
| **Liczba artykulow** | *(wyliczane)* | read-only statystyka |
| Uwagi klienta | — | — |

### 5.3. `03_Kontrahenci` → `contractors`

| Kolumna Excel | Pole DB | Typ |
|---|---|---|
| ID (nie zmieniac) | `id` | INT PK |
| Akcja | — | enum |
| Nazwa pelna | `name` | VARCHAR(400) NOT NULL |
| Nazwa skrocona | `name_short` | VARCHAR(200) |
| NIP | `nip` | VARCHAR(20) |
| REGON | `regon` | VARCHAR(20) |
| PESEL | `pesel` | VARCHAR(20) |
| Kod pocztowy | `postal_code` | VARCHAR(20) |
| Miejscowosc | `city` | VARCHAR(50) |
| Ulica | `street` | VARCHAR(50) |
| Lokal | `unit` | VARCHAR(50) |
| E-mail | `email` | VARCHAR(100) |
| Osoba kontaktowa 1 | `contact_person1` | VARCHAR(100) |
| Telefon 1 | `phone1` | VARCHAR(100) |
| Osoba kontaktowa 2 | `contact_person2` | VARCHAR(100) |
| Telefon 2 | `phone2` | VARCHAR(100) |
| Telefon stacjonarny | `landline_phone` | VARCHAR(20) |
| Strona WWW | `website` | VARCHAR(100) |
| Czy dostawca (1/0) | `is_supplier` | BOOL |
| Notatki | `notes` | TEXT |
| **Liczba umow** | *(wyliczane)* | read-only |
| **Data utworzenia** | `created_at` | DATE read-only |
| Uwagi klienta | — | — |

### 5.4. `04_Adresy_dostawy` → `contractor_addresses`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| ID kontrahenta | `contractor_id` FK → `contractors.id` |
| Kontrahent (nazwa) | JOIN — read-only |
| Opis adresu | `name` |
| Kraj | `country_code` (domyślnie `PL`) |
| Kod pocztowy | `postal_code` |
| Miejscowosc | `city` |
| Ulica | `street` |
| Osoba kontaktowa | `contact_person` |
| Telefon | `phone` |
| E-mail | `email` |
| Adres domyslny dostawy (1/0) | `is_default_delivery` |
| Siedziba firmy (1/0) | `is_headquarters` |
| Szerokosc geograf. | `latitude` DECIMAL(10,7) |
| Dlugosc geograf. | `longitude` DECIMAL(10,7) |
| Notatki | `notes` |
| Data utworzenia | `created_at` read-only |
| Uwagi klienta | — |

### 5.5. `05_Oddzialy` → `branches`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| Nazwa oddzialu | `name` NOT NULL |
| Adres (jedno pole) | `address` |
| Kod pocztowy | `postal_code` |
| Miejscowosc | `city` |
| Ulica | `street` |
| Data utworzenia | `created_at` read-only |

### 5.6. `06_Handlowcy` → `salespeople`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| Imie i nazwisko | `name` NOT NULL |
| Telefon | `phone` |
| Aktywny (1/0) | `is_active` |
| Prowizja (%) | `commission_rate` DECIMAL(5,2) |

### 5.7. `07_Typy_stawek` → `rate_types`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| Nazwa | `name` NOT NULL |
| Opis | `description` |
| Zalezny od pogody/innych (1/0) | `is_dependent` |

### 5.8. `08_Presety_oplat` → `fee_preset_groups`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| Nazwa presetu | `name` NOT NULL |
| Typ umowy (S/U) | `contract_type` CHAR(1) |
| Opis | `description` |
| Domyslny (1/0) | `is_default` |
| Kolejnosc | `sort_order` |
| **Liczba szablonow** | *(wyliczane)* read-only |

### 5.9. `09_Szablony_oplat` → `service_fee_templates`

| Kolumna Excel | Pole DB |
|---|---|
| ID (nie zmieniac) | `id` |
| Akcja | — |
| ID presetu | `preset_id` FK → `fee_preset_groups.id` |
| Preset (nazwa) | JOIN — read-only |
| Typ umowy (S/U) | `contract_type` |
| Kolejnosc | `sort_order` |
| Nazwa oplaty | `name` NOT NULL |
| Kwota od (PLN) | `amount_from` DECIMAL(18,2) |
| Kwota do (PLN) | `amount_to` DECIMAL(18,2) |
| Jednostka | `unit` |
| Opis | `description` |
| Aktywny (1/0) | `is_active` |

### 5.10. `10_Firma` → `company`

Wszystkie pola 1:1. Jedyny wiersz — `id=1`.

---

## 6. Scenariusz re-importu (TODO — nie wdrożone)

Po edycji przez klienta potrzebny będzie **skrypt importera** (`backend/import_from_unify.py`):

```python
for sheet in SHEETS:
    rows = load_sheet(wb, sheet.name)
    for row in rows:
        action = row["Akcja"].strip().upper()
        if action == "UPDATE":
            update_by_id(sheet.table, row["ID"], mapped_fields(row))
        elif action == "DELETE":
            soft_or_hard_delete(sheet.table, row["ID"])
        elif action == "NEW":
            insert(sheet.table, mapped_fields(row, exclude=["ID"]))
```

Wymagania importera:
- **Walidacja integralności:** sprawdź FK przed DELETE (nie wywalaj kategorii jeśli artykuły ją używają bez przepisania)
- **Transakcja:** wszystko w jednym `BEGIN/COMMIT` z rollback przy błędzie w dowolnym wierszu
- **Dry-run mode:** `--dry-run` pokazuje co się zmieni bez zapisu
- **Backup:** automatyczny `mysqldump` przed importem
- **Report:** po imporcie plik `import_report.xlsx` z listą zmian (OK / ERROR / WARN)

---

## 7. Audyt ekipą

**🏗️ Tech Lead** — OK. Źródłem prawdy pozostaje DB, Excel to tylko interfejs edycji. ID zachowane → round-trip bezpieczny. Osobne arkusze = modularne (można edytować/importować tylko jeden słownik).

**🗃️ DB Architect** — Mapowanie 1:1 oprócz JOIN-owanych kolumn (tylko do odczytu). Ryzyko: `DELETE kategorii` z powiązanymi `articles.category_id` — importer **musi** sprawdzać FK (ON DELETE SET NULL w bazie ratuje, ale warto zgłosić). Hierarchia kategorii → osobny ticket (zmiana schematu).

**⚙️ Backend Developer** — Eksport czysty pymysql (brak zależności od ORM async → szybsze). Transforms w `SHEETS[x].transforms` pozwalają łatwo dodać kolumny wyliczane.

**🖥️ Frontend Developer** — N/A. Ewentualnie w przyszłości upload Excela przez UI zamiast CLI.

**🎨 UX Designer** — Instrukcja (`00_Instrukcja`) prowadzi użytkownika za rękę. Dropdown na `Akcja` eliminuje literówki. Kolory kolumn (szary=klucz, żółty=akcja, zielony=stat) dają natychmiastowy feedback.

**🔒 Security Auditor** — **Nie eksportujemy tabeli `users`** (hasła bcrypt, e-maile, role). **Nie eksportujemy tabel transakcyjnych** (umowy, kwoty, prowizje). Plik zawiera dane osobowe kontrahentów → traktuj jak RODO (przekaż klientowi, nie publikuj).

**⚡ Performance Engineer** — 581 kontrahentów + 397 artykułów = ~3k komórek, openpyxl wytrzyma. Generowanie <2 s.

**🧪 QA Engineer** — Testy krawędziowe:
- [ ] `Arkusz1` pozostał nietknięty (zweryfikowane: `dims=1:15`, 269 wierszy — OK)
- [ ] ID kolumny zachowały wartości bazy (sprawdzone: `id=10064` → `Ładowarka teleskopowa JLG 3513` — OK)
- [ ] Dropdown `Akcja` działa (DataValidation z zapasem 500 wierszy na NEW)
- [ ] Freeze panes na kolumnie C i wierszu pod nagłówkiem — OK
- [ ] Autofilter pokrywa tylko dane (nie legendę) — OK
- [ ] Znaki diakrytyczne w nazwach kontrahentów — zachowane (UTF-8)

**📋 Product Owner** — Nadmiar kolumn jest świadomy (klient prosił — „najwyżej się skasuje"). Statystyki użycia (zielone kolumny) dają klientowi informację **biznesową** co warto czyścić (69 nieużywanych artykułów = ~17% bazy).

---

## 8. Status

| Zadanie | Status |
|---|---|
| Eksport danych z DB | ✅ Wykonane |
| Plik Excel z 11 arkuszami + instrukcja | ✅ Wykonane |
| Zachowanie oryginalnego `Arkusz1` | ✅ Wykonane |
| Dokumentacja mapowania (ten plik) | ✅ Wykonane |
| **Skrypt importera** | ⏳ TODO — po edycji klienta |
| **Hierarchia kategorii (schemat DB)** | ⏳ TODO — osobny ticket |
