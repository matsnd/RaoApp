# Vision Report

**Plik:** c:/projects/repos/RaoApp_new/contract_6135_u_full.png
**Model:** claude-opus-4-5 (anthropic)
**Data:** 2026-07-09T08:32:50.654Z

# UI/UX Review: Service Contract (U) Edit Page

## ✅ Odpowiedzi na pytania kontrolne

### 1) Nagłówek sekcji grid - "USŁUGI" vs "Pozycje umowy"
**✅ OK** - Nagłówek to **"USŁUGI"**, co jest poprawne dla umowy usługowej (U). Semantycznie właściwe rozróżnienie od umów wynajmu.

### 2) Kolumny grida
**✅ OK** - Grid pokazuje prawidłowe kolumny dla usług:
| Obecne | Wymagane |
|--------|----------|
| # | ✅ |
| USŁUGA | ✅ |
| ILOŚĆ | ✅ |
| JEDNOSTKA | ✅ |
| OPIS | ✅ |
| WARUNKI | ✅ |

**Brak kolumn 'Dni', 'Dostawca', 'Data dost.'** - poprawnie, te kolumny nie mają sensu dla usług.

### 3) Wiersze usług - prostota
**✅ OK** - Wiersz "Usługa wózkiem widłowym 8t" jest prosty:
- Brak dropdown'a artykułów
- Tylko tekst + ilość (1) + jednostka (godzina) + opis
- Minimalistyczna struktura

---

## ⚠️ Problemy wizualne i UX

### A) Problemy z wyrównaniem i spacingiem

| Problem | Lokalizacja | Ważność |
|---------|-------------|---------|
| **Niekonsekwentne odstępy sekcji** | Między "DANE PODSTAWOWE" a "KONTRAHENT" mniejszy margines niż między innymi sekcjami | 🟡 Medium |
| **Zbyt gęste pola w "WARUNKI FINANSOWE"** | Pola "Przedpłata" i "Faktura" ciasno przy "Wartość rozliczenia" | 🟡 Medium |
| **Różne szerokości inputów** | Kod pocztowy (05-090) vs miasto (Dawidy) - nieproporcionalne | 🟢 Low |

### B) Problemy z tabelami

```
ROZLICZENIE UMOWY - wizualne problemy:
┌─────────────────────────────────────────────────────┐
│ ⚠️ Pusta komórka MARŻA (—) bez wyjaśnienia         │
│ ⚠️ Przycisk czerwony "usuń" blisko danych          │
│ ⚠️ Brak separacji wizualnej header/body            │
└─────────────────────────────────────────────────────┘
```

### C) Konkretne błędy

1. **Overlapping concern**: Sekcja "USŁUGI DODATKOWE" ma tekst "Brak aktywnych usług dodatkowych" który zlewa się z instrukcją

2. **Inkonsystentne buttony**:
   - `+ Dodaj usługę` (granatowy, prawy)
   - `+ Dodaj` w usługach dodatkowych (inny styl)
   - `Odśwież z umowy` vs `Wyczyść wszystkie` (różne style)

3. **Status badge "Rozliczona"** - zielony kolor OK, ale duplikacja w header i w sekcji rozliczenia

---

## 🎯 Rekomendacje KISS/UX

### Quick wins (łatwe poprawki):

| # | Zmiana | Impact |
|---|--------|--------|
| 1 | **Ujednolicić spacing** między sekcjami (24px) | Lepszy rytm wizualny |
| 2 | **Dodać zebra-striping** w gridach | Czytelność |
| 3 | **Tooltip na puste "—"** w
