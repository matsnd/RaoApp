# Vision Report

**Plik:** C:/projects/repos/RaoApp_new/e2e/screenshots/archive_stats.png
**Model:** claude-opus-4-5
**Pytanie:** To jest widok statystyk archiwum. Sprawdź dokładnie: (1) marginesy/padding wokół kart statystyk, (2) czy karty mają border-radius i shadow, (3) czy spacing między kartami jest jednolity, (4) czy tabele w kartach mają odpowiedni padding, (5) czy banner archiwum na górze ma poprawny layout, (6) czy zakładki (Umowy/Maszyny/Statystyki/Kategorie) mają poprawny spacing. Wymień KONKRETNE problemy z wartościami px jeśli możesz.
**Data:** 2026-07-01T21:25:19.857Z

# Analiza UI/UX - Widok Statystyk Archiwum RAO

## 🔴 OGÓLNA OCENA: **WYMAGA POPRAWY**

---

## 1. MARGINESY I PADDING KART STATYSTYK

### ❌ **KRYTYCZNE PROBLEMY:**

| Element | Stan obecny | Powinno być | Problem |
|---------|-------------|-------------|---------|
| Karta "PODSUMOWANIE" | ~0-4px padding wewnętrzny | 20-24px | Dane "734 / 878 / 3 169 639,63 zł" przylegają do krawędzi |
| Karta "TOP MASZYNY" | Brak widocznego padding-left | 16-20px | Nagłówek i tabela zaczynają się zbyt blisko lewej krawędzi |
| Karta "KATEGORIE" | Analogicznie ~4-8px | 16-20px | Niespójne z design systemem |
| Odstęp między kartami | ~8px | 16-24px | Karty wizualnie "zlewają się" |

---

## 2. BORDER-RADIUS I SHADOW

### ❌ **PROBLEMY:**

```
STAN OBECNY:
- Karty: border-radius = 0px (ostre rogi)
- Shadow: brak lub bardzo subtelny (0px 0px 0px)

DESIGN SYSTEM WYMAGA:
- border-radius: 12px
- box-shadow: 0 2px 8px rgba(0,0,0,0.08)
```

**Wizualnie:** Karty wyglądają jak płaskie div-y bez głębi, co łamie zasady design systemu RAO.

---

## 3. SPACING MIĘDZY KARTAMI

### ❌ **NIESPÓJNOŚĆ:**

| Przejście | Obecny spacing | Wymagany |
|-----------|----------------|----------|
| Banner → PODSUMOWANIE | ~12px | 24px |
| PODSUMOWANIE → TOP MASZYNY | ~8px | 16-24px |
| TOP MASZYNY → KATEGORIE | ~8px | 16-24px |

**Problem:** Brak wizualnego "oddechu" między sekcjami.

---

## 4. PADDING TABEL W KARTACH

### ❌ **SZCZEGÓŁOWA ANALIZA:**

**Tabela TOP MASZYNY:**
```
- Padding-left pierwszej kolumny (NAZWA): ~8px → powinno 16px
- Padding między kolumnami: OK (~12-16px)
- Padding wierszy (row height): ~36px → OK
- Nagłówek tabeli: brak górnego padding (~0px) → powinno 12px
```

**Tabela KATEGORIE:**
```
- Analogiczne problemy
- Ikona 📁 przed "KATEGORIE" ma ~4px margin-right → powinno 8px
```

---

## 5. BANNER ARCHIWUM (GÓRA)

### ⚠️ **PROBLEMY LAYOUT:**

```css
/* OBECNY STAN (estymacja): */
.banner-warning {
  padding: 8px 12px;        /* → powinno: 12px 16px */
  margin-bottom: 8px;       /* → powinno: 16-20px */
  border-radius: 0px;       /* → powinno: 8px */
}
```

**Konkretne błędy:**
1. ⚠️ Ikona ostrzeżenia za blisko tekstu (~4px → 8px)
2. Tekst "Archiwum — dane historyczne..." ma line-height zbyt ciasny
3. Banner nie ma wyraźnego border-radius (powinien mieć 8px)
4. Kolor tła (#FFF3CD-podobny) OK, ale border powinien być 1px solid #FFCC00

---

## 6. ZAKŁADKI (Umowy/Maszyny/Statystyki/Kategorie)

### ❌ **PROBLEMY SPACING:**

```
OBECNY STAN:
┌─────────────────────────────────────────────┐
│UmowyMaszyny Statystyki Kategorie            │ ← brak spacing!
└─────────────────────────────────────────────┘

POWINNO BYĆ:
┌─────────────────────────────────────────────┐
│ Umowy   Maszyny   Statystyki   Kategorie   │
└─────────────────────────────────────────────┘
   ↑ 16px padding-left
        ↑ 24px gap między zakładkami
```

**Konkretne wartości:**
| Problem | Obecne | Wymagane |
|---------|--------|----------|
| Gap między zakładkami | 0-4px (zlepione!) | 16-24px |
| Padding wewnętrzny zakładki | ~4px 8px | 8px 16px |
| Podkreślenie aktywnej | brak widocznego | 2px solid primary |
| Wysokość paska zakładek | ~32px | 40-44px |

---

## 7. DODATKOWE PROBLEMY

### ❌ **ALIGNMENT:**
- Kolumny numeryczne (UMÓW, POZYCJI, DNI) - wyrównanie **left** zamiast **right**
- Kolumna PRZYCHÓD - wartości przekreślone sugerują starą cenę, ale brak nowej (UX issue)

### ❌ **OVERFLOW:**
- Przy węższym ekranie tabela prawdopodobnie nie ma horizontal scroll
- Długie nazwy maszyn ("Ładowarka teleskopowo - obrotowa 21m") mogą się obcinać

### ⚠️ **TYPOGRAPHY:**
- "Data od: / Data do:" - label ma ~11px font → powinien 12-14px
- Link "[szac.]" przy przychodach - za mały kontrast, ~10px font

---

## 📋 PODSUMOWANIE WYMAGANYCH POPRAWEK

| Priorytet | Element | Poprawka |
|-----------|---------|----------|
| 🔴 P1 | Zakładki nawigacji | Dodać gap: 20px między items |
| 🔴 P1 | Padding kart | Ustawić padding: 20px |
| 🔴 P1 | Border-radius kart | Dodać border-radius: 12px |
| 🟡 P2 | Shadow kart | Dodać box-shadow |
| 🟡 P2 | Spacing między kartami | margin-bottom: 24px |
| 🟡 P2 | Wyrównanie kolumn numerycznych | text-align: right |
| 🟢 P3 | Banner archiwum | padding + border-radius |

---

## SZYBKI FIX CSS (estymacja):

```css
/* Karty */
.card-podsumowanie,
.card-top-maszyny,
.card-kategorie {
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(29, 43, 83, 0.08);
  margin-bottom: 24px;
}

/* Zakładki */
.tabs-navigation {
  display: flex;
  gap: 20px;
  padding-left: 16px;
}

.tab-item {
  padding: 8px 16px;
}

/* Tabele */
.table td:first-child {
  padding-left: 16px;
}

.table td.numeric {
  text-align: right;
}
```
