# RAO Backlog — Nowy sprint

> **Status:** Uwagi klienta wciągnięte (2026-07-08)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260705_20260708.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem
> **Źródło uwag:** `temp/uwagi klienta/ROA - uwagi.md` (15 uwag + 1 notatka o statystykach)

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`

---

## 🚨 P0 — Production Blockers
*(brak)*

---

## 🔴 P1 — Must-Have (uwagi klienta 2026-07-08)

### P1-001: Odhaczenie czy maszyna nasza czy zewnętrzna

```yaml
id: P1-001
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 1)
component: frontend/ContractFormView + backend/contracts
```

**Opis:** Możliwość odhaczenia (checkbox) czy maszyna jest nasza (własna firmy) czy zewnętrzna (podnajem od innej firmy).

**Implementacja:** Checkbox w inline article form + kolumna "Zewnętrzna" w Article picker modal (badge ✓/—). Backend pole `is_external` już istnieje w `articles` table.

---

### P1-002: Ręczne dodawanie adresu

```yaml
id: P1-002
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 2)
component: frontend/ContractFormView + integrations/GUS-Nominatim
```

**Opis:** Możliwość dodawania adresu ręcznie, jeśli system nie zaciągnie po adresie/kodzie pocztowym, lub jeśli będzie potrzeba dopisania szczegółów (np. numer działki, bramka, dodatkowe wskazówki dojazdu).

**Implementacja:** Checkbox "Ręczny adres (wyłącz auto-fill z PNA/Nominatim)" w sekcji Adres dostawy. Gdy zaznaczony → pola postal_code/city disabled, auto-fill z PNA/Nominatim skipowane.

---

### P1-003: Wybór liczby dni wynajmu w tygodniu (5/6/7)

```yaml
id: P1-003
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 3)
component: frontend/ContractFormView + backend/contracts + backend/settlements
```

**Opis:** Możliwość liczenia wynajmu 5, 6 lub 7 dni w tygodniu — operator wybiera przy tworzeniu umowy. Obecnie system liczy stałą liczbę dni; klient potrzebuje elastyczności (niektóre umowy 5 dni/tyg, inne 6 lub 7).

**Implementacja:** Segmented control 5/6/7 (inline buttons) w ContractFormView. Backend pole `working_days_per_week` już istnieje.

---

### P1-004: Zapis o naliczaniu dni w tyg. i weekendach z GPS

```yaml
id: P1-004
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 4)
component: frontend/ContractFormView (sekcja Uwagi) + backend/reports (PDF umowy)
```

**Opis:** Dodać zapis do naliczania, ile dni w tygodniu i weekendy z GPS. Zmienić brzmienie zapisu w sekcji Uwagi na umowie na:

> „Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)”

**Kontekst z obrazka (image1 — skan sekcji Uwagi z obecnej umowy):**
Obecna sekcja Uwagi na umowie zawiera:
```
Uwagi
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
- Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)
- dokumentację zdjęciową: wykonano
```
Klient zaznaczył na czerwono linię „Naliczanie: 5 dni w tygodniu (pozostałe dni według zapisu GPS)" — to jest docelowe brzmienie, które ma się pojawiać na umowach.

Tabela główna umowy: kolumny „Przewidywana ilość dni najmu | Wartość odtworzeniowa | Rozliczenie", przykładowy wiersz: „2 | 261 000,00 | 215,00 zł / doba".

**Implementacja:** Zmiana brzmienia w contract.html sekcja Uwagi: "Naliczanie: {working_days_per_week} dni w tygodniu (pozostałe dni według zapisu GPS)".

---

### P1-005: Uproszczenie wybierania widełek cenowych

```yaml
id: P1-005
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 5)
component: frontend/ConditionPanel + backend/contracts (warunki rozliczeniowe)
```

**Opis:** Uprościć proces wybierania widełek cenowych. Obecnie system ma sztywne przedziały; klient potrzebuje:
- **Wynajem:** możliwość edycji okresu widełek, np. 1-2, 1-3, 1-4, 4-7, 4-8, powyżej 16 dni, powyżej 20 dni itp. — operator definiuje przedziały
- **Usługa:** np. do 2h, do 3h (podstawa) — również konfigurowalne

Klient chce elastycznego definiowania widełek zamiast sztywnych dropdown-ów.

**Implementacja:**
- Backend: position_conditions dodane kolumny period_from/period_to (INT NULL) + migration
- Frontend: ConditionPanel nowe kolumny Od/Do w tabeli + modal form + walidacja ciągłości + podgląd PDF live
- Commit: 72ce2c3

**Scenariusze testowe:** `e2e/tests/SCENARIOS_P1-005_elastyczne_widelki.md` (12 scenariuszy)

---

### P1-006: Dwa warianty zapisów w umowie — diesel vs elektryk

```yaml
id: P1-006
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 6)
component: frontend/ContractFormView + backend/contracts + backend/reports (PDF) + backend/articles
```

**Opis:** Chcemy mieć możliwość dodania dwóch różnych wariantów sekcji „Inne usługi" na umowie, w zależności od typu maszyny (diesel vs elektryk). Wybór przez operatora (Patrycję).

**Wariant A — maszyny dieslowe:**
Sekcja „Inne usługi" na umowie (z image2):
```
Inne usługi
- Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór
- Przegląd techniczny i czyszczenie maszyny: 150,00 zł
- Czyszczenie maszyny (zabrudzenia ponadnormatywne): wycena indywidualna
- Usługa tankowania: 200,00 zł (plus koszt paliwa)
- Ponadnormatywny przestój transportu: 200,00 zł / h - 300,00 zł / h
- Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)
```
Domyślna kwota przeglądu dla diesli: **150,00 zł**

**Wariant B — maszyny elektryczne:**
Sekcja „Inne usługi" na umowie (z image3):
```
Inne usługi
- Transport: 1 200,00 zł dostawa / 1 200,00 zł odbiór
- Przegląd techniczny, ładowanie akumulatorów oraz czyszczenie maszyny: 90,00 zł
- Czyszczenie maszyny (zabrudzenia ponadnormatywne): wycena indywidualna
- Usługa tankowania: 200,00 zł (plus koszt paliwa)
- Ponadnormatywny przestój transportu: 200,00 zł / h - 300,00 zł / h
- Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)
```
Domyślna kwota przeglądu dla elektryków: **90,00 zł** *(uwaga: w tekście uwagi jest 35,00 zł, ale klient poprawił na 90,00 zł w dopisku — „dla elektryków 90")*

**Kluczowe wymagania:**
- Głównie chodzi o górną pozycję (przegląd techniczny + czyszczenie) — różna treść i kwota dla diesla vs elektryka
- Kwoty czyszczenia maszyn itp. muszą być **do edycji** (nie sztywne)
- Domyślnie pojawiają się jak powyżej: diesel 150 zł, elektryk 90 zł
- Pozostałe pozycje (transport, tankowanie, przestój, serwis) wspólne dla obu wariantów

**Implementacja:** Seed Diesel/Elektryk presetów w backend/main.py (idempotentny po nazwie). Dropdown inline w ContractFormView. OWN 8b zaktualizowany w contract.html.

---

### P1-007: Miejsce na dodatkowe informacje na protokole usług

```yaml
id: P1-007
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 7)
component: frontend/ProtocolForm + backend/reports (PDF protokołu)
```

**Opis:** Dodać miejsce zapisu dodatkowych informacji na protokole dla usług. Umiejscowienie: nad górnymi polami do podpisu (nad pieczątką) — tak jak ustalano z klientem.

**Implementacja:** Dodatkowe pole "Dodatkowe informacje" w protocol_zo_u.html (nad podpisami). Wypełniane z contract.notes.

---

### P1-008: „Przewidywana ilość dni najmu" w dwóch linijkach

```yaml
id: P1-008
status: done
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 8)
component: frontend/ContractFormView + backend/reports (PDF umowy)
```

**Opis:** Zmienić nagłówek kolumny „Przewidywana ilość dni najmu" tak, żeby łamał się na dwie linijki:
```
Przewidywana
ilość dni najmu
```

**Implementacja:** `white-space:normal` w contract.html nagłówek kolumny.

**Kontekst z obrazka (image4 — skan tabeli z umowy):**
Obecnie nagłówek kolumny jest w jednej linii i się nie mieści. Kolumna jest zaznaczona czerwoną ramką przez klienta. Tabela ma kolumny: „Przedmiot najmu | Przewidywana ilość dni najmu | Wartość | Wartość odtworzeniowa". Przykładowy wiersz: „Ładowarka teleskopowa obrotowa 3,2t | 1 | 590 000,00 | 1 000 – 3000,00 / doba".

---

### P1-009: Opiekun zamówienia na protokole

```yaml
id: P1-009
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 9)
component: frontend/ProtocolForm + backend/protocols + backend/reports (PDF)
```

**Opis:** Opiekun zamówienia na każdym protokole (wynajem i usługa) — imię i nazwisko oraz nr telefonu. Dodać dedykowaną przestrzeń na dole lub na górze protokołu z tymi informacjami.

---

### P1-010: Usunięcie pieczątki przy zwrocie na protokole

```yaml
id: P1-010
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 10)
component: backend/reports (PDF protokołu) + frontend/ProtocolForm
```

**Opis:** Usunąć pieczątkę firmy przy zwrocie na protokole. Pieczątka ma zostać tylko przy wydaniu (jeśli jest), przy zwrocie ma nie być.

---

### P1-011: Osobny protokół dla każdej maszyny

```yaml
id: P1-011
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 11)
component: backend/protocols + backend/reports (PDF) + frontend/ProtocolForm
```

**Opis:** Utworzyć każdy oddzielny protokół do każdej maszyny, jeśli na umowie jest więcej niż jedna maszyna. Każdy protokół ma być powiązany z jedną umową ale dotyczyć jednej maszyny. Obecnie protokół prawdopodobnie grupuje wszystkie maszyny z umowy — klient chce osobny PDF per maszyna.

---

### P1-012: Nr telefonu klienta tylko na protokole, nie na umowie

```yaml
id: P1-012
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 12)
component: backend/reports (PDF umowy + PDF protokołu)
```

**Opis:** Numer telefonu klienta ma się wyświetlać **tylko na protokole**. Na umowie najmu mają być puste pola na telefon — ten numer ma wypełnić klient ręcznie wypełniając umowę (papierową).

---

### P1-013: Eliminacja nr wewnętrznego przy tworzeniu usługi

```yaml
id: P1-013
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 13)
component: frontend/ContractFormView (tryb usługa) + backend/contracts
```

**Opis:** Nr wewnętrzny przy tworzeniu usługi wyeliminować — pole nie powinno się pojawiać lub nie być wymagane w trybie usługi.

---

### P1-014: Przedpłata na umowie — lepsza pozycja

```yaml
id: P1-014
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 14)
component: frontend/ContractFormView + backend/reports (PDF umowy)
```

**Opis:** Przedpłata na umowie przesunąć na dół lub w inne bardziej pasujące miejsce niż obecnie (na górze pod tytułem). Klient uważa obecne umiejscowienie za nieintuicyjne.

---

### P1-015: Zmiana punktu 8 b) w OWN (Ogólne Warunki Najmu)

```yaml
id: P1-015
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 15)
component: backend/reports (PDF umowy — sekcja OWN) + backend/settings (szablony OWN)
```

**Opis:** Zmiana jednego punktu w zapisach na umowie (OWN) — zmiana punktu 8. b).

**Obecny tekst (z image5 — skan dokumentu OWN z żółtym highlighterem na punkcie b):**
```
8. Najemca zobowiązany będzie do dodatkowej zapłaty w następujących przypadkach:

a) Uszkodzenia Przedmiotu Najmu w trakcie trwania umowy lub zwrotu niespraw-
   nego Przedmiotu Najmu oraz konieczności dokonania naprawy przez Wynajmu-
   jącego. Naprawy w takich przypadkach przeprowadza lub zleca wyłącznie Wy-
   najmujący. Najemca w żadnym razie nie jest uprawniony do dokonywania sa-
   modzielnych napraw, wprowadzania zmian, uzupełnienia Przedmiotu Najmu o
   dodatkowe elementy, ani do zlecenia ich wykonania osobom trzecim.

b) Zwrotu zabrudzonego Przedmiotu Najmu, gdzie Najemca zostanie obciążony
   kosztami jego czyszczenia – po ocenie stanu czystości zwracanego Sprzętu – wg
   stawki ustalonej w Umowie Najmu.

c) W przypadku wezwania serwisowego, które okaże się nieuzasadnione, a pro-
   blem wynikać będzie z prostych do usunięcia przyczyn (np. wciśnięty wyłącznik
   awaryjny, nieprawidłowo załączony bieg, brak paliwa, niewłaściwie ustawienie
   przetączników lub inne błędne operacje eksploatacyjne), Najemca ponosi koszt
   takiego wezwania zgodnie z obowiązującym cennikiem serwisowym.

d) W przypadku opóźnienia po stronie Najemcy w odbiorze lub przyjęciu dostawy
   Przedmiotu Najmu, Wynajmujący zastrzega sobie prawo do naliczenia opłaty za
   przestój kierowcy wynikający z konieczności oczekiwania na Najemcę według
```

**Nowy tekst punktu 8 b):**
```
b) Zwrotu zabrudzonego Przedmiotu Najmu, w przypadku którego Najemca zostanie obciążony kosztami jego czyszczenia po ocenie stanu czystości zwracanego Sprzętu. Rozliczenie kosztów czyszczenia nastąpi według stawki 250,00 zł netto za każdą rozpoczętą roboczogodzinę oraz kosztów materiałów, środków czyszczących i eksploatacyjnych niezbędnych do usunięcia zabrudzeń i przywrócenia Przedmiotu Najmu do stanu czystości z dnia jego wydania.
```

Kluczowa zmiana: zamiast „wg stawki ustalonej w Umowie Najmu" → konkretna stawka „250,00 zł netto za każdą rozpoczętą roboczogodzinę" + koszty materiałów.

---

### P1-016: Statystyki — błędne wartości (-300%, -7)

```yaml
id: P1-016
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, notatka na końcu dokumentu)
component: frontend/AnalyticsView + backend/stats
```

**Opis:** W statystykach pojawiają się błędne wartości: „-300%" i „-7". Klient zauważył nieprawidłowe dane w module statystyk/analytics. Wymaga analizy — prawdopodobnie błędne obliczenia delta/percentage lub brakujące dane powodujące ujemne wartości.


---

## 🏗️ P1-100 — EPIC: Usługi dodatkowe + rozliczenie umowy (cennik) — v2

> **Scalony epic** — łączy P1-003, P1-004, P1-005, P1-006, P1-008 (freebie), P1-013, P1-014, P1-015
> **Wersja 2 (2026-07-08)** — po weryfikacji każdego założenia w kodzie. Kluczowa zmiana vs v1: **zero migracji DB w minimalnym scope** — większość infrastruktury już istnieje, epic to głównie UX + seed danych + 4 zmiany w szablonie PDF.
> **Analiza źródłowa:** 515 PDF-ów legacy z `c:\Temp\legacy_pdfs\` (374 N + 141 U, 157 wariantów "Inne usługi") — `temp/legacy_summary.txt`

```yaml
id: P1-100
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08) + analiza legacy PDF + weryfikacja kodu
component: frontend/ContractFormView + frontend/ConditionPanel + backend/reports (contract.html) + seed danych
subtasks: [P1-003, P1-004, P1-005, P1-006, P1-008, P1-013, P1-014, P1-015]
classification: frontend-heavy (backend: seed + PDF template)
migration_impact: no (minimalny scope) / yes (tylko opcjonalny power_type, P2)
estimated_complexity: medium
```

### User story

Jako handlowiec (Patrycja), chcę edytować usługi dodatkowe, widełki cenowe i warunki rozliczenia **bezpośrednio w widoku umowy** (jak w gridzie Excel), bez osobnych ekranów/modali, żeby szybko przygotować umowę z poprawnym cennikiem diesel/elektryk.

### Kluczowe odkrycie v2: infrastruktura JUŻ ISTNIEJE

Weryfikacja kodu obaliła 5 założeń z v1:

| Założenie v1 | Fakt z kodu (zweryfikowany) |
|---|---|
| "Dodać `contracts.days_per_week`" | ❌ **`working_days_per_week` JUŻ ISTNIEJE** (`contracts/models.py:47`, default 6) i **już drukuje się w PDF** (`contract.html:245`: "Ilość dni pracy w tygodniu: {{ working_days_per_week }}") |
| "Dodać `variant` ENUM na szablonach + endpoint reset?variant=" | ❌ **`FeePresetGroup` już to robi** — diesel/elektryk to **dwa zestawy jako SEED DANYCH**, endpoint `POST /contracts/{id}/service-fees/apply-preset` już istnieje (`contracts/router.py`), `apply_preset_to_contract()` w service już działa |
| "PDF nie wyrazi tekstów typu 'odbiór własny'" | ❌ **PDF już wspiera pełny override tekstowy** przez `description` (`contract.html:223-230`): jeśli `description` ustawione → drukuje się zamiast kwot. Legacy: "Transport: odbiór własny" (43×), "wycena indywidualna", "(plus koszt paliwa)" — wszystko wyrażalne dziś |
| "Auto-detekcja power_type jako rdzeń feature" | ❌ Klient napisał wprost: **"Wybór przez operatora (Patrycję)"**. Auto-detekcja = over-engineering. Najwyżej pre-selekcja sugerowana (P2) |
| "Usunąć kolumnę Opis z gridu" (sugestia UX) | ❌ **Błąd** — `description` to jedyny sposób na wartości tekstowe. Legacy dowodzi że są niezbędne. Kolumnę trzeba **przemianować i wyjaśnić**, nie usuwać |

**Co FAKTYCZNIE brakuje (zweryfikowana luka):**
1. Brak zestawów diesel/elektryk w danych (`fee_preset_groups`) — **seed, nie kod**
2. Preset-picker i edycja warunków są w **modalach** — klient chce inline grid
3. Grid nie tłumaczy Patrycji mechaniki `description`-override — zły UX dla wartości tekstowych
4. Tekst "Ilość dni pracy w tygodniu: X" w PDF ma złe brzmienie (P1-004 chce "Naliczanie: X dni w tygodniu (pozostałe dni według zapisu GPS)")
5. OWN pkt 8b hardcoded ze starym tekstem (`contract.html:330` — tylko umowa najmu; `contract_u.html` ma inny §8, **nie dotyczy**)
6. Nagłówek kolumny PDF w 1 linii (P1-008)
7. Przedpłata na górze umowy (P1-014)
8. Nr wewnętrzny widoczny w trybie usługi (P1-013)

### Kontekst z analizy legacy (515 PDF-ów) — wnioski projektowe

| Usługa | Zmienność | Wniosek projektowy |
|--------|-----------|--------------------|
| Transport | **111 wariantów** (100–3900 zł, "odbiór własny" 43×, "w cenie usługi", "zamiana maszyn", per-maszyna "Transport Ładowarka:") | Kwota ZAWSZE edytowana per umowa; często tekst zamiast kwoty → grid musi mieć łatwy tryb tekstowy |
| Czyszczenie drobne/trudne | 1–3 warianty (150–400 / 400–1500) | Stałe defaulty z zestawu, rzadko edytowane |
| Tankowanie | 2 warianty (150/200 zł "+ koszt paliwa") | Default z zestawu; suffix "(plus koszt paliwa)" = tekst w description |
| Przestój, serwis | 1 wariant każdy (200–300 zł/h; 280 zł) | Stałe, nigdy nie edytowane — idealni kandydaci na zestaw |
| Butla gazowa, wywóz gruzu, rolki, zawiesia, dodatki operatora | 30 wariantów ad-hoc | Dodawane ręcznie z artykułów-usług lub wpisywane; zestaw ich NIE zawiera |
| **Przegląd diesel/elektryk** | **0× w legacy!** | To NOWE wymaganie klienta — nie ma wzorca w legacy, defaulty tylko z uwag klienta (diesel 150, elektryk 90) |

**Rozliczenie (cennik):** 127 unikalnych wariantów kaskad ("1-3 dni - 540/doba, 4-16 - 410, powyżej 16 - 350"; usługi: "do 2 godzin - 1600, każda kolejna 200"). Model `position_conditions` **już wyraża dowolne przedziały** (period_count jest dowolnym int) — P1-005 to problem czysto UX-owy (modal + niezrozumiałe pola), nie danych.

### Architektura v2 (minimalna, na istniejącej infrastrukturze)

#### A. Diesel/elektryk = dwa zestawy `FeePresetGroup` (SEED danych, zero zmian schema)

Seed (idempotentny, w startup lub skrypcie seed):

```
FeePresetGroup: "Najem — Diesel" (contract_type=S, is_default=True)
  ├─ Transport: 1200 / 1200 zł (amount_from/to; opis dostawa/odbiór w description)
  ├─ Przegląd techniczny i czyszczenie maszyny: 150 zł
  ├─ Czyszczenie maszyny (zabrudzenia ponadnormatywne): description="wycena indywidualna"
  ├─ Usługa tankowania: 200 zł, description="200,00 zł (plus koszt paliwa)"
  ├─ Ponadnormatywny przestój transportu: 200–300, unit="zł/h"
  └─ Nieuzasadnione wezwanie serwisowe: 280 zł, description="280,00 zł (plus transport)"

FeePresetGroup: "Najem — Elektryk" (contract_type=S)
  └─ jak wyżej, ale: "Przegląd techniczny, ładowanie akumulatorów oraz czyszczenie maszyny: 90 zł"
```

- Każda pozycja zestawu linkuje `article_id` do artykułu-usługi (`is_service=1`) — zgodnie ze spec `core/25_uslugi_dodatkowe` ("nie stringi tylko matchowane z artykułami usługi"). Seed tworzy brakujące artykuły-usługi (Transport, Przegląd diesel, Przegląd elektryk, Tankowanie, ...).
- Wybór wariantu w UI = wywołanie istniejącego `apply-preset?preset_id=X&replace=true` z potwierdzeniem. **Zero nowego backendu.**
- `copy_fee_templates()` przy tworzeniu umowy zostaje bez zmian (kopiuje default) — dropdown wariantu podmienia zestaw świadomie, na życzenie operatora.

#### B. Wartości tekstowe — UX nad istniejącym `description`

Mechanika już działa (PDF: `description` override). Luka = grid. Zmiana w gridzie "Usługi dodatkowe":
- Kolumnę "Opis" przemianować na **"Tekst na umowie (zamiast kwot)"** + tooltip: "Jeśli wypełnione — na PDF drukuje się ten tekst zamiast kwot. Np. «Transport: odbiór własny», «wycena indywidualna»"
- Kolumna **"Podgląd PDF"** (live, read-only) — pokazuje dokładnie linię jaka wyjdzie na umowie (ta sama logika co Jinja: description || auto-format). Patrycja widzi efekt bez generowania PDF
- Combobox artykułów-usług także przy edycji istniejącego wiersza (dziś tylko w nowym)

#### C. Dni w tygodniu (P1-003 + P1-004) — pole już jest, brakuje UI + brzmienia

- `working_days_per_week` istnieje (default 6). **Sprawdzić czy formularz umowy eksponuje pole** — jeśli nie, dodać segmented control [5][6][7] w sekcji pozycji/rozliczenia
- `contract.html:245` — zmienić brzmienie na: `Naliczanie: {{ working_days_per_week }} dni w tygodniu (pozostałe dni według zapisu GPS)` (P1-004, dokładne brzmienie z uwagi klienta)
- Uwaga: linia drukuje się tylko gdy `contract.notes` puste (else-branch) — zdecydować czy linia naliczania ma być ZAWSZE (rekomendacja: tak, wynieść przed `{% if notes %}`)

#### D. Cennik rozliczenia (P1-005) — czysty UX, zero backendu

Model `position_conditions` już wyraża dowolne widełki. Zmiany tylko w `ConditionPanel.vue`:
- Usunąć modal edycji → inline grid (klik wiersz = edycja, Enter/Esc)
- Kolumny: # | Od–Do (okresy) | Stawka | Jednostka | Min. | **Podgląd PDF (live)**
- Walidacja ciągłości przedziałów inline ("Luka między 3 a 5 — ustaw Od = 4")
- "Zastosuj cennik" (ArticleRatePreset) → inline dropdown zamiast modala
- "Z ostatniej umowy" — zostaje (działa)

#### E. Zmiany w `contract.html` (4 punktowe edycje)

1. **OWN pkt 8b** (linia 330) — nowy tekst z uwagi klienta (stawka 250 zł netto/rozpoczęta rg + materiały). Zweryfikowano: klauzula jest TYLKO w `contract.html` (najem); `contract_u.html` ma inny §8 — nie dotykać
2. **Sekcja Uwagi** (linia 245) — brzmienie "Naliczanie: X dni w tygodniu (pozostałe dni według zapisu GPS)" (pkt C)
3. **Nagłówek "Przewidywana ilość dni najmu"** — złamanie na 2 linie (`Przewidywana<br>ilość dni najmu`) (P1-008)
4. **Przedpłata** — przenieść z góry na dół (sekcja rozliczenia/podpisów) (P1-014); równolegle w formularzu przenieść pole niżej

#### F. Tryb usługi (P1-013) — frontend only

Ukryć pole "nr wewnętrzny" gdy `contract_type === 'U'` w `ContractFormView.vue`.

#### G. OPCJONALNIE / P2 (nie blokuje epica)

- `articles.power_type` ENUM — tylko jako **pre-selekcja sugerowanego zestawu** w dropdownie wariantu (nigdy silent auto-apply). Jedyna migracja w całym epicu — odłożona do P2
- Wyciągnięcie całego OWN do `settings.own_text` — P2-001 (już w backlogu)

### Kolejność sekcji na formularzu (UX, "od pierwsze do drugie")

```
1. Dane podstawowe (typ, numer, okres)
2. Kontrahent i adres
3. Pozycje umowy (CO wynajmujemy)
   └─ Cennik rozliczenia (ZA ILE) — inline grid pod wybraną pozycją
4. Usługi dodatkowe (CO DODATKOWO)
   └─ [Zestaw: Najem — Diesel ▾] [↻ Reset] [+ Dodaj]   ← dropdown zestawu inline, nie modal
5. Rozliczenie umowy (finanse)
   └─ Dni w tygodniu: [5][6][7] · Przedpłata (przeniesiona z góry)
6. Uwagi
```

### Definition of Done

**Seed / dane:**
- [ ] Artykuły-usługi (is_service=1): Transport, Przegląd (diesel), Przegląd (elektryk), Czyszczenie ponadnormatywne, Tankowanie, Przestój transportu, Wezwanie serwisowe — idempotentny seed
- [ ] `FeePresetGroup` "Najem — Diesel" (is_default) + "Najem — Elektryk", pozycje z article_id + kwoty/teksty jak w uwagach klienta (diesel 150, elektryk 90)

**PDF (`contract.html` — 4 edycje):**
- [ ] OWN 8b: nowy tekst 250 zł/rg + materiały (P1-015)
- [ ] Uwagi: "Naliczanie: {{working_days_per_week}} dni w tygodniu (pozostałe dni według zapisu GPS)" (P1-004), drukowana zawsze
- [ ] Nagłówek kolumny w 2 liniach (P1-008)
- [ ] Przedpłata na dole umowy (P1-014)

**Frontend:**
- [ ] `ContractFormView`: dropdown zestawu (Diesel/Elektryk/inne presety) inline w nagłówku sekcji — wywołuje istniejący apply-preset z potwierdzeniem (diff: co się zmieni)
- [ ] `ContractFormView`: kolumna "Tekst na umowie (zamiast kwot)" z tooltipem + kolumna "Podgląd PDF" live
- [ ] `ContractFormView`: combobox artykułów-usług także przy edycji wiersza
- [ ] `ContractFormView`: segmented control dni/tyg [5][6][7] (jeśli pole nie jest już eksponowane)
- [ ] `ContractFormView`: przedpłata przeniesiona na dół formularza
- [ ] `ContractFormView`: nr wewnętrzny ukryty w trybie U (P1-013)
- [ ] `ConditionPanel`: modal → inline grid + walidacja ciągłości + podgląd PDF live + preset-dropdown inline (P1-005)

**Weryfikacja:**
- [ ] E2E: nowa umowa → zestaw Diesel default → zmiana na Elektryk → tylko przegląd się zmienia (150→90 + nazwa) → PDF poprawny
- [ ] E2E: transport → wpisz tekst "odbiór własny" w kolumnie tekstowej → PDF drukuje "- Transport: odbiór własny"
- [ ] E2E: dni/tyg = 6 → PDF "Naliczanie: 6 dni w tygodniu (pozostałe dni według zapisu GPS)"
- [ ] E2E: cennik — dodaj przedział 1-3/4-16/powyżej 16 inline → podgląd zgodny z PDF
- [ ] E2E: umowa U → brak pola nr wewnętrzny
- [ ] PDF diff vs legacy: porównać wygenerowaną umowę z `c:\Temp\legacy_pdfs\S1_2026_N.pdf` (sekcje Inne usługi + Uwagi)
- [ ] Smoke: `e2e/tests/01-login.spec.ts` PASS
- [ ] Spec sync: 02_backend_api (seed), 03_frontend_screens, 04_business_logic; 01_database TYLKO jeśli P2 power_type wejdzie

**Security DoD:**
- [ ] apply-preset i service-fees mają już `Depends(get_current_user)` — potwierdzić testem IDOR na `{contract_id}`
- [ ] Brak `v-html` w podglądzie PDF live (renderować jako text)

### Czerwone flagi — pytania do klienta PRZED implementacją

⚠️ **P1-005:** czy Patrycja chce dodawać/usuwać przedziały widełek, czy tylko edytować kwoty w istniejących? (model wspiera oba — pytanie o UI)
⚠️ **P1-003:** wybór dni/tyg statyczny (info na PDF) czy wpływa na naliczanie w rozliczeniu? Legacy sugeruje statyczny (naliczanie wg GPS) — przyjęto statyczny, potwierdzić
⚠️ **Trzy różne stawki czyszczenia** to różne byty — nie łączyć: przegląd+czyszczenie (150/90, zestaw), czyszczenie ponadnormatywne ("wycena indywidualna", zestaw), OWN 8b (250 zł/rg, tekst prawny)
⚠️ **Default dni/tyg:** kod ma 6, uwaga klienta pokazuje przykład z 5 — potwierdzić domyślną wartość

### Podział na subtaski (kolejność)

| # | Subtask | Stack | Zależności |
|---|---------|-------|------------|
| 1 | Seed: artykuły-usługi + 2 zestawy diesel/elektryk | Backend (dane) | — |
| 2 | `contract.html`: OWN 8b + Naliczanie + nagłówek 2 linie + przedpłata dół | Backend (PDF) | — |
| 3 | `ContractFormView`: dropdown zestawu inline + potwierdzenie z diff | Frontend | 1 |
| 4 | `ContractFormView`: kolumna tekstowa + podgląd PDF live + combobox w edycji | Frontend | — |
| 5 | `ContractFormView`: dni/tyg control + przedpłata dół + nr wewn. ukryty | Frontend | — |
| 6 | `ConditionPanel`: inline grid + walidacja + podgląd + preset-dropdown | Frontend | — |
| 7 | E2E scenariusze + PDF diff vs legacy | QA | 1–6 |
| 8 | Spec sync | Tech Lead | 1–7 |

Subtaski 2, 4, 5, 6 są niezależne — można robić równolegle.

### Szacowanie

- **v2 (minimalny scope, zero migracji):** 1.5–2.5 dnia dev — vs 3–5 dni w v1
- Różnica bierze się z wykorzystania istniejącej infrastruktury (FeePresetGroup, apply-preset, description-override, working_days_per_week) zamiast budowania równoległych mechanizmów

### Dane źródłowe

- Analiza legacy: `temp/legacy_summary.txt` (515 PDF, 157 wariantów), `temp/legacy_analysis.txt` (pełna ekstrakcja)
- Zweryfikowane pliki: `backend/contracts/models.py:47` (working_days_per_week), `backend/settings/models.py:32-90` (FeePresetGroup/ServiceFeeTemplate), `backend/contracts/service.py:123` (apply_preset_to_contract), `backend/reports/templates/contract.html:214-250,330` (fees render + Uwagi + OWN 8b)


---

## 🟡 P2 — Should-Have

### P2-001: Wyciągnięcie OWN do edytowalnego szablonu w settings

```yaml
id: P2-001
status: triaged
priority: P2
created: 2026-07-08
source: tech-lead (follow-up po P1-100)
component: backend/settings + backend/reports
```

**Opis:** Wyciągnięcie tekstu OWN (Ogólne Warunki Najmu) z `contract.html` do edytowalnego pola w settings (np. `settings.own_text`, TEXT) + rendering przez Jinja2. Pozwoli operatorowi edytować OWN bez zmiany kodu. Odłożone z P1-100 (P1-015 zmienia tylko pkt 8b bezpośrednio w szablonie).

---

### P2-002: `articles.power_type` — sugestia zestawu diesel/elektryk

```yaml
id: P2-002
status: triaged
priority: P2
created: 2026-07-08
source: tech-lead (follow-up po P1-100)
component: backend/articles + frontend/ArticleFormView + frontend/ContractFormView
migration_impact: yes
```

**Opis:** Dodać `articles.power_type` ENUM('diesel','electric','other') + dropdown w formularzu artykułu. W formularzu umowy: pre-selekcja sugerowanego zestawu usług dodatkowych na podstawie typu pierwszej pozycji sprzętu (nigdy silent auto-apply — klient wymaga wyboru przez operatora). Migracja legacy: heurystyka po nazwie (`%spalinowy%` → diesel, `%elektryczny%` → electric).

---

## 🟢 P3 — Nice-to-Have
*(brak)*
