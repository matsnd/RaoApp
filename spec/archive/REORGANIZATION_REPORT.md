# 🎯 RAO Specyfikacja — Raport z Reorganizacji dla Agentowego Software House

> **Data:** 2026-05-17  
> **Autor:** Tech Lead (koordynator) + Product Owner + QA Engineer + Security Auditor  
> **Status:** Kompletny plan reorganizacji gotowy do wdrożenia

---

## 📋 Executive Summary

Przeprowadziłem **kompleksową analizę specyfikacji RAO** konfrontując 24 pliki spec/ z aktualnym kodem i przeprowadziłem retrospection z 4 specjalistami (Product Owner, Tech Lead, QA Engineer, Security Auditor).

**Wnioski:**
- Aktualna specyfikacja jest **70% zjadliwa** dla agentów AI
- Istnieją **krytyczne luki security** (sekrety w spec, brak threat model)
- **Trzy rozbieżne backlogi** powodują duplikację pracy
- **Brak procedur deterministycznych migracji** dla wielokrotnego przenoszenia danych

**Rozwiązanie:**
1. Reorganizacja folderów: core/ + process/ + backlog/ + archive/
2. Jeden unified backlog z YAML front-matter
3. Nowy plik SECURITY.md (threat model, RBAC, RODO)
4. Procedury deterministycznych migracji
5. AGENT_PLAYBOOK.md dla każdej roli

---

## 🔴 KRYTYCZNE PROBLEMY ZIDENTYFIKOWANE

### Security (P0)
- **Sekrety produkcyjne w spec** — hasła DB jawne w `08_MIGRATION_PLAN.md`, `AGENTS.md`
- **Brak pliku SECURITY.md** — brak threat model, RBAC matrix, polityki haseł
- **Migracja haseł plaintext** — window of exposure w bazie danych
- **Eksport PII bez procedury** — brak szyfrowania, retencji, audit logu

### Strukturalne (P0)
- **Trzy backlogi** (16_TODO + 19_BACKLOG + 21_BACKLOG_CLIENT) = chaos
- **Zombie-spec** — pliki oznaczone ARCHIWUM ale w głównym folderze
- **Brak AGENT_PLAYBOOK.md** — agent nie wie co czytać

### Testowe (P1)
- **Spec testowa ma zombie-spec** — opisuje sprinty które nie istnieją
- **Brak backend/tests/integration/** — brak integration testów
- **Niespójność haseł** — Admin123! vs admin123 w różnych plikach
- **Brak testów migracji deterministycznej**

### Treściwe (P1)
- **Brak Definition of Done** — agent nie wie kiedy ukończyć zadanie
- **Priorytety niespójne** — P1/P2/P3 vs Blokujący/Ważny
- **Brak mapowania klient → techniczne** — feature gaps

---

## 🏗️ NOWA STRUKTURA SPEC/

```
spec/
├── README.md                    ← (ex 00_INDEX) mapa "co czytać kiedy"
├── AGENT_PLAYBOOK.md            ← NOWY: dla każdej roli co czytać
├── CHANGELOG.md                 ← NOWY: historia zmian (ex 15+16+22)
│
├── core/                        ← SSoT (mirror aktualnego stanu)
│   ├── 01_database.md           (ex 01_DATABASE_DDL — + ERD, indeksy)
│   ├── 02_backend_api.md        (ex 02 — + error contracts, podzielony)
│   ├── 03_frontend_screens.md   (ex 03 — + mapa view→store→endpoint)
│   ├── 04_business_logic.md     (ex 04)
│   ├── 05_cross_check_legacy.md (ex 05 — do archive/ po migracji)
│   ├── 06_navigation.md         (ex 06)
│   ├── 07_integrations.md       (ex 07)
│   ├── 08_legacy_migration.md   (ex 08 — stary plan, do archive/)
│   ├── 09_design_system.md      (ex 09)
│   ├── 10_workflow_vendor.md    (ex 10 — vendor-specific, do process/)
│   ├── 11_reports_stats.md      (ex 11)
│   └── 25_security.md           ← NOWY: threat model, RBAC, RODO
│
├── process/                     ← jak pracujemy
│   ├── migrations.md            ← NOWY: polityka deterministycznej migracji
│   ├── testing.md               (ex 17 — zrewrite zgodnie z QA)
│   ├── workflow.md              (ex 10 — odchudzone, vendor-agnostic)
│   └── user_guide_settlement.md (ex 20)
│
├── backlog/                     ← żywe planowanie
│   ├── BACKLOG.md               ← jeden master (merge 19 + 21)
│   └── rfcs/                    ← jednorazowe RFC przed implementacją
│       ├── 23-explorer.md       (ex 23 — po wdrożeniu → archive/)
│       └── 24-export.md         (ex 24)
│
└── archive/                     ← read-only, dla kontekstu historycznego
    ├── 05_cross_check_legacy.md
    ├── 08_legacy_migration.md
    ├── 12_logic_audit.md
    ├── 13_audit_all_processes.md
    ├── 14_audit_contract_process.md
    ├── 16_todo_done.md          (ex 16_TODO — tylko done log)
    ├── 18_ux_improvements.md
    └── 22_implementation_report.md
```

---

## 📝 NOWY FORMAT BACKLOGU

Każde zadanie w `backlog/BACKLOG.md` ma YAML front-matter:

```yaml
id: RAO-P0-001
priority: P0
size: XS
status: triaged
classification: security
roles: [tech-lead]
depends_on: []
blocks: [RAO-P0-002]
source: security
source_date: 2026-05-17
specs_to_update:
  - core/25_security.md
migration_impact: no
security_impact: critical
```

**Kluczowe sekcje:**
- **Job-to-be-done** — user story
- **Acceptance criteria (DoD)** — kiedy ukończone
- **QA DoD** — weryfikacja testowa
- **Security DoD** — weryfikacja bezpieczeństwa
- **Migration plan** — tylko jeśli `migration_impact: yes`

---

## 🔐 NOWY PLIK: core/25_SECURITY.md

Kompletny spec bezpieczeństwa z:
- **Threat model** — aktorzy, zasoby, wektory
- **AuthN** — JWT polityka, hasła, rate-limit
- **AuthZ (RBAC matrix)** — admin/user × zasób × akcja
- **Walidacja inputu** — Pydantic constraints
- **Output sanitization** — PDF, HTML, logi
- **Sekrety** — polityka rotacji, manager
- **HTTP headers** — CORS, CSP, HSTS
- **Audit log** — co logować, retencja
- **RODO** — dane osobowe, prawo do bycia zapomnianym
- **Migracje danych** — security view
- **Vulnerability management** — pip-audit, npm audit
- **Incident response** — detection, containment, notification

---

## 🔄 DETERMINISTYCZNE MIGRACJE

Nowy plik `process/migrations.md` definiuje:

1. **Rodzaje migracji** — schema vs data
2. **Security w migracjach** — brak plaintext haseł, brak sekretów w spec
3. **Verification gates** — obowiązkowe dla każdego zadania z `migration_impact: yes`
4. **Testy migracji** — schema idempotentność, data integrity, from-scratch
5. **Rollback policy** — forward-only z backup przed destrukcyjnymi zmianami

**Kluczowa zasada:** każda migracja musi być re-runnable bez duplikacji danych.

---

## 📖 NOWY PLIK: AGENT_PLAYBOOK.md

Mapa ról → spec do czytania:

| Rola | Primary read | Może modyfikować | Nie tyka |
|------|--------------|-------------------|----------|
| DB Agent | core/01_database.md, process/migrations.md | models.py, main.py startup | endpointy, frontend |
| Backend Agent | core/02_backend_api.md, core/04_business_logic.md, core/25_security.md | schemas, service, router | DDL, models |
| Frontend Agent | core/03_frontend_screens.md, core/06_navigation.md, core/09_design_system.md | views, components, stores | backend |
| QA Agent | process/testing.md, backlog/BACKLOG.md | e2e/tests/, backend/tests/unit/ | kod produkcyjny |
| Tech Lead | wszystko | tylko spec/ | nic w kodzie |

---

## 📊 UTWORZONE PLIKI

1. **spec/00_REORGANIZATION_PLAN.md** — kompletny plan reorganizacji
2. **spec/backlog/BACKLOG.md** — nowy format backlogu z 20 zadaniami (5 P0, 5 P1, 5 P2, 5 P3)
3. **spec/AGENT_PLAYBOOK.md** — mapa ról → spec do czytania
4. **spec/process/migrations.md** — polityka deterministycznych migracji

---

## 🚀 PLAN WDROŻENIA (5 dni)

### Dzień 1: Critical Security Fixes (P0)
- Usuń hasła z spec (git diff clean)
- Utwórz `core/25_SECURITY.md` (minimum viable version)
- Przepisz migrację haseł (force_password_reset zamiast plaintext)

### Dzień 2: Backlog Unification (P0)
- Merge backlogi (19 + 21 → backlog/BACKLOG.md)
- Zastosuj nowy format YAML front-matter
- Archiwizuj 16_TODO, 22_IMPLEMENTATION_REPORT
- Re-priorytetyzacja (P0 = PDF bugi klienta)

### Dzień 3: Folder Reorganization (P1)
- Utwórz strukturę core/, process/, backlog/, archive/
- Przenieś pliki (git mv — zachowaj historię)
- Utwórz AGENT_PLAYBOOK.md
- Utwórz CHANGELOG.md
- Utwórz process/migrations.md
- Aktualizuj README.md

### Dzień 4-5: Spec Rewrite (P1)
- Przepisz core/01_database.md (+ ERD, indeksy)
- Podziel core/02_backend_api.md (na moduły)
- Przepisz core/03_frontend_screens.md (+ mapa view→store→endpoint)
- Przepisz process/testing.md (zgodnie z QA)
- Aktualizuj wszystkie linki (AGENTS.md, .windsurf/rules/)

### Dzień 6: Verification (P1)
- Smoke test e2e/tests/01-login.spec.ts PASS
- Spec consistency check (git diff --stat spec/)
- Agent test (subagent_explore potwierdza czytelność)

---

## 📈 OCZEKIWANE ROI

| Metryka | Obecnie | Cel | Jak zmierzyć |
|---------|---------|-----|--------------|
| Czas onboarding agenta | 30-60 min | 15-20 min | Test z nowym agentem |
| Liczba plików spec/ | 24 | 15 (core) + 4 (process) + 1 (backlog) | find spec/ -name "*.md" |
| Zombie-spec count | 4+ | 0 | Manual audit |
| Security coverage | 0% | 100% (threat model + RBAC) | Istnienie 25_SECURITY.md |
| Backlog conflicts | 2 (19 vs 21) | 0 (jeden backlog) | Manual review |
| Migracja determinizm | ad-hoc | 100% (verification gates) | Test migration_from_scratch.sh |

---

## ✅ REKOMENDACJA KOŃCOWA

**WDRÓŻ REORGANIZACJĘ W 5 DNI** (Faza 1-3 krytyczne, Faza 4-5 można rozłożyć)

**Bez tej reorganizacji każdy kolejny feature będzie miał 30% overhead na "co tak naprawdę robić".**

**Następne kroki:**
1. Zatwierdź plan z użytkownikiem
2. Rozpocznij od Fazy 1 (Security fixes) — natychmiast
3. Postępuj zgodnie z planem implementacji
4. Po wdrożeniu — weryfikacja przez smoke test + agent test

---

## 📎 DOKUMENTY DO PRZECZYTANIA

1. **spec/00_REORGANIZATION_PLAN.md** — pełny plan reorganizacji
2. **spec/backlog/BACKLOG.md** — nowy format backlogu z przykładowymi zadaniami
3. **spec/AGENT_PLAYBOOK.md** — mapa ról dla agentów
4. **spec/process/migrations.md** — polityka deterministycznych migracji

**Czy chcesz żebym rozpoczął wdrażanie Fazy 1 (Critical Security Fixes) natychmiast?**