# 🏢 Software House RAO — Pełna Ekipa Subagentów

Zespół 11 wyspecjalizowanych subagentów Devin dla projektu RAO (FastAPI + Vue 3).

## 👥 Skład zespołu

| Profile | Rola | Model | Permisje | Kiedy wzywać |
|---------|------|-------|----------|--------------|
| `tech-lead` | Tech Lead / Architect | **opus** | Read-only | Decyzje architektoniczne, podział pracy |
| `db-architect` | Database Architect | **opus** | Write: models, migracje, DDL spec | Każda zmiana schema DB |
| `backend-dev` | Backend Developer | **sonnet** | Write: backend/**/*.py | Endpointy, logika biznesowa, testy unit |
| `frontend-dev` | Frontend Developer | **sonnet** | Write: frontend/** | Komponenty, stores, routing |
| `ux-designer` | UX Designer | **opus** | Read-only | Flow użytkownika, edge cases UX |
| `ui-designer` | UI Designer | **sonnet** | Read-only | Design system, spójność wizualna |
| `motion-designer` | Motion Designer | **sonnet** | Read-only | Animacje, mikro-interakcje |
| `security-auditor` | Security Auditor | **opus** | Read-only | Auth, IDOR, walidacja, sekrety |
| `performance-eng` | Performance Engineer | **opus** | Read-only | N+1, paginacja, bundle size |
| `qa-engineer` | QA Engineer | **opus** | Write: tests/** | Edge cases, testy unit + e2e |
| `product-owner` | Product Owner | **opus** | Read-only | Wartość biznesowa, priorytet, DoD |

### Strategia modeli (maksymalna skuteczność przy optymalizacji kosztów)

**Opus (7 agentów)** — tam gdzie głębokie rozumowanie jest KRYTYCZNE:
- Architektura, migracje (nieodwracalne decyzje)
- Security (adversarial thinking)
- QA (wyliczanie edge cases)
- UX (empathia użytkownika)
- Performance (reasoning o bottleneckach)
- PO (strategia i priorytety)

**Sonnet (4 agentów)** — tam gdzie throughput kodu > głębokie rozumowanie:
- Backend CRUD (pattern matching)
- Frontend CRUD (pattern matching)
- UI design (pattern matching design system)
- Motion design (pattern matching CSS animations)

## 🚀 Jak uruchomić

### Opcja 1: Skill `software-house` (rekomendowana)

W sesji Devin wpisz:
```
/software-house <opis zadania>
```

Główny agent wcieli się w **Tech Leada** i automatycznie zorganizuje pracę zespołu.

**Przykład:**
```
/software-house Dodaj pole delivery_address do umów z UI i testami
```

### Opcja 2: Manualne wzywanie subagentów

Możesz też explicite poprosić Devin o użycie konkretnego subagenta:
```
"Użyj subagent db-architect żeby zaprojektować migrację dla nowej tabeli deliveries"

"Wezwij security-auditor do review tego endpointa"

"Zrób research w subagent product-owner czy ten feature ma sens biznesowy"
```

## 🔄 Wzorzec współpracy

```
User → Main Agent (Tech Lead)
         │
         ├─ FAZA ANALIZY (parallel, background)
         │  ├─ product-owner    → "Czy to potrzebne?"
         │  ├─ tech-lead        → "Jaka architektura?"
         │  ├─ qa-engineer      → "Edge cases?"
         │  └─ security-auditor → "Auth/IDOR?"
         │
         ├─ FAZA IMPLEMENTACJI (sequential dependencies)
         │  ├─ db-architect    → schema + migracja
         │  ├─ backend-dev     → models/schemas/service/router
         │  └─ frontend-dev    → components/stores/views
         │     └─ (parallel) ui-designer + ux-designer review
         │
         ├─ FAZA POLISHU (parallel, background)
         │  ├─ motion-designer → animacje
         │  ├─ performance-eng → optymalizacje
         │  └─ ui-designer     → spójność końcowa
         │
         └─ FAZA WERYFIKACJI
            └─ qa-engineer    → testy unit + e2e + smoke regression
```

## 📋 Przykładowe zadania → którzy agenci

### "Dodaj nowe pole do tabeli"
1. `product-owner` - czy potrzebne biznesowo?
2. `tech-lead` - klasyfikacja, side effects
3. `db-architect` - migracja
4. `backend-dev` - schema, service
5. `frontend-dev` - UI integration
6. `qa-engineer` - testy

### "Napraw bug w UI"
1. `qa-engineer` - repro, isolacja
2. `ux-designer` - czy fix poprawia UX
3. `frontend-dev` - implementacja fixu
4. `qa-engineer` - regression test

### "Optymalizuj wolny endpoint"
1. `performance-eng` - profiling, identyfikacja bottlenecka
2. `db-architect` - indeksy, eager loading
3. `backend-dev` - implementacja
4. `qa-engineer` - benchmark before/after

### "Dodaj nowy widok"
1. `product-owner` - wymagania, DoD
2. `ux-designer` - flow
3. `ui-designer` - design system
4. `frontend-dev` - implementacja
5. `motion-designer` - animacje
6. `qa-engineer` - e2e test

### "Security review"
1. `security-auditor` - audyt całego modułu
2. `backend-dev` / `frontend-dev` - fixy

## ⚙️ Konfiguracja

### Lokalizacja
- Skill: `.devin/skills/software-house/SKILL.md`
- Agenty: `.devin/agents/<name>/AGENT.md`

### Permisje
Każdy agent ma `allowed-tools` i `permissions` w frontmatter. Najważniejsze:
- **Write/Edit** ograniczone do "swojego obszaru" (np. backend-dev nie może pisać do frontend/)
- **Read-only** role (UX, UI, Motion, Security, Performance, Product, Tech Lead) NIE modyfikują kodu

### Modele
Domyślnie wszystkie używają domyślnego modelu Devin (możesz nadpisać per-agent dodając `model: opus` w frontmatter).

## 🎯 Reguły operacyjne

1. **Tech Lead jest orchestratorem** — nie wykonawcą
2. **Subagenty są stateless** — każdy musi dostać pełny kontekst w prompt
3. **Background dla niezależnych zadań** — parallelism = szybkość
4. **Foreground dla decyzyjnych kroków** — czekaj na wynik przed dalej
5. **Spec/ to single source of truth** — update po każdej zmianie funkcjonalnej
6. **Smoke test po zmianach** — `e2e/tests/01-login.spec.ts` musi przejść
7. **Zero `kill-port`/`pkill`** — port zajęty → kolejny wolny

## 🔍 Weryfikacja konfiguracji

```bash
# Sprawdź czy Devin widzi agenty
devin
> /agents list

# Powinno pokazać 11 custom profili + 2 built-in (subagent_explore, subagent_general)
```

## 📚 Powiązane

- `.windsurf/workflows/loop-do-skutku-rao.md` — autonomiczna pętla pełnostackowa
- `.windsurf/rules/` — reguły always-on (rao-project, rao-migrations, rao-spec-sync)
- `AGENTS.md` — uniwersalna instrukcja dla wszystkich agentów AI
- `spec/` — single source of truth o aktualnym stanie aplikacji

## 🎨 Anatomia AGENT.md

```markdown
---
name: <profile-name>           # zgodne z nazwą folderu
description: <kiedy wzywać>    # main agent czyta to zeby wybrac profile
allowed-tools:                 # ograniczenie tools (opcjonalne)
  - read
  - grep
  - edit
permissions:                   # nadpisuje user permissions
  allow:
    - Write(backend/**/*.py)
  deny:
    - Write(frontend/**/*)
model: sonnet                  # opcjonalny override modelu
---

# System prompt subagenta
[markdown z instrukcjami i wzorcami]
```
