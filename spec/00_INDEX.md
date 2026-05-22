# RAO Application Specification — Agent-Ready Build Guide

> **Cel:** Poniższe pliki stanowią **kompletną specyfikację** nowej aplikacji RAO (FastAPI + Vue.js 3).
> Agent budujący aplikację NIE POTRZEBUJE dostępu do starego kodu WinForms — wystarczą te dokumenty.

## Struktura folderów

```
spec/
├── core/           # Single source of truth (database, API, screens, business logic, security)
├── process/        # Procedures (migrations, testing, workflow)
├── backlog/        # Planning with YAML front-matter format
├── archive/        # Historical specs
├── AGENT_PLAYBOOK.md  # Role mapping for agents
└── 00_INDEX.md     # This file
```

## Core Specifications (single source of truth)

|| # | Plik | Opis |
||---|------|------|
|| 01 | [core/01_database.md](./core/01_database.md) | Kompletne DDL nowej bazy MariaDB (3NF) + migracja ze starej bazy |
|| 02 | [core/02_backend_api.md](./core/02_backend_api.md) | Kompletne endpointy FastAPI + Pydantic modele + logika biznesowa |
|| 03 | [core/03_frontend_screens.md](./core/03_frontend_screens.md) | Kompletne ekrany Vue.js + wireframe + dokładny layout + event handlers |
|| 04 | [core/04_business_logic.md](./core/04_business_logic.md) | Algorytmy: numeracja umów, kalkulacja wartości, stawki, warunki |
|| 05 | [core/05_cross_check.md](./core/05_cross_check.md) | Macierz: stary GUI ↔ SQL ↔ widoki ↔ procedury ↔ nowe endpointy |
|| 06 | [core/06_navigation_flow.md](./core/06_navigation_flow.md) | Flow użytkownika, routing, uprawnienia |
|| 07 | [core/07_integrations.md](./core/07_integrations.md) | GUS API, Nominatim, raporty PDF |
|| 08 | [core/08_migration_plan.md](./core/08_migration_plan.md) | Migracja danych: stare → nowe tabele + skrypty SQL |
|| 09 | [core/09_design_reference.md](./core/09_design_reference.md) | Design system Toolsmart: paleta, CSS, screenshots |
|| 11 | [core/11_reports_stats.md](./core/11_reports_stats.md) | Wydruki PDF (Jinja2) + Analityka i KPI |
|| 12 | [core/12_logic_audit.md](./core/12_logic_audit.md) | Audyt logiki biznesowej (historyczne) |
|| 13 | [core/13_audit_all_processes.md](./core/13_audit_all_processes.md) | Cross-role audyt wszystkich 9 procesów (historyczne) |
|| 14 | [core/14_audit_contract_process.md](./core/14_audit_contract_process.md) | Szczegółowy audyt procesu umów (historyczne) |
|| 15 | [core/15_build_progress.md](./core/15_build_progress.md) | Status budowy — implementacja P0/P1/P2 + migracja |
|| 17 | [core/17_testing_plan.md](./core/17_testing_plan.md) | Strategia testowania + scenariusze |
|| 18 | [core/18_ux_improvements.md](./core/18_ux_improvements.md) | UX/GUI propozycje usprawnień (historyczne) |
|| 20 | [core/20_user_guide_settlement.md](./core/20_user_guide_settlement.md) | Instrukcja użytkownika: jak wykonać rozliczenie |
|| 23 | [core/23_explorer_design.md](./core/23_explorer_design.md) | Design eksploratora raportów |
|| 24 | [core/24_export_ujednolicenie.md](./core/24_export_ujednolicenie.md) | Export ujednolicenie |
|| 25 | [core/25_security.md](./core/25_security.md) | Security spec: threat model, RBAC, JWT, RODO |
|| 25 | [core/25_uslugi_dodatkowe/](./core/25_uslugi_dodatkowe/) | Usługi dodatkowe szczegóły |

## Process Specifications

|| # | Plik | Opis |
||---|------|------|
|| 01 | [process/migrations.md](./process/migrations.md) | Deterministic migration policy |
|| 10 | [process/10_windsurf_workflow.md](./process/10_windsurf_workflow.md) | Workflow agentowy: self-healing budowa od zera do produkcji |

## Backlog

|| # | Plik | Opis |
||---|------|------|
|| 01 | [backlog/BACKLOG.md](./backlog/BACKLOG.md) | Aktywny backlog (Sprint 2) — YAML front-matter |
|| 02 | [archive/BACKLOG_SPRINT_1.md](./archive/BACKLOG_SPRINT_1.md) | Sprint 1 (zakończony 2026-05-22) — 73 taski, ~190h |

## Archive

Historical specs and completed tasks:
- `archive/16_todo_done.md` — Historia zadań ukończonych
- `archive/22_IMPLEMENTATION_REPORT.md` — Raport implementacji
- `archive/19_backlog_old.md` — Stary backlog (przed reorganizacją)
- `archive/21_backlog_client_old.md` — Stary backlog klienta
- `archive/BACKLOG_SPRINT_1.md` — Backlog Sprint 1 (zakończony 2026-05-22)
- `archive/00_REORGANIZATION_PLAN.md` — Plan reorganizacji
- `archive/REORGANIZATION_REPORT.md` — Raport reorganizacji
- `archive/DB_CONFIG.md`, `NEW_DB_CONFIG.md` — Stare konfiguracje DB
- `archive/reference_reports/` — Raporty referencyjne

## Agent Playbook

- [AGENT_PLAYBOOK.md](./AGENT_PLAYBOOK.md) — Role mapping for agents (tech-lead, backend-dev, frontend-dev, etc.)

## Technologie

|| Warstwa | Technologia | Wersja |
||---------|-------------|--------|
|| Backend | Python + FastAPI | 3.12 / 0.115+ |
|| ORM | SQLAlchemy 2.0 (async) | 2.0+ |
|| Walidacja | Pydantic v2 | 2.0+ |
|| Frontend | Vue.js 3 (Composition API) | 3.5+ |
|| Router | Vue Router 4 | 4.0+ |
|| State | Pinia | 2.0+ |
|| HTTP | Axios | 1.7+ |
|| UI | Vanilla CSS (design system Toolsmart) | — |
|| DB | MariaDB | 10.6+ |
|| Auth | JWT (python-jose) + bcrypt | — |
|| Raporty | WeasyPrint / Jinja2 HTML templates | — |
|| Email | smtplib (SMTP) | — |

## Stary system (dla kontekstu)

- WinForms (.NET 4.7.2) + Crystal Reports
- MariaDB z 30+ tabelami (wiele legacy, brak FK constraints)
- ADO.NET z surowymi SQL stringami (SQL injection vulnerable)

## Ważne zasady dla agenta

1. **1:1 feature parity** — nowa app musi mieć identyczną funkcjonalność
2. **Identyczny flow nawigacji** — użytkownicy muszą się poruszać tak samo
3. **Normalizacja 3NF** — stare denormalizowane dane → prawidłowe FK
4. **Bezpieczeństwo** — bcrypt, JWT, parameterized queries, env vars
5. **Wygląd Toolsmart** — navy `#1D2B53`, Montserrat, rounded cards 12px, pill buttons
6. **ORM only** — zero procedur składowanych, cała logika w Python
7. **Workflow** — przeczytaj `process/10_windsurf_workflow.md` i AGENT_PLAYBOOK.md