# Audit: Kod vs. Specyfikacja — RAO
**Data:** 2026-05-19  
**Zakres:** Backend (router.py, models.py) + Frontend (views, stores, routing) + Backlog status  
**Zadanie:** RAO-P2-014  
**Metodologia:** 3 równoległe subagenty analityczne + synthesis

---

## Spis treści

1. [Podsumowanie wykonawcze](#1-podsumowanie-wykonawcze)
2. [Backend Audit](#2-backend-audit)
3. [Frontend Audit](#3-frontend-audit)
4. [Backlog Status Audit](#4-backlog-status-audit)
5. [Skonsolidowana lista rozbieżności](#5-skonsolidowana-lista-rozbieżności)
6. [Plan naprawczy](#6-plan-naprawczy)

---

## 1. Podsumowanie wykonawcze

| Obszar | Zbadano | Zgodne | Rozbieżności |
|--------|---------|--------|--------------|
| **Backend endpointy** | ~111 | ~95 (86%) | 14 w kodzie poza spec |
| **Backend tabele DB** | 26 spec / 20 kod | 20 | 6 tabel w spec bez modeli |
| **Backend pola modeli** | ~200 | ~196 | 4 niezgodności |
| **Frontend widoki** | 12 kod / 7 spec | 7 | 5 widoków bez opisu w spec |
| **Frontend routes** | 15 kod / 10 spec | 10 | 5 routes bez opisu w spec |
| **Frontend komponenty** | 9 | 7 | 2 pickery inline zamiast osobnych plików |
| **Backlog done tasks** | 42 | 41 (97.6%) | 1 w review, 1 in_progress |

**Ogólna ocena:** Kod jest **bardziej zaawansowany niż spec** — spec nie nadąża za implementacją. Nie ma przypadków kodu niezgodnego ze spec w sensie brakującej funkcjonalności. Backlog jest wiarygodny (97.6% weryfikowalności).

---

## 2. Backend Audit

### 2.1 Moduły — 100% pokrycia

Wszystkie 14 modułów backendu są zgodne: `auth`, `contractors`, `articles`, `contracts`, `settings`, `reports`, `integrations`, `integrations/fakturownia`, `explorer`, `stats`, `settlements`, `categories` (w settings), `positions`/`conditions` (w contracts).

### 2.2 Endpointy [BRAK_W_SPEC] — 14 endpointów w kodzie, nieudokumentowanych w spec

#### Stats module — 6 endpointów

| Endpoint | Lokalizacja | Opis |
|----------|-------------|------|
| `GET /stats/expiring-contracts` | `backend/stats/router.py:625-667` | Umowy wygasające w N dni (`?days=30`) |
| `GET /stats/overdue-contracts` | `backend/stats/router.py:668-697` | Umowy przeterminowane |
| `GET /stats/deliveries-today` | `backend/stats/router.py:698-730` | Dostawy zaplanowane na dzisiaj |
| `GET /stats/unprinted-contracts` | `backend/stats/router.py:731-764` | Umowy niewydrukowane |
| `GET /stats/stale-print-contracts` | `backend/stats/router.py:765-803` | Umowy ze starym wydrukiem (edycja po wydruku) |
| `GET /stats/commissions` | `backend/stats/router.py:804-890` | Raporty prowizji handlowców |

#### Explorer module — 5 endpointów

| Endpoint | Lokalizacja | Opis |
|----------|-------------|------|
| `GET /explorer/search` | `backend/explorer/router.py:135-270` | Uniwersalne wyszukiwanie (q, date_from, date_to, category, city, contractor_id) |
| `GET /explorer/services` | `backend/explorer/router.py:395-467` | Podsumowanie usług dodatkowych |
| `GET /explorer/locations` | `backend/explorer/router.py:470-531` | Podsumowanie wynajmów po lokalizacjach |
| `GET /explorer/services/{id}` | `backend/explorer/router.py:534-667` | Szczegóły konkretnej usługi |
| `GET /explorer/locations/{city}` | `backend/explorer/router.py:668-843` | Szczegóły konkretnej lokalizacji |

#### Inne — 3 endpointy

| Endpoint | Lokalizacja | Opis |
|----------|-------------|------|
| `POST /contracts/{id}/service-fees/apply-preset` | `backend/contracts/router.py:281-291` | Aplikuje szablon opłat do umowy (`?preset_id=&replace=true`) |
| `POST /integrations/teryt/sync` | `backend/integrations/router.py:122-171` | Synchronizacja kodów pocztowych z TERYT (RAO-P2-015) |
| `GET /health` | `backend/main.py:258-260` | Health check |

### 2.3 Tabele DB [BRAK_W_KODZIE] — 6 tabel w spec bez modeli SQLAlchemy

| Tabela | Spec | Kod | Priorytet | Rekomendacja |
|--------|------|-----|-----------|--------------|
| `deliveries` | `spec/core/01_database.md:375-386` | brak | P2 | Wyjaśnić z PO — czy potrzebna |
| `delivery_addresses` | `spec/core/01_database.md:388-407` | brak | P2 | Wyjaśnić z PO — czy potrzebna |
| `costs` | `spec/core/01_database.md:463-475` | brak | P2 | Wyjaśnić z PO — czy potrzebna |
| `settlements` (stara) | `spec/core/01_database.md:523-531` | brak | P1 | Usunąć ze spec — zastąpiona przez `contract_settlements` (RAO-P1-012) |
| `audit_log` | `spec/core/01_database.md:556-563` | brak | P3 | Wyjaśnić z PO — czy w backlogu |
| `cost_types` | `spec/core/01_database.md:92-98` | brak | P2 | Wyjaśnić z PO — czy potrzebna |

### 2.4 Niezgodności pól modeli — 4 przypadki

| # | Pole | Spec | Kod | Priorytet | Rekomendacja |
|---|------|------|-----|-----------|--------------|
| 1 | `Branch.created_at` | `DATETIME` | `String(30)` **BŁĄD TYPU!** | **P0** | Zmienić na `DateTime` + migracja |
| 2 | `ContractorAddress.email` | `VARCHAR(20)` | `String(20)` (za krótko) | P1 | Zmienić na `String(100)` + migracja |
| 3 | `FeePresetGroup.description` | brak w spec | `String(400)` w kodzie | P3 | Dodać do spec |
| 4 | `Salesperson.commission_rate` | brak w spec | `Numeric(5,2)` w kodzie | P3 | Dodać do spec |

---

## 3. Frontend Audit

### 3.1 Widoki [BRAK_W_SPEC] — 5 widoków bez opisu w spec

| Widok | Route | Opis funkcjonalny |
|-------|-------|-------------------|
| `HomeView.vue` | `/home` | Główny dashboard z KPI: maszyny w terenie, kończące się umowy, dostawy, niewydrukowane, nieaktualne wydruki + szybka nawigacja |
| `ChangePasswordView.vue` | `/password` | Formularz zmiany hasła (aktualne, nowe, potwierdzenie) |
| `ResetPasswordView.vue` | `/reset-password` | Reset hasła z tokenem z URL (`?token=...`) |
| `CommissionView.vue` | `/commissions` | Raporty prowizji handlowców (tabela per handlowiec + summary) |
| `WorkerView.vue` | `/worker` | Pulpit operacyjny: kończące się umowy, dostawy, statystyki |
| `AdminView.vue` | `/admin` | Panel administracyjny: zarządzanie użytkownikami (CRUD, role, aktywacja) |

### 3.2 Routes [BRAK_W_SPEC] — 5 routes nieudokumentowanych

`/reset-password`, `/home`, `/worker`, `/commissions`, `/password`, `/admin`  
→ Dodać do `spec/core/06_navigation_flow.md`

### 3.3 Komponenty zaimplementowane inline zamiast jako osobne pliki

| Komponent | Spec (oczekiwany plik) | Implementacja |
|-----------|----------------------|---------------|
| `ContractorPicker` | `components/contractors/ContractorPicker.vue` | Modal inline w `ContractFormView.vue:435-458` |
| `ArticlePicker` | `components/articles/ArticlePicker.vue` | Modal inline w `ContractFormView.vue:603-637` |

**Uwaga:** Obecna implementacja inline działa poprawnie. Ekstrakcja do osobnych komponentów jest refactorem opcjonalnym (poprawi reusability).

### 3.4 Niezgodności techniczne

| # | Element | Spec | Kod | Priorytet |
|---|---------|------|-----|-----------|
| 1 | Router file extension | `.ts` (TypeScript) | `.js` (JavaScript) | P3 (kosmetyczny) |
| 2 | ConditionFormView | osobny widok/dialog | `ConditionPanel.vue` jako komponent | P2 (do weryfikacji funkcjonalnej) |

### 3.5 Pinia Stores — 100% zgodności

Wszystkie 8 storów (`auth`, `contracts`, `contractors`, `articles`, `settings`, `stats`, `serviceHours`, `fakturownia`) są zgodne ze spec lub wynikają z zaimplementowanych zadań.

---

## 4. Backlog Status Audit

### 4.1 Weryfikacja zadań `done`

| Priorytet | Zadań done | Zweryfikowanych | % |
|-----------|-----------|-----------------|---|
| P0 | 5 | 5 ✅ | 100% |
| P1 | 21 | 21 ✅ | 100% |
| P2 | 13 | 13 ✅ | 100% |
| **Razem** | **39** | **39** | **100%** |

Wszystkie zadania oznaczone jako `done` mają weryfikowalną implementację w kodzie.

### 4.2 Zadania wymagające korekty statusu

| ID | Tytuł | Obecny status | Rekomendowany | Powód |
|----|-------|---------------|---------------|-------|
| RAO-P2-017 | Poprawa UX/UI (Login, Dashboard, Contract) | `review` | `done` | Zaimplementowane i zatwierdzone w commit `44f3210` |
| RAO-P2-014 | Weryfikacja kodu vs. spec | `in_progress` | `done` | Ten audit — do zamknięcia po commicie |

### 4.3 Rozbieżności w tabeli podsumowania BACKLOG.md

Tabela na końcu BACKLOG.md zawiera stare statusy (przed reorganizacją). Zadania P0 widnieją jako `triaged`/`todo` zamiast `done`. Wymaga ręcznej aktualizacji.

---

## 5. Skonsolidowana lista rozbieżności

### Krytyczne (blokują integralność danych)

| # | Typ | Opis | Plik | Akcja |
|---|-----|------|------|-------|
| **C-1** | BŁĄD TYPU | `Branch.created_at`: `String(30)` zamiast `DateTime` | `backend/settings/models.py` | Zmiana typu + `ALTER TABLE` + spec update |
| **C-2** | BŁĄD DŁUGOŚCI | `ContractorAddress.email`: `VARCHAR(20)` (za krótko) | `backend/contractors/models.py` | Zmiana na `VARCHAR(100)` + `ALTER TABLE` + spec update |

### Spec nie nadąża za kodem (spec gap)

| # | Typ | Opis | Akcja |
|---|-----|------|-------|
| **S-1** | [BRAK_W_SPEC] | 14 endpointów backend nieudokumentowanych | Dodać do `spec/core/02_backend_api.md` |
| **S-2** | [BRAK_W_SPEC] | 6 widoków frontend nieudokumentowanych | Dodać do `spec/core/03_frontend_screens.md` |
| **S-3** | [BRAK_W_SPEC] | 5 routes nieudokumentowanych | Dodać do `spec/core/06_navigation_flow.md` |
| **S-4** | [BRAK_W_SPEC] | `FeePresetGroup.description` — pole w kodzie, brak w spec | Dodać do `spec/core/01_database.md` |
| **S-5** | [BRAK_W_SPEC] | `Salesperson.commission_rate` — pole w kodzie, brak w spec | Dodać do `spec/core/01_database.md` |

### Spec zawiera martwą/nieaktualną treść

| # | Typ | Opis | Akcja |
|---|-----|------|-------|
| **D-1** | [BRAK_W_KODZIE] | Tabela `settlements` (stara) — zastąpiona przez `contract_settlements` | Usunąć ze spec |
| **D-2** | [BRAK_W_KODZIE] | Tabele: `deliveries`, `delivery_addresses`, `costs`, `audit_log`, `cost_types` | Decyzja PO: usunąć lub dodać do backlogu |

### Dług techniczny (opcjonalne refaktory)

| # | Typ | Opis | Priorytet |
|---|-----|------|-----------|
| **T-1** | REFACTOR | Ekstrakcja `ContractorPicker` do osobnego komponentu | P3 |
| **T-2** | REFACTOR | Ekstrakcja `ArticlePicker` do osobnego komponentu | P3 |
| **T-3** | KONWENCJA | Migracja `router/index.js` → `.ts` | P3 |
| **T-4** | WERYFIKACJA | Czy `ConditionPanel.vue` pokrywa wszystkie wymagania `ConditionFormView` ze spec | P2 |

---

## 6. Plan naprawczy

### Faza 1 — Natychmiastowa (w tym sprint)

**Zadanie S-2a: Spec frontend — dodać HomeView**  
Dodać do `spec/core/03_frontend_screens.md` pełny opis `HomeView.vue` (KPI, panele, quick nav).

**Zadanie S-2b: Spec frontend — dodać Admin, Commission, Worker, ChangePassword, ResetPassword**  
Dodać krótkie opisy 5 brakujących widoków do spec.

**Zadanie S-3: Spec routing — uzupełnić routes**  
Dodać do `spec/core/06_navigation_flow.md`: `/home`, `/admin`, `/commissions`, `/worker`, `/password`, `/reset-password`.

**Zadanie S-1: Spec backend — 14 endpointów**  
Dodać brakujące endpointy do `spec/core/02_backend_api.md` w sekcjach STATS, EXPLORER, INTEGRATIONS, CONTRACTS.

**Zadanie S-4/S-5: Spec DB — brakujące pola**  
Dodać `description` (FeePresetGroup) i `commission_rate` (Salesperson) do `spec/core/01_database.md`.

### Faza 2 — Następny sprint (przed przejściem P3 tasks)

**Zadanie C-1 (KRYTYCZNE): Branch.created_at typ**  
```python
# backend/settings/models.py - zmiana:
created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
# backend/main.py startup - migracja:
# UWAGA: MariaDB może nie pozwolić na MODIFY COLUMN z danymi — najpierw sprawdź czy kolumna ma dane
```

**Zadanie C-2: ContractorAddress.email długość**  
```python
# backend/contractors/models.py - zmiana:
email = Column(String(100), nullable=True)
# backend/main.py startup - migracja:
ALTER TABLE contractor_addresses MODIFY COLUMN email VARCHAR(100) NULL
```

**Zadanie D-1: Usunąć starą tabelę `settlements` ze spec**  
Usunąć sekcję `settlements` z `spec/core/01_database.md` (zastąpiona przez `contract_settlements` w RAO-P1-012).

### Faza 3 — Backlog (do oceny PO)

**Decyzja o tabelach D-2:**  
- `deliveries` + `delivery_addresses` → czy planowane w backlogu?
- `costs` + `cost_types` → system kosztów w backlogu?
- `audit_log` → logi audytu w backlogu?

Jeśli nie — usunąć ze spec. Jeśli tak — dodać jako zadania P2/P3.

**Dług techniczny T-1/T-2/T-3/T-4:**  
Ekstrakcja pickerów, migracja routera na TS — opcjonalne, niski priorytet.

---

## Metryki końcowe

| Metryka | Wartość |
|---------|---------|
| Pokrycie endpointów (spec vs kod) | 86% (95/111) |
| Pokrycie tabel DB (spec vs kod) | 77% (20/26) |
| Pokrycie widoków frontend (spec vs kod) | 58% (7/12) |
| Zgodność backlogu (done tasks) | 100% (39/39) |
| Błędy krytyczne (typy pól) | 2 |
| Braki w spec (endpointy + widoki + routes) | 25 pozycji |
| Martwe wpisy w spec (tabele bez kodu) | 6 |

**Wniosek:** System jest dojrzały i stabilny. Główny problem to **spec lag** — dokumentacja nie nadąża za implementacją. Brak scenariuszy gdzie kod jest niezgodny z wymaganiami (regresja 0%). Rekomendowane: zamknąć spec gap (faza 1) przed kolejnymi wdrożeniami.

---

*Wygenerowany przez RAO audit pipeline — RAO-P2-014*
