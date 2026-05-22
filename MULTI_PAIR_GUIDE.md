# Multi-Pair Trading Agent with Strict Workflow Enforcement

## System Overview

The enhanced TechnobizTrader system now supports:

✓ **Any trading pair** — Forex, Crypto, Commodities, Indices, Stocks  
✓ **Dynamic pair selection** — Interactive user interface  
✓ **Multi-pair trading** — Multiple pairs in sequence (round-robin)  
✓ **Strict workflow enforcement** — Trend → Analyse → Trade (no skipping)  
✓ **Audit trail** — Complete workflow phase tracking

---

## Architecture

```
User Input
    ↓
Interactive Trading Manager (pair selection)
    ↓
Trading Loop (Round-Robin: Pair 1 → Pair 2 → Pair 1...)
    ↓
Workflow Orchestrator (Phase 1/2/3 enforcement)
    ├─ PHASE 1: Trend-Master (Market Analysis)
    │  └─ Input: OHLC data (Daily/4H/1H)
    │  └─ Output: TrendReport (bias, confidence, S/R)
    │
    ├─ PHASE 2: Analyse-Master (ICT Pattern Detection)
    │  └─ Input: TrendReport + 1H candles
    │  └─ Output: TradeSignal (all 4 ICT elements)
    │
    └─ PHASE 3: Trader-Master (Trade Execution)
       └─ Input: TradeSignal
       └─ Output: ExecutionRecord (or rejection)
       └─ Risk Management: Confidence ≥75%, R:R ≥1:2, Risk ≤2%
```

---

## New Components

### 1. Trading Pairs Registry (`config/trading_pairs_config.py`)

Supports unlimited trading pairs with predefined registry:

```python
# MAJOR FOREX PAIRS
EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, NZDUSD

# CROSS PAIRS
EURGBP, EURJPY, GBPJPY, AUDJPY

# COMMODITIES
XAUUSD (Gold), WTIUSD (WTI Oil), BRENTUSD (Brent Oil), XAGUSD (Silver)

# CRYPTOCURRENCIES
BTCUSD (Bitcoin), ETHUSD (Ethereum)

# INDICES
SPX500 (S&P 500), DAX40 (German DAX), FTSE100 (UK FTSE)
```

**Adding Custom Pairs:**

```python
from config.trading_pairs_config import pairs_registry, AssetClass

# Register a custom pair
pairs_registry.register_custom_pair(
    symbol="CADUSD",
    asset_class=AssetClass.FOREX,
    pip_value=0.0001,
    min_lot_size=0.01,
    max_lot_size=100.0,
    description="Canadian Dollar vs US Dollar"
)
```

### 2. Workflow Orchestrator (`agents/workflow_orchestrator.py`)

Enforces strict three-phase workflow:

```python
from agents.workflow_orchestrator import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()

# Start a trading cycle
state = orchestrator.start_cycle("EURUSD")

# Phase 1: Trend Analysis
orchestrator.begin_trend_analysis()
trend_report = await trend_master.analyze(market_data)
orchestrator.complete_trend_analysis(trend_report.to_dict())

# Phase 2: Signal Generation
orchestrator.begin_signal_generation()
trade_signal = await analyse_master.analyze(...)
orchestrator.complete_signal_generation(trade_signal.to_dict())

# Phase 3: Trade Execution
orchestrator.begin_trade_execution()
execution = await trader_master.analyze(...)
orchestrator.complete_trade_execution(execution.to_dict() if execution else None)
```

**Workflow Validation:**
- Each phase must complete before the next begins
- All required outputs must be present
- Phase transitions are validated
- Complete audit trail maintained

### 3. Interactive Trading Manager (`utils/interactive_trading_manager.py`)

User-friendly interface for pair selection:

```python
from utils.interactive_trading_manager import InteractiveTradingManager

manager = InteractiveTradingManager()

# Display welcome and quick start
manager.display_welcome()
manager.display_quick_start()

# Interactive selection menu
if manager.display_selection_menu():
    pairs = manager.get_selected_pairs()
    manager.display_selection_summary()
```

**Interactive Features:**
- Select single or multiple pairs
- Browse pairs by asset class
- View all available pairs
- Input validation
- Selection confirmation

---

## Running the System

### Basic Usage (Single Pair)

```bash
cd c:\Users\erick\Downloads\Trading_Agent

# Activate virtual environment
venv\Scripts\activate

# Run enhanced main (interactive)
python main_enhanced.py
```

**Interactive Flow:**
1. Welcome screen
2. Quick start guide
3. Asset class selection
4. Pair selection
5. Single or multiple pairs
6. Trading begins

### Programmatic Usage (Multiple Pairs)

```python
import asyncio
from agents.workflow_orchestrator import WorkflowOrchestrator
from agents.workflow import TradingWorkflow
from config.trading_pairs_config import pairs_registry

async def run():
    # Setup
    orchestrator = WorkflowOrchestrator()
    workflow = TradingWorkflow(mt5_provider=provider)
    
    # Select pairs
    pairs_registry.set_active_pairs(['EURUSD', 'GBPUSD', 'AUDUSD'])
    pairs = pairs_registry.get_active_pairs()
    
    # Trade multiple pairs
    for pair in pairs:
        state = orchestrator.start_cycle(pair.symbol)
        # ... execute trading cycle ...
    
    # Get statistics
    stats = orchestrator.get_performance_stats()
    print(f"Cycles: {stats['total_cycles']}")
    print(f"Signals: {stats['successful_signals']}")
    print(f"Trades: {stats['executed_trades']}")

asyncio.run(run())
```

---

## Workflow Enforcement Rules

### PHASE 1: Trend-Master (MANDATORY)

**Input Requirements:**
- OHLC data for 3 timeframes (Daily, 4H, 1H)
- Minimum 20 candles per timeframe

**Output Requirements:**
- TrendReport with:
  - `bias`: BULLISH, BEARISH, or NEUTRAL
  - `confidence`: 0-100%
  - `support_resistance`: Levels with 2+ tests
  - `swing_structure`: HH/HL or LL/LH pattern
  - `liquidity_levels`: Institutional zones

**Rejection Criteria:**
- ✗ Missing any timeframe
- ✗ Insufficient candles (<20)
- ✗ Extreme volatility (ATR > 3-month avg × 1.5)
- ✗ No clear market structure

### PHASE 2: Analyse-Master (CONDITIONAL)

**Input Requirements (from Phase 1):**
- TrendReport with directional bias (NOT NEUTRAL)
- Current 1H candles

**Output Requirements (if triggered):**
- TradeSignal with ALL 4 ICT elements:
  1. ✓ Liquidity Sweep
  2. ✓ Break of Structure
  3. ✓ Order Block/Imbalance
  4. ✓ Pullback Entry
- `confidence`: 0-100%
- `entry_level`: Exact entry price
- `stop_loss`: Hard stop beyond OB
- `take_profit_1/2/3`: Tiered exits
- `risk_reward_ratio`: ≥1:2
- `kill_zone_start/end`: Entry window (15-30 min)

**Rejection Criteria:**
- ✗ NEUTRAL trend bias
- ✗ Missing any ICT element
- ✗ Confidence < 75%
- ✗ Risk/Reward < 1:2
- ✗ Outside kill zone window

### PHASE 3: Trader-Master (CONDITIONAL)

**Input Requirements (from Phase 2):**
- TradeSignal with all fields
- Current account balance and open positions

**Pre-Execution Validation:**
- ✓ Confidence ≥ 75%
- ✓ Risk/Reward ≥ 1:2
- ✓ Position size ≤ 2% account risk
- ✓ Open trades < 3
- ✓ Daily drawdown < 5%
- ✓ Kill zone still valid

**Output (if executed):**
- ExecutionRecord with:
  - `signal_id`: Linked to Phase 2 signal
  - `mt5_ticket`: Order confirmation
  - `entry_price`: Actual filled price
  - `position_size`: Lot size
  - `status`: PENDING/OPEN/CLOSED

**Rejection Scenarios:**
- ✗ Confidence < 75%
- ✗ Risk/Reward < 1:2
- ✗ Position risk > 2%
- ✗ Max concurrent trades reached
- ✗ Daily drawdown exceeded
- ✗ MT5 connection issue

---

## Configuration

### Environment Variables (`.env`)

```env
# ─── MULTI-PAIR SELECTION ───────────────────────────────────
# Leave empty for interactive selection, or specify pairs
TRADING_PAIRS=EURUSD,GBPUSD,AUDUSD
# For single pair:
# TRADING_PAIRS=EURUSD

# ─── TRADING INTERVAL ────────────────────────────────────────
TRADING_INTERVAL_MINUTES=15

# ─── MT5 SETTINGS ────────────────────────────────────────────
MT5_ENABLED=true
MT5_ACCOUNT=your_account
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# ─── RISK MANAGEMENT ─────────────────────────────────────────
RISK_PER_TRADE=0.02  # 2% per trade
MAX_CONCURRENT_TRADES=3
MAX_DAILY_DRAWDOWN=0.05  # 5%

# ─── DEBUG ──────────────────────────────────────────────────
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### Pair Configuration (Python)

```python
# Option 1: Interactive selection (recommended for testing)
python main_enhanced.py
# Follow interactive prompts

# Option 2: Programmatic selection
from config.trading_pairs_config import pairs_registry, AssetClass

# Trade all forex pairs
forex_pairs = pairs_registry.get_pairs_by_asset_class(AssetClass.FOREX)

# Trade specific pairs
pairs_registry.set_active_pairs(['EURUSD', 'GBPUSD', 'USDJPY'])
selected = pairs_registry.get_active_pairs()
```

---

## Execution Examples

### Example 1: Single EURUSD Trade

```
[ORCHESTRATOR] STARTING NEW TRADING CYCLE
[ORCHESTRATOR] Cycle ID: a1b2c3d4 | Symbol: EURUSD

[ORCHESTRATOR] ┌─ PHASE 1: TREND-MASTER ANALYSIS
[ORCHESTRATOR] │  Analyzing market structure across timeframes (Daily/4H/1H)
[ORCHESTRATOR] │  Expected output: TrendReport with bias & support/resistance
[DATA] Fetching market data for EURUSD...
[DATA] ✓ D1: 20 candles
[DATA] ✓ H4: 25 candles
[DATA] ✓ H1: 50 candles
[CYCLE] Trend: BULLISH (Confidence: 82%)
[ORCHESTRATOR] └─ PHASE 1 COMPLETE

[ORCHESTRATOR] ┌─ PHASE 2: ANALYSE-MASTER - ICT PATTERN DETECTION
[ORCHESTRATOR] │  Input: TrendReport (bias=BULLISH)
[ORCHESTRATOR] │  Detecting: Liquidity Sweep, BoS, Order Block, Pullback
[ORCHESTRATOR] │  Expected output: TradeSignal with all 4 ICT elements
[CYCLE] Signal: BUY @ 1.0936 (Confidence: 90.2%)
[ORCHESTRATOR] └─ PHASE 2 COMPLETE

[ORCHESTRATOR] ┌─ PHASE 3: TRADER-MASTER - TRADE EXECUTION
[ORCHESTRATOR] │  Input: TradeSignal (entry=1.0936)
[ORCHESTRATOR] │  Validating: Confidence ≥75%, R:R ≥1:2, Risk ≤2%
[ORCHESTRATOR] │  Expected output: ExecutionRecord or REJECTION
[CYCLE] Trade Executed: PENDING | Ticket: 123456789
[ORCHESTRATOR] └─ PHASE 3 COMPLETE

═══════════════════════════════════════════════════════════════
[ORCHESTRATOR] TRADING CYCLE COMPLETE
═══════════════════════════════════════════════════════════════
```

### Example 2: Multi-Pair Round-Robin

```
[LOOP] Cycle #1 — EURUSD
  ✓ Trend: BULLISH (82%)
  ✓ Signal: BUY @ 1.0936
  ✓ Executed: Ticket 123456789

[LOOP] Cycle #2 — GBPUSD
  ✓ Trend: BEARISH (78%)
  ✗ No ICT signal (conditions not met)

[LOOP] Cycle #3 — AUDUSD
  ✓ Trend: BULLISH (75%)
  ✓ Signal: BUY @ 0.6850
  ✗ Rejected: Already 3 open trades

[LOOP] Performance — Cycles: 3, Signals: 2, Trades: 1
```

### Example 3: Rejected Trade (Risk Management)

```
[ORCHESTRATOR] ┌─ PHASE 2: ANALYSE-MASTER
[CYCLE] Signal: BUY @ 1.0950 (Confidence: 85%)

[ORCHESTRATOR] ┌─ PHASE 3: TRADER-MASTER
[VALIDATION] Confidence 85% ✓
[VALIDATION] Risk/Reward 2.5:1 ✓
[VALIDATION] Position Risk 1.8% ✓
[VALIDATION] Max Daily Drawdown Check: Current 4.8% < 5% ✓
[VALIDATION] All checks passed

[CYCLE] Trade Executed: PENDING | Ticket: 987654321
```

---

## Monitoring & Analytics

### Workflow Statistics

```python
stats = orchestrator.get_performance_stats()

{
    'total_cycles': 45,
    'successful_signals': 12,
    'executed_trades': 10,
    'rejected_trades': 2,
    'average_cycle_duration_seconds': 8.5,
}
```

### Workflow History

```python
history = orchestrator.get_workflow_history()

for workflow in history:
    print(f"Cycle: {workflow['cycle_id']}")
    print(f"  Symbol: {workflow['symbol']}")
    print(f"  Duration: {workflow['duration_seconds']}s")
    print(f"  Trend: {workflow['trend_report']}")
    print(f"  Signal: {workflow['trade_signal']}")
    print(f"  Trade: {workflow['execution_record']}")
```

---

## Troubleshooting

### Issue: "Cannot start signal generation: no trend report"

**Cause:** Trend-Master failed or returned None

**Solution:**
1. Check market data is fetching correctly
2. Verify sufficient candles available
3. Check timeframe data alignment

### Issue: "Invalid phase transition"

**Cause:** Attempting to skip a phase

**Solution:**
- Each phase MUST be completed in order
- Cannot jump from Phase 1 to Phase 3
- Check workflow state with `orchestrator.current_workflow`

### Issue: "Multi-pair trading stalls"

**Cause:** Previous pair cycle not completed

**Solution:**
1. Verify each cycle completes with `finalize()`
2. Check error logs for exceptions
3. Increase `TRADING_INTERVAL_MINUTES` if system overloaded

---

## Best Practices

✓ **Single Pair First** — Test with EURUSD before multi-pair  
✓ **Monitor Workflow** — Check logs for phase transitions  
✓ **Validate Data** — Ensure all market data before trading  
✓ **Risk Management** — Respect 2% per trade limit  
✓ **Testing** — Use demo account before live  
✓ **Gradual Rollout** — Start 1 pair → 2 pairs → 3+ pairs  
✓ **Automation** — Set `TRADING_PAIRS` in .env after testing  

---

**Document Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** May 3, 2026
