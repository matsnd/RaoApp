# Vision Report

**Plik:** C:\projects\repos\RaoApp\e2e\screenshots\ux-review\02-login-validation-error.png
**Model:** claude-opus-4-5
**Data:** 2026-05-19T08:39:55.658Z

# Analiza UX/UI - Ekran logowania z błędem walidacji RAO

## 📊 Ogólna ocena: 6/10

---

## ✅ Co jest OK

### 1. **Pozycja komunikatu błędu**
- Umieszczony bezpośrednio pod polem hasła - blisko kontekstu
- Użytkownik nie musi szukać informacji o błędzie

### 2. **Kolor czerwony**
- Standardowy kolor dla błędów (rozpoznawalny wzorzec)
- Kontrastuje z białym tłem formularza

### 3. **Ogólna estetyka formularza**
- Czyste, minimalistyczne podejście
- Zgodność z design systemem (border-radius 12px, kolory navy)

---

## 🚨 Problemy wymagające poprawy

### 1. **Niespecyficzny komunikat błędu**

| Problem | Rozwiązanie |
|---------|-------------|
| "Nieprawidłowy login lub hasło" - użytkownik nie wie, które pole jest błędne | Z punktu widzenia **security** to jest OK (zapobiega enumeracji użytkowników), ale można dodać kontekst |

**Zalecenie:** Zachować ogólny komunikat, ale dodać pomocną sugestię:
```
"Nieprawidłowy login lub hasło. Sprawdź wielkość liter."
```

---

### 2. **Brak wizualnego wyróżnienia błędnych pól**

**Aktualnie:** Pola wyglądają normalnie mimo błędu

**Powinno być:**
- 🔴 Czerwona ramka (border) na obu polach
- Ikona ⚠️ wewnątrz pól

```css
/* Sugerowany styl */
.input-error {
  border: 2px solid #DC3545;
  background: #FFF5F5;
}
```

---

### 3. **Za mały rozmiar i waga fontu komunikatu**

| Aktualnie | Zalecenie |
|-----------|-----------|
| Mały, cienki tekst | Min. 14px, font-weight: 500 |
| Łatwy do przeoczenia | Dodać ikonę ⚠️ przed tekstem |

---

### 4. **Brak ikony ostrzegawczej**

Komunikat tekstowy bez ikony jest mniej zauważalny.

**Zalecenie:**
```
⚠️ Nieprawidłowy login lub hasło
```

---

### 5. **Brak informacji o liczbie prób**

**Problem:** Użytkownik nie wie:
- Ile prób mu zostało
- Czy konto zostanie zablokowane
- Co robić dalej

**Zalecenie:** Po 2-3 próbach pokazać:
```
"Pozostały 2 próby. Po 5 nieudanych próbach konto zostanie 
tymczasowo zablokowane."
```

---

### 6. **Link "Nie pamiętam hasła" niewyróżniony po błędzie**

**Problem:** Po błędzie logowania ten link powinien być bardziej widoczny

**Zalecenie:** 
- Podświetlić link lub dodać tooltip
- Zmienić na: **"Zapomniałeś hasła? Zresetuj je"**

---

### 7. **Brak animacji/feedback wizualnego**

**Problem:** Błąd pojawia się statycznie

**Zalecenie:**
- Delikatne "shake" formularza (300ms)
- Fade-in komunikatu błędu
- Focus automatycznie na pole login

---

## 🎯 Podsumowanie priorytetów

| Priorytet | Problem | Wpływ na UX |
|-----------|---------|-------------|
| 🔴 Wysoki | Brak wizualnego oznaczenia
