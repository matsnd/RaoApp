# Vision Report

**Plik:** C:\projects\repos\RaoApp\spec\backlog\backlog_to_refinement\Zrzut ekranu 2026-05-17 220919.png
**Model:** claude-opus-4-5
**Data:** 2026-05-17T21:32:38.226Z

# Analiza UX/UI - Screenshot RAO

## 📋 Co pokazuje screenshot?

**Funkcjonalność:** Checkbox do ukrycia adresu dostawy na dokumentach - z opcją, aby klient sam wpisał adres na umowie (zamiast predefiniowanego).

**Kontekst:** Formularz protokołu/umowy najmu z danymi:
- Usługobiorca (zamazane)
- Nr telefonu: 515997186
- Adres budowy: Żwirowa 61, 05-090 Puchały

---

## ✅ Co jest OK

| Element | Ocena |
|---------|-------|
| Żółte podświetlenie pól | Dobra widoczność danych |
| Logiczny układ formularza | Czytelna struktura label: value |
| Funkcjonalność biznesowa | Odpowiada realnej potrzebie (prywatność klienta) |

---

## ❌ Problemy do poprawy

### 1. **Tekst checkboxa - katastrofa UX**
```
Obecny tekst (35+ słów!):
"Niech się nie pokazuje tutaj adres dostawy I pomimo że my numer 
wpisaliśmy niech on się wyświetla tylko na protokole a na umowie 
niech będzie możliwość żę klient sam wpisze."
```

**Problemy:**
- 🚫 Język potoczny/kolokwialny ("niech się nie pokazuje")
- 🚫 Błąd ortograficzny: "żę" → "że"
- 🚫 Za długi tekst - nikt tego nie przeczyta
- 🚫 Niejasna intencja

**Propozycja:**
```
☐ Ukryj adres dostawy na umowie (klient wpisze ręcznie)
```

### 2. **Niezgodność z Design System**

| Element | Obecny stan | Powinno być |
|---------|-------------|-------------|
| Border-radius | 0px (ostre rogi) | 12px |
| Font | Wygląda na Arial/system | Montserrat |
| Kolor primary | Nie widać #1D2B53 | Użyć w headerach |
| Tło | Białe bez struktury | #F8F9FA dla sekcji |

### 3. **Wizualne błędy**
- ⚠️ Checkbox bez wyraźnego stanu (słabo widoczny)
- ⚠️ Brak hierarchii wizualnej (wszystko tym samym fontem)
- ⚠️ Żółte highlight - czy to stan edycji czy stały wygląd?

---

## 🎯 Rekomendacja redesignu

```
┌─────────────────────────────────────────────────────┐
│  📍 ADRES DOSTAWY                          [navy]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Budowa:  Żwirowa 61, 05-090 Puchały               │
│           (przy nr 83, duży szaro-biały budynek)   │
│                                                     │
│  ☐ Ukryj adres na umowie (klient wpisze ręcznie)   │
│                                                     │
│  border-radius: 12px, bg: #F8F9FA                  │
└─────────────────────────────────────────────────────┘
```

**Priorytet #1:** Przepisać tekst checkboxa - obecny wygląda jak notatka developera, nie produkcyjny UI.
