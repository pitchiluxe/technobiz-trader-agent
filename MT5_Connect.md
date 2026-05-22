# MT5 Connection Guide - TechnobizTrader

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Purpose:** Connect TechnobizTrader to MetaTrader 5 for real-time trading

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What You Need](#what-you-need)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Supported Trading Pairs](#supported-trading-pairs)
5. [API & Documentation Links](#api--documentation-links)
6. [Troubleshooting](#troubleshooting)
7. [Automated Trading Workflow](#automated-trading-workflow)
8. [Trade Approval System](#trade-approval-system)

---

## Quick Start

**TL;DR - Get started in 5 minutes:**

```bash
# 1. Install MetaTrader5 Python package
pip install MetaTrader5

# 2. Download MetaTrader 5 terminal
# Link: https://www.metatrader5.com/en/download

# 3. Install and create account

# 4. Edit .env with MT5 credentials
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo

# 5. Run the agent
python main.py
```

---

## What You Need

### **1. MetaTrader 5 Terminal Application**

**Download Link:** https://www.metatrader5.com/en/download

**What it is:**
- Desktop application for forex/crypto/stock trading
- Provides live market data and execution
- Your app communicates with it via Python

**Installation:**
- Download for Windows, Mac, or Linux
- Run installer and complete setup
- Create a demo or live trading account

**File Location after install:**
- Windows: `C:\Program Files\MetaTrader 5`
- Mac: `/Applications/MetaTrader 5`

---

### **2. MetaTrader5 Python Package**

**Installation:**
```bash
pip install MetaTrader5
```

**What it does:**
- Allows your Python app to communicate with MT5
- Fetches market data (candles, prices)
- Executes trades on your account
- Retrieves account information

**Documentation:** https://www.mql5.com/en/docs/integration/python_metatrader5

---

### **3. MetaTrader 5 Trading Account**

**Option A: Demo Account (Recommended for Testing)**

```
✓ Free to create
✓ $10,000 virtual funds
✓ No real money risk
✓ Full feature access
✓ Real market data

Steps:
1. Download MT5 from: https://www.metatrader5.com/en/download
2. Install application
3. Click "Open Account" in MT5
4. Select "Demo Account"
5. Choose broker (e.g., ICMarkets, MetaQuotes)
6. Get account credentials
```

**Option B: Live Account (For Real Trading)**

```
✓ Use real money
✗ Real financial risk
✓ Real profits

Steps:
1. Choose a regulated broker:
   - IC Markets: https://www.icmarkets.com
   - Exness: https://www.exness.com
   - XM: https://www.xm.com
   - Others: https://www.mql5.com/en/brokers
2. Complete verification (ID, address, etc.)
3. Fund your account
4. Get trading credentials
```

---

## Step-by-Step Setup

### **STEP 1: Download & Install MetaTrader 5**

```
1. Go to: https://www.metatrader5.com/en/download
2. Click "Download MetaTrader 5"
3. Run installer
4. Follow installation wizard
5. Launch MT5 when complete
```

### **STEP 2: Create a Trading Account**

```
A. In MetaTrader 5 application:

1. Click "File" → "Open Account"
2. Select account type:
   ✓ Demo (recommended first)
   ✓ Live (requires funding)
3. Choose broker:
   - ICMarkets (recommended for automation)
   - MetaQuotes-Demo
   - Your broker's MT5 server
4. Fill account details:
   - First name, Last name, Email
   - Password (safe this!)
   - Leverage (1:30 - 1:500 typically)
5. Verify email
6. Login to new account

B. Your Account Credentials:
   Account Number: [from MT5]
   Password: [from account setup]
   Server: [from MT5, e.g., "ICMarkets-Demo"]
```

### **STEP 3: Verify Account Works in MT5**

```
In MetaTrader 5 application:

1. Verify you're logged in (check top-right corner)
2. Check Account Balance (bottom-right)
3. Check Market Watch shows prices updating
4. Verify you can see candles on charts

If everything shows data → Your account is LIVE and ready!
```

### **STEP 4: Install Python Package**

```bash
# Open terminal/PowerShell
pip install MetaTrader5

# Verify installation
python -c "import MetaTrader5; print('✓ MetaTrader5 installed')"
```

### **STEP 5: Configure .env File**

```bash
# Copy template
cp .env.template .env

# Edit .env with your credentials
```

**Fill in these fields:**

```env
# Your account credentials from MT5
MT5_ACCOUNT=12345678          # Account number (numeric)
MT5_PASSWORD=your_password     # Account password
MT5_SERVER=ICMarkets-Demo      # Broker server (from MT5)

# Your trading account balance
ACCOUNT_BALANCE=10000          # Your actual account balance

# Database
DATABASE_URL=postgresql://user:password@localhost/technobiz_trader

# Foundry API
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=your-model
FOUNDRY_API_KEY=your-api-key
```

**Example completed .env:**

```env
ENVIRONMENT=production
DEBUG=False

MT5_ACCOUNT=5007734
MT5_PASSWORD=MySecurePass123
MT5_SERVER=ICMarkets-Demo

ACCOUNT_BALANCE=50000
TRADING_PAIRS=EURUSD,GBPUSD,USDJPY,XAUUSD,BTCUSD

DATABASE_URL=postgresql://trader:securepass@db.example.com:5432/technobiz
FOUNDRY_PROJECT_ENDPOINT=https://tradingagent.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4-trading
FOUNDRY_API_KEY=sk-abc123...
```

### **STEP 6: Test Connection**

```bash
# Test MT5 connection
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.check_mt5_terminal()"

# Expected output:
# ✅ MetaTrader 5 terminal is accessible

# Full validation
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"

# Expected output:
# VALIDATION SUMMARY:
#   Environment Variables.....✅ PASS
#   MetaTrader 5 Terminal.....✅ PASS
#   Database Connection.......✅ PASS
```

### **STEP 7: Run the Application**

```bash
# Start trading agent
python main.py

# Expected startup sequence:
# [STEP 0] Running startup validation...
# [STEP 1] Initializing database...
# [STEP 2] Initializing trading agents...
# [STEP 3] Fetching real market data from MetaTrader 5...
#   ✓ Fetched 100 Daily candles for EURUSD
#   ✓ Fetched 100 4H candles for EURUSD
#   ✓ Fetched 100 1H candles for EURUSD
# [STEP 4] Executing trading cycle...
```

---

## Supported Trading Pairs

### **Forex Pairs (Most Common)**

| Pair | Description | Volatility |
|------|-------------|-----------|
| **EURUSD** | EUR → USD | Medium |
| **GBPUSD** | GBP → USD | Medium-High |
| **USDJPY** | USD → JPY | Medium |
| **USDCHF** | USD → CHF | Medium |
| **AUDUSD** | AUD → USD | Medium |
| **NZDUSD** | NZD → USD | Medium |
| **EURJPY** | EUR → JPY | High |
| **GBPJPY** | GBP → JPY | High |
| **EURGBP** | EUR → GBP | Low-Medium |
| **AUDNZD** | AUD → NZD | Low-Medium |

### **Crypto Pairs**

| Pair | Description |
|------|-------------|
| **BTCUSD** | Bitcoin → USD |
| **ETHUSD** | Ethereum → USD |
| **LTCUSD** | Litecoin → USD |
| **XRPUSD** | Ripple → USD |

### **Commodity Pairs**

| Pair | Description |
|------|-------------|
| **XAUUSD** | Gold (Spot) → USD |
| **XAGUSD** | Silver (Spot) → USD |
| **WTIUSD** | WTI Crude Oil → USD |

### **Index Pairs**

| Pair | Description |
|------|-------------|
| **US500** | S&P 500 Index |
| **US100** | NASDAQ-100 |
| **SPX500** | S&P 500 (alternative) |
| **DAX40** | German DAX Index |
| **FTSE100** | UK FTSE-100 Index |

### **Stock Pairs** (Available on some brokers)

Symbols like: **AAPL**, **MSFT**, **TSLA**, **GOOGL**, etc.

---

## API & Documentation Links

### **Official MetaTrader 5 Resources**

| Resource | Link |
|----------|------|
| **MT5 Download** | https://www.metatrader5.com/en/download |
| **Python API Docs** | https://www.mql5.com/en/docs/integration/python_metatrader5 |
| **MQL5 Community** | https://www.mql5.com/en |
| **Broker List** | https://www.mql5.com/en/brokers |

### **Python Package Documentation**

```python
# Official PyPI page
https://pypi.org/project/MetaTrader5/

# GitHub source
https://github.com/zhukant/MT5API

# Installation:
pip install MetaTrader5

# Usage example:
import MetaTrader5 as mt5

# Initialize
if not mt5.initialize():
    print("MT5 initialization failed")
    mt5.shutdown()

# Login
if mt5.login(login=5007734, password="password", server="ICMarkets-Demo"):
    print("Login successful")

# Get account info
account_info = mt5.account_info()
print(f"Balance: {account_info.balance}")

# Get symbol prices
tick = mt5.symbol_info_tick("EURUSD")
print(f"EURUSD Bid: {tick.bid}, Ask: {tick.ask}")

# Shutdown
mt5.shutdown()
```

### **Recommended Brokers for Automation**

| Broker | Link | Min Balance | Leverage |
|--------|------|-------------|----------|
| **IC Markets** | https://www.icmarkets.com | $100 | 1:500 |
| **Exness** | https://www.exness.com | $1 | 1:2000 |
| **XM** | https://www.xm.com | $5 | 1:888 |
| **Tickmill** | https://www.tickmill.com | $100 | 1:500 |

### **Azure AI Foundry Resources**

| Resource | Link |
|----------|------|
| **Portal** | https://ai.azure.com |
| **Documentation** | https://learn.microsoft.com/en-us/azure/ai-services/ |
| **API Reference** | https://learn.microsoft.com/en-us/azure/ai-services/reference/ |
| **Python SDK** | https://github.com/Azure/azure-sdk-for-python |

---

## Troubleshooting

### **Issue: "MT5 terminal is not running"**

```
Error: MT5 terminal not accessible

Solution:
1. Open MetaTrader 5 desktop application
2. Verify you're logged into your account
3. Keep MT5 running in background
4. Run TechnobizTrader again

⚠️ Important: MT5 MUST be running for the agent to work!
   It cannot connect to a closed application.
```

### **Issue: "Login failed for account"**

```
Error: MT5 login() failed

Causes & Solutions:
1. Wrong account number
   - Check .env MT5_ACCOUNT matches MT5 (top-left)
   
2. Wrong password
   - Verify MT5_PASSWORD in .env
   - Test password by logging in MT5 manually
   
3. Wrong server
   - Check MT5_SERVER matches (bottom-right in MT5)
   - Example: "ICMarkets-Demo" or "MetaQuotes-Demo"
   
4. Account not ready
   - Demo accounts take a few minutes to activate
   - Live accounts need verification
   
5. Network issues
   - Check internet connection
   - Verify MT5 shows "connected" status
```

### **Issue: "No candles returned"**

```
Error: get_candles() returns empty list

Causes & Solutions:
1. Symbol not available
   - Verify pair is supported by your broker
   - Check symbol name (e.g., "EURUSD" not "EUR/USD")
   
2. Market closed
   - Forex: Monday 00:00 - Friday 23:00 (UTC)
   - Crypto: 24/5 (closed weekends)
   - Check broker's market hours
   
3. No tick data
   - Some brokers don't provide old candles
   - Try fetching fewer candles (e.g., limit=20)
   
4. Symbol not in Market Watch
   - In MT5, right-click "Market Watch" → "Show All"
   - Add missing symbols manually
```

### **Issue: "Connection timeout"**

```
Error: MT5 connection timeout

Solutions:
1. Verify internet connectivity
   ping www.google.com
   
2. Check firewall
   - Ensure MT5 can access network
   - Add MT5 to firewall whitelist if needed
   
3. Restart MT5
   - Close MT5 completely
   - Reopen application
   - Wait for connection to establish (~10 seconds)
   
4. Check broker status
   - Some brokers have maintenance windows
   - Visit broker's status page
```

### **Issue: "Database connection failed"**

```
Error: Cannot connect to PostgreSQL

Solutions:
1. Verify PostgreSQL is running
   
2. Check DATABASE_URL in .env
   postgresql://user:password@localhost:5432/db
   
3. Verify credentials
   - Username and password are correct
   - Database exists
   
4. Check network
   - If remote DB, verify network access
   - Firewall port 5432 open if needed
```

---

## Automated Trading Workflow

### **How It Works - End-to-End Flow**

```
USER INPUT: "Analyze EURUSD and look for bullish trades"
       ↓
[1] TREND-MASTER
    ├─ Fetches EURUSD candles (Daily, 4H, 1H)
    ├─ Analyzes: swing highs/lows, support/resistance, trend
    └─ Generates TrendReport (Bias: BULLISH, Confidence: 78%)
       ↓
[2] ANALYSE-MASTER
    ├─ Receives TrendReport
    ├─ Scans for ICT patterns:
    │  ├─ Liquidity Sweep detected ✓
    │  ├─ Break of Structure detected ✓
    │  ├─ Order Block found ✓
    │  └─ Pullback in kill zone ✓
    └─ Generates TradeSignal (Entry: 1.0530, SL: 1.0480, Confidence: 82%)
       ↓
[3] TRADER-MASTER
    ├─ Validates signal (confidence 82% > 75% threshold ✓)
    ├─ Calculates position size (2% risk = 0.50 lots)
    └─ Prepares ExecutionRecord (Status: PENDING)
       ↓
[4] APPROVAL GATEWAY (USER APPROVAL REQUIRED)
    ├─ System displays trade details to user
    ├─ User reviews all parameters:
    │  ├─ Entry Price: 1.0530
    │  ├─ Stop Loss: 1.0480 (50 pips)
    │  ├─ Take Profit: 1.0580, 1.0630, 1.0680
    │  ├─ Risk: $500 (2% of account)
    │  └─ Confidence: 82%
    ├─ User chooses: APPROVE ✓ or REJECT ✗
    └─ If APPROVED → Execute on MT5
       If REJECTED → Wait for next signal
```

### **Requesting Analysis for Any Pair**

**In Interactive Mode (Future Feature):**

```bash
# User can request any trading pair
$ python main.py --pair EURUSD --direction bullish
$ python main.py --pair XAUUSD --direction any
$ python main.py --pair GBPJPY --analysis-only

# System analyzes and reports findings
```

**Current Usage (main.py):**

```bash
# Edit .env to set trading pairs
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD,BTCUSD

# Run agent - analyzes all pairs in sequence
python main.py
```

### **Supported Analysis Requests**

The system can analyze:

```python
# Trend Analysis Only
✓ "What is the trend for EURUSD?"
✓ "Is GBPJPY bullish or bearish?"
✓ "Show me support/resistance for XAUUSD"

# Trade Signals
✓ "Find buy opportunities in EURUSD"
✓ "Are there any sell signals in GBPUSD?"
✓ "What's the next best entry for BTC?"

# Multiple Pairs
✓ "Analyze EURUSD, GBPUSD, USDJPY"
✓ "Which pair has the best bullish setup?"

# Timeframe Specific
✓ "4H analysis for EURUSD"
✓ "Daily trends for commodities"
```

---

## Trade Approval System

### **How Trade Approval Works**

```
FLOW: Signal Generated → User Approval → Trade Executed
```

### **Step-by-Step Approval Process**

**1. Signal Generated by Analyse-Master**

```
TradeSignal generated:
├─ Entry Level: 1.0530
├─ Stop Loss: 1.0480
├─ Take Profit Levels: 1.0580, 1.0630, 1.0680
├─ Risk/Reward: 1:2.5
└─ Confidence: 82%
```

**2. System Requests Approval**

```
╔════════════════════════════════════════════════════════╗
║           ⚠️  TRADE APPROVAL REQUIRED                  ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  PAIR:           EURUSD                              ║
║  DIRECTION:      BUY                                 ║
║  SIGNAL ID:      SIG-A1B2C3D4                         ║
║                                                        ║
║  ENTRY PRICE:    1.0530 (Current: 1.0525)           ║
║  STOP LOSS:      1.0480 (50 pips risk)              ║
║  RISK AMOUNT:    $500 (2% of account)               ║
║                                                        ║
║  TAKE PROFIT 1:  1.0580 (50 pips gain)              ║
║  TAKE PROFIT 2:  1.0630 (100 pips gain)             ║
║  TAKE PROFIT 3:  1.0680 (150 pips gain)             ║
║                                                        ║
║  CONFIDENCE:     82%                                 ║
║  ICT ELEMENTS:   ✓ Sweep ✓ BoS ✓ OB ✓ Pullback      ║
║                                                        ║
║  ──────────────────────────────────────────────────   ║
║  [A] APPROVE TRADE  [R] REJECT  [V] VIEW DETAILS     ║
║  ──────────────────────────────────────────────────   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

**3. User Decision**

```python
# User options:
A) APPROVE   → Trade is executed immediately on MT5
R) REJECT    → Signal is logged, wait for next
V) VIEW      → See detailed analysis and pattern info
```

**4. Trade Execution (if approved)**

```
✓ Order placed on MT5
✓ Position opened: 0.50 lots @ 1.0530
✓ Stop Loss set: 1.0480
✓ Take Profits set: 1.0580, 1.0630, 1.0680
✓ Execution logged to database
✓ Real-time monitoring started
```

### **Approval Decision Factors**

**When to APPROVE:**

```
✓ Confidence ≥ 75%
✓ All 4 ICT elements confirmed
✓ R/R ratio ≥ 1:2
✓ Current price near entry (slippage < 2 pips)
✓ Market is active (not during low liquidity)
✓ Account drawdown < 5%
✓ Portfolio has room (< 3 concurrent trades)
✓ Your personal risk tolerance allows
```

**When to REJECT:**

```
✗ Confidence < 75%
✗ Missing any ICT elements
✗ R/R ratio < 1:2
✗ Slippage too high (> 2 pips from entry)
✗ Market is in low-liquidity period
✗ Account drawdown > 5% (reaching limit)
✗ Already have 3+ open trades
✗ You're unsure about the setup
✗ News/events coming that affect the pair
```

### **Future: Automated Approval Modes** (Optional)

```python
# Mode 1: Manual Approval (Current - RECOMMENDED)
APPROVAL_MODE = "manual"
# Each signal requires user approval

# Mode 2: Confidence-Based (Optional future)
APPROVAL_MODE = "confidence"
CONFIDENCE_THRESHOLD = 85
# Auto-approve if confidence ≥ 85%
# Manual approval for 75-85%
# Auto-reject if < 75%

# Mode 3: Paper Trading (Testing)
APPROVAL_MODE = "paper"
# Simulates trades without real money
# For backtesting and validation
```

---

## Advanced: Custom Pair Analysis

### **Analyze Specific Pairs On-Demand**

**Create a custom analysis script:**

```python
# File: analyze_pair.py
import asyncio
from agents.workflow import TradingWorkflow
from market_data.mt5_provider import MT5Provider
from config.settings import settings

async def analyze_pair(pair: str, direction: str = "any"):
    """
    Analyze a specific trading pair.
    
    Args:
        pair: Trading pair symbol (e.g., "EURUSD", "XAUUSD")
        direction: "any", "bullish", or "bearish"
    """
    # Initialize provider
    provider = MT5Provider(
        account=settings.MT5_ACCOUNT,
        password=settings.MT5_PASSWORD,
        server=settings.MT5_SERVER,
    )
    
    # Connect and fetch data
    await provider.connect()
    market_data = {
        "daily": await provider.get_candles(pair, "D", 100),
        "4h": await provider.get_candles(pair, "4H", 100),
        "1h": await provider.get_candles(pair, "1H", 100),
    }
    await provider.disconnect()
    
    # Analyze
    workflow = TrendingWorkflow(verbose=True)
    trend_report = await workflow.trend_master.analyze(market_data)
    
    # Display results
    print(f"\n{pair} Analysis ({direction}):")
    print(f"  Bias: {trend_report.bias}")
    print(f"  Confidence: {trend_report.confidence}%")
    print(f"  Support Levels: {trend_report.support_resistance.get('support_levels')}")
    print(f"  Resistance Levels: {trend_report.support_resistance.get('resistance_levels')}")

# Usage
if __name__ == "__main__":
    asyncio.run(analyze_pair("EURUSD", "bullish"))
    asyncio.run(analyze_pair("XAUUSD", "any"))
    asyncio.run(analyze_pair("GBPJPY", "bearish"))
```

**Run custom analysis:**

```bash
python analyze_pair.py EURUSD bullish
python analyze_pair.py XAUUSD any
python analyze_pair.py GBPJPY bearish
```

---

## Connecting Multiple Brokers (Advanced)

### **Switch Between Brokers**

```env
# Support multiple MT5 accounts
PRIMARY_MT5_ACCOUNT=5007734
PRIMARY_MT5_PASSWORD=password1
PRIMARY_MT5_SERVER=ICMarkets-Demo

SECONDARY_MT5_ACCOUNT=5007735
SECONDARY_MT5_PASSWORD=password2
SECONDARY_MT5_SERVER=Exness-Demo

# In code:
provider1 = MT5Provider(account=settings.PRIMARY_MT5_ACCOUNT, ...)
provider2 = MT5Provider(account=settings.SECONDARY_MT5_ACCOUNT, ...)
```

---

## Summary Checklist

- [ ] Download MetaTrader 5: https://www.metatrader5.com/en/download
- [ ] Create MT5 demo account (ICMarkets recommended)
- [ ] Note your account credentials (Account #, Password, Server)
- [ ] Install Python: `pip install MetaTrader5`
- [ ] Copy `.env.template` to `.env`
- [ ] Fill in .env with MT5 credentials
- [ ] Run validation: `python -c "from utils.startup_validator import StartupValidator; StartupValidator.full_startup_check()"`
- [ ] Start agent: `python main.py`
- [ ] Review trade signals in system output
- [ ] Approve/Reject trades as they come
- [ ] Monitor trades in MT5 terminal
- [ ] Check logs: `tail -f logs/technobiz_trader.log`

---

## Quick Reference

**MetaTrader 5 Download:** https://www.metatrader5.com/en/download  
**Python API Docs:** https://www.mql5.com/en/docs/integration/python_metatrader5  
**Broker List:** https://www.mql5.com/en/brokers  
**IC Markets:** https://www.icmarkets.com (Recommended)

---

**Document Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Status:** ✅ Ready for Production
