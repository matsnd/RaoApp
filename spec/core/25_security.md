# 25 — Security — Single Source of Truth Bezpieczeństwa

> **Owner:** Security Auditor | **Last verified:** 2026-05-17  
> **Read this if:** Wszyscy agenci — security jest inwariantem

## 1. Threat model

- **Zasoby chronione:** NIP/REGON/adresy kontrahentów, ceny umów, hasła handlowców
- **Aktorzy:** handlowiec (RBAC user), kierownik (admin), zewnętrzny atakujący (VPN/intranet)
- **Wektory:** brute-force loginu, IDOR na /contracts/{id}, XSS w PDF, leak przez export

### IDOR — `/reports/contract/{id}` (RAO-SEC-001, fixed 2026-07-01)

**Problem:** Endpoint `POST /reports/contract/{contract_id}` wymagał autentykacji ale nie sprawdzał ownership — każdy zalogowany user mógł wygenerować PDF (z danymi kontaktowymi klienta) dla cudzej umowy.

**Fix:** `backend/reports/router.py` — `_check_contract_access()`:
- Admin: pełny dostęp (role == "admin")
- Non-admin: tylko umowy z własnego branch (`contract.branch_id == user.branch_id`)
- Umowy bez branch (NULL) = legacy, dostępne dla wszystkich zalogowanych
- Fetch contract BEFORE PDF generation (early 404/403)

**Status:** done (2026-07-01) — commit w historii git
- **Out-of-scope:** ataki na MariaDB hosta, fizyczny dostęp do serwera

## 2. AuthN (Authentication)

- **JWT HS256**, access TTL=60min (RAO-SEC-004: fixed from 480min to 60min, commit c572e6c)
- **JWT_SECRET:** ≥32B z os.urandom (RAO_SECRET_KEY z .env, validator odrzuca pusty/"change-me")
- **Hasła:** bcrypt, min length 8 (RAO-SEC-006: podniesiono z 6 do 8, commit c572e6c). TODO: min 12 + blacklist top-10k
- **Rate-limit:** /auth/login 5/min/IP (wyłączony w dev mode)
- **Change-password:** wymaga aktualnego hasła. TODO: jti blacklist dla session invalidation (RAO-SEC-005 pending)
- **Security headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy (RAO-SEC-007: commit c572e6c). HSTS + CSP tylko w production.
- **CORS:** ograniczony do konkretnych metod i nagłówków (RAO-SEC-008: commit c572e6c, był "*")

## 3. AuthZ (RBAC matrix)

| Zasób | user | admin |
|---|---|---|
| GET /contracts/{id} | own branch only (RAO-P0-049) | all |
| POST /contracts | yes (own branch) | yes (any branch) |
| GET /settlements/contract/{id} | own branch only (RAO-SEC-001) | all |
| POST/PUT/DELETE /settlements | own branch only (RAO-SEC-001) | all |
| GET /contractors/{id} | yes (shared entity) | all |
| POST/PUT/DELETE /contractors | NO (admin only, RAO-SEC-002) | yes |
| GET /articles/{id} | own branch or NULL (RAO-SEC-003) | all |
| PUT/DELETE /articles/{id} | own branch only (RAO-SEC-003) | all |
| GET /reports/summary/* | NO (admin only, RAO-SEC-009) | yes |
| GET /archive/contracts/{id} | own branch only (RAO-SEC-010) | all |
| DELETE /users/{id} | no | yes |
| GET /audit_log | no | yes |
| POST /settings/company | no | yes |

## 4. Walidacja inputu (Pydantic v2)

- Każdy endpoint: schema z Field(min_length, max_length, pattern)
- NIP: checksum validator
- File upload: MIME whitelist (image/png,jpeg), max 5MB, hash filename, no SVG

## 5. Output sanitization

- PDF (WeasyPrint+Jinja2): autoescape=True, brak `|safe` na user-input
- Frontend: ZAKAZ `v-html` na user-input (egzekwowane w lint)
- Logi: redact `password`, `token`, `Authorization`

## 6. Sekrety

- Tylko w `.env` (nigdy w spec/!) — w spec używaj `<<PLACEHOLDER>>`
- Rotacja: JWT_SECRET 90d, DB_PASSWORD 180d, GUS_KEY 365d
- Manager: .env + chmod 600 (docelowo Vault/SOPS)

## 7. Headers HTTP (FastAPI middleware) — RAO-SEC-007/008 (commit c572e6c)

- CORS: allow_origins z .env, credentials=True, methods=[GET,POST,PUT,PATCH,DELETE,OPTIONS], headers=[Authorization,Content-Type,Accept], expose=[Content-Disposition]
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Strict-Transport-Security: max-age=31536000; includeSubDomains (prod only)
- Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' (prod only)

## 8. Audit log

- Append-only (brak UPDATE/DELETE z aplikacji)
- Co loguje: login/logout, create/update/delete contracts/contractors/users, export PDF/Excel
- Retencja: 24 miesiące
- Czytelny tylko dla admin (RBAC)

## 9. RODO

- Dane osobowe: tabela `contractors` (NIP, adres, telefon, email, kontakty)
- Prawo do bycia zapomnianym: soft-delete + anonimizacja po 30d
- Eksport `24_EXPORT_UJEDNOLICENIE`: ZIP z hasłem AES-256, hasło osobnym kanałem, log w audit_log
- Dev/staging: `anonymize_db.py` przed kopią produkcyjnej bazy

## 10. Migracje danych (security view)

- **ZAKAZ:** kopiowanie plaintext haseł do nowej bazy
- **WYMAGANE:** stare hasła → force_password_reset=1
- Dump produkcyjny: szyfrowane GPG, retencja 30d, log dostępu

## 11. Vulnerability management

- `pip-audit` + `npm audit` w CI (fail build dla high/critical)
- SBOM generated co release
- Dependency update: kwartalnie + patch ASAP dla CVE >7.0

## 12. Incident response

- Detection: alert na 100+ 401/min, 50+ 403/min
- Containment: `revoke_all_tokens.py` (zmienia JWT_SECRET)
- Notification: PUODO w 72h jeśli wyciek PII