# Vision Report

**Plik:** c:/projects/repos/RaoApp_new/e2e/screenshots/ux-review/07-article-form-new-empty.png
**Model:** claude-opus-4-5 (anthropic) [fallback z free model: empty/thin response]
**Data:** 2026-07-05T11:00:18.979Z

# Analiza UX/UI Formularza "Nowy artykuł" - RAO

## 📊 Ocena ogólna: **6/10**

---

## ✅ Co jest OK

### Układ pól
- **Logiczny podział na sekcje** (dane podstawowe → techniczne → integracja)
- **Dwukolumnowy layout** dobrze wykorzystuje przestrzeń
- **Grupowanie powiązanych pól** (Marka/Model, Zasięg/Udźwig)

### Czytelność
- **Placeholdery z przykładami** ("np. 21.5", "np. 5.0") - pomocne
- **Jednostki w labelach** (m), (zł), (t) - jasne dla użytkownika
- **Wyraźne nagłówki sekcji** ("Dane techniczne", "Integracja Fakturownia")

### Spójność z design system
- Kolorystyka zgodna z #1D2B53
- Font wygląda na Montserrat

---

## ❌ Co wymaga poprawy

### 1. **Walidacja - KRYTYCZNE**
```
❌ Tylko jedno pole oznaczone gwiazdką (*)
❌ Brak informacji które pola są wymagane
❌ Błąd "Błąd pobierania produktów z Fakturownia" 
   - czerwony tekst bez ikony
   - brak kontekstu jak naprawić
   - brak przycisku "Spróbuj ponownie"
```

### 2. **Niespójności wizualne**

| Element | Problem |
|---------|---------|
| Border-radius | Pola wyglądają na ~4px zamiast **12px** z design system |
| Checkboxy | Standardowe HTML, nie custom |
| Dropdown | Natywny select, brak spójności |
| Nagłówki sekcji | Brak separacji wizualnej (linia, spacing) |

### 3. **Problemy z hierarchią**

```
⚠️ "Typ artykułu" - dropdown bez wartości domyślnej "— brak —"
   Lepiej: "Wybierz typ artykułu"

⚠️ Checkboxy pod głównym formularzem bez wizualnego grupowania

⚠️ Sekcja "Integracja Fakturownia" wygląda jak część 
   formularza, a jest opcjonalna
```

### 4. **Brakujące elementy UX**

- ❌ Brak tooltipów (np. "Wartość odtworzeniowa" - co to znaczy?)
- ❌ Brak progress/kroków jeśli formularz jest długi
- ❌ Przycisk "Zapisz" tylko w headerze - powinien być też na dole
- ❌ Brak przycisku "Anuluj" obok "Zapisz"
- ❌ Brak auto-save lub informacji o niezapisanych zmianach

---

## 🔧 Rekomendacje napraw

### Priorytet 1 (Quick wins)
```css
/* Napraw border-radius */
input, select, textarea {
  border-radius: 12px;
  border: 1px solid #E0E0E0;
}

input:focus {
  border-color: #1D2B53;
  box-shadow: 0 0 0 3px rgba(29, 43, 83, 0.1);
}
```

### Priorytet 2 (Struktura)
```
┌─────────────────────────────────────────────┐
│ Dane podstawowe                        ▼    │
├─────────────────────────────────────────────┤
│ [Nazwa artykułu *]     [Typ artykułu ▼]    │
│                                             │
│ ☐ Artykuł jest us
