# RAO — Bugfix Log

> **Data:** 2026-07-11
> **Źródła:** Phase 0 analiza (Security Auditor, Tech Lead, QA Engineer)
> **Status:** W trakcie

---

## CRITICAL — IDOR (Insecure Direct Object Reference)

### RAO-SEC-001: IDOR w settlements/router.py — FIXED ✅

**Severity:** CRITICAL
**Plik:** `backend/settlements/router.py`
**Opis:** Wszystkie endpointy `/settlements/*` z `{contract_id}` lub `{settlement_id}` w ścieżce nie miały ownership check. Każdy zalogowany user (nawet z innej filii) mógł czytać, modyfikować i usuwać rozliczenia dowolnej umowy.

**Fix:** Dodano `_verify_settlement_access()` helper, który:
1. Pobiera settlement → pobiera `contract_id` → wywołuje `contract_service.verify_contract_access()`
2. Dla endpointów z `contract_id` w ścieżce — bezpośrednio wywołuje `verify_contract_access()`
3. Dla operacji mutacji (PUT/DELETE/init) — `allow_mutation=True` (sprawdza też `is_settled` lock)

**Endpointy naprawione:**
- `GET /settlements/contract/{contract_id}` — verify_contract_access
- `GET /settlements/{settlement_id}` — _verify_settlement_access
- `POST /settlements` — verify_contract_access (jeśli data.contract_id)
- `PUT /settlements/{settlement_id}` — _verify_settlement_access (allow_mutation=True)
- `POST /settlements/contract/{contract_id}/init` — verify_contract_access (allow_mutation=True)
- `POST /settlements/contract/{contract_id}/init-from-fakturownia` — verify_contract_access (allow_mutation=True)
- `DELETE /settlements/{settlement_id}` — _verify_settlement_access (allow_mutation=True)
- `DELETE /settlements/contract/{contract_id}/all` — verify_contract_access (allow_mutation=True)

**Weryfikacja:**
- Admin (branch 1): `GET /settlements/contract/1` → 200 ✅
- User (branch 2): `GET /settlements/contract/1` → 404 ✅ (nie ujawnia istnienia)
- Smoke E2E: 11/11 passed ✅

---

### RAO-SEC-002: IDOR w contractors/router.py — FIXED ✅

**Severity:** CRITICAL
**Plik:** `backend/contractors/router.py`
**Opis:** Endpointy PUT/DELETE/POST dla kontrahentów nie miały ownership check. PII (NIP, adres, telefon, email) dostępne dla każdego zalogowanego, a modyfikacja/usuwanie bez gate.

**Fix:** Kontrahenci nie mają `branch_id` (są encjami współdzielonymi — jeden kontrahent może mieć umowy w wielu filiacjach). Dlatego:
- **Read** (GET): dostępne dla wszystkich zalogowanych (jak obecnie)
- **Write** (POST/PUT/DELETE): wymagają roli `admin` (`_require_admin()` helper)
- **Adresy** (POST/PUT/DELETE): również wymagają `admin`

**Endpointy naprawione:**
- `POST /contractors` — _require_admin
- `PUT /contractors/{contractor_id}` — _require_admin
- `DELETE /contractors/{contractor_id}` — _require_admin
- `POST /contractors/{contractor_id}/addresses` — _require_admin
- `PUT /contractors/{contractor_id}/addresses/{address_id}` — _require_admin
- `DELETE /contractors/{contractor_id}/addresses/{address_id}` — _require_admin

**Weryfikacja:**
- User (non-admin): `POST /contractors` → 403 ✅
- Admin: `POST /contractors` → 201 ✅
- User (non-admin): `GET /contractors/1` → 200 ✅ (read allowed)

---

### RAO-SEC-003: IDOR w articles/router.py — FIXED ✅

**Severity:** HIGH
**Plik:** `backend/articles/router.py`
**Opis:** Endpointy GET/PUT/DELETE/duplicate dla artykułów nie miały ownership check. Każdy user mógł modyfikować/usuwać dowolną maszynę.

**Fix:** Artykuły mają `branch_id`. Dodano `_verify_article_access()` helper:
- **admin**: pełny dostęp
- **user/viewer**: tylko własny branch (branch_id match) lub NULL branch (legacy)
- **viewer**: read-only (allow_mutation=False → 403)
- Nie ujawnia istnienia cudzego zasobu (404 zamiast 403 dla cross-branch)

**Endpointy naprawione:**
- `GET /articles/{article_id}` — _verify_article_access
- `POST /articles` — viewer → 403
- `PUT /articles/{article_id}` — _verify_article_access (allow_mutation=True)
- `DELETE /articles/{article_id}` — _verify_article_access (allow_mutation=True)
- `POST /articles/{article_id}/duplicate` — _verify_article_access (allow_mutation=True)

**Weryfikacja:**
- User (branch 2): `GET /articles/1` (branch_id=NULL) → 200 ✅ (legacy, visible to all)
- Admin: `PUT /articles/1` → 200 ✅
- Smoke E2E: 11/11 passed ✅

---

## Pending fixes (z Phase 0 — do implementacji)

| # | ID | Severity | Opis | Status |
|---|----|----------|------|--------|
| 4 | RAO-SEC-004 | HIGH | JWT TTL 480min vs spec 60min | PENDING |
| 5 | RAO-SEC-005 | HIGH | Brak session invalidation po change-password | PENDING |
| 6 | RAO-SEC-006 | HIGH | Password min 6 vs spec 12 | PENDING |
| 7 | RAO-SEC-007 | HIGH | Brak security headers (CSP, HSTS, X-Frame) | PENDING |
| 8 | RAO-SEC-008 | MEDIUM | CORS zbyt permisywny | PENDING |
| 9 | RAO-SEC-009 | MEDIUM | Brak branch filter w summary PDF reports | PENDING |
| 10 | RAO-SEC-010 | MEDIUM | Brak branch check w archive | PENDING |
| 11 | RAO-SEC-011 | HIGH | DB password w spec/process/migrations.md | PENDING |
| 12 | RAO-TECH-001 | LOW | Martwy store feeTemplates | PENDING |
| 13 | RAO-TECH-002 | LOW | Martwe kolumny Company | PENDING |
| 14 | RAO-TECH-003 | LOW | Zakładka folder vs pdf-folders | PENDING |
| 15 | RAO-TECH-004 | LOW | STALE spec RAO-P1-023 | PENDING |
| 16 | RAO-TECH-005 | LOW | STALE ASCII layout SettingsView | PENDING |
| 17 | RAO-TECH-006 | LOW | spec/core/15_build_progress.md STALE | PENDING |
| 18 | RAO-QA-002 | MEDIUM | POST contracts bez date_from → 500 | PENDING |
| 19 | RAO-QA-003 | MEDIUM | PDF nieistniejący contract_id → 500 | PENDING |
| 20 | RAO-QA-004 | MEDIUM | PDF nieistniejący contractor_id → 500 | PENDING |
