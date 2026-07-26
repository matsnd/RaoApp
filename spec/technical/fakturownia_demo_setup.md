# Fakturownia Configuration — Demo Setup (matsnd.fakturownia.pl)

> Dokumentacja konfiguracji konta Fakturownia dla środowiska demo RAO.
> Konto: matsnd.fakturownia.pl | Email: mateusz.wiatrak@gmail.com

## 1. Konto i token API

- **Domain:** `matsnd` (subdomena Fakturownia)
- **API token:** `sejjNboMz7zZ3fFLxtoW` (z env `FA_TOKEN`)
- **Base URL:** `https://matsnd.fakturownia.pl`
- **API base:** `https://matsnd.fakturownia.pl/{resource}.json?api_token={token}`

## 2. Dział firmy (Seller/Department)

Utworzony dział główny w FA (`/departments`):

| Pole | Wartość |
|------|---------|
| Nazwa | RAO Sp. z o.o. |
| Skrót | RAO |
| NIP | 1234563218 |
| Adres | ul. Przykładowa 1, 00-001 Warszawa |
| Telefon | +48 500 123 456 |
| Email | biuro@rao.pl |
| WWW | www.rao.pl |
| Osoba | Mateusz Wiatrak |
| Kraj | PL |
| Domyślne VAT | 23% |

## 3. Produkty (11 szt.)

### Maszyny (5)

| Kod | Nazwa FA | Cena netto | PKWiU | GTU | FA ID |
|-----|----------|-----------|-------|-----|-------|
| KOP001 | Koparka CAT 320 | 800 zł | 77.32.19.0 | GTU_12 | 8845156432567 |
| LAD001 | Ładowarka JCB 3CX | 650 zł | 77.32.19.0 | GTU_12 | 8845156436442 |
| POD001 | Podnośnik Haulotte 18m | 450 zł | 77.32.19.0 | GTU_12 | 8845156436443 |
| SPY001 | Spychar Wirtgen | 1200 zł | 77.32.19.0 | GTU_12 | 8845156436444 |
| ZAG001 | Zagęszczarka Wacker Neuson | 150 zł | 77.32.19.0 | GTU_12 | 8845156436446 |

### Usługi dodatkowe (6)

| Kod | Nazwa FA | Cena netto | PKWiU | GTU | FA ID |
|-----|----------|-----------|-------|-----|-------|
| TRA001 | Transport | 400 zł | 77.32.19.0 | GTU_12 | 8845156432587 |
| CZY001 | Czyszczenie drobne | 150 zł | 77.32.19.0 | GTU_12 | 8845156432589 |
| CZY002 | Czyszczenie trudne | 400 zł | 77.32.19.0 | GTU_12 | 8845156436448 |
| TAN001 | Tankowanie | 200 zł | 77.32.19.0 | GTU_12 | 8845156432620 |
| PZT001 | Przestój | 200 zł | 77.32.19.0 | GTU_12 | 8845156436449 |
| SER001 | Serwis | 280 zł | 77.32.19.0 | GTU_12 | 8845156436450 |

### Konfiguracja produktów

- **Tax rate:** 23% (wszystkie)
- **GTU code:** `GTU_12` (array: `["GTU_12"]` — FA API wymaga array, nie string)
- **PKWiU:** `77.32.19.0` (pole `additional_info`)
- **price_gross:** musi być ustawione alongside `price_net` aby wymusić aktualizację ceny

## 4. Klienci (8 firm demo)

| Nazwa | NIP | Miasto | FA ID |
|-------|-----|--------|-------|
| Bud-Plus Sp. z o.o. | 7010001234 | Warszawa | 260564893 |
| Invest S.A. | 5260005678 | Kraków | 260564910 |
| Terra-Masz Budownictwo | 7790009012 | Poznań | 260564912 |
| Wod-Bud Sp. z o.o. | 9510003456 | Wrocław | 260564913 |
| Fundament Sp. z o.o. | 1460007890 | Łódź | 260564914 |
| Trakcja-Polska S.A. | 6790002345 | Gdynia | 260564915 |
| Eko-Bud Nowoczesne Budownictwo | 2580006789 | Katowice | 260564917 |
| Miejskie Inwestycje Sp. z o.o. | 8350001230 | Bydgoszcz | 260564918 |

### Ważne: `tax_no_kind: "other"`

Wszyscy klienci demo mają ustawione `tax_no_kind: "other"` (Nr. id. podatkowej) zamiast domyślnego `""` (NIP). Powód: demo NIP-y nie są w rejestrze GUS i FA odrzuca faktury z błędem "błędny nr NIP nabywcy". Ustawienie `tax_no_kind: "other"` wyłącza walidację NIP.

## 5. Faktury (12 szt.)

Utworzone faktury dla rozliczonych umów z `source=fakturownia`:

| Umowa | Kontrahent | Faktura FA | FA ID |
|-------|-----------|-----------|-------|
| U012/2026 | Wod-Bud | 1/02/2026 | 526200225 |
| S002/2026 | Invest | 1/06/2026 | 526200497 |
| U003/2026 | Terra-Masz | 2/06/2026 | 526200501 |
| U006/2026 | Trakcja | 1/05/2026 | 526200503 |
| S007/2026 | Eko-Bud | 1/04/2026 | 526200507 |
| S008/2026 | Miejskie | 2/04/2026 | 526200509 |
| S011/2026 | Terra-Masz | 2/02/2026 | 526200511 |
| S013/2026 | Fundament | 1/01/2026 | 526200514 |
| S016/2026 | Miejskie | 1/12/2025 | 526200516 |
| S017/2026 | Bud-Plus | 1/11/2025 | 526200521 |
| U018/2026 | Invest | 2/11/2025 | 526200523 |
| U021/2026 | Fundament | 1/09/2025 | 526200525 |

Każda faktura ma:
- `description`: "Rozliczenie umowy {OID}" (OID = numer umowy RAO)
- Pozycje z `product_id` mapowanym do FA product
- `issue_date` = `date_to` umowy
- `buyer_tax_no_kind: "other"` (omija walidację NIP)

## 6. Mapowanie RAO ↔ FA

### Article.fakturownia_product_id

Każdy artykuł RAO (maszyna/usługa) ma pole `fakturownia_product_id` powiązane z produktem FA:

| RAO Article | FA Product ID |
|-------------|---------------|
| Koparka gąsienicowa JCB 8035 | 8845156432567 |
| Ładowarka teleskopowa Manuscop 6.36 | 8845156436442 |
| Podnośnik koszowy Haulotte HA16PX | 8845156436443 |
| Spychar Wirtgen W100CFi | 8845156436444 |
| Zagęszczarka Ammann APF 15/50 | 8845156436446 |
| Transport maszyny | 8845156432587 |
| Czyszczenie maszyny — drobne | 8845156432589 |
| Czyszczenie maszyny — trudne | 8845156436448 |
| Tankowanie paliwa | 8845156432620 |
| Przestój maszyny | 8845156436449 |
| Serwis maszyny | 8845156436450 |

### Contract OID = numer umowy

OID umowy w RAO odpowiada numerowi umowy (np. `S001/2026`). W FA fakturach OID jest zapisany w polu `description` jako "Rozliczenie umowy {OID}".

## 7. Skrypty seedujące

### `scripts/seed_demo_data.py`
- Idempotentny skrypt seedujący dane demo w RAO DB
- Tworzy: kategorie, artykuły, kontrahentów, handlowców, oddziały, rate types, umowy, pozycje, warunki, usługi dodatkowe, rozliczenia
- Użycie: `python scripts/seed_demo_data.py`

### `scripts/seed_fa_invoices.py`
- Idempotentny skrypt wystawiający faktury w FA dla rozliczonych umów
- Sprawdza czy faktura już istnieje po OID (numer umowy w description)
- Aktualizuje `contract_settlements.fakturownia_invoice_id`
- Użycie: `python scripts/seed_fa_invoices.py`

## 8. API quirks (odkryte podczas konfiguracji)

1. **`gtu_codes` (array) nie `gtu_code` (string)** — FA API dla produktów wymaga array `["GTU_12"]`
2. **`price_gross` required for price update** — sama `price_net` nie aktualizuje ceny
3. **`tax_no` nie `nip`** — FA API dla klientów używa `tax_no`, nie `nip`
4. **`tax_no_kind: "other"`** — wyłącza walidację NIP dla demo klientów
5. **`buyer_tax_no_kind: "other"` w invoice** — nadpisuje ustawienia klienta przy tworzeniu faktury
6. **Cookie banner `#cmpwrapper`** — intercepts clicks w UI, trzeba usunąć przez JS przed klikaniem
