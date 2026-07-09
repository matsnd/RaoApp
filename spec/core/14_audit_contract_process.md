# Audyt Procesowy: Dodawanie Umowy — Stara vs Nowa Aplikacja

> **Data:** 2026-03-15 | **Wersja:** 1.0  
> **Metoda:** Cross-role team analysis (Analityk Biznesowy + DBA + UX + Frontend Architect + Backend Architect)

> ⚠️ **ARCHIWUM** — Wszystkie P0 i większość P1 z tego dokumentu zostały zaimplementowane do 2026-04-07.  
> **Aktualny backlog → patrz `backlog/BACKLOG.md`**

---

## 1. Stary Proces (WinForms FormU4.cs) — Pełna Rekonstrukcja

### Krok po kroku — co działo się w starej aplikacji:

| # | Akcja użytkownika | Co się działo pod spodem | Tabele DB |
|---|---|---|---|
| 1 | Klik [+] na Dashboard | Otwarcie FormU4, tryb "nowa" | — |
| 2 | Auto-numer | `SELECT numeracja FROM firma` + `SELECT max(autonumer) FROM umowa2` → format `S001/2026` | `firma`, `umowa2` |
| 3 | Typ umowy S/U | Dropdown, wpływa na numer i szablony usług | — |
| 4 | Wybór kontrahenta | FormKwybor (picker) → snapshot nazwy do `umowa2.nazwa` | `kontrahent2` via VIEW `kontrahenci` |
| 5 | Po wyborze kontrahenta | Auto-ładowanie adresów do dropdown | `adres WHERE id_kontrahenta=X` |
| 6 | Wybór adresu dostawy | Dropdown adresów kontrahenta → auto-fill pól adresu | `adres` |
| 7 | Reverse geocoding | Nominatim API → zapis współrzędnych | `dostawa` (lat/lng) |
| 8 | Handlowiec | Dropdown (aktywni) | `handlowiec WHERE aktywny=1` |
| 9 | Oddział | Dropdown | `oddzial` |
| 10 | Daty od/do | Kalendarz 2-miesieczny (wizualny widget) | — |
| 11 | Osoby kontaktowe | 2× (imię + telefon + checkbox "reprezentująca"/"kontaktowa") | `umowa2.osoba1/2, telefon1/2` |
| 12 | Usługi dodatkowe | Auto-wczytane z `firma.uslugi1` (S) lub `firma.uslugi2` (U) jako blok tekstowy | `firma` → `umowa2.oplaty` |
| 13 | Dni robocze/tyg | Pole numeryczne, default 6 | `umowa2` |
| 14 | Email + telefon | Pola tekstowe | `umowa2` |
| 15 | **[+] Pozycja** | FormAwybor → lista artykułów z **kolorowym oznaczeniem zajętości** (Moccasin = na aktywnej umowie) | VIEW `artykuly`/`artykulyy` |
| 16 | Sprawdzenie dostępności | Procedura `sprDostepnosc(id, data_od, data_do)` | `umowa_pozycja3` |
| 17 | Wybór artykułu | + ustawienie: **data dostawy**, **liczba dni**, opcjonalny **dostawca** | `umowa_pozycja3` INSERT |
| 18 | Duplikacja artykułu | Przycisk w pickerze → `CALL duplikujartykul2(id)` | `artykul3` |
| 19 | **[+] Warunki** | FormW → dedykowany formularz warunków rozliczenia | — |
| 20 | Nawigacja [<][>] | Przełączanie między pozycjami umowy | `pozycje2` VIEW |
| 21 | Typ stawki | Dropdown z tabeli `stawka` (excl. id=4) | `stawka` |
| 22 | Billing frequency | Dropdown: tygodniowo / dziennie / godzinowo / miesięcznie | `umowa_pozycja3.ROZLICZANIE` |
| 23 | Billing unit | Dropdown: tydzień / doba / godzina / miesiąc | `umowa_pozycja3.OPLATAZA` |
| 24 | Progi cenowe | Dodawanie: okres, opłata1, opłata2, minimum | `umowa_pozycja2_warunek` |
| 25 | Auto-opis warunku | Generowany tekst: "stawka 5000 zł/tyg. do 5 tygodni" | UI (tbxwarunek) |
| 26 | **Auto-kalkulacja** | Wartość pozycji obliczana on-the-fly z warunków (progowy algorytm) | Logika w RAM |
| 27 | **Total value** | Suma wartości pozycji → pole "Wartość" | wyświetlane, nie persistowane |
| 28 | **Pozostało** | `total - prepayment - invoice` → pole "Pozostało" | wyświetlane, nie persistowane |
| 29 | Zapis | INSERT/UPDATE umowa2 + umowa_oddzial + dostawa | `umowa2`, `umowa_oddzial`, `dostawa` |

---

## 2. Nowy Proces (Vue.js ContractFormView.vue + FastAPI) — Stan Obecny

### Co jest zaimplementowane:

| Element | Status | Uwagi |
|---------|--------|-------|
| Typ umowy (S/U) | ✅ | Dropdown, disabled w edycji |
| Auto-numer | ✅ | `generate_contract_number()` w backend |
| Kontrahent picker | ✅ | Modal z wyszukiwaniem |
| Handlowiec dropdown | ✅ | Z `settingsStore.salespeople` |
| Daty od/do | ✅ | Zwykłe `<input type="date">` |
| Adres dostawy | ⚠️ | **Tylko text input** — brak dropdown adresów kontrahenta |
| Osoby kontaktowe 2× | ✅ | Imię + tel + checkbox "Drukuj" |
| Wartość (zł) | ⚠️ | **Ręczny input!** Brak auto-kalkulacji |
| Przedpłata + Faktura | ✅ | Pola numeryczne |
| Uwagi | ✅ | Textarea |
| Pozycje — lista | ✅ | Tabela z CRUD |
| Pozycje — artykuł picker | ✅ | Modal z wyszukiwaniem |
| Pozycje — rental_days | ✅ | W modalu |
| Pozycje — quantity, unit_price | ✅ | W modalu |
| Usługi dodatkowe | ✅ | Read-only tabela, auto-kopiowanie z szablonów |
| Raport PDF | ✅ | Przyciski w toolbar + context menu |
| Kaskadowe usuwanie | ✅ | Backend: conditions → positions → fees → contract |

---

## 3. 🔴 KRYTYCZNE BRAKI — Cross-Role Team Discussion

### 🔴 ANALITYK BIZNESOWY mówi:

> **"Bez UI warunków rozliczenia cały system jest procesowo bezużyteczny."**
> 
> Warunki rozliczenia (`position_conditions`) to **jedyne źródło prawdy o przychodach** w systemie.  
> Formuła: `revenue = SUM(rate1 × period_count)` generuje ~4 mln zł przychodów w starej bazie.
> 
> Obecny stan:
> - Backend ma pełne CRUD endpointy dla warunków ✅
> - Frontend **NIE MA żadnego komponentu** do zarządzania warunkami ❌
> - `total_value` jest wpisywane ręcznie (zawsze 0 dla nowych umów) ❌
> - Raporty PDF nie mają danych cenowych z warunków ❌
> - Statystyki (stats endpoints) zwracają poprawne wartości bo czytają z `rate1`, ale ręczny `total_value` na liście umów nie zgadza się z rzeczywistością ❌

### 🔴 DBA / ARCHITEKT DANYCH mówi:

> **"6 tabel ze specyfikacji DDL nie ma modeli w backendzie."**
>
> | Tabela z DDL | Model w backendzie | Endpoint |
> |---|---|---|
> | `deliveries` | ❌ BRAK | ❌ BRAK |
> | `delivery_addresses` | ❌ BRAK | ❌ BRAK |
> | `costs` | ❌ BRAK | ❌ BRAK |
> | `cost_types` | ❌ BRAK | ❌ BRAK |
> | `settlements` | ❌ BRAK | ❌ BRAK |
> | `audit_log` | ❌ BRAK | ❌ BRAK |
>
> Ale **KRYTYCZNIEJSZE** jest to, że `calculate_contract_value()` ze spec `04_BUSINESS_LOGIC.md` **nigdzie nie jest wywoływane** przy zapisie umowy ani po zmianie warunków. `total_value` powinno być przeliczane automatycznie.

### 🔴 UX DESIGNER mówi:

> **"Formularz umowy ma 2 z 4 głównych sekcji z FormU4."**
>
> Stary FormU4 miał 4 logiczne sekcje:
> 1. ✅ Nagłówek (dane umowy) — jest, choć niekompletny
> 2. ✅ Pozycje — jest, ale modal ma 6 pól zamiast 11
> 3. ❌ **Warunki rozliczenia (FormW)** — **KOMPLETNIE BRAK**
> 4. ⚠️ Usługi dodatkowe — read-only, brak edycji
>
> Modal pozycji — brakujące pola:
> | Pole | W backend schema | W UI modal |
> |------|-----------------|------------|
> | `billing_frequency` | ✅ | ❌ |
> | `billing_unit` | ✅ | ❌ |
> | `rate_type_id` | ✅ | ❌ |
> | `supplier_id` | ✅ | ❌ |
> | `delivery_date` | ✅ | ❌ |
> | `costs` | ✅ | ❌ |

### 🟡 FRONTEND ARCHITECT mówi:

> **"Store `contracts.js` ma już kompletne API methods — problem jest TYLKO w braku komponentów Vue."**
>
> Istniejące (nieużywane) metody w store:
> - `fetchConditions(contractId, posId)` ✅
> - `createCondition(contractId, posId, payload)` ✅
> - `updateCondition(contractId, posId, condId, payload)` ✅
> - `deleteCondition(contractId, posId, condId)` ✅
>
> Potrzebne nowe komponenty:
> 1. **`ConditionPanel.vue`** — formularz warunków z progami (odpowiednik FormW)
> 2. Rozszerzenie **Position Modal** o 6 brakujących pól
> 3. **Computed `remaining`** = total - prepayment - invoice
> 4. **`ContractorAddressPicker`** — dropdown adresów przy wyborze kontrahenta
> 5. Rozszerzenie **Article Picker** o status dostępności (kolor/badge)

### 🟡 BACKEND ARCHITECT mówi:

> **"Backend CRUD jest kompletny. Brakuje 2 endpoint + 1 bug."**
>
> Brakuje:
> 1. **`POST /contracts/{id}/recalculate`** — przelicz `total_value` z warunków
> 2. **Walidacja NIP** (checksum) — spec `04_BUSINESS_LOGIC.md` sekcja 13
>
> Bug:
> - `DashboardView.vue` wysyła `params.type` ale backend `contracts/router.py` filtruje po `contract_type`. Param się nie matchuje → filtr typu nie działa.

---

## 4. Priorytetyzacja Implementacji

### 🔴 P0 — BLOCKER (bez tego app jest bezużyteczna biznesowo)

| # | Zadanie | Gdzie | Effort |
|---|---------|-------|--------|
| 1 | **UI Warunków Rozliczenia** — nowy komponent ConditionPanel z progami, typem stawki, billing freq/unit, auto-opis | Frontend | L |
| 2 | **Auto-kalkulacja total_value** — endpoint + trigger po zmianach warunków | Backend + Frontend | M |
| 3 | **Rozszerzenie modalu pozycji** — dodanie billing_frequency, billing_unit, rate_type_id, delivery_date, supplier_id | Frontend | S |

### 🟡 P1 — WAŻNE (pełna funkcjonalność procesowa)

| # | Zadanie | Gdzie | Effort |
|---|---------|-------|--------|
| 4 | Dropdown adresów kontrahenta w formularzu umowy | Frontend | S |
| 5 | Pole computed "Pozostało" (total - prepay - invoice) | Frontend | XS |
| 6 | Branch/oddział selector w formularzu | Frontend | XS |
| 7 | Edycja/dodawanie/usuwanie service fees w formularzu | Frontend | M |
| 8 | Oznaczenie dostępności artykułów w pickerze (badge/kolor) | Frontend | S |
| 9 | Sprawdzanie dostępności przy dodawaniu pozycji | Frontend + Backend | S |
| 10 | Fix: param `type` → `contract_type` w DashboardView | Frontend | XS |

### 🟢 P2 — ULEPSZENIA

| # | Zadanie | Gdzie | Effort |
|---|---------|-------|--------|
| 11 | Duplikacja artykułu z poziomu pickera | Frontend | S |
| 12 | NIP validation (checksum) w create/update contractor | Backend | XS |
| 13 | Modele + CRUD: deliveries, delivery_addresses | Backend | M |
| 14 | Modele + CRUD: costs, cost_types | Backend | M |
| 15 | Kalendarz 2-miesieczny (zamiast date inputs) | Frontend | M |
| 16 | Auto-generowanie opisu warunku (tekst "stawka X zł/tyg.") | Frontend + Backend | S |
| 17 | Audit log (zdarzenia systemowe) | Backend | M |

---

## 5. Diagram: Stary vs Nowy Flow

```
STARY (FormU4.cs):
═══════════════════════════════════════════════════════
Dashboard [+] → FormU4 (nagłówek + kalendarz + finanse)
                   ├── Kontrahent picker → auto-load adresów
                   ├── Adres dropdown → reverse geocoding
                   ├── Oddział dropdown
                   ├── Handlowiec dropdown
                   ├── [+] Pozycja → FormAwybor (z availability check)
                   │       └── artykuł + data_dostawy + dni + dostawca
                   ├── [+] Warunki → FormW (dedykowany formularz)
                   │       ├── [<][>] nawigacja między pozycjami
                   │       ├── Typ stawki + billing freq/unit
                   │       ├── Progi (okres, rate1, rate2, min)
                   │       └── Auto-opis + auto-kalkulacja
                   ├── AUTO total_value (z warunków)
                   ├── AUTO "Pozostało" (total - prepay - invoice)
                   └── [Zapisz] → INSERT/UPDATE

NOWY (ContractFormView.vue):
═══════════════════════════════════════════════════════
Dashboard [+] → ContractFormView (nagłówek)
                   ├── Kontrahent picker modal
                   ├── Adres dostawy (text input) ← ⚠️ brak dropdown
                   ├── ❌ brak oddział
                   ├── Handlowiec dropdown
                   ├── [+] Pozycja → modal (6/11 pól)
                   │       └── artykuł + typ + dni + ilość + cena + opis
                   ├── ❌ BRAK UI WARUNKÓW
                   ├── ❌ RĘCZNY total_value
                   ├── ❌ brak "Pozostało"
                   └── [Zapisz] → POST/PUT
```

---

## 6. Rekomendacja Kolejności Implementacji

**Sprint 1 (P0 — unblock core process):**
1. ConditionPanel.vue + integracja w ContractFormView
2. Rozszerzenie position modal o brakujące pola
3. Auto-recalculate total_value endpoint + frontend trigger

**Sprint 2 (P1 — production-ready):**
4. Contractor address picker
5. Branch selector + "Pozostało" computed
6. Service fees CRUD w formularzu
7. Article availability w pickerze
8. Bug fix: contract_type filter

**Sprint 3 (P2 — polish):**
9. Brakujące tabele/modele
10. NIP validation
11. UX improvements (kalendarz, duplikacja, auto-opisy)
