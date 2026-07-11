# .devin v2.2 — Autonomiczny Software House RAO

Przeprojektowany setup zbudowany wokol jednego faktu runtime: **custom profile AGENT.md nie dostaja MCP** (bug CLI, zweryfikowany 2026-07-05, CLI 2026.8.18). W v2 nic nie jest martwe — kazdy plik robi to, co deklaruje.

## Trzy tryby (nowosc v2.2) — kto jest bramka jakosci

| Tryb | Wywolanie | Bramka | Kiedy |
|---|---|---|---|
| **FAST** (domyslny) | `/software-house "zadanie"` | Ty, na biezaco — orkiestrator pokazuje diff --stat po fazach i leci dalej; review-spawn tylko dla plikow wysokiego ryzyka (kalkulacje, auth, migracje); self-heal 1 proba potem pytanie; spec-sync raz na koncu | codzienna praca przy terminalu; M w 8-15 min |
| **CHECKPOINT** | `--checkpoint` | Ty, na granicach faz — plan wymaga OK, stop po commicie kazdej fazy | duze L, gdy jestes w poblizu |
| **FULL-AUTO** | `--full-auto` | maszyna — pelny rygor: Phase 0, review kazdej fazy, self-heal do 12 prob | wsad z backlogu (triaged + ostre DoD), odpalasz wieczorem, odbierasz rano |

Konstytucja wspolna dla wszystkich: commit per faza, targeted `git add`, secret scan, scope check, hierarchia konfliktow, backlog max `team-verified`. Pelna tabela roznic — w SKILL.md.


## Architektura (co sie zmienilo vs v1)

| v1 (stary) | v2 (ten) | Dlaczego |
|------------|----------|----------|
| 22 profile AGENT.md (ignorowane przez runtime) | 9 rol w `roles/*.md` wstrzykiwanych do `subagent_general` | Jedyny profil z MCP. Zero martwej konfiguracji, jedno zrodlo prawdy per rola. |
| "Pair programming" — 2 agenty rozmawiaja w locie | `workflows/review-protocol.md` — sekwencyjny implement→review na diffie | Stateless agenty NIE rozmawiaja. Review diffu = realna 2. para oczu za ulamek kosztu. |
| Kazde zadanie = pelny lancuch 7 faz | Routing S/M/L w SKILL.md | Typo nie budzi 20 subagentow. |
| ui + ux + motion (3 role, 6 profili) | `design-reviewer` (1 rola, 3 soczewki) | 3 spawny → 1; ta sama checklista, jeden screenshot. |
| Runtime permissions w AGENT.md | Scope check orkiestratora: `git diff --name-only` vs Scope roli | subagent_general nie egzekwuje per-rolowych perms — egzekwuje parent, post-hoc. |
| `git add .` + revert HEAD | Targeted `git add` + commit per faza + gitleaks | Revert cofa TYLKO faze; sekrety i smieci nie wchodza do repo. |
| Sekrety w config.json | Tylko `config.example.json`; config.json + config.local.json w .gitignore | Incydent z kluczami sie nie powtorzy. |
| Mapa vision w 3 miejscach | 1 kanoniczna kopia w SKILL.md | Koniec driftu dokumentacji. |
| Brak pomiaru | `_metrics.csv` po kazdym zadaniu | Po ~20 zadaniach wiesz, czy review sie oplaca (qa_escapes). |

## Struktura

```
.devin/
├── README.md                     ← ten plik
├── .gitignore                    ← config.json, config.local.json, _evidence, artefakty
├── config.example.json           ← przenosna (npx -y), BEZ sekretow
├── skills/software-house/SKILL.md ← ORKIESTRATOR (serce setupu)
├── workflows/review-protocol.md  ← kanoniczny implement→review
├── context/rao-stack.md          ← wspolny kontekst (1 kopia, wklejana do spawnow)
├── roles/                        ← 9 rol (prompt-snippety)
│   ├── tech-lead.md  db-architect.md  backend-dev.md  frontend-dev.md
│   ├── qa-engineer.md  security-auditor.md  performance-eng.md
│   ├── design-reviewer.md  product-owner.md
├── templates/
│   ├── spawn-prompt.md           ← szablon spawnu subagent_general
│   └── session-context.md        ← szablon _session_context.md
└── _evidence/                    ← artefakty sesji (git-ignored)
```

## Instalacja

1. **NAJPIERW — jesli jeszcze nie zrobione: zrotuj klucze z v1** (Anthropic, OpenRouter, GitHub PAT, Brave — byly w config.json w repo).
2. Usun z repo stary `.devin/` (w szczegolnosci: `agents/` — 22 martwe profile, `_commit*`, `audit_*`, `CHANGES.md`, `instructions/GLM_MCP_SUBAGENTS_SETUP.md` — sprzeczny z workaroundem, `MCP_CONFIG.md` z kluczami w historii: rozwaz `git filter-repo` na sekrety).
3. Wgraj v2, `cp config.example.json config.json`, wpisz sekrety do `config.local.json`.
4. `gitleaks` zainstaluj globalnie (`winget install gitleaks` / `brew install gitleaks`) — SKILL wymusza scan przed kazdym commitem, z grep-fallbackiem gdy brak.
5. Restart sesji terminala (Devin scala configi przy starcie).
6. Test: `/software-house "smoke: pokaz SHOW TABLES przez mariadb MCP w subagencie"` — subagent_general ma zwrocic 33 tabele.

## Uzycie

```
/software-house "Dodaj pole delivery_address do umow z UI i testami"          # FAST (domyslny)
/software-house --checkpoint "Refactor modulu rozliczen na nowy algorytm"   # plan-approval + bramki po fazach
/software-house --full-auto "Zadanie P0-001 z BACKLOG.md"                   # wsad nocny, zero pytan
```

## Po kazdym `devin update`

Re-test buga: spawn custom profilu z `mcp__mariadb__query_database`. Dziala → bug naprawiony → mozna wygenerowac profile AGENT.md z `roles/*.md` (skryptem, nie recznie) i przywrocic runtime permissions. Do tego czasu: `subagent_general` only.

## Zasady, ktore trzymaja jakosc

1. **Evidence albo odrzut** — kazdy HANDOFF z dowodami w `_evidence/<rola>/`
2. **Scope check** — `git diff --name-only` vs Scope roli, violation = checkout + respawn
3. **Commit per faza** — bezpieczny rollback (`git revert <hash-fazy>`)
4. **Secret scan przed commitem** — gitleaks lub grep-fallback, hit = blokada
5. **Hierarchia konfliktow** — Security veto > Data > Correctness > UX > Perf > UI > Motion > Style
6. **Metryki** — `_metrics.csv`: review_findings vs qa_escapes = twardy dowod czy proces dziala
