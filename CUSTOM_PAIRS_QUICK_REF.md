# Quick Reference: Custom Pairs

## In 30 Seconds

```bash
$ python main.py
Select option (1-5): 3
Enter pair symbol: BTCUSD
Select asset class (1-5): 2
Accept defaults or customize parameters
Trade begins ✓
```

---

## Main Menu Options

| Option | Use Case |
|--------|----------|
| 1 | Browse & select from predefined pairs (20+) |
| 2 | Mix multiple pairs (predefined + custom) |
| **3** | **Enter any custom pair symbol** |
| 4 | View all available pairs |
| 5 | Exit |

---

## Symbol Requirements

```
Valid:   EURUSD, BTCUSD, SOLANA, CUSTOMUSD
Invalid: EUR (too short), 123USD (has numbers), EUR@USD (special char)

Rules:
✓ 3-10 characters
✓ Letters only (A-Z)
✓ Auto-converted to UPPERCASE
```

---

## Asset Classes

```
1. FOREX          → EURUSD, GBPUSD, USDJPY
2. CRYPTO         → BTCUSD, ETHUSD, SOLANA
3. COMMODITIES    → XAUUSD, WTIUSD, XAGUSD
4. INDICES        → SPX500, DAX40, FTSE100
5. STOCKS         → AAPL, MSFT, TSLA, GOOGL
```

---

## Default Parameters

| Parameter | Default | Range |
|-----------|---------|-------|
| Pip value | 0.0001 | 0.0001 - 1.0 |
| Min lot | 0.01 | 0.001 - 100.0 |
| Max lot | 100.0 | 0.01 - 10000.0 |

---

## Common Pairs to Try

### Forex
```
EURUSD, GBPUSD, USDJPY, AUDUSD, USDBRL, NZDUSD
```

### Crypto
```
BTCUSD, ETHUSD, SOLANA, ADAUSD, XRPUSD, DOGEUSD
```

### Commodities
```
XAUUSD (Gold), WTIUSD (Oil), XAGUSD (Silver)
```

### Indices
```
SPX500 (S&P 500), DAX40 (German), FTSE100 (UK)
```

### Stocks
```
AAPL, MSFT, TSLA, GOOGL, AMZN, META, NVDA
```

---

## Workflow: Custom Pair → Trading

```
Enter Symbol (e.g., BTCUSD)
        ↓
Select Asset Class
        ↓
Set Parameters (optional)
        ↓
Register to System
        ↓
PHASE 1: Trend-Master analyzes BTCUSD
        ↓
PHASE 2: Analyse-Master detects patterns
        ↓
PHASE 3: Trader-Master executes trade
        ↓
Monitor P&L
```

---

## Troubleshooting

### "Symbol must be 3-10 characters"
```
Too short: EU, EUR
Too long:  EURUSDGBPJPY
Correct:   EURUSD, SOLANA
```

### "Symbol must contain only letters"
```
Invalid: EUR123, EUR_USD, EUR-USD
Valid:   EURUSD, CUSTOMUSD, SOLANA
```

### "Trade fails: Pair not found"
```
Check: Does the pair exist in your MT5 terminal?
Action: Verify symbol name matches broker exactly
```

---

## Risk Management (Always Enforced)

- Max 2% risk per trade
- Max 3 concurrent trades
- Max 5% daily drawdown
- Min 75% confidence required
- Min 1:2 risk/reward ratio

---

## Example: Adding SOLANA

```
Step 1: python main.py
Step 2: Select option 3
Step 3: Enter: SOLANA
Step 4: Select: 2 (CRYPTO)
Step 5: Pip value: 0.01 [or press Enter]
Step 6: Min lot: 0.001 [or press Enter]
Step 7: Max lot: 10.0 [or press Enter]
Step 8: [OK] Ready to trade SOLANA!
```

---

**More Details:** See `CUSTOM_PAIRS_GUIDE.md`
