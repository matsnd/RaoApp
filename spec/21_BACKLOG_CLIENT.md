# Backlog — Zgłoszenia i wymagania klienta

> **Przeznaczenie:** Lista zadań i uwag od klienta do realizacji  
> **Status:** Otwarty na nowe wpisy  
> **Ostatnia aktualizacja:** 2026-04-08

---

## Jak dodawać wpisy

Każde zgłoszenie powinno zawierać:
- **Co:** Opis funkcjonalności lub problemu
- **Priorytet:** Blokujący / Ważny / Dobry dodatek
- **Kontekst:** Gdzie w aplikacji (np. "Formularz umowy", "Dashboard")

---

## Lista zgłoszeń

| # | Zgłoszenie | Priorytet | Status | Uwagi |
|---|-----------|-----------|--------|-------|
| 1 | Adres dostawy — pole wielolinijkowe | Ważny | Oczekuje | Wymaga zmiany input → textarea + aktualizacji PDF protokołu |
| 3 | Kwota tankowania — zmiana default na 200,00 zł | Dobry dodatek | Oczekuje | Settings → default fee value |
| 4 | Adres dostawy — rozdzielenie umowa vs protokół | Ważny | Oczekuje | Ukryć na umowie, pokazać na protokole, umożliwić klientowi wpisanie własnego |
| 5 | Usługi dodatkowe — format wyświetlania kwot | Ważny | Oczekuje | Usunąć "$", dodać "zł" do wyświetlania kwot |
| 6 | Podpisy na umowie — układ stron | Ważny | Oczekuje | Podpisy tylko na ostatniej stronie, nie na pierwszej |
| 7 | Sekcja "Uwagi" w umowie — brakująca treść | Ważny | Oczekuje | Weryfikacja z kodem WinForms i dodanie do PDF |
| 8 | Picker artykułów — filtrowanie po typie umowy | Dobry dodatek | Oczekuje | Dla umowy usługi → tylko artykuły-usługi (is_service=true) |
| 9 | Protokół usługi — ewidencja godzin operatora | Ważny | ✅ Zrobione | Nowa tabela/functionality dla godzin od/do |
| 16 | Eksplorator — UX i filtrowanie | Ważny | ✅ Zrobione | Okres od-do, dynamiczne grupy usług, typeahead maszyn, auto-reload |
| 17 | Poprawa ekstrakcji miast z adresów dostawy | Blokujący | Oczekuje | delivery_address to pole wielolinijkowe - dane rozdrobnione w raportach lokalizacyjnych |

---

## Szczegóły zgłoszeń

### #1 — Adres dostawy — pole wielolinijkowe

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Adres dostawy w formularzu umowy powinien być bardziej czytelny. Aktualnie jest to jednolinijkowe pole tekstowe, co utrudnia wpisanie szczegółowych informacji o dojeździe.

**Kontekst:**
Formularz umowy (ContractFormView) — sekcja "Adres dostawy"

**Oczekiwane zachowanie:**
- Pole adresu dostawy jako textarea (wielolinijkowe)
- Możliwość wpisania adresu w formacie:
  ```
  Ul. Miedziana 15; Kraków
  (wjazd od ul. Warszawskiej)
  ```
- Taki sam format wyświetlania w protokole PDF

**Aktualne zachowanie:**
- Jednolinijkowe pole input
- Długi adres jest ucinany lub nieczytelny
- Brak możliwości dodania uwag o dojeździe

**Wymagane zmiany:**
1. Frontend: zmiana `<input>` na `<textarea rows="3">` w ContractFormView.vue
2. Backend: weryfikacja czy schema przyjmuje multiline (powinno działać bez zmian)
3. PDF: aktualizacja szablonu protokołu — adres jako blok tekstowy z zachowaniem nowych linii

**Załączniki:**
- [ ] Screenshot
- [ ] Mockup
- [x] Przykład formatowania: "Ul. Miedziana 15; Kraków (wjazd od ul. Warszawskiej)"

---

### #3 — Kwota tankowania — zmiana domyślnej wartości

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Dobry dodatek

**Opis:**
Zmiana domyślnej kwoty tankowania w szablonie usług dodatkowych z aktualnej na 200,00 zł.

**Kontekst:**
Ustawienia → Szablony usług / Usługi dodatkowe w umowie

**Oczekiwane zachowanie:**
- Defaultowa wartość dla nowych szablonów: 200,00 zł
- Dotyczy pola "Tankowanie" w service_fee_templates

**Aktualne zachowanie:**
- Aktualna defaultowa wartość jest inna (wymaga weryfikacji w kodzie)

**Wymagane zmiany:**
1. Sprawdzić aktualną wartość default w kodzie/settings
2. Zmienić na 200.00 w szablonie/migracji

---

### #4 — Adres dostawy — rozdzielenie wyświetlania umowa vs protokół

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Adres dostawy nie powinien być widoczny na dokumencie umowy. Powinien się wyświetlać tylko na protokole. Numer telefonu wpisany w formularzu niech będzie widoczny tylko na protokole. Na umowie klient powinien mieć możliwość samodzielnego wpisania danych.

**Kontekst:**
PDF Umowy vs PDF Protokołu — sekcja adresowa

**Oczekiwane zachowanie:**
- **PDF Umowy:** 
  - Ukryty adres dostawy z formularza
  - Puste pole lub pole do wpisania ręcznego przez klienta
- **PDF Protokołu:**
  - Widoczny adres dostawy z formularza
  - Widoczny numer telefonu z formularza

**Aktualne zachowanie:**
- Adres dostawy pojawia się zarówno na umowie jak i na protokole
- Numer telefonu jest widoczny w obu dokumentach

**Wymagane zmiany:**
1. Szablony PDF (Jinja2):
   - `contract.html` — usunąć/sekcja adres dostawy
   - `protocol.html` — pozostawić adres dostawy
2. Rozważyć dodanie osobnego pola "Adres na umowie" (opcjonalny, ręczny)
3. Sprawdzić gdzie dokładnie pokazuje się nr tel — czy to pole kontaktowe czy dostawy

**Załączniki:**
- [x] Screenshot sekcji "na budowie" z protokołu
- [ ] Mockup pożądanego układu

---

### #5 — Usługi dodatkowe — poprawa formatu wyświetlania kwot

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
W liście usług dodatkowych pojawiają się symbole "$1", "$2" zamiast rzeczywistych kwot. Brakuje symbolu waluty "zł" przy kwotach.

**Kontekst:**
PDF Umowy/Protokół — sekcja "Inne usługi" / "Usługi dodatkowe"

**Oczekiwane zachowanie:**
- Zamiast "$1 zł" → wyświetlać faktyczną kwotę np. "150,00 zł"
- Zamiast "$2 zł" → wyświetlać faktyczną kwotę np. "400,00 zł"
- Format: "{nazwa usługi}: {kwota_from} zł - {kwota_to} zł"
- Przykład: "Tankowanie: 150,00 zł (plus koszt paliwa)"

**Aktualne zachowanie:**
- Wyświetla się: "Tankowanie (- Usługa tankowania: $1 zł (plus koszt paliwa)): 150,00"
- Symbole "$1", "$2" nie są zamieniane na wartości
- Brak spójności formatu kwot

**Wymagane zmiany:**
1. Szablon PDF (Jinja2) — sekcja usługi dodatkowe:
   - Zamiana placeholderów $1, $2 na wartości z `amount_from`, `amount_to`
   - Dodanie suffixu " zł" po każdej kwocie
   - Usunięcie powtórzeń w opisie
2. Sprawdzić czy problem dotyczy tylko PDF czy też UI w aplikacji

**Załączniki:**
- [x] Screenshot sekcji "Inne usługi" z widocznymi "$1", "$2"

---

### #6 — Podpisy na umowie — układ stron

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Na pierwszej stronie umowy nie powinno być podpisów. Podpisy mają się znajdować tylko na ostatniej stronie dokumentu umowy.

**Kontekst:**
PDF Umowy — układ stron, sekcja podpisów

**Oczekiwane zachowanie:**
- **Pierwsza strona umowy:** 
  - Nagłówek z danymi firmy (TOOLSMART)
  - Dane umowy, pozycje, warunki
  - BEZ sekcji podpisów
- **Ostatnia strona umowy:**
  - Sekcja podpisów: "czytelny podpis Wynajmującego" i "czytelny podpis Najemcy"
  - Dane handlowca (opcjonalnie)

**Aktualne zachowanie:**
- Podpisy pojawiają się na pierwszej stronie (jak widać na załączniku)
- Nie jest to standardowy układ umowy — podpisy powinny być na końcu

**Wymagane zmiany:**
1. Szablon PDF (Jinja2) `contract.html`:
   - Usunąć sekcję podpisów z pierwszej strony
   - Dodać sekcję podpisów na końcu dokumentu (ostatnia strona)
   - Upewnić się że podpisy nie dzielą się między stronami (CSS `page-break-inside: avoid`)
2. Sprawdzić czy protokół ma poprawny układ podpisów (powinien być na końcu)

**Załączniki:**
- [x] Screenshot pierwszej strony z widocznymi podpisami u góry

---

### #7 — Sekcja "Uwagi" w umowie — brakująca treść

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
W umowie PDF brakuje sekcji "Uwagi" zawierającej ważne informacje o warunkach wynajmu. Sekcja ta była obecna w starej aplikacji i musi zostać odtworzona.

**Kontekst:**
PDF Umowy — sekcja "Uwagi" (zazwyczaj na końcu dokumentu, przed podpisami)

**Oczekiwane zachowanie:**
Sekcja "Uwagi" powinna zawierać:
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godzin pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, minimum z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: {wartość z formularza, domyślnie 6}
- Dokumentacja zdająca: wykonano

Przykład formatowania:
```
Uwagi:
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godzin pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: 6
- dokumentacja zdająca: wykonano
```

**Aktualne zachowanie:**
- Sekcja "Uwagi" nie pojawia się w generowanym PDF umowy
- Dane te są prawdopodobnie obecne w formularzu (pole `working_days_per_week`) ale nie są wyświetlane w PDF

**Wymagane zmiany:**
1. **Weryfikacja w kodzie WinForms** — znaleźć w FormU4.cs lub szablonach Crystal Reports skąd pochodziła ta sekcja
2. Szablon PDF (Jinja2) `contract.html`:
   - Dodać sekcję "Uwagi" przed podpisami (na ostatniej stronie)
   - Użyć danych z formularza: `working_days_per_week` (dni pracy w tygodniu)
   - Pozostałe punkty to stały tekst szablonu
3. Sprawdzić czy pole `working_days_per_week` jest poprawnie przekazywane do szablonu

**Załączniki:**
- [x] Screenshot sekcji "Uwagi" ze starej umowy

---

### #8 — Picker artykułów — filtrowanie po typie umowy

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Dobry dodatek

**Opis:**
Podczas tworzenia umowy typu "Usługa" (U), w pickerze artykułów powinny wyświetlać się wyłącznie artykuły oznaczone jako usługi (`is_service = true`), a nie sprzęt do wynajmu. Ułatwi to wybór odpowiednich pozycji.

**Kontekst:**
Formularz umowy → Dodaj pozycję → Picker artykułów

**Oczekiwane zachowanie:**
- **Umowa typu "Najem" (S):** Picker pokazuje artykuły z `is_service = false` (sprzęt)
- **Umowa typu "Usługa" (U):** Picker pokazuje artykuły z `is_service = true` (usługi)
- Dodatkowo: badge/label w pickerze wskazujący typ artykułu

**Aktualne zachowanie:**
- Picker pokazuje wszystkie artykuły niezależnie od typu umowy
- Klient musi ręcznie szukać odpowiednich pozycji

**Wymagane zmiany:**
1. Frontend: `ContractFormView.vue` — picker artykułów
   - Przekazać parametr `contract_type` do API artykułów
   - Lub filtrować client-side po załadowaniu listy
2. Backend (opcjonalnie): `GET /articles` — dodać parametr `is_service` do filtrowania
3. UI: Dodanie badge'ów "Usługa" / "Sprzęt" w liście artykułów

**Weryfikacja:**
- Pole `is_service` istnieje w tabeli `articles` (potwierdzone w DDL)
- Badge dla usług już istnieje w pickerze (weryfikacja z kodu)

---

### #9 — Protokół usługi — ewidencja godzin operatora

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Protokół usługi (inny niż protokół najmu) musi umożliwiać ewidencję godzin pracy operatora. Dla każdego dnia wykonania usługi należy zapisać godzinę rozpoczęcia i zakończenia pracy.

**Kontekst:**
PDF Protokół usługi — sekcja "Data wykonania usługi" z tabelą godzin

**Oczekiwane zachowanie:**
- Tabela w protokole usługi z kolumnami:
  - Data (dd.mm.yyyy)
  - Od (godzina)
  - Do (godzina)
  - Uwagi (opcjonalnie)
- Możliwość wpisania wielu dni dla jednej pozycji usługi
- Przykład z załącznika:
  ```
  30.03.2026 | 8   | 17
  31.03.2026 | 7   | 17
  1.04.2026  | 7   | 16:30
  2.04.2026  | 7   | 16
  3.04.2026  | 7   | 12
  ```

**Aktualne zachowanie:**
- Brak możliwości ewidencji godzin w protokole usługi
- Tabela `settlements` istnieje w DDL ale nie ma funkcjonalności (była tylko cache'm technicznym w starym systemie)
- Wymaga nowej tabeli lub rozszerzenia obecnej logiki

**Wymagane zmiany:**
1. **Weryfikacja w kodzie WinForms** — znaleźć czy stary system miał taką funkcjonalność (prawdopodobnie nie, to nowe wymaganie)
2. **Schemat DB:** Nowa tabela `service_hours` lub rozszerzenie `settlements`:
   - `id`, `position_id`, `date`, `time_from`, `time_to`, `notes`
3. **Backend:** Nowe endpointy CRUD dla godzin usługi
4. **Frontend:** Nowy komponent w `ContractFormView` dla umów typu "U" — tabela godzin
5. **PDF:** Nowy szablon lub modyfikacja protokołu usługi z sekcją godzin

**Załączniki:**
- [x] Zdjęcie protokołu usługi z ręcznie wpisanymi godzinami

---

### #10 — UX Raportów — rozdzielenie "teraz" od "okres"

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Aktualnie w sekcji raportów pokazuje się "Wynajętych teraz" obok filtrów datowych. Użytkownik myśli że wybór przedziału czasowego wpływa na tę liczbę, co jest mylące.

**Oczekiwane zachowanie:**
- Jasne rozdzielenie sekcji "Stan aktualny" (niezależnie od daty) od "Analiza historyczna" (zależnie od daty)
- Sekcja "Stan aktualny" powinna być wizualnie wyodrębniona (np. inne tło, nagłówek)
- Daty powinny wpływać tylko na dane historyczne (przychód, trendy, top maszyn)

**Wymagane zmiany:**
1. `ReportsSection.vue` — wizualna separacja sekcji "Stan aktualny"
2. `statsStore.js` — nowy endpoint `/stats/current-status` (niezależnie od dat)
3. Backend — endpoint zwracający zawsze aktualny stan floty

---

### #11 — Numer wewnętrzny maszyny — widoczność i wyszukiwanie

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Pole `internal_number` już istnieje w tabeli `articles`, ale nie jest widoczne w formularzach ani w raportach. Klient potrzebuje identyfikować maszyny po numerach wewnętrznych (np. "TS-042") dla celów operacyjnych i raportowania.

**Oczekiwane zachowanie:**
- Widoczność nr wewnętrznego w formularzu artykułu
- Wyszukiwanie po nr wewnętrznym w article pickerze
- Wyświetlanie nr wewnętrznego w raportach i statystykach
- Możliwość filtrowania raportów per konkretna maszyna (po nr wewnętrznym)

**Wymagane zmiany:**
1. `ArticleFormView.vue` — dodanie pola internal_number
2. `ArticlePicker.vue` — wyszukiwanie po internal_number
3. `ReportsSection.vue` — filtr "Szukaj maszyny" po nr wewnętrznym
4. Backend — endpoint `/stats/machine/{internal_number}`

---

### #12 — Statystyki per maszyna (ROI, wykorzystanie)

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Normalny

**Opis:**
Klient potrzebuje sprawdzać rentowność (stopę zwrotu) dla konkretnych maszyn. Ile dana maszyna była wynajmowana w danym okresie (miesiąc/3miesiące/rok).

**Oczekiwane zachowanie:**
- Po wyborze maszyny (po nr wewnętrznym) pokazują się statystyki:
  - Okres analizy (np. 3 miesiące)
  - Całkowity przychód z maszyny w okresie
  - Liczba dni wynajmu
  - Średni przychód/dzień wynajmu
  - Procent wykorzystania w okresie

**Wymagane zmiany:**
1. Backend — endpoint `/stats/machine/{id}/history?from=&to=`
2. `ReportsSection.vue` — panel szczegółów maszyny
3. Ewentualnie wykres wykorzystania w czasie

---

### #13 — Filtrowanie pozycji umowy po typie

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Normalny

**Opis:**
W raportach klient chce widzieć nie tylko maszyny, ale też podsumowanie pozycji dodatkowych: transport, ładowanie akumulatorów, mycie, itp. — zsumowane za dane okresy.

**Oczekiwane zachowanie:**
- Filtr "Typ pozycji" w raportach: Maszyny | Usługi | Wszystkie
- Podsumowanie przychodu z usług dodatkowych osobno
- Lista najczęściej wykonywanych usług dodatkowych

**Wymagane zmiany:**
1. Backend — `/stats/positions?type=&from=&to=`
2. `ReportsSection.vue` — filtry typu pozycji
3. Tabela/usług dodatkowych w raporcie

---

### #14 — Statystyki po lokalizacji/miejscowości

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Normalny

**Opis:**
Klient chce analizować gdzie najczęściej wynajmują maszyny (miejscowości/obszary) aby lepiej planować logistykę.

**Oczekiwane zachowanie:**
- Filtrowanie raportów po miejscowości (z adresu dostawy)
- Podsumowanie: ilość wynajmów w danej lokalizacji
- Mapa lub lista top lokalizacji

**Wymagane zmiany:**
1. Backend — `/stats/locations/detail?city=&from=&to=`
2. Frontend — filtr miejscowości w raportach
3. Lista/heatmap lokalizacji

---

### #15 — Rezerwacja maszyn (blokada wynajmu)

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
System musi umożliwiać rezerwację maszyn na przyszłe terminy. Maszyna zablokowana w rezerwacji nie może być wynajęta w tym okresie. Przy próbie wynajmu pokazuje się informacja kiedy maszyna będzie dostępna.

**Oczekiwane zachowanie:**
- Rezerwacja maszyny na konkretny przedział dat (przyszły)
- Blokada wynajmu jeśli maszyna jest zarezerwowana
- W pickerze artykułów: badge "Zarezerwowana do DD.MM.YYYY"
- Informacja kiedy maszyna będzie dostępna przy próbie wynajmu zablokowanej

**Wymagane zmiany:**
1. **DB:** Nowa tabela `article_reservations` (opcjonalnie — można użyć istniejących umów jako "soft reservation")
2. **Backend:** API rezerwacji, walidacja konfliktów dat
3. **Frontend:** Formularz rezerwacji, badge w pickerze, walidacja dostępności

---

### #16 — Eksplorator — UX i filtrowanie

**Zgłaszający:** Klient  
**Data:** 2026-04-08  
**Priorytet:** Ważny

**Opis:**
Eksplorator raportów wymagał gruntownej przebudowy UX. Aktualny interfejs był mylący i nieintuicyjny — okresy nie działały poprawnie, usługi miały hardcoded chipy niepasujące do danych, a maszyny miały dropdown z 100+ pozycjami.

**Kontekst:**
Raporty → Eksplorator — wszystkie 4 sub-taby (Wszystko, Maszyny, Usługi, Lokalizacje)

**Oczekiwane zachowanie:**
- **Okresy:** Pills preset (miesiąc/kwartał/rok/wszystko) + "📅 Własny" z dwoma inputami date (od-do)
- **Usługi:** Dynamiczne grupy z rzeczywistych danych, nie hardcoded "transport/mycie/tankowanie"
- **Maszyny:** Jeden typeahead search z dropdownem wyników, nie dropdown + osobne szukanie
- **Auto-reload:** Zmiana okresu ma natychmiast odświeżyć dane w aktywnym tabie (bez klikania "Szukaj")

**Aktualne zachowanie przed zmianą:**
- Dropdown z presetami okresów, brak custom od-do
- Usługi: hardcoded chips (transport, mycie, tankowanie) które nie istnieją w DB
- Maszyny: dropdown 100+ pozycji + osobne pole search = nieczytelne
- Lokalizacje/Usługi nie reagowały na zmianę okresu (wymagany klik "Szukaj")

**Wymagane zmiany:**
1. **Period selector:** Pills + custom date inputs + auto-reload
2. **Service groups:** Dynamiczne grupy z danych (ładowarki teleskopowe, wózki widłowe, żurawie/HDS, etc.)
3. **Machine search:** Typeahead z wynikami, klik = ładuj detale
4. **Auto-reload:** `onExplorerPeriodChange()` dla wszystkich tabów

**Zrealizowane:**
✅ Pills preset + custom date inputs (type=date)  
✅ Dynamiczne service groups z licznikami  
✅ Typeahead search maszyn z wynikami  
✅ Auto-reload na zmianę okresu  
✅ Weryfikacja Playwright (0 błędów)

**Załączniki:**
- [x] Weryfikacja Playwright: Lokalizacje, Usługi, Maszyny, Własny okres

---

### #17 — Poprawa ekstrakcji miast z adresów dostawy

**Zgłaszający:** Zespół deweloperski  
**Data:** 2026-04-09  
**Priorytet:** Blokujący

**Problem:**
Pole `delivery_address` w bazie danych zawiera wielolinijkowe adresy z szczegółowymi instrukcjami dojazdu, co powoduje rozdrobnienie danych w raportach lokalizacyjnych. Ekstrakcja samych miast jest trudna i zawodna.

**Kontekst:**
Raporty → Eksplorator → Lokalizacje — agregacja danych po miastach

**Przykładowy zawartość `delivery_address`:**
```
Warszawa, ul. Krakowska 12
Brama od ulicy Pawiej, dzwonek #3
II piętro, pokój 23
Informacje dla kierowcy: wjazd od godziny 8:00
```

**Aktualne zachowanie:**
- Funkcja `extract_city()` próbuje wyciągać miasta z takich wielolinijkowych adresów
- To samo miasto jest traktowane jako różne lokalizacje:
  - "Warszawa"
  - "Warszawa, Brama od ulicy Pawiej"
  - "Warszawa Krakowska 12 Brama"
- Raporty lokalizacyjne są nieczytelne i rozdrobnione

**Oczekiwane zachowanie:**
- Spójne nazwy miast w raportach niezależnie od formatu adresu
- Możliwość wyboru miasta z autocomplete (jak przy kontrahentach)
- Zachowanie pełnego adresu dostawy dla logistyki

**Propozycja rozwiązania (3 fazy):**

**Faza 1 - Ulepszenie ekstrakcji (natychmiast):**
- ✅ Ulepszona funkcja `extract_city()` z priorytetyzacją znanych miast
- ✅ Lepsze wykrywanie i ignorowanie instrukcji dojazdu
- ✅ Testy: 16/22 przypadków poprawnych (73% skuteczności)

**Faza 2 - Migracja bazy danych (krótkotermin):**
```sql
-- Dodanie dedykowanej kolumny
ALTER TABLE contract ADD COLUMN city VARCHAR(100);

-- Wypełnienie danymi (użycie ulepszonej funkcji)
UPDATE contract SET city = extract_city(delivery_address);

-- Indeks dla wydajności
CREATE INDEX idx_contract_city ON contract(city);
```

**Faza 3 - Autocomplete miast (średniotermin):**
- Nowy endpoint: `GET /contracts/cities?search=warsz`
- Wykorzystanie istniejących miast z `contractor_addresses.city`
- Modal picker identyczny jak przy kontrahentach
- Możliwość dodawania nowych miast "on-the-fly"

**Backend endpoint proposal:**
```python
@router.get("/cities")
async def get_cities(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get unique cities for autocomplete"""
    # Z adresów kontrahentów (już dostępne)
    query = select(ContractorAddress.city).distinct()
    query = query.where(ContractorAddress.city.isnot(None))
    
    if search and len(search) >= 2:
        query = query.where(ContractorAddress.city.ilike(f"%{search}%"))
    
    query = query.order_by(ContractorAddress.city).limit(50)
    result = await db.execute(query)
    cities = [row[0] for row in result.fetchall()]
    
    return {"cities": cities}
```

**Frontend implementation:**
- Modal picker z debounced search (300ms delay)
- Taki sam interfejs jak picker kontrahentów
- Opcja "Dodaj nowe miasto" jeśli nie ma na liście

**Wymagane zmiany:**
1. **Backend:**
   - `contracts/models.py` - dodanie `city: Column(String(100))`
   - `contracts/router.py` - endpoint `/cities`
   - Migration script do wypełnienia danych
2. **Frontend:**
   - `ContractFormView.vue` - city picker modal
   - Formularz umowy: pole "Miasto" + textarea "Adres dostawy"
3. **Eksplorator:**
   - Agregacja po `contract.city` zamiast `extract_city(delivery_address)`

**Korzyści:**
- ✅ Spójne dane w raportach lokalizacyjnych
- ✅ Lepsza wydajność (brak ekstrakcji przy każdym zapytaniu)
- ✅ Możliwość ręcznej korekty błędnych miast
- ✅ Znany interfejs użytkownika (picker jak kontrahenci)

**Ryzyka:**
- Migracja bazy danych wymaga downtime'u
- Konieczność aktualizacji istniejących umów
- Potrzebne testy wydajności przy dużych wolumenach

**Status realizacji:**
- ✅ Faza 1: Ulepszenie `extract_city()` - zrobione
- ⏳ Faza 2: Migracja bazy - oczekuje na decyzję klienta
- ⏳ Faza 3: Autocomplete - zależne od migracji

---

## Historia zmian

| Data | Zmiana | Autor |
|------|--------|-------|
| 2026-04-08 | Utworzenie pliku backlogu | Zespół |
| 2026-04-08 | Dodanie zgłoszeń #10-#15 (raporty, rezerwacje) | Zespół |
| 2026-04-09 | Zrealizowanie #16 — Eksplorator redesign UX | Zespół |
| 2026-04-09 | Dodanie #17 — Poprawa ekstrakcji miast z adresów dostawy | Zespół |

