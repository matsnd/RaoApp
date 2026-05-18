# 11 — Reports & Statistics

> **INSTRUKCJA DLA AGENTA:** Ten plik definiuje specyfikację wydruków PDF (odtworzenie starych
> raportów z WinForms) oraz zestaw 5 nowych funkcji analitycznych i statystycznych.
> **Wszystkie oryginalne pliki PDF (wzory raportów oraz OWU) zostały skopiowane do folderu `docs/spec/reference_reports/`.** Użyj ich jako absolutnego wzorca do odtworzenia widoków 1:1.

---

## 1. Wydruki PDF (Jinja2 + WeasyPrint)

W starej aplikacji RAO wykorzystywany był Crystal Reports. Nowa aplikacja generuje PDF-y ze spójnych szablonów HTML/CSS (Jinja2) obsługiwanych przez WeasyPrint.

### 1.1 Sześć rodzajów raportów (Szablony)

Ze względu na rozróżnienie typów umów (Najem / Usługa) oraz potrzeby (z kwotami / bez kwot dla kierowców), system posiada **6 wariantów** wydruków. 
Pliki referencyjne znajdziesz w folderze `docs/spec/reference_reports/`:

1. **Umowa Najmu** (`Umowa.html`) — Pełna umowa najmu sprzętu z kwotami. Oparta na `umowa_..._Umowa_Umowa_najmu.pdf`.
2. **Umowa Usługi** (`UmowaU.html`) — Umowa na świadczenie usług z kwotami. Oparta na `umowa_..._Umowa_Umowa_usługi.pdf`.
3. **Protokół Z-O Najmu** (`ProtokolZO.html`) — Protokół Zdawczo-Odbiorczy dla najmu (zawiera ceny). Oparty na `umowa_..._ProtokolZO_Umowa_najmu.pdf`.
4. **Protokół Z-O Usługi** (`ProtokolZOU.html`) — Protokół dla usług. Oparty na `umowa_..._ProtokolZO_Umowa_usługi.pdf`.
5. **Protokół Z-O "bez" Najmu** (`ProtokolZObez.html`) — Protokół dla kierowców, **ukrywający kolumny z cenami**. Oparty na `umowa_..._ProtokolZObez_Umowa_najmu.pdf`.
6. **Protokół Z-O "bez" Usługi** (`ProtokolZObezU.html`) — Analogicznie dla usług bez kwot. Oparty na `umowa_..._ProtokolZObez_Umowa_usługi.pdf`.

### 1.2 Wizualizacja raportów (referencja)

Aby zachować pełną ciągłość dla klientów, nowe raporty PDF muszą wyglądać i być sformatowane **identycznie** jak w starym systemie.

#### Umowa Najmu/Usługi
Poniżej znajduje się wizualizacja oryginalnej wygenerowanej "Umowy":
![Umowa Najmu](file:///C:/Users/mateu/.gemini/antigravity/brain/cee607b1-9ee9-4f47-9765-9b5a8c0a77a8/umowa_najmu_pdf_1773516575945.png)

#### Protokół Z-O (Zdawczo-Odbiorczy)
Poniżej znajduje się wizualizacja oryginalnego "Protokołu Z-O":
![Protokół Z-O](file:///C:/Users/mateu/.gemini/antigravity/brain/cee607b1-9ee9-4f47-9765-9b5a8c0a77a8/protokol_zo_pdf_1773516585796.png)

*(Zwróć uwagę na tabele, ułożenie danych firmy po lewej i kontrahenta po prawej, oraz sekcje podpisów).*

### 1.3 Logika `own` — Wbudowanie OWU (Ogólnych Warunków Umowy) do szablonów

Stara aplikacja posiadała mechanizm, który fizycznie "doklejał" statyczne pliki PDF (`ownA.pdf` dla najmu, `ownU.pdf` dla usług) na końcu wygenerowanego pliku korzystając z biblioteki PDF.

**Implementacja w nowym systemie:**
Odchodzimy od nielogicznego sklejania plików PDF w locie. 
W nowym systemie (FastAPI + WeasyPrint) będziesz musiał zaprojektować **spójny, jednolity szablon Jinja2**.

1. W folderze `docs/spec/reference_reports/` znajdziesz oryginalne pliki `ownA.pdf` i `ownU.pdf`. Są to Ogólne Warunki Umowy (tekst, punkty regulaminu).
2. Jako Agent postaraj się **wyekstrahować treść** (tekst / układ) z tych plików PDF.
3. Zbuduj układ HTML dla głównych szablonów umów:
   - Na końcu pliku `Umowa.html` (dla najmu), dołącz w HTMLu wyekstrahowaną treść z `ownA.pdf` jako **kolejne strony dokumentu** (użyj CSS `page-break-before: always;`).
   - Na końcu pliku `UmowaU.html` (dla usług), dołącz HTML wyekstrahowany z `ownU.pdf`.
4. Dzięki temu WeasyPrint podczas generowania raportu wygeneruje **jeden, płynny i kompletny plik PDF** z idealnym formatowaniem dla druku, bez potrzeby post-processingu i doklejania innych plików w backendzie.


### 1.4 Tabela "Przy wydaniu / Przy odbiorze" (RAO-P1-010)

Do wszystkich 4 wariantów protokołu Z-O dodana została sekcja `Przy wydaniu / Przy odbiorze`
umieszczona **przed podpisami** (po linii z akceptacją OWU/OWN).

**Lokalizacja w szablonach:**
- `backend/reports/templates/protocol_zo.html` — Protokół Najmu z cenami
- `backend/reports/templates/protocol_zo_u.html` — Protokół Usług z cenami
- `backend/reports/templates/protocol_zo_nodata.html` — Protokół Najmu bez cen
- `backend/reports/templates/protocol_zo_nodata_u.html` — Protokół Usług bez cen

**Struktura tabeli:**

| Kolumna | Opis |
|---------|------|
| (label) | "Przy wydaniu" / "Przy odbiorze" |
| Data i godzina | Puste pole do ręcznego wypełnienia |
| Urządzenie i model | Puste pole |
| Stan paliwa | Puste pole |
| Ilość kluczyków | Puste pole |
| Stan wideł | Puste pole |
| Czystość maszyny | Puste pole |
| Dokumentacja zdjęciowa | Puste pole |
| Dodatkowe akcesoria | Puste pole |
| Uwagi | Puste pole |

**Pola:** Wszystkie pola są **puste** — do ręcznego wypełnienia przez klienta.
**Styl:** Nagłówek tabeli w kolorze `#1D2B53` (Toolsmart navy), tło etykiet wierszy `#f0f2f8`.

### 1.5 Sekcja "Uwagi" przed podpisami (RAO-P1-004 + RAO-P1-016)

Do obu wariantów umowy dodana została sekcja `Uwagi` umieszczona **przed podpisami**
(na ostatniej stronie, po sekcji OWN).

**Lokalizacja w szablonach:**
- `backend/reports/templates/contract.html` — Umowa Najmu
- `backend/reports/templates/contract_u.html` — Umowa Usługi

**Zawartość sekcji:**
- Doba wynajmu: 8 godzin pracy urządzenia
- Zgłoszenie zwrotu: pisemne powiadomienie 1 dzień przed zwrotem
- Dni pracy/tydzień: dane z `contract.working_days_per_week` (default: 5)
- Dokumentacja zdjęciowa: obowiązek dostarczenia przy zwrocie

### 1.6 Font dokumentów — Montserrat (RAO-P1-015 scope-cut)

### 1.7 Sekcja "Ewidencja godzin operatora" w protokole usługi (RAO-P1-014)

**Lokalizacja:**
- `backend/reports/templates/protocol_zo_u.html` — Protokół Usług z cenami

**Zawartość:**
- Tabela z kolumnami: Data, od (godzina), do (godzina), uwagi
- Dane z bazy `service_hours` (jeśli istnieją) lub 12 pustych wierszy do ręcznego wypełnienia
- Sekcja widoczna dla każdej pozycji umowy
- Automatyczne ładowanie przez `build_contract_data()` w `reports/service.py`

**Logika:**
```python
# W reports/service.py, build_contract_data():
hours_result = await db.execute(
    select(ServiceHour).where(ServiceHour.position_id == pos.id).order_by(ServiceHour.service_date)
)
service_hours = hours_result.scalars().all()

# W template:
{% if p.service_hours and p.service_hours|length > 0 %}
  {% for hour in p.service_hours %}
  <tr>
    <td>{{ hour.service_date|datepl }}</td>
    <td>{{ hour.time_from.strftime('%H:%M') }}</td>
    <td>{{ hour.time_to.strftime('%H:%M') }}</td>
    <td>{{ hour.notes }}</td>
  </tr>
  {% endfor %}
{% else %}
  <!-- 12 pustych wierszy -->
{% endif %}
```

### 1.7 Pieczątki firmowe w dokumentach (RAO-P1-022)

Wszystkie dokumenty PDF (umowy, protokoły, OWN) zawierają pieczątkę firmową Toolsmart Sp. z o.o. w sekcjach podpisów Wynajmującego.

**Lokalizacja pieczątki:**
- `backend/reports/assets/company_stamp.jpg` — plik z pieczątką (JPEG, 12275 bytes)
- Wyekstrahowany z referencyjnych PDF z `spec/archive/reference_reports/` używając fitz (PyMuPDF)

**Integracja w szablonach:**
- `contract.html` — Umowa Najmu (sekcja OWN podpisów)
- `contract_u.html` — Umowa Usługi (sekcja podpisów umowy + OWN)
- `protocol_zo.html` — Protokół Najmu (dwie sekcje podpisów: wydanie + zwrot)
- `protocol_zo_u.html` — Protokół Usługi (dwie sekcje podpisów: wydanie + zwrot)
- `protocol_zo_nodata_u.html` — Protokół Usługi bez cen (dwie sekcje podpisów)

**Implementacja:**
- Pieczątka wstawiana przez `<img>` tag z `file://` URI (absolute path)
- Wymiary: 220x85px dla OWN (contract.html), 180x70px dla protokołów
- Pozycja: nad linią podpisu "Czytelny podpis Wynajmującego"
- CSS 1:1 z referencyjnym ownA.pdf: Times New Roman, line-height 1.2, margines 40px

**Metoda ekstrakcji:**
- Biblioteka: fitz (PyMuPDF) — działa na Windows
- Skrypt: `backend/test_pdf_extraction.py` — wyekstrahował 10 obrazów z 6 referencyjnych PDF
- Vision AI: rao-vision MCP — przeanalizował pozycje i wymiary pieczątek

**Weryfikacja:**
- Wygenerowany PDF zawiera pieczątkę na wszystkich stronach (12157 bytes vs 12275 bytes oryginału)
- Test: `curl` endpoint + `fitz.open()` do sprawdzenia obrazów w PDF

Font we wszystkich szablonach PDF zmieniony z Roboto na Montserrat dla spójności
z design systemem Toolsmart.

**Zmienione pliki:**
- `backend/reports/templates/contract.html`
- `backend/reports/templates/contract_u.html`

**Dodatkowo:** Punkt §3 w OWN ma `page-break-before: right` dla lepszego layoutu.

**Klasy CSS:**
- `.pwo-section` — kontener sekcji
- `.pwo-title` — tytuł sekcji (uppercase, navy, border-bottom)
- `table.pwo-table` — tabela 10-kolumnowa z border-collapse
- `.pwo-row-label` — etykieta wiersza (Przy wydaniu / Przy odbiorze)

---

## 2. Statystyki i Analityka (Nowe funkcje)

Użytkownik potrzebuje narzędzi do badania rentowności maszyn. Poniżej specyfikacja nowych endpointów.

> **RAO-P1-017 (zaimplementowane):** Statystyki bazują na kategoriach (`category_main`/`category_sub1`),
> nie na numerach wewnętrznych. Domyślny filtr `is_archival=FALSE` we wszystkich endpointach maszyn.

### 2.1 Numer Wewnętrzny Maszyny

W tabeli `articles` dodane zostało pole `internal_number`. Odróżnia ono maszyny systemowe (np. "Koparka ABC" nr seryjny 123) za pomocą wewnętrznych indeksów ewidencyjnych firmy. Wszystkie widoki na frontendzie (tabele, pola wyboru, PDFy) muszą uwzględniać ten numer tam gdzie wyświetlana jest maszyna.

### 2.1a Kategorie Maszyn (RAO-P1-017)

Tabela `articles` posiada denormalizowane kolumny hierarchii kategorii:
- `category_main VARCHAR(100)` — kategoria główna (snapshot nazwy)
- `category_sub1 VARCHAR(100)` — podkategoria 1
- `category_sub2 VARCHAR(100)` — podkategoria 2
- `category_sub3 VARCHAR(100)` — podkategoria 3
- `is_archival BOOLEAN DEFAULT FALSE` — flaga maszyny archiwalnej

**Domyślny filtr:** wszystkie endpointy statystyk maszyn domyślnie wykluczają `is_archival=TRUE`.
Maszyny bez kategorii trafiają do grupy `(bez kategorii)` w raportach.

### 2.2 Endpoint: Rentowność Maszyny (ROI)

**Cel:** Ile czasu dana maszyna (konkretny egzemplarz `article_id`) była wynajmowana w podanym okresie i ile bezpośrednio wygenerowała przychodu z tytułu *najmu*.

**`GET /stats/machine-roi`**
```
Query: ?article_id=5&date_from=2026-01-01&date_to=2026-12-31&include_archival=false
```

```python
class MachineRoiResponse(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    category_main: str | None     # RAO-P1-017: kategoria główna maszyny
    replacement_value: Decimal | None
    total_rented_days: int
    estimated_revenue: Decimal    # Suma wartości z warunków przypisanych do najmu w tych umowach
    contracts_count: int          # W ilu umowach brała udział
    roi_pct: float | None         # estimated_revenue / replacement_value * 100
```

**Parametry:**
- `article_id` (wymagany) — ID artykułu
- `date_from`, `date_to` — zakres dat (domyślnie: bieżący miesiąc)
- `include_archival=false` — gdy False (domyślnie), maszyny archiwalne zwracają 404

*Opis algorytmu:* Pobierz wszystkie umowy, w których dany `article_id` widnieje, których daty trwania nakładają się na `[date_from, date_to]`. Zlicz przepracowane fizycznie dni i pomnóż przez wynegocjowane warunki z tych konkretnych umów.

### 2.3 Endpoint: Maszyny Obecnie Wynajęte

**Cel:** Szybka statystyka "ile i jakie maszyny pracują na ten moment u klientów".

**`GET /stats/currently-rented`**
```python
class CurrentlyRentedResponse(BaseModel):
    total_rented: int             # Ile łącznie maszyn aktualnie wynajętych
    total_machines: int           # Ile mamy wszystkich maszyn (nie archiwalnych, nie usług)
    utilization_pct: float        # % wypożyczalności
    items: list[CurrentlyRentedItem]

class CurrentlyRentedItem(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    category_main: str | None     # RAO-P1-017: kategoria główna maszyny
    contract_number: str
    contractor_name: str | None
    return_date: date | None      # Kiedy planowany zwrot (date_to aktualnej umowy)
```

**Filtr:** automatycznie wyklucza maszyny `is_archival=TRUE`.
*Opis algorytmu:* `SELECT` maszyn w aktywnych umowach (`date_from <= CURDATE() AND date_to >= CURDATE()`), z wykluczeniem maszyn archiwalnych.

### 2.4 Endpoint: Statystyki Pozycji Dodatkowych/Kosztów

**Cel:** Sumowanie opłat dodatkowych i usług za dany okres (od/do). Wyfiltrowanie kwot czysto za "transport", "mycie", "ładowanie akumulatorów" itp., które płaci klient, obok samych maszyn.

**`GET /stats/additional-fees`**
```
Query: ?date_from=2026-01-01&date_to=2026-03-31
```

```python
class AdditionalFeesResponse(BaseModel):
    date_from: date
    date_to: date
    total_services_revenue: Decimal
    breakdown: list[ServiceFeeItem]

class ServiceFeeItem(BaseModel):
    article_id: int               # Usługi (mycie, transport) jako artykuły gdzie is_service=true
    service_name: str
    total_revenue: Decimal
    times_billed: int             # Użyte np. na 10 umowach
```

*Opis algorytmu:* Sumujemy wartości pozycji na umowach, ale tylko tych, gdzie powiązany `articles.is_service = true` dla umów trwających w zadanym zakresie. Usługi nie mają filtra `is_archival`.

### 2.5 Statystyki Lokalizacji

**Cel:** Zestawienie, w jakich miastach / obszarach mamy najwięcej wynajmów. Odpowiada za dostawy.

**`GET /stats/locations`**
```
Query: ?date_from=2026-01-01&date_to=2026-12-31
```

```python
class LocationStatItem(BaseModel):
    city: str
    rentals_count: int      # Ilość umów w danym mieście
    total_revenue: Decimal  # Wygenerowany obrót z danego miasta
```

*Opis algorytmu:* RAO-P1-008: Grupowanie po `contract.city` (miasto z adresu dostawy) zamiast `contractor.city`. Sumuje liczbę umów oraz przychód per miejscowość w zadanym zakresie dat.

### 2.6 Endpoint: Statystyki Po Kategoriach (RAO-P1-017, NOWY)

**Cel:** Rentowność maszyn agregowana po kategorii (`category_main` lub `category_sub1`).
Zastępuje wcześniejszą agregację po `internal_number`.

**`GET /stats/by-category`**
```
Query: ?level=main&date_from=2026-01-01&date_to=2026-12-31&include_archival=false
```

```python
class CategoryStatsResponse(BaseModel):
    date_from: date
    date_to: date
    level: str              # "main" | "sub1"
    total_revenue: Decimal
    items: list[CategoryStatItem]

class CategoryStatItem(BaseModel):
    category_name: str      # Nazwa kategorii lub "(bez kategorii)"
    articles_count: int     # Ile unikalnych maszyn wynajętych w okresie
    rented_days: int        # Suma dni wynajmu (z zakresu dat)
    revenue: Decimal        # Suma przychodu z kategorii
    contracts_count: int    # Ile unikalnych umów
```

**Parametry:**
| Parametr | Opis | Default |
|----------|------|---------|
| `level` | Poziom kategorii: `main` lub `sub1` | `main` |
| `date_from` | Początek okresu | 1. dzień bieżącego miesiąca |
| `date_to` | Koniec okresu | dzisiaj |
| `include_archival` | Uwzględnij maszyny archiwalne | `false` |

**HTTP codes:** 200 OK | 401 Unauthorized | 422 Validation Error (zły `level`)

**Algorytm:**
1. Pobierz pozycje umów nakładające się na `[date_from, date_to]`, tylko maszyny (`is_service=FALSE`)
2. Opcjonalnie filtruj `is_archival=FALSE` (domyślnie)
3. Grupuj po `category_main` (lub `category_sub1`) — brak kategorii → `(bez kategorii)`
4. Agreguj: `revenue`, `rented_days` (clamped do okna dat), unikalne `article_id`, unikalne `contract_id`
5. Sortuj malejąco po `revenue`

**Implementacja:** `backend/stats/calc.py::aggregate_by_category()` (pure function, testowalny bez DB)

---

### Dashboard (Frontend)
Widok **Dashboard** w nowej aplikacji, obok list "Umowy", "Kontrahenci", musi zawierać dodatkową przestrzeń/zakładkę na **Statystyki / Raporty**, gdzie użytkownik będzie mógł generować powyższe dane we wprowadzonych ramach czasowych.
