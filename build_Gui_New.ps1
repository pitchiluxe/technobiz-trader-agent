# build_Gui_New.ps1
# Builds TechnobizTrader and places the installer in Gui_New\
# Run from the repo root:  .\build_Gui_New.ps1

$ErrorActionPreference = "Stop"
$Root   = Split-Path $MyInvocation.MyCommand.Path -Parent
$GuiDir = Join-Path $Root "gui"
$OutDir = Join-Path $Root "Gui_New"

Write-Host ""
Write-Host "=== TechnobizTrader - Build to Gui_New ===" -ForegroundColor Cyan
Write-Host ""

# 1. npm install if needed
if (-not (Test-Path (Join-Path $GuiDir "node_modules"))) {
    Write-Host "[1/3] Installing npm packages..." -ForegroundColor Yellow
    Push-Location $GuiDir
    npm install
    $c = $LASTEXITCODE
    Pop-Location
    if ($c -ne 0) { Write-Host "npm install failed" -ForegroundColor Red; exit 1 }
} else {
    Write-Host "[1/3] npm packages present - skipping install" -ForegroundColor DarkGray
}

# 2. Ensure output folder exists
Write-Host ""
Write-Host "[2/3] Output folder: $OutDir" -ForegroundColor Yellow
if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
}

# 3. Build installer
Write-Host ""
Write-Host "[3/3] Building Windows installer..." -ForegroundColor Yellow

$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"

Push-Location $GuiDir
npx electron-builder --win "--config.directories.output=$OutDir"
$exitCode = $LASTEXITCODE
Pop-Location

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "=== BUILD SUCCESSFUL ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Output : $OutDir\" -ForegroundColor Cyan
    if (Test-Path $OutDir) {
        Get-ChildItem $OutDir -File | Where-Object { $_.Extension -in @('.exe', '.dmg', '.AppImage') } | ForEach-Object {
            $mb = [math]::Round($_.Length / 1048576, 1)
            Write-Host "  File   : $($_.Name)  ($mb MB)" -ForegroundColor White
        }
    }
    Write-Host ""
    Write-Host "  To install : run TechnobizTrader-Setup-1.0.0.exe" -ForegroundColor DarkGray
    Write-Host "  Requires   : Python 3.11+ on PATH before first launch" -ForegroundColor DarkGray
} else {
    Write-Host "BUILD FAILED (exit code $exitCode)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Ensure Node.js is installed  : https://nodejs.org" -ForegroundColor DarkGray
    Write-Host "  - Run: cd gui && npm install" -ForegroundColor DarkGray
    Write-Host "  - Check gui\assets\ has icon.ico" -ForegroundColor DarkGray
}

exit $exitCode
