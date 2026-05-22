# build_installer.ps1
# Clean-build the Vite bundle and the Windows NSIS installer, then
# report the output paths.
# Run from repo root:  .\build_installer.ps1

param(
    [ValidateSet("win", "mac", "linux", "all")]
    [string]$Target = "win"
)

$ErrorActionPreference = "Stop"
$Root   = Split-Path $MyInvocation.MyCommand.Path -Parent
$GuiDir = Join-Path $Root "gui"

Write-Host "`n=== TechnobizTrader Installer Build ($Target) ===" -ForegroundColor Cyan

# 1. Install npm dependencies if needed
if (-not (Test-Path (Join-Path $GuiDir "node_modules"))) {
    Write-Host "`n[1/3] Installing npm packages..." -ForegroundColor Yellow
    Push-Location $GuiDir
    npm install
    Pop-Location
} else {
    Write-Host "`n[1/3] npm packages already present - skipping install" -ForegroundColor DarkGray
}

# 2. Vite production build
Write-Host "`n[2/3] Building React app (Vite)..." -ForegroundColor Yellow
Push-Location $GuiDir
npm run build
Pop-Location
Write-Host "  OK - Web bundle written to gui\dist\web\" -ForegroundColor Green

# 3. Electron-builder packaging
Write-Host "`n[3/3] Packaging Electron installer ($Target)..." -ForegroundColor Yellow
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
Push-Location $GuiDir
switch ($Target) {
    "win"   { npm run build:win   }
    "mac"   { npm run build:mac   }
    "linux" { npm run build:linux }
    "all"   { npm run build:all   }
}
$exitCode = $LASTEXITCODE
Pop-Location

if ($exitCode -eq 0) {
    $ReleaseDir = Join-Path $GuiDir "release"
    Write-Host "`n=== Build successful! ===" -ForegroundColor Green
    Write-Host "  Installer : $ReleaseDir\" -ForegroundColor Cyan
    if (Test-Path $ReleaseDir) {
        Get-ChildItem $ReleaseDir -File |
            Where-Object { $_.Extension -in @('.exe', '.dmg', '.AppImage', '.deb') } |
            ForEach-Object {
                $sizeMB = [math]::Round($_.Length / 1048576, 1)
                Write-Host "    $($_.Name)  ($sizeMB MB)"
            }
    }
} else {
    Write-Host "`nBuild FAILED with exit code $exitCode" -ForegroundColor Red
}

exit $exitCode
