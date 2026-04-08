# 📋 Product Design Document — Eksplorator Raportów

> **Zadania:** #12 (statystyki per maszyna), #13 (filtrowanie usług), #14 (lokalizacje)  
> **Status:** Draft do akceptacji Product Ownera  
> **Autorzy:** Product Owner + UX Designer  
> **Data:** 2026-04-08

---

## 🎯 Problem użytkownika

**User story:**
> Jako kierownik floty chcę znaleźć konkretną maszynę (np. "TS-042") i zobaczyć jej historię wynajmów, przychód i wykorzystanie w danym okresie, żeby ocenić czy opłaca się ją utrzymywać.

**Aktualne frustrujące:**
- Raporty pokazują tylko TOP 10 — nie mogę znaleźć maszyny poza topem
- Nie widzę szczegółów per konkretna maszyna (kto wynajmował, za ile, na ile dni)
- Nie mogę filtrować po usługach (ile zarobiłem na transporcie?)
- Nie mogę filtrować po miastach (gdzie najczęściej wynajmuję?)

---

## 🏗️ Proponowane rozwiązanie — Eksplorator

### Koncept: "Google dla Twojej floty"

Jeden search box + filtry = pełna wyszukiwarka po wszystkich danych.

### Trzy tryby wyszukiwania (3 pod-taby w Eksploratorze):

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🔍 EKSPLORATOR                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│  [🔍 Wszystko]  [🏗️ Maszyny]  [🛠️ Usługi]  [📍 Lokalizacje]            │
│  ─────────────────────────────────────────────────────────────────────  │
│                                                                         │
│  Szukaj: [______________________________]  [Szukaj]                    │
│                                                                         │
│  Filtry:  [Okres: Ten miesiąc ▼]  [Status: Wszystkie ▼]                │
│                                                                         │
│  ════════════════════════════════════════════════════════════════════   │
│                                                                         │
│  Wyniki:                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Maszyna            │ Nr wewn. │ Kontrahent       │ Data   │ Kwota │   │
│  │ ───────────────────────────────────────────────────────────────│   │
│  │ Ładowarka 17m      │ TS-042   │ DAR-TECH         │ 15.03  │ 1250  │   │
│  │ Transport          │ —        │ DAR-TECH         │ 15.03  │ 350   │   │
│  │ Podnośnik 12m      │ TS-015   │ Jungle Park      │ 14.03  │ 890   │   │
│  │ ... (paginacja: 1 2 3 ... 12)                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  📊 Podsumowanie: Przychód: 45 230 zł | 127 dni wynajmu | 24 umowy     │
│                                                                         │
│  [📥 Export CSV]  [🖨️ Drukuj]                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📑 Szczegóły per pod-tab

### 1️⃣ Tab "🔍 Wszystko" — Universal Search

**Służy do:** Szybkiego znalezienia czegokolwiek (jedno pole, jedna tabela, typ w kolumnie)

**Search box obsługuje:**
- Nazwa maszyny ("ładowarka", "podnośnik")
- Numer wewnętrzny ("TS-042")
- Nazwa kontrahenta ("DAR-TECH")
- Miasto ("Warszawa", "Pruszków")
- Numer umowy ("S205/2026")

**Layout — jedna tabela z typami:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Szukaj: [TS-042________________________]  [Szukaj]            │
│                                                                 │
│  Wyniki (12):                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Typ      │ Nazwa                │ Kontrahent   │ Data   │ Kwota │
│  │──────────┼──────────────────────┼──────────────┼────────┼───────│
│  │ 🏗️       │ Ładowarka 17m (TS-042│ DAR-TECH     │ 15.03  │ 1250  │
│  │ 🏗️       │ Ładowarka 17m (TS-042│ Budowlanka   │ 01.03  │ 600   │
│  │ 🛠️       │ Transport            │ DAR-TECH     │ 15.03  │ 350   │
│  │ 📍       │ Warszawa             │ —            │ —      │ 45230 │
│  │ 👤       │ DAR-TECH (kontrahent)│ —            │ —      │ 15200 │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Legenda: 🏗️ Maszyna  🛠️ Usługa  📍 Miasto  👤 Kontrahent       │
└─────────────────────────────────────────────────────────────────┘
```

**Wyniki:**
- Jedna tabela, posortowane: najnowsze pierwsze
- Kolumna "Typ" z ikoną/etykietą co to jest
- Kliknięcie w wiersz = szczegóły (przejście do odpowiedniego taba)
- Max 50 wyników na stronę

---

### 2️⃣ Tab "🏗️ Maszyny" — Szczegóły per maszyna

**Służy do:** Analiza konkretnej maszyny (ROI, wykorzystanie)

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  [Wybierz maszynę ▼]  [lub wpisz nr wewnętrzny: TS-___ ]        │
│                                                                 │
│  ╔═══════════════════════════════════════════════════════════╗  │
│  ║  📊 MASZYNA: Ładowarka teleskopowa 17m (TS-042)          ║  │
│  ║                                                            ║  │
│  ║  Okres: Styczeń — Marzec 2026                             ║  │
│  ║  ┌────────────┐  ┌────────────┐  ┌────────────┐            ║  │
│  ║  │ 12 450 zł  │  │ 45 dni     │  │ 276 zł/dz  │            ║  │
│  ║  │ Przychód   │  │ Wynajmu    │  │ Średnio    │            ║  │
│  ║  └────────────┘  └────────────┘  └────────────┘            ║  │
│  ║  Wykorzystanie: 50% (45/90 dni w okresie)                ║  │
│  ╚═══════════════════════════════════════════════════════════╝  │
│                                                                 │
│  📋 Historia wynajmów:                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Data       │ Kontrahent        │ Dni  │ Stawka  │ Suma  │    │
│  │─────────────────────────────────────────────────────────│    │
│  │ 15.03.2026 │ DAR-TECH          │ 5    │ 250 zł  │ 1250  │    │
│  │ 01.03.2026 │ Budowlanka Nowak  │ 3    │ 200 zł  │ 600   │    │
│  │ ...                                                    │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**Metryki per maszyna:**
- Przychód w okresie (suma)
- Liczba dni wynajmu (suma)
- Średni przychód/dzień (przychód/dni)
- % Wykorzystania (dni wynajmu/dni w okresie)
- Liczba umów

**Wykres:** Timeline wynajmów (mini Gantt) — widać kiedy maszyna była zajęta/wolna

---

### 3️⃣ Tab "🛠️ Usługi" — Analiza usług dodatkowych

**Służy do:** Sprawdź ile zarobiłem na transporcie, myciu, ładowaniu akumulatorów

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Filtr usługi: [Wszystkie ▼]  [Transport]  [Mycie]  [Ładowanie]  │
│                                                                 │
│  📊 Podsumowanie usług:                                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Usługa         │ Ilość   │ Przychód    │ % całości   │    │
│  │────────────────────────────────────────────────────────│    │
│  │ Transport      │ 45      │ 15 750 zł   │ 35%         │    │
│  │ Mycie          │ 28      │ 5 600 zł    │ 12%         │    │
│  │ Ładowanie akum │ 12      │ 2 400 zł    │ 5%          │    │
│  │ Tankowanie     │ 8       │ 1 600 zł    │ 4%          │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  📈 Wykres: Rozkład usług w czasie (bar chart miesiącami)      │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4️⃣ Tab "📍 Lokalizacje" — Mapa wynajmów

**Służy do:** Gdzie najczęściej wynajmuję? Planowanie logistyki.

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🗺️ Widok: [Lista ▼]  [Mapa — jeśli zintegrujemy później]        │
│                                                                 │
│  Filtr: [Województwo: Wszystkie ▼]  [Miasto: ____________]       │
│                                                                 │
│  📊 Ranking lokalizacji:                                        │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ # │ Miasto         │ Umowy │ Dni   │ Przychód        │    │
│  │───┼────────────────┼───────┼───────┼─────────────────│    │
│  │ 1 │ Warszawa       │ 45    │ 120   │ 45 000 zł       │    │
│  │ 2 │ Pruszków       │ 12    │ 35    │ 12 400 zł       │    │
│  │ 3 │ Piaseczno      │ 8     │ 22    │ 8 200 zł        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  🔍 Szczegóły miasta (kliknij w wiersz):                      │
│  └─> Lista wszystkich wynajmów w tym mieście                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Filtry globalne (dostępne we wszystkich tabach)

| Filtr | Opcje | Domyślnie |
|-------|-------|-----------|
| **Okres** | Ten miesiąc / Ten kwartał / Ten rok / Własny | Ten miesiąc |
| **Status umowy** | Wszystkie / Aktywne / Zakończone / Przyszłe | Wszystkie |
| **Kontrahent** | Dropdown + search | Wszystkie |
| **Oddział** | Dropdown (jeśli multi-branch) | Mój oddział |

---

## ✅ Acceptance Criteria (Definition of Done)

### Kryteria ogólne:
- [ ] Wszystkie 4 taby działają i przełączają się bez reloadu
- [ ] Wyszukiwanie ma debounce 300ms (nie wysyła requestu po każdej literze)
- [ ] Wyniki paginowane (max 50/stronę)
- [ ] Loading state (spinner) podczas fetchowania
- [ ] Empty state gdy brak wyników („Spróbuj zmienić filtry”)

### Kryteria per tab:

**Tab Wszystko:**
- [ ] Search box wyszukuje po: nazwa maszyny, nr wewnętrzny, kontrahent, miasto, nr umowy
- [ ] Wyniki pokazują: typ (ikona), nazwa, data, kwota, status

**Tab Maszyny:**
- [ ] Dropdown pokazuje wszystkie maszyny z nr wewnętrznym
- [ ] Można wyszukać maszynę po nr wewnętrznym
- [ ] Po wyborze maszyny pokazuje się panel metryk (przychód, dni, średnia, %)
- [ ] Tabela historii sortowalna (data, kontrahent, kwota)
- [ ] Wykres timeline wynajmów renderuje się poprawnie

**Tab Usługi:**
- [ ] Filtry usług jako chipsy (jednoklikowe)
- [ ] Tabela podsumowania pokazuje sumy i %
- [ ] Można kliknąć w usługę = przejście do szczegółów tej usługi

**Tab Lokalizacje:**
- [ ] Lista sortowalna (umowy, dni, przychód)
- [ ] Kliknięcie w miasto = rozwija szczegóły wynajmów
- [ ] Filtrowanie po województwie (jeśli mamy dane)

---

## 📊 Metryki sukcesu (jak zmierzyć czy to działa)

1. **Czas do odpowiedzi:** User znajduje konkretną maszynę < 30 sekund
2. **Zadowolenie:** Brak complainów "nie mogę znaleźć maszyny"
3. **Usage:** Eksplorator używany częściej niż stary raport "Top 10"

---

## ⚡ Ograniczenia i decyzje (co NIE robimy w tej wersji)

| Nie w tej wersji           | Dlaczego                         | Kiedy może być           |
| -------------------------- | -------------------------------- | ------------------------ |
| ~~Export CSV~~             | MVP — screen wystarczy           | P3, na życzenie          |
| Mapa Google/Leaflet        | Za dużo pracy, wymaga klucza API | P3, jeśli zespół urośnie |
| Zaawansowane raporty PDF   | Podstawowy podgląd wystarczy     | P2, na życzenie          |
| Porównanie maszyn (A vs B) | UI skomplikowane                 | P2                       |
| Predykcje/analiza trendów  | Wymaga ML, zbyt duże             | P3                       |
| Rezerwacje maszyn (z #15)  | To osobne zadanie                | P1, po zatwierdzeniu #15 |

---

## 🗓️ Estymacja i podział pracy

| Krok | Zadanie | Backend | Frontend | Razem |
|------|---------|---------|----------|-------|
 1 | Endpoint search universal | 1h | — | 1h |
 2 | Endpoint per maszyna (metryki) | 1h | — | 1h |
 3 | Endpoint usługi (agregacja) | 0.5h | — | 0.5h |
 4 | Endpoint lokalizacje | 0.5h | — | 0.5h |
 5 | UI — tab Wszystko | — | 1h | 1h |
 6 | UI — tab Maszyny (szczegóły) | — | 1.5h | 1.5h |
 7 | UI — tab Usługi | — | 1h | 1h |
 8 | UI — tab Lokalizacje | — | 1h | 1h |
| **RAZEM** | | **3.5h** | **4.5h** | **~7-8h** |

---

## 🎯 Rekomendacja PO + UX Designer

> **Zatwierdzamy wersję z 4 pod-tabami w jednym Eksploratorze.**
> 
> To daje userowi jedno miejsce zamiast 3 osobnych ekranów, 
> zachowując spójność z obecnym designem (taby w raportach).
> 
> Priorytet implementacji:
> 1. Tab "Wszystko" (szybki win, używa istniejącego API)
> 2. Tab "Maszyny" (najważniejszy dla ROI)
> 3. Tab "Usługi" i "Lokalizacje" (można dodać później)

---

## ✅ AKCEPTACJA PRODUCT OWNERA

| | |
|---|---|
| **Akceptuję projekt?** | [ ] Tak / [ ] Nie — wymagane zmiany: _______ |
| **Priorytet:** | [ ] P0 — zrób TERAZ / [ ] P1 — w tym tygodniu / [ ] P2 — potem |
| **Wersja minimalna (MVP):** | [ ] Tylko tab "Maszyny" / [ ] Wszystkie 4 taby od razu |
| **Uwagi / zmiany:** | _________________________________ |

---

> **Po akceptacji:** Przechodzimy do implementacji `/agent-loop-do-skutku`.
