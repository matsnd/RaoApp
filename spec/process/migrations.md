# Migrations — Polityka Deterministyczna

> **Owner:** DB Architect + Tech Lead  
> **Last updated:** 2026-07-05  
> **Read this if:** Dotykasz schematu bazy danych lub migracji danych

---

## 🎯 Cel

RAO wymaga **deterministycznych migracji** — każda migracja musi być:
1. **Idempotentna** — można uruchomić N razy bez błędów
2. **Re-runnable** — drugie uruchomienie nie duplikuje danych
3. **Weryfikowalna** — ma jasne kryteria sukcesu
4. **Bezpieczna** — brak sekretów w spec, brak plaintext haseł

To jest krytyczne ponieważ:
- Baza będzie migrowana wielokrotnie (dev → staging → production)
- Każdy nowy agent musi móc postawić system od zera
- Błędy w migracji = data loss lub corruption

---

## 📋 Rodzaje migracji

### A. Migracje schema (deterministyczne)
**Lokalizacja:** `backend/main.py` startup (event handler)

**Przykład:**
```python
@app.on_event("startup")
async def startup_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS "
            "delivery_address VARCHAR(255) NULL"
        ))
        # FK i indeksy też z IF NOT EXISTS (MariaDB 10.0.2+ dla FK, 10.0.9+ dla indeksów)
        await conn.execute(sa.text(
            "ALTER TABLE contracts ADD CONSTRAINT IF NOT EXISTS fk_contractor "
            "FOREIGN KEY (contractor_id) REFERENCES contractors(id)"
        ))
        await conn.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS idx_contracts_contractor ON contracts(contractor_id)"
        ))
```

**Zasady:**
- Zawsze `IF NOT EXISTS` lub `IF EXISTS` (dla FK i indeksów też!)
- Zawsze deterministyczne (brak warunków z runtime)
- Zawsze w `main.py` startup (nie w oddzielnych skryptach)
- **ZABRONIONE:** try/except z `pass` dla FK/indeksów (to ukrywa prawdziwe błędy)
- MariaDB wspiera IF NOT EXISTS dla FK od 10.0.2, dla indeksów od 10.0.9

### B. Migracje danych (legacy → rao_new)
**Lokalizacja:** `backend/migrate.py`

**Przykład:**
```python
async def migrate_contractors(old_conn, new_conn):
    old_data = await old_conn.execute("SELECT * FROM contractors")
    for row in old_data:
        contractor = Contractor(**transform(row))
        new_conn.add(contractor)
    await new_conn.commit()
```

**Zasady:**
- Zawsze idempotentne (drugi run = 0 zmian lub identyczne)
- Zawsze weryfikowalne (row counts, sample diff)
- Zawsze bezpieczne (brak plaintext haseł)

---

## 🔐 Security w migracjach

### Hasła
**ZABRONIONE:** Kopiowanie plaintext haseł do nowej bazy (nawet "tymczasowo")

**WYMAGANE:** 
```python
# ZAMIAST tego:
new_password = old_password  # plaintext w bazie!

# ZRÓB TO:
new_password = generate_random_temp_password()  # bcrypt
force_password_reset = True
send_reset_email(user.email, reset_token)
```

**Powód:** Każdy snapshot/dump bazy między migracją a rehashem = wszystkie hasła w plaintext.

### Sekrety w spec
**ZABRONIONE:** Hasła, API keys, secrets w plikach spec/

**WYMAGANE:**
```yaml
# ZAMIAST tego:
password: 'RaoPass2026!'  # sekret w spec!

# ZRÓB TO:
password: '<<DB_PASSWORD>>'  # placeholder
# W .env:
DB_PASSWORD=RaoPass2026!
```

**Powód:** Repo (nawet prywatne) → leak przez fork, AI training, copy-paste.

### Dane osobowe (PII)
**WYMAGANE:** Anonimizacja przed kopią produkcyjną do dev/staging

**Przykład:**
```python
# anonymize_db.py
for contractor in contractors:
    contractor.nip = generate_valid_nip_checksum()
    contractor.email = f"user{contractor.id}@example.invalid"
    contractor.phone = f"+48 500 000 000{contractor.id}"
```

---

## 🧪 Verification Gates (obowiązkowe)

Każde zadanie z `migration_impact: yes` musi zawierać sekcję:

```markdown
**Migration plan (RAO deterministic):**
1. `core/01_database.md` — finalny DDL (mirror, nie ALTER)
2. `backend/<feature>/models.py` — SQLAlchemy Column
3. `backend/main.py` startup — `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`
4. **Jeśli touch `migrate.py`:** zmodyfikuj parser legacy → nowe pole
5. **Verification gate (obowiązkowe):**
   - [ ] `DROP DATABASE rao_new && CREATE` → restart backend → schema OK
   - [ ] Re-run `python migrate.py` → idempotentne (drugi przebieg = 0 zmian)
   - [ ] Drugi restart backend bez błędu "Duplicate column"
   - [ ] Row count parity: stare vs nowe (lub udokumentowana różnica)
   - [ ] Sample diff: 10 losowych rekordów
```

---

## 📋 Testy migracji

### Schema migrations (test idempotentności)
**Plik:** `backend/tests/migration/test_schema_idempotent.py`

```python
@pytest.mark.asyncio
async def test_startup_migrations_idempotent():
    """ALTER ... IF NOT EXISTS musi być uruchamialny N razy."""
    from main import startup_migrations
    await startup_migrations()  # 1. raz
    await startup_migrations()  # 2. raz — NIE może rzucić "Duplicate column"
    await startup_migrations()  # 3. raz — gwarancja determinizmu

@pytest.mark.asyncio
async def test_schema_matches_spec_ddl():
    """SHOW CREATE TABLE ↔ spec/01_DATABASE_DDL.md — nie może być dryfu."""
    for table in EXPECTED_TABLES:
        actual = await conn.execute(f"SHOW CREATE TABLE {table}")
        expected = parse_ddl_from_spec("core/01_database.md", table)
        assert_columns_match(actual, expected)  # nazwa, typ, NULL, default
```

### Data migrations (test integrity)
**Plik:** `backend/tests/migration/test_data_migration.py`

```python
async def test_row_count_parity():
    """SELECT COUNT(*) z starej == NOWEj."""
    old_count = await old_conn.execute("SELECT COUNT(*) FROM contractors")
    new_count = await new_conn.execute("SELECT COUNT(*) FROM contractors")
    assert old_count == new_count  # lub udokumentowana różnica

async def test_structural_integrity():
    """Zero orphan FK, zero NULL w NOT NULL."""
    # Sprawdź czy wszystkie contractor_id w contracts istnieją w contractors
    orphans = await new_conn.execute("""
        SELECT COUNT(*) FROM contracts c 
        LEFT JOIN contractors co ON c.contractor_id = co.id 
        WHERE co.id IS NULL
    """)
    assert orphans.scalar() == 0

async def test_parsing_edge_cases():
    """Test edge cases w parserze OPLATY."""
    test_cases = [
        ("", None),                                    # empty
        ("   ", None),                                 # whitespace
        ("- : 100 zł", ...),                           # missing name
        ("- Transport: abc zł", ...),                  # invalid amount
    ]
    for input_str, expected in test_cases:
        result = parse_oplaty(input_str)
        assert result == expected
```

### From-scratch migration (nightly)
**Plik:** `scripts/test_migration_from_scratch.sh`

```bash
#!/bin/bash
# Test pełnego pipeline od zera
mariadb -e "DROP DATABASE rao_new; CREATE DATABASE rao_new CHARACTER SET utf8mb4 COLLATE utf8mb4_polish_ci;"
cd backend && uvicorn main:app --port 8001 &
sleep 5
python migrate.py
pytest tests/migration/ -v
# Cleanup
kill %1
```

---

## 🚨 Common Pitfalls

| Pitfall | Dlaczego boli | Jak unikać |
|---------|---------------|-------------|
| ALTER bez `IF NOT EXISTS` | Drugi start rzuci "Duplicate column" | Zawsze `IF NOT EXISTS` |
| FK/indeks bez `IF NOT EXISTS` | Drugi start rzuci "Duplicate key" | Zawsze `IF NOT EXISTS` (MariaDB 10.0.2+) |
| try/except z `pass` dla FK/indeksów | Ukrywa prawdziwe błędy, nie jest deterministyczne | Użyj `IF NOT EXISTS` zamiast try/except |
| Plaintext hasła w bazie | Snapshot = wszystkie hasła w plaintext | `force_password_reset=1` |
| Sekrety w spec | Repo leak | Używaj `<<PLACEHOLDER>>` |
| Brak verification gates | Migracja "udała się" ale jest broken | Zawsze dodaj gates |
| Brak testów idempotentności | Nie wiesz czy drugi run jest safe | Zawsze testuj double-restart |
| Brak rollback plan | Produkcja broken i nie można wrócić | Zawsze dump przed migracją |

---

## 🧹 Dead column/table cleanup

Czasem dochodzi do sytuacji, gdy pole/tabela przestaje być używane (martwe kolumny).  
Procedura w RAO jest taka sama jak dla każdej migracji forward-only — z jednym wyjątkiem:

1. **Zgoda użytkownika + backup** — `DROP COLUMN`/`DROP TABLE` to destrukcyjne operacje.
2. **Dodaj `IF EXISTS` i try/except** — MariaDB <10.6 nie wspiera `DROP COLUMN IF EXISTS`;
   dla `DROP TABLE IF EXISTS` jest ono bezpieczne, ale try/except chroni przed innymi błędami.
   ```python
   try:
       await conn.execute(sa.text("ALTER TABLE t DROP COLUMN IF EXISTS x"))
   except Exception:
       pass
   ```
3. **NIE usuwaj archive_** — tabele archiwalne (`archive_*`) zostaw w spokoju.
4. **Usuń martwe kolumny z modelu SQLAlchemy** — inaczej `Base.metadata.create_all` przywróci
   je na nowej bazie i `DROP` w `main.py` zrobi niepotrzebną pracę.
5. **Uaktualnij `spec/core/01_database.md`** — finalny DDL nie może zawierać martwych kolumn/tabel.

Przykład (RAO Phase 1, 2026-07-05):
- `service_fee_templates.default_price`
- `service_fee_template_items` (tabela)
- `contract_positions.costs`
- `position_conditions.rate_type_id`, `position_conditions.description`
- `contract_service_fees.article_id`, `contract_service_fees.default_price`
- `contracts.total_value`, `contracts.is_legacy` (wycofane wcześniej, usunięte z DDL)

## 📝 Rollback Policy

RAO ma **forward-only migrations** — to znaczy że KAŻDA destrukcyjna migracja wymaga:

1. **Dump przed migracją**
   ```bash
   mysqldump rao_new | gpg --encrypt -r ops@firma.pl > backups/$(date +%Y-%m-%d)_pre-migration.sql.gpg
   ```

2. **Approval użytkownika** — w specyfikacji zadania

3. **Wpis w `core/25_security.md`** — sekcja "Destructive migrations log"

4. **Rollback plan** — opisany w zadaniu backlogu

**Przykład destrukcyjnej migracji:**
- DROP COLUMN (tracisz dane)
- MODIFY COLUMN z konwersją typu (może stracić dane)

---

## ✅ Checklist przed commitem migracji

- [ ] Schema migration: `IF NOT EXISTS` / `IF EXISTS` (dla FK i indeksów też!)
- [ ] Data migration: idempotentna (drugi run = 0 zmian)
- [ ] Brak sekretów w kodzie/spec
- [ ] Hasła: `force_password_reset=1` zamiast plaintext
- [ ] Verification gates dodane do zadania backlogu
- [ ] Testy napisane (schema_idempotent, data_integrity)
- [ ] `core/01_database.md` zaktualizowany (mirror finalnego stanu)
- [ ] Rollback plan zdefiniowany (jeśli destrukcyjne)

---

## 📞 Gdzie szukać pomocy

- **Polityka migracji:** ten plik
- **Aktualny DDL:** `core/01_database.md`
- **Security:** `core/25_security.md` (sekcja 10)
- **Testy:** `process/testing.md` (sekcja 6.4)
- **Backlog:** `backlog/BACKLOG.md` (zadania z `migration_impact: yes`)