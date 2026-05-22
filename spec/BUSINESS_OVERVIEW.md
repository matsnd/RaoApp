# RAO — Opis biznesowy aplikacji

**System zarządzania wynajmem maszyn budowlanych dla firmy Toolsmart Sp. z o.o.**

---

## 1. Czym jest RAO

RAO to nowoczesna aplikacja webowa zastępująca dotychczasowy desktopowy system (WinForms) używany do zarządzania wynajmem maszyn budowlanych. Aplikacja kompleksowo obsługuje cały cykl wynajmu: od pozyskania kontrahenta, przez przygotowanie umowy i protokołu zdawczo-odbiorczego, aż po analitykę rentowności floty.

**Użytkownicy:** handlowcy biurowi, księgowi, kadra zarządzająca.
**Dostęp:** przez przeglądarkę (zamiast tylko desktopu — zysk migracyjny).
**Jednoczesna obsługa:** ~10 użytkowników w firmie.

---

## 2. Główne moduły funkcjonalne

### 2.1 Kontrahenci (Klienci) — ✅ Zrealizowane

Centralna baza klientów wynajmujących maszyny.

- Pełna kartoteka kontrahenta (dane firmowe, adresowe, kontaktowe)
- **Integracja z GUS** — automatyczne pobieranie danych firmy po NIP-ie (jednym kliknięciem zamiast ręcznego przepisywania)
- **Walidacja NIP** (suma kontrolna) — eliminuje literówki przy wprowadzaniu
- Pole „reprezentowany przez" (osoba podpisująca umowę)
- Dedykowany **email do faktur** (zwiększa skuteczność dostarczania dokumentów księgowych)
- Wiele adresów dostawy per kontrahent

### 2.2 Maszyny (Artykuły) — ✅ Zrealizowane

Ewidencja floty sprzętu firmy.

- Kartoteka maszyny: marka, model, nr rejestracyjny, nr seryjny, **numer wewnętrzny ewidencyjny**, wartość odtworzeniowa
- Rozróżnienie: **maszyna fizyczna** vs **usługa** (np. transport, mycie, tankowanie)
- **Drzewiaste kategorie** (główna + 3 poziomy podkategorii) — czytelna nawigacja po flocie
- **Flaga „archiwalna"** — maszyny wycofane są ukrywane domyślnie, ale historia pozostaje
- Duplikacja maszyny jednym kliknięciem (przyspiesza dodanie nowego egzemplarza tego samego modelu)
- **Sprawdzanie dostępności** — system informuje, jeśli maszyna jest już wynajęta w wybranym terminie i na której umowie (eliminuje konflikty rezerwacji)

### 2.3 Umowy — ✅ Zrealizowane

Sercem systemu są umowy najmu / usługi.

- **Dwa typy umów:** Najem (S) i Usługa (U), z osobną automatyczną numeracją (`S001/2026`, `U002/2026`)
- **Pozycje umowy** — wiele maszyn / usług w jednej umowie
- **Elastyczny system stawek** (warunki rozliczeniowe):
  - Stawka jednorazowa (cena × ilość)
  - Stawka prosta (np. dzienna, tygodniowa)
  - **Stawki progowe** (np. „5000 zł/tydz. do 5 tygodni, potem 4000 zł/tydz.")
  - Częstotliwości: godzinowo / dziennie / tygodniowo / dwutygodniowo / miesięcznie / jednorazowo
- **Automatyczna kalkulacja wartości** umowy na podstawie warunków, dni najmu, częstotliwości
- **Strukturalny adres dostawy** — kod pocztowy (auto-uzupełniający miasto), miasto, pełny adres jako notatka — daje wiarygodne raporty geograficzne
- **Reverse geocoding (Nominatim/OpenStreetMap)** — kliknięcie na mapie wypełnia adres
- Pole „osoba kontaktowa na budowie", „adres dostawy", „dni pracy/tydzień", uwagi
- **Rezerwacja maszyn** — automatyczna blokada terminowa wynikająca z wprowadzonych umów
- **Panel rozliczenia umowy** — koszty po stronie klienta vs po stronie firmy, przedpłaty, faktury, pozostała kwota do zapłaty
- **Prowizje handlowców** liczone od realnego zarobku (po odjęciu kosztów firmy)

### 2.4 Dokumenty PDF — ✅ Zrealizowane

Profesjonalne wydruki — sześć wariantów dokumentów odpowiadających dotychczasowym wzorcom z WinForms.

| Dokument | Z kwotami | Bez kwot (dla kierowcy) |
|----------|-----------|-------------------------|
| Umowa Najmu | ✅ | — |
| Umowa Usługi | ✅ | — |
| Protokół Zdawczo-Odbiorczy Najmu | ✅ | ✅ |
| Protokół Zdawczo-Odbiorczy Usługi | ✅ | ✅ |

Funkcjonalności:
- **Pełna wizualna zgodność** z wydrukami z legacy (Crystal Reports → WeasyPrint) — klient nie odczuje różnicy
- **Ogólne Warunki Najmu (OWN)** zintegrowane jako kolejne strony PDF (zamiast doklejania osobnego pliku)
- **Pieczątka firmowa i podpis** automatycznie wstawiane w dokumentach
- **Tabela „Przy wydaniu / Przy odbiorze"** — pola do ręcznego wypełnienia (stan paliwa, kluczyki, czystość, dokumentacja zdjęciowa)
- **Ewidencja godzin operatora** w protokole usługi
- Sekcja **„Uwagi"** z warunkami doby najmu, zgłaszania zwrotu, dokumentacji
- **Rozdzielenie informacji**: adres dostawy i telefon widoczne tylko na protokole, ukryte na umowie
- Konfigurowalne foldery zapisu PDF (umowy / protokoły osobno)

### 2.5 Raporty i statystyki — ✅ Zrealizowane

Moduł dostarczający kadrze decyzyjnej rzeczywiste dane biznesowe (nowość względem legacy).

- **Rentowność maszyny (ROI)** — ile dni dany egzemplarz pracował, jaki wygenerował przychód, ROI vs wartość odtworzeniowa
- **Maszyny obecnie wynajęte** — szybki podgląd „co teraz pracuje u klienta" + wskaźnik wykorzystania floty
- **Statystyki kosztów dodatkowych / usług** — przychód z transportu, mycia, tankowania w okresie
- **Statystyki lokalizacyjne** — najbardziej dochodowe miasta/regiony (na podstawie strukturalnych kodów pocztowych)
- **Statystyki po kategoriach maszyn** — agregacja przychodu i wykorzystania per kategoria, drilldown na podkategorie
- **Filtrowanie**: zakres dat, kategoria, udźwig, archiwalne/aktywne, per rok/miesiąc
- **Stan aktualny floty** — co posiadamy, co pracuje, co stoi
- **Eksplorator** — krzyżowe widoki kontrahent ↔ umowa ↔ maszyna

### 2.6 Ustawienia firmowe — ✅ Zrealizowane

- Dane firmy (Toolsmart) widoczne na dokumentach
- **Logo firmy** w sidebar i nagłówkach PDF
- **Handlowcy** (z prowizjami)
- **Szablony usług dodatkowych** (zesłownikowane z artykułami) — drag & drop kolejność
- **Szablony cenników** (warunki rozliczeniowe wielokrotnego użytku)
- Konfiguracja folderów zapisu dokumentów

### 2.7 Bezpieczeństwo i konta — ✅ Zrealizowane

- Logowanie z JWT
- Role: admin / user (RBAC)
- **Wymuszenie zmiany hasła** przy pierwszym logowaniu po migracji (brak haseł plaintext)
- Zmiana hasła z poziomu sidebara
- Polityki RODO i retencji danych

### 2.8 Rozliczenia i raporty marżowe — 📋 Propozycje przyszłych raportów

**Kontekst:** Obecna implementacja rozliczeń (`ContractSettlement`) zawiera dane o kosztach po stronie klienta (`cost_client`) i firmie (`cost_company`), co pozwala na obliczenie **realnej marży**. To jest kluczowa wartość dodana migracji — legacy WinForms widział tylko fakturowanie, nie realne koszty.

**Dane dostępne:**
- `cost_client` — koszty po stronie klienta (faktury)
- `cost_company` — koszty po stronie firmy (paliwo, operator, serwis)
- `margin` — marża = cost_client - cost_company
- Integracja z Fakturownia (automatyczne pobieranie faktur)
- Prowizje handlowców liczone od realnego zarobku

---

#### Propozycje raportów biznesowych (priorytetyzowane)

| # | Raport | Dla | Priorytet | Opis biznesowy |
|---|--------|-----|-----------|----------------|
| **1** | **Marża realna vs fakturowana** | Kierownictwo | **HIGH** | "Ile *naprawdę* zarobiliśmy w tym miesiącu — nie ile zafakturowaliśmy." KPI: SUM(cost_client), SUM(cost_company), SUM(margin), margin %, trend MoM/YoY. **NOWOŚĆ** — legacy nie miał cost_company. |
| **2** | **Ranking handlowców wg marży** | Handlowcy + Kierownictwo | **HIGH** | "Mój bonus zależy od marży — chcę widzieć gdzie jestem względem celu i kolegów." KPI: marża/handlowiec, liczba umów, średnia marża na umowę. **NOWOŚĆ** — legacy liczył prowizje od obrotu. |
| **3** | **Top/Flop kontrahenci wg marży** | Kierownictwo + Handlowcy | **HIGH** | "Który klient generuje obrót, ale tak naprawdę na nim tracimy?" KPI: TOP 20 / BOTTOM 20 kontrahentów wg SUM(margin), flag dla margin < 0. Action: renegocjacja stawek. **NOWOŚĆ**. |
| **4** | **Umowy nierozliczone / niekompletne** | Księgowość | **HIGH** | "Które umowy zakończyły się ale nie mają wpisanego cost_company — czyli marża jest fałszywa?" KPI: liczba umów po date_to gdzie cost_company IS NULL. Worklist dla księgowej. **NOWOŚĆ** — data quality gate. |
| **5** | **Rentowność maszyny v2 (z cost_company)** | Operacje + Kierownictwo | MEDIUM | Rozszerzenie istniejącego ROI o kolumny: total_company_cost, real_margin, real_margin_per_rental_day. Action: maszyny z niskim real-ROI → sprzedaż/podniesienie stawki. |
| **6** | **Struktura kosztów własnych** | Księgowość + Operacje | MEDIUM | "Gdzie nam ucieka kasa — paliwo, operator, serwis?" KPI: SUM(cost_company) po typie service_fee, trend miesięczny. Wizualizacja: stacked bar chart. **NOWOŚĆ**. |
| **7** | **Marża po kategoriach maszyn** | Kierownictwo (decyzje inwestycyjne) | LOW | "W którą kategorię floty inwestować — koparki gąsienicowe czy kołowe?" KPI: SUM(margin) i margin % po category_main/sub1. Rozszerzenie istniejącego /stats/by-category. **NOWOŚĆ**. |

---

#### Rekomendowana kolejność implementacji

1. **#4 Umowy nierozliczone (data quality gate)** — najpierw, bo bez niego pozostałe raporty kłamią (garbage in / garbage out)
2. **#1 Marża realna vs fakturowana** — killer feature migracji, uzasadnia biznesowo całą zmianę
3. **#2 Ranking handlowców** — bezpośrednio wpływa na motywację (prowizje już są od margin)
4. **#3 Top/Flop kontrahenci** — trigger decyzji handlowych
5. **#5 Rentowność maszyny v2** — rozszerzenie istniejącego (2h)
6. **#6 Struktura kosztów** — wartościowe, ale nie blokujące
7. **#7 Marża po kategoriach** — strategiczne, decyzja raz na kwartał/rok

---

#### Czerwone flagi do walidacji przed implementacją

1. **Czy klient faktycznie wpisuje cost_company?** Jeśli pole jest 90% puste → raporty bezużyteczne. Najpierw raport #4 (hygiene), później reszta.
2. **RBAC dla #2 i #3** — handlowiec nie może widzieć cudzych marż per-deal. Należy zaprojektować z security agentem przed kodowaniem.
3. **NIE budować osobnego modułu raportów** — 4-5 widgetów na istniejącym Dashboard + 2-3 sub-taby w ReportsSection.vue.
4. **NIE robić eksportów Excel/PDF w v1** — odkładamy do P2. v1 = tabela + chart na ekranie.

---

#### Architektura techniczna (podsumowanie)

**Endpointy proponowane:** `/stats/profitability/*`
- `/stats/profitability/contracts` — lista umów z revenue, cost_client, cost_company, margin (paginacja)
- `/stats/profitability/by-contractor` — marża per kontrahent (TOP N)
- `/stats/profitability/by-salesperson` — marża + commission_amount per handlowiec
- `/stats/profitability/by-category` — marża per kategoria (rozszerzenie istniejącego)
- `/stats/profitability/by-period` — trend miesięczny (rozszerzenie istniejącego)
- `/stats/profitability/summary` — KPI dashboard tile
- `/stats/profitability/unsettled` — lista umów is_settled=False z data_to < today - X

**Indeksy DB wymagane:**
- `contracts`: date_range, salesperson, contractor, is_settled
- `contract_positions`: contract_id, article_id
- `contract_settlements`: contract_id, position_id
- `articles`: category_main, is_service, is_archival

**Decyzja biznesowa wymagana:** Definicja marży — `margin = revenue (calc) - cost_company` czy `margin = cost_client - cost_company`? Rekomendacja: **obie** jako `margin_estimated` (z calc) i `margin_realized` (z settlement).

---

## 3. Doświadczenie użytkownika (UX)

Funkcjonalności poprawiające codzienną pracę:

- ✅ **Filtrowanie umów po datach** w Dashboard (zamiast scrollowania)
- ✅ **Sortowanie umów** od najnowszych domyślnie
- ✅ **Kalendarz 2-miesięczny** w wyborze dat
- ✅ **Skróty klawiszowe** dla power-userów
- ✅ **Picker artykułów** z filtrem po typie umowy + duplikacja w locie
- ✅ **Auto-generowanie opisu warunku** (np. „stawka 5000 zł/tyg. do 5 tygodni")
- ✅ **Empty states z CTA** (przy pustych listach)
- ✅ **Globalny pasek postępu** podczas operacji
- ✅ **Drzewiasty picker kategorii**
- ✅ **Toast notifications** (potwierdzenia zapisu)

---

## 4. Migracja z legacy WinForms — feature parity

Zrealizowano pełną migrację funkcjonalną:
- ✅ Migracja danych historycznych (kontrahenci, maszyny, umowy, kategorie z CSV)
- ✅ Ustawienie maszyn z migracji jako archiwalnych domyślnie
- ✅ Wszystkie 6 typów dokumentów PDF zweryfikowanych wizualnie 1:1 z oryginałami WinForms
- ✅ Etykiety, pola i sekcje zgodne z oczekiwaniami klienta („NAJEMCA", „dni najmu", uwagi, OWN)

---

## 5. Status backlogu

| Priorytet | Liczba | Status |
|-----------|--------|--------|
| **P0** (production blockers) | 5 | ✅ Wszystkie ukończone |
| **P1** (must-have przed go-live) | ~30 | ✅ Wszystkie ukończone (1 superseded) |
| **P2** (ważne usprawnienia) | ~22 | ✅ Wszystkie ukończone (1 in-progress) |
| **P3** (nice-to-have) | ~13 | ✅ Wszystkie ukończone |

**Łącznie:** ~70+ zadań zrealizowanych w ostatnim cyklu.

### Aktualnie w toku (in-progress)
- **RAO-P2-021** — UX Raportów: kategorie jako pierwszy poziom + drilldown gridowy + oznaczenie danych historycznych (refinement już istniejących statystyk)

### Świadomie odłożone / niezrealizowane
- Powiadomienia email z linkiem reset hasła (P2 — workaround przez admina wystarcza)
- Ręczna rezerwacja maszyn — zastąpiona automatyczną z umów (RAO-P1-015 superseded)
- **Raporty marżowe** — propozycje w sekcji 2.8 (do realizacji w kolejnym cyklu, po walidacji jakości danych cost_company)

---

## 6. Wartość dla klienta

| Obszar | Wartość biznesowa |
|--------|-------------------|
| **Dostęp WWW** | Praca z dowolnego stanowiska zamiast tylko jednego desktopu |
| **GUS / NIP** | ~3 min/kontrahent zaoszczędzone na ręcznym przepisywaniu |
| **Sprawdzanie dostępności** | Eliminacja konfliktów wynajmu = brak reklamacji od klientów |
| **Statystyki ROI / kategorie / lokalizacje** | Decyzje zakupowe oparte na danych (nowość vs legacy) |
| **Strukturalne adresy + GUS** | Wiarygodne raporty geograficzne (legacy ich nie miał) |
| **PDF 1:1 z legacy** | Klienci końcowi nie odczują migracji — brak edukacji |
| **Prowizje od realnego zarobku** | Zdrowsza motywacja handlowców |
| **Drzewiaste kategorie** | Skalowalność floty bez chaosu |
| **Raporty marżowe (proponowane)** | Realna marża vs fakturowanie — decyzje biznesowe oparte na rzeczywistych kosztach (nowość vs legacy) |

---

## 7. Stan aplikacji — gotowość

**Aplikacja jest funkcjonalnie gotowa do produkcyjnego wdrożenia.** Wszystkie blockery (P0) i wymagania pre-go-live (P1) są ukończone. Pozostałe prace dotyczą polish UX (np. drilldown w raportach), nie blokują wdrożenia.

### Przyszłe prace — raporty marżowe

Sekcja 2.8 zawiera **propozycje raportów biznesowych opartych na rozliczeniach**, które mogą być zrealizowane w kolejnym cyklu rozwoju. Są to w 90% NOWE raporty, których legacy WinForms nie miał — kluczowa wartość dodana migracji to możliwość śledzenia **realnej marży** (cost_client - cost_company) zamiast tylko fakturowania.

**Kluczowa decyzja przed implementacją:** Czy klient faktycznie wpisuje `cost_company` w rozliczeniach? Jeśli pole jest 90% puste → najpierw raport #4 (umowy nierozliczone) jako data quality gate, pozostałe raporty po poprawie jakości danych.

---

## 8. Kontakt i wsparcie

W razie pytań dotyczących funkcjonalności lub zgłoszeń błędów, prosimy o kontakt:
- **Dokumentacja techniczna:** `spec/00_INDEX.md`
- **Backlog zadań:** `spec/backlog/BACKLOG.md`
- **Status wdrożenia:** patrz sekcja 5 powyżej

---

*Data utworzenia: 2026-05-22*
*Wersja: 1.0*
