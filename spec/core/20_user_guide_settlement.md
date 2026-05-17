# Instrukcja obsługi: Rozliczenie umowy

> **Dla użytkownika końcowego** — porównanie starego systemu (WinForms) z nowym (Vue.js)  
> **Cel:** Wykonanie rozliczenia finansowego umowy (faktury, przedpłaty, saldo)

---

## 📋 Stary system (WinForms) — Jak to działało

### Scenariusz: Nowa umowa z rozliczeniem tygodniowym

#### Krok 1: Otwórz formularz umowy
```
Dashboard → [+] Dodaj umowę
      ↓
FormU4 (formularz umowy)
```

#### Krok 2: Wypełnij dane umowy
- Wybierz **Kontrahenta** z listy
- Ustaw **Daty od/do** w kalendarzu 2-miesięcznym
- Wybierz **Handlowca** z dropdown
- W sekcji **"Rozliczenie"** (groupBox1):
  - Wpisz **Wartość** umowy (ręcznie lub auto-z warunków)
  - Wpisz **Przedpłata** kwota + dokument
  - Wpisz **Faktura** kwota + dokument
  - System wyliczy **Pozostało** automatycznie

#### Krok 3: Dodaj pozycje z artykułami
```
[+] Pozycja → FormAwybor (lista artykułów)
      ↓
Wybierz artykuł (kolorem żółtym = zajęty)
      ↓
Ustaw: Data dostawy, Liczba dni, Cena
      ↓
[OK] → powrót do FormU4
```

#### Krok 4: Ustaw warunki rozliczenia (FormW)
```
Zaznacz pozycję w tabeli
      ↓
[+] Warunki → FormW (dedykowany formularz)
      ↓
Typ stawki: [Stawka z progiem ▼]
Naliczanie:  [tygodniowo ▼]
Opłata za:   [tydzień ▼]
      ↓
Dodaj progi:
  • Min [5] tygodni × Opłata1 [5000,00] zł
  • Powyżej [99] tygodni × Opłata1 [4000,00] zł
      ↓
Auto-opis: "stawka 5000,00 zł/tyg. do 5 tygodni, powyżej 4000,00 zł/tyg."
      ↓
[Zakończ] → powrót do FormU4
```

#### Krok 5: Rozlicz pozycje (opcjonalnie — techniczny cache)
```
Menu kontekstowe na pozycji → "Rozlicz"
      ↓
System generuje wiersze w tabeli 'rozliczenie'
(1 wiersz = 1 dzień wynajmu — użytkownik tego nie widzi)
      ↓
LUB: przycisk "Rozlicz wszystko" → dla wszystkich pozycji
```

#### Krok 6: Sprawdź saldo i zapisz
```
Wartość:     15 000,00 zł
Przedpłata:  -5 000,00 zł
Faktura:    -10 000,00 zł
──────────────────────────
Pozostało:       0,00 zł  ✓
      ↓
[Zapisz i wyjdź]
```

---

## 🚀 Nowy system (Vue.js + FastAPI) — Jak to działa

### Scenariusz: Ta sama umowa — ulepszony flow

#### Krok 1: Otwórz formularz umowy
```
Dashboard → [+] Dodaj umowę
      ↓
ContractFormView (responsywny formularz)
```

#### Krok 2: Wypełnij dane umowy
- Kliknij **Wybierz** przy polu Kontrahent → modal z wyszukiwaniem
- Wybierz kontrahenta → **adresy dostawy auto-ładują się** do dropdown
- Wybierz **Adres dostawy** z listy (lub wpisz ręcznie)
- Ustaw **Daty od/do** w polach typu date
- Wybierz **Oddział** i **Handlowca** z dropdown

#### Krok 3: Finanse (sekcja w formularzu)
```
┌─ Finanse ───────────────────────────────────┐
│                                              │
│  Wartość      [    15 000,00 zł    ]  ✨    │  ← auto-kalkulacja
│                                              │
│  Przedpłata   [ 5 000,00 ] zł                 │
│  Dokument     [ Zaliczka-03/2026 ]            │
│                                              │
│  Faktura      [ 10 000,00 ] zł                │
│  Dokument     [ FV-123/2026 ]                 │
│                                              │
│  Pozostało    [     0,00 zł    ]  🟢         │  ← computed
│                                              │
└──────────────────────────────────────────────┘
```

> **✨ Auto-kalkulacja:** Wartość umowy jest wyliczana automatycznie z warunków cenowych po zapisaniu pozycji lub zmianie warunków. Nie trzeba wpisywać ręcznie!

#### Krok 4: Dodaj pozycje
```
[ + Dodaj pozycję ] → modal
      ↓
Artykuł:     [ Wybierz ▼ ] → modal picker z badge'm dostępności
             🟢 Dostępny / 🔴 Wynajęty
      ↓
Typ:         [ WN ▼ ]
Opis:        [ Wynajem koparki... ]
Dni:         [ 30 ]
Ilość:       [ 1 ]
      ↓
Rozliczanie: [ tygodniowo ▼ ]
Opłata za:   [ tydzień ▼ ]
Typ stawki:  [ Stawka z progiem ▼ ]
Data dost.:  [ 2026-03-15 ▼ ]
      ↓
[ Zapisz pozycję ]
```

#### Krok 5: Ustaw warunki cenowe (ConditionPanel)
```
Zaznacz pozycję w tabeli (kliknij wiersz)
      ↓
┌─ Warunki rozliczenia ───────────────────────┐
│                                              │
│  [<] [>]  Nawigacja między pozycjami         │
│                                              │
│  Typ:        [ Stawka z progiem ▼ ]          │
│  Naliczanie: [ tygodniowo ▼ ]                │
│  Opłata za:  [ tydzień ▼ ]                    │
│                                              │
│  ┌─ Opis auto-generowany ──────────────────┐ │
│  │ stawka 5000,00 zł/tyg. do 5 tygodni,   │ │
│  │ powyżej 4000,00 zł/tyg.                │ │
│  └──────────────────────────────────────────┘ │
│                                              │
│  Dodaj próg:                                 │
│  Min [ 5 ] × Rate1 [ 5000,00 ] Rate2 [ 4000 ]│
│  [ + Dodaj ]                                 │
│                                              │
│  Lista progów:                               │
│  • do 5 tyg. × 5000 zł                       │
│  • pow. 5 tyg. × 4000 zł                     │
│                                              │
└──────────────────────────────────────────────┘
```

> **Auto-opis:** System generuje tekst opisu automatycznie — nie trzeba wpisywać ręcznie!

#### Krok 6: Auto-kalkulacja wartości
```
Po zapisaniu warunków:
      ↓
System automatycznie wylicza wartość pozycji
      ↓
Wartość = 5 tyg. × 5000 zł + 25 tyg. × 4000 zł
        = 25 000 zł + 100 000 zł
        = 125 000 zł
      ↓
Wartość umowy (total_value) aktualizuje się automatycznie
Pozostało = total - prepayment - invoice
```

#### Krok 7: Sprawdź i zapisz
```
Wartość (auto):     125 000,00 zł
Przedpłata:          -5 000,00 zł
Faktura:           -10 000,00 zł
────────────────────────────────
Pozostało (auto):   110 000,00 zł  🟡

[ Zapisz umowę ]
```

---

## 📊 Porównanie: Stary vs Nowy

| Funkcja | Stary (WinForms) | Nowy (Vue.js) | Zmiana |
|---------|------------------|---------------|--------|
| **Wartość umowy** | Ręczna wpisana | Auto-kalkulacja z warunków | ✅ Lepsze |
| **Warunki cenowe** | FormW — osobne okno | ConditionPanel — wbudowane | ✅ Szybsze |
| **Auto-opis warunków** | Ręczny tekst | Auto-generowany | ✅ Mniej błędów |
| **Adresy kontrahenta** | Dropdown | Dropdown + auto-fill | ✅ Takie same |
| **Dostępność artykułu** | Kolor tła (Moccasin) | Badge Dostępny/Wynajęty | ✅ Czytelniejsze |
| **Pozostało** | Auto-wyliczone | Auto-wyliczone (computed) | ✅ Takie same |
| **Responsywność** | Desktop only | Desktop + Tablet + Mobile | ✅ Lepsze |

---

## 🎯 Co się zmieniło na lepsze

### 1. Nie trzeba ręcznie wpisywać wartości umowy

**Stary:** Użytkownik musiał wpisać `Wartość` ręcznie (lub kopiować z kalkulatora), potem klikał "Rozlicz" żeby wygenerować techniczny cache wierszy na dzień.

**Nowy:** System liczy wartość automatycznie z warunków cenowych po:
- Zapisaniu pozycji umowy
- Zmianie warunków cenowych w ConditionPanel

> � **Better practice:** Auto-kalkulacja eliminuje błędy ludzkie i oszczędza czas. Brak przycisku "Rozlicz" — bo nie potrzeba generować sztucznego cache'u.

### 2. Warunki w tym samym oknie
- **Stary:** FormW osobne okno, nawigacja [<][>], zapisywanie, zamykanie
- **Nowy:** ConditionPanel wbudowany w formularz — zaznacz pozycję, edytuj warunki, gotowe

### 3. Opis warunków generowany automatycznie
- **Stary:** Użytkownik wpisywał: `"stawka 5000 zł/tyg. do 5 tygodni"`
- **Nowy:** System generuje z pól — mniej błędów, zawsze poprawny format

### 4. Wybór artykułu z informacją o dostępności
- **Stary:** Żółte tło (Moccasin) = zajęty — mało widoczne
- **Nowy:** Badge 🟢 Dostępny / 🔴 Wynajęty — jasny komunikat

---

## ❓ FAQ — Najczęstsze pytania

### P: Gdzie jest przycisk "Rozlicz wszystko"?
**O:** W nowym systemie nie ma potrzeby ręcznego rozliczania. System wylicza wartość automatycznie z warunków cenowych. Tabela `settlements` była technicznym cache'm — nie była widoczna dla użytkownika.

### P: Czy mogę edytować wartość ręcznie?
**O:** Tak, pole `Wartość` jest edytowalne. Jeśli chcesz wymusić inną wartość niż wyliczona z warunków — wpisz ją ręcznie. System nie nadpisze jej automatycznie (chyba że dodasz nową pozycję lub zmienisz warunki).

### P: Co jeśli klient płaci w ratach (więcej faktur)?
**O:** Obecnie system obsługuje jedną fakturę i jedną przedpłatę (jak w starym). Jeśli potrzebujesz ewidencji wielu płatności — zgłoś to jako zapotrzebowanie na nową funkcjonalność.

### P: Jak sprawdzić historię rozliczeń pozycji?
**O:** W nowym systemie historia nie jest zapisywana. Warunki cenowe są źródłem prawdy — każda zmiana warunku jest widoczna w ConditionPanel.

---

## 🆘 Wsparcie

W razie problemów z rozliczeniem:
1. Sprawdź czy pozycje mają ustawione **Warunki** (bez warunków wartość = 0)
2. Sprawdź czy **Daty umowy** pokrywają się z okresem wynajmu pozycji
3. Jeśli wartość jest 0 — sprawdź czy warunki mają wypełnione pola `rate1` i `period_count`
4. Jeśli "Pozostało" jest czerwone — klient zalega z płatnością

---

> **Autor:** Zespół deweloperski RAO  
> **Data:** 2026-04-08  
> **Wersja:** 1.0
