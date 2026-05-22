# TechnobizTrader - User Guide & Usage Instructions

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Status:** ✅ Production Ready

---

## Overview

TechnobizTrader is a fully automated multi-agent trading system with **mandatory user approval** for every trade. The system analyzes any trading pair across multiple timeframes using ICT methodology and generates trade signals with complete transparency and control.

### Key Features

- ✅ **Any Trading Pair Support** - Analyze EURUSD, GBPJPY, XAUUSD, BTCUSD, or any symbol
- ✅ **Automated Analysis Pipeline** - Trend-Master → Analyse-Master → Trader-Master
- ✅ **User Approval Gateway** - Every trade requires explicit user approval before execution
- ✅ **Real Market Data** - Live data from MetaTrader 5
- ✅ **Complete Risk Management** - Position sizing, stop loss, multiple take profits
- ✅ **Transparent Decision Making** - See all analysis and reasoning behind each trade

---

## Two Operating Modes

### **Mode 1: Automated Mode (main.py)**

**Best for:** Set-and-forget traders who want daily analysis

```bash
python main.py
```

**What happens:**
1. System analyzes configured trading pairs from .env
2. Generates trend reports and trade signals
3. **REQUIRES YOUR APPROVAL** before execution
4. Executes approved trades on MetaTrader 5
5. Logs all results to database

**Configuration in .env:**
```env
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD,BTCUSD
ACCOUNT_BALANCE=50000
```

---

### **Mode 2: Interactive Mode (interactive_mode.py)**

**Best for:** Active traders who want full control and flexibility

```bash
python interactive_mode.py
```

**Menu Options:**
- Analyze any trading pair (trend only, no trades)
- Analyze and generate trade signal (with approval)
- Execute trade with approval gateway
- View trading history
- Analyze multiple pairs
- Settings management

---

## Quick Start Guide

### **First Time Setup**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.template .env
# Edit .env with your MT5 credentials (see MT5_Connect.md)

# 3. Validate setup
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"

# Expected output:
# ✅ Environment Variables....... PASS
# ✅ MetaTrader 5 Terminal........ PASS
# ✅ Database Connection.......... PASS
```

### **Daily Usage - Automated Mode**

```bash
# Start trading agent (analyzes pairs from .env)
python main.py

# System will:
# [STEP 1] Initialize database
# [STEP 2] Initialize trading agents
# [STEP 3] Fetch real market data
# [STEP 4] Analyze pairs and generate signals
# [4c] Displays trade for approval...
```

### **Interactive Mode - Ad-Hoc Analysis**

```bash
# Start interactive mode
python interactive_mode.py

# Menu appears with options:
# [1] Analyze trading pair (trend only)
# [2] Analyze and generate trade signal
# [3] Execute trade with approval
# [4] View trading history
# [5] Analyze multiple pairs
# [6] Settings
# [7] Exit

# Example: Analyze EURUSD for trends
# Select [1]
# Enter "EURUSD"
# System shows trend analysis without generating trades
```

---

## Understanding the Trade Approval Screen

When a trade signal is generated, you'll see this:

```
======================================================================
⚠️  TRADE APPROVAL GATEWAY - REVIEW BEFORE EXECUTION
======================================================================

PAIR & DIRECTION........................... BUY
Confidence Score.......................... 82% ✓

----------------------------------------------------------------------
ENTRY & RISK PARAMETERS
----------------------------------------------------------------------
Entry Price............................. 1.05300
Stop Loss............................... 1.04800
Risk (Pips)............................ 50 pips

----------------------------------------------------------------------
TAKE PROFIT LEVELS
----------------------------------------------------------------------
TP 1 (50% position).................... 1.05800 (+50 pips)
TP 2 (30% position).................... 1.06300 (+100 pips)
TP 3 (20% position).................... 1.06800 (+150 pips)

----------------------------------------------------------------------
RISK/REWARD & PATTERNS
----------------------------------------------------------------------
Risk/Reward Ratio...................... 2.50:1 (✓ Good)

ICT Pattern Elements:
  Liquidity Sweep.................. ✓ CONFIRMED
  Break Of Structure.............. ✓ CONFIRMED
  Imbalance....................... ✓ CONFIRMED
  Pullback........................ ✓ CONFIRMED

======================================================================

  [A] APPROVE TRADE   [R] REJECT   [V] VIEW DETAILS
  Enter your choice (A/R/V): _
```

### **Your Options:**

| Choice | Action | Result |
|--------|--------|--------|
| **A** | APPROVE | Trade executed immediately on MT5 |
| **R** | REJECT | Signal discarded, wait for next |
| **V** | VIEW DETAILS | See detailed ICT analysis |

---

## Analyzing Specific Trading Pairs

### **Interactive Mode - Single Pair**

```bash
python interactive_mode.py

# Select [1] - Analyze trading pair (trend only)
# Enter: EURUSD
# System displays:
#   - Trend bias (BULLISH/BEARISH/NEUTRAL)
#   - Confidence level
#   - Support/Resistance levels
#   - Liquidity zones
#   - Swing structure
```

### **Interactive Mode - Multiple Pairs**

```bash
python interactive_mode.py

# Select [5] - Analyze multiple pairs
# Enter: EURUSD,GBPJPY,XAUUSD,BTCUSD
# System analyzes each sequentially and displays results
```

### **Automated Mode - All Configured Pairs**

**Edit .env:**
```env
TRADING_PAIRS=EURUSD,GBPJPY,XAUUSD,BTCUSD
```

**Run:**
```bash
python main.py
# Analyzes all pairs, generates signals for each
# You approve/reject each trade individually
```

### **Custom Python Script - Programmatic Analysis**

```python
# File: custom_analysis.py
import asyncio
from interactive_mode import InteractiveTradingMode

async def custom_analysis():
    trader = InteractiveTradingMode()
    await trader.initialize()
    
    # Analyze single pair
    result = await trader.analyze_pair("EURUSD", analysis_only=True)
    
    # Analyze multiple pairs
    for pair in ["GBPJPY", "XAUUSD", "BTCUSD"]:
        await trader.analyze_pair(pair, analysis_only=True)
    
    await trader.shutdown()

asyncio.run(custom_analysis())
```

```bash
python custom_analysis.py
```

---

## Trade Approval Decision Guide

### **When to APPROVE a Trade**

✅ **Good reasons to approve:**

```
✓ Confidence ≥ 75% (shows in approval screen)
✓ All 4 ICT elements confirmed
  (Liquidity Sweep, Break of Structure, Imbalance, Pullback)
✓ Risk/Reward ratio ≥ 1:2 (good risk/reward)
✓ Current price near entry level (< 2 pips slippage)
✓ Market is active (good liquidity for your pair)
✓ Account drawdown < 5% (you have risk capacity)
✓ Portfolio has room (< 3 concurrent trades)
✓ You understand the ICT setup
```

### **When to REJECT a Trade**

❌ **Good reasons to reject:**

```
✗ Confidence < 75% (borderline setup)
✗ Missing any ICT elements
✗ Risk/Reward ratio < 1:2 (unfavorable)
✗ Slippage too high (entry moved > 2 pips)
✗ Market is low-liquidity (spreads widening)
✗ Account drawdown > 5% (approaching limit)
✗ Already have 3 open trades (portfolio full)
✗ You're unsure about the setup
✗ Major news event coming (economic calendar)
✗ Chart looks choppy or unclear
```

---

## Environment Variables Explained

**Critical for Trading:**

```env
# Your MT5 Account (from MT5 terminal)
MT5_ACCOUNT=5007734
MT5_PASSWORD=YourSecurePassword
MT5_SERVER=ICMarkets-Demo

# Your Account Size (used for position sizing)
ACCOUNT_BALANCE=50000

# Which pairs to analyze (automated mode)
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD

# Maximum concurrent open trades
MAX_CONCURRENT_TRADES=3

# Risk per trade (2% is conservative)
MAX_RISK_PER_TRADE=0.02

# Minimum confidence to generate signals
MIN_CONFIDENCE_THRESHOLD=75
```

**Database:**

```env
# PostgreSQL for production
DATABASE_URL=postgresql://user:password@db.example.com/technobiz

# SQLite for development only
DATABASE_URL=sqlite:///./technobiz_trader.db
```

**Azure AI Foundry (for agent model):**

```env
FOUNDRY_PROJECT_ENDPOINT=https://tradingagent.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4-trading
FOUNDRY_API_KEY=sk-abc123...
```

---

## Supported Trading Pairs

### **Forex (FX) - Most Common**

| Pair | Description | Typical Volatility |
|------|-------------|------------------|
| EURUSD | Euro vs US Dollar | Medium |
| GBPUSD | British Pound vs USD | Medium-High |
| USDJPY | US Dollar vs Japanese Yen | Medium |
| USDCHF | US Dollar vs Swiss Franc | Medium |
| AUDUSD | Australian Dollar vs USD | Medium |
| EURGBP | Euro vs British Pound | Low |
| EURJPY | Euro vs Japanese Yen | High |
| GBPJPY | British Pound vs JPY | High |
| AUDNZD | Australian Dollar vs NZD | Low-Medium |

### **Commodities**

| Pair | Description |
|------|-------------|
| XAUUSD | Gold (Spot) per Ounce |
| XAGUSD | Silver (Spot) per Ounce |
| WTIUSD | WTI Crude Oil per Barrel |

### **Cryptocurrencies**

| Pair | Description |
|------|-------------|
| BTCUSD | Bitcoin to USD |
| ETHUSD | Ethereum to USD |
| LTCUSD | Litecoin to USD |
| XRPUSD | Ripple to USD |

### **Indices**

| Pair | Description |
|------|-------------|
| US500 | S&P 500 |
| US100 | NASDAQ-100 |
| DAX40 | German DAX |
| FTSE100 | British FTSE |

**Check with your MT5 broker for available symbols**

---

## Log Files & Monitoring

### **View Live Logs**

```bash
# Real-time log viewing
tail -f logs/technobiz_trader.log

# Last 100 lines
tail -100 logs/technobiz_trader.log

# Search for trades
grep "TRADE EXECUTED" logs/technobiz_trader.log

# Search for approvals
grep "APPROVAL" logs/technobiz_trader.log

# On Windows PowerShell
Get-Content logs/technobiz_trader.log -Tail 100 -Wait
```

### **Log Levels Explained**

```
[ERROR]     - Fatal issues (connection failed, invalid config)
[WARNING]   - Non-fatal issues (skipped signal, low confidence)
[INFO]      - Normal flow (analysis complete, signal generated)
[DEBUG]     - Detailed analysis (only in DEBUG mode)
```

### **Important Log Messages**

```
"✓ Trend: BULLISH"              - Trend analysis complete, bias found
"✓ Trade Signal Generated"      - ICT signal found, awaiting approval
"TRADE APPROVAL GATEWAY"        - User decision requested
"✓ User APPROVED"               - User approved the trade
"✗ User REJECTED"               - User rejected the trade
"✅ TRADE EXECUTED"             - Trade placed successfully on MT5
```

---

## Troubleshooting

### **Issue: "Trade approval screen doesn't appear"**

**Solution:**
1. Ensure you're using main.py (not the old version)
2. Check that a trade signal was actually generated (look for "Trade Signal Generated" in logs)
3. Verify NO_APPROVAL environment variable is not set

```bash
# Verify approval is enabled
grep -i "approval" logs/technobiz_trader.log
```

### **Issue: "All trades are being rejected"**

**Reasons & Solutions:**
1. Confidence too low
   - Signals must be ≥75% confidence
   - Wait for better patterns to align

2. Missing ICT elements
   - All 4 elements required: Sweep, BoS, Imbalance, Pullback
   - May take time to see perfect confluence

3. Risk/Reward unfavorable
   - Minimum 1:2 ratio required
   - Wait for better setups

### **Issue: "MT5 terminal connection lost"**

**Solution:**
```bash
# Restart MT5 application
1. Close MetaTrader 5 completely
2. Wait 5 seconds
3. Reopen MetaTrader 5
4. Verify you're logged in
5. Run trading agent again
```

### **Issue: "Cannot find trading pair"**

**Solution:**
1. Verify pair is supported by your broker
2. Check spelling (e.g., "EURUSD" not "EUR_USD" or "EUR/USD")
3. Add pair to Market Watch in MT5:
   - Right-click "Market Watch" in MT5
   - Select "Show All"
   - Find and enable your pair

---

## Best Practices

### **Daily Routine**

```
1. Start MT5 terminal
2. Run: python main.py
3. Review each trade signal
4. Approve/Reject based on your judgment
5. Monitor open trades in MT5
6. Check logs at end of day
7. Review performance: tail logs/technobiz_trader.log
```

### **Risk Management**

```
✓ Start with DEMO account first
✓ Never trade with money you can't afford to lose
✓ Monitor your account daily
✓ Keep max 2-3 concurrent trades
✓ Review each signal carefully before approval
✓ Don't override the system's stop loss
✓ Exit if drawdown exceeds 5%
```

### **Market Awareness**

```
✓ Check economic calendar before trading
  - Avoid high-impact news events
  - FOMC meetings, employment reports, etc.
✓ Know market hours for your pair
  - Forex: Sunday 5pm - Friday 4pm ET
  - Crypto: 24/5 (24/7 except weekends)
✓ Monitor volatility
  - Use ATR (Average True Range)
  - High volatility = wider stops needed
```

---

## Database & Record Keeping

**All trades are automatically logged:**

```sql
-- View all trades executed
SELECT * FROM trade_execution WHERE status='CLOSED' ORDER BY exit_time DESC;

-- View performance by month
SELECT 
  DATE_TRUNC('month', exit_time) as month,
  COUNT(*) as total_trades,
  SUM(p_and_l) as total_profit
FROM trade_execution
WHERE status='CLOSED'
GROUP BY month;

-- Calculate win rate
SELECT 
  COUNT(CASE WHEN p_and_l > 0 THEN 1 END) as wins,
  COUNT(CASE WHEN p_and_l < 0 THEN 1 END) as losses,
  ROUND(100.0 * COUNT(CASE WHEN p_and_l > 0 THEN 1 END) / COUNT(*), 2) as win_rate_percent
FROM trade_execution
WHERE status='CLOSED';
```

---

## Performance Metrics

The system tracks:

- **Win Rate** - % of profitable trades (target: ≥60%)
- **Risk/Reward** - Profit vs. Loss ratio (target: ≥1:2)
- **Profit Factor** - Gross Profit / Gross Loss (target: >1.5)
- **Drawdown** - Max loss from peak (target: <5% per day)
- **Slippage** - Difference between signal entry and actual entry

Check database for detailed metrics:

```bash
# Connect to database
psql -U trader -d technobiz_trader

# Query performance table
SELECT * FROM performance_metric ORDER BY date DESC LIMIT 30;
```

---

## Frequently Asked Questions (FAQ)

**Q: Can I use this with live money?**

A: Yes, but:
1. Start with DEMO account first
2. Paper trade for 1-2 months
3. Verify all systems work
4. Only then move to live with small amounts

**Q: Do I have to approve EVERY trade?**

A: Yes, by design! This ensures you maintain control. Future versions may add optional auto-approval modes.

**Q: Can I analyze pairs not in TRADING_PAIRS?**

A: Yes! Use interactive_mode.py to analyze any pair on-demand.

**Q: What if I reject a trade? Can I still trade it later?**

A: System generates new signals. If pattern re-confirms, you'll get another chance.

**Q: Can I run multiple pairs simultaneously?**

A: Yes! The system handles multiple pairs in TRADING_PAIRS. Trades are executed sequentially with your approval.

**Q: How long does analysis take?**

A: Typically 5-30 seconds per pair depending on:
- MT5 data fetch speed
- Number of candles analyzed
- Your computer performance

---

## Support & Documentation

**Key Documents:**

- [MT5_Connect.md](MT5_Connect.md) - Complete MT5 setup guide
- [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) - Production deployment
- [AGENTS.md](AGENTS.md) - Technical agent documentation
- [claude.md](claude.md) - System blueprint

**External Resources:**

- MetaTrader 5: https://www.metatrader5.com
- Python API Docs: https://www.mql5.com/en/docs/integration/python_metatrader5
- ICT Methodology: https://www.innerCircleTrading.com

---

**Version 1.0.0 - Ready for Trading**  
**Last Updated:** April 25, 2026
