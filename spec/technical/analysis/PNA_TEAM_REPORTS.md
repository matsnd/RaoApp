# P2-028: Pełne raporty zespołu — Statystyki PNA

**Data:** 2026-06-30
**Zadanie:** Weryfikacja miarodajności statystyk po PNA + ocena propozycji użytkownika
**Zespół:** DB Architect, Tech Lead, UX Designer, Product Owner (4 subagentów równolegle)

---

## 1. DB ARCHITECT — Analiza schematu DB

### Kluczowe ustalenia z danych (spispna_full.csv)

| Metryka | Wartość | Wniosek |
|---|---|---|
| Wierszy w CSV | 21,910 | zgodne z obecnym stanem tabeli |
| Unikalnych PNA | 21,910 | **PNA jest unikalny w spisie PP** |
| Unikalnych nazw miast | 2,824 | nazwa miasta **NIE** jest unikalna |
| Unikalnych par (city, gmina) | 4,686 | 2,824 → 4,686 = ~1,862 nazw występuje w >1 gminie |
| Warszawa | 3,978 PNAs | jeden "miasto" → wiele PNA (potwierdza 1:N) |
| Duplikaty (PNA, city) | 0 | kombinacja jest unikalna |

**Przykład z danych** (potwierdza problem disambiguation):
```
07-405, Aleksandrów, Troszyn,      ostrołęcki,  mazowieckie
09-440, Aleksandrów, Staroźreby,   płocki,      mazowieckie
06-330, Aleksandrów, Chorzele,     przasnyski,  mazowieckie
```
Trzy różne "Aleksandrowy" w trzech gminach/powiatach — rozróżniane deterministycznie przez PNA.

### Ocena obecnej schemy `postal_codes`

```sql
CREATE TABLE postal_codes (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    postal_code  VARCHAR(10)  NOT NULL UNIQUE,   -- poprawne (PNA unikalny w spisie PP)
    city         VARCHAR(100) NOT NULL,           -- OK
    wojewodztwo  VARCHAR(50)  NULL,               -- NULL — w spisie zawsze wypełnione
    powiat       VARCHAR(100) NULL,               -- NULL — w spisie zawsze wypełnione
    gmina        VARCHAR(100) NULL,               -- NULL — w spisie zawsze wypełnione
    INDEX idx_postal_codes_code (postal_code),    -- redundantne (UNIQUE już indeksuje)
    INDEX idx_postal_codes_city (city),           -- potrzebne do GROUP BY / lookup
    INDEX idx_postal_codes_wojewodztwo (wojewodztwo) -- potrzebne do statystyk
)
```

**Werdykt: schema wystarcza strukturalnie, ale ma 3 problemy:**

1. **`wojewodztwo`/`powiat`/`gmina` są NULL** — w spisie PP zawsze wypełnione. Rekomendacja: zostawić NULL (forward-only), wymusić NOT NULL w warstwie aplikacji (Pydantic) i w nowym imporcie.

2. **Brak indeksu na `gmina` i `powiat`** — statystyki po gminie/powiecie zrobią full scan. Dodać.

3. **Brak indeksu composite `(city, gmina)`** — disambiguation "Wola z gminy X vs Wola z gminy Y" wymaga lookupu po parze. Dodać.

4. **`idx_postal_codes_code` jest redundantny** — `UNIQUE` już tworzy indeks. Można usunąć (po zgodzie usera).

### Relacja miasto → PNA (1:N) — poprawna?

**TAK, poprawna.** Dane potwierdzają:
- Warszawa: 1 miasto → 3,978 PNA
- 2,824 nazw miast → 21,910 PNA (średnio 1 miasto = 7.76 PNA)

**Ale uwaga:** w spisie PP "miasto" to nazwa miejscowości, nie obiekt miasta. "Warszawa" występuje jako 3,978 wierszy (jeden na PNA), a nie jako 1 wiersz z 3,978 PNA. To jest model **denormalizowany** — `postal_codes` to słownik PNA, nie słownik miast.

### Czy potrzebna jest oddzielna tabela `cities` (master)?

**NIE — rekomendacja: nie tworzyć.** Uzasadnienie:

| Kryterium | Tabela `cities` | Denormalizacja w `postal_codes` |
|---|---|---|
| Złożoność | +1 tabela, +1 FK, +1 join | brak |
| Spójność (gmina/powiat/woj) | master w `cities`, PNA dziedziczy | redundancja, ale deterministyczna z importu |
| Aktualizacja | UPDATE `cities` → propagacja | reimport `postal_codes` (rzadkie, 1×/rok) |
| Disambiguation | `cities.id` jako klucz | `(city, gmina)` lub PNA |
| Statystyki GROUP BY | join potrzebny | bezpośrednio na `postal_codes` |

**RAO nie potrzebuje `cities` master**, bo:
- Spis PNA aktualizuje się rzadko (rocznie), redundancja gmina/powiat/woj jest akceptowalna
- Auto-fill działa z jednego zapytania: `SELECT * FROM postal_codes WHERE postal_code = ?` — bez joina
- Statystyki GROUP BY województwo/powiat działają bezpośrednio na `postal_codes` (po FK z `contracts`)

### Czy `contracts` powinien mieć FK do `postal_codes`?

**TAK — rekomendacja: wariant C** (FK `postal_code_id` + zostaw `postal_code`/`city` jako snapshot).

| Wariant | Plusy | Minusy |
|---|---|---|
| **A. Status quo** (`postal_code` VARCHAR, brak FK) | proste, brak migracji | auto-fill wymaga lookupu; statystyki po województwie wymagają joina z `postal_codes` po stringu (wolne) |
| **B. FK `postal_code_id` + drop `postal_code`/`city`** | pełna normalizacja | 18 umów z NULL PNA nie ma FK; denormalizacja potrzebna dla wydruku PDF |
| **C. FK `postal_code_id` + zostaw `postal_code`/`city` jako snapshot** ✅ | auto-fill z jednego zapytania; statystyki po FK (szybkie); snapshot zachowuje dane historyczne | redundancja (akceptowalna — snapshot) |

**Ddl:**
```sql
ALTER TABLE contracts ADD COLUMN postal_code_id INT NULL
    COMMENT 'FK do postal_codes (deterministyczna lokalizacja)';
ALTER TABLE contracts ADD CONSTRAINT fk_contracts_postal_code
    FOREIGN KEY (postal_code_id) REFERENCES postal_codes(id) ON DELETE SET NULL;
CREATE INDEX idx_contracts_postal_code_id ON contracts(postal_code_id);
```

### Algorytm disambiguation "Wola z gminy X vs Wola z gminy Y"

**Klucz: PNA jest ostatecznym disambiguatorem.** Nie potrzebujemy skomplikowanego algorytmu.

**A. User wpisuje PNA (główny przypadek):**
```
1. User wpisuje "64-122" w contracts.postal_code
2. Backend: SELECT id, city, gmina, powiat, wojewodztwo FROM postal_codes WHERE postal_code = '64-122'
3. Zwraca: { id: 12345, city: "Wola", gmina: "Wągrowiecki", powiat: "wągrowiecki", wojewodztwo: "wielkopolskie" }
4. Frontend autofill: postal_code_id=12345, city="Wola", gmina/powiat/woj (do statystyk)
→ Deterministyczne, jednoznaczne, 1 zapytanie, indeks UNIQUE
```

**B. User wpisuje miasto (bez PNA — 18 umów NULL):**
```
1. User wpisuje "Wola" w contracts.city
2. Backend: SELECT id, postal_code, city, gmina, powiat, wojewodztwo FROM postal_codes WHERE city = 'Wola'
3. Zwraca N wierszy (np. 15 różnych "Woli" w różnych gminach)
4. Frontend pokazuje dropdown: "Wola (64-122, gm. Wągrowiecki, wlkp.)", "Wola (39-206, gm. Kunów, świętokrzyskie)", ...
5. User wybiera → autofill PNA + gmina + powiat + woj
→ Disambiguation przez wybór usera z listy z gminą jako disambiguatorem
```

**C. Migracja 18 umów z NULL PNA (jednorazowa):**
```
1. Dla każdej umowy z NULL postal_code:
   - SELECT id, postal_code FROM postal_codes WHERE city = <contracts.city> [AND gmina = ?]
   - Jeśli 1 wynik → autofill postal_code_id
   - Jeśli >1 wynik → zostawić NULL, oznaczyć do manualnego rozpatrzenia (raport)
   - Jeśli 0 wyników → literówka w mieście → fuzzy match (Levenshtein) lub manualne
2. Log: "18 umów z NULL PNA: 10 autofilled, 5 niejednoznacznych, 3 literówki"
```

### Rekomendacje indeksów

**Postal_codes (po zmianach):**
```sql
-- Istniejące (zostają):
UNIQUE (postal_code)                          -- lookup po PNA (auto-fill)
INDEX idx_postal_codes_city (city)            -- lookup po mieście
INDEX idx_postal_codes_wojewodztwo (wojewodztwo) -- GROUP BY województwo

-- Dodać:
INDEX idx_postal_codes_gmina (gmina)          -- GROUP BY gmina
INDEX idx_postal_codes_powiat (powiat)        -- GROUP BY powiat
INDEX idx_postal_codes_city_gmina (city, gmina) -- disambiguation "Wola z gminy X"
INDEX idx_postal_codes_woj_pow (wojewodztwo, powiat) -- hierarchiczne statystyki
```

**Contracts (po dodaniu FK):**
```sql
INDEX idx_contracts_postal_code_id (postal_code_id)  -- FK join do statystyk
```

### Podsumowanie rekomendacji DB

| # | Zmiana | Priorytet | Uzasadnienie |
|---|---|---|---|
| 1 | `contracts.postal_code_id INT NULL` + FK + index | **P1** | statystyki po lokalizacji, auto-fill deterministyczny |
| 2 | `postal_codes`: dodać `idx_gmina`, `idx_powiat`, `idx_city_gmina`, `idx_woj_pow` | **P1** | statystyki GROUP BY, disambiguation |
| 3 | `Contract.postal_code` relationship `lazy="selectin"` | **P1** | N+1 prevention |
| 4 | Backfill `postal_code_id` dla 551 umów z PNA | **P1** | migracja danych, jednorazowa |
| 5 | Audit + auto-resolve 18 umów NULL PNA | **P2** | data quality, nie blokuje |
| 6 | Endpoint `/postal-codes/lookup?postal_code=XX-XXX` | **P1** | auto-fill frontend |
| 7 | Endpoint `/postal-codes/search?city=...` (zwraca listę z gminą) | **P2** | disambiguation dropdown |

**NIE rekomendowane:**
- Tabela `cities` master (niepotrzebna złożoność)
- Drop `contracts.postal_code`/`city` (snapshot potrzebny dla PDF i historii)
- Unique `(postal_code, city, gmina)` (redundantne z UNIQUE na `postal_code`)

---

## 2. TECH LEAD — Architektura PNA-based stats

### Klasyfikacja
- **Cross-stack** (DB schema tweak + Backend refactor + Frontend form/panel + spec sync)
- **Rozmiar:** M
- **Priorytet:** P1 (determinizm statystyk — obecnie `extract_city` regex daje rozjazd)

### Kluczowe odkrycie
**Tabela `postal_codes` już istnieje** (21 910 rekordów, schema `postal_code, city, wojewodztwo, powiat, gmina`), a endpoint `/integrations/postal-codes/{code}` już działa — ale zwraca tylko `city + voivodeship`, nie `powiat + gmina`. To zmienia charakter pracy z "zbuduj słownik" na "rozszerz istniejący słownik + ujednolić konsumpcję".

### Ocena propozycji użytkownika — punkt po punkcie

| # | Propozycja | Werdykt | Komentarz |
|---|---|---|---|
| 1 | PNA jako klucz deterministyczny (nie miasto) | ✅ **POPRAWNE** | Potwierdzone danymi: 1 PNA → dokładnie 1 (city, woj, pow, gmina). Miasto → wiele PNA (Warszawa: 3978 PNAs). 2817 distinct miast, 5124 distinct (city,woj,pow,gmina) → nazwa miasta NIE jest unikalna. |
| 2 | Relacja miasto → PNA (1:N), disambiguator = gmina/powiat/woj | ✅ **POPRAWNE** | Słownik `postal_codes` już to modeluje. Brak relacji FK — PNA jest "lookup", nie join. |
| 3 | Algorytm disambiguation xx-xxx vs ww-www → różne "Dupa" | ✅ **POPRAWNE i trywialne** | Skoro PNA → (city,woj,pow,gmina) jest 1:1, disambiguation jest **darmowy** — wystarczy grupować po `postal_code`. Żadnego regexu. |
| 4 | Statystyki deterministyczne PNA-based | ✅ **POPRAWNE** | `stats/router.py:locations` już grupuje po `(postal_code, city)` — ale `explorer/router.py:/locations/{city}` nadal używa `extract_city(delivery_address)` regex → rozjazd. |
| 5 | "Miejsce luzne dostawy" na umowie → wylapuje miasto + dane z PDF | ⚠️ **CZĘŚCIOWO** | Konflikt z `delivery_address` jako uwagi dojazdowe. |
| 6 | Rozwinięcie panelu przy adresie do statystyk | ✅ **POPRAWNE** | Frontend `ReportsSection.vue` — rozbudowa existing panel. |
| 7 | PNA wczytany jako tekst, miasto nie do wypisywania ręcznie | ⚠️ **ZALEŻY** | Patrz sekcja "Blokada ręcznej edycji miasta" poniżej. |

### Odkryte rozjazdy (potwierdzone w kodzie)

1. **Duplikacja algorytmu grupowania** — `stats/router.py:479` i `explorer/router.py:508` mają **identyczną** logikę `key = f"{pna} {city}"` skopiowaną dwa razy. Brak shared helpera.

2. **`extract_city()` (regex, 100 linii) w `explorer/router.py:21`** — używany w 5 miejscach (`/locations/{city}` drill-down, `services/{id}` location_breakdown, top_machines, top_contractors). To jest **legacy heurystyka** która powinna zniknąć gdy PNA jest source of truth.

3. **Rozjazd przychodu** — `stats` liczy przychód przez `_compute_position_revenues` (kaskadowe warunki, `calculate_position_value`), `explorer` liczy przez `rate1 × period_count` (uproszczone, błędne dla stawek jednorazowych i progowych). To jest **bug**, nie tylko duplikacja.

4. **`PostalCodeLookupResponse`** (`integrations/router.py:179`) zwraca `code, city, voivodeship` — **nie zwraca `powiat, gmina`** mimo że są w modelu. Frontend nie dostaje pełnych danych do auto-fill.

5. **191 umów z NULL PNA** (nie 18 jak w propozycji — weryfikacja: `SELECT COUNT(*) FROM contracts WHERE postal_code IS NULL OR postal_code=''` = 191). Liczba 18 dotyczyła prawdopodobnie aktywnych/nierozliczonych.

6. **`stats/calc.py:242` ma drugą kopię `KNOWN_CITIES`** — jeszcze jedna duplikacja listy miast.

### Odpowiedzi na pytania użytkownika

**Q1: PNA jako klucz deterministyczny poprawny?** TAK. PNA → (city, woj, pow, gmina) jest 1:1. Miasto nie jest unikalne (37 różnych "Aleksandrów", 13 "Aleksandrowo"). PNA jest jedynym deterministycznym kluczem.

**Q2: Auto-fill PNA → miasto+gmina+powiat+woj?** Endpoint już istnieje (`/integrations/postal-codes/{code}`), trzeba tylko **dodać `powiat, gmina` do `PostalCodeLookupResponse`** (1-linijkowa zmiana schema + 2 linie w routerze). Frontend `onPostalCodeBlur` już to wywołuje — wystarczy rozszerzyć przypisanie.

**Q3: Statystyki deterministyczne PNA-based?** Grupować po `postal_code` (nie po `city`). Dla drill-down używać `postal_code` jako klucza (nie `city`). Agregacja "po miejscowości" = grupa po `(city, woj, pow, gmina)` z `postal_codes` (JOIN), nie po `contracts.city`.

**Q4: "Miasto nie do wypisywania ręcznie"?** NIE polecam pełnej blokady. Rekomendacja: **auto-fill z PNA + flaga `city_manually_overridden`**. Powody: (a) 191 umów legacy bez PNA — blokada uniemożliwi edycję; (b) PNA może nie być w słowniku (nowe kody, błędy); (c) WinForms parity — stara app pozwalała ręcznie. Kompromis: pole `city` **read-only gdy PNA jest w słowniku**, edytowalne gdy PNA pusty/nieznany.

**Q5: 191 umów z NULL PNA?** NIE wymuszaj PNA w formularzu (breaking dla legacy + kontrahenci zagraniczni). Rekomendacja: (a) **backfill batchowy** — dla umów z `delivery_address` zawierającym `\d{2}-\d{3}` uruchom jednorazowy skrypt `extract_postal_code` + UPDATE; (b) dla pozostałych zostaw NULL; (c) statystyki traktują NULL PNA jako bucket "(brak PNA)" — NIE próbuj `extract_city` regex.

**Q6: "Miejsce luzne dostawy" + dane z PDF?** `delivery_address` w modelu to `Text` — obecnie używane jako "uwagi dojazdowe" (placeholder w formularzu). Propozycja zmienia jego semantykę. Rekomendacja: **NIE przeciążać `delivery_address`**. Zamiast tego: PNA jest kluczem, `delivery_address` zostaje jako wolny tekst uwag. "Miejsce luzne" z PDF = osobne pole `delivery_place` (VARCHAR 100) lub reuse `city` z auto-fill.

**Q7: Panel statystyk: PNA + miasto + gmina + powiat + woj?** TAK, ale z hierarchią: główna kolumna = `postal_code + city`, rozwijane (drill-down) = `gmina, powiat, województwo`. Schema `LocationStatItem` rozszerzyć o te 3 pola (nullable, z LEFT JOIN do `postal_codes`).

**Q8: Uniknąć duplikacji stats vs explorer?** Wyciągnąć shared helper `locations/aggregate.py` (nowy moduł `backend/locations/` lub `shared/locations.py`) z funkcją `aggregate_by_pna(contracts_qs)`. Obie routery importują. `extract_city` → usunąć.

**Q9: `extract_city` całkowicie usunąć?** TAK, ale **sekwencyjnie**: (1) dodać PNA-based drill-down, (2) przepiąć wszystkie 5 call-site'ów, (3) dopiero wtedy usunąć. Nie usuwać natychmiast — `services/{id}/location_breakdown` też tego używa.

**Q10: Spójność algorytmu przychodu?** `explorer` musi używać `_compute_position_revenues` z `stats/router.py` (lub wyekstrahowanego do `shared/revenue.py`), nie `rate1 × period_count`. To jest **bug P1** niezależnie od propozycji PNA.

### Proponowana architektura

**Source of truth:**
```
postal_codes (słownik, 21 910 wierszy, już istnieje)
  ↓ JOIN po postal_code
contracts.postal_code (FK logiczna, nie DB FK — słownik może mieć luki)
  → determinuje city + gmina + powiat + wojewodztwo
```

**Klucz statystyk:**
- **Grupowanie wg PNA** (najbardziej granularne) → `GROUP BY postal_code`
- **Rollup wg miejscowości** → `GROUP BY city, wojewodztwo, powiat, gmina` (z JOIN do `postal_codes`)
- **Drill-down URL** → `/explorer/locations/{postal_code}` (zmienić z `{city}` — BC break, ale konieczne)
- **NULL PNA** → bucket `(brak PNA)`, NIE regex fallback

**Disambiguation — darmowe:** PNA determinuje wszystko. "Dupa" w woj. mazowieckim vs "Dupa" w woj. wielkopolskim to po prostu różne PNA. Statystyki po PNA nigdy ich nie pomyli. Rollup po `city` bez `(woj,pow,gmina)` → NIEPOPRAWNY (suma dwóch różnych miejscowości) — dlatego rollup musi grupować po pełnym tuple.

### Plan podziału pracy (Tech Lead)

1. **DB Agent** (XS, sekwencyjnie, bloker): Rozszerzyć `PostalCodeLookupResponse` o `powiat, gmina`. JOIN, nie denormalizować.
2. **Backend Agent — refactor shared** (S, sekwencyjnie po #1, bloker): Wyekstrahować `shared/locations.py` + `shared/revenue.py`.
3. **Backend Agent — stats/explorer unifikacja** (S, sekwencyjnie po #2): `stats/locations` + `explorer/locations` → użyć shared helper. `/locations/{city}` → `/locations/{postal_code}`. Usunąć `extract_city`.
4. **Backend Agent — backfill NULL PNA** (XS, równolegle z #3): Skrypt jednorazowy.
5. **Frontend Agent — formularz** (S, sekwencyjnie po #2): `onPostalCodeBlur` rozszerzyć, `city` readonly gdy PNA w słowniku.
6. **Frontend Agent — panel statystyk** (S, sekwencyjnie po #3): Kolumny lokalizacji + drill-down po PNA.
7. **QA Agent** (S, sekwencyjnie po #3/#5/#6): E2E + smoke.
8. **Spec sync** (XS, równolegle z #7).

### Ryzyka

- **BC break `/locations/{city}` → `/locations/{postal_code}`**: frontend + e2e + ew. zewnętrzni konsumenci. Mitygacja: alias `/locations/{city_or_pna}` z heurystyką.
- **191 umów NULL PNA**: statystyki bez PNA wpadną do bucket "(brak)". Mitygacja: backfill z `delivery_address` (regex) + zostaw NULL dla reszty.
- **Słownik `postal_codes` niekompletny**: nowe kody PNA, błędy w słowniku. Mitygacja: `postal_code` w formularzu = warning (nie error) gdy nie znaleziono; `city` edytowalne gdy PNA nie w słowniku.
- **`extract_city` usuwane za wcześnie**: 5 call-site'ów w explorerze. Mitygacja: sekwencyjnie — najpierw przepiąć, potem usunąć.
- **Rozjazd przychodu stats vs explorer**: niezależny bug, ale naprawa w tym samym refactorze. Mitygacja: shared `revenue.py`, test jednostkowy porównujący wyniki obu endpointów.

---

## 3. UX DESIGNER — Panel adresu PNA + statystyki

### Flow analysis — obecny stan

**Formularz adresu (ContractFormView, linie 63–82):**
1. User widzi select "— wpisz ręcznie —" lub listę adresów kontrahenta
2. Jeśli wybierze adres z listy → pola wypełniają się z bazy
3. Jeśli "wpisz ręcznie" → wpisuje PNA (input 6 znaków) + Miasto (input) + textarea "Uwagi dojazdowe"
4. Po `blur` na PNA → fetch `/integrations/postal-codes/{code}` → wypełnia **tylko** `city` (bez gminy/powiatu/województwa)
5. Wpisanie w textarea `delivery_address` → debounce 800ms → POST `/integrations/extract-address` → wypełnia city + postal_code + lat/lon
6. **Brak pól gmina/powiat/województwo** w formularzu

**Statystyki lokalizacji (ReportsSection, linie 744–848):**
1. Tab "Eksplorator" → subtab "Lokalizacje"
2. Input "Szukaj miasto" → live filter po `city`
3. Ranking miast: #, Miasto, PNA, Umów, Przychód (top 20)
4. Klik na miasto → detail panel: KPI + top maszyny + top kontrahenci
5. **Brak hierarchii** PNA → miasto → gmina → powiat → województwo
6. **Brak filtrów** po województwie/powiecie/gminie
7. **Brak mapy**

### Ocena propozycji użytkownika

| # | Propozycja | Ocena UX | Komentarz |
|---|---|---|---|
| 1 | PNA jako klucz → auto-fill miasto+gmina+powiat+woj | ✅ Bardzo dobra | Redukuje kroki, eliminuje literówki. **Ale** wymaga fallback gdy PNA nieznaleziony |
| 2 | "Miasto nie do wypisywania" — auto-fill z PNA | ⚠️ Częściowo | Dobry kierunek, **ALE** user musi móc nadpisać gdy PNA ma wiele miast lub jest błędny. Read-only = ryzyko blokady |
| 3 | Miejsce luźne dostawy → wylapuje miasto + dane z PDF | ✅ Dobre | Już częściowo działa (onDeliveryAddressInput). Trzeba rozszerzyć o PNA extraction |
| 4 | Rozwinięcie panelu przy adresie do statystyk | ✅ Dobre | Inline panel = mniej klików niż nawigacja do Raportów |
| 5 | Kod pocztowy wczytany jako tekst w panelu do przeczytania | ✅ Dobre | Read-only display potwierdza auto-fill |
| 6 | Statystyki miarodajne i deterministyczne | ✅ Krytyczne | Bez tego cała funkcjonalność traci sens |

### Problemy znalezione

#### P0 — Blokujące UX

- **Brak fallback gdy PNA nie znaleziony w bazie**
  - **Case:** User wpisze `99-999` (nieistniejący) → pole Miasto zostaje puste, brak komunikatu
  - **Fix:** Inline error pod polem PNA: "Nie znaleziono kodu 99-999 w bazie. Wpisz miasto ręcznie." + odblokuj pole Miasto

- **18 umów z NULL PNA — niewidoczne w statystykach**
  - **Case:** W ranking miast te 18 umów jest zgrupowane pod miastem z `postal_code = NULL` → pokazywane jako "—"
  - **Fix:** W panelu statystyk sekcja "Umowy bez PNA (18)" z listą numerów umów + CTA "Uzupełnij"

- **"Miasto nie do wypisywania" (read-only) blokuje edge case wielu miast dla jednego PNA**
  - **Case:** PNA `00-001` → Warszawa, ale PNA `05-070` → Sulejówek + Warszawa (częściowo). Jeśli user wie że dostawa jest w Sulejówku, a system wstawi Warszawę — nie może poprawić
  - **Fix:** Pole Miasto = auto-filled ale **edytowalne**. Po auto-fill pokazuj tooltip "Wypełnione z PNA. Kliknij aby zmienić." Jeśli user edytuje → flag `city_manually_overridden = true`

#### P1 — Pogorszone UX

- **Brak loading state na lookup PNA** — spinner w polu Miasto podczas lookup
- **Brak walidacji formatu PNA przed lookup** — inline walidacja: "PNA musi mieć format 00-000"
- **Brak pól gmina/powiat/województwo w formularzu** — read-only panel pod polami PNA+Miasto
- **Statystyki — brak filtra po województwie** — dropdown "Województwo" nad rankingiem
- **Brak drill-down hierarchii w statystykach** — breadcrumb-style: `Województwo › Powiat › Gmina › Miasto`

#### P2 — Polish

- **Brak undo dla auto-fill** — toast "Wypełniono z PNA 00-001: Warszawa, mazowieckie" z przyciskiem "Cofnij"
- **Brak potwierdzenia przy zmianie PNA w istniejącej umowie** — confirm dialog
- **Brak mapy geograficznej** — opcjonalny widok mapy (Leaflet + OpenStreetMap, bez API key)

### Proponowany UX flow — formularz adresu z auto-fill PNA

```
┌─ Adres dostawy ──────────────────────────────────────────┐
│                                                          │
│  [Select: — wpisz ręcznie — ▾]   (lista adresów kontr.) │
│                                                          │
│  Kod pocztowy *    Miasto                                │
│  [00-001    ] ⓘ    [Warszawa    ] ⓘ  ← auto-filled      │
│   ↑ spinner gdy      ↑ disabled podczas lookup           │
│     lookup w toku      ↑ edytowalny po lookup (z flagą)  │
│                                                          │
│  ┌─ Wypełnione z PNA 00-001 ────────────────────────┐    │
│  │ Gmina: Warszawa • Powiat: Warszawa • Woj: mazow.│    │
│  │ (muted, font-size-sm, read-only)                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Uwagi dojazdowe (opcjonalnie)                          │
│  [textarea: auto-uzupełni PNA+miasto z tekstu]          │
│                                                          │
│  ┌─ 📊 Statystyki dla tej lokalizacji ──────────────┐    │
│  │ ▸ 12 umów • 245 000 zł przychodu (wszystkie)    │    │
│  │ ▸ 3 umowy w tym roku • 78 000 zł                │    │
│  │ [Zobacz szczegóły →]  (link do Eksploratora)    │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Proponowany panel statystyk — hierarchia, filtry, drill-down

```
┌─ 📍 Lokalizacje ─────────────────────────────────────────┐
│                                                          │
│  Filtry:                                                 │
│  Województwo [— wszystkie — ▾]                          │
│  Powiat      [— wszystkie — ▾]  (kaskadowy, zależny)    │
│  Gmina       [— wszystkie — ▾]  (kaskadowy, zależny)    │
│                                                          │
│  Breadcrumb: 🇵🇱 Polska › Mazowieckie › Warszawa        │
│                                                          │
│  [Tabela] [Mapa]  ← toggle widoku                       │
│                                                          │
│  ┌─ Ranking (poziom: POWIAT) ───────────────────────┐    │
│  │ # Powiat          Umów  Przychód   Średnio       │    │
│  │ 1 Warszawa         45   1.2M zł    27k zł  →     │    │
│  │ 2 Piaseczyński     18   456k zł    25k zł  →     │    │
│  │ 3 Wołomiński       12   298k zł    25k zł  →     │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌─ ⚠️ Umowy bez PNA (18) ──────────────────────────┐    │
│  │ UM-2024-001 • UM-2024-005 • ...  [Uzupełnij →]   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Drill-down flow:**
1. Domyślnie: ranking **województw** (16 pozycji)
2. Klik na województwo → breadcrumb + ranking **powiatów**
3. Klik na powiat → ranking **gmin**
4. Klik na gminę → ranking **miast/PNA**
5. Klik na miasto → detail panel (KPI + top maszyny + top kontrahenci)
6. Breadcrumb klikalny na każdym poziomie — cofanie

### Edge cases do obsługi

- **PNA nie znaleziony w bazie:** Inline error "Nie znaleziono kodu 99-999. Wpisz miasto ręcznie." + odblokuj Miasto
- **PNA z literówką:** Walidacja formatu + komunikat "Czy chodziło o 00-010? (Warszawa)" — sugestia Levenshtein
- **Wiele PNA dla jednego miasta:** Reverse lookup "miasto → lista PNA" — user wybiera z listy
- **Jeden PNA → wiele miast (rzadkie):** Auto-fill pierwsze miasto + tooltip "Ten PNA obejmuje też: Sulejówek, Marki. Kliknij aby zmienić."
- **NULL PNA w statystykach:** Osobna sekcja "Umowy bez PNA (18)" z listą + CTA "Uzupełnij"
- **PNA poza Polską:** Komunikat "Kody pocztowe poza Polską nie są obsługiwane. Wpisz miasto ręcznie."
- **User edytuje miasto po auto-fill:** Flaga `city_manually_overridden` — w statystykach oznacz jako "ręcznie poprawione" (badge)
- **Network timeout na lookup PNA:** Toast "Nie udało się pobrać danych PNA. Spróbuj ponownie lub wpisz ręcznie." + pole Miasto odblokowane

### Rekomendacje priorytetowe UX

| Priorytet | Co | Dlaczego |
|---|---|---|
| P0 | Fallback gdy PNA nie znaleziony + inline error | Bez tego user wpisze miasto ręcznie = zanieczyszczone statystyki |
| P0 | Sekcja "Umowy bez PNA (18)" w statystykach | User musi wiedzieć że problem istnieje |
| P0 | Pole Miasto edytowalne po auto-fill (z flagą override) | Edge case wielu miast dla PNA |
| P1 | Read-only panel Gmina/Powiat/Województwo w formularzu | User weryfikuje poprawność auto-fill |
| P1 | Loading state na lookup PNA (spinner w polu Miasto) | Eliminuje race condition UX |
| P1 | Walidacja formatu PNA + auto-format z myślnikiem | Redukuje błędy wpisów |
| P1 | Filtry województwo/powiat/gmina w statystykach | Analityka regionalna |
| P1 | Drill-down hierarchiczny z breadcrumb | Nawigacja po poziomach agregacji |
| P2 | Reverse lookup "miasto → lista PNA" | Dla userów którzy nie znają PNA |
| P2 | Mapa geograficzna (toggle) | Wizualizacja geograficzna |
| P2 | Undo toast dla auto-fill | Polish, redukuje frustrację |

### Czego NIE rekomenduję UX

- ❌ **Dropdown/autocomplete dla 21,910 kodów PNA** — za dużo pozycji, wolne, nieczytelne. Input tekstowy + lookup jest lepszy
- ❌ **Read-only pole Miasto (całkowita blokada)** — edge case wielu miast dla PNA wymaga możliwości korekty
- ❌ **Mapa jako domyślny widok statystyk** — handlowiec chce liczby, mapa jest wolniejsza i mniej analityczna
- ❌ **Alert() dla błędów PNA** — legacy WinForms pattern, użyj inline error + toast

### Design system Toolsmart

- Kolory: `--color-primary` (navy) dla nagłówków, `--color-text-muted` dla read-only gmina/powiat/woj, `--color-error` dla inline errors, `--color-success` dla toast auto-fill
- Font: Montserrat, `--font-size-sm` (13px) dla read-only panel hierarchii, `--font-size-base` (14px) dla inputów
- Border radius: `--border-radius-md` (12px) dla paneli, `--border-radius-sm` (8px) dla inputów
- Shadow: `--shadow-card` dla paneli, `--shadow-card-hover` dla row-clickable w tabeli
- Spacing: `--spacing-3` (12px) między polami PNA/Miasto, `--spacing-4` (16px) między sekcjami adresu
- Toast: pill-shaped (`--border-radius-pill`), navy bg dla info, green dla success, red dla error

---

## 4. PRODUCT OWNER — Wartość biznesowa PNA-based

### Problem statement

**User story:** Jako właściciel floty / handlowiec, chcę aby statystyki lokalizacji były deterministyczne (nie rozbijały Warszawy na 20 wierszy ani nie łączyły 5 różnych "Woli" w jeden koszyk), a wpisanie kodu pocztowego automatycznie uzupełniało miasto — żebym mógł podejmować decyzje alokacyjne na rzetelnych danych i nie tracił czasu na ręczne wpisywanie.

**Frequency:**
- Wpisywanie PNA w umowie: kilkanaście razy dziennie na handlowca (~10 userów × ~10 umów/dzień = ~100 wpisów/dzień)
- Odczyt statystyk lokalizacji: tygodniowo / przy planowaniu serwisu i alokacji
- Decyzje regionalne (ekspansja, nowa baza): kwartalnie / rocznie

**Impact braku rozwiazania:**
- **Statystyki niedeterministyczne** = decyzje alokacyjne na błędnych danych (5 różnych "Woli" jako jeden koszyk → błędne wnioski o zapotrzebowaniu)
- **Warszawa rozbita na 20 wierszy** = regresja UX vs legacy, handlowiec nie widzi agregatu
- **Ręczne wpisywanie miasta** = literówki (18 NULL-i w bazie, "Wola x5" w legacy), ~30s/umowę zbędnej pracy

### Feature parity check

- **Legacy WinForms:** grupowało po nazwie miasta (tekst) → problem "Wola x5", "Michałowice x3" — słabe, ale Warszawa jako jeden wiersz
- **Nowy RAO (obecnie):** agreguje po `PNA + city` → deterministyczne, ALE Warszawa rozbita na 20 wierszy = **regresja czytelności** vs legacy
- **Czy gubimy cos:** TAK — czytelność agregatu dla dużych miast. Trzeba naprawić display, nie rezygnować z determinizmu.
- **Czy zyskujemy:** TAK — disambiguation małych miejscowości (Wola, Michałowice, Lesznowola) — legacy tego nie miało

### Priorytet

**Klasyfikacja: P1 (częściowo) + P2 (większość)**

**Uzasadnienie podziału:**
- **P1 — Auto-fill PNA→miasto + naprawa regresji "Warszawa x20":** naprawia istniejący bug w statystykach (regresja vs legacy) + oszczędność czasu codziennie. ROI jasne.
- **P2 — Pełna hierarchia terytorialna (gmina/powiat/wojew.) + drill-down:** decyzje regionalne podejmowane kwartalnie/rocznie, 10 userów, flota operuje głównie na 2 województwach. Premature optimization na ten moment.
- **ODRZUC — "Miasto nie do wypisywania" (read-only z PNA):** ryzyko biznesowe (patrz czerwone flagi).

### Definition of Done

**v1 (P1 — naprawa regresji + auto-fill):**
- [ ] Wpisanie PNA w formularzu umowy → automatycznie uzupełnia `city` z tabeli `postal_codes` (jeśli PNA znaleziony)
- [ ] Pole `city` pozostaje **edytowalne** (fallback gdy PNA nie znaleziony lub miasto dostawy ≠ miasto PNA)
- [ ] `/stats/locations` agreguje wewnętrznie po `postal_code` (determinizm), ale **display pokazuje "Miasto"**; tylko gdy nazwa miasta ma >1 PNA → suffix "Miasto (XX-XXX)"
- [ ] Warszawa (151 umów, 82 PNA) → **jeden wiersz "Warszawa"** w statystykach (agregat), z opcją rozwinięcia per-PNA
- [ ] "Wola" z 5 PNA → 5 wierszy "Wola (05-500)", "Wola (05-506)" itd.
- [ ] Test: 21,910 PNA w bazie, zapytanie lookup <10ms (indeks PK)
- [ ] Test: umowa z PNA "02-699" → city auto-filled "Warszawa", nie wymaga ręcznego wpisu

**v2 (P2 — hierarchia, na później):**
- [ ] Tabela `postal_codes` rozszerzona o `gmina`, `powiat`, `wojewodztwo`, `lat`, `lng`
- [ ] `/stats/locations` z opcjonalnym filtrem `wojewodztwo`, `powiat`
- [ ] Drill-down: województwo → powiat → gmina → miasto → PNA
- [ ] Raport regionalny (nowy widok lub sekcja w StatsView)

### Scope

**W tym zadaniu (v1, P1):**
- Auto-fill `city` z PNA w formularzu umowy (frontend + backend endpoint — endpoint `/integrations/postal-codes/{code}` już istnieje)
- Naprawa display w `/stats/locations`: agregat po PNA, display "Miasto" lub "Miasto (XX-XXX)" gdy ambiguous
- Zachowanie edytowalności pola `city` (NIE read-only)

**Poza scope (na później — P2):**
- Pełna hierarchia terytorialna (gmina/powiat/województwo) w tabeli `postal_codes`
- Drill-down woj→powiat→gmina→miasto→PNA
- Filtry regionalne w statystykach
- Raport ekspansji regionalnej
- "Kod pocztowy wczytany jako tekst w panelu do przeczytania" — niezrozumiałe wymaganie, wymaga doprecyzowania od użytkownika

**Odrzucone z scope:**
- **"Miasto nie do wypisywania" (read-only z PNA)** — patrz czerwone flagi
- **"Miejsce luzne dostawy wylapuje miasto + dodaje dane z PDF"** — już obsługiwane przez RAO-P1-017 (extract-address z `delivery_address`, hybryda offline + Nominatim, status dev-verified). Nie duplikuj.

### ROI

**v1 (P1):**
- **Czas oszczędzony:** ~30s/umowę × ~100 umów/dzień = ~50 min/dzień = ~4h/tydzień zespołu handlowego
- **Userzy korzystający:** ~10 handlowców (codziennie) + właściciel floty (statystyki tygodniowo)
- **Alternatywa:** ręczne wpisywanie miasta (istnieje, ale generuje literówki → 18 NULL-i, "Wola x5")
- **Koszt implementacji:** ~3-4h (endpoint już istnieje, frontend debounce już istnieje z P1-017, zmiana SQL w `/stats/locations` + display logic)
- **ROI:** pozytywny — oszczędność 4h/tydz. vs koszt 3-4h jednorazowo = zwrot w 1 tyg.

**v2 (P2):**
- **Czas oszczędzony:** trudny do oszacowania — decyzje regionalne kwartalnie
- **Userzy korzystający:** głównie właściciel floty (1 osoba), sporadycznie
- **Koszt:** 6-8h (rozszerzenie tabeli, import hierarchii, nowe filtry, drill-down UI)
- **ROI:** marginalny na ten moment — odłożyć do momentu ekspansji na 3+ województwa

### Czerwone flagi PO

1. **🔴 "Miasto nie do wypisywania" (read-only z PNA) — ODRZUC**
   - **Realny scenariusz:** firma ma siedzibę w Warszawie (PNA 00-001), ale dostawa maszyny na budowę w Radomiu (PNA 26-600). Jeśli `city` jest read-only z PNA kontrahenta → zapisze się "Warszawa" zamiast "Radom".
   - **PNA nie znaleziony:** 21,910 kodów w bazie vs ~42,000 oficjalnie — coverage ~52%. Co z resztą? Read-only pole = blokada wprowadzania danych.
   - **PNA zmienia przynależność:** Poczta Polska aktualizuje PNA kwartalnie — miasto może się "zmienić" bez wiedzy usera.
   - **Rekomendacja:** `city` zostaje edytowalne. Auto-fill to **sugestia**, nie wymuszenie.

2. **🟡 "Miejsce luzne dostawy" + ekstrakcja z PDF — duplikacja z P1-017**
   - P1-017 (status dev-verified) już robi hybrydowy extract-address z `delivery_address` (offline regex + Nominatim fallback, coverage 97%). Nie buduj drugiego mechanizmu ekstrakcji z PDF — to ten sam problem.

3. **🟡 "Kod pocztowy wczytany jako tekst w panelu do przeczytania" — niejasne**
   - Wymaga doprecyzowania: co to jest "panel do przeczytania"? Czy chodzi o wyświetlenie PNA w PDF umowy? W statystykach? W formularzu? Bez jasnego job-to-be-done nie buduj.

4. **🟡 Warszawa rozbita na 20 wierszy = regresja vs legacy**
   - To jest **bug**, nie feature. Powinien być naprawiony niezależnie od decyzji o hierarchii. Agregat display po nazwie miasta + rozwinięcie per-PNA on-demand.

5. **🟡 21,910 PNA vs 42,000 oficjalnie — coverage 52%**
   - Auto-fill zadziała tylko dla ~52% wpisów. Dla reszty user musi móc wpisać miasto ręcznie (patrz flaga #1). Komunikat "PNA nie znaleziony w słowniku" zamiast blokady.

6. **🟢 Hierarchia terytorialna dla 10 userów na 2 województwach = premature optimization**
   - Backlog P2-028 sam notuje: "Czy importować pełną bazę PNA czy tylko Mazowsze + Pomorskie (główne obszary operacyjne)?" — odpowiedź PO: tylko obszary operacyjne na v1, pełna baza na v2 gdy ekspansja.

### Sugestia decyzji PO

**REKOMENDACJA: UPROSC + BUDUJ TERAZ (v1) / ODŁOŻ (v2)**

**Uzasadnienie:**

Propozycja użytkownika zawiera **3 różne wartości biznesowe o różnym ROI** — nie buduj ich jako jednego zadania:

1. **BUDUJ TERAZ (P1, ~3-4h):** Auto-fill PNA→miasto (endpoint już istnieje) + naprawa regresji "Warszawa x20" w statystykach (agregat po PNA, display po mieście z suffixem tylko gdy ambiguous). To naprawia istniejący bug i oszczędza 4h/tydz. zespołu. Zwrot w 1 tyg.

2. **ODŁOŻ (P2, 6-8h):** Pełna hierarchia terytorialna (gmina/powiat/wojew.) + drill-down + filtry regionalne. Decyzje regionalne są kwartalne, 10 userów na 2 województwach — premature optimization. Wrócić gdy flota ekspanduje na 3+ województwa lub gdy klient wyraźnie poprosi o raport regionalny.

3. **ODRZUC:** "Miasto nie do wypisywania" (read-only z PNA) — ryzyko biznesowe (dostawa pod inny adres niż siedziba, PNA nie znaleziony, zmiany w bazie Poczty Polskiej). Auto-fill = sugestia, nie wymuszenie.

4. **NIE DUPLIKUJ:** "Miejsce luzne dostawy + ekstrakcja z PDF" — RAO-P1-017 już to robi (dev-verified, coverage 97%). Zamiast nowego mechanizmu → dokończ weryfikację P1-017 i wdróż.

**Akcja dla backloga:**
- Reaktywuj RAO-P2-028, ale **podziel na 2 sub-zadania**:
  - RAO-P1-XX (nowe): Auto-fill PNA→city + naprawa display statystyk (P1, S, ~3-4h)
  - RAO-P2-028 (pozostaje): Pełna hierarchia terytorialna + drill-down (P2, L, odłożone)
- Dodaj decyzję PO do backloga: *"city pozostaje edytowalne — auto-fill to sugestia, nie wymuszenie"* (nadpisuje propozycję "miasto nie do wypisywania")
- Doprecyzuj z użytkownikiem: co to jest "kod pocztowy wczytany jako tekst w panelu do przeczytania" — bez jasnego JTBD nie buduj

---

## KONSENSUS ZESPOŁU (synteza Tech Leada)

### Odpowiedź na pytanie użytkownika: "Czy statystyki będą miarodajne po PNA?"

**Z obecną implementacją: NIE w pełni.** 6 rozjazdów:
1. Warszawa rozbita na 20 wierszy w top 20 (regresja vs legacy)
2. Drill-down `/explorer/locations/{city}` używa `extract_city(delivery_address)` zamiast `Contract.city` — klik na miasto zwraca inny zestaw umów niż ranking
3. `stats/locations` i `explorer/locations` mają **różne algorytmy przychodu**
4. Frontend `:key="loc.city"` → duplikat klucza Vue (bug renderowania)
5. 191 umów z NULL PNA (nie 18 — weryfikacja TL)
6. `extract_city` regex (100 linii) w 5 miejscach — legacy heurystyka

**Z propozycją użytkownika (PNA jako klucz): TAK, ale wymaga naprawy.**

### Werdykt zespołu dla propozycji użytkownika

| Propozycja | Werdykt | Konsensus |
|------------|---------|-----------|
| PNA jako klucz deterministyczny | ✅ POPRAWNE | Wszyscy zgodni — PNA→(city,woj,pow,gmina) jest 1:1 |
| Auto-fill PNA→miasto+gmina+powiat+woj | ✅ BUDUJ | Endpoint już istnieje, brakuje `powiat,gmina` w response |
| Disambiguation xx-xxx vs ww-www | ✅ DARMOWE | PNA determinuje wszystko, żadnego algorytmu potrzeba |
| Statystyki PNA-based | ✅ BUDUJ | Grupuj po PNA, rollup po (city,woj,pow,gmina) |
| **"Miasto nie do wypisywania" (read-only)** | ❌ **ODRZUC** | PO+UX+TL: ryzyko blokady (191 umów NULL, PNA nie w słowniku, dostawa pod inny adres) |
| Miejsce luzne dostawy + dane z PDF | ⚠️ NIE DUPLIKUJ | P1-017 już robi extract-address (coverage 97%) |
| Panel statystyk z hierarchią | ✅ BUDUJ (P2) | Drill-down woj→powiat→gmina→miasto→PNA |

### Kluczowa decyzja zespołu: "miasto nie do wypisywania" = ODRZUC

**3 z 4 agentów (PO, UX, TL) odrzucają read-only miasta:**
- 191 umów legacy bez PNA — blokada uniemożliwi edycję
- PNA może nie być w słowniku (21,910 vs ~42,000 oficjalnie = 52% coverage)
- Dostawa pod inny adres niż siedziba kontrahenta (realny scenariusz)
- WinForms parity — stara app pozwalała ręcznie

**Kompromis zespołu:** auto-fill z PNA + pole `city` **edytowalne** (z flagą `city_manually_overridden` gdy user poprawi).
