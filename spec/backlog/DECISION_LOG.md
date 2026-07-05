# RAO — Decision Log

> **Cel:** Pełna historia decyzji projektowych RAO — co, kiedy, dlaczego, status.
> Single source of truth dla "skąd się wzięło to rozwiązanie".
> Aktualizowany przy każdej decyzji architektonicznej / biznesowej / odłożeniu zadania.

---

## Legenda statusów

| Status | Znaczenie |
|--------|-----------|
| `done` | Zaimplementowane, przetestowane, zamknięte |
| `team-verified` | Zaimplementowane + weryfikacja software-house (QA/Security/UX/PO/Tech Lead) |
| `user-verified` | Wymaga wizualnej weryfikacji operatora (PDF, UI) |
| `dev-verified` | Zaimplementowane + testy programatyczne, czeka na team-verified |
| `client-approved` | Klient zatwierdził (final) |
| `deferred` | Świadomie odłożone (z uzasadnieniem) |
| `removed` | Usunięte z backlogu (z uzasadnieniem) |

---

## Sprint 2026-05-25 → 2026-07-05 (zamknięty)

**Backlog zarchiwizowany:** `spec/backlog/archiwum/BACKLOG_SPRINT_20260525_20260705.md`
**Liczba zadań:** 48 (P0: 7, P1: 14, P2: 22, P3: 1, SEC: 2, decyzje: 2)
**Commity:** 452 w historii git

---

## Sprint 2026-07-05 → (bieżący)

### P0-001 — `/stats/currently-rented` 500 (Pydantic ValidationError)

**Data:** 2026-07-05
**Status:** done (naprawione 2026-07-05)
**Decyzja:** Naprawione natychmiast po zgłoszeniu — operator poprosił o wyleczenie systemu.
**Root cause:** `stats/router.py:312` używa `id=r[0]` ale schema wymaga `article_id`. Fix = jednopunktowa zmiana `id=` → `article_id=`.
**Weryfikacja:** `/stats/currently-rented` → 200 (31 items, 86 machines). Playwright test PASS. Vision screenshot potwierdza KPI + tabela z 31 wierszami + kontrahenci.

---

## P0 — Production Blockers (wszystkie done/team-verified)

| ID | Tytuł | Decyzja / Dlaczego | Status | Implementacja |
|----|-------|--------------------|--------|---------------|
| RAO-P0-030 | UNIQUE na contract.number + FOR UPDATE | Race condition w generowaniu numeru umowy → unique constraint + FOR UPDATE + retry×3 | team-verified | `unique=True` w model + DB index `uq_contracts_number` + 4 testy PASS |
| RAO-P0-031 | XSS w PDF — Jinja2 autoescape | PDF generowany z user input bez escape → autoescape=True + markupsafe.escape() | done | `autoescape=True` w `reports/service.py:588` |
| RAO-P0-032 | build_contract_data mutuje sesję | SQLAlchemy session mutation bug → lokalne kopie description | done | Lokalne kopie `description` w `fees_data` |
| RAO-P0-033 | recalculate_total — algorytm kaskadowy | Legacy używało prostego mnożenia → kaskadowe rate1/period_count/minimum jak w WinForms | team-verified | `calculate_position_value` tiered, 18 testów PASS |
| RAO-P0-034 | ContractUpdate schema z exclude_unset | PUT z częściowymi danymi nadpisywał nullami → exclude_unset=True | team-verified | `exclude_unset=True` w `update_contract`, 3 testy PASS |
| RAO-P0-035 | N+1 queries | List endpointy robiły N+1 → selectinload + batch-fetch | team-verified | `selectinload(conditions)` w `list_positions`, batch-fetch w `list_contracts/articles` |
| RAO-P0-036 | Stack trace disclosure | 500 zwracał pełny stack → global handler z generic message | team-verified | Global exception handler w `main.py`, JSONResponse 500 "Błąd serwera" + `logger.exception` |
| RAO-P0-054 | Kategorie — normalizacja nazw | Diakrytyki + spacje powodowały duplikaty kategorii → normalize + polish_ci collation | team-verified | `normalize` w `settings/service.py` + `ALTER TABLE polish_ci` w `main.py`, 19 testów PASS |

---

## P1 — Must-Have (wszystkie done/team-verified/user-verified)

| ID | Tytuł | Decyzja / Dlaczego | Status | Implementacja |
|----|-------|--------------------|--------|---------------|
| RAO-P1-014 | Błędne obliczanie daty końcowej | Off-by-one w dacie końcowej okresu | user-verified | → client-approved |
| RAO-P1-015 | PDF — ukryć telefony na wydruku | Klient nie chce telefonów w PDF | team-verified | → user-verified |
| RAO-P1-016 | PDF Protokół ZO — brak adresu dostawy | Adres dostawy brakował w protokole | team-verified | → user-verified |
| RAO-P1-017 | Naprawa Nominatim | Auto-fill adresu z uwag dojazdowych nie działał | team-verified | Nominatim hybryda offline+online, debounce 800ms, AbortController |
| RAO-P1-018 | PDF — usuń pieczątkę z pierwszej strony | Pieczątka na str.1 niepotrzebna (S i U) | team-verified | → user-verified |
| RAO-P1-019 | PDF Umowa usługi (U) — redesign | Umowa U wyglądała inaczej niż S → unify | dev-verified | → user-verified (PDF generuje, do wizualnej weryfikacji) |
| RAO-P1-020 | PDF — rozliczenie kaskadowe | Rozliczenie w PDF nie pokazywało kaskady | dev-verified | → user-verified (algorytm działa, do wizualnej weryfikacji) |
| RAO-P1-021 | Pole "Wartość (zł)" | **Decyzja biznesowa:** pole przechodzi do ekranu rozliczenia (nie formularz). Wartość z Fakturowni LUB ręcznie | team-verified | `total_value` usunięte (martwe pole), `settlementTotalValue` computed read-only |
| RAO-P1-022 | Nazewnictwo umów — S i G dla Gdańska | Oddział Gdańsk potrzebuje suffixu G w numerze | dev-verified | Format `S{NNN}/{ROK}G` działa, → user-verified |
| RAO-P1-037 | delete_contract — guard na is_settled | Usunięcie rozliczonej umowy traci dane → blokada | team-verified | Guard `is_settled` → 409 w `delete_contract` |
| RAO-P1-038 | Brak indeksów DB | 5 kolumn bez indeksów → wolne zapytania | team-verified | 5 indeksów w DB (`main.py CREATE INDEX IF NOT EXISTS`) |
| RAO-P1-039 | Walidacja date_from > date_to + ujemne kwoty | Brak walidacji w ContractCreate | team-verified | `model_validator` odrzuca `date_from>date_to` + kwoty<0 |
| RAO-P1-040 | is_settled blokuje mutacje pozycji | Rozliczona umowa nie powinna być modyfikowana | team-verified | Guard `is_settled` na wszystkich mutatorach |
| RAO-P1-041 | Hardcoded JWT fallback "change-me" | Security risk → wymuś z env | team-verified | JWT z env, validator odrzuca "" i "change-me", `config.py.bak` usunięty |
| RAO-P1-042 | Frontend: logout + redirect + baseURL z env | Token leak po logout, hardcoded baseURL | team-verified | Logout hard redirect, `baseURL` z `VITE_API_URL`, redirect po 401 |
| RAO-P1-043 | Frontend: memory leaks | Event listenery i timery nie czyszczone | team-verified | `onUnmounted` cleanup wszędzie (ArchiveView, DashboardView, ContractFormView) |
| RAO-P1-044 | localStorage 'token' → 'rao_token' | Brak prefiksu → kolizje z innymi apps | team-verified | 11/11 `rao_token`, 0 trafień bez prefiksu |
| RAO-P1-045 | _build_conditions_text — dedup | Duplikaty warunków w tekście | team-verified | `format_position_conditions_cascading` z dedup, 4 testy PASS |
| RAO-P1-055 | Branch — migracja + /stats/by-branch | Oddział Gdańsk potrzebuje statystyk per branch | done | Migracja `branch_id` z G suffix + indeks `idx_contracts_branch_id` + endpoint + 12 unit tests |
| RAO-P2-060 | Statystyki — gruba krecha legacy vs nowe | Legacy stats vs nowe niespójne → unify | team-verified | 9 bugów PASS, 3 indeksy, merge do AnalyticsView, ArchiveView osobny, 70 testów PASS |
| RAO-P2-062 | Archiwum — migracja legacy do `archive_*` | Legacy umowy wymieszane z nowymi → separacja tabel | team-verified | 742 umów w `archive_*`, 62 nowe, 15 endpointów `/archive/*`, ArchiveView 4 zakładki, 22 testy PASS |

---

## P2 — Should-Have (wszystkie done/team-verified)

| ID | Tytuł | Decyzja / Dlaczego | Status | Implementacja |
|----|-------|--------------------|--------|---------------|
| RAO-P2-028 | Statystyki miast via PNA | **Decyzja:** grupuj po `postal_code` (PNA) + miasto. Jedno miasto = wiele PNA | done | Faza 1+2+3: `shared/locations` + `shared/revenue`, `extract_city` usunięte, drill-down po PNA |
| RAO-P2-029 | Statystyki — audyt determinizmu | Niespójności archiwalnych statystyk | done | dev-verified → user-verified |
| RAO-P2-047 | Rate limiting /auth/login + /auth/forgot-password | Brute-force protection | done | In-memory limiter 5/60s/IP, 429+Retry-After, 8 unit tests |
| RAO-P2-048 | Swagger docs_url=None na produkcji | Publiczne API docs = security risk | done | Warunkowe `docs_url`/`redoc_url` z `RAO_ENV` |
| RAO-P2-049 | Frontend error/loading/empty states | Brak feedback przy błędach/ładowaniu | done | `StateMessage.vue` + `TableSkeleton.vue` + `SkeletonRow.vue` w 13 widokach |
| RAO-P2-050 | Frontend form validation | Brak walidacji po stronie klienta | done | `validateForm()` w 4 formularzach + required/aria-invalid/pattern/min/max + NIP checksum |
| RAO-P2-051 | Cache dla statystyk (TTL 5 min) | Stats read-heavy → cache zmniejsza DB load | done | `TTLCache` in-memory (thread-safe), 11 endpointów stats, `/cache/clear` + `/cache/stats`, 22 unit tests |
| RAO-P2-052 | /explorer/locations/{city} SQL filter | Filtrowanie w Pythonie zamiast SQL → wolne | done | SQL WHERE + LEFT JOIN, `contract_ids` param |
| RAO-P2-053 | /stats/positions — double _compute + paginacja | 2× wywołanie `_compute_position_revenues` → wolne | done | Single compute + `limit/offset/total_count` (backward compat) |
| RAO-P2-056 | contract_type (S/U) grupowanie | Brak statystyk per typ umowy | done | `/stats/by-contract-type` + `aggregate_by_contract_type` w `calc.py` |
| RAO-P2-057 | is_external — filtrowanie czy usunąć | **Decyzja:** external nie blokuje (nie wpływa na rentowność). Checkbox w details | team-verified | `is_external` nie blokuje + checkbox w details |
| RAO-P2-058 | Fakturownia OID + product cache | OID = numer umowy, mapowanie artykułów z metadanymi | done | OID hybrydowe (`contract.oid ?? contract.number`) + product cache (`sync_products`/`search_products`) + 7 unit tests |
| RAO-P2-059 | Usługi dodatkowe — migracja per-artikel | Legacy plain-text → structured per-artikel | done | `ContractServiceFee` model + CRUD + `migrate_service_fees.py` + `ServiceFeeTemplate` + 9 unit tests |
| RAO-P2-061 | Demo data seeding | Showcase statystyk wymaga danych | done | 11 artykułów, 8 kontrahentów, 24 umowy, 74 rozliczenia (72% FA), 12 faktur FA |
| RAO-P2-063 | Merge Statystyki + Raporty → AnalyticsView | Dwa osobne widoki → unify | team-verified | AnalyticsView z 4 zakładkami (Live, Period, Locations, Explorer) |
| RAO-P2-064 | Opcje wydruku PDF | `hide_delivery_address` + `signatures_on_page1` + cleanup `report_without_data` | team-verified | Opcje w PDF generation |
| RAO-P2-065 | Statystyki — poprawki po full-team review | ROI, kontrahent, kategorie, bugi UX/UI | team-verified | 18 testów PASS (4 stale testy naprawione 2026-07-05) |
| RAO-P2-066 | Rezerwacje maszyn — UI + integracja | Martwy moduł backend → ożywienie | team-verified | UI + integracja z availability |
| RAO-P2-067 | Demo data refactor | `migrate_all.py` orchestrator + FA-pending + delivery_address | done | 31 faktur FA (19 backfill + 12 FA-pending), delivery_address z miastami, hardcoded token usunięty |
| RAO-P2-068 | Demo data — cenniki kaskadowe | Pełna konfiguracja "jak od klienta" | done | 5 cenników kaskadowych per maszyna, 6 presetów usług, 22 SFTI, 6 rate types |
| RAO-P2-069 | Analytics — agregacja po mieście | Toggle Miasto/PNA + drill-down | done | Toggle w `LocationsTab`, 1 wiersz per miasto (Warszawa 3978 PNA → 1), drill-down `/locations/city/{city}` |
| RAO-P2-070 | Audyt interaktywności | 30 usterek UX (8 HIGH, 13 MEDIUM, 9 LOW) | team-verified | Faza 1 (23 alert→toast) + Faza 2 (drilldown 50+11 linków) + Faza 3 (sort 5/9 kolumn) + Faza 5 (goBack `router.back`) |

---

## P3 — Nice-to-Have

| ID | Tytuł | Decyzja / Dlaczego | Status | Implementacja |
|----|-------|--------------------|--------|---------------|
| RAO-P3-071 | Audyt UX — czytelność, spójność, a11y | 5 faz: font-size, kontrast, a11y, design system, skeleton loaders | team-verified | Faza 1 (font-size 11→13px, kontrast WCAG AA) + Faza 2 (formatCurrency/formatDate) + Faza 3 (a11y: focus-visible, aria-label, role="alert"/"dialog") + Faza 4 (CSS variables unify) + Faza 5 (TableSkeleton, view transitions, glossary tooltips) |

---

## Security (pre-existing issues z audit P1-015)

| ID | Tytuł | Decyzja / Dlaczego | Status | Implementacja |
|----|-------|--------------------|--------|---------------|
| RAO-SEC-001 | IDOR `/reports/contract/{id}` | Brak ownership check w PDF generation | done | Ownership check dodany |
| RAO-SEC-002 | Jinja2 bez autoescape | XSS w PDF → autoescape=True | done | `autoescape=True` w `reports/service.py` (zmapowane do P0-031) |

---

## Decyzje operatora (środowiskowe / biznesowe)

### RAO-P1-021 — Pole "Wartość (zł)" → ekran rozliczenia
**Data:** 2026-06-30
**Decyzja:** Pole "Wartość" przechodzi do **ekranu rozliczenia** (nie formularz umowy).
**Dlaczego:** Wartość nie jest znana przy tworzeniu umowy — dopiero po rozliczeniu.
**Implementacja:** Ekran rozliczenia pobiera pozycje umowy, pozwala uzupełnić kwoty (auto z Fakturowni lub ręcznie), sumuje → wartość umowy. Pole "Wartość" w formularzu umowy ukryte/puste.
**Status:** team-verified (`total_value` usunięte, `settlementTotalValue` computed read-only)

### RAO-P2-028 — Statystyki miast via PNA
**Data:** 2026-06-30
**Decyzja:** Grupuj po `postal_code` (PNA) + miasto (precyzyjne).
**Dlaczego:** Jedno miasto ma wiele PNA — grupowanie po nazwie miasta traci precyzję.
**Pilne:** Wymagało analizy źródeł danych PNA (tabela `postal_codes`, integracja TERYT, GUS).
**Status:** done (Faza 1+2+3 complete)

### RAO-P2-046 — IDOR / RBAC (USUNIĘTE Z BACKLOGU)
**Data:** 2026-06-30 (decyzja), 2026-07-05 (usunięcie z backlogu)
**Decyzja:** **Brak izolacji** na ten moment (single-tenant, wszyscy widzą wszystko).
**Dlaczego:** Aplikacja jest single-tenant, wszyscy użytkownicy widzą wszystkie dane. RBAC dodamy gdy pojawi się potrzeba multi-tenant.
**Akcja:** Zostaw tylko SEC-001 (PDF ownership check). P2-046 usunięte z backlogu.
**Status:** removed

### RAO-P2-057 — is_external (maszyna zewnętrzna)
**Data:** 2026-06-30
**Decyzja:** Maszyna external **nie blokuje** dodawania w wielu miejscach (nie wpływa na rentowność).
**Dlaczego:** External = maszyna niebędąca własnością firmy, ale wynajmowana. Nie powinna blokować operacji.
**Implementacja:**
- Możliwe do wyboru w detailsach maszyny podczas dodawania
- Sprawdzenie mechanizmu blokowania maszyn (czy external poprawnie nie blokuje)
- Sprawdzenie vs wyliczanie dni umowy
- Blokada = pytanie z informacją (gdzie i dlaczego zablokowana)
**Status:** team-verified

---

## Architektura — kluczowe decyzje techniczne

### Migracje DB — deterministyczne (bez Alembic)
**Decyzja:** RAO nie używa Alembic. Schema zarządzane przez:
1. Modele SQLAlchemy w `backend/<feature>/models.py`
2. `Base.metadata.create_all` przy starcie
3. Idempotentne `ALTER TABLE ... IF NOT EXISTS` w `@app.on_event("startup")` w `backend/main.py`
4. DDL w `spec/core/01_database.md` jako single source of truth

**Dlaczego:** Alembic dodaje złożoność dla single-developer project. Deterministyczne migracje są prostsze i wystarczające.

### Cache — in-memory TTLCache (bez Redis)
**Decyzja:** Własna implementacja `TTLCache` w `shared/cache.py` (bez Redis/cachetools).
**Dlaczego:** Single-instance FastAPI → in-memory cache wystarcza. Redis = dodatkowa infrastruktura.
**TTL:** Stats 5 min (300s), słowniki 1h (3600s).

### Fakturownia — OID hybrydowe
**Decyzja:** OID = `contract.oid` jeśli ustawiony, w przeciwnym razie `contract.number`.
**Dlaczego:** Pozwala na custom OID dla specjalnych umów, ale fallback na numer umowy dla standardowych.

### Archiwum — separacja tabel
**Decyzja:** Legacy umowy (z WinForms) migracja do osobnych tabel `archive_*`.
**Dlaczego:** Legacy dane mają inną strukturę (brak niektórych pól, inne typy). Mieszanie z nowymi umowami powoduje niespójności.

### Stats — `shared/revenue.py` (extracted z `stats/router.py`)
**Decyzja:** Logika obliczania przychodu wydzielona do `shared/revenue.py`.
**Dlaczego:** DRY — używana przez stats, reports, explorer. Wcześniej duplikowana w 3 miejscach.

### Locations — `shared/locations.py` (PNA-based)
**Decyzja:** Grupowanie lokalizacji po `postal_code` (PNA) z LEFT JOIN do `postal_codes`.
**Dlaczego:** Precyzja — jedno miasto ma wiele PNA. Fallback na `contracts.postal_code` gdy brak FK.

---

## Backlog cleanup — 2026-07-05

**Akcja:** Cały backlog zarchiwizowany do `spec/backlog/archiwum/BACKLOG_SPRINT_20260525_20260705.md`.
**Dlaczego:** Wszystkie 48 zadań ukończone (done/team-verified/user-verified). Backlog miał ~15 duplikatów (~10700 linii). Czyszczenie do pustego szablonu dla nowego sprintu.
**P2-046 (IDOR):** Usunięte z backlogu (decyzja biznesowa — single-tenant, brak izolacji potrzebna teraz).

---

## Nowy sprint — zasady

1. Nowe zadania dodawane na podstawie wymagań klienta / operatora
2. Format: YAML front-matter + sekcje (jak w poprzednim backlogu)
3. Status flow: `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved (done)`
4. Po zakończeniu zadania → lokalny commit + update DECISION_LOG.md
5. Każda decyzja architektoniczna/biznesowa → sekcja w DECISION_LOG.md
