# Data Providers Guide - TechnobizTrader

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Purpose:** Choose and configure the right data provider for your trading setup

---

## Table of Contents

1. [Quick Comparison](#quick-comparison)
2. [Provider Selection Guide](#provider-selection-guide)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [Switching Providers](#switching-providers)

---

## Quick Comparison

| Feature | MT5 | TradingView | Hybrid |
|---------|-----|-------------|--------|
| **Cost** | Free (demo) / Broker fees | Free (1-min delay) / $15+ premium | Both combined |
| **Analysis** | Good | Excellent | ✅ Excellent |
| **Execution** | ✅ Direct | ❌ No | ✅ Direct |
| **Real-time Data** | ✅ Real-time | Free (1-min delay) / Premium (real-time) | ✅ Real-time |
| **Charts** | Good | Best-in-class | Both |
| **Indicators** | Many | 100+ | All available |
| **Complexity** | Medium | Low | Medium |
| **Best For** | Trading | Analysis | Everything |

---

## Provider Selection Guide

### **Option 1: MT5 Only** ✅ RECOMMENDED FOR EXECUTION

**Best for:**
- Traders who want simple, direct execution
- Real-time market data required
- Prefer one platform for everything
- Don't need advanced technical analysis

**Setup:**
```env
DATA_PROVIDER=mt5
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

**Workflow:**
```
Market Data (MT5)
    ↓
Trend-Master Analysis
    ↓
Analyse-Master Signals
    ↓
Trader-Master Execution (MT5)
```

**Pros:**
- ✅ Simple setup
- ✅ Real-time execution
- ✅ Single login required
- ✅ Direct account management

**Cons:**
- ❌ Limited technical indicators
- ❌ Basic charting tools
- ❌ Broker-specific pair selection

**Cost:**
- Demo: Free
- Live: Broker fees (typically 0-2 pips per trade)

---

### **Option 2: TradingView Only** ✅ RECOMMENDED FOR ANALYSIS

**Best for:**
- Traders who want best-in-class analysis
- Multi-market exploration (stocks, crypto, forex)
- Paper trading or manual execution
- Advanced technical pattern detection

**Setup:**
```env
DATA_PROVIDER=tradingview
TRADINGVIEW_API_TYPE=free        # or 'premium'
TRADINGVIEW_EXCHANGE=FOREX
```

**Workflow:**
```
TradingView Analysis
    ↓
Trend-Master Analysis
    ↓
Analyse-Master Signals
    ↓
Manual Execution or Webhooks
```

**Pros:**
- ✅ Best charting and analysis
- ✅ 100+ technical indicators
- ✅ Huge community and scripts
- ✅ All markets in one platform
- ✅ Free (with 1-min delay)

**Cons:**
- ❌ No direct trade execution
- ❌ Delayed data (free tier)
- ❌ Webhook setup required for automation

**Cost:**
- Free: $0/month (1-minute delayed data)
- Pro: $15/month (real-time)
- Premium: $30-50/month (webhooks + advanced)

---

### **Option 3: Hybrid (RECOMMENDED) ⭐ BEST OVERALL**

**Best for:**
- Traders who want everything
- Best analysis + reliable execution
- Professional trading setups
- Maximum accuracy and flexibility

**Setup:**
```env
DATA_PROVIDER=hybrid
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX
```

**Workflow:**
```
TradingView Analysis (excellent indicators)
    ↓
Trend-Master Analysis
    ↓
Analyse-Master Signals
    ↓
MT5 Real-time Prices
    ↓
Trader-Master Execution (MT5)
```

**Pros:**
- ✅ Best analysis from TradingView
- ✅ Reliable execution from MT5
- ✅ Real-time data combined
- ✅ All markets explorable
- ✅ Full automation possible

**Cons:**
- ⚠️ Requires both accounts
- ⚠️ Slightly more setup

**Cost:**
- TradingView: Free (1-min delay)
- MT5: Free (demo) or Broker fees (live)
- Total: Broker fees only (no additional cost)

---

## Configuration

### **Step 1: Edit .env File**

```bash
cp .env.template .env
```

### **Step 2: Choose Your Provider**

#### **For MT5 Only:**
```env
# Data Provider
DATA_PROVIDER=mt5

# MT5 Credentials
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo

# Trading Configuration
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD
ACCOUNT_BALANCE=50000
```

#### **For TradingView Only:**
```env
# Data Provider
DATA_PROVIDER=tradingview

# TradingView Configuration
TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX

# For execution (optional)
# You'll need to implement webhook handler

# Trading Configuration
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD
ACCOUNT_BALANCE=50000
```

#### **For Hybrid (RECOMMENDED):**
```env
# Data Provider
DATA_PROVIDER=hybrid

# TradingView Configuration
TRADINGVIEW_API_TYPE=free
TRADINGVIEW_EXCHANGE=FOREX

# MT5 Credentials (for execution)
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo

# Trading Configuration
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD
ACCOUNT_BALANCE=50000
```

### **Step 3: Validate Configuration**

```bash
python -c "
from market_data.data_provider_factory import get_data_provider_info, validate_data_provider

# Show configuration
info = get_data_provider_info()
print('Data Provider Configuration:')
for key, value in info.items():
    print(f'  {key}: {value}')

# Validate
print('\\nValidating provider...')
is_valid = validate_data_provider()
print('✅ PASS' if is_valid else '❌ FAILED')
"
```

---

## Usage Examples

### **Using MT5 Provider**

```python
from market_data.mt5_provider import MT5Provider

provider = MT5Provider()

# Get current price
price = provider.get_current_price("EURUSD")
print(f"EURUSD current price: {price}")

# Get candles
candles = provider.get_candles("EURUSD", timeframe="1d", limit=100)
for candle in candles[:3]:
    print(f"{candle.timestamp}: {candle.open} → {candle.close}")

# Execute trade
order = provider.place_order(
    symbol="EURUSD",
    order_type="BUY",
    entry=1.05300,
    stop_loss=1.05000,
    take_profit=1.05600
)
```

### **Using TradingView Provider**

```python
from market_data.tradingview_provider import TradingViewProvider

provider = TradingViewProvider()

# Get technical analysis
analysis = provider.get_analysis("EURUSD", interval="1d")
print(f"Recommendation: {analysis['recommendation']}")
print(f"Buy signals: {analysis['buy_signals']}")
print(f"Sell signals: {analysis['sell_signals']}")

# Get multi-timeframe analysis
mtf_analysis = provider.get_multi_timeframe_analysis("EURUSD")
print(f"Daily: {mtf_analysis['1d']['recommendation']}")
print(f"4H: {mtf_analysis['4h']['recommendation']}")
print(f"1H: {mtf_analysis['1h']['recommendation']}")

# Get consensus
consensus = provider.get_consensus("EURUSD")
print(f"Consensus: {consensus['consensus']} (Confidence: {consensus['confidence']:.0f}%)")

# Scan multiple symbols
results = provider.scan_symbols(["EURUSD", "GBPUSD", "USDJPY"])
for symbol, result in results.items():
    print(f"{symbol}: {result['recommendation']}")
```

### **Using Hybrid Provider**

```python
from market_data.tradingview_provider import HybridDataProvider

provider = HybridDataProvider(use_tradingview=True, use_mt5=True)

# Get combined analysis
hybrid_analysis = provider.get_hybrid_analysis("EURUSD", interval="1d")
print(f"TradingView recommendation: {hybrid_analysis['tradingview']['recommendation']}")
print(f"Current price from MT5: {hybrid_analysis.get('current_price')}")

# Execute trade (MT5 component)
# TradingView provides analysis
# MT5 provides execution
```

---

## Switching Providers

### **Switch from MT5 to TradingView**

```bash
# Edit .env
DATA_PROVIDER=tradingview

# Restart application
python main.py
```

**No code changes needed!** The factory pattern handles everything.

### **Switch from TradingView to Hybrid**

```bash
# Add MT5 credentials to .env
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=your_broker

# Change provider
DATA_PROVIDER=hybrid

# Restart application
python main.py
```

### **Emergency Fallback**

If your primary provider fails:

```env
DATA_PROVIDER=mt5
FALLBACK_PROVIDER=tradingview
```

The system will automatically switch to fallback if primary fails (when implemented).

---

## Performance Comparison

### **Data Fetch Speed**

| Operation | MT5 | TradingView |
|-----------|-----|-------------|
| Current price | <100ms | ~200ms |
| 100 daily candles | ~500ms | ~500ms |
| Technical analysis | ~1000ms | ~300ms |
| Multi-symbol scan | ~2000ms | ~800ms |

### **Reliability**

| Metric | MT5 | TradingView |
|--------|-----|-------------|
| Uptime | 99%+ | 99%+ |
| Data accuracy | Real-time | Free: 1-min delay |
| Execution speed | <100ms | N/A |
| Failure recovery | Manual restart | Auto-retry |

---

## Troubleshooting

### **"Invalid DATA_PROVIDER"**

```
Error: Invalid DATA_PROVIDER: 'thinkorswim'

Solution:
Must be 'mt5', 'tradingview', or 'hybrid'
Check your .env file
```

### **"Cannot connect to MT5"**

```
Error: MT5 terminal is not running

Solution:
1. Start MetaTrader 5 desktop application
2. Login to your account
3. Ensure "connected" status shows
4. Run TechnobizTrader again
```

### **"TradingView API error"**

```
Error: No data available for symbol

Solution:
1. Verify symbol name on TradingView.com
2. Check symbol format (e.g., "OANDA:EURUSD")
3. Verify market is open for that symbol
4. Check internet connection
```

### **"Hybrid provider partially failed"**

```
Error: MT5 failed but TradingView working

Solution:
1. If MT5 failed: Start MetaTrader 5
2. If TradingView failed: Check internet/symbol
3. Decide if you want analysis-only or execution-only mode
4. Can switch DATA_PROVIDER if needed
```

---

## Recommendations

### **For New Traders (Start Here)**

```
Step 1: Use MT5 Only (simple setup)
Step 2: Paper trade for 1-2 weeks
Step 3: Upgrade to Hybrid (get better analysis)
Step 4: Go live after successful paper trading
```

### **For Active Traders**

```
Use Hybrid:
- TradingView for advanced analysis
- MT5 for execution
- Best of both worlds
```

### **For Analysts**

```
Use TradingView Only:
- Focus on analysis without execution pressure
- Explore all markets
- Develop trading strategies
```

---

**Data Providers Guide v1.0.0** • April 25, 2026
