@echo off
REM ============================================================
REM  TechnobizTrader — One-click build script
REM  Run from the repo root:  build.bat
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo  TechnobizTrader Build Pipeline
echo ============================================================

REM ── 1. Check Python ─────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+ and add it to PATH.
    pause & exit /b 1
)
echo [1/4] Python OK

REM ── 2. Check Node / npm ─────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 18+ from https://nodejs.org
    pause & exit /b 1
)
echo [2/4] Node.js OK

REM ── 3. Generate icon ────────────────────────────────────────
echo [3/4] Generating application icon...
python create_icon.py
if errorlevel 1 (
    echo [ERROR] Icon generation failed. Ensure Pillow is installed:
    echo         pip install Pillow
    pause & exit /b 1
)

REM ── 4. Build Electron installer ─────────────────────────────
echo [4/4] Building Windows installer...
cd gui
if not exist node_modules (
    echo     Installing npm packages...
    call npm install --save-dev electron electron-builder
)
call npm run build:win
if errorlevel 1 (
    echo [ERROR] electron-builder failed. See output above.
    cd ..
    pause & exit /b 1
)
cd ..

echo.
echo ============================================================
echo  BUILD COMPLETE
echo  Installer: gui\release\TechnobizTrader-Setup-1.0.0.exe
echo ============================================================
echo.
pause
