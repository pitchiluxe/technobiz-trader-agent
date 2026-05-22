# TradingView Connection Guide - TechnobizTrader

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Purpose:** Connect TechnobizTrader to TradingView for advanced technical analysis

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [What You Need](#what-you-need)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [TradingView API Types](#tradingview-api-types)
5. [Supported Trading Pairs](#supported-trading-pairs)
6. [API & Documentation Links](#api--documentation-links)
7. [Troubleshooting](#troubleshooting)
8. [Usage Examples](#usage-examples)
9. [Webhook Configuration (Advanced)](#webhook-configuration-advanced)

---

## Quick Start

**TL;DR - Get started in 10 minutes:**

```bash
# 1. Install TradingView Python package
pip install tradingview-ta

# 2. Create TradingView account (free)
# Link: https://www.tradingview.com/accounts/signup/

# 3. Edit .env with TradingView settings
DATA_PROVIDER=tradingview
TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX

# 4. Run the agent
python main.py

# 5. Start analyzing!
# The system will fetch analysis from TradingView automatically
```

---

## What You Need

### **1. TradingView Account (Free)**

**Signup Link:** https://www.tradingview.com/accounts/signup/

**What you get (Free tier):**
- ✅ Access to 100+ technical indicators
- ✅ Multi-market coverage (stocks, crypto, forex, commodities)
- ✅ Technical analysis API (1-minute delayed data)
- ✅ Community scripts and strategies
- ⚠️ 1-minute data delay
- ⚠️ No webhooks (need premium)

**Account creation steps:**
```
1. Go to: https://www.tradingview.com/accounts/signup/
2. Sign up with email
3. Verify email
4. Create profile
5. Done! Ready to use
```

**No credit card required for free account!**

---

### **2. TradingView-TA Python Package**

**Installation:**
```bash
pip install tradingview-ta
```

**What it does:**
- Analyzes technical indicators from TradingView data
- Returns buy/sell recommendations
- Provides access to 100+ indicators (RSI, MACD, Bollinger Bands, etc.)
- Multi-market support (Forex, Crypto, Stocks, Commodities)
- Real-time analysis

**Documentation:** https://github.com/AnalysisIndicators/tradingview_ta

---

### **3. Internet Connection**

- Stable internet required (TradingView API calls)
- API calls are fast (~200-500ms)
- Caching layer built in to minimize calls

---

## Step-by-Step Setup

### **STEP 1: Create TradingView Account**

```
1. Go to: https://www.tradingview.com/accounts/signup/
2. Click "Sign up"
3. Enter email address
4. Create password
5. Verify email (check inbox)
6. Complete profile setup
7. Login to dashboard
```

**Verify your account works:**
- Go to: https://www.tradingview.com/chart/
- See live charts and data
- You're ready to go!

---

### **STEP 2: Install Python Package**

```bash
# Open terminal/PowerShell
pip install tradingview-ta

# Verify installation
python -c "from tradingview_ta import AnalysisIndicators; print('✓ tradingview-ta installed')"
```

---

### **STEP 3: Understand API Types**

TradingView offers three API access levels:

#### **Option A: Free API** (Recommended to start)

```env
TRADINGVIEW_API_TYPE=free
```

**Features:**
- ✅ Completely free
- ✅ 100+ indicators
- ✅ All markets (Forex, Crypto, Stocks, etc.)
- ⚠️ 1-minute delayed data
- ⚠️ Rate limited (for safety)

**Best for:**
- Testing and development
- Traders who don't need real-time
- Paper trading and backtesting

---

#### **Option B: Premium API** ($15/month)

```env
TRADINGVIEW_API_TYPE=premium
TRADINGVIEW_API_KEY=your_premium_api_key
```

**Features:**
- ✅ Real-time data (no delay)
- ✅ Higher rate limits
- ✅ Webhook support
- ✅ Extended technical analysis
- ✓ Cost: $15/month

**Best for:**
- Active traders
- Scalpers who need real-time
- Traders wanting webhooks

**Get Premium:** https://www.tradingview.com/gopro/?source=technical_analysis

---

#### **Option C: Pro/Advanced** ($30-50/month)

```env
TRADINGVIEW_API_TYPE=advanced
TRADINGVIEW_API_KEY=your_advanced_api_key
```

**Features:**
- ✅ All premium features
- ✅ API webhooks
- ✅ Strategy backtesting
- ✅ Pine Script development
- ✓ Cost: $30-50/month

**Best for:**
- Professional traders
- Strategy developers
- Automated webhook systems

**Get Advanced:** https://www.tradingview.com/gopro/?source=technical_analysis

---

### **STEP 4: Configure .env File**

```bash
# Copy template
cp .env.template .env

# Edit .env with TradingView settings
```

**Fill in these fields:**

```env
# Use TradingView as data provider
DATA_PROVIDER=tradingview

# TradingView API settings
TRADINGVIEW_API_TYPE=free              # free, premium, or advanced
TRADINGVIEW_EXCHANGE=FOREX             # Market focus (FOREX, BINANCE, NYSE, etc.)

# Optional: If using premium/advanced
# TRADINGVIEW_API_KEY=your_api_key_here
```

**Example completed .env:**

```env
ENVIRONMENT=development
DEBUG=False
DATA_PROVIDER=tradingview

# TradingView Configuration
TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX

# Trading Account
ACCOUNT_BALANCE=10000
TRADING_PAIRS=EURUSD,GBPUSD,USDJPY,XAUUSD,BTCUSD

# Database
DATABASE_URL=sqlite:///./technobiz_trader.db

# Azure Foundry
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=your-model
FOUNDRY_API_KEY=your-api-key
```

---

### **STEP 5: Test Connection**

```bash
# Test TradingView connection
python -c "
from market_data.tradingview_provider import TradingViewProvider

provider = TradingViewProvider()
analysis = provider.get_analysis('EURUSD', '1d')
print('✓ TradingView connection successful!')
print(f'  EURUSD Daily recommendation: {analysis[\"recommendation\"]}')
print(f'  Buy signals: {analysis[\"buy_signals\"]}')
print(f'  Sell signals: {analysis[\"sell_signals\"]}')
"
```

**Expected output:**
```
✓ TradingView connection successful!
  EURUSD Daily recommendation: BUY
  Buy signals: 5
  Sell signals: 2
```

---

### **STEP 6: Validate Full System**

```bash
# Full validation
python -c "
from market_data.data_provider_factory import validate_data_provider

if validate_data_provider():
    print('✅ VALIDATION PASSED')
    print('   TradingView connection: ✓')
    print('   Ready to analyze markets!')
else:
    print('❌ VALIDATION FAILED')
    print('   Check your .env file')
"
```

---

### **STEP 7: Run the Application**

```bash
# Start analysis mode (no execution)
python main.py

# Or start interactive mode
python interactive_mode.py

# Or use hybrid mode with MT5 execution
# (Edit .env: DATA_PROVIDER=hybrid)
python main.py
```

**Expected startup:**
```
✓ TradingView provider initialized
✓ Database connected
✓ Agents ready
✓ Fetching EURUSD analysis (Daily, 4H, 1H)...
✓ Signal generated
[Ready for manual execution or trade approval]
```

---

## TradingView API Types

### **Quick Comparison**

| Feature | Free | Premium | Pro |
|---------|------|---------|-----|
| **Cost** | $0 | $15/mo | $30+/mo |
| **Data Delay** | 1 min | Real-time | Real-time |
| **Indicators** | 100+ | 100+ | All |
| **Rate Limit** | Limited | Higher | Highest |
| **Webhooks** | ❌ | ✅ | ✅ |
| **API Key** | ❌ | ✅ | ✅ |
| **Pine Scripts** | ✅ | ✅ | ✅ |
| **Best For** | Learning | Trading | Pro traders |

---

## Supported Trading Pairs

### **Forex Pairs** (FOREX exchange)

```
Major Pairs (most liquid):
EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD

Minor Pairs:
EURJPY, GBPJPY, EURGBP, AUDNZD, NZDJPY, EURAUD

Exotic Pairs:
USDZAR, USDHKD, USDSGD, USDMXN, USDBRL

Currency format: XXX:YYY
Example: "OANDA:EURUSD" or "FX_IDC:EURUSD"
```

### **Cryptocurrencies** (BINANCE exchange)

```
Major Crypto:
BTCUSD, ETHUSD, LTCUSD, XRPUSD, BNBUSD, DOGEUSD

Format: BINANCE:BTCUSD
Examples:
- BINANCE:BTCUSD
- BINANCE:ETHUSD
- BINANCE:BNBUSD
```

### **Commodities** (FOREX exchange)

```
Precious Metals:
XAUUSD (Gold)
XAGUSD (Silver)
XPTUSD (Platinum)

Energy:
WTIUSD (WTI Oil)
BRENTUSD (Brent Oil)
NATGASUSD (Natural Gas)

Format: XAUUSD or Ticker:Symbol
Examples:
- XAUUSD
- XAGUSD
- WTIUSD
```

### **Indices** (NYSE/NASDAQ exchange)

```
US Indices:
US500 (S&P 500)
US100 (NASDAQ-100)
US30 (Dow Jones)

European Indices:
DAX40 (German DAX)
FTSE100 (UK FTSE)

Format: CRYPTOCOMPARE:SP500USD or INDEXSP:SPX
Examples:
- US500
- DAX40
- FTSE100
```

### **Stocks** (NYSE/NASDAQ exchange)

```
US Stocks:
AAPL (Apple)
MSFT (Microsoft)
TSLA (Tesla)
GOOGL (Google/Alphabet)
AMZN (Amazon)

European Stocks:
SAP (SAP SE)
SAN (Sanofi)

Format: NASDAQ:AAPL or NYSE:TSLA
Examples:
- NASDAQ:AAPL
- NYSE:TSLA
- NASDAQ:MSFT
```

### **How to Find Symbol Formats**

1. **Go to TradingView.com**
2. **Search for your symbol** (e.g., "EURUSD")
3. **Check the symbol bar** - shows correct format
   - Example: Might show `OANDA:EURUSD` or `FX_IDC:EURUSD`
4. **Copy exact format** into your code/config

---

## API & Documentation Links

### **Official TradingView Resources**

| Resource | Link | Purpose |
|----------|------|---------|
| **Website** | https://www.tradingview.com | Main platform |
| **Signup** | https://www.tradingview.com/accounts/signup/ | Free account |
| **Chart Tool** | https://www.tradingview.com/chart/ | Live charts |
| **Market Overview** | https://www.tradingview.com/markets/ | All markets |
| **Ticker Guide** | https://www.tradingview.com/documentation/index.html | Symbol formats |

### **Python Package Documentation**

```
Package: tradingview-ta
GitHub: https://github.com/AnalysisIndicators/tradingview_ta
PyPI: https://pypi.org/project/tradingview-ta/

Installation:
pip install tradingview-ta

Quick Example:
from tradingview_ta import AnalysisIndicators

symbol = "EURUSD"
screener = "forex"  # or "crypto", "stock"
interval = "1d"     # Daily timeframe

analysis = AnalysisIndicators(symbol, interval, screener)
print(analysis.summary)  # Returns overall recommendation
print(analysis.indicators)  # All indicators
```

### **Supported Screeners (Markets)**

```
screener="forex"        → Forex pairs (EURUSD, GBPUSD, etc.)
screener="crypto"       → Cryptocurrencies (BTCUSD, ETHUSD, etc.)
screener="stock"        → Stocks (AAPL, MSFT, etc.)
screener="cfd"          → Indices and commodities (US500, XAUUSD, etc.)
```

### **Supported Timeframes**

```
"1m"  → 1 minute
"5m"  → 5 minutes
"15m" → 15 minutes
"30m" → 30 minutes
"1h"  → 1 hour
"4h"  → 4 hours
"1d"  → 1 day
"1w"  → 1 week
"1M"  → 1 month
```

### **100+ Supported Indicators**

```
Trend Indicators:
  ADX, Aroon, CCI, Ichimoku, Keltner Channel, MACD, 
  Moving Average, Parabolic SAR, Supertrend, etc.

Momentum Indicators:
  RSI, Stochastic, Williams %R, ROC, Rate of Change, etc.

Volatility Indicators:
  ATR (Average True Range), Bollinger Bands, Donchian Channel,
  Historical Volatility, Keltner Channel, etc.

Volume Indicators:
  On Balance Volume, Volume Rate of Change, Accumulation/Distribution,
  Money Flow Index, Chaikin Money Flow, etc.

See full list: https://github.com/AnalysisIndicators/tradingview_ta
```

### **Premium/Webhooks**

| Feature | Link | Cost |
|---------|------|------|
| **Premium Plan** | https://www.tradingview.com/gopro/ | $15/month |
| **Pro Plan** | https://www.tradingview.com/gopro/ | $30/month |
| **Advanced Plan** | https://www.tradingview.com/gopro/ | $50/month |
| **Webhooks** | https://www.tradingview.com/scripts/webhooks/ | Premium+ only |

---

## Troubleshooting

### **Issue: "No module named 'tradingview_ta'"**

```
Error: ModuleNotFoundError: No module named 'tradingview_ta'

Solution:
pip install tradingview-ta
python -m pip install --upgrade pip
pip install tradingview-ta --force-reinstall
```

---

### **Issue: "Connection timeout to TradingView"**

```
Error: Request timed out, TradingView API unreachable

Causes:
- Internet connection issue
- TradingView API temporarily down
- Firewall blocking requests

Solutions:
1. Check internet connection: ping google.com
2. Test TradingView: go to https://www.tradingview.com in browser
3. Restart your application
4. Check if you're rate limited (too many requests)
5. Try again in a few minutes
```

---

### **Issue: "Invalid symbol format"**

```
Error: Symbol not found: EURUSD

Causes:
- Wrong symbol format
- Symbol doesn't exist on chosen screener
- Typo in symbol name

Solutions:
1. Go to https://www.tradingview.com/chart/
2. Search for your symbol (e.g., "EURUSD")
3. Copy exact symbol shown (might be "OANDA:EURUSD")
4. Use that format in your code
```

**Symbol Format Examples:**
```
❌ Wrong: EURUSD
✅ Correct: OANDA:EURUSD or FX_IDC:EURUSD

❌ Wrong: BTCUSD
✅ Correct: BINANCE:BTCUSD or COINBASE:BTCUSD

❌ Wrong: AAPL
✅ Correct: NASDAQ:AAPL

❌ Wrong: XAUUSD
✅ Correct: TVC:GOLD (alternative format)
```

---

### **Issue: "Data delay or old data"**

```
Problem: Getting 1-minute old data even for fast trades

Causes:
- Using free TradingView API (has 1-min delay)
- Not on premium plan

Solutions:
1. For real-time data: Upgrade to Premium ($15/mo)
   - Go to: https://www.tradingview.com/gopro/
2. Alternative: Use hybrid mode with MT5 for execution:
   - DATA_PROVIDER=hybrid
   - Get analysis from TradingView, execute with MT5
3. Accept the 1-min delay for analysis-only trading
```

---

### **Issue: "API key required but I only have free account"**

```
Problem: Code asking for API_KEY but I don't have premium

Causes:
- Using premium-only features with free account
- Code configured for premium but account is free

Solutions:
1. For free tier: Don't include TRADINGVIEW_API_KEY in .env
   TRADINGVIEW_API_TYPE=free
   # Don't add TRADINGVIEW_API_KEY

2. Or upgrade to premium:
   https://www.tradingview.com/gopro/
   Get API key from account settings
   Add to .env:
   TRADINGVIEW_API_TYPE=premium
   TRADINGVIEW_API_KEY=pk_live_xxxxx
```

---

### **Issue: "Rate limit exceeded"**

```
Error: Too many requests to TradingView API

Causes:
- Making too many API calls too quickly
- No caching implemented

Solutions:
1. Add delays between requests: import time; time.sleep(1)
2. Use caching (built into TechnobizTrader)
3. Upgrade to premium for higher limits
4. Reduce analysis frequency
```

---

## Usage Examples

### **Example 1: Analyze EURUSD (Simple)**

```python
from market_data.tradingview_provider import TradingViewProvider

# Initialize provider
provider = TradingViewProvider()

# Get daily analysis
daily = provider.get_analysis("EURUSD", "1d")

print(f"Recommendation: {daily['recommendation']}")
print(f"Buy signals: {daily['buy_signals']}")
print(f"Sell signals: {daily['sell_signals']}")

# Output:
# Recommendation: BUY
# Buy signals: 8
# Sell signals: 2
```

---

### **Example 2: Multi-Timeframe Analysis**

```python
from market_data.tradingview_provider import TradingViewProvider

provider = TradingViewProvider()

# Analyze 3 timeframes
result = provider.get_multi_timeframe_analysis("EURUSD", ["1d", "4h", "1h"])

print("Daily:", result["1d"]["recommendation"])
print("4H:", result["4h"]["recommendation"])
print("1H:", result["1h"]["recommendation"])

# Output:
# Daily: BUY
# 4H: BUY
# 1H: NEUTRAL
```

---

### **Example 3: Consensus Across Timeframes**

```python
from market_data.tradingview_provider import TradingViewProvider

provider = TradingViewProvider()

# Get consensus
consensus = provider.get_consensus("EURUSD")

print(f"Overall: {consensus['consensus']}")
print(f"Confidence: {consensus['confidence']:.0f}%")

# Output:
# Overall: BUY
# Confidence: 85%
```

---

### **Example 4: Scan Multiple Symbols**

```python
from market_data.tradingview_provider import TradingViewProvider

provider = TradingViewProvider()

# Scan multiple forex pairs
pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
results = provider.scan_symbols(pairs)

for pair, analysis in results.items():
    print(f"{pair}: {analysis['recommendation']}")

# Output:
# EURUSD: BUY
# GBPUSD: NEUTRAL
# USDJPY: SELL
# AUDUSD: BUY
```

---

### **Example 5: Use with TechnobizTrader (Full Integration)**

```python
# In main.py or interactive_mode.py
from market_data.data_provider_factory import create_data_provider
from agents.workflow import TradingWorkflow
import asyncio

async def main():
    # Factory auto-creates TradingView provider based on .env
    provider = create_data_provider()
    
    # Initialize workflow
    workflow = TradingWorkflow(provider=provider)
    
    # Get analysis
    trend_report = await workflow.trend_master.analyze({
        "daily": await provider.get_multi_timeframe_analysis("EURUSD")["1d"],
        "4h": await provider.get_multi_timeframe_analysis("EURUSD")["4h"],
        "1h": await provider.get_multi_timeframe_analysis("EURUSD")["1h"]
    })
    
    print(trend_report)

# Run
asyncio.run(main())
```

---

## Webhook Configuration (Advanced)

**Webhooks** allow TradingView to push alerts directly to your system (Premium+ required).

### **What are Webhooks?**

- Real-time notifications when signals trigger
- Automatic trade execution when criteria met
- No polling/constant checking needed
- Premium/Pro plans only

### **Setup Steps**

**Step 1: Upgrade to Premium**
```
https://www.tradingview.com/gopro/
Cost: $15+/month
```

**Step 2: Create Alert in TradingView**

```
1. Go to https://www.tradingview.com/chart/
2. Add indicator (e.g., RSI)
3. Click "Create Alert"
4. Set conditions (e.g., RSI > 70)
5. Set notification: "Webhook URL"
6. Enter your webhook URL
```

**Step 3: Create Webhook Receiver**

In your app:
```python
from fastapi import FastAPI, Request
import json

app = FastAPI()

@app.post("/webhook/tradingview")
async def webhook_handler(request: Request):
    data = await request.json()
    signal = data.get("signal")  # e.g., "BUY" or "SELL"
    symbol = data.get("symbol")
    
    # Process signal
    print(f"Received {signal} signal for {symbol}")
    
    # Execute trade or generate alert
    return {"status": "received"}

# Run: uvicorn app:app --port 8000
```

**Step 4: Expose to TradingView**

```
Locally: Use ngrok to tunnel:
ngrok http 8000

Webhook URL in TradingView:
https://your-ngrok-url.ngrok.io/webhook/tradingview
```

---

## Hybrid Mode (TradingView + MT5)

**Recommended for serious traders!**

```env
# Use both TradingView (analysis) + MT5 (execution)
DATA_PROVIDER=hybrid

TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX

MT5_ACCOUNT=12345678
MT5_PASSWORD=password
MT5_SERVER=ICMarkets-Demo
```

**Benefits:**
- ✅ TradingView's advanced analysis (100+ indicators)
- ✅ MT5's reliable execution
- ✅ Real-time prices from MT5
- ✅ No additional cost (free TradingView analysis)

---

**TradingView Connection Guide v1.0.0** • April 25, 2026

For questions: See [DATA_PROVIDERS.md](DATA_PROVIDERS.md) or [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
