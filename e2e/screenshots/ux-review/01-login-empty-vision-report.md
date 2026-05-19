# Vision Report

**Plik:** C:\projects\repos\RaoApp\e2e\screenshots\ux-review\01-login-empty.png
**Model:** claude-opus-4-5
**Data:** 2026-05-19T08:39:32.582Z

# Analiza UX/UI - Ekran Logowania RAO

## 📊 Ogólna ocena: 7/10

---

## ✅ Co jest OK

### Kolorystyka
- **Tło navy (#1D2B53)** - zgodne z design systemem Toolsmart ✓
- **Biała karta logowania** - dobry kontrast z tłem ✓
- **Przycisk CTA w kolorze navy** - spójność z paletą ✓

### Layout
- **Centralne położenie karty** - standardowe, intuicyjne ✓
- **Hierarchia wizualna** - logo → tytuł → formularz → CTA ✓
- **Link "Nie pamiętam hasła"** - obecny i widoczny ✓

### Typografia
- **Font wygląda na Montserrat** - zgodność z DS ✓
- **Czytelne labelki** (Login, Hasło) ✓

---

## ❌ Problemy UX/UI do poprawy

### 1. **Border-radius karty - NIEZGODNY**
| Element | Jest | Powinno być |
|---------|------|-------------|
| Karta logowania | ~20-24px | **12px** |
| Inputy | ~8px | **12px** |
| Przycisk | ~8px | **12px** |

> Niespójność radiusów - karta ma za duży, inputy i przycisk za mały

---

### 2. **Brak walidacji wizualnej pól**
- ❌ Brak ikony użytkownika przy polu Login
- ❌ Brak ikony kłódki przy polu Hasło
- ❌ Brak ikony "pokaż/ukryj hasło" 👁️

---

### 3. **Słaby kontrast placeholderów**
```
Placeholder "Podaj login" / "Podaj hasło" 
→ Zbyt jasny szary, może być nieczytelny dla osób z wadami wzroku
→ Wymaga sprawdzenia WCAG AA (min. 4.5:1)
```

---

### 4. **Spacing - problemy**

```
┌─────────────────────────────┐
│          RAO                │ 
│       Logowanie             │ ← OK
│                             │
│ Login                       │ ← Za mały margines górny
│ [_______________]           │
│ Hasło                       │ ← Za mały spacing między polami (~16px, powinno ~24px)
│ [_______________]           │
│                             │
│ [   Zaloguj się   ]         │ ← OK
│                             │
│   Nie pamiętam hasła        │ ← OK
└─────────────────────────────┘
```

---

### 5. **Brak stanów interaktywnych (prawdopodobnie)**
- ❓ Hover na przycisku
- ❓ Focus state na inputach (outline)
- ❓ Error state (czerwona ramka + komunikat)

---

### 6. **Accessibility issues**
| Problem | Wpływ |
|---------|-------|
| Brak `aria-label` (zakładam) | Screen readery |
| Brak widocznego focus ring | Nawigacja klawiaturą |
| Niski kontrast placeholderów | Czytelność |

---

### 7. **Brakujące elementy UX**
- ❌ **Checkbox "Zapamiętaj mnie"** - standard w systemach B2B
- ❌ **Logo firmy/ikona** - tylko tekst "RAO"
- ❌ **Informacja o systemie** - np. "System wynajmu maszyn"

---

## 🔧 Rekomendacje naprawcze

```css
/* Poprawki CSS */
.login
