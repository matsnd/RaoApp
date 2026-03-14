---
description: Self-review workflow z automatycznymi commitami
---

# Self-Review Agent Workflow

> **KONTEKST:** Agent pracuje sam nad zadaniem, ale symuluje proces code review z wieloma commitami.
> Po każdym logicalznym kroku zmienia "kontekst developera" i robi self-review.

## Zasady ogólne

1. **Małe, atomowe commity** — każdy commit = jedna logicalzna zmiana
2. **Kontekst developera** — przed każdym commitem zmień "osobę" która commituje:
   - `dev-backend` — praca nad backendem
   - `dev-frontend` — praca nad frontendem  
   - `dev-db` — praca nad bazą danych
   - `dev-infra` — praca nad infrastrukturą
   - `dev-review` — faza review
3. **Self-review przed commitem** — przeanalizuj zmiany, oceń jakość, napraw jeśli trzeba
4. **Dobre commit messages** — konwencja Conventional Commits

## Format commit messages

```
<typ>(<zakres>): <opis>

[opcjonalnie: szczegóły]

Co zostało zrobione:
- <lista zmian>

Dlaczego: <uzasadnienie biznesowe/techniczne>
```

Typy: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`, `perf`, `ci`

## Workflow krok po kroku

### KROK 1: Rozpocznij zadanie

```
1. Przeczytaj specyfikację zadania
2. Podziel na logicalzne podzadania (max 10-20 linii kodu każde)
3. Wykonaj pierwszy podzadanie
4. ZMIEŃ KONTEKST NA: dev-backend (lub inny właściwy)
```

### KROK 2: Self-review zmian

```
1. git diff --staged
2. Przeanalizuj:
   - Czy kod jest zgodny ze specyfikacją?
   - Czy nazwy zmiennych są sensowne?
   - Czy są komentarze gdzie potrzeba?
   - Czy testy przechodzą?
   - Czy nie ma console.log / debug?
   - Czy formatowanie jest spójne?
3. Jeśli NIE OK → napraw → wróć do 2
4. Jeśli OK → przejdź dalej
```

### KROK 3: Commit z review

```
1. git add <pliki>
2. git commit -m "feat(backend): implementuj model Uzytkownik

- dodano model SQLAlchemy z polami zgodnymi z DDL
- dodano walidacje Pydantic
- dodano indeks na kolumnie login

Dlaczego: potrzebne do systemu logowania"
3. ZMIEŃ KONTEKST NA: następny developer
```

### KROK 4: Powtórz dla każdego podzadania

```
DLA każdego podzadania:
  1. Wykonaj zmianę
  2. Self-review (KROK 2)
  3. Commit (KROK 3)
  4. Zmień kontekst
```

### KROK 5: Finalne review

```
1. git log --oneline -10
2. Sprawdź czy commity są logicalznie spójne
3. Jeśli trzeba: squash lub rebase
4. git push origin <branch>
```

## Przykład sekwencji commitów

```bash
# Zadanie: implementuj logowanie

# 1. dev-backend: model + auth
feat(auth): dodaj model Uzytkownik i hashowanie hasel
fix(auth): popraw walidacje hasla (min 8 znakow)
refactor(auth): wyodrębnij AuthService z routera

# 2. dev-backend: endpointy
feat(auth): implementuj POST /auth/login
feat(auth): implementuj POST /auth/register  
feat(auth): implementuj POST /auth/refresh

# 3. dev-frontend: komponenty
feat(login): dodaj komponent LoginView
feat(login): dodaj walidacje formularza
style(login): dostosuj do design systemu

# 4. dev-review: finalne
docs(readme): aktualizuj dokumentacje logowania
chore(ci): dodaj github workflow dla testow
```

## Automatyzacja (opcjonalnie)

Możesz użyć skryptu do automatycznego generowania commitów:

```bash
# .git/hooks/pre-commit
#!/bin/bash
# Sprawdź czy commit message jest zgodny z konwencją
```

## Checklist przed każdym commitem

- [ ] Kod działa (testy przechodzą)
- [ ] Brak debug/console.log
- [ ] Nazwy zmiennych sensowne
- [ ] Komentarze gdzie potrzeba
- [ ] Formatowanie spójne (ESLint/Black)
- [ ] Commit message zgodny z konwencją
- [ ] Zmieniony kontekst developera

## Konwencja nazewnictwa branchy

```
<typ>/<ticket>-<krotki-opis>
np:
feature/RAO-123-implement-login
fix/RAO-456-login-validation
refactor/RAO-789-auth-service
```
