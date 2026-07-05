# Vision Report

**Plik:** c:/projects/repos/RaoApp_new/e2e/screenshots/ux-review/05-contractor-form-new-empty.png
**Model:** claude-opus-4-5 (anthropic) [fallback z free model: empty/thin response]
**Data:** 2026-07-05T10:43:42.717Z

# Analiza UX/UI: Formularz "Nowy kontrahent"

## 📊 Ogólna ocena: **6.5/10**

---

## ✅ Co jest OK

### Układ i struktura
- **Logiczny podział sekcji** - "Dane kontrahenta", "Adres główny", "Kontakt", "Adresy dostawy" → dobra hierarchia informacji
- **Dwukolumnowy layout pól** - efektywne wykorzystanie przestrzeni
- **Nagłówki sekcji** wyraźnie oddzielone (navy background)
- **Przycisk GUS przy NIP** - smart feature, automatyczne pobieranie danych

### Zgodność z Design System
- ✅ Kolor primary #1D2B53 użyty poprawnie w nagłówkach sekcji
- ✅ Jasne tło formularza (zgodne z #F8F9FA/#FFFFFF)
- ✅ Gwiazdka przy polu wymaganym "Pełna nazwa *"

---

## ⚠️ Co wymaga poprawy

### 1. **Border-radius - NIEZGODNOŚĆ z DS**
```
Aktualnie: ~4-6px (ostre rogi)
Powinno być: 12px (zgodnie z design system)
```
Dotyczy: wszystkich inputów, przycisków, kart sekcji

### 2. **Walidacja - brak wizualnych wskazówek**

| Problem | Rozwiązanie |
|---------|-------------|
| Tylko 1 pole oznaczone jako wymagane (*) | Oznaczyć wszystkie required fields |
| Brak inline validation | Dodać real-time walidację NIP, PESEL, REGON |
| Placeholder "0000000000" w NIP | Użyć maski formatu: `___-___-__-__` |
| Placeholder "00-000" w kodzie pocztowym | OK, ale dodać maskę input |

### 3. **Czytelność i typografia**

```diff
- Labele zbyt małe i słabo kontrastowe (szary na białym)
+ Zwiększyć font-weight labeli do 500-600
+ Poprawić kontrast (min. 4.5:1 WCAG AA)
```

### 4. **Spójność wizualna**

| Element | Problem |
|---------|---------|
| Przycisk "GUS" | Inny styl niż reszta (niebieski badge vs. navy system) |
| Sekcja "Adresy dostawy" | Pusta przestrzeń - brak CTA do dodania adresu |
| Komunikat "Zapisz kontrahenta, aby dodać adresy" | Słabo widoczny, brak ikony info |

---

## 🐛 Błędy wizualne

### Krytyczne
1. **Brak przycisku "Anuluj"** obok "Zapisz" - użytkownik ma tylko "Wstecz"
2. **Przycisk "Zapisz"** - zbyt mały kontrast, brak hover state widocznego

### Średnie
3. **Pola REGON i PESEL** w jednej linii - mylące (firma ma REGON, osoba PESEL, rzadko oba)
4. **Brak separacji wizualnej** między sekcjami (tylko nagłówki)
5. **Ikona "Wstecz"** - niespójna z resztą UI (outline style)

### Drobne
6. **Nierówne odstępy** między polami w sekcji "Kontakt"
7. **Brak tooltipów** przy polach specjalistycznych (NIP, REGON)

---

## 🎯 Rekomendacje priorytetowe

```
1. [WYSOKI] Ujednolicić border-radius do 12px
2. [WYSOKI] Dod
