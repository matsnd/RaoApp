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
**RAO-P2-012:** ODŁOŻONE po refinement  
**Data refinement:** 2026-05-18  
**Decyzja:** PO rekomenduje po P0/P1, Security podnia impact na HIGH  
**Następny krok:** Zakończyć wszystkie P1, potem ponownie rozważyć RAO-P2-012