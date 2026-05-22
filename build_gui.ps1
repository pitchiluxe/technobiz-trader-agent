#!/usr/bin/env pwsh
# build_gui.ps1 — Build TechnobizTrader distributables for Windows, Mac, Linux
# Run from repo root: .\build_gui.ps1 [-Target win|mac|linux|all]

param(
    [ValidateSet("win", "mac", "linux", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$Root    = Split-Path $MyInvocation.MyCommand.Path -Parent
$GuiDir  = Join-Path $Root "gui"
$Venv    = Join-Path $Root ".venv"
$Python  = if (Test-Path "$Venv\Scripts\python.exe") { "$Venv\Scripts\python.exe" } else { "python" }

Write-Host "`n=== TechnobizTrader GUI Build ===" -ForegroundColor Cyan

# 1. Generate icons
Write-Host "`n[1/4] Generating icons…" -ForegroundColor Yellow
& $Python "$Root\scripts\generate_icons.py"

# 2. Install Python GUI deps
Write-Host "`n[2/4] Installing Python dependencies…" -ForegroundColor Yellow
& $Python -m pip install -r "$Root\requirements.txt" --quiet

# 3. Install npm deps
Write-Host "`n[3/4] Installing GUI npm packages…" -ForegroundColor Yellow
Push-Location $GuiDir
npm install
Pop-Location

# 4. Build Electron app
Write-Host "`n[4/4] Building Electron app (target: $Target)…" -ForegroundColor Yellow
Push-Location $GuiDir
switch ($Target) {
    "win"   { npm run build:win   }
    "mac"   { npm run build:mac   }
    "linux" { npm run build:linux }
    "all"   { npm run build:all   }
}
Pop-Location

Write-Host "`n=== Build complete! ==="  -ForegroundColor Green
Write-Host "  Web bundle  : gui/dist/web/"  -ForegroundColor Cyan
Write-Host "  Installer   : gui/release/"   -ForegroundColor Cyan
