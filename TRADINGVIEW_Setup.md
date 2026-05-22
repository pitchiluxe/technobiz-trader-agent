# TradingView Setup Guide - TechnobizTrader

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Purpose:** Connect TechnobizTrader to TradingView for market analysis

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [TradingView vs MT5 Comparison](#tradingview-vs-mt5-comparison)
3. [What You Need](#what-you-need)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Supported Data Sources](#supported-data-sources)
6. [API Documentation](#api-documentation)
7. [Webhook Configuration](#webhook-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Get started with TradingView in 5 minutes:**

```bash
# 1. Install TradingView Python package
pip install tradingview-ta

# 2. Create free TradingView account
# Link: https://www.tradingview.com/accounts/signup

# 3. Edit .env to use TradingView
DATA_PROVIDER=tradingview
TRADINGVIEW_API_TYPE=free  # or 'premium' for paid features

# 4. Run the agent
python main.py
```

---

## TradingView vs MT5 Comparison

| Feature | TradingView | MT5 |
|---------|-------------|-----|
| **Cost** | Free (limited) / $15+/month | Free (demo) / Broker fees (live) |
| **Market Data** | All markets (stocks, crypto, forex) | Broker-specific pairs |
| **Execution** | No direct execution | Direct execution on MT5 |
| **Charts** | Best-in-class charting | Good charting |
| **Community Scripts** | Huge Pine Script library | Limited scripts |
| **Real-time Data** | Free with 1-min delay | Real-time with MT5 |
| **Technical Indicators** | 100+ built-in indicators | Full customization via MQL5 |
| **Webhooks** | Premium feature ($15+/month) | N/A |
| **Best For** | Analysis & signals | Trading execution |

### **Recommended Setup**

**Option 1: TradingView + MT5 (RECOMMENDED)**
```
TradingView (analysis & signals)
    ↓
TechnobizTrader (agent logic & risk management)
    ↓
MT5 (trade execution & account management)
```

Benefits:
- ✅ Best charting from TradingView
- ✅ Reliable execution from MT5
- ✅ Comprehensive analysis
- ✅ Full control over trades

**Option 2: TradingView Only**
```
TradingView (analysis & signals only)
    ↓
TechnobizTrader (processes signals)
    ↓
Manual execution or external API
```

Limitations:
- ❌ No direct trade execution
- ❌ Manual or webhook-based only

**Option 3: MT5 Only**
```
MT5 (analysis & execution)
    ↓
TechnobizTrader (agent logic)
```

Limitations:
- ❌ Limited technical indicators
- ❌ Less powerful charting

---

## What You Need

### **1. TradingView Account**

**Free Account:**
- Create at: https://www.tradingview.com/accounts/signup
- Access to all charts and data
- 1-minute delayed data (free tier)
- Limited to browser/mobile access

**Premium Account ($15-50/month):**
- Real-time data (no delay)
- Webhook alerts (requires Premium+)
- Advanced screeners
- Pine Script creation rights
- API access

**Tier Comparison:**

| Feature | Free | Pro | Pro+ | Premium |
|---------|------|-----|------|---------|
| Chart Access | ✓ | ✓ | ✓ | ✓ |
| Technical Alerts | ✓ | ✓ | ✓ | ✓ |
| Webhooks | ✗ | ✗ | ✓ | ✓ |
| Real-time Data | ✗ | ✓ | ✓ | ✓ |
| API Access | ✗ | ✗ | Limited | Full |
| Cost | Free | $15/mo | $20/mo | $30-50/mo |

### **2. Python TradingView Package**

**Installation:**
```bash
pip install tradingview-ta
```

**What it does:**
- Access TradingView technical analysis
- Get indicator values (RSI, MACD, etc.)
- Fetch market data
- No authentication required (uses TradingView API)

**Documentation:** https://github.com/AnalysisTradingViewTA/tradingview_ta

### **3. API Key (Optional - For Advanced Features)**

**If using Webhooks:**
- Requires Premium subscription ($20+/month)
- Get API key from: https://www.tradingview.com/account/password
- Create Pine Script alerts that send to your webhook

---

## Step-by-Step Setup

### **STEP 1: Create TradingView Account**

```
1. Go to: https://www.tradingview.com
2. Click "Sign Up" (top-right)
3. Enter email and password
4. Verify email
5. Login to TradingView

You now have free access to all charts!
```

### **STEP 2: Explore Available Data**

```
In TradingView Web:

1. Click search bar (top-left)
2. Search for any symbol:
   EURUSD, GBPUSD, XAUUSD, BTCUSD, AAPL, etc.
3. View the chart
4. Notice the symbol name format (e.g., "FOREX:EURUSD" or "OANDA:EURUSD")

Note: Symbol format varies by exchange
- Forex: FOREX:EURUSD or specific broker (e.g., OANDA:EURUSD)
- Crypto: Binance:BTCUSD or Coinbase:BTCUSD
- Stocks: NASDAQ:AAPL or NYSE:IBM
- Indices: TradingView:SPX or other exchanges
```

### **STEP 3: Install Python Package**

```bash
pip install tradingview-ta
```

**Verify installation:**

```bash
python -c "from tradingview_ta import AnalysisIndicators; \
           print('✓ TradingView package installed')"
```

### **STEP 4: Configure .env File**

```bash
# Copy template
cp .env.template .env

# Edit .env with TradingView settings
```

**Add these fields:**

```env
# Data Provider Selection
DATA_PROVIDER=tradingview        # or 'mt5' for MetaTrader 5

# TradingView Configuration
TRADINGVIEW_API_TYPE=free        # 'free' or 'premium'
TRADINGVIEW_EXCHANGE=FOREX       # FOREX, Binance, NYSE, NASDAQ, etc.

# Fallback (if TradingView fails)
FALLBACK_PROVIDER=mt5            # Optional fallback to MT5
```

**Example completed .env:**

```env
# System Settings
ENVIRONMENT=production
DEBUG=False

# Data Provider
DATA_PROVIDER=tradingview        # Use TradingView for analysis
TRADINGVIEW_API_TYPE=free

# MT5 (for execution only)
MT5_ACCOUNT=5007734
MT5_PASSWORD=MyPassword123
MT5_SERVER=ICMarkets-Demo

# Trading Settings
ACCOUNT_BALANCE=50000
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD,BTCUSD

# Database
DATABASE_URL=postgresql://user:password@localhost/technobiz_trader

# Foundry
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4-trading
FOUNDRY_API_KEY=your-api-key
```

### **STEP 5: Test TradingView Connection**

```bash
python -c "
from market_data.tradingview_provider import TradingViewProvider
provider = TradingViewProvider()
data = provider.get_analysis('EURUSD')
print(f'Recommendation: {data[\"recommendation\"]}')
print(f'Indicators: {data[\"indicators\"]}')
"

# Expected output:
# Recommendation: BUY/SELL/NEUTRAL
# Indicators: {...detailed analysis...}
```

### **STEP 6: Get Market Data**

```bash
python -c "
from market_data.tradingview_provider import TradingViewProvider
provider = TradingViewProvider()

# Get analysis for multiple timeframes
analysis = {}
for interval in ['1d', '4h', '1h']:
    analysis[interval] = provider.get_analysis('EURUSD', interval)
    print(f'{interval}: {analysis[interval][\"recommendation\"]}')
"
```

### **STEP 7: Run the Application**

```bash
# With TradingView data provider
DATA_PROVIDER=tradingview python main.py

# Or use interactive mode
DATA_PROVIDER=tradingview python interactive_mode.py
```

**Expected startup:**

```
[STEP 0] Running startup validation...
[STEP 1] Initializing database...
[STEP 2] Initializing trading agents...
[STEP 3] Fetching market data from TradingView...
  ✓ Fetched analysis for EURUSD (1D)
  ✓ Fetched analysis for EURUSD (4H)
  ✓ Fetched analysis for EURUSD (1H)
[STEP 4] Executing trading cycle...
```

---

## Supported Data Sources

### **Forex (FOREX Exchange)**

```
Symbol Format: FOREX:EURUSD or OANDA:EURUSD

Supported Pairs:
EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD,
EURJPY, GBPJPY, EURGBP, EURAUD, EURCAD, EURNZD,
GBPAUD, GBPCAD, AUDNZD, AUDCAD, CADCHF, etc.

Data Availability: 24/5 (forex market hours)
Real-time Data: Premium only (free has 1-min delay)
```

### **Cryptocurrencies**

```
Symbol Format: Binance:BTCUSD or Coinbase:ETHUSD

Common Pairs:
BTCUSD, ETHUSD, LTCUSD, XRPUSD, BCHUSD, LINKUSD,
ADAUSD, DOTUSD, UNIUSD, DOGEUSD, SOLUSD, etc.

Data Availability: 24/7
Real-time Data: Free (most exchanges)
```

### **Commodities**

```
Symbol Format: COMEX:GC1! or NYMEX:CL1!

Supported Symbols:
XAUUSD (Gold), XAGUSD (Silver), WTIUSD (Oil),
NGAS (Natural Gas), CORN, WHEAT, SOYBEANS, etc.

Data Availability: Market hours (varies by commodity)
Real-time Data: Premium only
```

### **Stock Indices**

```
Symbol Format: NASDAQ:AAPL or SPX (without prefix for TradingView)

Supported Indices:
SPX (S&P 500), INDU (Dow Jones), CCMP (NASDAQ),
DAX40 (German DAX), FTSE100 (UK FTSE), etc.

Data Availability: Stock market hours
Real-time Data: Premium only
```

### **Stocks**

```
Symbol Format: NASDAQ:AAPL or NYSE:IBM

Available Stocks:
All US stocks (NASDAQ, NYSE),
International stocks,
ETFs,
etc.

Data Availability: Market hours only
Real-time Data: Premium only
```

---

## API Documentation

### **TradingView-TA Package**

**Main Functions:**

```python
from tradingview_ta import AnalysisIndicators, Exchange

# Get analysis for a symbol
analysis = AnalysisIndicators(symbol='EURUSD', interval='1d')

# Get recommendation
print(analysis.summary)          # Overall recommendation
print(analysis['RSI'])           # Specific indicator

# Available indicators:
# RSI, STOCH.K, STOCH.D, STOCH.RSI.K, STOCH.RSI.D, MACD,
# MACD.signal, MACD.hist, ADX, AO, MOM, WR, CCI, CMO, ROC,
# BBPERCENT, HALO.UPPER, HALO.LOWER, SAR, TRIX, IKH.TENKAN,
# IKH.KIJUN, IKH.SENKOU_A, IKH.SENKOU_B, IKH.CHIKOU,
# EMA10, EMA20, EMA30, EMA50, EMA100, EMA200,
# SMA10, SMA20, SMA30, SMA50, SMA100, SMA200,
# BBANDS.UPPER, BBANDS.LOWER, ATR, Volatility

# Intervals:
# 1m (1 minute), 5m (5 min), 15m, 30m, 1h, 4h, 1d, 1w, 1mo

# Output format:
summary = {
    'RECOMMENDATION': 'BUY'/'SELL'/'NEUTRAL',
    'BUY': 5,                    # Number of buy signals
    'SELL': 2,                   # Number of sell signals
    'NEUTRAL': 1,                # Number of neutral signals
}
```

**Symbol Formats:**

```python
# Forex
analysis = AnalysisIndicators(symbol='OANDA:EURUSD')

# Crypto (Binance)
analysis = AnalysisIndicators(symbol='BINANCE:BTCUSD')

# Stocks (NASDAQ)
analysis = AnalysisIndicators(symbol='NASDAQ:AAPL')

# Commodities
analysis = AnalysisIndicators(symbol='COMEX:GC1!')

# Note: Different exchanges have different symbol formats
# Check TradingView charts for correct format
```

### **Using Multiple Exchanges**

```python
from tradingview_ta import Exchange

# Specify exchange for better accuracy
exchanges_to_check = [
    'FOREX:EURUSD',
    'OANDA:EURUSD',
    'FXCM:EURUSD',
]

for symbol in exchanges_to_check:
    try:
        analysis = AnalysisIndicators(symbol=symbol)
        print(f"{symbol}: {analysis['RECOMMENDATION']}")
    except:
        print(f"{symbol}: Not available")
```

---

## Webhook Configuration

### **Advanced: Using Pine Script for Automated Alerts**

**Only available with Premium subscription ($20+/month)**

**Setup:**

```
1. Subscribe to TradingView Premium/Pro+
2. Create custom Pine Script indicator
3. Add alert: "Alert" → "Create Alert"
4. In webhook field, enter your endpoint: https://your-domain.com/webhook
5. Alert triggers automatically on your conditions
```

**Example Pine Script Alert:**

```pine
//@version=5
strategy("TechnobizTrader Alert", overlay=true)

// Your custom logic here
longCondition = ta.crossover(ta.sma(close, 14), ta.sma(close, 28))
shortCondition = ta.crossunder(ta.sma(close, 14), ta.sma(close, 28))

if longCondition
    alert("BUY:EURUSD:1.05300:1.05000:1.05600", alert.freq_once_per_bar)

if shortCondition
    alert("SELL:EURUSD:1.05300:1.05600:1.05000", alert.freq_once_per_bar)
```

**Webhook Receiver (Optional):**

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_alert():
    data = request.get_json()
    
    # Parse TradingView alert
    # Format: "BUY:EURUSD:ENTRY:SL:TP"
    
    signal = data.get('signal')
    print(f"Received alert: {signal}")
    
    # Pass to TechnobizTrader for processing
    # ...
    
    return "OK", 200

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Troubleshooting

### **Issue: "No data available for symbol"**

```
Error: TradingView returns no data

Causes & Solutions:
1. Wrong symbol format
   - Check exact symbol on TradingView chart
   - Example: FOREX:EURUSD not EURUSD alone
   - Different exchanges have different formats
   
2. Market closed
   - Forex: Monday 00:00 - Friday 23:00 UTC
   - Stocks: During market hours only
   - Crypto: 24/7 available
   
3. Symbol doesn't exist
   - Verify spelling (case-sensitive)
   - Try searching on TradingView.com first
```

### **Issue: "Delayed data (1-minute lag)"**

```
Problem: Free TradingView has 1-minute delayed data

Solution:
1. Upgrade to Premium ($15-50/month) for real-time
2. Or combine with MT5 for real-time execution
3. Add 1-minute buffer in analysis (acceptable for most)
```

### **Issue: "Limited indicators/analysis"**

```
Problem: Free API has limited technical analysis

Solutions:
1. Upgrade to Premium for full API
2. Combine with MT5 (better for execution anyway)
3. Use community scripts/indicators
```

### **Issue: "Webhook not receiving alerts"**

```
Error: Pine Script alerts not arriving

Solutions:
1. Verify Premium subscription is active
2. Check webhook URL is publicly accessible
3. Check firewall allows incoming connections
4. Test with curl: curl -X POST http://localhost:5000/webhook
5. Verify alert condition is actually triggering
```

### **Issue: "API rate limits"**

```
Error: Too many requests to TradingView API

Solutions:
1. Add delays between requests (2+ seconds)
2. Cache results (don't re-fetch same symbol)
3. Limit number of symbols analyzed
4. Use batch mode (analyze all at once)
```

---

## Comparison with MT5

### **When to Use TradingView**

✅ **Best for:**
- Advanced technical analysis
- Community indicators and scripts
- Multi-market exploration (stocks, crypto, forex)
- Chart pattern identification
- Pre-analysis before trading

❌ **Not ideal for:**
- Direct trade execution
- Real-time data (free tier)
- Account management
- Position tracking

### **When to Use MT5**

✅ **Best for:**
- Direct trade execution
- Real-time market data
- Account management
- Position sizing
- Stop loss enforcement

❌ **Not ideal for:**
- Advanced technical analysis (limited indicators)
- Multi-market exploration
- Community collaboration
- Chart drawing tools

### **Recommended Hybrid Approach**

```
Workflow:
1. Use TradingView for analysis
2. Use TechnobizTrader for signal processing
3. Use MT5 for execution
4. Track results in database
```

**Benefits:**
- Best analysis tools (TradingView)
- Best execution platform (MT5)
- Intelligent signal processing (TechnobizTrader)
- Complete risk management
- Full audit trail

---

## Next Steps

1. **Choose your data provider:**
   - TradingView only (analysis only, no execution)
   - MT5 only (analysis + execution)
   - Hybrid (TradingView analysis + MT5 execution) ⭐ RECOMMENDED

2. **Set up TradingView:**
   - Create free account
   - Explore available symbols
   - Install Python package

3. **Configure .env:**
   - Set DATA_PROVIDER=tradingview
   - Optionally add MT5 for execution

4. **Run the system:**
   - `python main.py` (automated mode)
   - `python interactive_mode.py` (interactive mode)

---

**TradingView Setup v1.0.0** • April 25, 2026
