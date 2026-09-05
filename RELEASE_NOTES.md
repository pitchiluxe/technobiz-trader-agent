# TechnobizTrader v1.0.0 — Initial Release

**Release date:** September 4, 2026
**Platform:** Windows 10/11 (win-x64)
**Python:** 3.14

## What's included

### Desktop Application
- **TechnobizTrader.exe** — One-click launcher for Windows. Starts the backend server and opens the trading office UI in your browser.
- Bundled Python 3.14 runtime — no Python installation required on the host machine.

### System Requirements
- Windows 10 or Windows 11
- 4 GB available RAM
- Internet connection for live market data
- MetaTrader 5 (optional — runs in demo mode without it)

## Installation

1. Download `TechnobizTrader-Setup-1.0.0.exe` from this release page.
2. Run the installer — no admin rights needed.
3. Launch from the Start menu or desktop shortcut.
4. On first run, open **Settings** to connect MetaTrader 5 or enter your API credentials.

## Key Features in This Release

- **Three-agent ICT pipeline**: Trend-Master → Analyse-Master → Trader-Master
- **Hard risk controls**: 2% max per trade, 5% daily drawdown stop, news blackout (±10 min around FOMC/NFP/CPI/ECB/BoE/BoJ)
- **Kill zone detection**: liquidity sweep, break of structure, order block, pullback entry
- **Tiered exits**: 50% at TP1 → BE, 30% at TP2, 20% trailing stop
- **Desktop GUI**: Minecraft-inspired trading office with real-time phase feed
- **GUI auth**: session-token based login with 1-hour expiry

## Verifying the Download

SHA-256 checksum for the Windows installer exe (`TechnobizTrader-Setup-1.0.0.exe`):

```powershell
Get-FileHash TechnobizTrader-Setup-1.0.0.exe -Algorithm SHA256

# Expected:
# BFEEE821D05495496FCDC9E67EF6AAFC70D341982ED1C184B50504A9D41CA746

# Then verify the contained exe:
cd .\TechnobizTrader\
Get-FileHash TechnobizTrader.exe -Algorithm SHA256
```

## Known Limitations

- Linux/macOS builds not yet available (source install: see README)
- Telegram notifications require a Telegram bot token (configured in Settings)
- MT5 data feed requires the MT5 terminal running on the same machine

## Source Code

Full source is available at:
https://github.com/pitchiluxe/technobiz-trader-agent

## Changelog

### v1.0.0 — September 4, 2026
- Initial release
- 3-agent ICT trading pipeline
- Minecraft-style desktop GUI
- News blackout for high-impact economic events
- Hard risk management (2% risk, tiered exits, daily DD stop)
