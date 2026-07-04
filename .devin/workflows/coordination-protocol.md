---
description: Protokół koordynacji 11 ról RAO — shared context, handoff, review chain matrix, conflict resolution, evidence folder, vision deduplikacja
---

# 🤝 Coordination Protocol — RAO Software House

> **Single source of truth dla koordynacji między agentami.**
> Linkowany z: `AGENTS.md` (root), `.devin/skills/software-house/SKILL.md`, każdego `.devin/agents/*/AGENT.md`.
>
> **Cel:** Subagenty są stateless — ten protokół definiuje jak przekazują sobie kontekst,
> kto na kogo czeka, jak rozstrzygać konflikty i gdzie persistować dowody.

---

## 1. Shared Context File

### 1.1 Lokalizacja

```
.devin/_session_context.md
```

Plik tworzony przez **parent agenta (Tech Leada)** na starcie zadania, aktualizowany po każdej fazie.
Subagenty **obowiązkowo czytają** ten plik jako pierwszy krok — zanim zaczną pracę.

### 1.2 Struktura

```markdown
# Session Context — <task-id lub krótki opis>

> Utworzono: <ISO datetime> | Parent: Tech Lead | Status: in_progress

## Zadanie
<pełny opis zadania od użytkownika>

## Decyzja architektoniczna (Tech Lead)
- Klasyfikacja: <DB-only | Backend-only | Frontend-only | Cross-stack | Bugfix | Refactor>
- Rozmiar: <XS | S | M | L>
- Priorytet: <P0 | P1 | P2>

## Definition of Done (Product Owner)
- [ ] <kryterium 1>
- [ ] <kryterium 2>

## Plan podziału pracy
1. db-architect: <zadanie> — status: ⬜/⏳/✅/❌
2. backend-dev: <zadanie> — status: ⬜/⏳/✅/❌
3. frontend-dev: <zadanie> — status: ⬜/⏳/✅/❌
4. ...

## Handoff log (chronologicznie)

### [db-architect] ✅ 2026-07-04 14:23
**CO ZROBIŁEM:** ADD COLUMN delivery_address VARCHAR(255) NULL on contracts
**GOTOWE DLA:** backend-dev (model + DDL gotowe, schema w spec/core/01_database.md)
**EVIDENCE:** .devin/_evidence/db-architect/contracts_describe_after.txt
**BLOCKERY:** brak

### [backend-dev] ⏳ 2026-07-04 14:45
**CO ROBIĘ:** dodaję delivery_address do ContractOut schema + endpoint
**GOTOWE DLA:** (jeszcze nie) frontend-dev po zakończeniu
**EVIDENCE:** (pending)
**BLOCKERY:** brak

## Open issues / conflicts
- (puste jeśli brak)

## Evidence index
- .devin/_evidence/db-architect/contracts_describe_after.txt
- .devin/_evidence/backend-dev/curl_contracts_201.json
- .devin/_evidence/frontend-dev/screenshot_contracts_view.png
- .devin/_evidence/qa-engineer/playwright_01_login_pass.txt
```

### 1.3 Zasady aktualizacji

- **Tylko parent (Tech Lead) tworzy plik** na starcie zadania
- **Każdy subagent dopisuje swoją sekcję do "Handoff log"** po zakończeniu pracy (przez `edit`)
- **Statusy w "Plan podziału pracy"** aktualizuje parent po każdej fazie
- **Open issues / conflicts** — każdy subagent może dopisać konflikt który znalazł
- Plik jest **git-ignored** (`.devin/_session_context.md` w `.gitignore`) — artefakt sesji, nie kod

### 1.4 Co subagent robi z tym plikiem

1. **Na starcie:** `read .devin/_session_context.md` → zrozum zadanie + kontekst poprzedników
2. **W trakcie:** może `read` ponownie żeby sprawdzić czy poprzednik nie dodał czegoś
3. **Na koniec:** `edit` — dopisz swoją sekcję do "Handoff log" + zaktualizuj status w planie

---

## 2. Handoff Protocol

### 2.1 Standardowy format końcowego outputu

Każdy subagent kończy pracę sekcją w formacie:

```
## HANDOFF

**CO ZROBIŁEM:**
<1-3 zdania, konkretne pliki zmienione>

**GOTOWE DLA:**
<lista ról + co dokładnie mogą użyć>
- frontend-dev: endpoint POST /rao/api/contracts (201 ContractOut), pole delivery_address w schema
- qa-engineer: testy do napisania dla endpointu wyżej

**BLOCKERY:**
<lista lub "brak">

**EVIDENCE:**
<ścieżki do .devin/_evidence/<role>/ lub "brak">

**SPEC UPDATE:**
<które pliki spec/ zostały zaktualizowane lub "brak">
```

### 2.2 Handoff matrix — kto przekazuje komu

| Od | Do | Co przekazuje |
|----|-----|---------------|
| db-architect | backend-dev | Schema DDL, model SQLAlchemy, kolumny, FK |
| backend-dev | frontend-dev | Endpoint URL, method, request/response schema, status codes |
| backend-dev | qa-engineer | Endpoint + edge cases do testowania |
| frontend-dev | qa-engineer | Widoki + data-testid selectors + flow |
| frontend-dev | ui-designer | Zmienione komponenty .vue do review design system |
| frontend-dev | ux-designer | Zmienione flowy/widoki do review UX |
| frontend-dev | motion-designer | Nowe komponenty do dodania animacji |
| qa-engineer | backend-dev / frontend-dev | BUGS z owner + steps to repro |
| security-auditor | backend-dev / frontend-dev | Luki z fix + owner |
| performance-eng | backend-dev / db-architect / frontend-dev | Optymalizacje z owner |
| ui-designer / ux-designer / motion-designer | frontend-dev | Sugestie do implementacji (CSS snippety, teksty) |
| product-owner | tech-lead | Rekomendacja BUDUJ/ODŁÓŻ/UPROSC + DoD |
| tech-lead | wszyscy | Plan podziału pracy + side effects |

### 2.3 Anti-patterns handoffu

- ❌ "Zrobione" bez konkretów — następca nie wie co dokładnie
- ❌ Brak ścieżek plików — następca musi grepować
- ❌ Brak schema endpointu — frontend-dev musi czytać router.py żeby zgadnąć URL
- ❌ Brak evidence — final review nie może zweryfikować
- ❌ Dopisywanie do shared context bez sekcji HANDOFF — chaos

---

## 3. Review Chain Matrix — kto czeka na kogo

### 3.1 Graf zależności (DAG)

```
Phase 0 — ANALYSIS (równolegle, background)
┌─────────────────────────────────────────────────┐
│ product-owner  tech-lead  qa-engineer  security │
│ (czy ma sens)  (arch)     (edge cases)  (auth?) │
└─────────────────────────────────────────────────┘
                    │
                    ▼
Phase 1 — DB LAYER (foreground, sekwencyjnie)
            db-architect
                    │
                    ▼
Phase 2 — BACKEND (foreground, sekwencyjnie po DB)
            backend-dev
                    │
                    ▼
Phase 3 — FRONTEND (foreground, sekwencyjnie po Backend)
            frontend-dev
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
Phase 4 — POLISH (równolegle, background po Frontend)
   ui-designer  ux-designer  motion-designer
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
Phase 5 — AUDIT (równolegle, background po Backend+Frontend)
   security-auditor  performance-eng
        │               │
        └───────────────┘
                    │
                    ▼
Phase 6 — QA (foreground, po wszystkich implementacjach)
            qa-engineer
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
Phase 7 — FINAL REVIEW (równolegle, background)
   tech-lead  product-owner
        │           │
        └───────────┘
                    │
                    ▼
              COMMIT (Tech Lead)
```

### 3.2 Reguły zależności

| Subagent | Czeka na | Blokuje |
|----------|----------|---------|
| product-owner | (nikogo — start) | tech-lead (decyzja CO) |
| tech-lead | product-owner (rekomendacja) | db-architect, backend-dev, frontend-dev (plan) |
| qa-engineer (analysis) | (nikogo — start) | tech-lead (edge cases input) |
| security-auditor (analysis) | (nikogo — start) | tech-lead (auth scope) |
| db-architect | tech-lead (plan) | backend-dev (model + DDL) |
| backend-dev | db-architect (schema) | frontend-dev (API), qa-engineer (endpoint) |
| frontend-dev | backend-dev (API contract) | ui-designer, ux-designer, motion-designer, qa-engineer |
| ui-designer | frontend-dev (komponenty) | (nikogo — review only) |
| ux-designer | frontend-dev (flow) | (nikogo — review only) |
| motion-designer | frontend-dev (komponenty) | (nikogo — review only) |
| security-auditor (audit) | backend-dev + frontend-dev | qa-engineer (luki = test cases) |
| performance-eng | backend-dev + frontend-dev | qa-engineer (slow = test) |
| qa-engineer (test) | backend-dev + frontend-dev + security + performance | tech-lead (final review) |
| tech-lead (final) | qa-engineer (pass) | commit |
| product-owner (final) | tech-lead (final) | (akceptacja zadania) |

### 3.3 Kiedy pominąć fazę

- **DB-only task** → pomiń Phase 3 (Frontend), Phase 4 (Polish)
- **Backend-only task** → pomiń Phase 3, 4
- **Frontend-only task** → pomiń Phase 1 (DB), Phase 2 może być pominięte jeśli API istnieje
- **Bugfix** → pomiń Phase 0 (analysis) jeśli trywialny, zacznij od QA repro
- **Refactor** → zachowaj wszystkie fazy, ale Phase 4 (Polish) opcjonalne

### 3.4 Równoległość vs sekwencyjność

- **Foreground (czekaj na wynik):** kroki zależne — DB → Backend → Frontend
- **Background (nie czekaj):** kroki niezależne — analiza, polish, audit, final review
- **Max 4 subagenty równolegle** (limit kontekstu parenta)

---

## 4. Conflict Resolution

### 4.1 Hierarchia priorytetów

Gdy dwa subagenty mają sprzeczne wymagania, wyższy priorytet wygrywa:

```
1. Security (P0 — blokuje produkcję)
2. Data integrity (DB-architect — brak utraty danych)
3. Correctness (QA — testy zielone, happy path działa)
4. UX (zrozumiałość flow, feedback)
5. Performance (p95 < target)
6. UI consistency (design system)
7. Motion (polish, animacje)
8. Code style (preferecje estetyczne)
```

### 4.2 Decision authority — kto decyduje CO vs JAK

| Pytanie | Decyduje |
|---------|----------|
| **CO** budujemy (scope, priorytet, czy w ogóle) | Product Owner |
| **JAK** architektonicznie (moduł, wzorzec, stack) | Tech Lead |
| **JAK** w backendzie (endpoint shape, schema) | Backend Dev (z Tech Lead review) |
| **JAK** w DB (kolumna, indeks, FK) | DB Architect |
| **JAK** w frontendzie (komponent, store) | Frontend Dev |
| **JAK** wygląda (kolory, spacing) | UI Designer |
| **JAK** się czuje (flow, kliki) | UX Designer |
| **JAK** się rusza (animacje) | Motion Designer |
| **CZY** jest bezpieczne | Security Auditor (veto) |
| **CZY** jest wystarczająco szybkie | Performance Engineer (rekomendacja, nie veto) |
| **CZY** działa (testy) | QA Engineer (veto do merge) |

### 4.3 Typowe konflikty i rozstrzygnięcia

| Konflikt | Rozstrzygnięcie |
|----------|-----------------|
| UX chce animację 300ms, Performance chce <100ms | Performance wygrywa jeśli p95 > target; inaczej UX |
| Security blokuje endpoint, PO naciska na deadline | Security veto — blokuje. PO może odłożyć feature |
| UI chce niestandardowy kolor, UX chce hierarchy | UX wygrywa (hierarchy > consistency jeśli P0) |
| QA znalazł bug, PO mówi "to edge case" | QA wygrywa jeśli bug dotyka happy path lub data integrity |
| Backend chce N+1 fix, Performance rekomenduje | Backend implementuje, Performance weryfikuje |
| DB-architect chce DROP COLUMN, PO chce zachować | DB-architect wymaga zgody usera (reguła z AGENTS.md) |

### 4.4 Escalation path

1. Subagent zgłasza konflikt w `Open issues / conflicts` w shared context
2. Parent (Tech Lead) czyta, rozstrzyga według hierarchii (4.1)
3. Jeśli konflikt dotyka **CO** (scope) → escalation do Product Ownera
4. Jeśli konflikt dotyka **security/data** → escalation do usera (NIGDY nie omijaj)
5. Rozstrzygnięcie zapisane w shared context jako decyzja

---

## 5. Evidence Folder

### 5.1 Lokalizacja

```
.devin/_evidence/
├── db-architect/
│   ├── contracts_describe_after.txt
│   └── restart_idempotent_check.txt
├── backend-dev/
│   ├── curl_contracts_201.json
│   └── pytest_unit_pass.txt
├── frontend-dev/
│   ├── vue_tsc_clean.txt
│   └── screenshot_contracts_view.png
├── ui-designer/
│   └── vision_analysis_contracts.md
├── ux-designer/
│   └── flow_click_count.md
├── motion-designer/
│   └── vision_animation_review.md
├── security-auditor/
│   └── idor_check_contracts.md
├── performance-eng/
│   ├── explain_contracts_list.txt
│   └── bundle_size.txt
├── qa-engineer/
│   ├── playwright_01_login_pass.txt
│   └── pytest_full_pass.txt
├── product-owner/
│   └── feature_parity_check.md
└── tech-lead/
    └── architecture_review.md
```

### 5.2 Zasady

- **Każdy subagent ZAPISUJE dowody** do `.devin/_evidence/<role>/`
- Format dowodu: plik tekstowy z outputem (curl, pytest, vue-tsc, DESCRIBE, EXPLAIN)
- Screenshoty: plik PNG + opcjonalnie `.md` z analizą vision
- **Final review (Tech Lead + QA) weryfikuje evidence** przed commitem
- Folder jest **git-ignored** (artefakty sesji) — dodaj `.devin/_evidence/` do `.gitignore`
- **Brak evidence = niedopełniony obowiązek** — Tech Lead może odrzucić handoff

### 5.3 Co jest evidence a co nie

| Typ | Evidence? |
|-----|-----------|
| `curl` output endpointu | ✅ Tak — zapisz do `.txt` |
| `pytest` output (pass/fail) | ✅ Tak |
| `vue-tsc --noEmit` output | ✅ Tak |
| `npm run build` output | ✅ Tak (ostatnie 20 linii) |
| `DESCRIBE` po migracji | ✅ Tak |
| `EXPLAIN` zapytania | ✅ Tak |
| Playwright screenshot | ✅ Tak — `.png` |
| Vision analysis (rao-vision) | ✅ Tak — `.md` z verdict |
| `git diff` | ❌ Nie — w commit history |
| `read` pliku | ❌ Nie — kod jest w repo |
| Subagent raport tekstowy | ❌ Nie — to nie evidence, to handoff |

---

## 6. Vision Deduplikacja

### 6.1 Problem

5 ról używa `rao-vision` (frontend-dev, ui-designer, ux-designer, motion-designer, product-owner).
Każdy robi własny screenshot = 5× koszt, 5× czas, 5× zmienne wyniki.

### 6.2 Rozwiązanie — 1 screenshot, wiele analiz

**Frontend-dev** (jako pierwszy po implementacji) robi **1 screenshot** przez `playwright.browser_take_screenshot` i zapisuje do:

```
.devin/_evidence/frontend-dev/screenshot_<view>.png
```

Następnie **ui-designer, ux-designer, motion-designer, product-owner** używają:

```python
mcp_call_tool(
    server_name="rao-vision",
    tool_name="analyze_screenshot",
    arguments={
        "image_path": ".devin/_evidence/frontend-dev/screenshot_<view>.png",
        "question": "<pytanie specyficzne dla roli>"
    }
)
```

### 6.3 Kiedy nowy screenshot

- ✅ Reuse screenshotu gdy: ten sam widok, ta sama zmiana, analiza z innej perspektywy
- ❌ Nowy screenshot gdy: inny widok, inny stan (loading vs loaded), inna akcja
- Reguła: **max 1 screenshot per widok per faza** — jeśli potrzebny inny stan, uzasadnij w evidence

### 6.4 Pytania specyficzne per rola (ten sam screenshot)

| Rola | Pytanie do tego samego screenshotu |
|------|-----------------------------------|
| ui-designer | "Czy spacing/kolory/border-radius zgodne z design system Toolsmart?" |
| ux-designer | "Czy hierarchy wizualna prowadzi usera do głównej akcji?" |
| motion-designer | "Czy hover/active states są widoczne? Czy loading state jest odpowiedni?" |
| product-owner | "Czy feature jest widoczny? Czy user go znajdzie w <N> klikach?" |

### 6.5 Workflow vision dedup

```
1. frontend-dev implementuje zmianę
2. frontend-dev: playwright.browser_navigate → browser_take_screenshot
   → zapisz do .devin/_evidence/frontend-dev/screenshot_<view>.png
3. frontend-dev: rao-vision.analyze_screenshot z własnym pytaniem
   → zapisz verdict do .devin/_evidence/frontend-dev/vision_<view>.md
4. frontend-dev: HANDOFF z path do screenshotu w sekcji EVIDENCE
5. ui-designer (background): rao-vision.analyze_screenshot na tym samym pliku
   → zapisz do .devin/_evidence/ui-designer/vision_<view>.md
6. ux-designer, motion-designer, product-owner — analogicznie
```

### 6.6 Oszczędności

- **Bez dedup:** 5 screenshotów × ~$0.02 = $0.10 per widok + 5× czas (~50s)
- **Z dedup:** 1 screenshot × ~$0.02 + 4× analyze_screenshot (~$0.01 each) = $0.06 + ~30s
- **Nemotron free:** koszt $0 i tak — ale czas nadal oszczędzony

---

## 7. Shared Todo List — koordynacja postępu

### 7.1 Problem

`todo_write` jest per-agent. Subagenty nie widzą postępu innych.

### 7.2 Rozwiązanie

Parent (Tech Lead) utrzymuje **jedno źródło prawdy** w sekcji "Plan podziału pracy" w `.devin/_session_context.md`. Każdy subagent po zakończeniu aktualizuje swój status przez `edit`.

**Nie duplikuj todo_write w subagentach** — one i tak są stateless. Jeden shared plan w context file wystarczy.

---

## 8. Quick Reference — dla każdego subagenta

### Na starcie (KAŻDY subagent):

1. `read .devin/_session_context.md` — zrozum zadanie + kontekst poprzedników
2. `read .devin/workflows/coordination-protocol.md` — jeśli nie znasz protokołu
3. Wykonaj swoje zadanie (zgodnie ze swoim AGENT.md)
4. Zapisz evidence do `.devin/_evidence/<twoja-rola>/`
5. Na koniec: `edit .devin/_session_context.md` — dopisz sekcję HANDOFF do "Handoff log"

### Na koniec (KAŻDY subagent):

```markdown
### [<twoja-rola>] ✅ <timestamp>
**CO ZROBIŁEM:** <konkret>
**GOTOWE DLA:** <role + co>
**BLOCKERY:** <lista lub "brak">
**EVIDENCE:** <ścieżki lub "brak">
**SPEC UPDATE:** <pliki spec/ lub "brak">
```

### Dla parenta (Tech Lead):

1. Stwórz `.devin/_session_context.md` na starcie
2. Deleguj zgodnie z Review Chain Matrix (sekcja 3)
3. Rozstrzygaj konflikty według Conflict Resolution (sekcja 4)
4. Po każdej fazie aktualizuj statusy w planie
5. Przed commitem: zweryfikuj evidence w `.devin/_evidence/`
6. Commit + usuń `_session_context.md` i `_evidence/` (lub zostaw do post-mortem)

---

## 9. Anti-patterns koordynacji

- ❌ Subagent zaczyna pracę bez czytania `_session_context.md`
- ❌ Subagent kończy bez sekcji HANDOFF
- ❌ Parent deleguje równolegle kroki zależne (DB + Backend jednocześnie)
- ❌ Parent nie rozstrzyga konfliktu — subagenty się kłócą w context file
- ❌ Brak evidence — "działa bo mówię że działa"
- ❌ 5 screenshotów tego samego widoku zamiast 1 + 4 analizy
- ❌ Subagent modyfikuje kod poza swoim scope (np. backend-dev edytuje frontend)
- ❌ Parent pomija fazę QA żeby "oszczędzić czas"
- ❌ Subagent nie aktualizuje spec/ po zmianie funkcjonalnej

---

**Ostatnia aktualizacja:** 2026-07-04
**Właściciel:** Tech Lead (RAO)
**Powiązane:** `AGENTS.md`, `.devin/skills/software-house/SKILL.md`, `.devin/agents/*/AGENT.md`
