# RAO Backlog — Nowy sprint

> **Status:** Czysty arkusz (2026-07-05)
> **Poprzedni backlog:** Zarchiwizowany w `spec/backlog/archiwum/BACKLOG_SPRINT_20260525_20260705.md`
> **Decision log:** `spec/backlog/DECISION_LOG.md` — pełna historia decyzji (co, dlaczego, status)
> **Cel:** Nowe zadania będą dodawane na podstawie współpracy z klientem

---

## ℹ️ Zasady

- Nowe taski dodawane na podstawie wymagań klienta / operatora
- Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
- Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
- Po zakończeniu zadania → lokalny commit + update `DECISION_LOG.md`
- Każda decyzja architektoniczna/biznesowa → sekcja w `DECISION_LOG.md`

---

## 🚨 P0 — Production Blockers

### P0-011: ContractFormView — TypeError: inv.total_net.toFixed is not a function

```yaml
id: P0-011
status: triaged
priority: P0
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/ContractFormView (Fakturownia invoices modal)
severity: blocker
```

**Symptom:** W ContractFormView przy wyświetlaniu faktur z Fakturownia:
```
Uncaught (in promise) TypeError: inv.total_net.toFixed is not a function
    at ContractFormView.vue:380:78
```

**Root cause:** `inv.total_net` nie jest number (prawdopodobnie string z API lub null/undefined). Kod próbuje wywołać `.toFixed(2)` na wartości która nie jest number.

**Fix:**
- Dodaj typecasting: `Number(inv.total_net).toFixed(2)` lub fallback `inv.total_net?.toFixed(2) ?? '0.00'`
- Sprawdzić backend schema dla Fakturownia invoice response — czy `total_net` jest number czy string
- Jeśli backend zwraca string → fix w backend (zwracaj number), jeśli number → fix w frontend (safe casting)

**Lokalizacja:** `frontend/src/views/ContractFormView.vue:380`

---

### P0-001: `/stats/currently-rented` zwraca 500 — Pydantic ValidationError

```yaml
id: P0-001
status: done
priority: P0
created: 2026-07-05
reporter: Devin (session 2026-07-05)
component: backend/stats
severity: blocker
```

**Symptom:** `GET /rao/api/stats/currently-rented` → 500 Internal Server Error.
Blokada: AnalyticsView → LiveFleet tab (`/rao/analytics`) nie renderuje tabeli.
E2E test `06-analytics.spec.ts:26` (TEST-01: LiveFleet) failuje (1/205 e2e).

**Root cause:** `stats/router.py:311-315` tworzy `CurrentlyRentedItem(id=r[0], ...)`,
ale schema `stats/schemas.py:30` wymaga pola `article_id: int` (brak aliasu `id`).
Pydantic v2 rzuca `ValidationError: article_id Field required`.

**Fix:** zmienić `id=r[0]` → `article_id=r[0]` w `stats/router.py:312`.

**Weryfikacja:**
- `curl /rao/api/stats/currently-rented` → 200 + JSON z `items[]`
- E2E `06-analytics.spec.ts:26` → PASS
- AnalyticsView `/rao/analytics` → LiveFleet tab pokazuje tabelę maszyn

---

### P0-002: AnalyticsView — brak scrolla w dół (treść ucięta)

```yaml
id: P0-002
status: done
priority: P0
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/views/AnalyticsView
severity: blocker
```

**Symptom:** `http://localhost:5173/rao/analytics` — nie da się przewijać w dół.
Treść pod tabelą / sekcjami jest niedostępna (ucięta).

**Podejrzany plik:** `frontend/src/views/AnalyticsView.vue` (style: `overflow: hidden`
lub brak `overflow-y: auto` na kontenerze, ew. `height: 100vh` bez scrolla).

**Fix (propozycja):** sprawdzić `.analytics-view` i parent layout — usunąć
`overflow: hidden`, dodać `overflow-y: auto` na scrollowalnym kontenerze.

---

### P0-003: Znak `$` (jedna kreska) kojarzy się z USD — niedopuszczalne

```yaml
id: P0-003
status: done
priority: P0
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend (globalne)
severity: blocker
```

**Symptom:** W UI używany jest znak `$` z jedną kreską pionową, który silnie
kojarzy się z dolarem amerykańskim (USD). W polskiej aplikacji wynajmu maszyn
jest to niedopuszczalne — należy używać `zł` lub `PLN`.

**Zakres:** wszystkie miejsca w UI gdzie pojawia się `$` (placeholder, PDF,
raporty, formularze, tabele). Wymaga audytu globalnego.

**Fix (propozycja):**
- Zamienić wszystkie `$` na `zł` w frontend (formatowanie waluty)
- Sprawdzić `frontend/src/utils/format.ts` lub podobne (formatter waluty)
- Sprawdzić szablony PDF (`backend/reports/templates/*.html`)
- Sprawdzić czy `$` nie jest używane jako symbol zmiennej w treściach (np. `$1`, `$2` w opisach opłat — tam zamienić na `{{ }}` lub `zł`)

---

### P0-004: Eksplorator — kontrahent jako dropdown (select) zamiast wyszukiwarki

```yaml
id: P0-004
status: done
priority: P0
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/components/analytics/ExplorerTab + AnalyticsFilters
severity: blocker
```

**Symptom:** W Eksploratorze (`/rao/analytics` → tab Eksplorator) kontrahent
jest zwykłym dropdownem (`<select>`). Przy dużej liczbie kontrahentów (698 w DB)
zwykły select jest nieużywalny — nie da się wyszukać po nazwie.

**Wymaganie:** Kontrahent musi być comboboxem (dropdown wpisywalny) —
pole tekstowe z autouzupełnianiem, filtrujące listę w miarę wpisywania.

**Podejrzany plik:** `frontend/src/components/analytics/AnalyticsFilters.vue`
(`data-testid="filter-contractor"` — obecnie `<select>`).

**Fix (propozycja):**
- Zamienić `<select>` na combobox (input + dropdown z filtrowaniem)
- Lub użyć istniejący komponent `ContractorPicker` jeśli istnieje
- Filtr po nazwie (case-insensitive, substring match)
- Backend już wspiera `?contractor_id=` — frontend musi wysłać ID wybranego
- Sprawdzić czy ten sam filtr jest używany w innych tabach (PeriodRental, Locations) —
  jeśli tak, naprawa w jednym miejscu (`AnalyticsFilters.vue`) pokryje wszystkie

---

### P0-005: Wszystkie umowy mają mieć prefiks `S` w numerze (niezależnie od typu)

```yaml
id: P0-005
status: done
priority: P0
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/contracts (generowanie numeru umowy)
severity: blocker
```

**Symptom:** Umowy mają różne prefiksy w zależności od typu (najem S, usługa U).
W bazie widać numery: `S001/2026`, `U043/2026G`, `S047/2026` itd.

**Wymaganie:** Wszystkie umowy mają się nazywać z prefiksem `S` —
niezależnie czy to najem czy usługa. Prefiks `U` jest niedopuszczalny.

**Podejrzany plik:** `backend/contracts/service.py` (logika generowania numeru
umowy — prawdopodobnie switch/if na `contract_type` wybierający literę).

**Fix (propozycja):**
- Zmienić generator numeru umowy: zawsze `S` zamiast warunkowego `S`/`U`
- Sprawdzić czy istniejące umowy z `U` wymagają renaminowania (migacja danych?)
  — prawdopodobnie tak, zapytać operatora
- Zaktualizować testy e2e/unit które zakładają prefiks `U`
- Zaktualizować `spec/core/04_business_logic.md` (reguła numeracji umów)

---

### P1-001: Predefiniowane cenniki warunków rozliczenia maszyn + auto-prefill z historii

```yaml
id: P1-001
status: dev-verified
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/settings + backend/contracts + frontend/ConditionPanel + frontend/SettingsView
severity: high
size: M (cross-stack)
done_date: 2026-07-05
verification:
  dev:
    - "Backend: 12 endpointów (10 settings + apply-preset + last-conditions), 53 testy pass, commit 7909e0e"
    - "Frontend: RatePresetSection.vue (CRUD w ArticleFormView), ConditionPanel apply-preset + auto-prefill, SettingsView overview tab"
    - "vue-tsc --noEmit: PASS, npm run build: PASS (ArchiveView.vue pre-existing issue excluded)"
    - "Snapshot principle: apply-preset kopiuje warunki (brak FK), edycja cenniku nie wpływa na istniejące umowy"
    - "Guard 409: apply-preset na rozliczonej umowie (is_settled=true) → HTTPException 409"
    - "Auto-prefill: GET /articles/{id}/last-conditions (404 gdy brak historii → toast info)"
```

**Symptom:** Warunki rozliczenia maszyn (PositionCondition) trzeba wpisywać ręcznie
dla każdej pozycji umowy. Ta sama maszyna w kolejnej umowie wymaga ponownego wpisywania
3 progów kaskadowych (~18 pól). Frustracja + ryzyko literówki w cenie → błędna faktura.

**Feature parity:** Stara aplikacja WinForms (FormW.cs) MIAŁA kopiowanie z historii
umów tej samej maszyny (btnprev/btnnext, "Skopiuj", "X historycznych rozliczeń").
To jest odtworzenie + ulepszenie tej funkcji.

**Decyzja operatora (2026-07-05):**
- **Model:** hybryda (a)+(c) z odwróconym priorytetem
  - Auto-prefill = warunki z **ostatniej umowy** tej maszyny (NIE domyślny cennik)
  - Predefiniowane cenniki nazwane per maszyna (dostępne przez "Zastosuj cennik")
  - Wiele cenników per maszyna (np. "Standard", "Promo", "Długoterminowy")
- **Auto-prefill:** banner "Zastosuj/Pomiń/Zmień" — NIE auto-apply (unika zaskoczenia)
- **Snapshot:** warunki zapisane jako kopia na pozycji (NIE referencja do cennika)
- **"Zapisz jako cennik":** TAK w v1, z poziomu umowy (po edycji warunków)
- **Edycja w locie:** po zastosowaniu można edytować (snapshot, zmiana tylko na tej pozycji)

**Flow użytkownika:**
1. Dodajesz maszynę do umowy → auto-prefill z ostatniej umowy (banner)
2. Banner: "Ostatnie warunki: umowa S047/2026 z 2026-06-15 — [Zastosuj] [Pomiń] [Zmień ▾]"
3. "Zastosuj" → warunki skopiowane jako snapshot (nowe PositionCondition)
4. "Zmień ▾" → dropdown z predefiniowanymi cennikami tej maszyny
5. Edycja w locie → zmiana tylko na tej pozycji
6. "Zapisz jako cennik" → modal: nazwa + "Ustaw jako domyślny dla tej maszyny"
7. "Zastosuj cennik" (przycisk w header) → modal z listą cenników + podgląd + confirm

**Model danych (Tech Lead):**
- `article_rate_presets` (nazwane cenniki per maszyna)
  - id, company_id, article_id (FK articles, CASCADE), name, description,
    is_default, sort_order, created_at, updated_at
- `article_rate_preset_items` (progi cennika — 1:1 z PositionCondition)
  - id, preset_id (FK article_rate_presets, CASCADE), sort_order,
    rate_type_id, description, rate1, rate2, billing_label, period_count, minimum
- Brak FK z PositionCondition do cennika (snapshot, nie referencja)
- Brak ALTER na istniejących tabelach (tylko nowe przez create_all)

**Endpointy (Tech Lead):**
- `GET /settings/articles/{article_id}/rate-presets` — lista cenników maszyny
- `POST /settings/articles/{article_id}/rate-presets` — utwórz cennik
- `GET /settings/rate-presets/{preset_id}` — cennik z items
- `PUT /settings/rate-presets/{preset_id}` — edytuj cennik
- `DELETE /settings/rate-presets/{preset_id}` — usuń cennik
- `POST /settings/rate-presets/{preset_id}/items` — dodaj warunek do cennika
- `PUT /settings/rate-presets/items/{item_id}` — edytuj warunek
- `DELETE /settings/rate-presets/items/{item_id}` — usuń warunek
- `PATCH /settings/rate-presets/{preset_id}/set-default` — ustaw domyślny
- `GET /articles/{article_id}/last-conditions` — auto-prefill z ostatniej umowy
- `POST /contracts/{id}/positions/{pos_id}/conditions/apply-preset` — zastosuj cennik

**Frontend (UX Designer — lokalizacja cenników):**
- **PRIMARY (CRUD):** `ArticleFormView.vue` → nowa sekcja "Cenniki rozliczenia"
  obok istniejącej "Rezerwacje maszyny" (tryb edit, v-if isEdit)
  - Pattern preset-card z expand/collapse (spójny z fee-presets w SettingsView)
  - Jeden cennik rozwinięty na raz (expandedPresetId)
  - `[Domyślny]` badge widoczny bez expand
  - `[+ Nowy cennik]` inline form (nazwa + checkbox "Ustaw jako domyślny"), NIE modal
  - Edycja progów inline w tabeli (✎ → inputy → Enter/Esc), NIE modal
  - Sortowanie progów: przyciski ↑↓ (prostsze niż drag, działa na mobile)
  - Empty state: "Ta maszyna nie ma jeszcze cenników. Utwórz pierwszy,
    aby móc szybko stosować warunki w umowach."
  - Podpowiedź pod sekcją: "Edycja cennika nie zmienia warunków w istniejących
    umowach — one mają własną kopię (snapshot)."
- **SECONDARY (audit overview):** `SettingsView.vue` → nowa zakładka
  "Cenniki rozliczeń maszyn" — READ-ONLY z redirect do karty maszyny
  - Tabela: Maszyna | Cenników | Domyślny | Akcja [Otwórz →] / [Utwórz →]
  - Filtr: Wszystkie / Z cennikiem domyślnym / Bez cennika domyślnego / Bez cenników
  - Search po nazwie maszyny (operator myśli maszynami, nie cennikami)
  - Deep link `#cenniki` — po kliknięciu karta maszyny scrolluje się do sekcji
  - NIE tworzymy tu cenników — tylko mapa nawigacyjna (audit use case)
- `ConditionPanel.vue` (w ContractFormView):
  - Banner auto-prefill (gdy warunki puste + maszyna ma historię/cennik)
  - Przycisk "Zastosuj cennik" (modal z listą + podgląd + confirm)
  - Przycisk "Zapisz jako cennik" (modal z nazwą + "Ustaw jako domyślny")
  - Toast "Cofnij" po zastosowaniu (5s window)
  - Toast po "Zapisz jako cennik" z linkiem "Zobacz w karcie maszyny →"
- Nowy store `ratePresets.ts` (Pinia)
- Walidacja: unikalność (article_id, name), rate1 > 0, rate2 ≤ rate1, periods ≥ 1

**Priorytet źródeł auto-prefill (operator):**
1. Ostatnia umowa z tą maszyną (główne źródło, feature parity)
2. Predefiniowany cennik domyślny (opcja przez "Zmień ▾")
3. Brak danych → pusta tabela (ręczne wpisywanie)

**Edge cases:**
- Maszyna wynajmowana pierwszy raz → brak auto-prefill, empty state z CTA
- Maszyna z cennikiem "Standard" ale klient ma inną cenę → "Pomiń" lub edytuj po zastosowaniu
- Operator chce jednorazową cenę → "Pomiń" + ręczne + NIE zapisuj jako cennik
- Cennik domyślny zmieniony w ustawieniach → istniejące umowy NIE dotknięte (snapshot)
- Dwie pozycje z tą samą maszyną w jednej umowie → każda ma własny banner/warunki

**DoD:**
- [ ] Backend: 11 endpointów + 2 modele + schemas + service
- [ ] Frontend: zakładka w ustawieniach + banner + 2 modale + store
- [ ] E2E: dodaj maszynę z historią → banner → Zastosuj → warunki skopiowane → edytuj → zapisz jako cennik
- [ ] Test: zmiana ceny w starej umowie NIE zmienia skopiowanych warunków (snapshot)
- [ ] Spec sync: 01_database.md, 02_backend_api.md, 03_frontend_screens.md, 04_business_logic.md

---

### P0-006: ContractFormView — checkboxy niepowiązane z dokumentami PDF

```yaml
id: P0-006
status: done
priority: P0
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/ContractFormView + backend/reports/templates
severity: blocker
```

**Symptom:** W formularzu nowej umowy (`/rao/contracts/new`) są checkboxy/pola
które NIE wpływają na generowane dokumenty PDF. Użytkownik zaznacza opcję,
ale PDF ignoruje ją — błędne oczekiwanie, że dokument będzie inny.

**Audyt checkboxów/pól w ContractFormView.vue:**

| Linia | Pole | W PDF? | Status |
|-------|------|--------|--------|
| 159 | `show_person1` (Drukuj osobę 1) | ❌ NIE | **BROKEN** — checkbox w UI, ale szablon PDF zawsze drukuje `contact_person1` bez warunku `{% if contract.show_person1 %}` |
| 167 | `show_person2` (Drukuj osobę 2) | ❌ NIE | **BROKEN** — j.w. dla `contact_person2` |
| 191 | `hide_delivery_address` | ✅ TAK | OK — `contract.html:152`, `contract_u.html:138` |
| 192 | `signatures_on_page1` | ✅ TAK | OK — `contract.html:253`, `contract_u.html:225` |
| 137 | `prepayment_document` (pole tekstowe) | ❌ NIE | **BROKEN** — pole w UI, ale PDF używa tylko `prepayment_amount` (liczba), nie `prepayment_document` (opis) |
| 145 | `invoice_document` (pole tekstowe) | ❌ NIE | **BROKEN** — pole w UI, brak w PDF |
| 298 | `editingFeeData.is_active` | ✅ TAK | OK — `contract.html:217` filtruje `fees if fd.fee.is_active` |
| 331 | `newFeeData.is_active` | ✅ TAK | OK — j.w. |
| 864 | `inlineArticleForm.is_service` | ✅ TAK | OK — wpływa na typ artykułu |
| 869 | `inlineArticleForm.is_external` | ✅ TAK | OK — wpływa na statystyki floty |

**Root cause:**
1. `show_person1`/`show_person2` — pola istnieją w DB (`contracts/models.py:36`),
   w schema, w service — ale szablon PDF `contract.html:163` i `contract_u.html:149`
   robią `{{ contract.contact_person1 or '' }}` bez sprawdzania `show_person1`.
   Checkbox "Drukuj" jest martwy — nic nie kontroluje.
2. `prepayment_document` / `invoice_document` — pola tekstowe w UI (opis dokumentu
   przedpłaty/faktury), ale PDF pokazuje tylko kwotę (`prepayment_amount`).
   Opis dokumentu nigdy nie trafia do PDF.

**Pliki do naprawy:**
- `backend/reports/templates/contract.html:163,167` — dodać `{% if contract.show_person1 %}...{% endif %}`
- `backend/reports/templates/contract_u.html:149,153` — j.w.
- `backend/reports/templates/protocol_zo*.html` — sprawdzić czy też drukują osoby bez warunku
- `backend/reports/templates/contract.html` + `contract_u.html` — dodać `prepayment_document` i `invoice_document` jeśli mają sens biznesowy
- Lub usunąć martwe checkboxy z UI jeśli nie ma potrzeby drukowania

**Decyzja biznesowa (odpowiedzi operatora 2026-07-05):**
- ✅ "Drukuj" dla osób kontaktowych → TAK, ma ukrywać osobę w PDF gdy odznaczone
- ❌ `prepayment_document` / `invoice_document` → NIE ma być na PDF umowy
  (potwierdzone audytem starej aplikacji WinForms: pola zapisywane do DB,
  wyświetlane w DataGridView, ale **NIE używane w raportach Crystal Reports** —
  sprawdzone binarnie w `Umowa.rpt`, `Umowa2.rpt`, `UmowaU.rpt`: NOT FOUND)
- ✅ Checkboxy domyślnie zaznaczone → TAK dla "Drukuj" (show_person1/2)
  (zgodne z DB `default=True`)

**Zakres naprawy:**
1. `show_person1`/`show_person2` — dodać warunek `{% if contract.show_person1 %}`
   w `contract.html:163`, `contract_u.html:149` (i analogicznie dla osoby 2)
2. `prepayment_document` / `invoice_document` — **usunąć z UI** (pola "Dok. przedpłaty"
   i "Dok. faktury" w `ContractFormView.vue:137,145`) lub zostawić jako info wewnętrzne
   (nie na PDF). Decyzja: usunąć z UI, bo w starej aplikacji też nie trafiały do PDF.
   Pola w DB/schema zostawić (migracja danych z starej bazy je zachowuje).

---

## 🔴 P1 — Must-Have

### P1-012: Archiwum maszyn — kaskada kategorii NIE działa (regresja P1-002)

```yaml
id: P1-012
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/ArchiveView (zakładka Maszyny)
severity: high
```

**Symptom:** W Archiwum → zakładka "Maszyny" filtr kategorii jest nadal płaskim `<select>` z 67 opcjami (ogólna, Podesty ruchome, Podesty nozycowe, Wózki widłowe, itd.). Kaskada 3-poziomowa (główna → sub1 → sub2) nie działa.

**Oczekiwane:** P1-002 miało zaimplementować kaskadę kategorii z breadcrumbem, ale w UI nadal jest płaski select.

**HTML aktualny:**
```html
<select class="form-control form-control-xs" style="width: 200px;">
  <option>— brak kategorii —</option>
  <option value="24">Akcesoria</option>
  <option value="37">Hak obrotowy</option>
  <option value="25">HDS</option>
  <option value="2">ogólna</option>
  <option value="3">Podesty ruchome</option>
  <option value="4">Podesty nozycowe</option>
  <option value="20">Wózki widlowe</option>
  <!-- ... 67 opcji total ... -->
</select>
```

**Wymagane:**
- Sprawdzić czy commit P1-002 (`72ac1c2`) został wdrożony do frontendu
- Jeśli tak → fix kaskady (prawdopodobnie nie podpięto do articleFilters.category_id)
- Jeśli nie → wdrożyć zmiany z P1-002 (ArchiveView.vue cascade + categoriesTree)

**Powiązane:** P1-002 (marked done, ale nie działa w UI — regresja)

---

### P1-002: Archiwum maszyn — drilldown kategorii przy wyborze i filtrowaniu

```yaml
id: P1-002
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/views/ArchiveView (maszyny)
severity: high
```

**Symptom:** W Archiwum maszyn zmiana kategorii jest słabo widoczna.
Brak drilldownu do przechodzenia od kategorii głównej → podkategorii
gdy użytkownik wybiera i filtruje.

**Wymaganie:** Fajniejszy drilldown kategorii (kaskada: główna → sub1 → sub2)
przy wyborze i filtrowaniu w Archiwum. Obecnie jest płaski select.

**Fix (propozycja):**
- Użyć istniejącego komponentu kaskady kategorii (jak w ArticleFormView)
- Filtrowanie z breadcrumbem pokazującym wybraną ścieżkę
- Klik w kategorię główną → rozwija podkategorie inline

---

### P1-003: Pulpit (Dashboard) — zły wygląd, złe formatowanie, wąski na ekranie

```yaml
id: P1-003
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/views/DashboardView
severity: high
```

**Symptom:** Pulpit (`/rao/home`) ma zły wygląd — złe formatowanie,
jest wąski na ekranie (nie wykorzystuje pełnej szerokości).

**Fix (propozycja):**
- Audyt layoutu DashboardView — usunąć niepotrzebne `max-width` ograniczenia
- Karty KPI w gridzie responsywnym (auto-fill, minmax)
- Wykresy pełnej szerokości kontenera
- Sprawdzić czy parent layout nie narzuca wąskiego kontenera

---

### P1-004: Demo seed — tylko 1 aktywna umowa, potrzeba 10+ aktywnych gotowych do pobrania z FA

```yaml
id: P1-004
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/seed_demo_data.py + backend/seed_fa_invoices.py
severity: high
```

**Symptom:** Po seedzie demo tylko 1 aktywna umowa jest gotowa do pobrania
z Fakturowni. Operator chce conajmniej 10 aktywnych umów gotowych do
pobrania danych z FA (demo integracji).

**Wymaganie:**
- 10+ aktywnych umów (date_to >= today) z fakturami czekającymi w FA
- Każda z nich po kliknięciu "Pobierz z Fakturowni" → rozliczenia tworzą się na żywo
- Obecnie Pula C (FA-pending) ma 16 umów ale wszystkie są NIEROZLICZONE/zakończone
- Potrzeba: aktywnych umów (w trakcie wynajmu) z fakturami w FA gotowymi do pobrania

**Fix (propozycja):**
- Dodać pulę D: 10+ aktywnych umów (date_to w przyszłości) z fakturami w FA
- seed_fa_invoices.py: wystawić faktury dla aktywnych umów (bez settlements)
- Demo flow: user widzi aktywną umowę → "Pobierz z FA" → rozliczenia na żywo

---

### P1-005: Błąd pobierania produktów z Fakturownia w /articles/14145/edit

```yaml
id: P1-005
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/integrations/fakturownia + frontend/ArticleFormView
severity: high
```

**Symptom:** `http://localhost:5173/rao/articles/14145/edit` —
błąd pobierania produktów z Fakturownia.

**Do zdiagnozowania:**
- Sprawdzić console network tab — jaki endpoint i jaki błąd (500/401/422?)
- Sprawdzić `GET /integrations/fakturownia/products` — czy działa
- Sprawdzić czy article 14145 ma `fakturownia_product_id` ustawione
- Sprawdzić czy FA_TOKEN jest skonfigurowany w ustawieniach (nie w env)
- Może integracja FA jest WYŁĄCZONA w ustawieniach (verify step 5 fail)

**Fix (propozycja):**
- Odtworzyć błąd (curl + frontend)
- Sprawdzić `integrations/fakturownia/service.py:fetch_products`
- Sprawdzić czy `FakturowniaSettings` w DB ma token (nie tylko env)
- Naprawić + test e2e

---

### P1-006: Ikona `$` (SVG z jedną kreską) kojarzy się z USD — zmienić ikonkę

```yaml
id: P1-006
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend (globalne — SVG icon)
severity: high
related: P0-003
```

**Symptom:** SVG ikona z jedną kreską pionową (przypomina `$` ale z jedną kreską)
silnie kojarzy się z USD. W polskiej aplikacji wynajmu maszyn jest to mylące.

**SVG (z DOM):**
```html
<svg class="app-icon" width="22" height="22" viewBox="0 0 24 24">
  <line x1="12" y1="2" x2="12" y2="22"></line>
  <path d="M17 6.5C17 5 15 4 12 4S7 5 7 7s2 3 5 3 5 1 5 3-2 3-5 3-5-1-5-2.5"></path>
</svg>
```

**Wymaganie:** Zaproponować inną ikonkę (nie przypominającą waluty USD).
Opcje: ikona umowy/dokumentu, ikona maszyny, ikona wynajmu, lub po prostu `zł`.

**Fix (propozycja):**
- Znaleźć gdzie ten SVG jest używany (grep `app-icon` + ten path)
- Zamienić na ikonę neutralną (np. dokument, klucz, maszyna)
- Lub użyć tekstowego `zł` zamiast SVG
- Powiązane z P0-003 (globalne usuwanie `$` z UI)

---

### P1-007: /analytics — po seedzie brak pozycji dodatkowych (usług) w demo

```yaml
id: P1-007
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/seed_demo_data.py + frontend/AnalyticsView
severity: high
```

**Symptom:** `http://localhost:5173/rao/analytics` po seedzie nie pokazuje
pozycji dodatkowych (usług). Usługi nie działają i nie ma ich w demo.

**Wymaganie:**
- Seed powinien pokazywać wszystkie usługi w /analytics
- NIE musi być jako "Pozycje dodatkowe" — może być jako standardowe pozycje
- Usługi (article_type='usługa') mają być widoczne w statystykach/analityce

**Fix (propozycja):**
- Sprawdzić czy seed_demo_data.py tworzy usługi jako pozycje umów
- Sprawdzić czy AnalyticsView filtruje po article_type (może ukrywa usługi)
- Sprawdzić czy stats endpointy agregują usługi czy tylko maszyny
- Może trzeba dodać usługi do puli demo jako osobne pozycje w umowach

---

### P1-008: Brak scrolla — ucięty dół ekranu, niedostępny scrollbar

```yaml
id: P1-008
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend (globalne — layout)
severity: high
related: P0-002
```

**Symptom:** Nadal nie można przewijać — dół ekranu jest ucięty
i nie ma żadnego dostępnego scrolla. Problem globalny (nie tylko AnalyticsView).

**Wymaganie:** Wszystkie widoki muszą mieć działający scroll pionowy.

**Fix (propozycja):**
- Audyt globalnego layoutu (App.vue, router-view, parent kontenery)
- Sprawdzić `height: 100vh` + `overflow: hidden` na parentach
- Dodać `overflow-y: auto` na scrollowalnym kontenerze treści
- Test na wszystkich widokach: Dashboard, Contracts, Analytics, Archive, Settings

---

### P1-013: Lokalizacje wynajmu — "(brak PNA — Miasto)" nadal w tabeli (regresja P1-009)

```yaml
id: P1-013
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/AnalyticsView (Locations tab) + backend/stats
severity: high
```

**Symptom:** W tabeli Lokalizacje wynajmu nadal widać "(brak PNA — Miasto)":
```
Kraków    (brak PNA — Kraków)    2    26 280,00 zł
Warszawa  (brak PNA — Warszawa)  2    38 690,00 zł
Katowice  (brak PNA — Katowice)  1    5 280,00 zł
Bydgoszcz (brak PNA — Bydgoszcz) 1    14 850,00 zł
// ... 12 miast total
```

**Problem:** P1-009 miało usunąć bucket "(brak PNA)" z tabeli głównej (skip w `group_by='city'`), ale nadal jest wyświetlany.

**Wymaganie:**
- Kolumna PNA NIE ma być używana do agregacji w tabeli głównej
- Tylko miasto + liczba umów + wartość
- PNA może być w detail view (po kliknięciu)

**Powiązane:** P1-009 (marked done, ale regresja)

---

### P1-014: Analytics — Pozycje dodatkowe (usługi) i kategorie nie są klikalne

```yaml
id: P1-014
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/AnalyticsView (PeriodRentalTab, CategoriesTab)
severity: high
```

**Symptom:** W Analytics tabach "Pozycje dodatkowe" (usługi) i "Kategorie" nie są klikalne. Brak drilldown do szczegółów (jak w "Top maszyny po przychodzie").

**Wymaganie:**
- Pozycje dodatkowe (usługi) — klikalne → drilldown do szczegółów (które umowy, kiedy, kwota)
- Kategorie — klikalne → drilldown do szczegółów (jakie maszyny, umowy, przychód)
- UI podobne do "Top maszyny po przychodzie" (klik wiersz → szczegóły)

---

### P1-017: Pulpit operacyjny (HomeView) — wąski, nie full-width (regresja P1-003)

```yaml
id: P1-017
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/HomeView
severity: high
```

**Symptom:** Pulpit operacyjny (`/rao/home`) jest wąski, nie zajmuje pełnej szerokości ekranu.

**Problem:** P1-003 miało naprawić HomeView na full-width (usunięcie `#app { width: 1126px }`), ale może nie działać poprawnie lub zostało nadpisane.

**Wymaganie:**
- HomeView powinien być full-width (jak w P1-003 fix)
- Sprawdzić czy `#app { width: 1126px }` zostało usunięte z `style.css`
- Sprawdzić czy HomeView ma odpowiednie responsywne KPI/quick-nav grid

**Powiązane:** P1-003 (marked done, ale regresja)

---

### P1-016: Pulpit pracownika (WorkerView) — wąski, nie full-width (regresja P1-003)

```yaml
id: P1-016
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/WorkerView
severity: high
```

**Symptom:** Pulpit pracownika (`/rao/worker`) jest wąski (~1126px), nie zajmuje pełnej szerokości ekranu.

**Problem:** P1-003 miało naprawić Pulpit (HomeView) na full-width (usunięcie `#app { width: 1126px }`), ale WorkerView nie został uwzględniony w fixie.

**Wymaganie:**
- WorkerView powinien być full-width (jak HomeView po P1-003)
- Sprawdzić czy WorkerView ma `height: 100vh` na root div (jak inne widoki przed P1-002 fix)
- Jeśli tak → zmienić na `height: 100%` (jak w P1-002 fix)

**Powiązane:** P1-003 (marked done, ale WorkerView nie był w scope)

---

### P1-015: Analytics — filtry nie działają dla wszystkich dashboardów

```yaml
id: P1-015
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/AnalyticsView (AnalyticsFilters) + backend/stats
severity: high
```

**Symptom:** Filtry w Analytics (date_from, date_to, branch_id, contractor_id) mogą nie działać dla wszystkich dashboardów/tabów.

**Wymaganie:**
- Sprawdzić czy filtry są stosowane do wszystkich endpointów stats
- Jeśli nie → fix w backend (endpointy nie respektują filtry) lub frontend (nie wysyła parametry)
- Dashboardy do sprawdzenia: PeriodRentalTab, LocationsTab, CategoriesTab, ContractorsTab, MachinesTab

---

### P1-009: Lokalizacje wynajmu — "brak PNA" w tabeli głównej bez sensu

```yaml
id: P1-009
status: done
priority: P1
created: 2026-07-05
resolved: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: frontend/AnalyticsView (Locations tab) + backend/stats
severity: high
```

**Symptom:** W tabeli Lokalizacje wynajmu pojawia się "brak PNA — Kraków"
i "brak PNA — Warszawa". Miasto ma wiele kodów PNA — pokazanie "brak PNA"
jest bez sensu w tabeli głównej.

**Przykład:**
```
Kraków    (brak PNA — Kraków)    1    8 400,00 zł
Warszawa  (brak PNA — Warszawa)  1    11 340,00 zł
```

**Wymaganie:**
- W tabeli głównej Lokalizacje: NIE pokazywać kodu PNA (miasto ma wiele)
- "brak PNA" ma być do wywalenia z tabeli głównej
- Może być po wklikaniu (detail view) — tam PNA ma sens
- W tabeli głównej: tylko miasto + liczba umów + wartość

**Fix (propozycja):**
- Sprawdzić `stats/router.py` endpoint lokalizacji — czy zwraca postal_code
- Sprawdzić `AnalyticsView.vue` Locations tab — usunąć kolumnę PNA z tabeli
- Lub zmienić format: z "Kraków (brak PNA — Kraków)" → po prostu "Kraków"
- Detail view (po kliknięciu) może pokazywać PNA per umowa

---

### P1-010: Warunki finansowe — "Wartość z rozliczenia" bez sensu, usunąć z DB i UI

```yaml
id: P1-010
status: triaged
priority: P1
created: 2026-07-05
reporter: operator (manual test 2026-07-05)
component: backend/contracts (DB schema, models, schemas) + frontend/ContractFormView
severity: high
```

**Symptom:** W sekcji "Warunki finansowe" w formularzu umowy jest pole "Wartość z rozliczenia (zł)" które jest redundantne. Faktura jest źródłem prawdy.

**Problem:**
- "Wartość z rozliczenia" to de facto suma faktur, ale jest duplikatem w DB i UI
- Pole "Faktura" powinna pokazywać sumę faktur z Fakturownia (read-only)
- Pole "Pozostało" powinno być obliczane: faktura - przedpłata (read-only)
- Pole "Przedpłata" — zostawić bo jest na umowie (editable)

**Wymagane zmiany (full-stack):**
1. **DB schema:** usunąć kolumnę `wartosc_z_rozliczenia` z tabeli `contracts`
2. **Backend models:** usunąć pole z `Contract` model w SQLAlchemy
3. **Backend schemas:** usunąć pole z Pydantic schemas (Create/Update/Response)
4. **Backend service/logic:** usunąć użycia pola w service functions
5. **Frontend UI:** usunąć pole z ContractFormView (Warunki finansowe)
6. **Frontend UI:** pole "Faktura" → read-only, suma faktur z Fakturownia
7. **Frontend UI:** pole "Pozostało" → read-only, obliczane jako faktura - przedpłata
8. **Frontend UI:** pole "Przedpłata" → zostawić (editable)

**Uwaga:** W sekcji "Rozliczenie umowy" jest modal "Faktury z Fakturownia (read-only)" — to zostaje bez zmian.

**Migracja DB:** DROP COLUMN (po backupie) lub soft-delete (set NULL + deprecate w spec).

**⚠️ WYMAGANA ZGODA UŻYTKOWNIKA:** DROP COLUMN na produkcyjnych danych wymaga backupu `mariadb-dump rao_new > backup_before_p1_010.sql` przed migracją.

---

## 🟡 P2 — Should-Have
*(brak)*

---

## 🟢 P3 — Nice-to-Have
*(brak)*

---

## 📋 Decyzje operatora

*(nowe decyzje dodawane tutaj + w `DECISION_LOG.md`)*

---

## 📊 Summary

**Razem:** 15 zadań (P0: 6, P1: 8, done: 1)

### Pipeline weryfikacji (status flow)

```
triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)
           │              │               │               │               │
           Devin koduje   Devin testuje   Software-house  Ty wzrokowo    Klient zatwierdza
           zmianę         programatycz.   subagenty       w UI/PDF        → zadanie zamknięte
                          (Playwright,    (QA, Security,
                           PyMuPDF,       UX, PO, Tech
                           pytest,        Lead review)
                           vue-tsc)
```
