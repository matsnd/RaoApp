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
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 1)
component: frontend/ContractFormView + backend/contracts
```

**Opis:** Możliwość odhaczenia (checkbox) czy maszyna jest nasza (własna firmy) czy zewnętrzna (podnajem od innej firmy).

---

### P1-002: Ręczne dodawanie adresu

```yaml
id: P1-002
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 2)
component: frontend/ContractFormView + integrations/GUS-Nominatim
```

**Opis:** Możliwość dodawania adresu ręcznie, jeśli system nie zaciągnie po adresie/kodzie pocztowym, lub jeśli będzie potrzeba dopisania szczegółów (np. numer działki, bramka, dodatkowe wskazówki dojazdu).

---

### P1-003: Wybór liczby dni wynajmu w tygodniu (5/6/7)

```yaml
id: P1-003
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 3)
component: frontend/ContractFormView + backend/contracts + backend/settlements
```

**Opis:** Możliwość liczenia wynajmu 5, 6 lub 7 dni w tygodniu — operator wybiera przy tworzeniu umowy. Obecnie system liczy stałą liczbę dni; klient potrzebuje elastyczności (niektóre umowy 5 dni/tyg, inne 6 lub 7).

---

### P1-004: Zapis o naliczaniu dni w tyg. i weekendach z GPS

```yaml
id: P1-004
status: triaged
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

---

### P1-005: Uproszczenie wybierania widełek cenowych

```yaml
id: P1-005
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 5)
component: frontend/ConditionPanel + backend/contracts (warunki rozliczeniowe)
```

**Opis:** Uprościć proces wybierania widełek cenowych. Obecnie system ma sztywne przedziały; klient potrzebuje:
- **Wynajem:** możliwość edycji okresu widełek, np. 1-2, 1-3, 1-4, 4-7, 4-8, powyżej 16 dni, powyżej 20 dni itp. — operator definiuje przedziały
- **Usługa:** np. do 2h, do 3h (podstawa) — również konfigurowalne

Klient chce elastycznego definiowania widełek zamiast sztywnych dropdown-ów.

---

### P1-006: Dwa warianty zapisów w umowie — diesel vs elektryk

```yaml
id: P1-006
status: triaged
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

---

### P1-007: Miejsce na dodatkowe informacje na protokole usług

```yaml
id: P1-007
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08, pozycja 7)
component: frontend/ProtocolForm + backend/reports (PDF protokołu)
```

**Opis:** Dodać miejsce zapisu dodatkowych informacji na protokole dla usług. Umiejscowienie: nad górnymi polami do podpisu (nad pieczątką) — tak jak ustalano z klientem.

---

### P1-008: „Przewidywana ilość dni najmu" w dwóch linijkach

```yaml
id: P1-008
status: triaged
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

## \U0001f3d7\ufe0f P1-100 — EPIC: Us\u0142ugi dodatkowe + rozliczenie umowy (cennik)

> **Scalony epic** \u2014 \u0142\u0105czy P1-003, P1-004, P1-005, P1-006, P1-008 (freebie), P1-013, P1-014, P1-015
> **Uzasadnienie scalenia:** wszystkie taski dotykaj\u0105 tych samych 3 plik\u00f3w (`ContractFormView.vue`, `backend/contracts/models.py`, `backend/reports/templates/contract.html`). Robienie ich osobno = 8\u00d7 merge conflict, 8\u00d7 regresja PDF, 8\u00d7 test tego samego flow umowy. Scalenie = jeden sp\u00f3jny redesign formularza z grid-ed cennikiem.
> **Analiza \u017ar\u00f3d\u0142owa:** 515 PDF-\u00f3w legacy z `c:\Temp\legacy_pdfs\` (374 umowy najmu N + 141 um\u00f3w us\u0142ug U), 157 unikalnych wariant\u00f3w sekcji "Inne us\u0142ugi" \u2014 pe\u0142na analiza w `temp/legacy_summary.txt`

```yaml
id: P1-100
status: triaged
priority: P1
created: 2026-07-08
source: client-request (uwagi klienta 2026-07-08) + analiza legacy PDF
component: frontend/ContractFormView + frontend/ConditionPanel + backend/contracts + backend/settings + backend/articles + backend/reports
subtasks: [P1-003, P1-004, P1-005, P1-006, P1-008, P1-013, P1-014, P1-015]
classification: cross-stack
migration_impact: yes
estimated_complexity: high
```

### User story

Jako handlowiec (Patrycja), chc\u0119 edytowa\u0107 us\u0142ugi dodatkowe, wide\u0142ki cenowe i warunki rozliczenia **bezpo\u015brednio w widoku umowy** (jak w gridzie Excel), bez przechodzenia przez osobne ekrany/modal, \u017ceby m\u00f3c szybko przygotowa\u0107 umow\u0119 z poprawnym cennikiem diesel/elektryk.

### Kontekst z analizy legacy (515 PDF-\u00f3w)

**Sekcja "Inne us\u0142ugi" \u2014 wzorce z 412 um\u00f3w z t\u0105 sekcj\u0105:**

| Us\u0142uga | Warianty | Najcz\u0119stsza |
|--------|----------|-------------|
| Transport | 111 wariant\u00f3w kwot (100\u20133900 z\u0142, "odbi\u00f3r w\u0142asny", "w cenie us\u0142ugi") | 500 z\u0142 dostawa/odbi\u00f3r (45\u00d7), "odbi\u00f3r w\u0142asny" (43\u00d7) |
| Czyszczenie (drobne) | 3 warianty | 150\u2013400 z\u0142 (373\u00d7) |
| Czyszczenie (trudne) | 1 wariant | 400\u20131500 z\u0142 (374\u00d7) |
| Tankowanie | 2 warianty | 200 z\u0142 (235\u00d7), 150 z\u0142 (139\u00d7) |
| Przest\u00f3j transportu | 1 wariant (sta\u0142y) | 200\u2013300 z\u0142/h (374\u00d7) |
| Serwis nieuzasadniony | 1 wariant (sta\u0142y) | 280 z\u0142 + transport (374\u00d7) |
| Butla gazowa | 3 warianty | 120 z\u0142 (6\u00d7), 100 z\u0142 (2\u00d7), 150 z\u0142 (1\u00d7) |
| Inne (dodatki operatora, dojazd, wyw\u00f3z gruzu, rolki) | 30 wariant\u00f3w | \u2014 |

**Wniosek:** Transport jest najbardziej zmienny (111 wariant\u00f3w) \u2014 musi by\u0107 w pe\u0142ni edytowalny. Pozosta\u0142e us\u0142ugi maj\u0105 1\u20133 warianty \u2014 mog\u0105 mie\u0107 defaulty ale z override. **Brak przegl\u0105du "diesel vs elektryk"** w legacy (przegl\u0105d nie pojawia si\u0119 wcale w PDF-ach!) \u2014 to jest **nowe wymaganie** klienta (P1-006).

**Rozliczenie (cennik) \u2014 wzorce z 374 um\u00f3w N:**
- Kaskadowe stawki dobowe: "1-3 dni - 540 z\u0142/doba, 4-16 dni - 410 z\u0142/doba, powy\u017cej 16 dni - 350 z\u0142/doba"
- 127 unikalnych wariant\u00f3w rozliczenia \u2014 ka\u017cda maszyna ma w\u0142asny cennik

**Rozliczenie us\u0142ug (141 um\u00f3w U):**
- "do 2 godzin - 1600 z\u0142, ka\u017cda kolejna 200 z\u0142" (w\u00f3zek wid\u0142owy)
- "do 8 godzin - 4700 z\u0142, ka\u017cda kolejna 300 z\u0142" (\u0142adowarka obrotowa 18m)
- "110 z\u0142/godzina" (us\u0142uga operatorska)

### Stan obecny kodu (co ju\u017c jest)

| Element | Status | Plik |
|---------|--------|------|
| `ContractServiceFee` model | \u2705 Istnieje (id, contract_id, sort_order, name, amount_from, amount_to, unit, description, is_active, article_id, default_price) | `backend/contracts/models.py:99` |
| `ServiceFeeTemplate` (szablon) | \u2705 Istnieje | `backend/settings/models.py:46` |
| `FeePresetGroup` (zestaw szablon\u00f3w) | \u2705 Istnieje | `backend/settings/models.py:32` |
| `ArticleRatePreset` (cennik per maszyna) | \u2705 Istnieje | `backend/settings/models.py:123` |
| `ArticleRatePresetItem` (warunek w cenniku) | \u2705 Istnieje | `backend/settings/models.py:152` |
| Endpointy CRUD service-fees | \u2705 Istniej\u0105 (list/create/update/delete/reorder/reset/apply-preset) | `backend/contracts/router.py:254-315` |
| Grid "Inne us\u0142ugi" inline | \u2705 Istnieje (Excel-style: click\u2192edit, Enter/Esc) | `frontend/src/views/ContractFormView.vue:266-339` |
| `ConditionPanel.vue` (cennik) | \u26a0\ufe0f Ma modal do edycji \u2014 **do zamiany na inline grid** | `frontend/src/components/contracts/ConditionPanel.vue` |
| Reset do szablonu | \u2705 Jest \u2014 ale **jeden sztywny zestaw**, nie rozr\u00f3\u017cnia diesla/elektryka | `backend/contracts/service.py:673` |
| `copy_fee_templates()` przy tworzeniu umowy | \u2705 Kopiuje szablony `ServiceFeeTemplate` wg `contract_type` (S/U) | `backend/contracts/service.py:49` |
| `article.power_type` (diesel/elektryk) | \u274c **Brak pola** \u2014 trzeba doda\u0107 | `backend/articles/models.py` |
| Warianty diesel/elektryk w szablonach | \u274c **Brak** \u2014 `ServiceFeeTemplate` nie ma pola `variant` | `backend/settings/models.py` |
| OWN (Og\u00f3lne Warunki Najmu) | \u26a0\ufe0f **Hardcoded w HTML** (`contract.html`) \u2014 P1-015 wymaga zmiany kodu | `backend/reports/templates/contract.html:281-420` |
| `contract.days_per_week` (5/6/7) | \u274c **Brak pola** \u2014 trzeba doda\u0107 | `backend/contracts/models.py` |

### Architektura docelowa (Tech Lead)

#### 1. Nowe pola DB (migracja deterministyczna)

**`articles.power_type`** (P1-006 auto-detekcja):
```sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS power_type ENUM('diesel','electric','other')
  NOT NULL DEFAULT 'other' COMMENT 'Typ zasilania maszyny dla auto-wariantu us\u0142ug dodatkowych';
```
- Warto\u015bci: `diesel` | `electric` | `other`
- Default: `other` (bezpieczne dla istniej\u0105cych danych)
- UI: dropdown w `ArticleFormView.vue` (3 opcje)
- Migracja legacy: heurystyka po nazwie artyku\u0142u (`LIKE '%spalinowy%'` \u2192 diesel, `LIKE '%elektryczny%'` \u2192 electric, reszta \u2192 other)

**`contracts.days_per_week`** (P1-003):
```sql
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS days_per_week TINYINT UNSIGNED
  NOT NULL DEFAULT 5 COMMENT 'Liczba dni wynajmu w tygodniu (5/6/7) dla naliczania';
```
- Warto\u015bci: 5 | 6 | 7
- Default: 5 (najcz\u0119stsze w legacy \u2014 "Ilo\u015b\u0107 dni pracy w tygodniu: 6" pojawia si\u0119 w 80% PDF-\u00f3w, ale klient chce domy\u015blnie 5 wg P1-004)
- UI: segmented control w sekcji rozliczenia (3 przyciski: 5 / 6 / 7)
- Wp\u0142ywa na: tekst w sekcji Uwagi PDF ("Naliczanie: 5 dni w tygodniu (pozosta\u0142e dni wed\u0142ug zapisu GPS)")

**`service_fee_templates.variant`** (P1-006 warianty szablon\u00f3w):
```sql
ALTER TABLE service_fee_templates ADD COLUMN IF NOT EXISTS variant ENUM('diesel','electric','common','custom')
  NOT NULL DEFAULT 'common' COMMENT 'Wariant us\u0142ug: diesel/elektryk/common (wsp\u00f3lny)/custom';
```
- `common` \u2014 us\u0142ugi wsp\u00f3lne dla obu wariant\u00f3w (transport, tankowanie, przest\u00f3j, serwis, czyszczenie)
- `diesel` \u2014 us\u0142ugi specyficzne dla diesla (przegl\u0105d 150 z\u0142, nazwa "Przegl\u0105d techniczny i czyszczenie maszyny")
- `electric` \u2014 us\u0142ugi specyficzne dla elektryka (przegl\u0105d 90 z\u0142, nazwa "Przegl\u0105d techniczny, \u0142adowanie akumulator\u00f3w oraz czyszczenie maszyny")
- `custom` \u2014 us\u0142ugi niestandardowe (butla gazowa, wyw\u00f3z gruzu, rolki, itp.)
- Reset context-aware: \u0142aduje `common` + `diesel` LUB `common` + `electric` w zale\u017cno\u015bci od wariantu

#### 2. Decyzja: NIE tworzymy osobnego modelu `ServiceFeeVariantGroup`

Zamiast tego:
- `ServiceFeeTemplate.variant` (ENUM) wystarczy
- Reset: `SELECT * FROM service_fee_templates WHERE contract_type=? AND is_active=1 AND (variant='common' OR variant=?)` \u2014 drugi `?` = auto-detekcja z pozycji umowy LUB r\u0119czny wyb\u00f3r operatora
- Endpoint: `POST /contracts/{id}/service-fees/reset?variant=diesel|electric|custom`

#### 3. Auto-detekcja wariantu z pozycji umowy

**Logika (backend, `contracts/service.py`):**
```python
async def detect_variant_from_positions(db, contract_id) -> str:
    """Auto-detekcja wariantu diesel/elektryk z pierwszej pozycji sprz\u0119tu."""
    positions = await db.execute(
        select(ContractPosition)
        .join(Article, ContractPosition.article_id == Article.id)
        .where(ContractPosition.contract_id == contract_id)
        .where(Article.is_service == False)  # tylko sprz\u0119t, nie us\u0142ugi
        .order_by(ContractPosition.sort_order)
        .limit(1)
    )
    pos = positions.scalars().first()
    if not pos or not pos.article:
        return "custom"
    return pos.article.power_type or "other"  # 'diesel'|'electric'|'other'
```

**Kiedy wywo\u0142a\u0107:**
- Po dodaniu pierwszej pozycji sprz\u0119tu do nowej umowy \u2192 auto-apply zestawu (je\u015bli brak service_fees)
- Po usuni\u0119ciu ostatniej pozycji sprz\u0119tu \u2192 NIE auto-reset (zachowaj r\u0119czne zmiany)
- Przy edycji istniej\u0105cej umowy \u2192 **NIGDY** auto-apply (zachowaj r\u0119czne zmiany)

#### 4. OWN \u2014 wyci\u0105gni\u0119cie do edytowalnego szablonu (P1-015)

**Obecnie:** OWN jest hardcoded w `contract.html` (Jinja2 template, ~140 linii HTML).
**Decyzja architektoniczna:** NIE wyci\u0105gamy ca\u0142ego OWN do DB (to prawniczy tekst, rzadko si\u0119 zmienia). Zamiast:
- **Opcja A (prostsza, rekomendowana):** Zmiana tekstu pkt 8b bezpo\u015brednio w `contract.html` (1 commit, 5 minut)
- **Opcja B (przysz\u0142o\u015b\u0107):** Wyci\u0105gni\u0119cie OWN do `settings.own_text` (TEXT field) + rendering przez Jinja2 `{{ own_text|safe }}` \u2014 ale to scope creep, **odk\u0142adamy na P2**

**Implementacja P1-015:** Opcja A \u2014 edycja `contract.html` linia ~360 (pkt 8b), zmiana tekstu na:
```
b) Zwrotu zabrudzonego Przedmiotu Najmu, w przypadku kt\u00f3rego Najemca zostanie obci\u0105\u017cony
   kosztami jego czyszczenia po ocenie stanu czysto\u015bci zwracanego Sprz\u0119tu. Rozliczenie
   koszt\u00f3w czyszczenia nast\u0105pi wed\u0142ug stawki 250,00 z\u0142 netto za ka\u017cd\u0105 rozpocz\u0119t\u0105
   roboczogodzin\u0119 oraz koszt\u00f3w materia\u0142\u00f3w, \u015brodk\u00f3w czyszcz\u0105cych i eksploatacyjnych
   niezb\u0119dnych do usuni\u0119cia zabrudze\u0144 i przywr\u00f3cenia Przedmiotu Najmu do stanu czysto\u015bci
   z dnia jego wydania.
```

#### 5. Frontend \u2014 grid inline (bez modali)

**Kluczowa zasada klienta:** "MA NIE BY\u0106 \u017cadnych dodatkowych screen\u00f3w/modali \u2014 wszystko edytowane jakby w gridzie z widoku umowy"

**Zmiany w `ContractFormView.vue`:**
1. **Sekcja "Inne us\u0142ugi"** (ju\u017c jest grid inline \u2705) \u2014 rozbudowa\u0107 o:
   - Dropdown "Wariant: Diesel/Elektryk/Inny" w nag\u0142\u00f3wku sekcji
   - Auto-apply zestawu po dodaniu pierwszej pozycji sprz\u0119tu (nowa umowa)
   - Combobox z artyku\u0142ami-us\u0142ugami w edycji istniej\u0105cego wiersza (nie tylko nowy)
   - Kolumna \u2191\u2193 (kolejno\u015b\u0107) \u2014 backend `sort_order` ju\u017c jest
   - Usun\u0105\u0107 kolumn\u0119 "Opis" (dubluje si\u0119 z Nazwa) \u2014 opis auto-generowany z Nazwa+Kwota+J.m.
   - Podgl\u0105d PDF live pod gridem

2. **Sekcja "Cennik rozliczenia"** (`ConditionPanel.vue`) \u2014 **usun\u0105\u0107 modal**, zamieni\u0107 na inline grid:
   - Kolumny: # | Przedzia\u0142 (Od/Do) | Stawka | J.m. | Min. | Podgl\u0105d PDF (live)
   - Walidacja ci\u0105g\u0142o\u015bci przedzia\u0142\u00f3w (inline error: "Luka mi\u0119dzy 3 a 5")
   - "Zastosuj cennik" \u2192 inline dropdown (nie modal) z list\u0105 `ArticleRatePreset`
   - "Z ostatniej umowy" \u2192 zostaje (ju\u017c dzia\u0142a)

3. **Sekcja rozliczenia** \u2014 doda\u0107:
   - Segmented control "Dni w tygodniu: [5] [6] [7]" (P1-003)
   - Przedp\u0142ata przeniesiona z g\u00f3ry na d\u00f3\u0142 (P1-014)
   - Pole "nr wewn\u0119trzny" ukryte w trybie us\u0142uga (P1-013)

4. **Kolejno\u015b\u0107 sekcji na formularzu** (od g\u00f3ry do do\u0142u):
   ```
   1. Dane podstawowe (typ, numer, okres)
   2. Kontrahent i adres
   3. Warunki finansowe (handlowiec) \u2014 BEZ przedp\u0142aty (P1-014)
   4. Pozycje umowy (CO wynajmujemy)
      \u2514\u2500 Cennik rozliczenia (ZA ILE \u2014 wide\u0142ki, inline grid)  \u2190 PRZENIE\u015a\u0106 z modala
   5. Inne us\u0142ugi (CO DODATKOWO \u2014 transport, przegl\u0105d, tankowanie)
      \u2514\u2500 Wariant: Diesel/Elektryk dropdown
   6. Rozliczenie umowy (KOSZT vs KOSZT FIRMY)
      \u2514\u2500 Dni w tygodniu: 5/6/7 (P1-003)
      \u2514\u2500 Przedp\u0142ata (P1-014 \u2014 przeniesiona z g\u00f3ry)
   7. Uwagi (tekst swobodny na PDF)
   ```

#### 6. PDF umowy \u2014 zmiany szablonu (`contract.html`)

**Sekcja "Inne us\u0142ugi"** (linia 219) \u2014 ju\u017c renderuje z `fees` (ContractServiceFee) \u2705. Zmiany:
- Auto-generowanie tekstu z `name + amount_from + amount_to + unit` (je\u015bli `description` puste)
- Format: `- {name}: {amount_from} z\u0142 - {amount_to} z\u0142 {unit}` (z wide\u0142kami)
- Format (sta\u0142a): `- {name}: {amount_from} z\u0142` (bez `amount_to`)
- Format (wycena indywidualna): `- {name}: wycena indywidualna` (je\u015bli obie kwoty puste)

**Sekcja "Uwagi"** (P1-004) \u2014 doda\u0107 lini\u0119:
```
- Naliczanie: {{ contract.days_per_week }} dni w tygodniu (pozosta\u0142e dni wed\u0142ug zapisu GPS)
```
Zamiast sztywnego "5" \u2014 warto\u015b\u0107 z `contract.days_per_week`.

**Sekcja OWN pkt 8b** (P1-015) \u2014 zmiana tekstu (patrz pkt 4 wy\u017cej).

**Nag\u0142\u00f3wek kolumny "Przewidywana ilo\u015b\u0107 dni najmu"** (P1-008 freebie) \u2014 CSS `white-space: normal` + `max-width` \u017ceby \u0142ama\u0142 si\u0119 na 2 linie:
```html
<th style="white-space: normal; max-width: 80px;">Przewidywana<br>ilo\u015b\u0107 dni najmu</th>
```

**Przedp\u0142ata** (P1-014) \u2014 przenie\u015b\u0107 z g\u00f3ry umowy na d\u00f3\u0142 (sekcja rozliczenia).

### Definition of Done

**Backend / DB:**
- [ ] `articles.power_type` (ENUM diesel/electric/other, default 'other') \u2014 migracja + heurystyka legacy
- [ ] `contracts.days_per_week` (TINYINT, default 5) \u2014 migracja
- [ ] `service_fee_templates.variant` (ENUM diesel/electric/common/custom, default 'common') \u2014 migracja
- [ ] Seed: szablony `common` (transport, czyszczenie\u00d72, tankowanie, przest\u00f3j, serwis) + `diesel` (przegl\u0105d 150 z\u0142) + `electric` (przegl\u0105d 90 z\u0142)
- [ ] `detect_variant_from_positions()` w `contracts/service.py`
- [ ] Endpoint `POST /contracts/{id}/service-fees/reset?variant=diesel|electric|custom` \u2014 reset context-aware
- [ ] Endpoint `POST /contracts/{id}/service-fees/auto-apply-variant` \u2014 auto-apply po dodaniu pozycji
- [ ] `contract.html` \u2014 zmiana OWN pkt 8b (P1-015)
- [ ] `contract.html` \u2014 sekcja Uwagi z `days_per_week` (P1-004)
- [ ] `contract.html` \u2014 nag\u0142\u00f3wek "Przewidywana ilo\u015b\u0107 dni najmu" w 2 liniach (P1-008)
- [ ] `contract.html` \u2014 przedp\u0142ata na dole (P1-014)
- [ ] `contract.html` \u2014 auto-generowanie tekstu "Inne us\u0142ugi" z name+amount+unit

**Frontend:**
- [ ] `ArticleFormView.vue` \u2014 dropdown `power_type` (diesel/electric/other)
- [ ] `ContractFormView.vue` \u2014 dropdown "Wariant: Diesel/Elektryk/Inny" w sekcji "Inne us\u0142ugi"
- [ ] `ContractFormView.vue` \u2014 auto-apply zestawu po dodaniu pierwszej pozycji sprz\u0119tu (nowa umowa)
- [ ] `ContractFormView.vue` \u2014 combobox z artyku\u0142ami-us\u0142ugami w edycji istniej\u0105cego wiersza
- [ ] `ContractFormView.vue` \u2014 kolumna \u2191\u2193 (kolejno\u015b\u0107) w "Inne us\u0142ugi"
- [ ] `ContractFormView.vue` \u2014 usun\u0105\u0107 kolumn\u0119 "Opis" (auto-generowany)
- [ ] `ContractFormView.vue` \u2014 podgl\u0105d PDF live pod gridem
- [ ] `ContractFormView.vue` \u2014 segmented control "Dni w tygodniu: 5/6/7" (P1-003)
- [ ] `ContractFormView.vue` \u2014 przedp\u0142ata przeniesiona na d\u00f3\u0142 (P1-014)
- [ ] `ContractFormView.vue` \u2014 pole "nr wewn\u0119trzny" ukryte w trybie us\u0142uga (P1-013)
- [ ] `ContractFormView.vue` \u2014 preset-picker jako inline dropdown (nie modal)
- [ ] `ConditionPanel.vue` \u2014 **usun\u0105\u0107 modal**, zamieni\u0107 na inline grid
- [ ] `ConditionPanel.vue` \u2014 kolumna "Podgl\u0105d na PDF" (live)
- [ ] `ConditionPanel.vue` \u2014 walidacja ci\u0105g\u0142o\u015bci przedzia\u0142\u00f3w (inline error)
- [ ] `ConditionPanel.vue` \u2014 "Zastosuj cennik" jako inline dropdown (nie modal)

**Weryfikacja:**
- [ ] E2E: nowa umowa diesel \u2192 auto-apply zestaw diesel (przegl\u0105d 150 z\u0142) \u2192 edytuj kwot\u0119 inline \u2192 PDF poprawny
- [ ] E2E: nowa umowa elektryk \u2192 auto-apply zestaw elektryk (przegl\u0105d 90 z\u0142) \u2192 zmiana nazwy przegl\u0105du
- [ ] E2E: zmiana wariantu diesel\u2192elektryk \u2192 modal potwierdzenia z diff \u2192 tylko przegl\u0105d si\u0119 zmienia
- [ ] E2E: wybierz 6 dni/tyg \u2192 PDF "Uwagi" pokazuje "6 dni w tygodniu"
- [ ] E2E: umowa us\u0142ugi (typ U) \u2192 brak "nr wewn\u0119trznego" \u2192 brak auto-apply zestawu
- [ ] E2E: PDF umowy \u2014 przedp\u0142ata na dole, OWN pkt 8b z 250 z\u0142/rg, nag\u0142\u00f3wek kolumny w 2 liniach
- [ ] Smoke: `e2e/tests/01-login.spec.ts` PASS
- [ ] `git diff spec/core/` niepusty (01_database, 02_backend_api, 03_frontend_screens, 04_business_logic)

**Security DoD:**
- [ ] Nowe endpointy maj\u0105 `Depends(get_current_user)`
- [ ] Endpointy z `{contract_id}` w \u015bcie\u017cce: test IDOR (user A nie modyfikuje umowy user B)
- [ ] Pydantic schemas z constraints na `days_per_week` (5\u20137), `power_type` (enum), `variant` (enum)
- [ ] Brak `v-html` na user-input w podgl\u0105dzie PDF live

### Czerwone flagi (do weryfikacji z klientem PRZED implementacj\u0105)

\u26a0\ufe0f **P1-005 "operator definiuje przedzia\u0142y"** \u2014 czy Patrycja chce **dodawa\u0107/usuwa\u0107 przedzia\u0142y** wide\u0142ek, czy tylko **edytowa\u0107 kwoty w obecnych**? Je\u015bli to drugie \u2192 uproszczenie o 60% scope (nie trzeba add/delete przedzia\u0142\u00f3w, tylko edit stawek).

\u26a0\ufe0f **P1-003 "5/6/7 dni"** \u2014 czy to wyb\u00f3r przy tworzeniu umowy (static) czy zmiana w trakcie trwania (dynamic, wp\u0142ywa na rozliczenie ju\u017c naliczonych dni)? Static = proste pole + tekst PDF. Dynamic = przeliczenie ca\u0142ego rozliczenia \u2014 drastycznie wi\u0119kszy scope.

\u26a0\ufe0f **P1-006 + P1-015 musz\u0105 by\u0107 projektowane wsp\u00f3lnie** \u2014 czyszczenie maszyny pojawia si\u0119 w "Inne us\u0142ugi" (150\u2013400 z\u0142 drobne, 400\u20131500 z\u0142 trudne) i w OWN 8b (250 z\u0142/rg). To **trzy r\u00f3\u017cne stawki za trzy r\u00f3\u017cne sytuacje** (przegl\u0105d vs drobne vs trudne vs ponadnormatywne rg). Nie po\u0142\u0105czy\u0107 w jedn\u0105 pozycj\u0119.

\u26a0\ufe0f **"Edycja jakby w gridzie"** \u2014 constraint na architektur\u0119 frontendu. NIE budowa\u0107 osobnego screena "Edytor cennika". Wszystko inline w `ContractFormView`.

### Podzia\u0142 na subtaski (kolejno\u015b\u0107 implementacji)

| # | Subtask | Stack | Zale\u017cno\u015bci |
|---|---------|-------|------------|
| 1 | Migracja DB: `power_type`, `days_per_week`, `variant` + seed szablon\u00f3w | DB | \u2014 |
| 2 | Backend: `detect_variant_from_positions()` + endpointy reset/auto-apply | Backend | 1 |
| 3 | Backend: `contract.html` zmiany (OWN 8b, Uwagi days_per_week, nag\u0142\u00f3wek 2 linie, przedp\u0142ata d\u00f3\u0142, auto-tekst Inne us\u0142ugi) | Backend | 1 |
| 4 | Frontend: `ArticleFormView` \u2014 dropdown `power_type` | Frontend | 1 |
| 5 | Frontend: `ContractFormView` \u2014 wariant dropdown + auto-apply + combobox + kolejno\u015b\u0107 + podgl\u0105d PDF | Frontend | 2 |
| 6 | Frontend: `ContractFormView` \u2014 segmented control dni/tyg + przedp\u0142ata d\u00f3\u0142 + nr wewn. ukryty | Frontend | 1 |
| 7 | Frontend: `ConditionPanel` \u2014 inline grid (usun\u0105\u0107 modal) + walidacja ci\u0105g\u0142o\u015bci + podgl\u0105d PDF | Frontend | \u2014 |
| 8 | Frontend: preset-picker inline dropdown (nie modal) | Frontend | 5 |
| 9 | E2E: scenariusze diesel/elektryk/us\u0142uga/dni-tyg/zmiana-wariantu | QA | 1-8 |
| 10 | Spec sync: 01_database, 02_backend_api, 03_frontend_screens, 04_business_logic | Tech Lead | 1-9 |

### Szacowanie

- **Bez uproszcze\u0144 (pe\u0142en scope):** 3-5 dni dev (1 DB + 1 backend + 2 frontend + 0.5 QA)
- **Z uproszczeniami (po odpowiedziach klienta na czerwone flagi):** 2-3 dni dev

### Dane \u017ar\u00f3d\u0142owe

- Analiza legacy PDF: `temp/legacy_summary.txt` (515 PDF-\u00f3w, 157 wariant\u00f3w "Inne us\u0142ugi")
- Pe\u0142na ekstrakcja: `temp/legacy_analysis.txt` (11987 linii, wszystkie PDF-y)
- UX spec (od UX Designer): powy\u017cej w tej sekcji
- Product review (od Product Owner): powy\u017cej w tej sekcji


---

## 🟡 P2 — Should-Have
*(brak)*

---

## 🟢 P3 — Nice-to-Have
*(brak)*
