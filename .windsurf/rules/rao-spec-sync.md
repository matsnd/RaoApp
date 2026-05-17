---
trigger: always_on
description: spec/ to single source of truth — aktualizuj odpowiedni plik PO każdej zmianie funkcjonalnej
---

# Spec sync — `spec/` jest single source of truth

Folder `spec/` opisuje aktualny stan aplikacji RAO. Następny agent / deweloper czyta to żeby zrozumieć system. **Zombie-spec** (opisuje rzeczy których nie ma) niszczy zaufanie do dokumentacji.

## Mapa: co zmieniłeś → który spec aktualizujesz

| Co zmieniłeś | Który spec aktualizujesz |
|--------------|--------------------------|
| Schema DB (kolumna, tabela, FK, indeks) | `spec/01_DATABASE_DDL.md` (mirror finalnego DDL) |
| Endpoint REST (URL, body, response, status codes) | `spec/02_BACKEND_API.md` |
| Pydantic schema (validation, fields, constraints) | `spec/02_BACKEND_API.md` |
| Nowy/zmieniony widok Vue / komponent | `spec/03_FRONTEND_SCREENS.md` |
| Algorytm biznesowy (kalkulacja, numeracja) | `spec/04_BUSINESS_LOGIC.md` |
| Mapping stary GUI ↔ nowe endpointy | `spec/05_CROSS_CHECK.md` |
| Routing / nawigacja / context menu | `spec/06_NAVIGATION_FLOW.md` |
| GUS, Nominatim, PDF, SMTP | `spec/07_INTEGRATIONS.md` |
| Skrypt migracji starych danych | `spec/08_MIGRATION_PLAN.md` |
| CSS variables / typografia / kolory | `spec/09_DESIGN_REFERENCE.md` |
| Szablony PDF / statystyki / KPI | `spec/11_REPORTS_AND_STATS.md` |
| User guide rozliczeń | `spec/20_USER_GUIDE_SETTLEMENT.md` |
| Backlog (oznacz jako ✅ done) | `spec/19_BACKLOG.md` |
| Audyt logiki / dziury w spec | `spec/12_LOGIC_AUDIT.md`, `13`, `14` (archiwum) |
| TODO i pomysły na przyszłość | `spec/16_TODO.md`, `19_BACKLOG.md` |

**Źle:** brak update spec po dodaniu kolumny `delivery_address` → następny agent nie wie że istnieje
**Dobrze:** kolumna w `01_DATABASE_DDL.md` + pole w `ContractOut` w `02_BACKEND_API.md` + wzmianka w `03_FRONTEND_SCREENS.md` (jeśli widoczna w UI)

## 5 reguł aktualizacji spec

1. **Najpierw zmień kod, potem spec** — żeby nie powstała zombie-spec opisująca rzeczy których nie ma
2. **Spec opisuje aktualny stan** — nie historię, nie plany. Plany trzymaj w `16_TODO.md` lub `19_BACKLOG.md`
3. **Spójność nazw** — przykład dla kolumny `delivery_address`:
   - DDL: `delivery_address VARCHAR(255) NULL`
   - API: `delivery_address: str | None` w `ContractOut`
   - Screens: wzmianka o polu w odpowiednim widoku (jeśli widoczne)
4. **Drobne fixy (1 linia, bez efektu na interfejs)** — można pominąć update spec
5. **Wątpliwości?** → zaktualizuj spec. Lepiej za dużo niż za mało.

## Sprawdź PRZED zamknięciem zadania

```pwsh
git diff --stat spec/
```

**Pass kryteria:**
- Pusty diff → zadanie czysto kosmetyczne / refactor bez zmian funkcjonalnych
- Diff w DDL + API → backend feature
- Diff w Screens / Navigation → frontend feature
- Diff w Business Logic → zmiana algorytmu (kalkulacja, numeracja)
- Diff w Backlog → zaznaczyłeś pozycję jako done

**Fail kryteria:**
- Dodałeś endpoint, ale `git diff spec/02_BACKEND_API.md` jest pusty → spec niezsynchronizowane
- Dodałeś kolumnę, ale `git diff spec/01_DATABASE_DDL.md` jest pusty → patrz reguła `rao-migrations`
- Zmieniłeś flow nawigacyjny, ale `06_NAVIGATION_FLOW.md` zostało stare → następny agent będzie zdezorientowany

## Format aktualizacji DDL w spec/01_DATABASE_DDL.md

DDL spec to **mirror finalnego stanu** (co dostaniesz po `SHOW CREATE TABLE`). Nie zostawiaj migracji-style "ALTER TABLE ADD COLUMN" w spec — to zaśmieca. Pełny finalny `CREATE TABLE` to format spec.

```sql
-- Stara wersja w spec:
CREATE TABLE contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id INT NOT NULL,
    ...
);

-- Nowa wersja w spec po dodaniu delivery_address:
CREATE TABLE contracts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contractor_id INT NOT NULL,
    delivery_address VARCHAR(255) NULL COMMENT 'Adres dostawy maszyny',
    ...
);
```

Migracja inkrementalna idzie do `backend/main.py` startup event (patrz reguła `rao-migrations`).

## Powiązane reguły

- `rao-project` — stack, porty, design system (always_on)
- `rao-migrations` — deterministyczne migracje DB (glob na pliki DB)
- workflow `/loop-do-skutku-rao` — autonomiczny tryb z 5-tier verification
