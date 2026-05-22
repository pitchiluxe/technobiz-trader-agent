# TechnobizTrader - AI Coding Agent Instructions

**Project:** Multi-agent AI trading system using ICT (Inner Circle Trading) methodology  
**Language:** Python 3.10+  
**Framework:** Microsoft Agent Framework v1.0.0rc6 with Azure AI Foundry  
**Status:** Blueprint implementation phase

---

## Quick Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.template .env

# Run
python main.py

# Test
pytest tests/ -v

# Development
black .                    # Format code
pytest tests/ --cov       # With coverage
DEBUG=True python main.py  # Debug mode
```

---

## Project Architecture

### Three-Agent System (Sequential Pipeline)

```
Market Data
    ↓
[TREND-MASTER] - Analyze multi-timeframe trends
    ↓ TrendReport
[ANALYSE-MASTER] - Detect ICT patterns → Generate signals
    ↓ TradeSignal
[TRADER-MASTER] - Execute trades with risk management
    ↓ ExecutionRecord
Database
```

### Core Concept: ICT Methodology

**ICT Elements** (all 4 required for signal):
1. **Liquidity Sweep** - Price breaks swing levels to capture stops
2. **Break of Structure (BoS)** - Price breaks previous swing pattern
3. **Imbalance/Order Block** - Unfilled gap or institutional entry zone
4. **Pullback Entry** - Re-entry into order block during "kill zone" (15-30 min window)

---

## Agent Responsibilities

### 1. **Trend-Master** (`agents/trend_master/trend_master.py`)

**Input:** Market OHLC data (Daily, 4H, 1H minimum)  
**Output:** `TrendReport` (bias, confidence, support/resistance, liquidity levels)

**Key Rules:**
- Analyze ≥3 timeframes minimum
- S/R levels must have ≥2 historical tests
- Confidence 0-100%
- Update every 4 hours

**Output Structure:**
```python
TrendReport(
    bias: str,                      # "BULLISH", "BEARISH", "NEUTRAL"
    confidence: float,              # 0-100%
    support_resistance: Dict,       # Level zones
    liquidity_levels: List[float]   # Institutional concentration zones
)
```

### 2. **Analyse-Master** (`agents/analyse_master/analyse_master.py`)

**Input:** TrendReport from Trend-Master  
**Output:** `TradeSignal` if all ICT elements confirmed, else None

**Key Rules:**
- NO signal without all 4 ICT elements
- Minimum 1:2 Risk/Reward ratio
- Confidence ≥75% required for execution
- Signal expires after 30 minutes
- 2-timeframe confluence minimum

**Output Structure:**
```python
TradeSignal(
    entry_level: float,
    stop_loss: float,
    take_profit_1/2/3: float,
    confidence: float,              # 0-100%
    pattern_elements: Dict,         # ICT element confirmation
    kill_zone_start/end: datetime   # Valid entry window
)
```

### 3. **Trader-Master** (`agents/trader_master/trader_master.py`)

**Input:** TradeSignal from Analyse-Master  
**Output:** `ExecutionRecord` (pending/open/closed trade)

**Key Rules:**
- Only execute if signal confidence ≥75%
- Max 3 concurrent trades
- 2% max risk per trade
- Hard stop loss (non-negotiable)
- Pause if daily drawdown >5%

**Output Structure:**
```python
ExecutionRecord(
    entry_price: float,
    position_size: float,
    status: str,                    # "PENDING", "OPEN", "CLOSED"
    exit_price: float,              # Optional
    exit_reason: str,               # "TP_HIT", "SL_HIT", etc.
    pnl: float                      # Profit/loss
)
```

---

## Key Files & Patterns

### Agents (`agents/`)

| File | Purpose |
|------|---------|
| `base_agent.py` | Abstract base with common logging, validation |
| `trend_master/trend_master.py` | Trend analysis - extends BaseAgent |
| `analyse_master/analyse_master.py` | Signal generation - extends BaseAgent |
| `trader_master/trader_master.py` | Trade execution - extends BaseAgent |
| `workflow.py` | **Orchestrates all 3 agents** (execute_trading_cycle) |

### Configuration (`config/`)

| File | Purpose |
|------|---------|
| `settings.py` | Env-based config (Settings class) |
| `api_config.py` | Data provider configs (MT5, Alpaca) |
| `trading_params.py` | Enums and constants (Timeframe, TradeStatus, etc.) |

### Market Data (`market_data/`)

| File | Purpose |
|------|---------|
| `data_provider.py` | Abstract interface (OHLCData, Candle, DataProvider) |
| `mt5_provider.py` | MetaTrader 5 implementation |

### Database (`database/`)

| File | Purpose |
|------|---------|
| `db_manager.py` | SQLAlchemy session management |
| `models.py` | ORM models (TrendAnalysis, TradeSignal, TradeExecution, Performance) |

### Utilities (`utils/`)

| File | Purpose |
|------|---------|
| `logger.py` | Rotating file logging setup |
| `validation.py` | Input validation helpers |
| `performance_tracker.py` | Trade metrics calculation |

### Entry Point

- `main.py` - Start application (asyncio.run on TradingWorkflow)

---

## Important Conventions

### 1. **Async Pattern**
All agents use `async def analyze()`. Workflow uses `asyncio.run()` and `await`.

```python
async def analyze(self, data: Dict[str, Any]) -> Optional[SomeReport]:
    # Validation first
    if not await self.validate_input(data, required_keys):
        return None
    # Analysis logic
    # Return result or None
```

### 2. **Logging**
- Import: `import logging` then `logger = logging.getLogger(__name__)`
- Log levels: debug, info, warning, error
- Each agent logs with prefix: `[TREND-MASTER]`, `[ANALYSE-MASTER]`, etc.

### 3. **Data Models**
Each agent has corresponding `*Report` or `*Record` class (see workflow.py imports):
- Must have `to_dict()` method for transmission
- Immutable after creation (no setters)

### 4. **Error Handling**
- Return `None` if validation fails (not exceptions)
- Log warnings/errors before returning None
- Try-except in workflow orchestration

### 5. **Configuration**
- Use `from config.settings import settings` for env vars
- Use `from config.trading_params import TradingParams` for constants
- Never hardcode values

---

## Common Development Tasks

### Add a New Analysis Method to Trend-Master

1. Add logic in `trend_master.py` → `analyze()` method
2. Update `TrendReport` to include new fields if needed
3. Add test in `tests/test_trend_master.py`
4. Log progress with `self.logger.info()`

### Add Risk Management Rule

1. Add threshold to `config/trading_params.py`
2. Add check in `trader_master.py` → `analyze()` before execution
3. Log rejection reason before returning None
4. Update guardrails in [claude.md](./claude.md)

### Add Market Data Provider

1. Create `providers/your_provider.py` inheriting from `DataProvider`
2. Implement `get_candles()`, `get_current_price()`, connection methods
3. Update `config/api_config.py` with config
4. Add tests in `tests/`

### Test a Single Agent

```bash
# Example: Test Trend-Master
pytest tests/test_trend_master.py -v -s
```

### Debug a Trading Cycle

```bash
DEBUG=True LOG_LEVEL=DEBUG python main.py
# Logs show all agent decisions with [STEP 1], [STEP 2], [STEP 3] markers
```

---

## Code Style & Quality

- **Format:** `black` (100 char line length)
- **Import Sort:** `isort` (black profile)
- **Lint:** `pylint` (check with `pylint agents/ config/`)
- **Type Hints:** Required in all function signatures
- **Docstrings:** Numpy-style for classes and methods

---

## Testing

### Test Structure
```
tests/
  fixtures/
    sample_candles.py    # Test data generators
  integration/
    test_end_to_end.py   # Full workflow tests
  test_workflow.py       # Workflow unit tests
```

### Run Tests
```bash
pytest tests/ -v              # All tests
pytest tests/ -k keyword -v   # Filter by keyword
pytest tests/ --cov -v        # With coverage report
```

### Key Test Patterns
- Use `@pytest.mark.asyncio` for async tests
- Use fixtures from `tests/fixtures/` for sample data
- Mock market data, not real API calls

---

## Database & Persistence

### Models
Four main ORM models in `database/models.py`:
- `TrendAnalysis` - Trend analysis records
- `TradeSignalRecord` - Generated signals (not executed)
- `TradeExecution` - Actual executions with outcomes
- `PerformanceMetric` - Daily/weekly summaries

### Setup
```bash
python -c "from database.db_manager import db_manager; db_manager.create_tables()"
```

### Query Example
```python
from database.db_manager import db_manager
session = db_manager.get_session()
trades = session.query(TradeExecution).filter_by(status="CLOSED").all()
session.close()
```

---

## Documentation

| File | Use For |
|------|---------|
| [claude.md](./claude.md) | Full blueprint (architecture, guardrails, KPIs) |
| [README.md](./README.md) | Quick start and overview |
| [docs/ICT_METHODOLOGY.md](./docs/ICT_METHODOLOGY.md) | ICT strategy reference |
| [docs/API_REFERENCE.md](./docs/API_REFERENCE.md) | Agent APIs and data models |
| [docs/SETUP_GUIDE.md](./docs/SETUP_GUIDE.md) | Detailed installation |
| [docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) | Common issues |

---

## Risk Management Guardrails

**Hard Constraints** (always enforced):
- ✓ 2% max risk per trade (position sizing)
- ✓ 1:2 minimum Risk/Reward ratio
- ✓ 3 concurrent trades maximum
- ✓ Hard stop loss (no exceptions)
- ✓ 5% daily drawdown → pause trading
- ✓ 75% confidence minimum for execution

**Pattern Validation:**
- All 4 ICT elements must be confirmed
- 2-timeframe confluence minimum
- Signal valid for max 30 minutes
- No trading during extreme volatility

See [claude.md](./claude.md) "Rules & Guardrails" section for complete list.

---

## Workflow Execution Flow

```python
TradingWorkflow.execute_trading_cycle(market_data)
  │
  ├─→ Trend-Master.analyze(market_data)
  │    Returns: TrendReport or None
  │    If None → Stop, return None
  │
  ├─→ Analyse-Master.analyze(trend_report.to_dict())
  │    Returns: TradeSignal or None
  │    If None → Stop, return None
  │
  ├─→ Trader-Master.analyze(trade_signal.to_dict())
  │    Returns: ExecutionRecord or None
  │    Store in: workflow.execution_records
  │
  └─→ Return ExecutionRecord (or None if stopped at any step)
```

---

## Key Performance Indicators (KPIs)

**Target Metrics:**
- Win Rate: ≥60% (minimum 40%)
- Risk/Reward: ≥1:2 per trade
- Profit Factor: >1.5
- False Signal Rate: <15%
- Max Consecutive Losses: ≤3

See [claude.md](./claude.md) "KPIs" for tracking.

---

## Environment Variables

Key `.env` variables (see `.env.template`):
- `DEBUG` - Enable debug logging
- `LOG_LEVEL` - Logging level (INFO, DEBUG)
- `DATABASE_URL` - SQLite or PostgreSQL connection
- `FOUNDRY_PROJECT_ENDPOINT` - Azure AI Foundry URL
- `FOUNDRY_MODEL_DEPLOYMENT_NAME` - Model name
- `MT5_ACCOUNT`, `MT5_PASSWORD`, `MT5_SERVER` - MetaTrader config
- `MAX_CONCURRENT_TRADES` - Risk limit
- `MAX_RISK_PER_TRADE` - Risk percentage (default 0.02 = 2%)
- `MIN_CONFIDENCE_THRESHOLD` - Signal confidence (default 75)

---

## Useful Debug Commands

```python
# In Python console
from agents.workflow import TradingWorkflow
import asyncio

workflow = TradingWorkflow(verbose=True)
result = asyncio.run(workflow.execute_trading_cycle({"daily": {}, "4h": {}, "1h": {}}))

# Check last trend report
print(workflow.last_trend_report.to_dict() if workflow.last_trend_report else "No report")

# Get performance summary
print(workflow.get_performance_summary())
```

---

## Next Development Phases

1. **Implement Real Market Data Integration** - Complete MT5/Alpaca providers
2. **Enhance ICT Pattern Detection** - Add technical analysis for Sweep, BoS, Imbalance
3. **Implement Trade Execution** - Connect to broker APIs
4. **Deploy to Azure** - Container Apps or App Service
5. **Add Monitoring/Dashboards** - Application Insights integration

---

## Helpful Links

- **Microsoft Agent Framework Docs**: https://github.com/microsoft/agents
- **Azure AI Foundry**: https://ai.azure.com
- **MetaTrader 5 API**: https://www.mql5.com/en/docs
- **Pytest Async**: https://pytest-asyncio.readthedocs.io

---

**Last Updated:** April 22, 2026  
**Version:** 1.0.0
