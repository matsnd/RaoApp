# UX/GUI Propozycje Usprawnień

> ⚠️ **ARCHIWUM** — Dokument z 2026-03-15. Większość pozycji zrealizowana.  
> **Aktualny backlog → patrz `backlog/BACKLOG.md`**

## Zrealizowane (sprint S1+S2+S3 — do 2026-04-07)

| # | Opis | Gdzie | Status |
|---|------|-------|--------|
| U1 | Kolorowanie wierszy umów kończących się / przeterminowanych | DashboardView — lista umów | ✅ Zrobione |
| U2 | Chip z liczbą dni przy dacie końca (≤14 dni) | DashboardView — kolumna "Data do" | ✅ Zrobione |
| U3 | Panel pracownika (4 raporty) | WorkerView | ✅ Zrobione |
| U4 | Widok prowizji z filtrem daty | CommissionView | ✅ Zrobione |

---

## Priorytet P1 — Krytyczne (blokują produkcję)

### U5: Brak UI warunków cenowych w formularzu umowy
**Problem:** Pozycje umowy mają warunki (`position_conditions`) — serce systemu cenowego — ale nie ma żadnego UI do ich dodawania/edycji.  
**Propozycja:** Modal "Warunki pozycji" z tabelą:
```
| Typ stawki | Opis | Opłata 1 | Opłata 2 | Okres | Min |
```
Przycisk "+ Dodaj warunek" poniżej każdej pozycji w formularzu umowy.  
**Wpływ:** Bez tego handlowcy nie mogą poprawnie wprowadzić umowy.

### U6: Auto-kalkulacja wartości umowy
**Problem:** `contract.total_value` = 0 dla wszystkich umów. Endpoint `/recalculate` istnieje ale nie jest wywoływany.  
**Propozycja:** Wywołaj `PATCH /contracts/{id}/recalculate` po każdym zapisie pozycji/warunków i wyświetl obliczoną wartość w nagłówku formularza umowy.

### U7: Brak 6 pól w modalu dodawania pozycji
**Problem:** Modal pozycji nie zawiera: `rental_type`, `costs`, `billing_frequency`, `billing_unit`, `supplier_id`, `delivery_date`.  
**Propozycja:** Rozbuduj modal o te pola. Wystarczą proste inputy/selecty.

---

## Priorytet P2 — Produkcja lepsza

### U8: "Dodaj umowę" z poziomu karty kontrahenta
**Problem:** Brak przycisku CTA na stronie kontrahenta.  
**Propozycja:** Dodaj button w `ContractorFormView`: `router.push('/contracts/new?contractor_id=X')` + pre-fill.

### U9: Autouzupełnienie adresu po GUS
**Problem:** GUS pobiera dane firmy ale nie uzupełnia adresu kontrahenta automatycznie.  
**Propozycja:** Po odpowiedzi GUS w `ContractorFormView` — ustaw `city`, `street`, `postal_code` z odpowiedzi.

### U10: Numer telefonu stacjonarny w formularzu kontrahenta
**Problem:** Pole `landline_phone` jest w modelu ale nie ma go w formularzu.  
**Propozycja:** Dodaj pole "Telefon stac." między "Telefon 2" a "Email" w `ContractorFormView`.

### U11: Podgląd PDF przed pobraniem
**Problem:** Kliknięcie "Drukuj" natychmiast pobiera plik bez podglądu.  
**Propozycja:** Otwórz PDF w nowej karcie przeglądarki zamiast pobierać (`window.open(blob URL, '_blank')`).

### U12: Edycja/usuwanie kategorii, typów stawek w Ustawieniach
**Problem:** Można dodać, ale nie edytować ani usunąć kategorii i typów stawek.  
**Propozycja:** Dodaj przyciski edytuj/usuń z potwierdzeniem w każdej sekcji Ustawień.

---

## Priorytet P3 — Polishing

### U13: Keyboard shortcuts
| Skrót | Akcja |
|-------|-------|
| `Ctrl+N` | Nowy rekord (kontekstowo) |
| `Escape` | Zamknij modal/menu |
| `Enter` na wierszu | Otwórz edycję |
| `Del` na zaznaczonym | Usuń z potwierdzeniem |

### U14: Pusta strona startowa — co teraz?
**Problem:** Po zalogowaniu lista umów jest pusta jeśli nie ma danych.  
**Propozycja:** Empty state z CTA: "Utwórz pierwszą umowę →"

### U15: Wskaźnik ładowania globalny
**Problem:** Każdy widok ma własny spinner; brak globalnego feedbacku.  
**Propozycja:** Pasek postępu w górze (NProgress.js) odpalany na każde zapytanie API.

### U16: Wyszukiwanie globalne
**Problem:** Wyszukiwanie działa per sekcja, brak globalnego "szukaj wszędzie".  
**Propozycja:** Skrót `Ctrl+K` — modal z full-text search po umowach, kontrahentach, artykułach jednocześnie.

### U17: Logo firmy w nagłówku sidebar
**Problem:** Sidebar ma "TOOLSMART" hard-coded.  
**Propozycja:** Pobierz `company.logo` z API i wyświetl jako `<img>` zamiast tekstu.

---

## Sprint plan

| Sprint | Zadania |
|--------|---------|
| **S1** | U5 (warunki), U6 (auto-calc), U7 (pola pozycji) — P0 |
| **S2** | U8 (add contract from contractor), U9 (GUS auto-address), U10 (landline), U11 (PDF preview), U12 (edit/delete settings) |
| **S3** | U13 (shortcuts), U14 (empty state), U15 (global loading), U16 (global search), U17 (logo) |

---

## Notatka dla Product Ownera

Priorytety P1 (U5, U6, U7) są **blokerami produkcyjnymi** — bez nich handlowcy nie mogą prawidłowo wprowadzić umowy z warunkami cenowymi. To jest najważniejszy sprint.

Koszt szacunkowy:
- U5 + U6 + U7: ~2-3 dni dev
- U8 + U9 + U10 + U11 + U12: ~1-2 dni dev  
- Sprint 3: ~1 dzień dev
