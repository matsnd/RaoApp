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
| #9 | Protokół usługi — ewidencja godzin | Ważny klient | ✅ Zrobione | Nowa tabela `service_hours`, API, frontend, PDF | Kompletna funkcjonalność dla umów typu U |
| #3 | Kwota tankowania — default 200 zł | Dobry dodatek | ✅ Zrobione | `SettingsView.vue:422-432` | Auto-ustawianie 200 zł dla "Tankowanie/Paliwo" |
| #8 | Picker artykułów — filtrowanie po typie umowy | Dobry dodatek | ✅ Zrobione | `ContractFormView.vue:692,878` | `is_service` param zależny od `contract_type` |

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

### Faza 4: P3 + Dodatki
- [ ] **B12-B17** — Keyboard shortcuts, empty states, NProgress, testy
- [ ] **#3** — Kwota tankowania default 200 zł
- [ ] **#8** — Filtrowanie artykułów po typie umowy

---

## Statystyki

| Metryka | Wartość |
|---------|---------|
| Zadań zrealizowanych | 7 |
| Zadań oczekujących | 14 |
| Blokerów | 0 |

**Szczegóły zrealizowanych:**
- B1 (P1 filtr dat) ✅
- #1, #4, #5, #6, #7, #9 (Ważne klienta — wszystkie zrobione!) ✅

**Faza 1 (P1 + Ważne klienta): KOMPLETNA** ✅

---

> **Następny update:** Po zakończeniu każdego zadania
