# Vision Report

**Plik:** c:/projects/repos/RaoApp_new/e2e/screenshots/ux-review/17-commission-view.png
**Model:** claude-opus-4-5 (anthropic) [fallback z free model: empty/thin response]
**Data:** 2026-07-05T10:55:37.150Z

# Analiza UI/UX - Widok Prowizji w RAO

## ⚠️ Problem: Brak widoku prowizji na screenshocie

Na załączonym screenshocie widzę **Dashboard (Pulpit)**, nie widok Prowizji. Mogę jednak przeprowadzić analizę na podstawie tego, co jest widoczne, oraz dać rekomendacje dla modułu Prowizji.

---

## 📊 Analiza widocznego Dashboardu

### ✅ Co jest OK

| Element | Ocena |
|---------|-------|
| **Hierarchia informacji** | Karty KPI na górze dobrze priorytetyzują dane |
| **Kolorystyka statusów** | Żółty (ostrzeżenie), czerwony (problem), zielony (OK) - intuicyjne |
| **Spójność ikon** | Jednolity styl ikon w nawigacji i kartach |
| **Border-radius** | Konsekwentne 12px zgodne z design systemem |
| **Typografia** | Montserrat zachowany, dobra hierarchia wielkości |

### ❌ Co wymaga poprawy

```
1. NAWIGACJA
   - "Prowizje" w menu bocznym - brak ikony (niespójność)
   - Sekcja "ARCHIWUM (SZACUNKOWE)" - słaby kontrast tekstu

2. KARTY KPI
   - Różne wysokości kart (62 niewydrukowane vs 0 dostawy)
   - Ikony w różnych stylach (outline vs filled)

3. QUICK ACTIONS (środkowe przyciski)
   - Duplikacja z menu bocznym - redundancja
   - Ikona "Statystyki" różni się od wersji w sidebar

4. LISTY
   - Brak wyraźnego hover state
   - "261 dni" przeterminowania - brak alarmu wizualnego
```

---

## 🎯 Rekomendacje dla widoku Prowizji

Na podstawie design systemu RAO, widok Prowizji powinien zawierać:

### Proponowany układ tabeli

```
┌─────────────────────────────────────────────────────────────────┐
│  PROWIZJE                                    [Filtruj] [Eksport]│
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 12 450 zł│  │  3 200 zł│  │    15    │  │  8 420 zł│        │
│  │ Ten mies.│  │Do wypłaty│  │  Umowy   │  │ Wypłacone│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
├─────────────────────────────────────────────────────────────────┤
│  Nr umowy │ Kontrahent │ Wartość │ Prowizja │ Status │ Akcje   │
│  ─────────┼────────────┼─────────┼──────────┼────────┼──────── │
│  S001/26  │ Wod-Bud    │ 15000zł │   450zł  │ ● Wyp. │  [...]  │
│  S002/26  │ BudMax     │ 22000zł │   660zł  │ ○ Ocz. │  [...]  │
└─────────────────────────────────────────────────────────────────┘
```

### Kluczowe wytyczne

| Aspekt | Rekomendacja |
|--------|--------------|
| **Szerokość kolumn** | Proporcjonalne, najważniejsze dane (kwoty)
