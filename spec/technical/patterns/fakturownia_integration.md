# Fakturownia Integration Pattern (RAO-P2-012 Refinement)

## Opis
Wzorzec integracji z systemem fakturowania Fakturownia (publiczne API) dla automatycznego pobierania kosztów do panelu rozliczenia umowy. Ten wzorzec jest wynikiem pełnego scrum refinement (PO, Tech Lead, QA, Security) i może być użyty dla przyszłych integracji z systemami fakturowania.

## Kontekst RAO-P2-012

**Zadanie:** Integracja z Fakturownia — automatyczne pobieranie kosztów  
**Priorytet:** P2  
**Size:** L (12h)  
**Status:** ODŁOŻONE po refinement — rekomendacja PO  
**Depends_on:** RAO-P1-012 (Panel rozliczenia umowy — DONE)

---

## Business Analysis (Product Owner)

### Problem statement
**User story:** Jako handlowiec/księgowa, chcę żeby koszty firmy (faktury zakupowe od dostawców/serwisu) były automatycznie pobierane z Fakturownia do panelu rozliczenia umowy, żebym nie musiała ręcznie przepisywać kwot z systemu fakturowego.

**Pain point:**
- Bez integracji: użytkownik otwiera Fakturownia, szuka faktur po OID umowy, przepisuje kwoty ręcznie do panelu rozliczenia RAO
- Jedna umowa = często **kilka faktur kosztowych** (paliwo, serwis, transport, części)
- Impact: ~3–5 min/umowę × 10 umów/tydz × ~50 tyg = **~30h/rok/userze**

### ROI
- Czas oszczędzony: ~30–50 min/tydz/user
- Roczny zysk: ~50–150h pracy + redukcja błędów w marży
- Koszt implementacji: 12h dev
- Break-even: ~2–3 miesiące

### Feature parity
- Legacy WinForms: integracji z Fakturownia **NIE było** → to jest nowa wartość, nie parity

### Rekomendacja PO
**ODŁOŻYC po zakończeniu wszystkich P0 i P1**

Uzasadnienie:
- Wartość biznesowa realna, ale P2 poprawna (workaround istnieje)
- 12h budżet — nie odpalać dopóki userzy nie potwierdzą pain point
- Czerwone flagi:
  - Automatyczne mapowanie po nazwie → wyciąć z v1 (tylko product_id)
  - Usługi dodatkowe → nie doprecyzowane
  - Uprawnienia → nie doprecyzowane

### UX Flow
**Setup jednorazowy (admin, ~5 min):**
1. Ustawienia → zakładka "Integracje" → karta "Fakturownia"
2. Toggle "Włącz integrację" + pola: Adres systemu + Klucz API
3. Guzik "Sprawdź połączenie" → ✓ "Połączono z Fakturownia"
4. Guzik "Pobierz produkty z Fakturownia" → tabela 2-kolumnowa (FA product ↔ RAO article)
5. Zapisz mapowanie

**Codzienne użycie (handlowiec, ~10s):**
1. Otwiera umowę → zakładka "Rozliczenie"
2. Widzi guzik "Pobierz koszty z Fakturownia"
3. Klika → spinner → toast "Pobrano 3 faktury, suma kosztów: 4 250 zł"
4. Tabela rozliczenia wypełnia się automatycznie
5. Sekcja "Pozycje niezmapowane" (jeśli są)
6. User może edytować dowolną wartość (override)
7. Zapisz rozliczenie

---

## Architektura (Tech Lead)

### Struktura modułu
```
backend/integrations/fakturownia/
├── __init__.py
├── models.py        # FakturowniaSettings (singleton), FakturowniaProductMapping
├── schemas.py       # SettingsOut/Update, ProductMappingOut/Create, InvoiceOut
├── client.py        # FakturowniaClient (httpx async, retry, 429 handling)
├── service.py       # logika: load_settings, sync_products, fetch_invoices, aggregate
└── router.py        # /fakturownia/* endpointy
```

### Schema DB
```sql
CREATE TABLE fakturownia_settings (
  id          INT PRIMARY KEY DEFAULT 1,
  enabled     BOOLEAN NOT NULL DEFAULT FALSE,
  api_token   VARCHAR(255) NULL,           -- TODO: encryption at-rest
  domain_url  VARCHAR(255) NULL,           -- np. "toolsmart" (subdomain only)
  last_sync_at DATETIME NULL,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT chk_singleton CHECK (id = 1)
);

CREATE TABLE fakturownia_product_mapping (
  id                       INT PRIMARY KEY AUTO_INCREMENT,
  fakturownia_product_id   BIGINT NOT NULL,
  fakturownia_product_name VARCHAR(255) NOT NULL,
  article_id               INT NULL,
  created_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_fa_product (fakturownia_product_id),
  CONSTRAINT fk_fpm_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL
);
```

### Plan warstwowy
1. Spec — dopisać sekcję Fakturownia do 07_integrations.md + DDL do 01_database.md
2. DB — SQLAlchemy models + ALTER/CREATE IF NOT EXISTS w main.py
3. Backend — client.py (httpx, retry) + service.py + router.py + schemas.py
4. Frontend — stores/fakturownia.ts + tab w SettingsView + mapping UI + button w umowie
5. UX — projekt panelu rozliczenia z tabelą faktur + sumowaniem
6. QA — unit (mock FA), integration, E2E
7. Spec sync — aktualizacja spec

### Ryzyka techniczne
- Rate limit Fakturownia → httpx + retry z exp. backoff
- Token plaintext → min: mask w response, docelowo: encryption
- Mapping niespójny → podwójna strategia (product_id + fallback po nazwie)
- Wiele faktur/korekty → agregacja z uwzględnieniem korekt
- Zmiana schematu API → wersjonowany klient + health check

---

## Edge Cases (QA Engineer)

### API Fakturownia (network/auth)
1. API down (HTTP 5xx) → toast + fallback do ręcznego wpisywania
2. API timeout (>30s) → timeout na httpx + loading state z anulowaniem
3. Invalid api_token (401) → komunikat "Token nieważny, sprawdź ustawienia"
4. Rate limit (429) → retry z backoff
5. Invalid domain_url → walidacja URL przy zapisie ustawień
6. Self-signed cert → jasny komunikat
7. API zwraca pustą tablicę → "Brak faktur" (NIE error)
8. API paginacja >100 produktów → testować per_page/page params

### OID / dopasowanie umowy
9. OID pusty/null → guzik disabled + tooltip
10. OID ze spacjami/polskimi znakami → URL encoding
11. OID duplikat w wielu umowach → która umowa dostaje koszty?
12. OID istnieje w Fakturownia ale przypisany do innego klienta → security filter

### Product mapping
13. Faktura ma produkt niezmapowany → warning "niezmapowane pozycje"
14. Mapping niekompletny przy starcie → co się dzieje?
15. Mapping orphan (article usunięty) → graceful degradation
16. Fakturownia product_id zmieniony/usunięty → mapping wskazuje na nieistniejący
17. Jeden RAO article → wiele FA products (1:N) → sumowanie?
18. Jeden FA product → wiele RAO articles (N:1) → konflikt?

### Wiele faktur / sumowanie
19. Faktura korygująca (ujemne wartości) → odejmować czy ignorować?
20. Faktura proforma vs VAT → tylko VAT liczy się?
21. Anulowane faktury → wykluczyć
22. Waluty inne niż PLN → konwersja czy error?
23. Pozycja z quantity=0 lub price_net=0 → skip czy zero-cost?
24. Faktura z setkami pozycji → performance (<2s render?)

### UI/UX
25. Double-click "Pobierz koszty" → button disabled during loading
26. Pobierz koszty → edytuj ręcznie → pobierz ponownie → confirm dialog
27. Toggle OFF z istniejącym mapowaniem → mapping zostaje?
28. Migracja danych przy DROP/CREATE → verification gate

### Security
29. API token plaintext w DB → encryption at-rest?
30. API token w logach → redact
31. IDOR na GET /invoices?oid= → ownership check
32. CSRF / token w response → admin only

---

## Security Audit (Security Auditor)

### Krytyczne zagrożenia (P0)
**T1. Plaintext storage API tokena** → AES-GCM encryption at-rest  
**T2. Token expozycja w GET /settings** → mask w response  
**T3. Brak RBAC** → admin only dla settings  
**T4. IDOR na GET /invoices?oid=** → contract_id z ownership check  
**T5. SSRF przez domain_url** → whitelist regex fakturownia.pl

### Średnie zagrożenia (P1)
**T6. Token w logach** → redact filter  
**T7. Brak audit logu** → fakturownia.token_changed, mapping_changed, invoices_fetched  
**T8. Brak rate limitingu** → slowapi 10/min/user  
**T9. Data injection → XSS** → Pydantic schema + autoescape  
**T10. CSV/Formula injection** → prefix `'` przy wartościach  
**T11. TLS cert validation** → verify=True enforced  
**T12. Mass-assignment** → Pydantic extra='forbid'

### Rekomendacje
**Encryption at rest:**
```sql
api_token_ciphertext  VARBINARY(512) NOT NULL
api_token_nonce       VARBINARY(12)  NOT NULL
api_token_preview     VARCHAR(16)    NOT NULL  -- "tk_****1234"
```

**RBAC matrix:**
| Endpoint | user | admin |
|---|---|---|
| GET/PUT /settings/fakturownia | ❌ | ✅ |
| PUT /settings/fakturownia/token | ❌ | ✅ |
| GET /fakturownia/products | ❌ | ✅ |
| POST /fakturownia/mapping | ❌ | ✅ |
| GET /fakturownia/invoices?contract_id= | ✅ (ownership) | ✅ |

**Validation:**
- domain_url: `^https://[a-z0-9-]+\.fakturownia\.pl$`
- api_token: min_length=20, max_length=128, pattern
- Response schema: max_length, extra='forbid'

### Security impact
**LOW → HIGH** (krytyczny błąd w backlog!)

---

## Strategia testowania (QA)

### Unit (pytest, backend/tests/unit/test_fakturownia.py)
- fetch_invoices_by_oid z mock (respx)
- map_invoice_lines_to_articles — czysta funkcja
- sum_costs_by_article — agregacja
- Walidatory Pydantic
- Min 15 unit testów

### Integration (pytest + DB)
- CRUD ustawień — duplikaty, FK invalid
- GET invoices — OID pusty → 422; 401 → 502; auth failure → 502
- RBAC — tylko admin może edytować
- Token mask w GET response

### E2E (Playwright, e2e/tests/06-fakturownia.spec.ts)
- Settings: enable integration + save token
- Invalid token → error toast
- Mapping: fetch products + assign to RAO articles
- Contract: button disabled when OID missing
- Contract: button hidden when integration disabled
- Contract: fetch invoices populates settlement panel
- Contract: API down → fallback to manual entry
- Contract: unmapped products → warning badge
- Contract: re-fetch after manual edit → confirm dialog
- Contract: double-click guard (button disabled during loading)

### Manual testing checklist
- Włączenie integracji → prawdziwy token testowy → fetch produktów
- Test na umowie z prawdziwym OID + prawdziwą fakturą
- Test z fakturą korygującą
- Test z 2-3 fakturami pod tym samym OID
- Test wyłączenia integracji
- DROP DATABASE + restart → tabele tworzone?
- Drugi restart bez błędu (idempotentność)
- Test wydajności: OID z >50 pozycji

---

## Wnioski dla przyszłych integracji

### Co zadziałało well
1. **Full scrum refinement** — 4 role (PO, Tech Lead, QA, Security) dały kompletny obraz
2. **Security-first approach** — auditor zidentyfikował 12 krytycznych zagrożeń przed implementacją
3. **Edge cases first** — QA zidentyfikował 32 edge cases, większość w error path
4. **Architecture documentation** — Tech Lead dał szczegółowy plan warstwowy
5. **Business validation** — PO zweryfikował ROI i rekomendował odłożenie

### Co można poprawić
1. **Skrócić scope v1** — wyciąć automapowanie po nazwie (zawodne)
2. **Feature flag** — enabled=false jako default
3. **Encryption at-rest** — od początku, nie jako "TODO"
4. **RBAC matrix** — zdefiniować przed implementacją
5. **Test account** — sandbox/demo konto Fakturownia przed startem

### Lekcje dla RAO
1. P2 zadania mogą mieć HIGH security impact — zawsze security review przed startem
2. Integracje zewnętrzne to "integration hell" — większość bugów w error path
3. ROI uzasadnione ≠ priorytet — P0/P1 first, P2 po
4. Refinement przed implementacją oszczędza 12h budżetu na złe rozwiązanie
5. Spec/technical/ jako miejsce na patterns — przyszłe integracje mogą korzystać z tego wzorca

---

## Status
**RAO-P2-012:** ODŁOŻONE po refinement + RE-REFINEMENT po P1 done + RE-REFINEMENT NOWY SCOPE
**Data refinement:** 2026-05-18
**Data re-refinement:** 2026-05-18 (po zakończeniu wszystkich P1)
**Data re-refinement new scope:** 2026-05-18 (zmiana scope: wyciąć automapowanie po nazwie)
**Decyzja:** Konsensus zespołu (PO, Tech Lead, Security, QA) — ODŁOŻYĆ DALEJ
**Kluczowe powody re-refinement nowy scope:** Pain point nadal niepotwierdzony, 16-20h na hipotezie = over-investment
**Następny krok:** PO przeprowadza wywiad z użytkownikami (1 tydzień), spike 4h jako walidacja przed pełnym scope

---

## Re-Refinement (2026-05-18 — po P1 done)

### Kontekst
Wszystkie zadania P1 zostały zakończone. Zespół (PO, Tech Lead, Security, QA) przeprowadził re-refinement RAO-P2-012 aby zweryfikować czy zadanie powinno zostać rozpoczęte.

### Wyniki re-refinement

| Rola | Rekomendacja | Kluczowy powód |
|------|--------------|----------------|
| **Product Owner** | ODŁOŻYĆ + ZWALIDOWAĆ pain point | Pain point niepotwierdzony przez użytkowników |
| **Tech Lead** | ODŁOŻYĆ DALEJ | Estimate 12h zaniżony → realnie 20-28h (L→XL) |
| **Security Auditor** | ZMIENIĆ PLAN - re-size + split | Security impact HIGH, 12h nie wystarczy na threat model |
| **QA Engineer** | ODŁOŻYĆ DALEJ + ZMIENIĆ TEST STRATEGY | 5 nowych edge cases po P1, test coverage nierealistyczny w 12h |

### Kluczowe zmiany od refinement 2026-05-18

1. **Estimate zaktualizowany:** 12h → 20-28h (L→XL)
   - Security layer sam: 14h (encryption, RBAC, SSRF, audit log, rate limiting)
   - Testy: 18-22h sam QA (15 unit + integration + 9 E2E + 9 manual)
   - Implementacja feature: 0h z 12h budżetu przy pełnym security

2. **Nowe edge cases po P1 (5 nowych):**
   - RBAC (kto może konfigurować integracje?)
   - Rezerwacje (czy faktura może domknąć rezerwację?)
   - Multi-tenancy / scope per user
   - OID collision (2 umowy ten sam OID)
   - Soft-delete contracts

3. **Pain point nadal niepotwierdzony**
   - Refinement 2026-05-18: "userzy muszą potwierdzić pain point"
   - Brak dowodu że 7 dni produkcji P1 zmieniło sytuację
   - ROI 30-50 min/tydz/user × ~5 userów = ~3h/tydz (break-even ~4 tyg tylko jeśli userzy faktycznie używają OID i Fakturownia konsekwentnie)

### Alternatywa (jeśli pain potwierdzony)

**MVP scope (6h, nie 12h):**
- ✅ Settings: token + domain (szyfrowany, RBAC admin-only)
- ✅ Button "Pobierz koszty po OID" → lista pozycji faktury (read-only)
- ✅ User ręcznie wybiera pozycje do rozliczenia
- ❌ WYTNIĆ: automapowanie po nazwie (czerwona flaga 2026-05-18, źródło bugów)
- ❌ WYTNIĆ: osobny widok mapowania produktów (over-engineering dla v1)

### Warunki do powrotu (gate)

- [ ] PO zbiera potwierdzenie pain pointu od ≥3 użytkowników (wywiad 1 tydzień)
- [ ] Jeśli pain potwierdzony → re-estimate na XL (20-28h) + re-refine z RBAC + rezerwacje + OID collision
- [ ] Decyzja security: Fernet vs HashiCorp Vault dla api_token
- [ ] Panel rozliczenia (P1-012) ma min. 2 tyg. produkcyjnej stabilności

### Priorytety alternatywne

**RAO-P2-011 (statystyki po lokalizacji)** — tańsze (S), bezpieczniejsze, mierzalna wartość raportowa. Zalecane przed RAO-P2-012.

---

## Re-Refinement Nowy Scope (2026-05-18 — wycięcie automapowania po nazwie)

### Kontekst
User decision: wyciąć automapowanie po nazwie, zachować mapowanie produktów z Fakturownia do artykułów (tylko product_id).

### Zmiana scope
- **WYCINĆ:** Automapowanie pozycji faktury na artykuły RAO po nazwie (fuzzy matching)
- **ZACHOWAĆ:** Mapowanie produktów (widok mapowania + API + DB tabela fakturownia_product_mapping)
- **ZACHOWAĆ:** Mapowanie tylko po product_id (deterministyczne, nie po nazwie)

### Nowa estimate
**16-20h** (z 20-28h) — oszczędność ~6-8h:
- Security layer: 14h → 9-10h (encryption + SSRF + RBAC wciąż wymagane)
- Test coverage: 18-22h → 9-11h (edge cases 32 → 19 +3 nowe)
- Automapowanie po nazwie: wycięte (−6-8h)

### Wyniki re-refinement nowy scope

| Rola | Nowa estimate | Rekomendacja | Kluczowy powód |
|------|---------------|--------------|----------------|
| **Tech Lead** | 16-20h | ODŁOŻYĆ DALEJ | P1-012 blocker (triaged), security layer 8-10h z 16-20h |
| **Product Owner** | ROI nieznany | ODŁOŻYĆ DALEJ | Pain point nadal niepotwierdzony, 16-20h na hipotezie = over-investment |
| **Security Auditor** | 9-10h security | ODŁOŻYĆ DALEJ | HIGH → MEDIUM-HIGH, encryption + SSRF + RBAC wciąż wymagane |
| **QA Engineer** | 9-11h tests | ZACZĄĆ TERAZ | Edge cases 32→19, ale wymaga spec UX dla unmapped |

### Kluczowe zmiany

1. **Security impact:** HIGH → MEDIUM-HIGH (9 zagrożeń pozostaje, 3 znikło)
   - Znikły: XSS przez nazwę, injection przez fuzzy matching, logic bugs silent mismapping
   - Pozostałe: encryption API tokenu, SSRF, RBAC, IDOR, audit log, rate limiting

2. **Edge cases zredukowane:** 32 → 19 (+3 nowe)
   - Znikają: fuzzy matching, case sensitivity, polskie znaki, encoding mismatch, duplikaty nazw, Unicode normalization, etc. (−13)
   - Nowe: product_id zmieniony/usunięty, mapping do skasowanego artykułu, pozycja bez product_id (+3)

3. **Architektura:**
   - Service layer: jedna ścieżka mapowania zamiast dwóch (`get_article_by_fakturownia_id()`, bez `match_by_name()` fallback)
   - Import flow: pozycje bez mapowania → "unmapped" bucket → user musi ręcznie zmapować w widoku (deterministyczne, brak "magii")
   - Widok mapowania: bez zmian (lista produktów z Fakturownia + select articles RAO)

4. **Nowe ryzyka:**
   - UX friction: każdy nowy produkt w Fakturownia = ręczne mapowanie (akceptowalne)
   - Orphan mapping: produkt usunięty w Fakturownia → 404 przy sync
   - P1-012 blocker: status triaged → wymaga sprawdzenia czy nie jest blocker przed startem

### Alternatywy

1. **Spike 4h (PO):** Tylko `GET /fakturownia/invoices?oid=` + wyświetlenie surowych pozycji faktury w panelu rozliczenia (read-only, bez mapowania, bez DB) — walidacja wartości przed pełnym scope

2. **Split 012a + 012b (Tech Lead):**
   - **RAO-P2-012a (6-8h):** Tabela mapowania + widok CRUD (bez integracji API) — można zrobić niezależnie od P1-012
   - **RAO-P2-012b (10-12h):** Sync + security (po ukończeniu P1-012)

3. **RAO-P2-011 priorytet:** Statystyki po lokalizacji (S) — tańsze, bezpieczniejsze, mierzalna wartość raportowa

### Warunki do powrotu (zaktualizowane)

- [ ] PO przeprowadza wywiad z 2-3 userami (ile faktur/tydzień? ile minut ręczne wpisywanie?)
- [ ] Jeśli > 30 min/tydzień/user × 3 userów = ~2h/tydzień → BUDUJ (ROI: ~10 tygodni)
- [ ] Jeśli < 30 min → ODRZUĆ (RAO-P2-011 lepszy kandydat)
- [ ] Spike 4h jako walidacja przed pełnym scope (opcjonalne)
- [ ] P1-012 ma status done (nie triaged) — blocker usunięty

---

## Re-Refinement Inline Matching (2026-05-18 — matching tylko w panelu rozliczenia)

### Kontekst
User requirement: matching tylko w panelu rozliczenia, nie w Settings; 1 produkt Fakturownia → wiele artykułów RAO (1:N) z contextem umowy. Zespół (UX, Tech Lead, PO, QA) przeprowadził re-refinement.

### Zmiana UX
- **Matching inline w panelu rozliczenia** (accordion pod tabelą rozliczenia, nie modal)
- **Combobox z autocomplete** (nie plain select, nie multi-select) — domyślnie 1:1, świadomie rozszerzane do 1:N przez `[+ Dodaj kolejną]`
- **Context-first** — combobox pokazuje tylko pozycje bieżącej umowy + escape hatch "pokaż wszystkie"
- **Auto-mapping z historii** — bez pytania (95% przypadków poprawne), z indicator `✨` + możliwość cofnięcia
- **Tylko 1 confirm dialog** — re-fetch nadpisujący ręczne edycje. Reszta flow bez friction.
- **1:N walidacja** — real-time "Pozostało: X zł", soft warning przy niedopasowaniu, blocker tylko przy overflow

### Architektura 1:N (Tech Lead proposal)
**Tabela A: `fakturownia_product_mapping` — słownik kandydatów (1:N)**
```sql
CREATE TABLE IF NOT EXISTS fakturownia_product_mapping (
  id                       INT PRIMARY KEY AUTO_INCREMENT,
  fakturownia_product_id   BIGINT       NOT NULL,
  fakturownia_product_name VARCHAR(255) NOT NULL,
  article_id               INT          NOT NULL,
  is_default               BOOLEAN      NOT NULL DEFAULT FALSE,
  is_active                BOOLEAN      NOT NULL DEFAULT TRUE,
  UNIQUE KEY uq_fa_article (fakturownia_product_id, article_id),
  KEY ix_fa_product (fakturownia_product_id),
  CONSTRAINT fk_fpm_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);
```

**Tabela B: `fakturownia_contract_resolution` — context-aware cache**
```sql
CREATE TABLE IF NOT EXISTS fakturownia_contract_resolution (
  id                     INT PRIMARY KEY AUTO_INCREMENT,
  contract_id            INT          NOT NULL,
  fakturownia_product_id BIGINT       NOT NULL,
  invoice_line_hash      VARCHAR(64)  NULL,
  article_id             INT          NOT NULL,
  resolved_by            VARCHAR(50)  NOT NULL,
  resolved_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_contract_fa (contract_id, fakturownia_product_id),
  KEY ix_contract (contract_id),
  CONSTRAINT fk_fcr_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
  CONSTRAINT fk_fcr_article  FOREIGN KEY (article_id)  REFERENCES articles(id)  ON DELETE RESTRICT
);
```

**Algorytm rozstrzygania (priorytet ↓):**
1. `resolutions[fa_pid]` istnieje → `resolved` (cache wygrywa zawsze)
2. `len(contextual) == 1` → `auto_suggested` (jednoznaczne na umowie)
3. `len(contextual) > 1` → `ambiguous` — user musi wybrać
4. `len(contextual) == 0` AND `len(all_cands) >= 1` → `unmapped` z hintem
5. `len(all_cands) == 0` → `unmapped` (wymaga dodania kandydata)

### Architektura 1:1+context (PO proposal)
**Pragmatyczna architektura:**
- `mapping`: 1:1 (FA product → default RAO article)
- Przy fetchu: jeśli umowa ma artykuł zgodny z mappingiem → użyj. Jeśli nie → zaproponuj wybór z artykułów BĘDĄCYCH NA UMOWIE (context-aware suggestion)
- To NIE jest 1:N, to jest 1:1 + smart suggestion. Tańsze i czytelniejsze.

**Uzasadnienie:** Realistyczny use case (paliwo, transport, serwis) jest prawdziwy, ale nie wymaga prawdziwego 1:N w tabeli mappingu. Pełna tabela 1:N BEZ context = bezużyteczna — system nie wie który article wybrać przy auto-fetchu.

### Edge cases (QA)
**15 nowych edge cases (E33-E47):**
- **Persystencja inline mappingu:** Mapping bez zapisu rozliczenia, "Pobierz koszty" ponownie po wykonanym mappingu, cofnięcie/edycja mappingu
- **1:N mapping z contextem umowy:** Konflikt cross-contract, reuse mappingu z innej umowy, artykuł usunięty z umowy, artykuł soft-deleted
- **Context-aware filtering:** Umowa ma 0 pozycji, umowa ma 100+ pozycji, FA product nie pasuje do żadnego artykułu umowy, filtering dropdown
- **UI/UX i race conditions:** Double-click "Pobierz koszty", zamknięcie panelu z dirty mappingiem, refetch costs podczas trwającego mappingu, dwie zakładki przeglądarki

**Priorytetyzacja:**
- **P0 (krytyczne):** 7 edge cases (E33, E34, E36, E38, E40, E44, E45)
- **P1 (ważne):** 6 edge cases (E35, E37, E39, E42, E43, E46)
- **P2 (nice-to-have):** 2 edge cases (E41, E47)

**Wpływ na estimate test coverage:**
- Obecnie: 9-11h (edge cases 32 → 19)
- Po inline matchingu: 15-18h (+6-7h)
- Realny zakres pełnego ficzera: 22-27h

### Estimate
| Pozycja | Stary spec | Inline matching (1:1+context) | Pełne 1:N z contextem |
|---|---|---|---|
| Settings UI (mapping view) | 3h | −3h (cut) + 1h (read-only listing) | jw. |
| Inline matching UI w panelu | 0h | +4h | +5h |
| Mapping logic + context-aware | 2h | +2h (suggestion logic) | +4h (1:N resolution) |
| Backend mapping table | 1h | 1h | 2h (+contract_id, +priority) |
| Security/auth (RBAC: kto może mapować) | included | +2h (nowy problem) | +2h |
| Reszta (client, fetch, sumowanie) | 10h | 10h | 10h |
| **TOTAL** | **16-20h** | **17-21h** | **22-26h** |

### Rekomendacja zespołu
| Rola | Rekomendacja | Kluczowy powód |
|------|--------------|----------------|
| **UX Designer** | Inline matching jest lepszy dla codziennego użycia | Context-first, mniej klików, ale wymaga RBAC |
| **Tech Lead** | Pełne 1:N z contextem jest do implementacji | Architektura rozstrzygnięta, dwie tabele |
| **Product Owner** | 1:N to over-engineering, wystarczy 1:1+context | Realistyczny use case zaspokaja 1:1 + smart suggestion |
| **QA Engineer** | Edge cases zwiększają estimate o +6-7h | 15 nowych edge cases, 7 P0 |

### Konsensus
**ODŁOŻYĆ DALEJ** — pain point nadal niepotwierdzony, koszt re-refine zaczyna konkurować z kosztem walidacji terenowej.

### Rekomendacja PO
**SPIKE 4h** zamiast pełnej implementacji:
1. Backend: `GET /fakturownia/invoices?oid=` — read-only fetch faktur, **bez DB, bez mapping**
2. Frontend: w panelu rozliczenia (po wpisaniu API tokenu w `.env` admina jako hardcoded MVP) — guzik "Pokaż faktury z FA" → lista pozycji **read-only z FA, nazwy bez mapping na RAO articles**
3. Daj 2-3 userom (1 tydzień użycia)
4. Mierz: ile razy klikali? czy przepisywali kwoty? co ich blokowało?

**Po spike — decyzja:**
- ✅ Klikali ≥3x/tydz/user, chcą mappingu → **BUDUJ pełny scope z 1:1+context (17-21h)** LUB pełne 1:N (22-26h) po decyzji architektonicznej
- ❌ Klikali <1x/tydz lub mówili "nie potrzebuję" → **ODRZUĆ na zawsze** (RAO-P2-011 statystyki priorytetowo)

### Warunki do powrotu (zaktualizowane)
- [ ] SPIKE 4h zrealizowany — read-only display faktur w panelu rozliczenia (GET /fakturownia/invoices?oid=)
- [ ] ≥2 userów testowało ≥1 tydzień — pomiar realnego użycia (clicks, time saved)
- [ ] Jeśli użycie potwierdzone (≥3 klik/tydz/user) → BUDUJ z architekturą 1:1+context (17-21h)
- [ ] Jeśli użycie poniżej progu → ODRZUĆ na zawsze, priorytet RAO-P2-011
- [ ] Decyzja architektoniczna: 1:1+context (PO) = WYBRANA, pełne 1:N (Tech Lead) = ODRZUCONE (patrz niżej)
- [ ] Decyzja RBAC: kto może mapować (handlowiec vs admin-only)
- [ ] Decyzja security: token w .env (MVP spike) vs Fernet w DB (production)

---

## Decyzja Architektoniczna (2026-05-18 — doprecyzowanie użytkownika)

**Decyzja:** 1:1+context (PO) = WYBRANA, pełne 1:N (Tech Lead) = ODRZUCONE

### Uzasadnienie użytkownika
- **Faktury read-only** — tylko wyświetlenie, nie edycja
- **Mapping 1:1** — produkty z faktury mapowane w artykułach (FA product → RAO article, nie 1:N)
- **Context umowy** — tylko filtr UI (combobox pokazuje tylko artykuły z tej umowy), nie rozgałęzienie DB
- **Kluczowe stwierdzenie:** "dana maszyna może być tym samym produktem z punktu widzenia naszej aplikacji" — czyli mapping 1:1 jest wystarczający

### Architektura wybrana (1:1+context)

**Tabela mappingu (1:1, nie 1:N):**
```sql
CREATE TABLE IF NOT EXISTS fakturownia_product_mapping (
  id                       INT PRIMARY KEY AUTO_INCREMENT,
  fakturownia_product_id   BIGINT       NOT NULL UNIQUE,  -- 1:1 (UNIQUE)
  fakturownia_product_name VARCHAR(255) NOT NULL,
  article_id               INT          NOT NULL,
  is_default               BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY ix_fa_product (fakturownia_product_id),
  CONSTRAINT fk_fpm_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);
```

**Context umowy = tylko filtr UI, nie rozgałęzienie DB:**
- Backend: `GET /contracts/{id}/fakturownia/invoices` → zwraca pozycje faktury + listę artykułów z tej umowy
- Frontend: combobox pokazuje **tylko artykuły z tej umowy** (context-aware filtering)
- Mapping zapisywany jest globalnie 1:1 (FA product → RAO article), ale user widzi tylko te artykuły które są na bieżącej umowie

**Przykład:**
- FA product "Koparka CAT 320" → mapowany do RAO article "Koparka CAT 320" (1:1)
- Umowa A ma artykuł "Koparka CAT 320" → combobox pokazuje "Koparka CAT 320"
- Umowa B ma artykuł "Dźwig 40t" → combobox pokazuje "Dźwig 40t" (nawet jeśli FA product "Koparka CAT 320" był mapowany wcześniej)
- User może wymusić mapping na inny artykuł (escape hatch "pokaż wszystkie")

### Architektura odrzucona (pełne 1:N)

**Powód odrzucenia:** Over-engineering
- Tabela B: `fakturownia_contract_resolution` (context-aware cache) — NIE POTRZEBNA
- Algorytm rozstrzygania 5-stopniowy — NIE POTRZEBNY
- Dodatkowe +5h estimate — NIE UZASADNIONE

**Kiedy pełne 1:N byłby potrzebny:** Gdy ten sam produkt FA musi być mapowany do różnych artykułów RAO **jednocześnie** (np. rozdzielenie kosztów 50/50). To NIE jest wymagane przez użytkownika.

### Estimate po decyzji

| Architektura | Estimate | Status |
|--------------|----------|--------|
| 1:1+context (PO) | 17-21h | **WYBRANA** |
| Pełne 1:N (Tech Lead) | 22-26h | ODRZUCONE |

### Zaktualizowany plan implementacji (po spike, jeśli pozytywny)

1. **DB:** Tabela `fakturownia_product_mapping` (1:1, UNIQUE na `fakturownia_product_id`)
2. **Backend:**
   - `GET /fakturownia/invoices?oid=` — read-only fetch faktur
   - `GET /contracts/{id}/articles` — list artykułów z tej umowy (do filtrowania dropdownu)
   - `POST /fakturownia/mapping` — zapisanie mappingu 1:1
3. **Frontend:**
   - Panel rozliczenia: guzik "Pokaż faktury z FA" → lista pozycji read-only z FA
   - Sekcja "Pozycje niezmapowane" → combobox z artykułami z tej umowy (context-aware filtering)
   - Mapping zapisywany do DB (globalnie 1:1)