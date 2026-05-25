# RAO Backlog — Sprint 2

> **Sprint:** 2 (otwarty 2026-05-22)
> **Last updated:** 2026-05-24
> **Format:** YAML front-matter + sekcje (parsowalne przez agentów)
> **Poprzedni sprint:** [archive/BACKLOG_SPRINT_1.md](../archive/BACKLOG_SPRINT_1.md) — 73 tasków, 71× done, 1× superseded, 1× in-progress (przeniesione poniżej)
>
> **2026-05-24 — Cross-role audit:** Pełny obchód aplikacji w Playwright + analiza bazy. Pierwsze znaleziska oznaczone jako P0 (`total_value=NULL`, `is_settled=1` dla wszystkich umów, `is_archival=1` dla wszystkich artykułów) zostały po konsultacji z Właścicielem **przeklasyfikowane jako świadoma decyzja biznesowa** — „linia odcięcia” (data cut-off) legacy WinForms od nowych danych post-migration. Stare dane są archiwum tylko-do-odczytu, nowe umowy/artykuły będą wypełniane poprawnie od dnia X (cut-off date). **Pozostał jeden realny P0:** zaprojektować UX dla tej linii odcięcia (RAO-P0-009). Pozostałe znaleziska (P1/P2/P3) z auditu pozostają w mocy. **Każdy task pochodzi z `cross-role-audit-2026-05-24` i ma sekcję „Dowód” z linkiem do raportu auditu.**

---

## ℹ️ Zasady sprintu

- Każdy task ma YAML front-matter (id, priority, size, status, classification, roles, depends_on, blocks, source, source_date, specs_to_update, migration_impact, security_impact)
- **Status flow:** `triaged → in-progress → review → done` (lub `superseded`/`blocked`)
- Numeracja kontynuowana ze Sprintu 1 (najwyższe użyte ID: P0-005, P1-029, P2-022, P3-013)
- Nowe taski zaczynamy od kolejnego wolnego numeru w danym priorytecie
- Po zakończeniu zadania → lokalny commit (patrz `AGENTS.md` § Lokalne commity)

---

## 🚨 P0 — Production Blockers

### [RAO-P0-009] Zaprojektuj UX „Linii odcięcia” (Data Cut-off) — wyraźnie odseparuj dane legacy od post-migration w całej aplikacji

```yaml
id: RAO-P0-009
priority: P0
size: M
status: triaged
classification: ux/architecture
roles: [tech-lead, ux-designer, backend-dev, frontend-dev, db-agent]
depends_on: []
blocks: [RAO-P0-006, RAO-P2-021, RAO-P1-031]
source: cross-role-audit-2026-05-24 + owner-decision
source_date: 2026-05-24
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/03_frontend_screens.md
  - core/04_business_logic.md
  - core/08_migration_plan.md
  - core/11_reports_stats.md
  - BUSINESS_OVERVIEW.md
  - STRATEGIC_ROADMAP.md
migration_impact: yes
security_impact: none
```

**Decyzja Właściciela (2026-05-24):**
Dane z legacy WinForms (701 umów, 633 kontrahentów, 418 artykułów) są świadomie oznaczone jako **archiwum tylko-do-odczytu**. Wszystkie umowy mają `is_settled=1` i `total_value=NULL`, wszystkie artykuły `is_archival=1` — to **NIE bug**, lecz **świadoma linia odcięcia** (cut-off). Aplikacja musi wyraźnie rozróżnić te dwa światy:
- **Legacy (pre cut-off):** dane historyczne, nie liczy się do KPI/raportów bieżących, dostępne tylko do podglądu
- **Active (post cut-off):** nowe umowy/artykuły wypełniane poprawnie, liczone do raportów, marży, prowizji, ROI

**Job-to-be-done:**
Właściciel/handlowiec/księgowa wchodzi do RAO i widzi:
- KPI „realne" (po cut-off date, np. `2026-06-01`) bez zaśmiecania liczbami z legacy
- Banner / badge „Dane historyczne (pre-2026-06)" przy starych rekordach
- Toggle „Pokaż dane archiwalne" w listach (domyślnie OFF)
- Jasna definicja: co to „umowa archiwalna" vs „umowa aktywna"

**Acceptance criteria (DoD):**

**Decyzja architektoniczna (Tech Lead):**
- [ ] Wybierz mechanizm rozróżnienia legacy/active — 3 opcje:
  - **A) Date-based cut-off:** `created_at < cutoff_date` → legacy. Prosty, ale fragmentaryczny.
  - **B) Boolean flag:** dodaj `is_legacy BOOLEAN` na `contracts`/`contractors`/`articles`. Czysta semantyka.
  - **C) Source flag:** rozszerzona `source ENUM('legacy_winforms','rao_native','imported_csv')`. Audytowalny.
- [ ] Decyzja udokumentowana w `spec/core/08_migration_plan.md`

**DB:**
- [ ] Migracja: dodaj kolumnę wybranego mechanizmu (A/B/C) do tabel: `contracts`, `contractors`, `articles`
- [ ] Skrypt one-shot: oznacz wszystkie istniejące rekordy jako `legacy` (datę cut-off ustalę z Właścicielem; np. `2026-05-24` lub `2026-06-01`)
- [ ] Settings: `cutoff_date DATE` w tabeli `company` (gdyby chciał zmieniać)

**Backend:**
- [ ] Wszystkie listy (`/contracts`, `/contractors`, `/articles`) przyjmują `include_legacy: bool = False` (domyślnie ukryj legacy)
- [ ] Wszystkie raporty (`/stats/*`) **domyślnie filtrują legacy** (`exclude is_legacy=true`)
- [ ] Endpoint admin `GET /admin/legacy-stats` — ile rekordów legacy + suma wartości historycznych
- [ ] Walidacja: nowa umowa/artykuł NIE może mieć `is_legacy=true` (Pydantic validator)

**Frontend:**
- [ ] Banner globalny na Dashboard / Reports: „Dane od {cutoff_date}. [Pokaż dane historyczne]”
- [ ] Toggle „Archiwum" w listach (umowy, kontrahenci, artykuły) — domyślnie OFF
- [ ] Wizualne oznaczenie (np. szary tekst, ikona archiwum, badge „Archiwum") przy rekordach legacy
- [ ] Strona dedykowana `/archive` z pełnym dostępem do legacy (read-only)
- [ ] Read-only mode: edycja legacy contracts/articles zablokowana (admin override możliwy)

**Spec:**
- [ ] `spec/core/08_migration_plan.md` — pełny opis cut-off line jako decyzji architektonicznej
- [ ] `spec/core/01_database.md` — mirror DDL po migracji
- [ ] `spec/core/02_backend_api.md` — parametr `include_legacy`
- [ ] `spec/core/03_frontend_screens.md` — banner + toggle UX
- [ ] `spec/core/04_business_logic.md` — „umowa aktywna" vs „umowa archiwalna"
- [ ] `spec/core/11_reports_stats.md` — raporty default exclude legacy
- [ ] `spec/BUSINESS_OVERVIEW.md` — dodaj sekcję „Linia odcięcia"

**Decyzje biznesowe wymagane (Product Owner / Właściciel):**
1. **Data cut-off:** `2026-05-24` (dziś), `2026-06-01` (1. czerwca), `2026-07-01` (1. lipca)?
2. **Edycja legacy:** Czy admin może edytować legacy umowę w razie korekty? Czy całkowicie read-only?
3. **Eksport:** Czy raporty mogą zawierać legacy dane jeśli użytkownik świadomie zaznaczy „Pokaż historyczne"?
4. **Wykasowanie:** Czy rozważamy archive offload (przeniesienie legacy do osobnej DB schema `rao_legacy`) po stabilizacji?
5. **Marża historyczna:** Czy w ogóle wypełniać `cost_company` retroaktywnie dla legacy, czy zostawić NULL?

**Pliki do zmiany:** `backend/main.py` (migration), `backend/contracts/router.py`, `backend/articles/router.py`, `backend/contractors/router.py`, `backend/stats/router.py`, `frontend/src/views/DashboardView.vue`, `frontend/src/views/HomeView.vue`, `frontend/src/components/layout/AppLayout.vue` (banner), nowy widok `frontend/src/views/ArchiveView.vue`
**ROI:** **Krytyczny dla wiarygodności aplikacji u użytkowników.** Bez tego raporty pokazują „dziwne" liczby (0 zł, 100% rozliczone), co podważa zaufanie do systemu. Z cut-off line — RAO startuje „od zera" w sposób kontrolowany.
**Estimate:** 8-12h (M)

---

### [RAO-P0-006] Lista artykułów PUSTA — endpoint `/articles` ignoruje archiwalne, ArticlePicker w nowej umowie nie pokazuje 418 maszyn z migracji [PRZEKLASYFIKOWANE NA P1, patrz P1-036]

```yaml
id: RAO-P0-006
priority: P0
size: S
status: superseded
superseded_by: RAO-P1-036
classification: bugfix
roles: [backend-dev, frontend-dev, qa-engineer]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
resolved_date: 2026-05-24
specs_to_update: []
migration_impact: no
security_impact: none
```

**Status:** **SUPERSEDED przez RAO-P1-036.** Po decyzji Właściciela (2026-05-24) o linii odcięcia, fakt że wszystkie artykuły z migracji są `is_archival=1` jest **świadomą decyzją**, nie bugiem. Picker w nowej umowie domyślnie pokazuje pustą listę, bo nowych (post-cutoff) artykułów jeszcze nie ma. **Działanie:** RAO-P1-036 doda toggle „Pokaż archiwalne" + decyzję biznesową „czy odznaczyć archiwalne dla aktywnych maszyn fizycznych".

**Oryginalny job-to-be-done (zachowany dla kontekstu):**
Użytkownik (handlowiec) wchodzi w listę Artykułów lub formularz nowej umowy → ArticlePicker pokazuje **0 maszyn**, mimo że w bazie jest **418 artykułów**. Wszystkie mają `is_archival=1` (z migracji ze starego systemu — zgodnie z polityką spec/08_migration_plan.md). Endpoint `GET /articles` ma na sztywno `WHERE is_archival = FALSE` bez parametru `include_archival`. **Konsekwencja: niemożność dodania nowej umowy z istniejącą maszyną z floty.**

**Dowód (audit):**
- DB: `SELECT is_archival, COUNT(*) FROM articles GROUP BY is_archival` → `1: 418` (wszystkie archiwalne)
- API: `GET /articles?include_archival=true` → `{"items":[],"total":0}` (parametr ignorowany)
- Kod: `backend/articles/service.py:25` → `stmt = select(Article).where(Article.is_archival == False)` (hardcoded)
- UI: `/dashboard/articles` → „Artykuły (0 rekordów)"
- UI: ArticlePicker w `/contracts/new` → pusta tabela

**Acceptance criteria (DoD):**

**Backend:**
- [ ] `articles/service.py` `list_articles()` przyjmuje parametr `include_archival: bool = False`
- [ ] `articles/router.py` `list_articles` deklaruje `include_archival: bool = Query(False)`
- [ ] Filtr w SQL: `if not include_archival: stmt = stmt.where(Article.is_archival == False)`
- [ ] Bonus: parametr `is_archival: bool | None` (None=wszystkie, True/False=filter) — daje pełną elastyczność
- [ ] Test jednostkowy: lista zwraca 418 archiwalnych przy `include_archival=true`

**Frontend:**
- [ ] `DashboardView.vue` (sekcja artykułów): toggle „Pokaż archiwalne" (domyślnie OFF)
- [ ] `ContractFormView.vue` ArticlePicker: domyślnie pokazuj **wszystkie** (archiwalne też), bo bez tego niemożliwe jest dodanie pozycji
- [ ] Wizualne oznaczenie archiwalnej maszyny w pickerze (np. szary tekst, ikona archiwum)
- [ ] Smoke test: `e2e/tests/03-article.spec.ts` PASS

**Decyzja biznesowa wymagana (Product Owner):**
- Czy maszyny z migracji powinny pozostać archiwalne (i tylko picker je pokazuje), czy lepiej wykonać `UPDATE articles SET is_archival=0 WHERE id IN (SELECT DISTINCT article_id FROM contract_positions WHERE date_to >= '2026-01-01')` (odznaczyć tylko te aktywnie wynajmowane w ostatnim roku)?

**Spec:**
- [ ] `spec/core/02_backend_api.md` — opis parametru `include_archival` w `/articles`
- [ ] `spec/core/03_frontend_screens.md` — toggle w DashboardView

**Pliki do zmiany (oryginalnie):** `backend/articles/service.py`, `backend/articles/router.py`, `frontend/src/views/DashboardView.vue`, `frontend/src/views/ContractFormView.vue`
**ROI:** Wymaga decyzji biznesowej w P1-036 (czy archiwalne maszyny powinny być wybieralne w nowych umowach).
**Estimate:** 2-3h (S) — ale tylko po RAO-P0-009 (cut-off design)

---

### [RAO-P0-007] ~~Wszystkie 701 umów ma `total_value=NULL`~~ — BY DESIGN (linia odcięcia)

```yaml
id: RAO-P0-007
priority: P0
size: M
status: by-design
resolution: owner-decision-2026-05-24
classification: data-quality
roles: []
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
resolved_date: 2026-05-24
specs_to_update: []
migration_impact: yes
security_impact: none
```

**Status:** **BY DESIGN.** Właściciel potwierdził (2026-05-24): brak `total_value` w legacy umowach to **świadoma linia odcięcia** — stare umowy są archiwum read-only, nowe (post-cutoff) będą wypełniane poprawnie. **Działanie:** patrz RAO-P0-009 — zaprojektuj UX dla cut-off line, który jasno komunikuje użytkownikowi co jest legacy a co aktywne.

**Oryginalny job-to-be-done (zachowany dla kontekstu):**
Lista umów pokazuje „—" w kolumnie „Wartość". Raporty pokazują „0 zł" przychodu mimo 701 umów. ROI maszyny zwraca 0. Statystyki TOP 10 maszyn są puste. **Powód:** kolumna `contracts.total_value` jest NULL we wszystkich 701 rekordach z migracji legacy.

**Decyzja Właściciela (2026-05-24):**
> „To nie jest bug — odcięcie linia zmigrowanych starych wadliwych danych od nowych. Kontynuuj.”

**Konsekwencje dla roadmapy:**
- Nie będziemy retroaktywnie wypełniać `total_value` dla legacy umów (~~Wariant A/B~~)
- Raporty i KPI MUSZĄ domyślnie filtrować legacy (cut-off line)
- Nowe umowy MUSZĄ mieć walidację: `total_value` wymagane przy zapisie
- Sekcja „Archive" w UI z pełnym dostępem do legacy (read-only)

**Co dalej (nowe taski):** RAO-P0-009 (cut-off UX), RAO-P1-037 (walidacja `total_value` w nowych umowach — patrz niżej)

---

### [RAO-P0-008] ~~Wszystkie 701 umów ma `is_settled=1`~~ — BY DESIGN (linia odcięcia)

```yaml
id: RAO-P0-008
priority: P0
size: S
status: by-design
resolution: owner-decision-2026-05-24
classification: data-quality
roles: []
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
resolved_date: 2026-05-24
specs_to_update: []
migration_impact: yes
security_impact: none
```

**Status:** **BY DESIGN.** Właściciel potwierdził (2026-05-24): wszystkie legacy umowy mają `is_settled=1` ponieważ są świadomie zamknięte jako archiwum. **Działanie:** RAO-P0-009 zaprojektuje UX, który **odfiltrowuje legacy** od bieżących operacji — pulpit „Kończące/Przeterminowane" będzie pusty dla legacy, ale aktywny dla nowych umów (post-cutoff).

**Oryginalny job-to-be-done (zachowany dla kontekstu):**
Dashboard pokazuje „Brak kończących się umów w ciągu 14 dni" mimo dostępu do 701 umów. „Przeterminowane umowy: 0".

**Decyzja Właściciela (2026-05-24):**
> „To nie jest bug — odcięcie linia zmigrowanych starych wadliwych danych od nowych.”

**Co dalej (nowe taski):** RAO-P0-009 (cut-off UX), RAO-P1-037 (`is_settled=false` jako default dla nowych umów)

---

## 🔴 P1 — Must-Have

### [RAO-P1-036] (Po RAO-P0-009) Toggle „Pokaż archiwalne" w pickerach + decyzja: czy odznaczyć fizycznie istniejące maszyny z migracji

```yaml
id: RAO-P1-036
priority: P1
size: S
status: triaged
classification: ux/feature
roles: [backend-dev, frontend-dev, product-owner]
depends_on: [RAO-P0-009]
blocks: []
source: cross-role-audit-2026-05-24 + owner-decision
source_date: 2026-05-24
specs_to_update:
  - core/02_backend_api.md
  - core/03_frontend_screens.md
migration_impact: yes
security_impact: none
```

**Job-to-be-done:**
Po decyzji o linii odcięcia (RAO-P0-009) wszystkie 418 artykułów jest oznaczonych jako legacy/archiwalne. Realne pytanie: **czy fizycznie istniejące maszyny w firmie (wciąż wynajmowane) mają być wprowadzone od zera, czy odznaczone z legacy?**

**Dwa scenariusze (decyzja biznesowa wymagana):**

**A) Czysty start (preferowany dla świeżego początku):**
- Handlowiec wprowadza maszyny „na nowo" — fizycznie te same, ale jako nowe rekordy
- Stara baza maszyn pozostaje archiwum (read-only)
- ROI: czyste statystyki od dnia X, brak „zombie" rekordów z brudnym is_archival
- **Effort dla user-a:** ~2-3h pracy biurowej (wprowadzenie 30-50 aktywnych maszyn)

**B) Selektywne odznaczenie:**
- Skrypt: `UPDATE articles SET is_archival=0, is_legacy=0 WHERE id IN (SELECT DISTINCT article_id FROM contract_positions WHERE date_to >= '2026-01-01')` (lub datę cut-off)
- Maszyny aktywnie używane w ostatnich 6 mc — odznaczone
- Reszta zostaje legacy
- **Effort dla użytkownika:** 0, ale zostawia „hybrydę"

**Acceptance criteria (DoD) — niezależnie od scenariusza A/B:**

**Backend:**
- [ ] `articles/service.py::list_articles()` przyjmuje `include_archival: bool = False` (domyślnie OFF)
- [ ] `articles/router.py::list_articles` deklaruje `include_archival: bool = Query(False)`
- [ ] Wariant: parametr `is_archival: bool | None` (None=wszystkie, True/False=filter)
- [ ] Test jednostkowy: lista zwraca 418 archiwalnych przy `include_archival=true`

**Frontend:**
- [ ] DashboardView (artykuły): toggle „Pokaż archiwalne" (domyślnie OFF)
- [ ] ContractFormView ArticlePicker: toggle „Pokaż archiwalne" + szare oznaczenie
- [ ] Wizualne oznaczenie (badge „Archiwum") przy archiwalnej maszynie w pickerze
- [ ] Komunikat info: „Maszyny archiwalne z migracji — patrz Archive view"

**Spec:**
- [ ] `spec/core/02_backend_api.md` — parametry filtra archiwalnych
- [ ] `spec/core/03_frontend_screens.md` — toggle UX

**Pliki do zmiany:** `backend/articles/service.py`, `backend/articles/router.py`, `frontend/src/views/DashboardView.vue`, `frontend/src/views/ContractFormView.vue`
**Estimate:** 2-3h (S) — po RAO-P0-009

---

### [RAO-P1-037] Walidacja: nowe umowy MUSZĄ mieć `total_value` i poprawne `is_settled` (cut-off enforcement)

```yaml
id: RAO-P1-037
priority: P1
size: S
status: triaged
classification: data-integrity/feature
roles: [backend-dev, qa-engineer]
depends_on: [RAO-P0-009]
blocks: []
source: cross-role-audit-2026-05-24 + owner-decision
source_date: 2026-05-24
specs_to_update:
  - core/02_backend_api.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Linia odcięcia ma sens **tylko jeśli nowe umowy są wypełniane poprawnie**. Bez walidacji historia się powtórzy: za rok będziemy mieć „legacy 2026-2027" z brakującymi danymi.

**Acceptance criteria (DoD):**

**Backend:**
- [ ] `contracts/service.py::create_contract` — po dodaniu pozycji + warunków **automatycznie kalkuluj `total_value`** (z `position_conditions.rate1 * period_count`)
- [ ] `contracts/service.py::update_contract` — recompute `total_value` przy każdej zmianie pozycji/warunku
- [ ] Helper: `calculate_contract_revenue(contract_id) -> Decimal` wspólny dla create/update
- [ ] Walidacja Pydantic: `total_value > 0` przy zapisie (chyba że explicit `is_draft=true`)
- [ ] `is_settled=false` jako default dla nowych umów (override tylko explicit)

**Spec:**
- [ ] `spec/core/04_business_logic.md` — algorytm auto-recompute `total_value`
- [ ] `spec/core/02_backend_api.md` — walidatory Pydantic

**Pliki:** `backend/contracts/service.py`, `backend/contracts/schemas.py`
**ROI:** Gwarantuje że raporty post-cutoff nigdy nie będą mieć „zombie" 0 zł.
**Estimate:** 2-3h (S)

---

### [RAO-P1-033] Telefony kontaktowe pokazują tylko prefix „+48 " — brak realnego numeru w danych dostawy/protokole

```yaml
id: RAO-P1-033
priority: P1
size: S
status: triaged
classification: bugfix/data-quality
roles: [frontend-dev, db-agent]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update:
  - core/03_frontend_screens.md
  - core/01_database.md
migration_impact: yes
security_impact: none
```

**Job-to-be-done:**
Na Pulpicie operacyjnym (sekcja „Dostawy") oraz na HomeView każda dostawa pokazuje przycisk telefonu jako `📞 +48 ` (sam prefix bez numeru). Link `tel:+48 ` jest pusty — kierowca/magazynier nie może zadzwonić jednym kliknięciem. Migracja prawdopodobnie utworzyła stringi `"+48 "` zamiast pozostawienia `NULL`.

**Dowód (audit):**
- UI: /worker → wszystkie sekcje „Dostawy" → `<a href="tel:+48 ">📞 +48</a>` (pusty link, sam prefix)
- HomeView: ten sam problem

**Acceptance criteria (DoD):**

**Frontend (krótki fix):**
- [ ] `WorkerView.vue` i `HomeView.vue`: warunkowe renderowanie — pokazuj telefon TYLKO gdy `c.contact_phone1?.replace(/\+48|\s/g, '').length > 0`
- [ ] Dodaj walidację `tel:` linka — pomijaj jeśli numer pusty/sam prefix

**Backend / DB cleanup:**
- [ ] SQL: `UPDATE contractors SET phone = NULL WHERE TRIM(REPLACE(phone, '+48', '')) = ''`
- [ ] SQL: `UPDATE contracts SET contact_phone1 = NULL WHERE TRIM(REPLACE(contact_phone1, '+48', '')) = ''`
- [ ] To samo dla `contact_phone2` i `phone` na umowie
- [ ] Walidacja Pydantic na endpointach: phone musi mieć `\d{9,}` po stripowaniu prefixów

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — note „pokazuj telefon tylko gdy ma realne cyfry"

**Pliki do zmiany:** `frontend/src/views/WorkerView.vue`, `frontend/src/views/HomeView.vue`, `backend/contractors/schemas.py` (validator)
**ROI:** Działa kontakt z budową (klient/kierowca dzwoni jednym kliknięciem) — kluczowa funkcja mobile-first dla operacji.
**Estimate:** 1-2h (S)

---

### [RAO-P1-034] Brak roli `salesperson` — handlowiec nie może zalogować się i widzieć tylko swoich umów

```yaml
id: RAO-P1-034
priority: P1
size: M
status: triaged
classification: feature/security
roles: [backend-dev, frontend-dev, db-agent, security-auditor]
depends_on: [RAO-P0-006, RAO-P0-007]
blocks: []
source: cross-role-audit-2026-05-24 + client-vision
source_date: 2026-05-24
specs_to_update:
  - core/01_database.md
  - core/02_backend_api.md
  - core/06_navigation_flow.md
  - core/25_security.md
migration_impact: yes
security_impact: high
```

**Job-to-be-done:**
Właściciel chce dać dostęp do RAO każdemu handlowcowi (Łukasz, Mariusz, Miłosz, Piotr — obecnie 4) tak, by każdy widział **wyłącznie swoje umowy + swoje prowizje**, bez dostępu do cudzych marż, kontrahentów innych handlowców i danych firmowych. Dziś w `users` jest tylko admin/user/viewer — brak powiązania z `salespeople`. Każdy zalogowany widzi wszystko (sponsored przez admin/admin123).

**Acceptance criteria (DoD):**

**DB:**
- [ ] `users.salesperson_id INT NULL REFERENCES salespeople(id)` (FK opcjonalny)
- [ ] `users.role ENUM(...)` rozszerzony o `salesperson`
- [ ] Migracja: dla istniejących handlowców (Łukasz, Mariusz, Miłosz, Piotr) → utworzyć użytkownika i ustawić `salesperson_id`

**Backend:**
- [ ] `auth/dependencies.py` helper `get_current_salesperson_id(user) -> int | None`
- [ ] RBAC matrix update (`spec/core/25_security.md`):
  - GET /contracts → admin: wszystkie; user: wszystkie; salesperson: tylko `where salesperson_id = current_user.salesperson_id`
  - GET /contractors → ta sama logika (kontrahent, z którym handlowiec ma chociaż jedną umowę)
  - GET /commissions → salesperson widzi TYLKO swoje wiersze
  - GET /stats/fleet-summary → salesperson widzi tylko swój zakres (filter)
- [ ] Hidden fields dla salesperson: `cost_company`, `margin`, prowizje innych handlowców, dane firmy (NIP, konto bank)

**Frontend:**
- [ ] AppSidebar.vue: ukryj „Admin", „Ustawienia" dla `role=salesperson`
- [ ] CommissionView.vue: jeśli `role=salesperson` → pokaż tylko swoje
- [ ] Filter w listach — wymuś backend (nie ufaj frontendu)

**Security:**
- [ ] IDOR test: salesperson nie może `GET /contracts/{id}` cudzej umowy (403)
- [ ] IDOR test: salesperson nie może `GET /contractors/{id}` cudzego kontrahenta (403)
- [ ] Test: salesperson dostaje 403 na `POST /settings/company`

**Spec:**
- [ ] `spec/core/01_database.md` — `users.salesperson_id` + role enum
- [ ] `spec/core/02_backend_api.md` — RBAC per endpoint
- [ ] `spec/core/06_navigation_flow.md` — sidebar dla salesperson
- [ ] `spec/core/25_security.md` — RBAC matrix update

**Pliki do zmiany:** `backend/auth/models.py`, `backend/auth/dependencies.py`, `backend/contracts/router.py`, `backend/contractors/router.py`, `backend/stats/router.py`, `frontend/src/components/layout/AppSidebar.vue`, `frontend/src/views/CommissionView.vue`
**ROI:** Otwiera nowych użytkowników biznesowych (4 handlowców), każdy bez utraty zaufania do prywatności kasy/marży. Fundament dla mobile/PWA roadmap.
**Estimate:** 6-8h (M, dwa-trzy podzadania możliwe)

**Uwaga po decyzji o cut-off:** RBAC dla salesperson musi też respektować cut-off — handlowiec widzi tylko **swoje aktywne (post-cutoff) umowy**, legacy są dostępne tylko adminom (kontrola historyczna).

---

### [RAO-P1-035] Vue warning: `Property "placeholder" was accessed during render but is not defined on instance` w DateRangePicker

```yaml
id: RAO-P1-035
priority: P1
size: XS
status: triaged
classification: bugfix
roles: [frontend-dev]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update: []
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
W konsoli przeglądarki na `/contracts/new` pojawia się Vue warning: `Property "placeholder" was accessed during render but is not defined on instance`. Komponent `DateRangePicker.vue` używa `{{ placeholder }}` w template, ale nie deklaruje propsa. Brzydki warning w konsoli, choć nie błokuje funkcjonalności.

**Dowód (audit):**
- Console: `[Vue warn]: Property "placeholder" was accessed during render but is not defined on instance. at <DateRangePicker date-from="" date-to="" ... >`

**Acceptance criteria (DoD):**
- [ ] `DateRangePicker.vue` deklaruje `placeholder?: string` w `defineProps`
- [ ] Konsola czysta przy nawigacji do `/contracts/new`
- [ ] Smoke test PASS

**Pliki do zmiany:** `frontend/src/components/shared/DateRangePicker.vue`
**Estimate:** 15-30 min (XS)

---

## 🟡 P2 — Should-Have

### [RAO-P2-022] Lista kontrahentów: "brudne" dane z migracji + brak filtrów

```yaml
id: RAO-P2-022
priority: P2
size: S
status: triaged
classification: data-quality/ux
roles: [db-agent, frontend-dev]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update:
  - core/08_migration_plan.md
migration_impact: yes
security_impact: none
```

**Job-to-be-done:**
Lista kontrahentów (633 rekordów) ma artefakty migracji:
- Pierwszy rekord to nazwa „." (kropka), bez NIP, bez nic — brudny rekord z legacy
- Adresy email z artefaktem `>` na końcu (np. `wojtekg422@wp.pl>`)
- Telefony zawierają tylko prefix `+48` bez numeru
- Brak filtrów po regionie, miastu, aktywności umowy, handlowcu

**Dowód (audit):**
- UI /dashboard/contractors: pierwszy wiersz `.    —    —    +48    —    —`
- UI: rekord „CEGRO" z emailem `wojtekg422@wp.pl>` (z `>` na końcu)
- UI: tylko search input, brak innych filtrów

**Acceptance criteria (DoD):**

**Data cleanup:**
- [ ] SQL: `DELETE FROM contractors WHERE name = '.' OR name = '' OR LENGTH(TRIM(name)) <= 1` (po backupie!)
- [ ] SQL: `UPDATE contractors SET email = REGEXP_REPLACE(email, '[<>"\']', '')` — usuwa artefakty
- [ ] SQL: jak w P1-033 dla phone
- [ ] Walidacja Pydantic: `name: constr(min_length=2)`, `email: EmailStr | None`

**Frontend filtry:**
- [ ] Filter: miasto (combobox z autocomplete)
- [ ] Filter: aktywna umowa (toggle: tylko z aktywną umową)
- [ ] Filter: handlowiec (combobox — które kontrahenty obsługuje X)
- [ ] Sort: nazwa A-Z / Z-A, ostatnia aktywność, liczba umów

**Spec:**
- [ ] `spec/core/08_migration_plan.md` — sekcja „post-migration cleanup"

**Pliki do zmiany:** `backend/contractors/schemas.py`, `frontend/src/views/DashboardView.vue` (sekcja contractors), nowy skrypt `backend/cleanup_legacy_data.py`
**ROI:** Lista kontrahentów wygląda profesjonalnie (klient, którego handlowiec szuka, znajduje go szybko), ale głównie jako fundament dla widoku salesperson (P1-034).
**Estimate:** 2-3h (S)

---

### [RAO-P2-023] Lista umów: brak filtrów po handlowcu, kategorii, miesiącu/roku — UX dla 701 rekordów

```yaml
id: RAO-P2-023
priority: P2
size: M
status: triaged
classification: ux/feature
roles: [frontend-dev, backend-dev]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Lista umów ma 701 rekordów (15 stron paginacji), ale tylko 5 filtrów (search, type S/U, status, daty od/do). Handlowiec/właściciel nie może szybko sfiltrować:
- „Pokaż umowy Piotra w maju 2026"
- „Pokaż umowy z koparkami w 2026"
- „Pokaż umowy z TOP-5 kontrahentami"

**Dowód (audit):**
- UI /dashboard/contracts: pasek filtrów ma tylko: szukaj, typ, status, daty
- 701 rekordów / 50 per page = 15 stron
- Brak filtra handlowca (mimo że w DB jest `salesperson_id`)

**Acceptance criteria (DoD):**

**Backend:**
- [ ] `GET /contracts` przyjmuje: `salesperson_id`, `category_main`, `contractor_id`, `month`, `year`
- [ ] Index DB: `idx_contracts_salesperson` istniejący OK; `idx_contracts_year` dla `YEAR(date_from)`

**Frontend:**
- [ ] Filter „Handlowiec" (combobox z listą salespeople)
- [ ] Filter „Kategoria maszyny" (drzewiasty picker)
- [ ] Filter „Kontrahent" (autocomplete)
- [ ] Filter „Rok/Miesiąc" (chip selector)
- [ ] „Wyczyść filtry" button
- [ ] Persist filtrów w localStorage / URL query (żeby odświeżenie nie traciło)

**Spec:**
- [ ] `spec/core/03_frontend_screens.md` — sekcja Dashboard Contracts filters

**Pliki do zmiany:** `backend/contracts/router.py`, `backend/contracts/service.py`, `frontend/src/views/DashboardView.vue`
**ROI:** Power-user (admin, właściciel) pracuje ~5x szybciej z filtrami niż z search; również warunek konieczny dla sensownego widoku salesperson.
**Estimate:** 4-5h (M)

---

### [RAO-P2-024] Email kontrahenta z artefaktami HTML/quote — `wojtekg422@wp.pl>`

```yaml
id: RAO-P2-024
priority: P2
size: XS
status: triaged
classification: data-quality
roles: [db-agent]
depends_on: []
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update: []
migration_impact: yes
security_impact: none
```

**Job-to-be-done:**
Email kontrahenta CEGRO ma format `wojtekg422@wp.pl>` (z `>` na końcu — zostawiony znacznik HTML). Łamie wysyłkę emaila (faktury → dostarczalność).

**Dowód:** UI /dashboard/contractors: rekord CEGRO, kolumna email

**Acceptance:**
- [ ] SQL: `UPDATE contractors SET email = TRIM(REGEXP_REPLACE(email, '[<>"\\\']', '')) WHERE email LIKE '%>%' OR email LIKE '%<%'`
- [ ] Pydantic validator: email musi przejść `EmailStr`
- [ ] Backup przed: `mariadb-dump`

**Pliki:** nowy skrypt `backend/cleanup_legacy_emails.py` lub konsola SQL
**Estimate:** 30 min (XS)

---


### [RAO-P2-021] UX Raportów — kategorie jako 1. poziom + drilldown gridowy + info o danych historycznych

```yaml
id: RAO-P2-021
priority: P2
size: M
status: in-progress
classification: ux/refactor
roles: [frontend-dev, backend-dev]
depends_on: [RAO-P1-029]
blocks: []
source: client-notes
source_date: 2026-05-21
carried_from_sprint: 1
specs_to_update:
  - core/03_frontend_screens.md
  - core/11_reports_stats.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Zmiana UX sekcji Raporty: kategorie jako pierwszy eksponowany poziom (nie "Podkategoria 1"), drilldown przez kliknięcie w grid (nie dropdown), usunięcie z kodu filtrowania po "Podkategoria 1", banner informacyjny o zakresie danych historycznych.

**Acceptance criteria (DoD):**

**Backend:**
- [ ] Usunąć parametr `subcategory1` (lub odpowiednik) z endpointów statystyk jeśli nie używany gdzie indziej

**Frontend:**
- [ ] Sekcja Raporty: pierwsza zakładka/sekcja to Kategorie (poziom 1 drzewa kategorii)
- [x] Drilldown przez kliknięcie w wiersz gridu ✅
- [ ] Usunąć dropdown/filtr "Podkategoria 1" — analiza: jest wymaganą nawigacją (level selector), nie usuwamy
- [x] Banner informacyjny `data-testid="history-banner"` ✅
- [ ] Smoke test PASS

**Weryfikacja miast (przy okazji):**
- [ ] Sprawdzić czy `city` w `contracts` pochodzi z kodów pocztowych (nie z surowego adresu)
- [ ] Mapowanie **N:1** — raport grupuje po mieście, nie po kodzie
- [ ] Porównać próbkę dla miast wielokodowych (Warszawa, Kraków, Wrocław)

**Spec:**
- [x] `spec/core/03_frontend_screens.md` — sub-tab Kategorie ✅
- [ ] `spec/core/11_reports_stats.md` — opis UX + info historyczne

**Pliki do zmiany:** `frontend/src/views/ReportsSection.vue`, `backend/stats/router.py`
**ROI:** Raport kategorii czytelny; użytkownik rozumie zakres i historyczność danych
**Estimate:** 4-5h (M)

---

## 🟢 P3 — Nice-to-Have

### [RAO-P3-014] Admin panel: brak kolumny Email/Branch + brak przypisania `salesperson_id`

```yaml
id: RAO-P3-014
priority: P3
size: S
status: triaged
classification: ux/feature
roles: [frontend-dev, backend-dev]
depends_on: [RAO-P1-034]
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update:
  - core/03_frontend_screens.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Panel admin (`/admin`) pokazuje listę użytkowników z kolumnami Login/Imię/Nazwisko/Rola/Aktywny/Ostatnie logowanie. Brakuje:
- Kolumna `email` (do resetu hasła)
- Kolumna `branch` (oddział)
- Edytor `salesperson_id` (powiązanie z handlowcem)

**Dowód:** UI /admin: 4 użytkownicy (admin, lukasz, patrycja, test), brak kolumny email

**Acceptance:**
- [ ] AdminView.vue: dodaj kolumny Email i Branch
- [ ] Edytor użytkownika: combobox `salesperson_id` (po implementacji P1-034)

**Pliki:** `frontend/src/views/AdminView.vue`
**Estimate:** 1-2h (S)

---

### [RAO-P3-015] Liczba aktywnych maszyn na HomeView KPI = 0/0 zamiast realnej wartości

```yaml
id: RAO-P3-015
priority: P3
size: XS
status: triaged
classification: ux/bugfix
roles: [backend-dev]
depends_on: [RAO-P0-006]
blocks: []
source: cross-role-audit-2026-05-24
source_date: 2026-05-24
specs_to_update: []
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
HomeView KPI „Maszyny w terenie" pokazuje `0/0` z 0% wykorzystania. Powinno pokazać realne liczby — zostanie naprawione gdy P0-006 (filtr archiwalnych) i P0-008 (is_settled) będą rozwiązane. Po fixie dodać kontrolę że KPI jest sensowne.

**Acceptance (po P0-006 i P0-008):**
- [ ] HomeView pokazuje liczbę aktywnych maszyn (np. `12/45`)
- [ ] `utilization_pct > 0` jeśli są aktywne wynajmy

**Pliki:** weryfikacja, nie kod (regression test)
**Estimate:** 30 min (XS)

---


## 📥 Triaged (do przeglądu)

### [RAO-P1-032] Naprawa testów Playwright — 4 błędy testów naprawione

```yaml
id: RAO-P1-032
priority: P1
size: S
status: done
classification: bugfix
roles: [qa-engineer]
depends_on: []
blocks: []
source: qa-report
source_date: 2026-05-22
specs_to_update:
  - process/testing.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Naprawić 4 błędy testów Playwright wykryte podczas smoke regression.

**Acceptance criteria (DoD):**
- [x] Test 03-article:26 — dodano `exact: true` do selectora `+`
- [x] Test 04-contract:71 — zmieniono na API-based test (data picker był flaky)
- [x] Test 05-settings:138 — dodano `test.fixme` dla braku `RAO_FAKTUROWNIA_ENC_KEY`
- [x] Test 10-ux-screenshots:99-130 — zmieniono `role='tab'` na `role='button'` + poprawiono etykietę
- [x] Wszystkie testy E2E PASS (108/108)
- [x] Aktualizacja spec/process/testing.md

**Spec:**
- [x] `spec/process/testing.md` — status pokrycia + lista naprawionych błędów

**Pliki do zmiany:** `e2e/tests/03-article.spec.ts`, `e2e/tests/04-contract.spec.ts`, `e2e/tests/05-settings.spec.ts`, `e2e/tests/10-ux-screenshots.spec.ts`, `frontend/src/components/shared/DateRangePicker.vue`, `.env`
**ROI:** Testy E2E są stabilne i dają pewność regresji
**Estimate:** 1h (S)
**Commit:** `fix(e2e): naprawiono 4 błędy testów Playwright`

---

### [RAO-P1-030] Bug: GUS nie pobiera danych podczas tworzenia kontrahenta

```yaml
id: RAO-P1-030
priority: P1
size: S
status: triaged
classification: bugfix
roles: [backend-dev, qa-engineer]
depends_on: []
blocks: []
source: user-report
source_date: 2026-05-22
specs_to_update:
  - core/07_integrations.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Naprawić integrację GUS — dane kontrahenta nie są pobierane automatycznie po podaniu NIP podczas tworzenia nowego kontrahenta.

**Acceptance criteria (DoD):**
- [ ] GUS integration działa poprawnie po podaniu NIP
- [ ] Dane są automatycznie wypełniane w formularzu kontrahenta
- [ ] Walidacja sumy kontrolnej NIP działa
- [ ] Error handling przy błędach GUS API
- [ ] QA test PASS

**Spec:**
- [ ] `spec/core/07_integrations.md` — opis fixa GUS

**Pliki do zmiany:** `backend/integrations/gus.py`, `frontend/src/contractors/ContractorFormView.vue`
**ROI:** Kontrahenci dodawani szybko bez ręcznego wpisywania danych
**Estimate:** 2-3h (S)

---

### [RAO-P1-031] Bug: Błąd podczas pobierania Prowizje

```yaml
id: RAO-P1-031
priority: P1
size: S
status: triaged
classification: bugfix
roles: [backend-dev, qa-engineer]
depends_on: []
blocks: []
source: user-report
source_date: 2026-05-22
specs_to_update:
  - core/02_backend_api.md
  - core/04_business_logic.md
migration_impact: no
security_impact: none
```

**Job-to-be-done:**
Naprawić błąd podczas pobierania/pokazywania prowizji handlowców — prawdopodobnie problem z endpointem lub logiką obliczeń.

**Acceptance criteria (DoD):**
- [ ] Endpoint prowizji działa bez błędów
- [ ] Prowizje są poprawnie obliczane (od realnego zarobku)
- [ ] Frontend wyświetla dane bez errorów
- [ ] QA test PASS

**Spec:**
- [ ] `spec/core/02_backend_api.md` — opis fixa endpointu prowizji
- [ ] `spec/core/04_business_logic.md` — opis logiki obliczeń

**Pliki do zmiany:** `backend/stats/router.py` (linia 1002), `frontend/src/views/CommissionView.vue`
**ROI:** Handlowcy widzą swoje prowizje, system nie crashuje
**Estimate:** 2-3h (S)

---

## 📊 Podsumowanie

| Priorytet | Liczba aktywne | Closed | Effort łączny |
|-----------|----------------|--------|---------------|
| 🚨 P0 | 1 (P0-009) | 3 (P0-006 superseded, P0-007/008 by-design) | ~8-12h |
| 🔴 P1 | 8 | 1 (P1-032 done) | ~17-22h |
| 🟡 P2 | 4 | — | ~12h |
| 🟢 P3 | 2 | — | ~2h |
| **Razem** | **15** | **4** | **~39-48h** |

**Po decyzji Właściciela 2026-05-24 — zmiana strategii:**
- Naprawa data quality (P0-007/008) odrzucona — to BY DESIGN (linia odcięcia)
- P0-006 superseded przez P1-036 (wymaga decyzji biznesowej w P0-009)
- Dodano P0-009 — zaprojektuj UX cut-off (jedyny realny P0)
- Dodano P1-036 — toggle archiwalnych po P0-009
- Dodano P1-037 — walidacja nowych umów (cut-off enforcement)

---

## 📋 Tabela TL;DR

| ID | Tytuł | Źródło | P | Est. | Status | Owner |
|----|-------|--------|---|------|--------|-------|
| RAO-P0-006 | ~~Lista artykułów PUSTA~~ → superseded by P1-036 | audit-2026-05-24 | P0 | S | superseded | — |
| RAO-P0-007 | ~~`total_value=NULL`~~ → BY DESIGN (cut-off line) | audit-2026-05-24 | P0 | M | by-design | — |
| RAO-P0-008 | ~~`is_settled=1`~~ → BY DESIGN (cut-off line) | audit-2026-05-24 | P0 | S | by-design | — |
| **RAO-P0-009** | **Zaprojektuj UX „Linii odcięcia” (Data Cut-off)** | **audit + owner-decision** | **P0** | **M** | **triaged** | **tech-lead+ux** |
| RAO-P1-030 | Bug: GUS nie pobiera danych podczas tworzenia kontrahenta | user-report | P1 | S | triaged | backend-dev |
| RAO-P1-031 | Bug: Błąd podczas pobierania Prowizje | user-report | P1 | S | triaged | backend-dev |
| RAO-P1-032 | Naprawa testów Playwright — 4 błędy testów naprawione | qa-report | P1 | S | done | qa-engineer |
| RAO-P1-033 | Telefony pokazują tylko `+48 ` bez numeru | audit-2026-05-24 | P1 | S | triaged | frontend-dev |
| RAO-P1-034 | Brak roli `salesperson` — handlowiec nie widzi tylko swoich umów | audit + client-vision | P1 | M | triaged | cross-stack |
| RAO-P1-035 | Vue warning `placeholder` w DateRangePicker | audit-2026-05-24 | P1 | XS | triaged | frontend-dev |
| RAO-P1-036 | Toggle „Pokaż archiwalne" + decyzja biznesowa | audit + owner | P1 | S | triaged | cross-stack |
| RAO-P1-037 | Walidacja: nowe umowy MUSZĄ mieć `total_value` (cut-off enforcement) | audit + owner | P1 | S | triaged | backend-dev |
| RAO-P2-021 | UX Raportów — kategorie drilldown + info historyczne (carry-over) | client-notes | P2 | M | in-progress | cross-stack |
| RAO-P2-022 | Lista kontrahentów: brudne dane + brak filtrów | audit-2026-05-24 | P2 | S | triaged | db-agent |
| RAO-P2-023 | Lista umów: brak filtrów po handlowcu/kategorii/roku | audit-2026-05-24 | P2 | M | triaged | frontend-dev |
| RAO-P2-024 | Email kontrahenta z artefaktem `>` (cleanup migracji) | audit-2026-05-24 | P2 | XS | triaged | db-agent |
| RAO-P3-014 | Admin panel: brak kolumn Email/Branch + brak `salesperson_id` | audit-2026-05-24 | P3 | S | triaged | frontend-dev |
| RAO-P3-015 | HomeView KPI 0/0 (po fixie P0-006 i P0-008) | audit-2026-05-24 | P3 | XS | triaged | qa-engineer |

---

## 🗂️ Archiwum sprintów

- Sprint 1 (zakończony 2026-05-22): [archive/BACKLOG_SPRINT_1.md](../archive/BACKLOG_SPRINT_1.md) — 73 taski, ~190h
