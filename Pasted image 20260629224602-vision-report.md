# Vision Report

**Plik:** C:/projects/repos/RaoApp/Pasted image 20260629224602.png
**Model:** claude-opus-4-5
**Data:** 2026-06-29T20:53:12.193Z

# Analiza UX/UI - Sekcja "Warunki Finansowe"

## 📋 Co przedstawia screenshot

Sekcja **"Warunki Finansowe"** w umowie wynajmu maszyn budowlanych - prawdopodobnie widok szczegółów historycznej umowy.

---

## 🔍 Widoczne elementy i wartości

| Pole | Wartość | Typ pola |
|------|---------|----------|
| **Handlowiec** | Piotr | Dropdown |
| **Oddział** | — brak — | Dropdown |
| **Wartość (zł)** | *(puste)* | Input |
| **Pozostało (zł)** | -3597,75 zł | Input (highlight) |
| **Przedpłata (zł)** | 3597,75 | Input |
| **Dok. przedpłaty** | *(puste)* | Input |
| **Faktura (zł)** | 0,00 | Input |
| **Dok. faktury** | *(puste)* | Input |

---

## 🎯 Problem zgłoszony przez klienta: Pole "Wartość (zł)"

### Kluczowy błąd logiczny:
```
Przedpłata: 3597,75 zł
Wartość:    (puste)
Pozostało: -3597,75 zł
```

**Formuła prawdopodobnie:** `Pozostało = Wartość - Przedpłata - Faktura`
**Rezultat:** `0 - 3597,75 - 0 = -3597,75` ✅ matematycznie OK, ale...

### ⚠️ Problem UX:
**Pole "Wartość" jest puste, mimo że istnieje przedpłata** — to sugeruje:
- Brak walidacji przy zapisie
- Umowa historyczna z niekompletnymi danymi
- Pole powinno być **wymagane** lub **obliczane automatycznie**

---

## ✅ Co jest OK

| Element | Ocena |
|---------|-------|
| Czytelny layout 2x4 grid | ✅ |
| Nagłówek sekcji uppercase | ✅ zgodny z DS |
| Border-radius ~12px | ✅ zgodny z DS |
| Tło kart białe/szare | ✅ zgodny z DS |
| Highlight na "Pozostało" (navy) | ✅ dobra praktyka |

---

## ❌ Błędy wizualne i UX

### 1. **Niespójność formatowania wartości**
```
3597,75      ← bez "zł"
-3597,75 zł  ← z "zł"
0,00         ← bez "zł"
```
**Fix:** Ujednolicić format lub użyć suffixu w polu

### 2. **Brak wizualnej walidacji pustego pola "Wartość"**
- Pole jest puste ale brak sygnału błędu
- W kontekście historycznym — powinien być placeholder "Nie podano" lub "—"

### 3. **Nieczytelność negatywnej kwoty**
```diff
- Pozostało: -3597,75 zł (navy background)
+ Powinno być: czerwone tło/tekst dla wartości ujemnych
```

### 4. **Brak stanu "readonly" dla historycznych umów**
- Jeśli to historia — pola nie powinny wyglądać jak edytowalne
- Sugestia: szare tło `#E9ECEF` lub usunięcie borderów

### 5. **Hierarchia wizualna**
- "Wartość (zł)" powinna być wizualnie priorytetowa (bold/większy font)
- To kluczowe pole dla rozliczeń

---

## 💡 Rekomendacje

```
┌─────
