# Custom Trading Pairs - User Entry Guide

## Overview

Users can now enter **ANY trading pair symbol** directly into the system. The platform supports:

- **Forex Pairs**: EURUSD, USDBRL, GBPJPY, etc.
- **Cryptocurrencies**: BTCUSD, ETHUSD, SOLANA, etc.
- **Commodities**: XAUUSD (Gold), WTIUSD (Oil), etc.
- **Indices**: SPX500, DAX40, FTSE100, etc.
- **Stocks**: Any ticker symbol (AAPL, MSFT, TSLA, etc.)

---

## How to Use Custom Pairs

### Method 1: Interactive Selection at Startup

When you start the trading agent:

```bash
python main.py
```

**Step 1:** Select "Enter Custom Pair Symbol" from the menu
```
[MENU] Trading Setup
────────────────────────────────────────────────────────────────
  1. Trade Single Pair (from registry)
  2. Trade Multiple Pairs
  3. Enter Custom Pair Symbol                    ← Choose this
  4. View All Available Pairs
  5. Exit
```

**Step 2:** Enter pair details
```
[CUSTOM] Enter Trading Pair Details
────────────────────────────────────────────────────────────────
Enter pair symbol (e.g., EURUSD, BTCUSD, CUSTOMUSD): SOLANA
```

**Step 3:** Select asset class
```
[ASSET] Select Asset Class for this pair:
  1. FOREX
  2. CRYPTO                                    ← For SOLANA
  3. COMMODITIES
  4. INDICES
  5. STOCKS

Enter asset class number (1-5): 2
```

**Step 4:** Set trading parameters (optional)
```
Enter pip value (default 0.0001): [Press Enter for default]
Enter minimum lot size (default 0.01): [Press Enter for default]
Enter maximum lot size (default 100.0): [Press Enter for default]

[OK] Registered custom pair: SOLANA
```

### Method 2: Multi-Pair with Custom Entries

When adding multiple pairs:

```
[OPTIONS] How to add pair:
  1. Select from registry
  2. Enter custom pair symbol                  ← Choose this

Choose (1-2): 2
```

Then follow the same steps as Method 1.

### Method 3: Programmatic Registration

In your Python code:

```python
from config.trading_pairs_config import pairs_registry, AssetClass

# Register a custom pair
custom_pair = pairs_registry.register_custom_pair(
    symbol="SOLANA",
    asset_class=AssetClass.CRYPTO,
    pip_value=0.01,
    min_lot_size=0.1,
    max_lot_size=100.0,
    description="Solana cryptocurrency"
)

# Use the pair for trading
pairs_registry.set_active_pairs(["SOLANA"])
```

---

## Symbol Validation Rules

Symbols must follow these rules:

| Rule | Requirement |
|------|-------------|
| Length | 3-10 characters |
| Characters | Letters only (A-Z) |
| Format | Case-insensitive (auto-converted to uppercase) |
| Examples | EURUSD ✓, SOLANA ✓, CUSTOMUSD ✓ |

**Invalid symbols:**
- Too short: `EUR` (needs at least 3 chars) ✗
- Too long: `EURUSDGBPJPY` (max 10 chars) ✗
- Contains numbers: `123USD` ✗
- Contains special chars: `EUR@USD` ✗
- Empty: `` ✗

---

## Asset Classes

### 1. FOREX (Foreign Exchange)
- **Symbol examples:** EURUSD, GBPUSD, USDJPY, AUDUSD
- **Pip value:** Usually 0.0001 (0.01 for yen pairs)
- **Lot sizes:** 0.01 - 100.0
- **Use case:** Trading currency pairs

### 2. CRYPTO (Cryptocurrencies)
- **Symbol examples:** BTCUSD, ETHUSD, SOLANA, ADAUSD
- **Pip value:** Typically 0.01 or higher
- **Lot sizes:** 0.001 - 100.0
- **Use case:** Trading crypto against USD

### 3. COMMODITIES (Metals, Oil, Energy)
- **Symbol examples:** XAUUSD (Gold), WTIUSD (Oil), XAGUSD (Silver)
- **Pip value:** 0.01 - 0.1
- **Lot sizes:** 0.01 - 100.0
- **Use case:** Commodity trading

### 4. INDICES (Stock Market Indices)
- **Symbol examples:** SPX500, DAX40, FTSE100, NQ100
- **Pip value:** 0.1 - 1.0
- **Lot sizes:** 0.01 - 100.0
- **Use case:** Trading stock index futures

### 5. STOCKS (Individual Equities)
- **Symbol examples:** AAPL, MSFT, TSLA, GOOGL
- **Pip value:** 0.01 - 0.1
- **Lot sizes:** 0.1 - 1000.0
- **Use case:** Trading individual company stocks

---

## Setting Custom Parameters

When registering a custom pair, you can set:

### Pip Value
The smallest price movement for the pair.
- **Forex:** 0.0001 (standard), 0.01 (yen pairs)
- **Crypto:** 0.01 or higher
- **Commodities:** 0.01 - 0.1
- **Indices:** 0.1 - 1.0
- **Stocks:** 0.01 - 0.1

### Minimum Lot Size
The smallest position you can open.
- **Example:** 0.01 = 1% of standard lot
- **Typical range:** 0.001 - 1.0

### Maximum Lot Size
The largest position you can open per trade.
- **Example:** 100.0 = 100 standard lots
- **Risk management:** Usually capped at account size limits

---

## Full Example Workflow

### Scenario: Trade Bitcoin (BTCUSD)

```
Step 1: Start the system
$ python main.py

Step 2: Select option 3 (Enter Custom Pair)
Select option (1-5): 3

Step 3: Enter symbol
Enter pair symbol (e.g., EURUSD, BTCUSD, CUSTOMUSD): BTCUSD

Step 4: Select asset class
[ASSET] Select Asset Class for this pair:
  1. FOREX
  2. CRYPTO
  3. COMMODITIES
  4. INDICES
  5. STOCKS
Enter asset class number (1-5): 2

Step 5: Accept defaults or customize
Enter pip value (default 0.0001): 0.01
Enter minimum lot size (default 0.01): 0.001
Enter maximum lot size (default 100.0): 10.0

[OK] Registered custom pair: BTCUSD

Step 6: System now trades BTCUSD with your settings
[LOOP] Cycle #1 — BTCUSD
[DATA] Fetching market data for BTCUSD...
[DATA] ✓ D1: 100 candles
[DATA] ✓ H4: 100 candles
[DATA] ✓ H1: 50 candles
...
```

---

## Integration with Workflow

Custom pairs work seamlessly with the strict three-phase workflow:

```
PHASE 1: Trend-Master
├─ Analyzes custom pair (BTCUSD)
├─ Identifies trend bias (BULLISH/BEARISH)
└─ Generates TrendReport

PHASE 2: Analyse-Master
├─ Receives trend from Phase 1
├─ Detects ICT patterns
├─ Validates entry signal
└─ Generates TradeSignal (if conditions met)

PHASE 3: Trader-Master
├─ Receives signal from Phase 2
├─ Validates risk management
├─ Executes trade on custom pair
└─ Logs execution record
```

---

## Limitations & Guardrails

### Data Availability
- Custom pairs must be available on your MT5 broker
- If pair not found on broker: Trade will fail during data fetch
- Check MT5 terminal to verify pair is tradeable

### Risk Management
- All custom pairs subject to same risk rules:
  - Max 2% risk per trade
  - Max 3 concurrent trades
  - Max 5% daily drawdown
- Pip value affects position sizing calculations

### Validation
- Symbol validation happens at entry (3-10 chars, letters only)
- Asset class must be one of 5 supported classes
- Pip value must be positive number
- Lot sizes must satisfy: min_lot_size ≤ max_lot_size

---

## Troubleshooting

### "Symbol must contain only letters"
**Problem:** You entered numbers or special characters
**Solution:** Use only alphabetic characters (A-Z)
```
Invalid: EUR123, EUR@USD, EUR-USD
Valid:   EURUSD, EURUSDX, CUSTOMUSD
```

### "Symbol must be 3-10 characters"
**Problem:** Symbol too short or too long
**Solution:** Use 3-10 character symbols
```
Invalid: EU (2 chars)
Invalid: EURUSDGBPJPY (12 chars)
Valid:   EURUSD, SOLANA, CUSTOMUSD
```

### "Invalid asset class"
**Problem:** Asset class number not in range 1-5
**Solution:** Enter number between 1 and 5
```
Options:
1. FOREX
2. CRYPTO
3. COMMODITIES
4. INDICES
5. STOCKS
```

### "Invalid input" on pip value
**Problem:** Entered non-numeric value
**Solution:** Enter decimal number (e.g., 0.0001, 0.01, 1.0)

### Trade fails: "Pair not found on broker"
**Problem:** Custom pair doesn't exist in MT5 terminal
**Solution:** 
1. Check MT5 terminal has the pair
2. Verify broker supports that pair
3. Check pair name matches exactly (case-insensitive, but must exist)
4. Contact broker if pair should be available

---

## Best Practices

### 1. Verify Pair Names Match Broker
Different brokers may use slightly different naming:
```
Broker A: EURUSD
Broker B: EUR/USD or Eurusd
Action: Check your MT5 terminal for exact symbol name
```

### 2. Set Realistic Lot Sizes
```
Good:  min=0.01, max=100.0 (safe range)
Bad:   min=100.0, max=0.01 (min > max!)
Bad:   min=1000.0, max=10000.0 (too large for risk management)
```

### 3. Use Correct Pip Values
```
Correct pip values:
- Most Forex: 0.0001
- Yen pairs: 0.01
- Crypto: 0.01
- Oil: 0.01
- Stocks: 0.01
```

### 4. Test with Small Position Sizes
```python
# Start with demo account
# Use minimum lot sizes
# Verify workflow executes correctly
# Only then increase position size
```

---

## Production Checklist

- [ ] Symbol is valid (3-10 letters)
- [ ] Symbol exists in your MT5 broker
- [ ] Asset class matches the pair type
- [ ] Pip value matches broker specifications
- [ ] Lot sizes are realistic (min < max)
- [ ] Tested on demo account first
- [ ] Risk management settings reviewed
- [ ] MT5 connection verified
- [ ] Ready to trade live

---

## Support

If custom pair registration fails:

1. **Check symbol:** Must be 3-10 letters only
2. **Check broker:** Verify pair exists in MT5 terminal
3. **Check parameters:** Verify pip value and lot sizes make sense
4. **Check connection:** Ensure MT5 is connected before trading
5. **Check logs:** Review system logs for detailed errors

---

**Version:** 2.1  
**Status:** Production Ready  
**Date:** May 4, 2026
