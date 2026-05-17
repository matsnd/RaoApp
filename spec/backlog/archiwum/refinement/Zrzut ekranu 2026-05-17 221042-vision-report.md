# Vision Report

**Plik:** C:\projects\repos\RaoApp\spec\backlog\backlog_to_refinement\Zrzut ekranu 2026-05-17 221042.png
**Model:** claude-opus-4-5
**Data:** 2026-05-17T21:33:18.159Z

# Analiza Screenshot - System RAO

## Co pokazuje ten screenshot?

To jest **widok podglądu/wydruku dokumentu "Ogólne Warunki Najmu" (OWN)** - regulaminu/umowy ramowej dla wynajmu maszyn budowlanych.

---

## 🔴 Zidentyfikowany Problem

**Komunikat użytkownika u góry jasno wskazuje problem:**
> "OWN niestety nie przejdzie w takiej formie musi być tak jak mamy teraz. że mieści się na 2 stronach i po prawej stronie zaczyna się punt 3"

**Problem:** Dokument nie mieści się w wymaganym formacie 2-stronicowym, a układ kolumn jest nieprawidłowy (punkt 3 powinien zaczynać się po prawej stronie).

---

## Analiza UI/UX

### ❌ Co wymaga poprawy

| Obszar | Problem |
|--------|---------|
| **Layout dokumentu** | Treść nie jest prawidłowo podzielona na 2 kolumny/strony |
| **Typografia** | Font wygląda na Times New Roman/serif - **niezgodny z design systemem (Montserrat)** |
| **Brak stylizacji RAO** | Dokument wygląda jak surowy Word/PDF, brak navy (#1D2B53) akcentów |
| **Checkbox u góry** | Niezaznaczony, bez kontekstu - użytkownik nie wie co oznacza |
| **Brak kontrolek** | Nie widać przycisków: "Drukuj", "Zapisz PDF", "Edytuj" |
| **Border-radius** | Brak zaokrągleń 12px - ostre krawędzie |

### ⚠️ Problemy funkcjonalne

1. **Brak responsywnego podziału** - system powinien automatycznie dzielić treść na 2 strony
2. **Brak podglądu "przed wydrukiem"** z podziałem na strony
3. **Nie widać numeracji stron**

---

## 💡 Rekomendacje

```
1. Dodać preview z wizualnym podziałem na strony (Page 1 | Page 2)
2. Implementować auto-layout: punkt §3 zawsze na prawej kolumnie
3. Zmienić font na Montserrat
4. Dodać header z logo RAO w kolorze #1D2B53
5. Dodać toolbar: [Drukuj] [PDF] [Edytuj] z border-radius: 12px
```

**Priorytet:** 🔴 Wysoki - dokument prawny musi mieć poprawny format
