# RAO Agents — Dual-Team (Pair Programming)

## Overview

Każda rola ma **parę**: GLM-5.2-High + SWE 1.7. Para pracuje razem (pair programming) — rozmawiają, implementują, cross-review. Nie ma podziału na "senior planuje, junior pisze". Obaj są kierowcami.

## 🤝 Koordynacja między agentami

**📖 Pełny protokół:** `.devin/workflows/coordination-protocol.md` — Pair Programming Loop (dyskutuj → implementuj → cross-review → handoff)

**📖 Skill:** `.devin/skills/software-house/SKILL.md` — sekcja "Tok porozumiewania — Pair Programming"

Każdy `.devin/agents/*/AGENT.md` ma sekcję "Handoff & Shared Context" z rolą-specyficznymi instrukcjami (GOTOWE DLA, evidence types).

## Pary agentów (11 ról × 2 modele = 22 profile)

| Rola | GLM-5.2-High | SWE 1.7 | Wspólna praca |
|------|-------------|---------|---------------|
| Tech Lead | `tech-lead` | `tech-lead-swe` | Architektura, plan, final review |
| DB Architect | `db-architect` | `db-architect-swe` | Migracje, schema, indeksy |
| Backend Dev | `backend-dev` | `backend-dev-swe` | Endpointy, service, testy |
| Frontend Dev | `frontend-dev` | `frontend-dev-swe` | Komponenty, stores, widoki |
| QA Engineer | `qa-engineer` | `qa-engineer-swe` | Testy, edge cases, bug repro |
| Product Owner | `product-owner` | `product-owner-swe` | ROI, priorytet, DoD |
| UX Designer | `ux-designer` | `ux-designer-swe` | Flow, feedback, edge cases UX |
| UI Designer | `ui-designer` | `ui-designer-swe` | Design system, spacing, kolory |
| Motion Designer | `motion-designer` | `motion-designer-swe` | Animacje, transitions, polish |
| Security Auditor | `security-auditor` | `security-auditor-swe` | Auth, IDOR, walidacja |
| Performance Eng | `performance-eng` | `performance-eng-swe` | N+1, indeksy, bundle |

## Pair Programming — jak to działa

```
1. DYSKUTUJA    — obaj dostają ten sam kontekst, wymieniają pomysły
2. IMPLEMENTUJA — jeden pisze, drugi patrzy; potem zamiana
3. CROSS-REVIEW — obaj reviewują kod drugiego
4. ZGODA        → HANDOFF do następnej pary
```

GLM widzi szerzej (architektura, side effects), SWE łapie detale (import, typo, edge case). Dwie perspektywy = mniej bugów przed QA.

## Agents z dostępem do vision (rao-vision MCP)

> **⚠️ ZWERYFIKOWANE 2026-07-05 (CLI 2026.8.18) testem runtime:**
> Custom subagenty (`AGENT.md`) **NIE dostają narzędzi MCP** w runtime — dostają tylko 5 narzędzi filesystem/shell (`read`, `grep`, `edit`, `exec`, `find_file_by_name`), mimo poprawnych `mcp__serwer__*` w `allowed-tools` i `permissions.allow`. To jest **bug CLI**, nie błąd konfiguracji (configi parsują się OK, `subagent_general` z tymi samymi serwerami działa).
>
> **Workaround (testowany, działa):** używaj wbudowanego profilu `subagent_general` z instrukcją roli w prompcie. `subagent_general` ma pełny dostęp do MCP (11 serwerów). Tech Lead (główny agent) spawnuje `subagent_general` z treścią roli z `AGENT.md` wklejoną do promptu.
>
> **Nie używaj `subagent_explore` dla zadań MCP** — też nie ma MCP (tylko filesystem + web_search).
>
> | Profil | MCP w runtime? | Narzędzia |
> |---|---|---|
> | `subagent_general` (wbudowany) | ✅ TAK | pełny zestaw + 11 serwerów MCP |
> | `subagent_explore` (wbudowany) | ❌ NIE | filesystem + web_search |
> | custom `AGENT.md` (db-architect, backend-dev, …) | ❌ NIE | 5 narzędzi filesystem/shell |
>
> **Dowód runtime (2026-07-05):** `subagent_general` wywołał `mcp__mariadb__query_database({"query":"SHOW TABLES"})` → 33 tabele; `mcp__codebase-memory__search_graph(...)` → 199 wyników. `db-architect` (custom) przy tym samym zadaniu: "narzędzie nie istnieje w moim runtime".

| Agent | Vision dostęp | Kto uruchamia | Kiedy używać | Priorytet |
|-------|---------------|---------------|--------------|-----------|
| **ui-designer** | przez `subagent_general` | Tech Lead → `subagent_general` z rolą ui-designer | Layout, kolory, wzory wizualne | WYSOKI — design system to wizualne |
| **motion-designer** | przez `subagent_general` | Tech Lead → `subagent_general` z rolą motion-designer | Animacje, płynność, mikro-interakcje | WYSOKI — animacje są czysto wizualne |
| **ux-designer** | przez `subagent_general` | Tech Lead → `subagent_general` z rolą ux-designer | Intuicyjność layoutu | BARDZO NISKI — rzadko, tylko gdy programatyczna niemożliwa |
| **frontend-dev** | przez `subagent_general` | Tech Lead → `subagent_general` z rolą frontend-dev | Layout/spacing/kolory/animacje | ŚREDNI — tylko gdy zmiana jest wizualna |
| **tech-lead** | ✅ bezpośrednio | Tech Lead (sam, główny agent) | Weryfikacja po raporcie subagenta | ŚREDNI — finalna weryfikacja UI |

## Agents BEZ dostępu do vision

| Agent | Dlaczego nie potrzebuje vision |
|-------|-------------------------------|
| **backend-dev** | Backend-only — weryfikacja przez testy unit, curl |
| **db-architect** | Database-only — weryfikacja przez DESCRIBE, SHOW CREATE TABLE |
| **performance-eng** | Performance-only — weryfikacja przez time curl, bundle analysis, EXPLAIN |
| **product-owner** | Biznesowa rola — read-only, analiza wymagań, ROI |
| **qa-engineer** | Ma Playwright — E2E robią screenshots automatycznie |
| **security-auditor** | Security-only — weryfikacja przez grep, curl, pip-audit |
| **tech-lead** | Architektura — read-only, git, grep, code analysis |

## Zasada decyzyjna (dla wszystkich agentów z vision)

```
Zadanie?
├─ Backend-only / DB-only / Performance → NIE używaj vision
├─ Frontend logika (pola, teksty, routing) → Programatyczna (grep/read)
├─ UI kolory/layout/spacing → UI Designer vision
├─ Animacje/transitions → Motion Designer vision
├─ Intuicyjność layoutu → UX Designer vision (bardzo rzadko)
└─ Wizualna zmiana w kodzie → Frontend-dev vision (tylko gdy potrzebne)
```

## Koszty vision

- **~$0.01-0.03 per screenshot** (Claude Opus 4.5)
- Vision jest wolne (~5-10s per screenshot)
- Używaj tylko gdy naprawdę potrzebne

## Priorytety weryfikacji

1. **Programatyczna** (darmowa, szybka) → zawsze pierwsza
   - `grep` — sprawdź czy pole istnieje w kodzie
   - `read` — sprawdź Vue component template
   - `curl` — sprawdź API endpoint
   - Testy unit/E2E — sprawdź funkcjonalność

2. **Vision** (kosztowna, wolna) → tylko gdy programatyczna niemożliwa
   - Layout/spacing/alignments
   - Kolory/gradients
   - Animacje/płynność
   - Intuicyjność wzorców wizualnych

## Przykłady praktyczne

**Przykład 1: Dodanie pola formularza**
```
Agent: frontend-dev
Decyzja: Programatyczna weryfikacja
Jak: grep -r "delivery_address" frontend/src/contracts/
Vision: NIE potrzebne
```

**Przykład 2: Zmiana koloru przycisku**
```
Agent: ui-designer
Decyzja: Vision verification
Dlaczego: Kolory są wizualne, nie da się wywnioskować z kodu
Jak: rao-vision.screenshot_and_analyze({question: "Czy button jest czerwony?"})
Vision: TAK potrzebne
```

**Przykład 3: Poprawa animacji**
```
Agent: motion-designer
Decyzja: Vision verification
Dlaczego: Animacje są czysto wizualne
Jak: rao-vision.screenshot_and_analyze({question: "Czy animacja jest płynna?"})
Vision: TAK potrzebne
```

**Przykład 4: Dodanie API endpoint**
```
Agent: backend-dev
Decyzja: Programatyczna weryfikacja
Dlaczego: Backend-only
Jak: curl http://localhost:8000/rao/api/contracts/1/positions
Vision: NIE potrzebne
```

## Implementacja w agentach

> **MCP w subagentach:** kazdy profil deklaruje narzedzia MCP w `allowed-tools` (format `mcp__serwer__*`) oraz w `permissions.allow` (auto-approval, wymagane dla trybu background). Jesli wywolanie MCP zwroci blad, wklej DOSLOWNY komunikat do raportu ("unknown tool" vs "permission denied" to rozne diagnozy) i dopiero wtedy uzyj fallbacku (grep / exec / prosba do Tech Leada o MCP context).

### ui-designer
- Dostęp: `mcp__rao-vision__*`
- Używaj gdy: layout, kolory, wzory wizualne
- Nie używaj gdy: sprawdzenie CSS variables (grep)

### motion-designer
- Dostęp: `mcp__rao-vision__*`
- Używaj gdy: animacje, płynność, hover effects
- Nie używaj gdy: sprawdzenie CSS duration/properties (grep)
- Ograniczenie: Vision nie oceni timing — tylko czy "wygląda płynnie"

### ux-designer
- Dostęp: `mcp__rao-vision__*`
- Używaj gdy: intuicyjność layoutu (bardzo rzadko)
- Nie używaj gdy: teksty, flow, walidacja (read template)

### frontend-dev
- Dostęp: `mcp__rao-vision__*`
- Używaj gdy: layout/spacing/kolory/animacje w implementacji
- Nie używaj gdy: dodanie pól, tekstów, logiki

## Konfiguracja MCP

Plik konfiguracyjny: `.devin/config.json`
```json
{
  "mcpServers": {
    "rao-vision": {
      "command": "node",
      "args": ["mcp-vision/index.js"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

## Aktualizacja software-house skill

Skill `.devin/skills/software-house/SKILL.md` zawiera:
- Krok 6.5: Vision Verification (tylko gdy potrzebne)
- Mapa decyzyjna: programatyczna vs vision
- 5 przykładów praktycznych
- Priorytety: programatyczna (darmowa) → vision (kosztowne)

## Benefits

- ⚡ **Szybsze execution** — vision jest wolne
- 💰 **Niższe koszty** — mniej screenshotów
- 🎯 **Lepsze decyzje** — vision tylko gdy naprawdę potrzebne
- 📝 **Praktyczne przewodniki** — agenty wiedzą kiedy używać vision

---

**Ostatnia aktualizacja:** 2026-05-17
**Refactor:** Ujednolicenie podejścia vision verification dla wszystkich agentów