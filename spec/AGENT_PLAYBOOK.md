# AGENT_PLAYBOOK.md — Co czytać przed rozpoczęciem pracy

> **Cel:** Każdy agent AI po wejściu do projektu wie *co czytać*, *dlaczego*, i *jak uniknąć common pitfalls*.  
> **Last updated:** 2026-05-17  
> **Read this if:** Jesteś agentem AI (Devin, Cascade, Codex, Aider, etc.) pracującym w RAO

---

## 🚀 Quick Start (5 minut)

1. **Czytaj `README.md`** — mapa całego projektu
2. **Czytaj `AGENT_PLAYBOOK.md`** (ten plik) — znajdź swoją rolę poniżej
3. **Czytaj swój "Primary read"** — spec dla Twojej roli
4. **Sprawdź `backlog/BACKLOG.md`** — co jest do zrobienia
5. **Zacznij od P0** — production blockers first

---

## 📋 Mapa Ról → Spec do czytania

### DB Agent (Database Architect)

**Primary read:**
- `core/01_database.md` — complete DDL, indeksy, FK
- `process/migrations.md` — polityka deterministycznej migracji

**Może modyfikować:**
- `backend/<feature>/models.py` — SQLAlchemy models
- `backend/main.py` startup — ALTER TABLE migrations
- `core/01_database.md` — mirror finalnego stanu

**Nie tyka:**
- Endpointy router.py (delegacja → Backend Agent)
- Frontend (delegacja → Frontend Agent)

**Przed migracją:**
1. Czytaj `process/migrations.md`
2. Sprawdź verification gates
3. Upewnij się że `migration_impact: yes` w zadaniu backlogu

**Common pitfalls:**
- ❌ ALTER bez `IF NOT EXISTS` → drugi restart rzuci "Duplicate column"
- ❌ DROP COLUMN bez user approval → destrukcyjna operacja
- ❌ Brak aktualizacji `core/01_database.md` → zombie-spec

---

### Backend Agent

**Primary read:**
- `core/02_backend_api.md` — endpointy, Pydantic schemas, logika
- `core/04_business_logic.md` — algorytmy (numeracja, kalkulacja)
- `core/25_security.md` — RBAC, auth, walidacja inputu

**Może modyfikować:**
- `backend/<feature>/{schemas,service,router}.py` — endpointy
- `backend/tests/unit/` — testy jednostkowe
- `core/02_backend_api.md` — aktualizacja po zmianach

**Nie tyka:**
- DDL/models (delegacja → DB Agent)
- Frontend (delegacja → Frontend Agent)

**Przed endpointem:**
1. Sprawdź Security DoD w zadaniu backlogu
2. Upewnij się że endpoint ma `Depends(get_current_user)` lub jest oznaczony jako public
3. Dodaj test IDOR jeśli endpoint ma `{id}` w ścieżce

**Common pitfalls:**
- ❌ Endpoint bez `Depends(get_current_user)` → security hole
- ❌ Brak Pydantic constraints → injection risk
- ❌ Brak aktualizacji `core/02_backend_api.md` → zombie-spec
- ❌ Brak testów jednostkowych → regression risk

---

### Frontend Agent

**Primary read:**
- `core/03_frontend_screens.md` — ekrany, komponenty, layout
- `core/06_navigation.md` — routing, flow użytkownika
- `core/09_design_system.md` — Toolsmart colors, fonts, spacing

**Może modyfikować:**
- `frontend/src/views/` — routowalne widoki
- `frontend/src/components/` — reużywalne komponenty
- `frontend/src/stores/` — Pinia stores
- `frontend/src/composables/` — useApi, useDebounce, etc.
- `frontend/src/style.css` — design system variables

**Nie tyka:**
- Backend (delegacja → Backend Agent)
- DDL/models (delegacja → DB Agent)

**Przed komponentem:**
1. Sprawdź Design System w `core/09_design_system.md`
2. Używaj tylko zmiennych CSS (żadnych hardcoded colors)
3. Dodaj `data-testid` dla elementów testowalnych

**Common pitfalls:**
- ❌ Hardcoded colors → naruszenie design systemu
- ❌ Brak loading/error/empty state → złe UX
- ❌ Brak `data-testid` → testy padają przy refactorze
- ❌ Brak aktualizacji `core/03_frontend_screens.md` → zombie-spec

---

### QA Agent

**Primary read:**
- `process/testing.md` — strategia testowania, convention
- `backlog/BACKLOG.md` — acceptance criteria dla każdego zadania
- `core/25_security.md` — security testy (IDOR, RBAC)

**Może modyfikować:**
- `e2e/tests/` — Playwright E2E tests
- `backend/tests/unit/` — pytest unit tests
- `backlog/BACKLOG.md` — dodawanie QA DoD do zadań

**Nie tyka:**
- Kod produkcyjny (tylko testy)

**Przed testami:**
1. Czytaj `process/testing.md`
2. Sprawdź edge case matrix dla endpointu
3. Upewnij się że smoke test `01-login.spec.ts` PASS

**Common pitfalls:**
- ❌ Testy bez `data-testid` → flaky przy refactorze
- ❌ Brak edge cases (401, 403, 404, 422) → regression risk
- ❌ Brak testów migracji deterministycznej → broken migrations
- ❌ Testy tylko happy path → bugs w production

---

### Tech Lead (koordynator)

**Primary read:**
- Wszystko — pełny widok systemu

**Może modyfikować:**
- `spec/` — governance, reorganizacja
- `backlog/BACKLOG.md` — priorytetyzacja, planowanie
- `AGENT_PLAYBOOK.md` — aktualizacja mapy ról

**Nie tyka:**
- Nic w kodzie produkcyjnym (tylko spec)

**Przed planowaniem:**
1. Czytaj ten playbook
2. Sprawdź `backlog/BACKLOG.md` — priorytety, zależności
3. Konsultuj z Product Ownerem dla priorytetów klienta

**Common pitfalls:**
- ❌ Planowanie bez czytania spec → duplikacja pracy
- ❌ Ignorowanie zależności → blocked tasks
- ❌ Brak aktualizacji spec → zombie-spec

---

## 🔄 Routing zadań (Decision Tree)

```
classification: db-only         → DB Agent (sekwencyjnie, blokuje resztę)
classification: backend         → Backend Agent (po DB Agent jeśli migration_impact)
classification: frontend        → Frontend Agent (równolegle z Backend jeśli kontrakt API stabilny)
classification: cross-stack     → DB → Backend → Frontend (sekwencyjnie), QA na końcu
classification: bugfix          → role z `roles:` field, QA repro test PRZED fixem
classification: refactor        → ten sam agent który tworzył oryginał
```

**Zasady równoległości:**
- **Backend ↔ Frontend równolegle** dozwolone TYLKO gdy kontrakt (Pydantic schema + URL) zamrożony w spec PRZED startem
- **Każdy DB-touching task blokuje** wszystkie inne task'i które czytają te same tabele (sequencjne)
- **QA Agent zawsze po** — nie pracuje równolegle z dev'em (smoke test po, e2e po)

---

## 📋 Definition of Done (uniwersalne)

Każde zadanie musi spełnić:

1. **Kod + testy** — unit tests (Backend/DB) lub typecheck zielony (Frontend)
2. **Smoke test** — `e2e/tests/01-login.spec.ts` PASS
3. **Spec updated** — `git diff --stat spec/core/` nie-pusty jeśli zmiana funkcjonalna
4. **Jeśli `migration_impact: yes`:** — verification gates przeszły (drop&recreate test)
5. **Backlog item** — ma `status: review` z linkiem do diffu
6. **Tech Lead review** — przegląda → `done`

---

## 🔒 Security Checklist (dla każdego zadania)

Każde zadanie w backlogu ma sekcję **Security DoD**. Jeśli nie masz — dodaj:

- [ ] Każdy nowy endpoint ma `Depends(get_current_user)` LUB explicite oznaczony jako public w spec
- [ ] Endpointy z `{id}` w ścieżce: test IDOR (user A nie czyta zasobów user B)
- [ ] Endpointy admin-only: test 403 dla zwykłego usera
- [ ] Pydantic schema ma constraints (min/max_length, pattern) na każdym polu user-input
- [ ] Brak nowych sekretów w kodzie/spec (`git diff | grep -iE "password|secret|api.?key"`)
- [ ] Brak `v-html` na user-input we frontendzie
- [ ] Logi nie zawierają PII/hasła/tokenów
- [ ] Zmieniony endpoint → wpis w `core/25_security.md` (RBAC matrix update)

---

## 🧪 Test Data Registry

Deterministyczne dane dla testów (nie używaj produkcyjnych):

| Typ | Test data | Gdzie używać |
|-----|-----------|--------------|
| NIP (valid) | `9512598092` | test GUS, NIP validation |
| NIP (invalid checksum) | `1234567890` | test NIP validation |
| Email test | `test@example.invalid` | test auth, notifications |
| Phone test | `+48 500 000 000` | test walidacji telefonu |
| User test | `test_user` | test RBAC, permissions |
| Kontrahent test | `TEST-KONTRAHENT` | test CRUD, IDOR |

**Zasada:** Nigdy nie używaj produkcyjnych danych w testach. Używaj `anonymize_db.py` dla dev/staging.

---

## 🚨 Common Pitfalls (jak unikać)

### Spec-related
- ❌ Czytanie zombie-spec (12, 13, 14, 18) → czytaj tylko `core/` i `process/`
- ❌ Ignorowanie `backlog/BACKLOG.md` → zawsze sprawdź co jest priorytetem
- ❌ Brak aktualizacji spec po zmianie → zombie-spec

### Code-related
- ❌ Hardcoded colors → użyj zmiennych CSS z `core/09_design_system.md`
- ❌ Brak `data-testid` → testy padają przy refactorze
- ❌ Endpoint bez auth → security hole
- ❌ ALTER bez `IF NOT EXISTS` → drugi start rzuci błąd

### Process-related
- ❌ Rozpoczynanie od P2 zamiast P0 → zawsze zacznij od production blockers
- ❌ Ignorowanie zależności → blocked tasks
- ❌ Brak smoke testu po zmianie → regression risk

---

## 📞 Gdzie szukać pomocy

- **Technical questions:** `core/` spec files (DDL, API, screens)
- **Business logic questions:** `core/04_business_logic.md`
- **Security questions:** `core/25_security.md`
- **Testing questions:** `process/testing.md`
- **Migration questions:** `process/migrations.md`
- **Workflow questions:** `process/workflow.md`

Jeśli nie ma odpowiedzi w spec → to jest gap w specyfikacji. Dodaj do `backlog/BACKLOG.md` jako zadanie P2/P3.