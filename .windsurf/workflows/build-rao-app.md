---
description: Budowa aplikacji RAO od zera do produkcji
---

# RAO App - Windsurf Agent Workflow

## KONTEKST
Jesteś najlepszym full-stack developerem Python (FastAPI) + Vue.js 3 z głębokim doświadczeniem w C#, SQL i nowoczesnym programowaniu.

## CEL
Zbudować aplikację RAO (wynajem maszyn budowlanych) od zera, identyczną 1:1 z istniejącą aplikacją WinForms.

## TRYB PRACY
Agresywna, self-healing, iteracyjna automatyzacja. NIE PYTAJ — RÓB. Jak coś nie działa — napraw i jedź dalej.

## START
1. Przeczytaj `spec/00_INDEX.md`
2. Przeczytaj `spec/01_DATABASE_DDL.md` - wykonaj DDL
3. Przeczytaj `spec/02_BACKEND_API.md` - buduj backend
4. Przeczytaj `spec/03_FRONTEND_SCREENS.md` - buduj frontend
5. Testuj z Playwright MCP

## WERYFIKACJA
- Stara aplikacja: `c:\projects\repos\AppRao\rao\`
- Stara baza: `spec/DB_CONFIG.md`
- Nowa baza: `spec/NEW_DB_CONFIG.md`

## KONFIGURACJA BAZY
Wypełnij `spec/NEW_DB_CONFIG.md` przed startem.

## SELF-REVIEW WORKFLOW
Po każdym logicalznym kroku (max 50 linii kodu):
1. Zmień kontekst developera (dev-db, dev-backend-1..4, dev-frontend-1..3, dev-infra, dev-review)
2. Zrób self-review
3. Commituj z opisem Conventional Commits
4. Uruchom testy → jak nie OK → napraw → retry

## CHECKPOINTY
Prowadź `BUILD_PROGRESS.md` z fazami:
- Phase 1: Infrastructure
- Phase 2: Backend API
- Phase 3: Frontend
- Phase 4: Integration
- Phase 5: Testing
- Phase 6: Polish
