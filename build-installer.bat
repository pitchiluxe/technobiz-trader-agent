@echo off
title TechnobizTrader — Build Installer
echo.
echo  =====================================================
echo   TechnobizTrader v2.1.2 — Windows Installer Build
echo  =====================================================
echo.

:: Change to the gui directory
cd /d "%~dp0gui"
if errorlevel 1 (
    echo ERROR: Could not find gui\ directory.
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js: & node --version

:: Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found.
    pause
    exit /b 1
)
echo [OK] npm: & npm --version

:: Install / refresh dependencies
echo.
echo Installing Electron dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed.
    pause
    exit /b 1
)

:: Build Windows NSIS installer
echo.
echo Building Windows installer (NSIS)...
call npx electron-builder --win
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo  =====================================================
echo   Build complete!
echo   Installer: gui\release\TechnobizTrader-Setup-v2.1.2-win64.exe
echo  =====================================================
echo.
start "" "%~dp0gui\release"
pause
