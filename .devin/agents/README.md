# RAO Agents - Vision Verification Strategy

## Overview

Inteligentne podejście do vision verification: **programatyczna weryfikacja (darmowa) → vision (kosztowne)** tylko gdy niemożliwe.

## 🤝 Koordynacja między agentami (NOWE 2026-07-04)

**📖 Pełny protokół:** `.devin/workflows/coordination-protocol.md`

Subagenty są stateless — koordynacja przez:

1. **Shared context file** (`.devin/_session_context.md`) — Tech Lead tworzy na starcie zadania, każdy subagent czyta i dopisuje sekcję HANDOFF
2. **Handoff protocol** — każdy subagent kończy sekcją: CO ZROBIŁEM / GOTOWE DLA / BLOCKERY / EVIDENCE / SPEC UPDATE
3. **Review chain matrix** (kto czeka na kogo):
   ```
   Phase 0 ANALYSIS (równolegle): product-owner, tech-lead, qa-engineer, security-auditor
   Phase 1 DB: db-architect (po tech-lead plan)
   Phase 2 BACKEND: backend-dev (po db-architect)
   Phase 3 FRONTEND: frontend-dev (po backend-dev)
   Phase 4 POLISH (równolegle po frontend): ui-designer, ux-designer, motion-designer
   Phase 5 AUDIT (równolegle po backend+frontend): security-auditor, performance-eng
   Phase 6 QA: qa-engineer (po wszystkich implementacjach)
   Phase 7 FINAL REVIEW (równolegle po QA): tech-lead, product-owner
   COMMIT (Tech Lead po final review)
   ```
4. **Conflict resolution** — hierarchia: Security (veto) > Data integrity > Correctness > UX > Performance > UI > Motion > Code style
5. **Evidence folder** (`.devin/_evidence/<role>/`) — każdy subagent zapisuje dowody. Brak evidence = odrzucony handoff
6. **Vision deduplikacja** — frontend-dev robi 1 screenshot per widok, inne role (ui-designer, ux-designer, motion-designer, product-owner) reuse przez `rao-vision.analyze_screenshot`

Każdy `.devin/agents/*/AGENT.md` ma sekcję "Handoff & Shared Context" z rolą-specyficznymi instrukcjami.

## Agents z dostępem do vision (rao-vision MCP)

| Agent | Dostęp do vision | Kiedy używać | Priorytet |
|-------|-----------------|--------------|-----------|
| **ui-designer** | ✅ `mcp_call_tool` + `MCP(rao-vision)` | Layout, kolory, wzory wizualne | WYSOKI — design system to wizualne |
| **motion-designer** | ✅ `mcp_call_tool` + `MCP(rao-vision)` | Animacje, płynność, mikro-interakcje | WYSOKI — animacje są czysto wizualne |
| **ux-designer** | ✅ `mcp_call_tool` + `MCP(rao-vision)` | Intuicyjność layoutu | BARDZO NISKI — rzadko, tylko gdy programatyczna niemożliwa |
| **frontend-dev** | ✅ W sekcji "Po zmianie" | Layout/spacing/kolory/animacje | ŚREDNI — tylko gdy zmiana jest wizualna |

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

### ui-designer
- Dostęp: `mcp_call_tool` + `MCP(rao-vision)`
- Używaj gdy: layout, kolory, wzory wizualne
- Nie używaj gdy: sprawdzenie CSS variables (grep)

### motion-designer
- Dostęp: `mcp_call_tool` + `MCP(rao-vision)`
- Używaj gdy: animacje, płynność, hover effects
- Nie używaj gdy: sprawdzenie CSS duration/properties (grep)
- Ograniczenie: Vision nie oceni timing — tylko czy "wygląda płynnie"

### ux-designer
- Dostęp: `mcp_call_tool` + `MCP(rao-vision)`
- Używaj gdy: intuicyjność layoutu (bardzo rzadko)
- Nie używaj gdy: teksty, flow, walidacja (read template)

### frontend-dev
- Dostęp: Opis w sekcji "Po zmianie" (nie w allowed-tools)
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