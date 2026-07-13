# RAO — skrypt budowania paczki wdrozeniowej
# Produkuje: rao_deploy_<data>.zip z 3 katalogami: backend/, frontend/, database/
#
# Zawartosc:
#   backend/   — kod produkcyjny (moduly + main.py + config + requirements + wsgi)
#   frontend/  — src/ + package.json + vite.config + tsconfig + index.html + .env.production
#   database/  — mysqldump rao_new (schema + dane)
#
# BEZ: _tmp/_check/_reset skryptow, logow, .venv, __pycache__, node_modules, dist,
#      pdf_screenshots, extracted_stamps, .devin, e2e, spec, backupow, screenshotow

param(
    [string]$OutputDir = ".",
    [string]$DbName = "rao_new"
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$pkgName = "rao_deploy_$timestamp"
$pkgPath = Join-Path $OutputDir $pkgName
$zipPath = "$pkgPath.zip"

Write-Host "=== RAO Deploy Package Builder ===" -ForegroundColor Cyan
Write-Host "Output: $zipPath"
Write-Host ""

# Utworz katalogi tymczasowe
$dirs = @("backend", "frontend", "database")
foreach ($d in $dirs) {
    $target = Join-Path $pkgPath $d
    New-Item -ItemType Directory -Path $target -Force | Out-Null
}

# ── 1. BACKEND ──────────────────────────────────────────────────────────────
Write-Host "[1/3] Backend..." -ForegroundColor Yellow

# Pliki root (kod produkcyjny)
$backendRootFiles = @(
    "main.py", "config.py", "database.py", "wsgi.py", "passenger_wsgi.py",
    "requirements.txt", "requirements-prod.txt"
)
# Skrypty operacyjne (przydatne na serwerze)
$backendScripts = @(
    "seed_demo_data.py", "migrate.py", "reset_db.py", "reset_admin_password.py"
)
# Moduly feature'owe (katalogi)
$backendModules = @(
    "additional_services", "archive", "articles", "audit", "auth",
    "categories", "contract_costs", "contractors", "contracts",
    "deliveries", "explorer", "integrations", "machines",
    "reports", "reservations", "services", "settings",
    "settlements", "shared", "static", "stats", "tests"
)

$beSrc = "backend"
$beDst = Join-Path $pkgPath "backend"

# Skopiuj pliki root
foreach ($f in $backendRootFiles + $backendScripts) {
    $src = Join-Path $beSrc $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $beDst $f)
    }
}

# Skopiuj moduly (bez __pycache__, .pyc)
foreach ($mod in $backendModules) {
    $src = Join-Path $beSrc $mod
    if (Test-Path $src -PathType Container) {
        $dst = Join-Path $beDst $mod
        # Uzyj robocopy dla wykluczen
        robocopy $src $dst /E /XD __pycache__ .pytest_cache .depwire .playwright-mcp /XF *.pyc *.log /NFL /NDL /NJH /NJS /NP | Out-Null
    }
}

# Skopiuj .env.example z root repo (NIE .env — sekret)
if (Test-Path ".env.example") {
    Copy-Item ".env.example" (Join-Path $beDst ".env.example")
}

$beFiles = (Get-ChildItem $beDst -Recurse -File).Count
Write-Host "  Backend: $beFiles plikow"

# ── 2. FRONTEND (zbuildowane dist/) ──────────────────────────────────────────
Write-Host "[2/3] Frontend (npm run build)..." -ForegroundColor Yellow

$feSrc = "frontend"
$feDst = Join-Path $pkgPath "frontend"

# Build frontend (produkuje dist/)
Push-Location $feSrc
Write-Host "  Budowanie dist/..."
& npm run build 2>&1 | Select-Object -Last 3 | Write-Host
Pop-Location

# Skopiuj tylko zawartosc dist/ (statyczne pliki do serwowania przez nginx/apache)
robocopy "$feSrc\dist" $feDst /E /XF *.log /NFL /NDL /NJH /NJS /NP | Out-Null

$feFiles = (Get-ChildItem $feDst -Recurse -File).Count
Write-Host "  Frontend: $feFiles plikow (zbuildowane dist/)"

# ── 3. DATABASE ─────────────────────────────────────────────────────────────
Write-Host "[3/3] Database (mysqldump)..." -ForegroundColor Yellow

$dbDumpPath = Join-Path (Join-Path $pkgPath "database") "rao_new_dump.sql"

# mysqldump — schema + dane, bez lock tables (kompatybilne z shared hosting)
$mysqldumpArgs = @(
    "--no-tablespaces",
    "--single-transaction",
    "--routines",
    "--triggers",
    "--default-character-set=utf8mb4",
    "-u", "rao_user",
    $DbName
)

# Czytaj haslo z .env
$envFile = Get-Content "backend/.env" -ErrorAction SilentlyContinue
$dbPass = ($envFile | Select-String "RAO_DATABASE_URL").ToString() -replace '.*:([^@]+)@.*','$1'
$env:MYSQL_PWD = $dbPass

try {
    # mysqldump output → UTF-8 bez BOM (mysql klient na Linux nie toleruje BOM)
    $dumpOutput = & mysqldump @mysqldumpArgs 2>&1
    $dumpText = $dumpOutput -join "`n"
    # Normalizuj COLLATE do utf8mb4_polish_ci (spójne z produkcją MariaDB 10.11)
    $dumpText = $dumpText -replace 'utf8mb4_uca1400_ai_ci', 'utf8mb4_polish_ci'
    $dumpText = $dumpText -replace 'utf8mb4_unicode_ci', 'utf8mb4_polish_ci'
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($dbDumpPath, $dumpText, $utf8NoBom)
    $dbSize = (Get-Item $dbDumpPath).Length
    Write-Host "  Database: $([math]::Round($dbSize/1KB, 1)) KB ($DbName, UTF-8 bez BOM, COLLATE=polish_ci)"
} catch {
    Write-Host "  UWAGA: mysqldump nie udany — sprawdz czy mysql jest w PATH" -ForegroundColor Red
    Write-Host "  Pusty plik .sql utworzony — wypelnij recznie" -ForegroundColor Red
    "" | Out-File $dbDumpPath
}
finally {
    Remove-Item Env:\MYSQL_PWD -ErrorAction SilentlyContinue
}

# ── 4. README paczki ────────────────────────────────────────────────────────
$readmePath = Join-Path $pkgPath "README_DEPLOY.txt"
$readme = @"
RAO — Paczka wdrozeniowa
========================
Data: $timestamp
Branch: $(git rev-parse --abbrev-ref HEAD)
Commit: $(git rev-parse --short HEAD)

Zawartosc:
  backend/    — kod produkcyjny FastAPI (moduly + main.py + requirements)
  frontend/   — zbuildowane pliki statyczne (dist/: index.html + assets/ + logo)
  database/   — dump SQL bazy rao_new (schema + dane)

Wdrozenie:
  1. Baza:    mysql --default-character-set=utf8mb4 rao_new < database/rao_new_dump.sql
              (WAZNE: --default-character-set=utf8mb4 wymagane — bez tego polskie znaki
               sie zepsuja. Dump jest UTF-8 bez BOM.)
  2. Backend: cd backend && python -m venv .venv && source .venv/bin/activate
              pip install -r requirements-prod.txt
              cp .env.example .env  (wypelnij dane produkcyjne)
              uvicorn main:app --port 8000  (lub passenger_wsgi.py na shared hosting)
  3. Frontend: skopiuj zawartosc frontend/ do katalogu serwowanego przez nginx/apache
               (np. /var/www/rao/). Proxy /rao/api -> backend:8000.
               UWAGA: frontend jest juz zbuildowany — nie potrzebuje npm ci / npm run build.

UWAGA: .env NIE jest w paczce (sekrety). Skopiuj .env.example i wypelnij recznie.
"@
$readme | Out-File $readmePath -Encoding utf8

# ── 5. ZIP ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Pakowanie ZIP..." -ForegroundColor Yellow
Compress-Archive -Path "$pkgPath\*" -DestinationPath $zipPath -Force

$zipSize = (Get-Item $zipPath).Length
Write-Host ""
Write-Host "=== GOTOWE ===" -ForegroundColor Green
Write-Host "Paczka: $zipPath"
Write-Host "Rozmiar: $([math]::Round($zipSize/1MB, 2)) MB"
Write-Host ""

# Wyczysc katalog tymczasowy
Remove-Item $pkgPath -Recurse -Force

Write-Host "Zawartosc paczki:"
Write-Host "  backend/    — $beFiles plikow (kod + requirements, BEZ .venv/__pycache__/logow)"
Write-Host "  frontend/   — $feFiles plikow (zbuildowane dist/: index.html + assets/ + logo)"
Write-Host "  database/   — rao_new_dump.sql (schema + dane)"
Write-Host "  README_DEPLOY.txt — instrukcja wdrozenia"
