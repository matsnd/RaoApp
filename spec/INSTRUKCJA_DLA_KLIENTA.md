# Instrukcja dla klienta — RAO

> **Cel:** Wyjaśnienie zmian i zasad działania systemu RAO w języku biznesowym (bez żargonu technicznego).
> **Aktualizacja:** 2026-06-29
> **Status:** Żywy dokument — dodawaj nowe sekcje przy każdej istotnej zmianie

---

## Spis treści

1. [Naliczanie dni wynajmu (naprawa 2026-06-29)](#1-naliczanie-dni-wynajmu-naprawa-2026-06-29)
2. *(kolejne sekcje dodawane w miarę realizacji zadań)*

---

## 1. Naliczanie dni wynajmu (naprawa 2026-06-29)

### Co się zmieniło

Naprawiliśmy błędne wyliczanie daty końcowej okresu umowy. Wcześniej system przy 5 dniach wynajmu od 25.06 pokazywał 28.06 zamiast 30.06. Problem wynikał z dwóch błędów:

1. **Błędne liczenie czasu** — system używał czasu uniwersalnego (UTC), który w polskim czasie letnim cofa datę o jeden dzień do tyłu
2. **Brak pomijania niedziel** — system liczył dni kalendarzowe zamiast dni roboczych w tygodniu 6-dniowym

### Zasada naliczania

System liczy dni wynajmu według **6-dniowego tygodnia pracy** (poniedziałek–sobota). Niedziele są pomijane. Dzień rozpoczęcia wynajmu **zawsze liczy się jako pierwszy dzień**, niezależnie od tego w jaki dzień tygodnia wypada.

---

### Jak działa liczenie przy tworzeniu umowy

Podajesz datę początkową i liczbę dni. System dodaje kolejne dni robocze, pomijając niedziele.

**Przykłady:**

| Data początkowa | Liczba dni | Kolejne dni | Data końcowa | Wyjaśnienie |
|-----------------|------------|-------------|--------------|-------------|
| 25.06 (czwartek) | 5 | 25 → 26 → 27 → ~~28~~ → 29 → 30 | **30.06** | 28.06 to niedziela — pominięta |
| 25.06 (czwartek) | 1 | 25 | **25.06** | Jeden dzień = ten sam dzień |
| 25.06 (czwartek) | 6 | 25 → 26 → 27 → ~~28~~ → 29 → 30 → 01 | **01.07** | Jedna niedziela pominięta |
| 28.06 (niedziela) | 5 | 28 → 29 → 30 → 01 → 02 | **02.07** | Start w niedzielę = pierwszy dzień, potem 4 dni robocze |
| 28.06 (niedziela) | 1 | 28 | **28.06** | Niedziela też może być pierwszym dniem |
| 31.12.2026 (czwartek) | 3 | 31.12 → 01.01 → 02.01 | **02.01.2027** | Przejście przez nowy rok działa normalnie |
| 10.06 (środa) | 16 | 10 → 11 → 12 → 13 → ~~14~~ → 15 → ... → 27 | **27.06** | Dwie niedziele pominięte (14.06 i 21.06) |

---

### Jak działa liczenie przy edycji umowy

Przy otwieraniu istniejącej umowy do edycji system odlicza dni od daty początkowej do końcowej, pomijając niedziele. Data początkowa **zawsze liczy się jako pierwszy dzień** — nawet jeśli to niedziela. Dzięki temu liczba dni pokazana przy edycji jest zgodna z tą wprowadzoną przy tworzeniu umowy.

**Przykłady:**

| Data początkowa | Data końcowa | Liczba dni | Wyjaśnienie |
|-----------------|--------------|------------|-------------|
| 25.06 | 30.06 | **5** | 25 (dzień 1) + 26, 27, 29, 30 = 5 (28.06 = niedziela, pominięta) |
| 28.06 (niedziela) | 02.07 | **5** | 28 (dzień 1) + 29, 30, 01, 02 = 5 |
| 10.06 | 27.06 | **16** | 10 (dzień 1) + 15 dni roboczych (14.06 i 21.06 pominięte) |
| 25.06 | 25.06 | **1** | Ten sam dzień = 1 dzień |

---

### Spójność tworzenia i edycji (gwarancja)

Data początkowa **zawsze** jest pierwszym dniem wynajmu, niezależnie czy to niedziela czy dzień roboczy. Dzięki temu:

- Przy tworzeniu umowy: **25.06 + 5 dni = 30.06**
- Przy edycji tej samej umowy: **25.06 – 30.06 = 5 dni** ✓

- Przy tworzeniu umowy: **28.06 (niedziela) + 5 dni = 02.07**
- Przy edycji tej samej umowy: **28.06 – 02.07 = 5 dni** ✓

**Wcześniej był błąd:** przy edycji umowy rozpoczynającej się w niedzielę system pokazywał o 1 dzień mniej (4 zamiast 5), bo pomijał niedzielę jako dzień początkowy. Naprawione — niedziela startowa zawsze liczy się jako pierwszy dzień.

---

### Sytuacje szczególne

| Sytuacja | Zachowanie systemu | Przykład |
|----------|---------------------|----------|
| Jeden dzień wynajmu | Data końcowa = data początkowa (ten sam dzień) | 25.06 + 1 = 25.06 |
| Start w niedzielę | Niedziela = pierwszy dzień, potem liczone normalnie | 28.06 + 5 = 02.07 |
| Niedziela w środku okresu | Pominięta w liczeniu | 25.06 + 5 = 30.06 (pominięta 28.06) |
| Kilka niedziel w okresie | Każda pominięta | 10.06 + 16 dni = 27.06 (pominięte 14.06 i 21.06) |
| Przejście przez koniec miesiąca | Normalne liczenie | 30.06 + 3 dni = 03.07 (pominięta 05.07) |
| Przejście przez nowy rok | Normalne liczenie | 31.12.2026 + 3 dni = 02.01.2027 |

---

### Podsumowanie w jednym zdaniu

**"5 dni"** oznacza 5 dni roboczych (poniedziałek–sobota); niedziele nie są liczone. Data początkowa zawsze jest pierwszym dniem wynajmu, nawet jeśli to niedziela. Przy edycji umowy liczba dni jest zgodna z tą wprowadzoną przy tworzeniu — liczba nie "skacze".

---

<!--
Sekcje do dodania w przyszłości:
- P1-015: Ukrywanie numerów telefonów na umowie PDF
- P1-018: Usunięcie pieczątki z pierwszej strony umowy
- P1-016: Adres dostawy na protokole ZO
- P1-019: Nowy wygląd umowy usługi
- P1-022: Zmiana nazewnictwa umów (S/G na końcu)
-->
