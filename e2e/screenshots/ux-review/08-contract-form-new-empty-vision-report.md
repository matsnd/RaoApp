# Vision Report

**Plik:** C:\projects\repos\RaoApp\e2e\screenshots\ux-review\08-contract-form-new-empty.png
**Model:** claude-opus-4-5
**Data:** 2026-05-19T08:40:43.389Z

# Analiza UX/UI - Formularz Nowej Umowy (ToolSmart/RAO)

## 📊 Ogólna ocena: 5.5/10

---

## ✅ Co jest OK

### 1. **Podstawowa struktura**
- Logiczny przepływ od góry: typ umowy → daty → kontrahent → szczegóły
- Nawigacja boczna jest czytelna, aktywna sekcja wyróżniona
- Przycisk "Zapisz" w prawym górnym rogu (standardowa lokalizacja)

### 2. **Niektóre elementy formularza**
- Pole "Kontrahent" ma gwiazdkę (*) oznaczającą wymagane pole
- Przycisk "Wybierz" przy kontrahentcie - dobra praktyka dla lookup
- Checkboxy "Drukuj" przy osobach kontaktowych - praktyczne

### 3. **Kolorystyka podstawowa**
- Navy sidebar zgodny z design systemem (#1D2B53)
- "Pozostało (zł)" w kolorze czerwonym/pomarańczowym - sygnalizuje uwagę

---

## ❌ Problemy UX/UI

### 🔴 **KRYTYCZNE**

#### 1. **Brak wizualnego grupowania pól**
```
Problem: Wszystkie pola są "płaskie" - brak sekcji, kart, separatorów
Skutek: Użytkownik nie wie, które pola są powiązane
Rozwiązanie: Dodać karty/sekcje z nagłówkami:
- "Dane podstawowe umowy"
- "Kontrahent i adres dostawy"  
- "Wartości i płatności"
- "Osoby kontaktowe"
- "Opcje dodatkowe"
```

#### 2. **Niespójne oznaczanie pól wymaganych**
```
Problem: Tylko "Kontrahent" ma gwiazdkę (*), a prawdopodobnie 
         więcej pól jest wymaganych (Data od, Typ umowy?)
Rozwiązanie: Konsekwentnie oznaczać WSZYSTKIE wymagane pola
```

#### 3. **Brak widocznej walidacji**
```
Problem: Nie widać żadnych komunikatów błędów, wskazówek
- Co jeśli data jest błędna?
- Jak wygląda błąd przy pustym polu wymaganym?
Rozwiązanie: Dodać inline validation z komunikatami pod polami
```

---

### 🟠 **WAŻNE**

#### 4. **Chaotyczny layout adresu dostawy**
```
Obecny stan:
[00-000] [Miasto] [Uwagi dojazdowe (opcjonalnie)]

Problem: 
- Brak pola na ulicę/numer!
- Kod pocztowy i miasto w jednej linii z uwagami
- Placeholder "00-000" zamiast etykiety "Kod pocztowy"

Rozwiązanie:
[Ulica i numer          ]
[Kod pocztowy] [Miasto  ]
[Uwagi dojazdowe        ]
```

#### 5. **Niespójne placeholdery vs etykiety**
```
Problemy:
- "Wybierz kontrahenta..." - OK jako placeholder
- "00-000" - to format, nie etykieta (brak label "Kod pocztowy")
- "Miasto" - to label czy placeholder?
- "(auto)" przy numerze umowy - niejasne
- "dd.mm.yyyy" - format daty jako placeholder

Rozwiązanie: Etykiety ZAWSZE nad polem, placeholdery jako przykłady
```

#### 6. **Spacing i alignment**
```
Problemy:
- Nierówne odstępy między wierszami
- Sekcja "Opcje" (checkboxy na dole) wygląda na "dorzuco
