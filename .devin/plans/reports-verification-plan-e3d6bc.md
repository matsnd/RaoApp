# Plan weryfikacji i dopasowania szablonów raportów (OWN oraz PZO) 1:1 ze wzorcami

Ten plan opisuje wdrożenie zautomatyzowanej oraz wizualnej pętli weryfikacji wygenerowanych umów (OWN) oraz protokołów zdawczo-odbiorczych (PZO), generując obrazy PNG strona po stronie i porównując je bezpośrednio z dostarczonymi plikami referencyjnymi w celu osiągnięcia 100% zgodności formatowania i pieczątek, z uwzględnieniem podziału na protokoły dla maszyn (S) oraz usług (U).

## 📋 Status i zakres prac

We wzorcowym katalogu `spec/archive/reference_reports/` znajdują się pliki:
- `S129_2026_own (1).pdf` i `S130_2026G_own (1).pdf` – Wzorcowe umowy z Ogólnymi Warunkami Najmu (OWN)
- `PZO_S129_2026 (1).pdf` i `PZO_S130_2026G (1).pdf` – Wzorcowe protokoły zdawczo-odbiorcze (PZO)
- W folderze `own/` znajdują się dodatkowo oryginalne pliki PDF/DOCX (`ownA.pdf`, `ownU.pdf`).

### ⚠️ Ważne rozróżnienie: Maszyny (Sprzęt) vs Usługi
Istnieją osobne szablony i flow generowania dla maszyn (typ `S`) oraz usług (typ `U`):
- **Maszyny (S)**: Umowa `contract.html` + Protokół `protocol_zo.html` / `protocol_zo_nodata.html`
- **Usługi (U)**: Umowa `contract_u.html` + Protokół `protocol_zo_u.html` / `protocol_zo_nodata_u.html`

Weryfikacja i dostosowanie szablonów będzie realizowane dla obu tych ścieżek niezależnie, aby upewnić się, że protokoły dla usług nie zawierają pól specyficznych dla maszyn (i odwrotnie), a formatowanie i rozmieszczenie elementów jest spójne i dopasowane do referencyjnych plików.

## 🛠️ Kroki Planu

### Krok 1: Wygenerowanie zrzutów ekranowych plików referencyjnych (PNG)
- Uruchomimy istniejący skrypt `spec/technical/scripts/convert_pdf_to_screenshots.py` w celu przekonwertowania wszystkich stron wzorcowych PDF na wysokiej jakości obrazy PNG (za pomocą biblioteki `pymupdf / fitz`).
- Wyniki zapiszemy w nowo utworzonym folderze `spec/archive/reference_screenshots/`.

### Krok 2: Przygotowanie danych testowych (Seeding)
- Pobierzemy z bazy danych pierwsze lepsze istniejące umowy typu sprzętowego (`S`) oraz usługowego (`U`) i użyjemy ich do wygenerowania dokumentów testowych. Nie ma potrzeby ręcznego seedowania konkretnych numerów S129 i S130.
- Na podstawie tych umów wygenerujemy dokumenty i dokonamy porównania układu kolumn, marginesów i elementów z plikami referencyjnymi.

### Krok 3: Wygenerowanie nowych PDF-ów z aplikacji i konwersja na PNG
- Uruchomimy serwer backendowy.
- Za pomocą skryptu Python wyślemy zapytania API o wygenerowanie dokumentów dla pobranych z bazy umów (sprzętowej i usługowej) w wersjach:
  - Umowa najmu (Contract - typy S i U)
  - Protokół zdawczo-odbiorczy (PZO - typy S i U, w tym z danymi i bez danych)
- Zapiszemy wygenerowane PDF-y i przekonwertujemy je na obrazy PNG (strona po stronie) w folderze `spec/archive/generated_screenshots/`.

### Krok 4: Analiza wizualna i dopasowanie szablonów (Pętla "do skutku")
- Porównamy wygenerowane PNG z wzorcowymi PNG, analizując:
  - **OWN (Ogólne Warunki Najmu)**: rozmieszczenie tekstu, Times New Roman, dwukolumnowy układ, justowanie, marginesy strony (35px, 40px, 60px, 40px), podział stron, nagłówki paragrafów (§ 1 - § 7).
  - **Protokoły PZO dla Usług i Maszyn**:
    - Usunięcie/zamiana pól sprzętowych w protokołach usługowych (np. stan licznika, motogodziny, akcesoria maszyny itp., zgodnie z wzorcem usługowym).
    - Sprawdzenie tabel i parametrów technicznych maszyn w protokole sprzętowym.
  - **Pieczątki i podpisy**: pozycjonowanie obrazu pieczątki `company_stamp.jpg` (lub podpisu) na dole strony OWN oraz w sekcjach podpisów protokołów. Pieczątka musi być wklejona identycznie jak we wzorcowych.
  - **Formatowanie i kolumny tabeli**: dopasowanie szerokości kolumn i rozmieszczenia tekstu w tabeli maszyn oraz innych usług/uwag.
- Będziemy iteracyjnie modyfikować szablony HTML/CSS (`backend/reports/templates/contract.html`, `contract_u.html`, `protocol_zo.html`, `protocol_zo_u.html` itp.), regenerować PDF-y i porównywać PNG, aż do osiągnięcia pełnej zgodności.

### Krok 5: Walidacja końcowa i synchronizacja dokumentacji
- Uruchomimy testy smoke i E2E (`e2e/tests/01-login.spec.ts` oraz `07-reports.spec.ts`), aby upewnić się, że nie wprowadzimistycznej regresji w generowaniu raportów.
- Zaktualizujemy odpowiednie specyfikacje w `spec/core/` (zgodnie z regułą `rao-spec-sync`).

---

## ❓ Pytania do Użytkownika

Przed przystąpieniem do realizacji chcielibyśmy potwierdzić poniższe kwestie:
1. **Czy dane dla umów S129 (sprzętowa) i S130 (usługowa) są już w bazie danych**, czy mam przygotować skrypt seedujący, który je utworzy?
2. **Którego pliku graficznego dla pieczątki z podpisem mam użyć** jako ostatecznego wzorca? Czy obecny `backend/reports/assets/company_stamp.jpg` jest właściwy, czy mam podstawić np. `stamp_from_old_app.png` z głównego katalogu?
