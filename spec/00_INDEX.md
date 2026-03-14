# RAO Application Specification — Agent-Ready Build Guide

> **Cel:** Poniższe pliki stanowią **kompletną specyfikację** nowej aplikacji RAO (FastAPI + Vue.js 3).
> Agent budujący aplikację NIE POTRZEBUJE dostępu do starego kodu WinForms — wystarczą te dokumenty.

## Pliki specyfikacji

| # | Plik | Opis |
|---|------|------|
| 01 | [01_DATABASE_DDL.md](./01_DATABASE_DDL.md) | Kompletne DDL nowej bazy MariaDB (3NF) + migracja ze starej bazy |
| 02 | [02_BACKEND_API.md](./02_BACKEND_API.md) | Kompletne endpointy FastAPI + Pydantic modele + logika biznesowa |
| 03 | [03_FRONTEND_SCREENS.md](./03_FRONTEND_SCREENS.md) | Kompletne ekrany Vue.js + wireframe + dokładny layout + event handlers |
| 04 | [04_BUSINESS_LOGIC.md](./04_BUSINESS_LOGIC.md) | Algorytmy: numeracja umów, kalkulacja wartości, stawki, warunki |
| 05 | [05_CROSS_CHECK.md](./05_CROSS_CHECK.md) | Macierz: stary GUI ↔ SQL ↔ widoki ↔ procedury ↔ nowe endpointy |
| 06 | [06_NAVIGATION_FLOW.md](./06_NAVIGATION_FLOW.md) | Flow użytkownika, routing, uprawnienia |
| 07 | [07_INTEGRATIONS.md](./07_INTEGRATIONS.md) | GUS API, Nominatim, raporty PDF |
| 08 | [08_MIGRATION_PLAN.md](./08_MIGRATION_PLAN.md) | Migracja danych: stare → nowe tabele + skrypty SQL |
| 09 | [09_DESIGN_REFERENCE.md](./09_DESIGN_REFERENCE.md) | Design system Toolsmart: paleta, CSS, screenshots |
| 10 | [10_WINDSURF_WORKFLOW.md](./10_WINDSURF_WORKFLOW.md) | Workflow agentowy: self-healing budowa od zera do produkcji |
| 11 | [11_REPORTS_AND_STATS.md](./11_REPORTS_AND_STATS.md) | Wydruki PDF (Jinja2) + Analityka i KPI |

## Technologie

| Warstwa | Technologia | Wersja |
|---------|-------------|--------|
| Backend | Python + FastAPI | 3.12 / 0.115+ |
| ORM | SQLAlchemy 2.0 (async) | 2.0+ |
| Walidacja | Pydantic v2 | 2.0+ |
| Frontend | Vue.js 3 (Composition API) | 3.5+ |
| Router | Vue Router 4 | 4.0+ |
| State | Pinia | 2.0+ |
| HTTP | Axios | 1.7+ |
| UI | Vanilla CSS (design system Toolsmart) | — |
| DB | MariaDB | 10.6+ |
| Auth | JWT (python-jose) + bcrypt | — |
| Raporty | WeasyPrint / Jinja2 HTML templates | — |
| Email | smtplib (SMTP) | — |

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
7. **Workflow** — przeczytaj `10_WINDSURF_WORKFLOW.md` i jedź iteracyjnie do skutku
