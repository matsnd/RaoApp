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

**Klasy CSS:**
- `.pwo-section` — kontener sekcji
- `.pwo-title` — tytuł sekcji (uppercase, navy, border-bottom)
- `table.pwo-table` — tabela 10-kolumnowa z border-collapse
- `.pwo-row-label` — etykieta wiersza (Przy wydaniu / Przy odbiorze)

---

## 2. Statystyki i Analityka (Nowe funkcje)

Użytkownik potrzebuje narzędzi do badania rentowności maszyn. Poniżej specyfikacja nowych endpointów.

### 2.1 Numer Wewnętrzny Maszyny

W tabeli `articles` dodane zostało pole `internal_number`. Odróżnia ono maszyny systemowe (np. "Koparka ABC" nr seryjny 123) za pomocą wewnętrznych indeksów ewidencyjnych firmy. Wszystkie widoki na frontendzie (tabele, pola wyboru, PDFy) muszą uwzględniać ten numer tam gdzie wyświetlana jest maszyna.

### 2.2 Endpoint: Rentowność Maszyny (ROI)

**Cel:** Ile czasu dana maszyna (konkretny egzemplarz `article_id` lub `internal_number`) była wynajmowana w podanym okresie i ile bezpośrednio wygenerowała przychodu z tytułu *najmu*.

**`GET /stats/machine-roi`**
```python
# Query: ?article_id=5&date_from=2026-01-01&date_to=2026-12-31

class MachineRoiResponse(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    total_rented_days: int
    estimated_revenue: Decimal    # Suma wartości z warunków przypisanych do najmu w tych umowach
    contracts_count: int          # W ilu umowach brała udział
```
*Opis algorytmu:* Pobierz wszystkie umowy, w których dany `article_id` widnieje, których daty trwania nakładają się na `[date_from, date_to]`. Zlicz przepracowane fizycznie dni i pomnóż przez wynegocjowane warunki z tych konkretnych umów.

### 2.3 Endpoint: Maszyny Obecnie Wynajęte

**Cel:** Szybka statystyka "ile i jakie maszyny pracują na ten moment u klientów".

**`GET /stats/currently-rented`**
```python
class CurrentlyRentedResponse(BaseModel):
    total_rented_count: int       # Ile łącznie maszyn
    total_owned_count: int        # Ile mamy wszystkich maszyn w bazie (nie usług)
    utilization_percentage: float # % wypożyczalności
    rented_articles: list[RentedArticleItem]

class RentedArticleItem(BaseModel):
    article_id: int
    name: str
    internal_number: str | None
    current_contract_number: str
    contractor_name: str
    return_date: date | None      # Kiedy planowany zwrot (date_to aktuanej umowy)
```
*Opis algorytmu:* Proste `SELECT` maszyn, które biorą udział w aktywnych umowach (`contracts.date_from <= CURDATE() AND contracts.date_to >= CURDATE()`).

### 2.4 Endpoint: Statystyki Pozycji Dodatkowych/Kosztów

**Cel:** Sumowanie opłat dodatkowych i usług za dany okres (od/do). Wyfiltrowanie kwot czysto za "transport", "mycie", "ładowanie akumulatorów" itp., które płaci klient, obok samych maszyn.

**`GET /stats/additional-fees`**
```python
# Query: ?date_from=2026-01-01&date_to=2026-03-31

class AdditionalFeesResponse(BaseModel):
    date_from: date
    date_to: date
    total_services_revenue: Decimal
    breakdown_by_service: list[ServiceRevenueItem]

class ServiceRevenueItem(BaseModel):
    article_id: int               # Pod warunkiem że usługi (mycie, transport) są artykułami gdzie is_service=true
    service_name: str
    total_revenue: Decimal
    times_billed: int             # Użyte np. na 10 umowach
```
*Opis algorytmu:* Sumujemy wartości pozycji na umowach, ale tylko tych, gdzie powiązany `articles.is_service = true` dla umów trwających w zadanym zakresie.

### 2.5 Statystyki Lokalizacji

**Cel:** Zestawienie, w jakich miastach / obszarach mamy najwięcej wynajmów. Odpowiada za dostawy.

**`GET /stats/locations`**
```python
# Query: ?date_from=2026-01-01&date_to=2026-12-31

class LocationStatItem(BaseModel):
    city: str
    postal_code: str | None
    rentals_count: int      # Ilość spisywanych umów/dostaw w danym mieście
    total_revenue: Decimal  # Wygenerowany obrót z danego miasta
```
*Opis algorytmu:* `GROUP BY delivery_address (lub contractor's city, zależnie czy zaimplementujemy w dostawach osobną kolumnę miasta)`. Sumuje liczbę umów oraz `total_value` per miejscowość w danym przedziale czasowym.

---

### Dashboard (Frontend)
Widok **Dashboard** w nowej aplikacji, obok list "Umowy", "Kontrahenci", musi zawierać dodatkową przestrzeń/zakładkę na **Statystyki / Raporty**, gdzie użytkownik będzie mógł generować powyższe dane we wprowadzonych ramach czasowych.
