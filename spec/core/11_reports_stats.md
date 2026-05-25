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
- Doba wynajmu: obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemne, min. z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: dane z `contract.working_days_per_week` (default: 6) — zmieniono z "Dni pracy/tydzień" wg RAO-P1-002
- Dokumentacja zdjęciowa: wykonano — zmieniono wg RAO-P2-002

**Uwaga - pole "na budowie":** Pole "na budowie" w sekcji "uzupełnij" jest puste (do ręcznego dopisania notatki). Adres dostawy jest wyświetlany tylko raz w sekcji "info-col" jako "Adres dostawy" (wg RAO-P1-001).

**Uwaga - footer-legal (ceny netto):** Sekcja `.footer-legal` na dole strony 1 została wzmocniona wizualnie wg RAO-P1-003: font-size 9px (z 8px), border-top, padding-top, page-break-after: avoid, a tekst "*ceny podane na umowie są cenami netto" jest pogrubiony, czerwony (color: #c00) i większy (font-size: 11px).

**Uwaga - cennik usług dodatkowych (typ U):** Szablon `contract_u.html` (Umowa Usługi z operatorem) NIE zawiera sekcji "Cennik usług dodatkowych" (transport, tankowanie, czyszczenie) wg RAO-P1-004. Szablon `contract.html` (Umowa Najmu) zachowuje tę sekcję, ponieważ klient sam obsługuje maszynę i płaci za te usługi.

**Uwaga - pole 'nr tel' w protokole (osoba upoważniona):** Wszystkie szablony protokołów (protocol_zo.html, protocol_zo_u.html, protocol_zo_nodata.html) zostały zaktualizowane wg RAO-P1-005, aby wyświetlać etykietę "nr tel:" osobno w nowym wierszu, nawet gdy pole jest puste. Format: kontakt_person1 w pierwszym wierszu, "nr tel: [wartość lub puste]" w drugim wierszu (font-size: 9px).

**Uwaga - tabela PWO (Przy wydaniu / Przy odbiorze):** Tabela w protocol_zo.html została powiększona wg RAO-P1-006: height wierszy 32px (z 20px), font-size 10px (z 8.5px), padding 5px 8px (z 2px 5px), wiersz "Uwagi" height 60px (z 36px). Tylko protocol_zo.html ma tę tabelę (inne protokoły mają uproszczone layouty).

**Uwaga - dolna sekcja protokołu (uwagi do zwrotu):** W protocol_zo.html 3 elementy dolne zostały połączone w 1 dużą tabelę "uwagi do zwrotu" wg RAO-P1-007: usunięto tabelę return-table (3 kolumny: dane zwrotu / ilość dni / kaucja), zamieniono div ret-uwagi na div big-uwagi z większym wymiarem (min-height: 140px, padding: 10px 12px, font-size: 10px). Notatka "Ogólna weryfikacja maszyny..." i podpisy zachowane.

**Uwaga - formatowanie warunków kaskadowych rozliczenia (RAO-P1-008):** Opis warunków rozliczenia w PDF jest teraz formatowany przez funkcję `format_position_conditions_cascading` w `backend/contracts/service.py`, która generuje czytelny format kaskadowy (np. "1 - 3 dni - 540,00 / doba", "4 - 16 dni - 410,00 / doba", "powyżej 16 dni - 350,00 / doba"). Funkcja jest używana w `backend/reports/service.py::build_contract_data` i wynik jest przekazywany do szablonu jako `conditions_text`.

**Uwaga - ujednolicenie wcięć w listach numerowanych OWN (RAO-P1-012):** CSS dla OWN w contract.html i contract_u.html zostało ujednolicone wg RAO-P1-012: poziom 0 (p.ot) bez wcięcia, poziom 1 (.own-num) z padding-left: 7mm i text-indent: -7mm (numer wisi na 0mm, tekst zaczyna na 7mm), poziom 2 (.own-num-indent) z padding-left: 13mm i text-indent: -6mm (litera wisi na 7mm, tekst zaczyna na 13mm). Font-size ujednolicony na 7.5pt, line-height na 1.15, text-align: justify. To zapewnia spójne wyrównanie pionowe dla wszystkich numerów (1-17) i sub-list, zgodnie z wymaganiami klienta.

**Uwaga - domyślne usługi dodatkowe dla umów najmu (RAO-P2-001):** Seed w backend/main.py::startup_migrations tworzy domyślny preset usług dodatkowych dla umów najmu (typ S) z 6 usługami w określonej kolejności: Transport (500 zł/dostawa), Czyszczenie drobne (150-400 zł), Czyszczenie trudne (400-1500 zł), Tankowanie (200 zł + paliwo), Prestój transportu (200-300 zł/h), Serwis (280 zł + transport). Seed jest idempotentny i automatycznie kopiowany do nowych umów typu S przez funkcję copy_fee_templates.

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

### 1.7 Pieczątki i podpisy w dokumentach (RAO-P1-022 - uaktualnione)

Wszystkie dokumenty PDF (umowy, protokoły, OWN) zawierają pieczątkę firmową Toolsmart Sp. z o.o. z podpisem w sekcjach podpisów Wynajmującego. Aby uzyskać 100% zgodności wizualnej, wprowadzono dwa odrębne pliki pieczątek firmowych:

**Lokalizacja pieczątek:**
- `backend/reports/assets/company_stamp_fixed.jpg` — Nowa pieczątka firmowa (JPEG, cropped from client screenshot 2026-05-25) z 4 liniami: Toolsmart Sp. z o.o., ul. Kłobucka 6B/103, 02-699 Warszawa, NIP 9512598092, Regon 528847124, KRS 0001109942. Stosowana na umowach (OWN).
- `backend/reports/assets/protocol_stamp.png` — Ta sama pieczątka w formacie PNG (z przezroczystym tłem) stosowana na wszystkich protokołach zdawczo-odbiorczych (PZO), dająca idealne dopasowanie do podpisów.

**Integracja w szablonach:**
- `contract.html` — Umowa Najmu (sekcja OWN podpisów z `company_stamp_fixed.jpg` o wymiarach 220x85px).
- `contract_u.html` — Umowa Usługi (sekcja podpisów umowy z `company_stamp_fixed.jpg` oraz OWN).
- `protocol_zo.html` — Protokół Najmu (dwie sekcje podpisów: wydanie + zwrot z `protocol_stamp.png` o wymiarach 180x70px).
- `protocol_zo_u.html` — Protokół Usługi (dwie sekcje podpisów: wydanie + zwrot z `protocol_stamp.png` o wymiarach 180x70px).
- `protocol_zo_nodata_u.html` — Protokół Usługi bez cen (dwie sekcje podpisów z `protocol_stamp.png` o wymiarach 180x70px).

**Optymalizacja layoutu dwukolumnowego OWN (WeasyPrint Fix):**
- W szablonach `contract.html` oraz `contract_u.html` wyeliminowano przestarzały i błędnie paginowany układ flexboxowy `.own-cols { display: flex; }` na rzecz natywnego, stabilnego układu wielokolumnowego CSS `.own-cols { column-count: 2; column-gap: 15px; }`.
- Usunięto sztuczne separatory kolumn i połączono sekcje OWN w jeden ciągły kontener, co pozwoliło na automatyczny, prawidłowy podział stron w WeasyPrint.
- Zmniejszono padding kontenera `.own-page` i zmieniono wielkość fontu paragrafów `p.ot` na `7.0pt` (margin `2px`, line-height `1.1`) w celu perfekcyjnego zmieszczenia całej treści OWN maszynowego na dokładnie 2 stronach (3 strony całej umowy łącznie) oraz OWN usługowego na dokładnie 1 stronie (2 strony całej umowy łącznie) - zgodnie z absolutnymi wzorcami referencyjnymi (S129 i S130).

**Implementacja techniczna:**
- Pieczątki są wstawiane przez `<img>` tag z `file://` URI (absolute path) generowanym dynamicznie na podstawie ścieżki projektu.
- Pozycja: nad linią podpisu "Czytelny podpis Wynajmującego" lub "czytelny podpis Wynajmującego".
- CSS 1:1 z referencyjnymi plikami: czcionka Times New Roman, line-height 1.15.

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

### 1.8 Eager loading dla artykułów i usług dodatkowych (RAO-P2-XXX)

W `reports/service.py::build_contract_data()` dodano eager loading dla relacji `article` w `ContractPosition` i `ContractServiceFee` w celu uniknięcia błędów N+1 i zapewnienia poprawnego wyświetlania nazw artykułów w szablonach PDF.

**Implementacja:**
```python
# W reports/service.py, build_contract_data():
from sqlalchemy.orm import selectinload
result = await db.execute(
    select(Contract)
    .options(selectinload(Contract.positions).selectinload(ContractPosition.article))
    .options(selectinload(Contract.service_fees).selectinload(ContractServiceFee.article))
    .where(Contract.id == contract_id)
)
```

**Relacje w modelach:**
- `contracts/models.py::ContractPosition.article` — relacja do `Article` (lazy="selectin")
- `contracts/models.py::ContractServiceFee.article` — relacja do `Article` (lazy="selectin")

### 1.9 Zapisywanie PDF do folderów z ustawień (RAO-P2-XXX)

W `reports/router.py::generate_contract_report()` dodano logikę zapisywania wygenerowanych PDF do folderów konfigurowanych w ustawieniach firmy (`Company`).

**Implementacja:**
- Dla umów: zapis do `Company.report_folder` (jeśli skonfigurowany)
- Dla protokołów: zapis do `Company.protocol_folder` (jeśli skonfigurowany)
- Folder jest tworzony automatycznie jeśli nie istnieje (`os.makedirs(folder_path, exist_ok=True)`)
- Błędy zapisu są logowane jako warning i nie przerywają generowania PDF

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
