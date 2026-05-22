# Agent API Reference

## Trend-Master Agent

### Method: `analyze(market_data)`

**Purpose**: Analyze market data across multiple timeframes to identify trends

**Parameters:**
- `market_data` (Dict): OHLC data organized by timeframe
  - `market_data['daily']`: Daily candle data
  - `market_data['4h']`: 4-hour candle data
  - `market_data['1h']`: 1-hour candle data

**Returns:**
- `TrendReport` object containing:
  - `bias` (str): "BULLISH", "BEARISH", or "NEUTRAL"
  - `confidence` (float): 0-100%
  - `support_resistance` (Dict): Support and resistance levels
  - `swing_structure` (Dict): Swing high/low analysis
  - `liquidity_levels` (List): Institutional liquidity zones
  - `risk_level` (str): "LOW", "MEDIUM", "HIGH"

**Example:**
```python
trend_report = await trend_master.analyze(market_data)
print(f"Trend: {trend_report.bias} (Confidence: {trend_report.confidence}%)")
```

---

## Analyse-Master Agent

### Method: `analyze(trend_report)`

**Purpose**: Generate trade signals using ICT methodology

**Parameters:**
- `trend_report` (Dict): Output from Trend-Master analysis

**Returns:**
- `TradeSignal` object if all ICT elements confirmed, else None
- `TradeSignal` contains:
  - `entry_level` (float): Entry price
  - `stop_loss` (float): Stop loss price
  - `take_profit_1, 2, 3` (float): Three profit targets
  - `risk_reward_ratio` (float): Calculated R:R ratio
  - `confidence` (float): 0-100% signal confidence
  - `pattern_elements` (Dict): Confirmation of ICT elements
  - `kill_zone_start/end` (datetime): Valid entry window

**Example:**
```python
trade_signal = await analyse_master.analyze(trend_report.to_dict())
if trade_signal and trade_signal.confidence >= 75:
    print(f"Entry: {trade_signal.entry_level}, SL: {trade_signal.stop_loss}")
```

---

## Trader-Master Agent

### Method: `analyze(trade_signal)`

**Purpose**: Execute trade based on validated signal

**Parameters:**
- `trade_signal` (Dict): Output from Analyse-Master analysis

**Returns:**
- `ExecutionRecord` if trade executed, else None
- `ExecutionRecord` contains:
  - `entry_price` (float): Actual entry price
  - `entry_time` (datetime): Execution time
  - `position_size` (float): Trade lot size
  - `status` (str): "PENDING", "OPEN", "CLOSED"
  - `exit_price` (float, optional): Exit price if closed
  - `exit_reason` (str, optional): "TP_HIT", "SL_HIT", "MANUAL_CLOSE"
  - `pnl` (float, optional): Profit/Loss in currency
  - `slippage` (float, optional): Execution slippage in pips

**Example:**
```python
execution = await trader_master.analyze(trade_signal.to_dict())
if execution:
    print(f"Trade Executed: {execution.status}")
    print(f"Entry: {execution.entry_price}, Position: {execution.position_size}")
```

---

## Data Models

### TrendReport
```python
{
    "bias": "BULLISH",                           # Direction
    "confidence": 82.5,                          # Score 0-100
    "timeframes_analyzed": ["D", "4H", "1H"],   # Analyzed TF
    "support_resistance": {
        "support_levels": [1.0450, 1.0400],
        "resistance_levels": [1.0600, 1.0650]
    },
    "swing_structure": {
        "recent_higher_lows": True,
        "recent_lower_highs": False
    },
    "liquidity_levels": [1.0500, 1.0600],       # Zone concentrations
    "risk_level": "MEDIUM",
    "timestamp": "2024-04-22T10:30:00"
}
```

### TradeSignal
```python
{
    "entry_level": 1.0530,
    "stop_loss": 1.0480,
    "take_profit_1": 1.0580,
    "take_profit_2": 1.0630,
    "take_profit_3": 1.0680,
    "risk_reward_ratio": 2.5,
    "confidence": 82.0,
    "pattern_elements": {
        "liquidity_sweep": True,
        "break_of_structure": True,
        "imbalance": True,
        "pullback": True
    },
    "kill_zone_start": "2024-04-22T10:35:00",
    "kill_zone_end": "2024-04-22T11:05:00"
}
```

### ExecutionRecord
```python
{
    "signal_id": "SIG_001",
    "entry_price": 1.0530,
    "entry_time": "2024-04-22T10:40:00",
    "position_size": 0.5,
    "stop_loss": 1.0480,
    "take_profit_1": 1.0580,
    "take_profit_2": 1.0630,
    "take_profit_3": 1.0680,
    "status": "OPEN",
    "exit_price": None,
    "exit_time": None,
    "exit_reason": None,
    "pnl": None,
    "slippage": None
}
```

---

## Error Handling

All agents return `None` if analysis fails or conditions not met:

```python
try:
    signal = await analyse_master.analyze(trend_report.to_dict())
    if signal is None:
        print("No valid signal generated")
except Exception as e:
    logger.error(f"Analysis error: {str(e)}")
```

---

## Validation Methods

### Validate Trend Report
```python
required_keys = ["bias", "confidence", "support_resistance"]
if await trend_master.validate_input(report, required_keys):
    print("Trend report is valid")
```

### Validate Signal Data
```python
from utils.validation import validate_signal_data

if validate_signal_data(signal):
    print("Signal data is valid")
```
