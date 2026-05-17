# Raport realizacji Backlogu — RAO App

> **Status:** W trakcie  
> **Rozpoczęcie:** 2026-04-08  
> **Metoda:** /cross-role-audit + /agent-loop-do-skutku

---

## Zadania zrealizowane

| # | Zadanie | Priorytet | Status | Commit/Plik | Uwagi |
|---|---------|-----------|--------|-------------|-------|
| B1 | Filtrowanie po zakresie dat w Dashboard | P1 | ✅ Zrobione | `DashboardView.vue:26-27,253-254` | dateFrom/dateTo + params do API |
| #1 | Adres dostawy — pole wielolinijkowe | Ważny klient | ✅ Zrobione | `ContractFormView.vue`, szablony PDF | textarea rows=3 + white-space: pre-wrap w PDF |
| #4 | Adres dostawy — rozdzielenie umowa vs protokół | Ważny klient | ✅ Zrobione | `contract.html`, `contract_u.html` | Ukryte na umowie (display:none), widoczne na protokole |
| #5 | Usługi dodatkowe — format wyświetlania kwot | Ważny klient | ✅ Zrobione | `ContractFormView.vue:587` | formatDescription() zamieniający $1, $2 na kwoty z walutą |
| #6 | Podpisy na umowie — układ stron | Ważny klient | ✅ Zrobione | `contract.html`, `contract_u.html` | Usunięto padding-top:40px z komórki podpisu Najemcy |
| #7 | Sekcja "Uwagi" w umowie | Ważny klient | ✅ Zrobione | `ContractFormView.vue:140-142` | Pole textarea już istniało, działa z API |
| #9 | Protokół usługi — ewidencja godzin (FORMULARZ PAPIEROWY) | Ważny klient | ✅ Zrobione | `protocol_zo_u.html` — tabela do ręcznego wypełnienia | Zmiana z systemu informatycznego na formularz papierowy |
| #3 | Kwota tankowania — default 200 zł | Dobry dodatek | ✅ Zrobione | `SettingsView.vue` — watch na nazwę pozycji | Auto-ustawianie 200 zł dla "Tankowanie/Paliwo/Paliw" |
| #8 | Picker artykułów — filtrowanie po typie umowy | Dobry dodatek | ✅ Zrobione | `ContractFormView.vue` — param `is_service` w API | Filtr `is_service` zależny od `contract_type` ('U'/'S') |
| #10-#15 | Nowe zgłoszenia klienta (UX raportów, numery wewnętrzne, statystyki, rezerwacje) | Backlog | ✅ Zrobione | `21_BACKLOG_CLIENT.md` | Dokumentacja 6 nowych zadań klienta |
| #10 | UX Raportów — rozdzielenie "teraz" od "okres" | Ważny klient | ✅ Zrobione | `ReportsSection.vue`, `stats.js` | Sekcja "Stan floty na żywo" niezależna od dat; "Analiza historyczna" z filtrami dat |
| — | Usunięcie zbędnego kodu service_hours | Refaktoryzacja | ✅ Zrobione | `router.py`, `models.py`, `schemas.py`, `ddl.sql`, `service.py`, `ContractFormView.vue` | Cleanup po zmianie #9 na formularz papierowy |
| #12-#14 | Eksplorator raportów — nowy widok | Ważny klient | ✅ Zrobione | `explorer/router.py`, `ReportsSection.vue:explorer` | 4 sub-taby: Wszystko, Maszyny, Usługi, Lokalizacje |
| #12 | Eksplorator — wyszukiwarka universalna | Ważny klient | ✅ Zrobione | `/explorer/search` + tab "Wszystko" | Search po maszynach, nr wewn., kontrahentach, miastach |
| #13 | Eksplorator — filtrowanie usług | Ważny klient | ✅ Zrobione | `/explorer/services` + tab "Usługi" | Agregacja przychodów per usługa (transport, mycie, tankowanie) |
| #14 | Eksplorator — lokalizacje | Ważny klient | ✅ Zrobione | `/explorer/locations` + tab "Lokalizacje" | Ranking miast po liczbie umów i przychodzie |
| — | Eksplorator — szczegóły maszyny | Ważny klient | ✅ Zrobione | `/explorer/machines/{id}` + tab "Maszyny" | Metryki: przychód, dni, średnia, % wykorzystania |
| — | Eksplorator — redesign UX (okres, usługi, maszyny) | Ważny klient | ✅ Zrobione | `ReportsSection.vue` (explorer section) | 1) Okres: pills + custom date od-do 2) Usługi: dynamiczne grupy z danych 3) Maszyny: typeahead search 4) Auto-reload na zmianę okresu |

---

## Zadania w trakcie

| # | Zadanie | Priorytet | Status | Bloker | Uwagi |
|---|---------|-----------|--------|--------|-------|

---

## Zadania do zrobienia

### Faza 1: P1 + Ważne klienta (pozostałe)
- [x] **B1** — Filtrowanie po zakresie dat w Dashboard (P1) ✅
- [x] **#1** — Adres dostawy — pole wielolinijkowe (Ważny klient) ✅
- [x] **#4** — Adres dostawy — rozdzielenie umowa vs protokół (Ważny klient) ✅
- [x] **#5** — Usługi dodatkowe — format wyświetlania kwot (Ważny klient) ✅
- [x] **#6** — Podpisy na umowie — układ stron (Ważny klient) ✅
- [x] **#7** — Sekcja "Uwagi" w umowie (pole `notes`) (Ważny klient) ✅
- [x] **#9** — Protokół usługi — ewidencja godzin (Ważny klient) ✅

### Faza 2: P2 Quick wins
- [ ] **B2** — Kolumna "Adres dostawy" w liście umów
- [ ] **B3** — Link "Zmień hasło" w sidebar
- [ ] **B4** — NIP validation (checksum)
- [ ] **B5** — Duplikacja artykułu z pickera
- [ ] **B11** — Auto-generowanie opisu warunku
- [ ] **B10** — Nominatim w formularzu umowy

### Faza 3: P2 Medium
- [ ] **B6** — Drag & drop reorder szablonów
- [ ] **B7** — Upload logo firmy
- [ ] **B8** — Export statystyk do CSV
- [ ] **B9** — Modele deliveries/costs/audit_log
- [ ] **#16** — Raportowanie prac (godzin operatorów) — Ewidencja godzin przepracowanych przez operatorów maszyn, podsumowanie per pracownik/okres

### Faza 4: P3 + Dodatki
- [ ] **B12-B17** — Keyboard shortcuts, empty states, NProgress, testy
- [ ] **#3** — Kwota tankowania default 200 zł
- [ ] **#8** — Filtrowanie artykułów po typie umowy

---

## Statystyki

| Metryka | Wartość |
|---------|---------|
| Zadań zrealizowanych | 8 |
| Zadań oczekujących | 14 |
| Blokerów | 0 |

**Szczegóły zrealizowanych:**
- B1 (P1 filtr dat) ✅
- #1, #4, #5, #6, #7, #9 (Ważne klienta — wszystkie zrobione!) ✅
- Eksplorator redesign UX (okres, usługi, maszyny, auto-reload) ✅

**Faza 1 (P1 + Ważne klienta): KOMPLETNA** ✅
**Eksplorator: KOMPLETNY** ✅

---

> **Następny update:** Po zakończeniu każdego zadania
