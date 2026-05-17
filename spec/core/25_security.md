# 25 — Security — Single Source of Truth Bezpieczeństwa

> **Owner:** Security Auditor | **Last verified:** 2026-05-17  
> **Read this if:** Wszyscy agenci — security jest inwariantem

## 1. Threat model

- **Zasoby chronione:** NIP/REGON/adresy kontrahentów, ceny umów, hasła handlowców
- **Aktorzy:** handlowiec (RBAC user), kierownik (admin), zewnętrzny atakujący (VPN/intranet)
- **Wektory:** brute-force loginu, IDOR na /contracts/{id}, XSS w PDF, leak przez export
- **Out-of-scope:** ataki na MariaDB hosta, fizyczny dostęp do serwera

## 2. AuthN (Authentication)

- **JWT HS256**, access TTL=60min, refresh TTL=7d, refresh w httpOnly cookie SameSite=Lax
- **JWT_SECRET:** ≥32B z os.urandom, rotacja co 90d, stary klucz akceptowany 24h (grace)
- **Hasła:** bcrypt cost=12, min length 12, blacklist top-10k haseł
- **Rate-limit:** /auth/login 5/min/IP + 10/h/login, lockout 15min po 10 fail
- **Change-password:** invalidates all sessions (jti blacklist)

## 3. AuthZ (RBAC matrix)

| Zasób | user | admin |
|---|---|---|
| GET /contracts/{id} | own only | all |
| POST /contracts | yes | yes |
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

## 7. Headers HTTP (FastAPI middleware)

- CORS: allow_origins=[FRONTEND_URL], credentials=True
- CSP: default-src 'self'; img-src 'self' data:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000 (prod HTTPS only)

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