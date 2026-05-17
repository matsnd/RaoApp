# Refinement Plan — 2026-05-17

## Podsumowanie

Przeanalizowano 11 zadań z instrukcji refinement. Większość już istniała w backlog (RAO-P1-008, RAO-P1-009, RAO-P1-010, RAO-P1-011, RAO-P1-012, RAO-P1-013). Dodano 5 nowych zadań:
- RAO-P1-013: Poprawa tekstu checkboxa ukrywania adresu
- RAO-P1-014: Poprawa checkboxa podpisów  
- RAO-P1-015: Format OWN dokumentu — 2 strony
- RAO-P1-016: Rozszerzenie sekcji "Uwagi" o brakujące pola
- RAO-P1-017: Migracja kategorii maszyn z CSV + flaga archiwalna

## Podział zadań do agentów

### Zadania istniejące w backlog (zaktualizacja priorytetów)

| ID | Zadanie | Agent | Priorytet | Status |
|----|---------|-------|-----------|--------|
| RAO-P1-008 | Strukturalizacja adresów (kod pocztowy + miasto) | db-architect, backend-dev, frontend-dev | P1 | triaged |
| RAO-P1-009 | Weryfikacja PDF vs stara aplikacja | qa-engineer, frontend-dev | P1 | triaged |
| RAO-P1-010 | Tabela "Przy wydaniu / Przy odbiorze" | frontend-dev | P1 | triaged |
| RAO-P1-011 | Usługi dodatkowe zesłownikowane z artykułami | db-architect, backend-dev | P1 | triaged |
| RAO-P1-012 | Panel rozliczenie umowy | product-owner, db-architect, backend-dev, frontend-dev | P1 | triaged |
| RAO-P1-013 (stare ID) | Refactor prowizji — od realnego zarobku | backend-dev | P1 | triaged |

### Nowe zadania dodane do backlog

| ID | Zadanie | Agent | Priorytet | Status |
|----|---------|-------|-----------|--------|
| RAO-P1-013 | Poprawa tekstu checkboxa ukrywania adresu | frontend-dev, ux-designer | P1 | triaged |
| RAO-P1-014 | Poprawa checkboxa "Na 1 stronie nie bez podpisów" | frontend-dev, ux-designer | P1 | triaged |
| RAO-P1-015 | Format OWN dokumentu — 2 strony | frontend-dev | P1 | triaged |
| RAO-P1-016 | Rozszerzenie sekcji "Uwagi" o brakujące pola | qa-engineer, frontend-dev | P1 | triaged |
| RAO-P1-017 | Migracja kategorii maszyn z CSV + flaga archiwalna | db-architect, backend-dev | P1 | triaged |

## Zalecenia wykonywania (kolejność i zależności)

### Faza 1: DB i struktura (blokuje inne zadania)
1. **RAO-P1-017** (Migracja kategorii maszyn) — db-architect, backend-dev
   - Musi być wykonane przed statystykami
   - Flaga archiwalna krytyczna dla raportów

2. **RAO-P1-008** (Strukturalizacja adresów) — db-architect, backend-dev, frontend-dev
   - Zależy od RAO-P1-005 (ekstrakcja miast) — już w backlog
   - Krytyczne dla statystyk

3. **RAO-P1-011** (Usługi dodatkowe zesłownikowane) — db-architect, backend-dev
   - Musi być przed RAO-P1-012 (panel rozliczenia)

### Faza 2: Panel rozliczenia (blokuje prowizje)
4. **RAO-P1-012** (Panel rozliczenie umowy) — product-owner, db-architect, backend-dev, frontend-dev
   - Product Owner musi zdefiniować nazwy pól kosztów
   - Blokuje RAO-P1-018 (refactor prowizji)

### Faza 3: Prowizje
5. **RAO-P1-018** (Refactor prowizji) — backend-dev
   - Zależy od RAO-P1-012 (dane settlement)

### Faza 4: PDF i dokumenty (równolegle)
6. **RAO-P1-015** (Format OWN dokumentu) — frontend-dev
   - Niezależne od innych

7. **RAO-P1-009** (Weryfikacja PDF vs stara aplikacja) — qa-engineer, frontend-dev
   - Może być równolegle z innymi PDF

8. **RAO-P1-010** (Tabela Przy wydaniu/Przy odbiorze) — frontend-dev
   - Niezależne od innych

### Faza 5: UX/UI poprawki (równolegle)
9. **RAO-P1-013** (Poprawa tekstu checkboxa ukrywania) — frontend-dev, ux-designer
   - Szybkie zadanie (30 min)

10. **RAO-P1-014** (Poprawa checkboxa podpisów) — frontend-dev, ux-designer
    - Szybkie zadanie (30 min)

11. **RAO-P1-016** (Rozszerzenie sekcji "Uwagi") — qa-engineer, frontend-dev
    - Zależy od RAO-P1-004 (sekcja uwag już częściowo istnieje)

## Vision AI Analysis

Przeanalizowano 3 screenshoty:
1. **Screenshot 1 (220919.png)**: Checkbox ukrywania adresu — tekst za długi, błędy ortograficzne, język potoczny
2. **Screenshot 2 (221011.png)**: Checkbox podpisów — podwójna negacja niezrozumiała
3. **Screenshot 3 (221042.png)**: OWN dokument — nie mieści się na 2 stronach, punkt §3 musi być po prawej

## Rekomendacje dla zespołu

### Tech Lead
- Koordynacja zależności między zadaniami
- Priorytety: Faza 1 (DB) → Faza 2 (Settlements) → Faza 3 (Prowizje) → Faza 4-5 (PDF/UX równolegle)

### Product Owner
- **RAO-P1-012**: Zdefiniowanie nazw pól kosztów (priorytet — blokuje prowizje)
- Nazwy pól: "Koszt faktura", "Koszt własny", "Marża", "Koszt paliwa", "Koszt transportu"

### DB Architect
- **RAO-P1-017**: Migracja kategorii z CSV + SQL — krytyczne dla statystyk
- **RAO-P1-008**: Strukturalizacja adresów — słownikowanie kodów pocztowych
- **RAO-P1-011**: Usługi dodatkowe z FK do articles

### Backend Dev
- **RAO-P1-017**: Skrypt migracji kategorii
- **RAO-P1-008**: Skrypt ekstrakcji kodu pocztowego + słownikowanie
- **RAO-P1-011**: Zmiana logiki szablonów usług
- **RAO-P1-018**: Refactor formuły prowizji

### Frontend Dev
- **RAO-P1-008**: Formularz z polami kod pocztowy + miasto + adres
- **RAO-P1-010**: Tabela "Przy wydaniu/Przy odbiorze" w protokole
- **RAO-P1-012**: Panel rozliczenia z tabelą pozycji
- **RAO-P1-013**: Poprawa tekstu checkboxa
- **RAO-P1-014**: Poprawa checkboxa podpisów
- **RAO-P1-015**: Format OWN dokumentu (2 strony)
- **RAO-P1-016**: Rozszerzenie sekcji uwag

### UX Designer
- **RAO-P1-013**: Weryfikacja nowego tekstu checkboxa
- **RAO-P1-014**: Weryfikacja nowego tekstu checkboxa podpisów

### UI Designer
- **RAO-P1-015**: Stylowanie OWN dokumentu zgodnie z design systemem
- **RAO-P1-010**: Stylowanie tabeli "Przy wydaniu/Przy odbiorze"

### QA Engineer
- **RAO-P1-009**: Analiza starej aplikacji WinForms (C:\projects\repos\AppRao)
- **RAO-P1-016**: Identyfikacja brakujących pól w sekcji uwag
- Weryfikacja wszystkich zmian PDF

## Szacowanie czasu

| Faza | Zadania | Szacowany czas |
|------|---------|----------------|
| Faza 1: DB | RAO-P1-017, RAO-P1-008, RAO-P1-011 | 32h |
| Faza 2: Settlements | RAO-P1-012 | 16h |
| Faza 3: Prowizje | RAO-P1-018 | 4h |
| Faza 4: PDF | RAO-P1-015, RAO-P1-009, RAO-P1-010 | 11h |
| Faza 5: UX/UI | RAO-P1-013, RAO-P1-014, RAO-P1-016 | 4h |
| **SUMA** | **11 zadań** | **~67h** |

## Ryzyka i blokery

### Krytyczne blokery:
- **RAO-P1-012** blokuje **RAO-P1-018** (panel rozliczenia potrzebny do refactoru prowizji)
- **RAO-P1-017** blokuje poprawne statystyki (dopóki nie ma kategorii)

### Ryzyka:
- **RAO-P1-017**: Migracja z CSV+SQL — ryzyko błędnych mapowań kategorii
- **RAO-P1-008**: Słownikowanie kodów pocztowych — ryzyko błędnych miast
- **RAO-P1-011**: Mapowanie stringów na FK — ryzyko utraty danych przy migracji

## Data refinement
2026-05-17

## Status backlog
Zaktualizowano BACKLOG.md o 5 nowych zadań (RAO-P1-013 do RAO-P1-017). Wszystkie 11 zadań z instrukcji refinement jest teraz w backlog z przypisanymi agentami i zależnościami.