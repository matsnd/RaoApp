# extract_legacy_pdfs.py — ekstrakcja tekstu z legacy PDFów

**Zadanie:** RAO-P2-059 (usługi dodatkowe — migracja plain-text → per-artikel)
**Data:** 2026-07-01

## Co robi

Ekstraktuje tekst z 4 legacy PDFów (2 umowy + 2 protokoły PZO) dostarczonych przez operatora,
żeby zweryfikować wzorce usług dodatkowych w starych dokumentach.

## Source PDFs

| Plik | Typ | Numer | Sekcja "Inne usługi" |
|------|-----|-------|----------------------|
| `S129_2026_own.pdf` | Umowa najmu (S) | S129/2026 | 6 usług + 4 uwagi |
| `S130_2026G_own.pdf` | Umowa usługi (U) | S130/2026G | **PUSTA** (tylko tekst zobowiązania) |
| `PZO_S129_2026.pdf` | Protokół zdawczo-odbiorczy | S129/2026 | brak (PZO nie ma usług) |
| `PZO_S130_2026G.pdf` | Protokół wykonania usługi | S130/2026G | brak (PZO nie ma usług) |

## Output

`spec/technical/legacy_samples/pzo_umowy_extracted/*.txt` — pełny tekst per PDF.

## Wzorce usług dodatkowych (potwierdzone z S129/2026)

```
- Transport: 500.00 zł dostawa / 500.00 zł odbiór
- Czyszczenie maszyny po wynajmie (zabrudzenia drobne): 150.00 zł - 400.00 zł
- Czyszczenie maszyny po wynajmie (zabrudzenia trudnościeralne): 400.00 zł - 1500.00 zł
- Usługa tankowania: 200.00 zł (plus koszt paliwa)
- Ponadnormatywny przestój transportu: 200.00 zł / h - 300.00 zł / h
- Nieuzasadnione wezwanie serwisowe: 280,00 zł (plus transport)
```

**Uwaga:** kwota `280,00 zł` (przecinek) vs `500.00 zł` (kropka) — niespójność w starych danych.
Parser migracji musi normalizować (replace `,` → `.`).

## Sekcja "Uwagi" (też w "Inne usługi" na PDF)

```
- Doba wynajmu obejmuje 1 dzień kalendarzowy (do 8 godz. pracy jednego dnia)
- Zgłoszenie zwrotu urządzenia: pisemnie, min. z jednodniowym wyprzedzeniem
- Ilość dni pracy w tygodniu: 6
- dokumentacja zdjęciowa: wykonano
```

Te 4 pozycje to **nie usługi dodatkowe** — to warunki umowy (powinny trafić do `contract.notes` lub osobnej sekcji, nie do `contract_service_fees`).

## Wniosek dla migracji (P2-059)

1. **Typ S (najem):** 6 usług dodatkowych (Transport, Czyszczenie×2, Tankowanie, Przestój, Serwis) — parsowalne regex
2. **Typ U (usługa):** sekcja "Inne usługi" pusta — usługi dla typ U są w `firma.uslugi2` (Transport + Operator), ale nie zawsze kopiowane
3. **PZO:** nie zawiera usług — nie wymaga migracji
4. **Mieszanie usług i uwag:** w starym PDF "Inne usługi" i "Uwagi" są w tej samej sekcji tabeli — parser musi rozróżnić (usługi mają kwoty, uwagi nie)
