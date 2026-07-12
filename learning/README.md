# Learn-By-Code — Python + Vue dla .NET + Angular dev

Materiały do nauki **na bazie realnego kodu aplikacji RAO** (FastAPI + Vue 3).
Założenie: znasz C#/.NET i Angular, chcesz zrozumieć Pythona i Vue 3, którego wygenerowałeś tutaj.

## Jak tego używać

1. **Czytaj lekcje** w `lessons/` — każda oparta na realnym pliku z repo, z mapowaniem .NET/Angular → Python/Vue i teorią.
2. **Odpal quiz** w terminalu między zadaniami:

   ```powershell
   # z venva backendu (ma pyyaml)
   cd C:\projects\repos\RaoApp_new
   .\backend\.venv\Scripts\python.exe learning\quiz\quiz.py
   ```

   Flagi:
   - `--topic python|sqlalchemy|pydantic|fastapi|di|async|service|migrations|vue|pinia|router|props` — tylko pytania z tematu
   - `--n 10` — liczba pytań w sesji (domyślnie 10)
   - `--all` — wszystkie pytania po kolei
   - `--history` — pokaż historię wyników

3. **Wolny tryb** — czytasz lekcję, potem 5 pytań z jej tematu, sprawdzasz czy siedzi.

## Lekcje

### Backend (Python / FastAPI)

| # | Lekcja | Plik bazowy | Odpowiednik .NET |
|---|--------|-------------|------------------|
| 01 | [Python basics for C# dev](lessons/01-python-basics-for-csharp-dev.md) | `backend/articles/schemas.py` | C# type system, async |
| 02 | [SQLAlchemy models vs EF Core](lessons/02-sqlalchemy-models-vs-ef-core.md) | `backend/articles/models.py` | EF Core entities |
| 03 | [Pydantic v2 schemas vs DTOs](lessons/03-pydantic-v2-schemas-vs-dtos.md) | `backend/articles/schemas.py` | C# records / DTOs |
| 04 | [FastAPI router vs Controller](lessons/04-fastapi-router-vs-controller.md) | `backend/articles/router.py` | `[ApiController]` |
| 05 | [DI & auth — JWT](lessons/05-di-and-auth-jwt.md) | `backend/auth/dependencies.py` | `[FromServices]` + JWT middleware |
| 06 | [Async SQLAlchemy session](lessons/06-async-sqlalchemy-session.md) | `backend/articles/service.py` | `DbContext` + async |
| 07 | [Service layer pattern](lessons/07-service-layer-pattern.md) | `backend/articles/service.py` | Application Service |
| 08 | [Migrations without Alembic](lessons/08-migrations-without-alembic.md) | `backend/main.py` | EF Migrations (różnice!) |

### Frontend (Vue 3)

| # | Lekcja | Plik bazowy | Odpowiednik Angular |
|---|--------|-------------|---------------------|
| 09 | [Vue SFC + Composition API](lessons/09-vue-sfc-composition-api.md) | `frontend/src/views/MachinesListView.vue` | Angular component |
| 10 | [Pinia store vs Angular service](lessons/10-pinia-store-vs-angular-service.md) | `frontend/src/stores/articles.js` | Service + NgRx |
| 11 | [vue-router + Axios interceptor](lessons/11-vue-router-and-axios-interceptor.md) | `frontend/src/router/index.js`, `composables/useApi.js` | Angular Router + HttpInterceptor |
| 12 | [Props/emit + composables](lessons/12-props-emit-composables.md) | `frontend/src/composables/useSort.ts` | `@Input`/`@Output` + service |

## Konwencja

- Każda lekcja ma sekcję **"Realny snippet z repo"** z cytatem `<ref_snippet>` — kliknij, otworzy się w IDE.
- Sekcja **"Mapowanie"** — tabela .NET/Angular → Python/Vue.
- Sekcja **"Teoria"** — jak to działa pod spodem (głębiej niż "to samo inaczej").
- Sekcja **"Gotchas"** — pułapki, które zaskoczą .NET/Angular deva.
- Sekcja **"Quiz"** — 3-5 pytań, które znajdziesz też w `quiz.py`.

## Status

- 12 lekcji + ~50 pytań quizowych
- Quiz CLI: losuje, pyta, sprawdza, daje feedback z linkiem do pliku
- Historia wyników w `learning/quiz/.history.json` (gitignored)

## Uwaga

Materiały są **read-only** — nie modyfikują kodu aplikacji. Drugie okno agenta może pracować nad zadaniami, Ty się uczysz obok.
