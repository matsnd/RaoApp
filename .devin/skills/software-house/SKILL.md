---
name: software-house
description: Autonomiczny orkiestrator RAO v2.2. Trzy tryby - fast (domyslny, interaktywny), checkpoint (plan-approval + bramki po fazach), full-auto (wsadowy, zero pytan). Glowny agent = Tech Lead, spawnuje subagent_general z rolami z .devin/roles/.
triggers:
  - user
  - model
arguments:
  - name: checkpoint
    description: "Plan-approval na starcie + stop po commicie kazdej fazy. Dla zadan L, gdy user jest w poblizu."
    type: boolean
    default: false
  - name: full-auto
    description: "Zero pytan, pelny rygor maszynowy, wsadowo z backlogu. Wolny celowo."
    type: boolean
    default: false
---

# Software House v2.2 — Orkiestrator RAO

Jestes **Tech Leadem-orkiestratorem**. Bez flag dzialasz w trybie **FAST**.

## ⚠️ FUNDAMENT RUNTIME (zweryfikowany, nie zgaduj)

**Custom profile AGENT.md NIE dostaja MCP** (bug CLI, runtime 2026-07-05, CLI 2026.8.18).
KAZDY spawn = `subagent_general` (pelny MCP) + rola wklejona z `.devin/roles/<rola>.md` + kontekst z `.devin/context/rao-stack.md`, wg `.devin/templates/spawn-prompt.md`. Subagenty sa STATELESS — pelny kontekst w prompcie, zawsze. NIE spawnuj custom profili ani `subagent_explore` do zadan MCP.
**Re-test po kazdym `devin update`:** custom profil + `mcp__mariadb__query_database` → dziala = bug naprawiony → zglos userowi.

## TRYBY — kto jest bramka jakosci

| | **FAST** (domyslny) | **CHECKPOINT** | **FULL-AUTO** |
|---|---|---|---|
| Bramka | user na biezaco | user na granicach faz | maszyna |
| Phase 0 | ZERO spawnow — wlasna analiza 2 min, plan pokazany, JEDZIESZ dalej nie czekajac | plan pokazany, **CZEKASZ na OK** | 4 spawny analityczne (L) |
| Implementacja M | **SAM, bez spawnu** (rola = Twoja checklista) | spawn wg faz | spawn wg faz |
| Review | TYLKO pliki wysokiego ryzyka (lista w review-protocol) | kazda faza | kazda faza |
| Po fazie | pokaz `git diff --stat` + 5 linii podsumowania, **lec dalej** | commit → **STOP, czekaj na "dalej"/korekte** | commit → dalej |
| Self-healing | 1 proba → pytanie do usera (diagnoza + opcje A/B) | 2 proby/faze → pytanie | 3 proby/faze, 2 strategie, budzet 12, revert per faza |
| Evidence | pytest / vue-tsc / build (tanie) | pelne | pelne |
| Vision | tylko gdy zadanie jawnie wizualne | wg mapy decyzyjnej | wg mapy decyzyjnej |
| Spec-sync | **RAZ na koncu zadania** (jeden przebieg po git diff calosci) | per faza | per faza |
| Audyty sec/perf | tylko gdy zadanie dotyka auth/danych/query | fazy L | fazy L |
| Przeznaczenie | codzienna praca przy terminalu | duze L "w poblizu" | wsad z backlogu (status `triaged`, ostre DoD), odpalasz i odchodzisz |

FULL-AUTO nie zadaje pytan; hard stopy tylko: security VETO i DROP/TRUNCATE (raport, nie pytanie).

## Krok 1 — Pre-flight (kazdy tryb, rownolegle w jednym bloku)

`spec/AGENT_PLAYBOOK.md` · `spec/00_INDEX.md` · relevantny spec/core · `spec/backlog/BACKLOG.md` · `git status` + `git log --oneline -5` · MCP zamiast grep: `codebase-memory.search_graph`, `depwire.impact_analysis`, `mariadb DESCRIBE`.
Utworz `.devin/_session_context.md` z szablonu (TY = jedyny writer). Wpisz tryb.

## Krok 2 — Routing S/M/L

| Rozmiar | Kryteria | FAST | CHECKPOINT/FULL-AUTO |
|---|---|---|---|
| **S** | typo, label, config, bugfix z jasnym root cause, 1 plik | sam → smoke → commit | jak FAST |
| **M** | feature jednowarstwowy, 2-5 plikow | sam wg roli-checklisty → smoke → commit (+review gdy high-risk) | implement→review (1 rola) → QA → commit per faza |
| **L** | cross-stack, refactor, migracja danych | fazy ze spawnami, ale rygor FAST (review tylko high-risk, spec-sync na koncu) | pelny lancuch |

Watpliwosc S/M → M. Dotyka DB **i** frontendu → L.

## Krok 3 — Plan (zastepuje Phase 0 w FAST/CHECKPOINT)

Wlasna analiza (bez spawnow): `depwire.impact_analysis` na dotykanych symbolach, `search_graph` za duplikacja, DESCRIBE dotykanych tabel. Wypisz: fazy, pliki, ryzyka, DoD (3-6 punktow weryfikowalnych).
- FAST: pokaz plan i zacznij natychmiast — user skoryguje w locie, jesli chce.
- CHECKPOINT: pokaz plan i CZEKAJ na akceptacje/korekte.
- FULL-AUTO (L): Phase 0 = spawny product-owner + tech-lead + (security-auditor gdy auth/dane) + qa-engineer, rownolegle, background.

## Krok 4 — Implementacja

Fazy: DB → Backend → Frontend → [Polish wizualny] → [Audyt sec+perf] → QA → [Final review L]. Pomijaj fazy nie dotyczace zadania. Max 4 spawny rownolegle; zalezne foreground, niezalezne background.
Cykl implement→review wg `.devin/workflows/review-protocol.md` — **stosowany wg tabeli trybow** (FAST: review tylko high-risk).
FAST po kazdej fazie: `git diff --stat` + max 5 linii co/dlaczego → commit → następna faza bez czekania.
CHECKPOINT po commicie fazy: STOP — "Faza X zacommitowana (<hash>). Kontynuowac / korekta?"

## Krok 5 — Weryfikacja przed commitem fazy (kazdy tryb)

1. **Scope check** (tylko gdy byl spawn): `git diff --name-only` vs Scope roli → violation = checkout plikow spoza + respawn/popraw.
2. **Evidence:** FAST = output pytest/vue-tsc/build wklejony w podsumowanie; CHECKPOINT/FULL-AUTO = pliki w `.devin/_evidence/<rola>/`, brak = odrzucony handoff.
3. **Spec:** CHECKPOINT/FULL-AUTO per faza wg mapy wlasnosci; FAST — pomin (Krok 8 zrobi calosc).

## Krok 6 — Commit per faza (kazdy tryb, bez wyjatkow)

NIGDY `git add .` — tylko jawne sciezki z `git diff --name-only` fazy. Przed commitem: `gitleaks protect --staged --no-banner` (fallback: `git diff --staged | grep -nE "sk-ant-|sk-or-v1-|ghp_[A-Za-z0-9]{20,}|BSA[A-Za-z0-9]{10,}|AKIA[A-Z0-9]{16}"` → hit = BLOKUJ). Komunikat `feat|fix(scope): faza X — opis`. Rollback = `git revert <hash-fazy>`.

## Krok 7 — Self-healing (limit wg trybu, patrz tabela)

Zawsze: root cause, nie symptom. FAST: 1 proba → pytanie z diagnoza i opcjami A/B (pytanie jest TANIE, uzywaj go). CHECKPOINT: 2 proby → pytanie. FULL-AUTO: 3 proby → revert fazy → strategia alternatywna (max 2) → budzet globalny 12 → final report z blokerem.

## Krok 8 — Zamkniecie zadania

1. FAST: **spec-sync calosci teraz** — `git diff <start>..HEAD --name-only`, zaktualizuj pliki spec wg mapy wlasnosci jednym przebiegiem, osobny commit `docs(spec): sync`.
2. Backlog: YAML flow `triaged → in_progress → dev-verified → team-verified → user-verified → client-approved`. Agent ustawia MAX `team-verified`; `user-verified`/`client-approved` = CZLOWIEK, nigdy agent. Decyzje → `DECISION_LOG.md`. Sweep done→archiwum gdy BACKLOG > 400 linii.
3. Wiedza: wzorce → `spec/technical/patterns/`, skrypty → `scripts/`, indeks `TECHNICAL_SOLUTIONS.md`.
4. Metryki → `.devin/_metrics.csv`: `data;task_id;rozmiar;tryb;fazy;spawny;review_findings;qa_escapes;proby_naprawcze;wynik`.
5. Raport: commity (hashe), pliki, evidence, porty.

## Mapa wlasnosci spec (kanoniczna)

| Zmiana | Plik | Wlasciciel |
|---|---|---|
| schema/migracje | `core/01_database.md` + `08_migration_plan.md` | db-architect |
| endpointy/schemas | `core/02_backend_api.md` | backend-dev |
| algorytmy/kalkulacje/stawki | `core/04_business_logic.md` | backend-dev |
| integracje GUS/PDF/Fakturownia | `core/07_integrations.md` | backend-dev |
| wydruki/KPI | `core/11_reports_stats.md` | backend-dev |
| widoki/routing | `core/03_frontend_screens.md` | frontend-dev |
| design system | `core/09_design_reference.md` | design-reviewer |
| auth/RBAC | `core/25_security.md` | security-auditor |
| testy | `core/17_testing_plan.md` + `process/TEST_MATRIX.md` | qa-engineer |

**FROZEN (nie aktualizuj):** `core/12/13/14/18_*`, `spec/AUDYT_*`, `spec/archive/**`, `spec/backlog/archiwum/**`.

## Vision — mapa decyzyjna (jedyna kopia)

Programatycznie (darmowe): pola/tekst/routing/logika/endpoint/schema → grep/read/curl/DESCRIBE. Vision (~$0.01-0.03): kolory, layout, spacing, typografia, animacje, breakpointy. Konkretne pytanie, 1 screenshot per widok (frontend-dev robi → `_evidence/frontend-dev/`, reszta reuse przez `analyze_screenshot`). OK→dalej, MINOR→log, MAJOR→fix+re-vision (max 2). FAST: vision tylko gdy zadanie jawnie wizualne.

## Hierarchia konfliktow (wyzszy wygrywa)

`1. Security (veto, ostateczne) > 2. Data > 3. Correctness (QA) > 4. UX > 5. Performance > 6. UI > 7. Motion > 8. Style`. CO buduje product-owner, JAK — Ty. Konflikty loguj w `_session_context.md`.

## Reguly nienaruszalne (kazdy tryb)

1. Spawn = `subagent_general` + rola z `roles/` 2. Pelny kontekst w prompcie (stateless) 3. NIGDY `git add .` 4. NIGDY commit bez secret-scanu 5. Zero kill-port/pkill/taskkill — port zajety → nastepny wolny (8001, 5174...) 6. DROP/TRUNCATE = hard stop 7. Smoke `e2e/tests/01-login.spec.ts` zielony po zmianach 8. Scope violation = checkout + poprawka 9. `_session_context.md` pisze tylko orkiestrator 10. Sekrety wylacznie w `config.local.json` (gitignored) 11. Backlog max `team-verified`.
