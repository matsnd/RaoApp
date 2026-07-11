# Vision Report

**Plik:** c:/projects/repos/RaoApp_new/contract_6134_s_conditions.png
**Model:** claude-opus-4-5 (anthropic)
**Data:** 2026-07-09T12:21:14.932Z

# UI/UX Review: Rental Contract Edit Page (S397/2025)

## 1. Condition Labels (WARUNKI ROZLICZENIA) — Day-based Rental

### ✅ Co jest OK:
- Etykiety kolumn są poprawne: **OD (DNI)**, **DO (DNI)**, **STAWKA (ZŁ)**, **JEDNOSTKA**, **MINIMUM**
- Wartość "dziennie" w kolumnie JEDNOSTKA jest prawidłowa dla wynajmu dziennego
- Podgląd PDF pokazuje poprawnie: "1-1 dzień - 185,00 zł / doba"

### ⚠️ Do poprawy:
- **Niespójność terminologii**: "dziennie" vs "doba" w PDF — ujednolicić
- Brak nagłówka sekcji z wyraźnym oddzieleniem od pozycji umowy
- Wartość "0" w MINIMUM może być myląca — rozważyć "brak" lub "-"

---

## 2. ConditionPanel Layout — KISS & Design System

### ✅ Co jest OK:
- Prosty, tabelaryczny układ
- Przyciski akcji (+Dodaj warunek, Zastosuj cennik) są widoczne
- Ikony usuwania (×) przy każdym wierszu

### ❌ Problemy:

| Problem | Szczegół |
|---------|----------|
| **Border-radius** | Tabela ma ostre krawędzie — powinno być **12px** wg DS |
| **Brak separacji wizualnej** | Panel zlewa się z sekcją POZYCJE UMOWY |
| **Przyciski "tj z ostatniej umowy"** | Niski kontrast, słaba czytelność |
| **Wyrównanie** | Przycisk "+ Dodaj warunek" niewystarczająco oddzielony od filtrów |

---

## 3. Service Fee Grid (OPŁATY DODATKOWE) + PDF Preview

### ✅ Co jest OK:
- Struktura kolumn logiczna: NAZWA, KWOTA OD, KWOTA DO, J.M., TEKST NA UMOWIE, AKTYWNA
- Tagi "Tak" (zielone) dobrze oznaczają status aktywności
- PDF preview na dole pokazuje wybrane opłaty — dobra transparentność

### ❌ Problemy czytelności:

```
┌─────────────────────────────────────────────────────────┐
│ TEKST NA UMOWIE - zbyt długi tekst w komórce           │
│ "Czyszczenie maszyny po wynajmie (zabrudzenia         │
│ trudnościeralne): 400,00 zł - 1 500,00 zł"            │
│                                                         │
│ → Tekst jest ucięty/zawinięty chaotycznie              │
└─────────────────────────────────────────────────────────┘
```

- **Kolumna TEKST NA UMOWIE**: za wąska, tekst łamie się nierównomiernie
- **Brak tooltipów** przy długich opisach
- **PDF preview**: mały font, słaba hierarchia wizualna
- **Filtry (Wspólne/Diesel/Elektryki)**: wyglądają jak taby, ale działają jak filtry — niejasna affordance

---

## 4. Ogólne problemy UI/UX

### 🔴 Krytyczne:

1. **Niespójne border-radius**: 
   - Przyciski mają różne zaokrąglenia (niektóre 4px, inne 8px)
   - Powinno być **12px** wszędzie

2. **Zbyt gęsty layout**:
   - Brak wystarczającego whitespace między sekcjami
   - Sekcje WARUNKI ROZLICZENIA i OPŁATY DOD
