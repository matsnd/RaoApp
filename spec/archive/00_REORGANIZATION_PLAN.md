# Reorganization Plan — Specyfikacja RAO dla Agentowego Software House

> **Data:** 2026-05-17  
> **Autorzy:** Tech Lead (koordynator) + Product Owner + QA Engineer + Security Auditor  
> **Status:** Draft do akceptacji  
> **Cel:** Przekształcenie spec/ z 70% zjadliwości do 95% zjadliwości dla agentów AI

---

## 📋 Executive Summary

**Problem:** Aktualna specyfikacja RAO ma 24 pliki w płaskiej strukturze, 3 rozbieżne backlogi, zombie-spec, brak security spec, i brak deterministycznych procedur migracji. Każdy nowy agent traci 30-60 minut na zrozumienie "co robić".

**Rozwiązanie:** 
1. Reorganizacja folderów: core/ + process/ + backlog/ + archive/
2. Jeden unified backlog z YAML front-matter
3. Nowy plik SECURITY.md
4. Procedury deterministycznych migracji
5. AGENT_PLAYBOOK.md dla każdej roli

**Expected ROI:** 
- -50% czasu onboarding nowych agentów
- -80% duplikacji pracy (konflikty backlogów)
- +100% pokrycia security (obecnie 0%)
- +100% determinizm migracji (obecnie ad-hoc)

---

## 🔴 KRYTYCZNE PROBLEMY ZIDENTYFIKOWANE PRZEZ ZESPÓŁ

### A. Strukturalne (Tech Lead)

| Problem | Priorytet | Impact |
|---------|-----------|--------|
| Płaska numeracja 00-25 miesza typy dokumentów | P0 | Agent czyta zombie-spec |
| Trzy backlogi (16_TODO + 19_BACKLOG + 21_BACKLOG_CLIENT) | P0 | Duplikacja pracy |
| Sekrety produkcyjne w spec/ (hasła DB) | P0 | Security breach risk |
| Brak AGENT_PLAYBOOK.md | P1 | Agent nie wie co czytać |
| Zombie-spec (12, 13, 14, 18 oznaczone ARCHIWUM ale w głównym folderze) | P1 | Zaszumienie informacji |

### B. Treściwe (Product Owner)

| Problem | Priorytet | Impact |
|---------|-----------|--------|
| Brak Definition of Done w zadaniach | P0 | Agent nie wie kiedy ukończyć |
| Priorytety niespójne (P1/P2/P3 vs Blokujący/Ważny) | P0 | Zła kolejność pracy |
| Brak mapowania klient → techniczne | P1 | Feature gaps |
| Brak "Job-to-be-done" w zadaniach | P1 | Agent nie rozumie "dlaczego" |
| Sprint plan w spec (Sprint 4/5/6/7) | P2 | Nie miejsce na sprint planning |

### C. Testowe (QA Engineer)

| Problem | Priorytet | Impact |
|---------|-----------|--------|
| Spec testowa ma zombie-spec (S1-S3 sprinty nie istnieją) | P0 | Testy nieaktualne |
| Brak backend/tests/integration/ | P0 | Brak integration testów |
| Niespójność haseł (Admin123! vs admin123) | P0 | Testy padają od razu |
| Brak data-testid registry | P1 | Refactor = testy padają |
| Brak testów migracji deterministycznej | P1 | Migracje nie są weryfikowane |

### D. Security (Security Auditor)

| Problem | Priorytet | Impact |
|---------|-----------|--------|
| Sekrety produkcyjne w spec/08_MIGRATION_PLAN.md | P0 | Hasła w repo |
| Brak pliku SECURITY.md | P0 | Brak threat model, RBAC matrix |
| Migracja haseł z plaintext (window of exposure) | P0 | Hasła w plaintext w bazie |
| Eksport PII bez procedury (24_EXPORT) | P0 | RODO violation risk |
| Brak Security DoD w zadaniach backlogu | P1 | Security nie jest weryfikowane |

---

## 🏗️ NOWA STRUKTURA FOLDERÓW SPEC/

```
spec/
├── README.md                    ← (ex 00_INDEX) mapa "co czytać kiedy"
├── AGENT_PLAYBOOK.md            ← NOWY: dla każdej roli co czytać
├── CHANGELOG.md                 ← NOWY: historia zmian (ex 15+16+22)
│
├── core/                        ← SSoT (mirror aktualnego stanu)
│   ├── 01_database.md           (ex 01_DATABASE_DDL — + ERD, indeksy, tabele-bez-modeli)
│   ├── 02_backend_api.md        (ex 02 — + error contracts, podzielony na moduły)
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
    ├── 22_implementation_report.md
    └── legacy_specs/             ← stare pliki sprzed reorganizacji
```

**Zasady:**
- `core/` — max 600 linii/plik, powyżej dziel na pod-pliki
- `process/` — procedury, nie stan
- `backlog/` — tylko żywe planowanie
- `archive/` — read-only, żaden agent nie musi czytać

---

## 📝 NOWY FORMAT BACKLOGU (YAML front-matter)

Każda pozycja w `backlog/BACKLOG.md`:

```markdown
### [RAO-042] Podpisy umowy tylko na ostatniej stronie

```yaml
id: RAO-042
priority: P1
size: S
status: triaged            # todo | triaged | in_progress | blocked | review | done
classification: bugfix     # db-only | backend | frontend | cross-stack | bugfix | refactor
roles: [frontend]
depends_on: []
blocks: []
source: client              # client | internal | security
source_date: 2026-04-08
specs_to_update:
  - core/11_reports_stats.md
migration_impact: no
security_impact: low
```

**Job-to-be-done:**
Jako handlowiec wysyłający umowę do podpisu chcę, żeby podpisy były tylko 
na ostatniej stronie, żeby dokument wyglądał profesjonalnie i nie mylił klienta.

**Legacy parity:** Stara WinForms (Crystal Report `umowa.rpt`) miała podpisy 
na końcu — regresja przy migracji.

**Acceptance criteria (DoD):**
- [ ] PDF wygenerowany dla umowy 5-stronicowej ma podpisy TYLKO na str. 5
- [ ] CSS `page-break-inside: avoid` na bloku podpisów
- [ ] Test wizualny: screenshot porównawczy w `e2e/visual/contract-pdf.spec.ts`
- [ ] `core/11_reports_stats.md` zaktualizowany

**QA DoD:**
- [ ] E2E test w `04-contract.spec.ts` rozszerzony o weryfikację podpisów
- [ ] Smoke test `01-login.spec.ts` PASS
- [ ] Brak nowych TS errors: `npx vue-tsc --noEmit` PASS

**Security DoD:**
- [ ] Brak `v-html` na user-input w szablonie PDF
- [ ] Logi nie zawierają PII (weryfikacja: `grep -r logger.*password backend/reports/`)

**Pliki do zmiany:** `backend/reports/templates/contract.html`, `contract.css`
**Out of scope:** Protokół (osobne zadanie), redesign nagłówka

**ROI:** 100% wysyłanych umów, koszt aktualnie = zażenowanie u klienta
**Estimate:** 2h (S)
```

**Sekcje backlogu:**
1. **🚨 P0 — Production blockers** (max 5, deadline ostry)
2. **🔴 P1 — Must-have przed go-live klienta** (feature parity + krytyczne bugi)
3. **🟡 P2 — Should-have w ciągu kwartału**
4. **🟢 P3 — Icebox** (pomysły, bez harmonogramu)
5. **✅ Done log** (link do `archive/16_todo_done.md`)

---

## 🔐 NOWY PLIK: core/25_SECURITY.md

Szkielet (pełna wersja do implementacji):

```markdown
# 25_SECURITY.md — Single Source of Truth Bezpieczeństwa

> **Owner:** Security Auditor | **Last verified:** 2026-05-17
> **Read this if:** Wszyscy agenci — security jest inwariantem

## 1. Threat model
- Zasoby chronione: NIP/REGON/adresy kontrahentów, ceny umów, hasła handlowców
- Aktorzy: handlowiec (RBAC user), kierownik (admin), zewnętrzny atakujący (VPN/intranet)
- Wektory: brute-force loginu, IDOR na /contracts/{id}, XSS w PDF, leak przez export
- Out-of-scope: ataki na MariaDB hosta, fizyczny dostęp do serwera

## 2. AuthN (Authentication)
- JWT HS256, access TTL=60min, refresh TTL=7d, refresh w httpOnly cookie SameSite=Lax
- JWT_SECRET: ≥32B z os.urandom, rotacja co 90d, stary klucz akceptowany 24h (grace)
- Hasła: bcrypt cost=12, min length 12, blacklist top-10k haseł
- Rate-limit: /auth/login 5/min/IP + 10/h/login, lockout 15min po 10 fail
- Change-password: invalidates all sessions (jti blacklist)

## 3. AuthZ (RBAC matrix)
| Zasób | user | admin |
|---|---|---|
| GET /contracts/{id} | own only | all |
| POST /contracts | yes | yes |
| DELETE /users/{id} | no | yes |
| GET /audit_log | no | yes |
| POST /settings/company | no | yes |

## 4. Walidacja inputu (Pydantic v2)
- Każdy endpoint: schema z Field(min_length, max_length, pattern)
- NIP: checksum validator
- File upload: MIME whitelist (image/png,jpeg), max 5MB, hash filename, no SVG

## 5. Output sanitization
- PDF (WeasyPrint+Jinja2): autoescape=True, brak `|safe` na user-input
- Frontend: ZAKAZ `v-html` na user-input (egzekwowane w lint)
- Logi: redact `password`, `token`, `Authorization`

## 6. Sekrety
- Tylko w `.env` (nigdy w spec/!) — w spec używaj `<<PLACEHOLDER>>`
- Rotacja: JWT_SECRET 90d, DB_PASSWORD 180d, GUS_KEY 365d
- Manager: .env + chmod 600 (docelowo Vault/SOPS)

## 7. Headers HTTP (FastAPI middleware)
- CORS: allow_origins=[FRONTEND_URL], credentials=True
- CSP: default-src 'self'; img-src 'self' data:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000 (prod HTTPS only)

## 8. Audit log
- Append-only (brak UPDATE/DELETE z aplikacji)
- Co loguje: login/logout, create/update/delete contracts/contractors/users, export PDF/Excel
- Retencja: 24 miesiące
- Czytelny tylko dla admin (RBAC)

## 9. RODO
- Dane osobowe: tabela `contractors` (NIP, adres, telefon, email)
- Prawo do bycia zapomnianym: soft-delete + anonimizacja po 30d
- Eksport: ZIP z hasłem AES-256, hasło osobnym kanałem, log w audit_log
- Dev/staging: `anonymize_db.py` przed kopią produkcyjnej bazy

## 10. Migracje danych (security view)
- ZAKAZ: kopiowanie plaintext haseł do nowej bazy
- WYMAGANE: stare hasła → force_password_reset=1
- Dump produkcyjny: szyfrowane GPG, retencja 30d, log dostępu

## 11. Vulnerability management
- `pip-audit` + `npm audit` w CI (fail build dla high/critical)
- SBOM generated co release
- Dependency update: kwartalnie + patch ASAP dla CVE >7.0

## 12. Incident response
- Detection: alert na 100+ 401/min, 50+ 403/min
- Containment: `revoke_all_tokens.py` (zmienia JWT_SECRET)
- Notification: PUODO w 72h jeśli wyciek PII
```

---

## 🔄 DETERMINISTYCZNE MIGRACJE DANYCH

### Procedura dla zadań z `migration_impact: yes`

Każde zadanie dotykające schematu/danych musi zawierać sekcję:

```markdown
**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (mirror, nie ALTER)
2. `backend/<feature>/models.py` — SQLAlchemy Column
3. `backend/main.py` startup — `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
4. **Jeśli touch `migrate.py`:** zmodyfikuj parser legacy → nowe pole
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Re-run `python migrate.py` → idempotentne (drugi przebieg = 0 zmian)
   - [ ] Drugi restart backend bez błędu "Duplicate column"
   - [ ] Row count parity: stare vs nowe (lub udokumentowana różnica)
   - [ ] Sample diff: 10 losowych rekordów
```

### Nowy plik: process/migrations.md

```markdown
# Migrations — Polityka Deterministyczna

## Zasady
1. **Schema migrations** (ALTER) zawsze idempotentne: `IF NOT EXISTS`
2. **Data migrations** (migrate.py) zawsze re-runnable bez duplikacji
3. **Sekrety nigdy w spec** — tylko `<<PLACEHOLDER>>`
4. **Hasła nigdy plaintext** — force_password_reset zamiast kopiowania
5. **Każda migracja ma verification gate**

## Testy migracji
- `backend/tests/migration/test_schema_idempotent.py` — double-restart
- `backend/tests/migration/test_data_migration.py` — row counts + integrity
- `scripts/test_migration_from_scratch.sh` — full pipeline (nightly)

## Security
- Stare hasła → losowe hasło tymczasowe + force_password_reset=1
- Eksport PII → ZIP AES-256 + hasło osobnym kanałem
- Dev/staging → `anonymize_db.py` przed kopią produkcyjnej
```

---

## 📖 NOWY PLIK: AGENT_PLAYBOOK.md

```markdown
# AGENT_PLAYBOOK.md — Co czytać przed rozpoczęciem pracy

## Dla każdego agenta

### DB Agent
- **Primary read:** `core/01_database.md`, `process/migrations.md`
- **Może modyfikować:** `models.py`, `main.py` startup, DDL spec
- **Nie tyka:** endpointy, frontend
- **Przed migracją:** `process/migrations.md` + verification gates

### Backend Agent
- **Primary read:** `core/02_backend_api.md`, `core/04_business_logic.md`, `core/25_security.md`
- **Może modyfikować:** `<feature>/{schemas,service,router}.py`, testy unit
- **Nie tyka:** DDL, models (delegacja → DB Agent)
- **Przed endpointem:** Security DoD z backlogu

### Frontend Agent
- **Primary read:** `core/03_frontend_screens.md`, `core/06_navigation.md`, `core/09_design_system.md`
- **Może modyfikować:** `views/`, `components/`, `stores/`, `composables/`, `style.css`
- **Nie tyka:** backend
- **Przed komponentem:** Design system w `core/09_design_system.md`

### QA Agent
- **Primary read:** `process/testing.md`, `backlog/BACKLOG.md` (acceptance criteria)
- **Może modyfikować:** `e2e/tests/`, `backend/tests/unit/`
- **Nie tyka:** kod produkcyjny
- **Przed testami:** `process/testing.md` + edge case matrix

### Tech Lead
- **Primary read:** wszystko
- **Może modyfikować:** tylko `spec/` (governance) i `backlog/BACKLOG.md`
- **Nie tyka:** nic w kodzie
- **Przed planowaniem:** ten playbook + backlog priorytetyzacja

## Routing zadań
- `classification: db-only` → DB Agent
- `classification: backend` → Backend Agent
- `classification: frontend` → Frontend Agent
- `classification: cross-stack` → DB → Backend → Frontend (sekwencyjnie)
- `classification: bugfix` → role z `roles:` field
- `classification: refactor` → ten sam agent który tworzył oryginał
```

---

## 📋 PLAN IMPLEMENTACJI (kolejność)

### Faza 1: Critical Security Fixes (P0) — 1 dzień
1. **Usuń hasła z spec** — `spec/08_MIGRATION_PLAN.md`, `AGENTS.md`, `.windsurf/rules/`
2. **Rotuj `RaoPass2026!`** — jeśli repo było udostępnione
3. **Utwórz `core/25_SECURITY.md`** — minimum viable version
4. **Przepisz migrację haseł** — force_password_reset zamiast plaintext

### Faza 2: Backlog Unification (P0) — 1 dzień
1. **Merge backlogi** — `19_BACKLOG.md` + `21_BACKLOG_CLIENT.md` → `backlog/BACKLOG.md`
2. **Zastosuj nowy format** — YAML front-matter dla wszystkich zadań
3. **Archiwizuj** — `16_TODO.md` → `archive/16_todo_done.md`, `22_IMPLEMENTATION_REPORT.md` → `archive/`
4. **Re-priorytetyzacja** — P0 = PDF bugi klienta, P1 = feature parity

### Faza 3: Folder Reorganization (P1) — 1 dzień
1. **Utwórz strukturę** — `core/`, `process/`, `backlog/`, `archive/`
2. **Przenieś pliki** — `git mv` (zachowaj historię)
3. **Utwórz AGENT_PLAYBOOK.md** — mapowanie ról → pliki do czytania
4. **Utwórz CHANGELOG.md** — konsolidacja 15+16+22
5. **Utwórz process/migrations.md** — polityka deterministyczna
6. **Aktualizuj README.md** — nowa mapa

### Faza 4: Spec Rewrite (P1) — 2-3 dni
1. **Przepisz core/01_database.md** — + ERD, indeksy, tabele-bez-modeli
2. **Podziel core/02_backend_api.md** — na moduły (contracts.md, contractors.md, etc.)
3. **Przepisz core/03_frontend_screens.md** — + mapa view→store→endpoint
4. **Przepisz process/testing.md** — zgodnie z QA recommendations
5. **Aktualizuj wszystkie linki** — `AGENTS.md`, `.windsurf/rules/`

### Faza 5: Verification (P1) — 1 dzień
1. **Smoke test** — `e2e/tests/01-login.spec.ts` PASS
2. **Spec consistency** — `git diff --stat spec/` zgodny z planem
3. **Agent test** — nowy agent (subagent_explore) testuje nową strukturę

---

## 📊 METRYKI SUKCESU

| Metryka | Obecnie | Cel | Jak zmierzyć |
|---------|---------|-----|--------------|
| Czas onboarding agenta | 30-60 min | 15-20 min | Test z nowym agentem |
| Liczba plików spec/ | 24 | 15 (core) + 4 (process) + 1 (backlog) | `find spec/ -name "*.md" \| wc -l` |
| Zombie-spec count | 4+ (12,13,14,18,22,24) | 0 | Manual audit |
| Security coverage | 0% | 100% (threat model + RBAC) | Istnienie 25_SECURITY.md |
| Backlog conflicts | 2 (19 vs 21) | 0 (jeden backlog) | Manual review |
| Migracja determinizm | ad-hoc | 100% (verification gates) | Test migration_from_scratch.sh |

---

## ✅ ACCEPTANCE CRITERIA DLA TEJ REORGANIZACJI

- [ ] Hasła usunięte ze spec (git diff clean)
- [ ] `core/25_SECURITY.md` utworzony z minimum viable content
- [ ] `backlog/BACKLOG.md` zawiera wszystkie zadania z 19+21 w nowym formacie
- [ ] Folder structure utworzona: core/, process/, backlog/, archive/
- [ ] `AGENT_PLAYBOOK.md` utworzony z mapą ról
- [ ] `process/migrations.md` utworzony z verification gates
- [ ] `CHANGELOG.md` utworzony (konsolidacja 15+16+22)
- [ ] Wszystkie linki w `AGENTS.md` i `.windsurf/rules/` zaktualizowane
- [ ] Smoke test `e2e/tests/01-login.spec.ts` PASS
- [ ] Nowy agent (subagent_explore) potwierdza czytelność nowej struktury

---

## 🚨 RYZYKA I MITIGACJA

| Ryzyko | Prawdopodobieństwo | Impact | Mitigacja |
|---------|-------------------|--------|-----------|
| Linki w AGENTS.md się zepsują | Średnie | Wysokie | Grep wszystkich referencji przed reorganizacją |
| Agenci vendor-specific (Cascade) mają hard-coded paths | Wysokie | Średnie | Zostawić symlinki na 1 sprint przejściowy |
| Merge backlogów ujawni konflikty priorytetów | Średnie | Średnie | Tech Lead arbitruje, klient akceptuje przed merge |
| Security spec zostanie zignorowany przez agentów | Średnie | Wysokie | Security DoD w każdym zadaniu backlogu |

---

## 📝 REKOMENDACJA KOŃCOWA

**REKOMENDACJA:** **WDRÓŻ REORGANIZACJĘ W 5 DNI** (Faza 1-3 krytyczne, Faza 4-5 można rozłożyć)

**Kolejność:**
1. **Dzień 1:** Security fixes (P0) — usuń hasła, utwórz 25_SECURITY.md
2. **Dzień 2:** Backlog unification (P0) — merge 19+21, nowy format
3. **Dzień 3:** Folder reorganization (P1) — struktura + AGENT_PLAYBOOK.md
4. **Dni 4-5:** Spec rewrite (P1) — przepisz core/01-03, process/testing
5. **Dzień 6:** Verification (P1) — smoke test + agent test

**Bez tej reorganizacji każdy kolejny feature będzie miał 30% overhead na "co tak naprawdę robić".**