# Seed demo scenariusza unmapped FA settlements (opcja E)

> **Faza 2d** — demo scenariusz "opcja E": umowa z usługami 1+2, faktura FA z usługą 2 (zmapowaną) + artykułem 4 (niezmapowanym w RAO). Po "Pobierz z FA" analytics pokazuje pełną kwotę faktury.

## Kontekst biznesowy

Wymaganie użytkownika: jeśli w danej umowie są zmapowane na artykuły inne usługi/artykuły niż były w umowie domyślnie (warunki rozliczenia, usługi dodatkowe), to weź je pod uwagę do analytics.

**Przykład:** umowa ma usługę 1 i 2, a z Fakturowni wraca usługa 2 + artykuł 4 (niezmapowany) → oba mają się pojawić w rozliczeniach i być brane pod te artykuły do wyciągania statystyk przychodów i wartości.

## Scenariusz demo

### Umowa (RAO)
- **Numer:** `S099/2026` (stała `DEMO_UNMAPPED_CONTRACT_NUMBER` w `seed_demo_data.py`)
- **Typ:** `U` (usługowa — usługa z operatorem)
- **Stan:** zakończona (date_to < today), NIEROZLICZONA (`fa_pending=True`)
- **Pozycje:** 1 maszyna (Koparka JCB 8035 — zmapowana w RAO)
- **Usługi dodatkowe (2):**
  - `Transport` → article_id = "Transport maszyny" (`fakturownia_product_id = 8845156432587`)
  - `Usługa tankowania` → article_id = "Tankowanie paliwa" (`fakturownia_product_id = 8845156432620`)
- **OID:** numer umowy (`S099/2026`) — `fetch_invoices_for_contract` używa `contract.oid or contract.number`

### Faktura FA (Fakturownia)
Wystawiana przez `seed_fa_invoices.py` z 3 pozycjami:
1. **Transport** (product_id zmapowany w RAO = `8845156432587`) — 350 zł brutto → mapped settlement
2. **Tankowanie** (product_id zmapowany w RAO = `8845156432620`) — 200 zł brutto → mapped settlement
3. **Praca operatora** (product_id NIEzmapowany w RAO) — 800 zł brutto → unmapped settlement (`source='fa_unmapped'`)

### Po "Pobierz z FA"
- 3 settlements: 2 mapped (Transport + Tankowanie) + 1 unmapped (Praca operatora)
- Analytics (`compute_position_revenues`): **1350 zł** (350 + 200 + 800)
- Frontend: badge "⚠ Niezmapowane" w ContractFormView dla pozycji 3

## Implementacja

### `spec/technical/scripts/seed_demo_data.py`
- Pula E: `_build_demo_unmapped_contract()` — tworzy umowę `S099/2026` typu 'U' z 2 usługami zmapowanymi (Transport + Tankowanie), `fa_pending=True` (bez settlements w RAO).
- Stała `DEMO_UNMAPPED_CONTRACT_NUMBER = "S099/2026"`.

### `spec/technical/scripts/seed_fa_invoices.py`
- `ensure_unmapped_fa_product(client, db)` — zwraca ID produktu "Praca operatora" w FA, NIEzmapowanego w RAO:
  1. Jeśli `FA_UNMAPPED_PRODUCT_ID` w env → użyj go (po weryfikacji że nie jest w `articles.fakturownia_product_id`).
  2. W przeciwnym razie szukaj w FA po nazwie (`GET /products.json?name=Praca operatora`).
  3. Jeśli nie znaleziono → utwórz nowy produkt w FA (`POST /products.json`).
- `_is_demo_unmapped_contract()` — wykrywa umowę `S099/2026`.
- `_append_demo_unmapped_position()` — dodaje 3. pozycję do faktury demo.
- `create_fa_invoice(..., db=None)` — dla umowy demo wywołuje `_append_demo_unmapped_position`.

## Procedura pełnego seeda (wymaga tokenu FA)

### Wymagania
- `.env` z `FAKTUROWNIA_API_TOKEN` (lub `FA_TOKEN`)
- MariaDB `rao_new` dostępna
- Backend NIE musi działać (skrypty łączą się bezpośrednio z DB)

### Kroki

```bash
# 1. Seed umów demo (tworzy umowę S099/2026 z 2 usługami zmapowanymi)
cd backend
python seed_demo_data.py

# 2. Wystaw faktury w FA (tworzy fakturę z 3 pozycjami dla S099/2026)
python seed_fa_invoices.py
# Oczekiwany output:
#   [S099/2026] Bud-Plus Sp. z o.o. — FA-pending
#     [unmapped] Używam FA_UNMAPPED_PRODUCT_ID z env: <id>  (lub "Tworzę nowy produkt...")
#     [unmapped] Dodano pozycję 'Praca operatora' (FA product_id=<id>, ~800 zł brutto)
#     OK: Faktura <numer> (ID=<id>) dla S099/2026 — 3 pozycji

# 3. Zaloguj się do RAO (admin/admin123)
# 4. Znajdź umowę S099/2026 (lista umów / wyszukiwarka)
# 5. Kliknij "Pobierz z Fakturowni"
# 6. Sprawdź: 3 settlements (2 mapped + 1 unmapped z badge "⚠ Niezmapowane")
# 7. Sprawdź analytics: period_revenue zawiera 1350 zł (350+200+800)
```

### Konfiguracja opcjonalna (env)

| Zmienna | Domyślna | Opis |
|---------|----------|------|
| `FA_UNMAPPED_PRODUCT_ID` | (brak) | ID produktu "Praca operatora" w FA — NIE może być w `articles.fakturownia_product_id` w RAO. Jeśli brak → skrypt szuka/tworzy produkt. |
| `FA_UNMAPPED_PRODUCT_NAME` | `Praca operatora` | Nazwa produktu w FA (do szukania/tworzenia). |
| `FA_UNMAPPED_PRODUCT_PRICE_NET` | `650.41` | Cena netto (800 zł brutto / 1.23). |

## Dry run (bez tokenu FA)

Pełny seed wymaga tokenu FA. Logika `ensure_unmapped_fa_product` jest pokryta testami unit (`test_settlements_unmapped.py` — 29 testów PASS) na poziomie source inspection + mock DB. Backend `init-from-fakturownia` (router) jest testowany source-inspection + mock.

Aby zweryfikować bez FA:
```bash
cd backend
python -m pytest tests/unit/test_settlements_unmapped.py -x --tb=short
# 29 passed
```

## Uwagi

- Umowa `S099/2026` jest idempotentna (re-run `seed_demo_data.py` nie duplikuje — sprawdza po numerze).
- Faktura FA jest idempotentna (re-run `seed_fa_invoices.py` sprawdza OID — `check_invoice_exists_by_oid`).
- Produkt "Praca operatora" w FA jest tworzony raz (kolejne runy znajdują go po nazwie).
- Pozycja 3 MUSI mieć `product_id` w FA (inaczej `line.fakturownia_product_id` = None → guard `pid is not None and pid != 0` odrzuca unmapped settlement).
