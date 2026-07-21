# RAO Backlog — Sprint 2026-07-21 →

> **Status:** Oczyszczony 2026-07-21 (31 tasków zarchiwizowanych → `archiwum/BACKLOG_SPRINT_20260711_20260721.md`)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260711_20260721.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem
> **Kontekst:** Aplikacja działa stabilnie na prod. User ma nowe uwagi — po czyszczeniu backlogu zostaną dodane.

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`
- Agent ustawia MAX `team-verified`; `user-verified`/`client-approved` = CZŁOWIEK, nigdy agent
- Sweep done→archiwum gdy BACKLOG > 400 linii

---

## 🚨 P0 — Production Blockers

*Brak aktywnych P0. Aplikacja działa stabilnie na prod (2026-07-21).*

---

## 🔴 P1 — Must-Have

### P1-201: Przedpłata w PDF — dopisek "brutto"

```yaml
id: P1-201
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates/contract.html + contract_u.html
migration_impact: no
```

**Opis:** W szablonie PDF umowy (S i U) w górnej tabeli informacyjnej przedpłata wyświetla się jako "Przedpłata: 1 200,00 zł" — klient chce dopisek "brutto" po kwocie: "Przedpłata: 1 200,00 zł brutto".

**Zadania:**
1. `backend/reports/templates/contract.html` (linia 136) — dodać " brutto" po `{{ contract.prepayment_amount | money }}`
2. `backend/reports/templates/contract_u.html` (linia 126) — to samo

**Definition of Done:**
- [x] PDF umowy S pokazuje "Przedpłata: ... zł brutto"
- [x] PDF umowy U pokazuje "Przedpłata: ... zł brutto"
- [x] Brak zmian w innych sekcjach PDF
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML, nie dotyka kodu)

---

### P1-206: Umowa U (usługa) — open-ended tier "każda kolejna x zł / h" zamiast "powyżej X godzin"

```yaml
id: P1-206
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/contracts/service.py + frontend/components/contracts/ConditionPanel.vue
migration_impact: no
scope: tylko godziny, tylko umowy U (is_flat=True, count_unit="godzin")
```

**Opis:** W warunkach rozliczeniowych open-ended tier (period_to=NULL, pf>1) dla umowy U (usługa) label był "powyżej 8 godzin - 150,00zł" (ryczałt, bez / unit). Klient chce "każda kolejna 150,00 zł / h" — stawka per godzina po progu. Grid konfiguracji bez zmian (operator wpisuje period_from, period_to puste, rate — jak wcześniej).

**Zmiany:**
1. `backend/contracts/service.py` `format_position_conditions_cascading` (linia ~446) — dla `is_flat=True` (U) + open-ended (period_to=None, pf>1) + `count_unit=="godzin"`: `lines.append(f"każda kolejna {_format_rate(n['rate'])}zł / h")` + `continue` (pomija `_format_period_range`)
2. `frontend/src/components/contracts/ConditionPanel.vue` `formatPreview` (linia ~433) — dla `isFlat` (isService) + `pt==null` + `pf>1` + `labels.count==='godzin'`: `return \`każda kolejna ${rateStr}zł / h\``

**Definition of Done:**
- [x] PDF umowy U z open-ended tier w godzinach pokazuje "każda kolejna 150,00 zł / h" (zamiast "powyżej 8 godzin - 150,00zł")
- [x] Podgląd w ConditionPanel (panel podglądu w widoku umowy) pokazuje to samo
- [x] Grid konfiguracji bez zmian (period_from, period_to puste, rate)
- [x] Umowy S (najem, dni) bez zmian — nadal "powyżej X dni"
- [x] Closed ranges w umowach U bez zmian — nadal "1 - 8 godzin - 150,00zł"
- [x] `vue-tsc` zielony, `compileall` zielony
- [x] Smoke `01-login.spec.ts` zielony (zmiana w label render, nie dotyka auth/routing)

---

### P1-205: Moduł Dostawy — kalendarz z datami dostaw z umów + drill-down do umowy

```yaml
id: P1-205
status: triaged
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/deliveries (nowy moduł read-only) + frontend/views/DeliveriesView.vue (nowy) + frontend/router + frontend/stores/deliveries.ts (nowy) + frontend/components (DrillDownDrawer reuse)
migration_impact: no
decisions:
  source: tylko z umów (read-only, brak nowej tabeli)
  drilldown: panel dnia → drawer umowy (jak w reservations)
  scope: tylko plan do backlogu (implementacja w osobnej sesji)
related: ReservationsView.vue (wzorzec kalendarza + panel dnia + drill-down), DrillDownDrawer.vue (reuse)
```

**Opis:** Nowy moduł "Dostawy" mirrorujący UX modułu Rezerwacje, ale pokazujący daty dostaw maszyn na budowy z umów (nie z osobnej tabeli). Klikalne dni na kalendarzu → panel dnia z listą dostaw → drill-down do draweru z danymi umowy.

**Kontekst (stan obecny — analiza 2026-07-21):**
- `Contract.date_from` = data przekazania/dostawy maszyny na budowę (pole "Termin przekazania" na PDF umowy)
- `ContractPosition.delivery_date` = opcjonalna data dostawy per pozycja (nullable, używane w umowach U)
- `Contract.delivery_address` + `postal_code` + `city` = adres dostawy
- `Contract.contractor_id` = kontrahent (odbiorca dostawy)
- `ContractPosition.machine_id` = maszyna dostarczana (dla umów S)
- Brak osobnej tabeli `deliveries` — dane są w umowach

**Wzorzec (ReservationsView.vue):**
- Kalendarz month grid (6 tygodni, stabilny rozmiar — fix cd37e5d)
- Panel dnia po prawej (lista eventów z checkboxami filtru)
- Kropki eventów w komórkach + tooltip na hover
- Drill-down drawer (DrillDownDrawer.vue — reuse z Analytics)
- Filtry: machine, contractor, salesperson, type
- Eksport CSV (ExportCsvButton — reuse)

**Architektura (read-only, bez migracji DB):**

```
Backend (nowy moduł, read-only):
  backend/deliveries/
    __init__.py
    router.py        # GET /deliveries/calendar?date_from&date_to&machine_id&contractor_id
    schemas.py       # DeliveryCalendarEvent (mirror CalendarEvent)
    service.py       # zapytanie o contracts + positions w zakresie dat
  main.py            # include_router(deliveries_router)

Frontend (nowy widok, mirror ReservationsView):
  frontend/src/views/DeliveriesView.vue     # kalendarz + panel dnia + drill-down
  frontend/src/stores/deliveries.ts         # fetchCalendar, fetchContractDetails
  frontend/src/router/index.js              # /deliveries → DeliveriesView
  frontend/src/components/AppLayout.vue     # link w menu "Dostawy"
```

**Fazy implementacji:**

**Faza 1 — Backend (read-only endpoint):**
1. `backend/deliveries/__init__.py` — pusty
2. `backend/deliveries/schemas.py` — `DeliveryCalendarEvent`:
   - `source: "contract"` (zawsze, jedyny source)
   - `source_id: int` (contract_id)
   - `contract_number: str`
   - `machine_id: Optional[int]` (z pozycji, NULL dla umów U)
   - `machine_name: Optional[str]`
   - `internal_number: Optional[str]`
   - `contractor_id: int`
   - `contractor_name: str`
   - `delivery_date: date` (Contract.date_from lub ContractPosition.delivery_date — wybiera最早szą z umowy)
   - `delivery_address: Optional[str]`
   - `city: Optional[str]`
   - `contract_type: str` ("S" | "U")
   - `salesperson_id: Optional[int]`
   - `salesperson_name: Optional[str]`
3. `backend/deliveries/service.py` — `list_calendar(db, date_from, date_to, machine_id, contractor_id)`:
   - Source: `contracts` WHERE `date_from BETWEEN date_from AND date_to` (data dostawy = date_from umowy)
   - JOIN `contractors` (nazwa), `salespeople` (handlowiec), `contract_positions` LEFT JOIN `machines` (nazwa maszyny)
   - Filtr `machine_id` przez `contract_positions.machine_id`
   - Filtr `contractor_id` przez `contracts.contractor_id`
   - Sort po `delivery_date`
   - Edge case: umowa bez `date_from` (NULL) → pominąć (brak daty dostawy)
4. `backend/deliveries/router.py` — `GET /deliveries/calendar` z `Depends(get_current_user)`, query params: `date_from`, `date_to`, `machine_id?`, `contractor_id?`
5. `backend/main.py` — `from deliveries.router import router as deliveries_router` + `app.include_router(deliveries_router)`
6. `backend/contracts/router.py` — sprawdzić czy istnieje endpoint zwracający pełne dane umowy dla drill-down (już jest `GET /contracts/{id}` z pozycjami/opłatami/warunkami) — reuse

**Faza 2 — Frontend (nowy widok):**
7. `frontend/src/stores/deliveries.ts` — Pinia store:
   - state: `calendarEvents: DeliveryCalendarEvent[]`, `loading`, `error`
   - actions: `fetchCalendar(dateFrom, dateTo, filters)`, `fetchContractDetails(id)` (reuse contracts store)
8. `frontend/src/views/DeliveriesView.vue` — mirror `ReservationsView.vue`:
   - Kalendarz month grid (6 tygodni, stabilny — copy fix cd37e5d)
   - Panel dnia po prawej (lista dostaw tego dnia)
   - Kropki w komórkach (1 kolor = dostawy, nie rozróżniać source bo jedyny)
   - Tooltip na hover (maszyna, kontrahent, adres, numer umowy)
   - Filtry: machine (combobox), contractor (ContractorCombobox reuse), salesperson, type (S/U)
   - Checkboxy w panelu dnia: "Dostawy S" / "Dostawy U" (filtrowanie listy)
   - Klik na dostawę w panelu → DrillDownDrawer z danymi umowy (numer, kontrahent, pozycje, opłaty, warunki, adres dostawy)
   - Eksport CSV (ExportCsvButton reuse)
   - Stany: loading, error, empty (ale kalendarz zawsze widoczny — nie chować jak w reservations, lessons learned)
9. `frontend/src/router/index.js` — dodać route `/deliveries` → `DeliveriesView.vue` (obok `/reservations`)
10. `frontend/src/components/AppLayout.vue` (lub sidebar) — dodać link "Dostawy" w menu (ikona truck/dostawa)

**Faza 3 — QA:**
11. `e2e/tests/07-deliveries.spec.ts` (nowy) — smoke:
    - Otwórz `/deliveries` → kalendarz renderuje się (6 tygodni, stabilny)
    - Klik na dzień z dostawą → panel dnia pokazuje listę
    - Klik na dostawę → drawer z danymi umowy
    - Filtr machine/contractor działa
12. Smoke `e2e/tests/01-login.spec.ts` — zielony (regresja)
13. `vue-tsc --noEmit` — zielony
14. `pytest` — zielony (jeśli dodano testy backend)

**Ryzyka:**
- **Umowy bez `date_from`** — pomijane (brak daty dostawy). Sprawdzić w DB ile umów ma `date_from IS NULL` — może być dużo starych. Filtrować tylko z `date_from IS NOT NULL`.
- **Umowy U (usługi)** — `date_from` = data dostawy usługi? Czy `ContractPosition.delivery_date`? Decyzja: używać `Contract.date_from` jako głównej daty dostawy (spójne z PDF "Termin przekazania"). `delivery_date` z pozycji tylko jako fallback gdy `date_from IS NULL` a `delivery_date IS NOT NULL`.
- **Wiele pozycji w jednej umowie** — jedna dostawa = jedna umowa (nie per pozycja). Kropka w kalendarzu = 1 umowa, tooltip pokazuje główne dane.
- **Brak CRUD** — user nie może dodać dostawy z kalendarza (brak tabeli). Dostawy powstają przez tworzenie umowy. To świadoma decyzja (user wybrał "read-only z umów").
- **Prawy klik / context menu** — w reservations jest "Dodaj rezerwację" z prawego kliku. W dostawach brak CRUD → context menu wyłączone lub pokazuje "Otwórz umowę".
- **Stabilny kalendarz** — lessons learned z reservations (fix cd37e5d): od razu 6 tygodni w DeliveriesView.

**Definition of Done:**
- [ ] `GET /deliveries/calendar` zwraca dostawy z umów w zakresie dat (Contract.date_from jako data dostawy)
- [ ] Filtry: machine_id, contractor_id działają
- [ ] Umowy bez `date_from` pomijane (lub fallback do delivery_date z pozycji)
- [ ] `/deliveries` route w frontend, kalendarz 6 tygodni stabilny
- [ ] Panel dnia po prawej z listą dostaw (maszyna, kontrahent, adres, numer umowy)
- [ ] Klik na dostawę → DrillDownDrawer z pełnymi danymi umowy
- [ ] Filtry: machine (combobox), contractor (ContractorCombobox), salesperson, type (S/U)
- [ ] Checkboxy w panelu: "Dostawy S" / "Dostawy U"
- [ ] Eksport CSV działa
- [ ] Stany: loading, error, empty (kalendarz zawsze widoczny)
- [ ] Link "Dostawy" w menu/sidebar
- [ ] `pytest` zielony, `vue-tsc` zielony
- [ ] E2E `07-deliveries.spec.ts` smoke zielony
- [ ] Smoke `01-login.spec.ts` zielony (regresja)
- [ ] Spec sync: `02_backend_api.md` (nowy endpoint), `03_frontend_screens.md` (nowy widok), `06_navigation_flow.md` (nowy route)

---

### P1-204: Niebieski pasek nagłówka PDF — marginesy boczne aligned z contentem

```yaml
id: P1-204
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates (6 PDF: contract.html, contract_u.html, protocol_zo.html, protocol_zo_nodata.html, protocol_zo_u.html, protocol_zo_nodata_u.html)
migration_impact: no
```

**Opis:** Niebieski pasek nagłówka (`table.hdr` z `background: #1D2B53`) na PDF rozciągał się edge-to-edge (width: 100%). Na ekranie wygląda OK, ale drukarki obcinają boki (nie drukują do krawędzi). Klient chce żeby pasek zaczął się równo z contentem formularzy (z białymi marginesami bocznymi).

**Stan obecny (przed):**
- `table.hdr { width: 100%; }` — pełna szerokość strony
- `.hdr-left { padding: ... 11mm/14mm ... }` — tekst headera miał 11mm/14mm padding wewnętrzny (symulował margines, ale tło niebieskie szło do krawędzi)
- `.content { padding: ... 11mm/14mm ... }` — content miał 11mm (umowy) / 14mm (protokoły) margines boczny

**Fix:**
- `table.hdr { width: calc(100% - 22mm); margin: 0 11mm; }` (umowy) / `width: calc(100% - 28mm); margin: 0 14mm;` (protokoły) — niebieski pasek z marginesami = aligned z contentem
- `.hdr-left` / `.hdr-right` — padding wewnętrzny z 11mm/14mm → 10px (tekst nadal ma mały inset od krawędzi niebieskiego, ale nie podwójny)

**Zadania:**
1. `contract.html` — `table.hdr` + `.hdr-left` + `.hdr-right` (margin 11mm, padding 10px)
2. `contract_u.html` — to samo
3. `protocol_zo.html` — `table.hdr` + `.hdr-left` + `.hdr-right` (margin 14mm, padding 10px)
4. `protocol_zo_nodata.html` — to samo
5. `protocol_zo_u.html` — to samo
6. `protocol_zo_nodata_u.html` — to samo

**Definition of Done:**
- [x] Niebieski pasek nagłówka we wszystkich 6 PDF ma marginesy boczne = padding contentu
- [x] Pasek zaczyna się i kończy równo z contentem formularzy
- [x] Tekst w headerze zachowuje czytelny inset (10px od krawędzi niebieskiego)
- [x] Brak zmian w innych sekcjach PDF
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML/CSS)

---

### P1-203: Protokół S — usunąć tekst "poziom uzupełnienia zbiornika/naładowania"

```yaml
id: P1-203
status: dev-verified
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/reports/templates/protocol_zo.html + protocol_zo_nodata.html
migration_impact: no
```

**Opis:** W PDF protokołu S (z danymi i nodata) jest linia "poziom uzupełnienia zbiornika/naładowania: ......................................." — klient chce usunąć ten tekst, zostawić pustą linię żeby nie zakłócić porządku na formularzu.

**Zadania:**
1. `backend/reports/templates/protocol_zo.html:165` — usunąć tekst z `div.fuel-line`, zostawić pusty `&nbsp;` (zachować div dla layoutu)
2. `backend/reports/templates/protocol_zo_nodata.html:131` — to samo

**Definition of Done:**
- [x] PDF protokołu S (z danymi) nie ma tekstu "poziom uzupełnienia zbiornika/naładowania"
- [x] PDF protokołu S (nodata) nie ma tego tekstu
- [x] Pusta linia zachowana (layout bez zmian — `div.fuel-line` z `&nbsp;`)
- [x] Brak zmian w protokole U (nie miał tej linii)
- [x] Smoke `01-login.spec.ts` zielony (zmiana w template HTML)

---

### P1-202: Rozdzielenie `contracts.notes` na `notes_contract` + `notes_protocol`

```yaml
id: P1-202
status: triaged
priority: P1
created: 2026-07-21
source: client-request (uwagi 2026-07-21)
component: backend/contracts (model+schema+service) + backend/reports/templates (4 PDF) + frontend/ContractFormView + DB migracja
migration_impact: yes (ALTER TABLE contracts: ADD 2 + backfill + DROP old)
decisions:
  ui: 2 textarea obok siebie ("Uwagi do umowy" + "Uwagi do protokołu")
  migration: ADD 2 + backfill + DROP old notes
  backfill: notes -> notes_protocol (stare uwagi = uwagi do protokołu, bo obecnie notes był tylko na protokole)
```

**Kontekst (stan obecny — analiza 2026-07-21):**
- `contracts.notes` (TEXT, nullable) — jedna kolumna w DB (`backend/contracts/models.py:29`)
- **PDF umowy S** (`contract.html`): `contract.notes` **usunięte** z sekcji "Uwagi" (komentarz `Zg3: contract.notes usunięte z umowy — uwagi mają być tylko na protokole`). Sekcja "Uwagi" ma 4 sztywne akapity (Doba wynajmu, Zgłoszenie zwrotu, Naliczanie, Dokumentacja zdjęciowa) i tyle.
- **PDF umowy U** (`contract_u.html`): też usunięte (komentarz `Puste notes = pusty blok uwag`).
- **PDF protokołu S** (`protocol_zo.html:214` + `protocol_zo_nodata.html:164`): `{% if contract.notes %}<div ...>{{ contract.notes }}</div>{% endif %}` — wyświetla `contract.notes` w sekcji "UWAGI BOX".
- **PDF protokołu U** (`protocol_zo_u.html:192` + `protocol_zo_nodata_u.html:139`): to samo.
- **Formularz** (`ContractFormView.vue:206-208`): jedno textarea `form.notes`, label "Uwagi".
- **Backend schemas** (`contracts/schemas.py`): `notes` w ContractOut/ContractCreate/ContractUpdate + 2 w settlement-related.
- **Backend service** (`contracts/service.py:100`): `notes` w liście mutowalnych pól; `:660`, `:760` — kopiowanie `c.notes` w response.

**Cel:** Rozdzielić na 2 niezależne pola, żeby operator mógł wpisać różne uwagi na umowę i na protokół. Obecnie `notes` = tylko protokół (umowa ma 4 sztywne akapity i nie czyta `notes`). Po zmianie:
- `notes_contract` → renderowane na PDF umowy (S i U) pod 4 sztywnymi akapitami (lub zamiast, do ustalenia w implementacji)
- `notes_protocol` → renderowane na PDF protokołu (S i U, z nodata wariantami) — zachowanie obecne

**Zadania:**

**Faza 1 — DB (deterministyczna migracja):**
1. `spec/core/01_database.md` — zaktualizować DDL `contracts`: usunąć `notes TEXT`, dodać `notes_contract TEXT NULL` + `notes_protocol TEXT NULL`
2. `backend/contracts/models.py:29` — zastąpić `notes = Column(Text, nullable=True)` dwiema kolumnami
3. `backend/main.py` startup migrations — 4 operacje w jednej transakcji (forward-only, idempotentne):
   ```python
   # 1. ADD notes_contract (IF NOT EXISTS)
   await conn.execute(sa.text(
       "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_contract TEXT NULL"
   ))
   # 2. ADD notes_protocol (IF NOT EXISTS)
   await conn.execute(sa.text(
       "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS notes_protocol TEXT NULL"
   ))
   # 3. Backfill: notes -> notes_protocol (tylko gdy notes_protocol IS NULL, żeby nie nadpisać przy re-run)
   await conn.execute(sa.text(
       "UPDATE contracts SET notes_protocol = notes "
       "WHERE notes IS NOT NULL AND notes_protocol IS NULL"
   ))
   # 4. DROP notes (IF EXISTS) — wymaga MariaDB 10.6+ dla IF EXISTS; fallback try/except
   try:
       await conn.execute(sa.text("ALTER TABLE contracts DROP COLUMN IF EXISTS notes"))
   except Exception:
       pass  # MariaDB <10.6 bez IF EXISTS — pominąć, kolumna zostanie (deprecated)
   ```
4. Weryfikacja: restart backendu × 2 (pierwszy = migracja, drugi = bez błędu "Duplicate column") + `DESCRIBE contracts` (brak `notes`, są `notes_contract` + `notes_protocol`)

**Faza 2 — Backend:**
5. `backend/contracts/schemas.py` — zastąpić `notes` przez `notes_contract` + `notes_protocol` w ContractOut/Create/Update (linie 230, 267, 314, 362, 391, 403, 410)
6. `backend/contracts/service.py:100` — zaktualizować listę mutowalnych pól (zastąpić `notes` przez 2 nowe)
7. `backend/contracts/service.py:660, 760` — zaktualizować response (kopiować `notes_contract` + `notes_protocol`)
8. `backend/migrate.py` (skrypt migracji starych danych) — zaktualizować mapowanie `przedplata_kwota, przedplata_dokument, uwagi` → `..., notes_protocol` (linia 322, 345)

**Faza 3 — PDF templates:**
9. `backend/reports/templates/contract.html` — dodać render `contract.notes_contract` w sekcji "Uwagi" (po 4 sztywnych akapitach, z `<div class="inne-item">` lub podobnym stylem — decyzja wizualna w implementacji)
10. `backend/reports/templates/contract_u.html` — to samo
11. `backend/reports/templates/protocol_zo.html:214` — zmienić `contract.notes` → `contract.notes_protocol`
12. `backend/reports/templates/protocol_zo_nodata.html:164` — to samo
13. `backend/reports/templates/protocol_zo_u.html:192` — to samo
14. `backend/reports/templates/protocol_zo_nodata_u.html:139` — to samo

**Faza 4 — Frontend:**
15. `frontend/src/views/ContractFormView.vue:204-208` — zastąpić 1 textarea dwoma obok siebie (form-row-2):
    - "Uwagi do umowy" → `v-model="form.notes_contract"`
    - "Uwagi do protokołu" → `v-model="form.notes_protocol"`
16. `frontend/src/views/ContractFormView.vue:1123` — `notes: ''` → `notes_contract: '', notes_protocol: ''` w `initialForm`
17. `frontend/src/views/ContractFormView.vue:1675` — zaktualizować listę białych pól mutowalnych (zastąpić `notes` przez 2 nowe)
18. `frontend/src/stores/contracts.ts` (jeśli jest typ `Contract`) — zaktualizować typ
19. `frontend/src/views/ArchiveView.vue:117` — jeśli pokazuje `prepayment_amount`, sprawdzić czy nie pokazuje też `notes` (zaktualizować jeśli tak)
20. `frontend/src/stores/archive.ts:24, 103` — zaktualizować typ jeśli ma `notes`

**Faza 5 — Weryfikacja:**
21. `pytest -x --tb=short` — backend testy (po aktualizacji testów używających `notes`)
22. `vue-tsc --noEmit` — frontend typecheck
23. Smoke `e2e/tests/01-login.spec.ts` — zielony
24. Manual: wygeneruj PDF umowy S z `notes_contract` wypełnione → uwagi na umowie; wygeneruj protokół S z `notes_protocol` → uwagi na protokole; oba puste → brak uwag na PDF
25. Regresja: PDF umowy bez zmian w 4 sztywnych akapitach; PDF protokołu bez zmian w stylu "UWAGI BOX"

**Ryzyka:**
- **DROP COLUMN `notes`** = hard stop wg reguł (reguła nienaruszalna #6: DROP/TRUNCATE = hard stop). User wyraźnie zaakceptował w pytaniu (2026-07-21) — OK.
- **MariaDB <10.6** — `DROP COLUMN IF EXISTS` nieobsługiwane. Fallback `try/except` — kolumna `notes` zostanie w DB (deprecated), kod jej nie używa. Akceptowalne.
- **Skrypt `backend/migrate.py`** — jednorazowy skrypt migracji starych danych (legacy WinForms). Jeśli nie będzie już używany (prod już zmigrowane), można pominąć aktualizację. Zweryfikować w implementacji.
- **Stare umowy** — po backfill `notes_protocol = notes`, stare uwagi nadal na protokole (zachowanie obecne). `notes_contract = NULL` → puste na umowie (nowe pole, brak danych). Jeśli user chce skopiować stare uwagi też na umowę — dodatkowy backfill (ale user wybrał `notes -> notes_protocol` tylko).
- **4 sztywne akapity na umowie** — pozostają. `notes_contract` renderowane po nich. Jeśli user chce je usunąć/zastąpić — osobny task.

**Definition of Done:**
- [ ] DB: `contracts` ma `notes_contract` + `notes_protocol`, nie ma `notes` (lub `notes` deprecated gdy MariaDB <10.6)
- [ ] Backfill: stare `notes` skopiowane do `notes_protocol` (gdzie `notes_protocol IS NULL`)
- [ ] Restart backendu ×2 bez błędu (idempotentne)
- [ ] Backend schemas/service: `notes` zastąpione przez 2 nowe pola
- [ ] PDF umowy S/U: `contract.notes_contract` renderowane w sekcji "Uwagi"
- [ ] PDF protokołu S/U (z nodata): `contract.notes_protocol` renderowane (zachowanie obecne)
- [ ] Formularz umowy: 2 textarea obok siebie (Uwagi do umowy + Uwagi do protokołu)
- [ ] `pytest` zielony, `vue-tsc` zielony
- [ ] Smoke `01-login.spec.ts` zielony
- [ ] Manual: PDF umowy z `notes_contract` → uwagi widoczne; PDF protokołu z `notes_protocol` → uwagi widoczne
- [ ] Spec sync: `01_database.md`, `02_backend_api.md`, `03_frontend_screens.md`, `11_reports_stats.md`

---

---

## 🟡 P2 — Should-Have

*Brak aktywnych P2.*

---

## 🟢 P3 — Nice-to-Have

*Brak*

---

## 📝 Nowe uwagi (do triage'u)

> **Instrukcja:** Wklej nowe uwagi poniżej. Po analizie Tech Lead zaklasyfikuje je (P0/P1/P2/P3) i utworzy taski z YAML front-matter w odpowiednich sekcjach powyżej.

<!-- Wklej uwagi tutaj -->

---

## ✅ Done — Ukończone zadania

*Brak done w bieżącym sprincie. Historia w `archiwum/`.*
