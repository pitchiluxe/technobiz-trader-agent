# Quick Command Reference — Multi-Pair Trading Agent

## Installation & Setup

```bash
# Navigate to project
cd c:\Users\erick\Downloads\Trading_Agent

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Update dependencies (if needed)
pip install --upgrade -r requirements.txt
```

---

## Running the System

### Option 1: Interactive Pair Selection (RECOMMENDED)

```bash
python main_enhanced.py
```

**What happens:**
1. Welcome screen displays
2. Quick start guide shown
3. Interactive menu appears
4. Select asset class (Forex, Crypto, Commodities, Indices, Stocks)
5. Select specific pair(s)
6. Trading begins

**Best for:** Beginners, testing, manual pair selection

### Option 2: Automated (from .env)

```bash
# Set pairs in .env
echo TRADING_PAIRS=EURUSD,GBPUSD,AUDUSD >> .env

# Run with predefined pairs
python main_enhanced.py
```

**Best for:** Production, consistent pair setup

### Option 3: Single Pair (Simplest)

```bash
# Set single pair
echo TRADING_PAIRS=EURUSD >> .env

# Run
python main_enhanced.py
```

**Best for:** Focused analysis, single currency pair

---

## Testing & Validation

### Test MT5 Connection

```bash
# Quick connection test
python test_mt5_connection.py

# Full integration test
python test_mt5_integration.py
```

### Test Individual Agents

```bash
# Test Trend-Master
python -m agents.trend_master.trend_master

# Test Analyse-Master
python -m agents.analyse_master.analyse_master

# Test Trader-Master
python -m agents.trader_master.trader_master
```

### Run Agent Commands

```bash
# Execute Trend-Master diagnostic
/trend-master run

# Execute Analyse-Master diagnostic
/analyse-master run

# Execute Trader-Master diagnostic
/trader-master run

# Execute full cycle
/full-cycle run
```

---

## Configuration

### Edit Trading Parameters

```bash
# Open .env in editor
notepad .env

# Key parameters to configure:
# TRADING_PAIRS=EURUSD,GBPUSD,AUDUSD
# TRADING_INTERVAL_MINUTES=15
# RISK_PER_TRADE=0.02
# MAX_CONCURRENT_TRADES=3
# MAX_DAILY_DRAWDOWN=0.05
```

### Register Custom Pair (Python)

```python
from config.trading_pairs_config import pairs_registry, AssetClass

# Add custom pair
pairs_registry.register_custom_pair(
    symbol="CADUSD",
    asset_class=AssetClass.FOREX,
    pip_value=0.0001,
    description="Canadian Dollar vs US Dollar"
)

# Verify
pair = pairs_registry.get_pair("CADUSD")
print(f"Registered: {pair.symbol}")
```

---

## Workflow Execution

### View Supported Pairs

```bash
# List all pairs in registry
python -c "
from config.trading_pairs_config import pairs_registry
for pair in pairs_registry.list_all_pairs():
    print(f'{pair.symbol:<10} | {pair.asset_class.value:<12} | {pair.description}')
"
```

### Get Pairs by Asset Class

```bash
# List all forex pairs
python -c "
from config.trading_pairs_config import pairs_registry, AssetClass
for pair in pairs_registry.get_pairs_by_asset_class(AssetClass.FOREX):
    print(pair.symbol)
"

# List all crypto pairs
python -c "
from config.trading_pairs_config import pairs_registry, AssetClass
for pair in pairs_registry.get_pairs_by_asset_class(AssetClass.CRYPTO):
    print(pair.symbol)
"
```

---

## Monitoring

### View Live Logs

```bash
# Stream logs in real-time
tail -f logs/trading_*.log

# View latest log file
ls -lht logs/trading_*.log | head -1
```

### Check Workflow Status

```bash
# Monitor workflow cycles
python -c "
from agents.workflow_orchestrator import WorkflowOrchestrator
orch = WorkflowOrchestrator()
stats = orch.get_performance_stats()
print(f'Total cycles: {stats[\"total_cycles\"]}')
print(f'Signals: {stats[\"successful_signals\"]}')
print(f'Trades: {stats[\"executed_trades\"]}')
"
```

---

## Stopping the System

### Graceful Shutdown

```bash
# Press Ctrl+C in terminal window
# System will:
# 1. Complete current trading cycle
# 2. Close open positions (or log for manual review)
# 3. Disconnect from MT5
# 4. Close database
# 5. Exit cleanly
```

### Emergency Stop

```bash
# Force stop (lose current state)
taskkill /IM python.exe /F

# Or in PowerShell:
Stop-Process -Name python -Force
```

---

## Troubleshooting Commands

### Check Python Version

```bash
python --version
# Expected: Python 3.10+
```

### Check Virtual Environment

```bash
where python
# Should show: ...venv\Scripts\python.exe

pip list | grep MetaTrader
# Should show: MetaTrader5 5.0.37+
```

### Verify MT5 Connection

```bash
python -c "
import MetaTrader5 as mt5
print(f'MT5 Version: {mt5.version()}')
info = mt5.terminal_info()
print(f'Terminal: {info.name}')
"
```

### Test Workflow Orchestrator

```bash
python -c "
from agents.workflow_orchestrator import WorkflowOrchestrator, WorkflowPhase
orch = WorkflowOrchestrator()
state = orch.start_cycle('EURUSD')
print(f'Workflow: {state.cycle_id}')
print(f'Phase: {state.phase.value}')
"
```

---

## Performance Monitoring

### Get Cycle Statistics

```bash
python -c "
from agents.workflow_orchestrator import WorkflowOrchestrator
orch = WorkflowOrchestrator()
stats = orch.get_performance_stats()
for key, value in stats.items():
    print(f'{key}: {value}')
"
```

### View Workflow History

```bash
python -c "
from agents.workflow_orchestrator import WorkflowOrchestrator
orch = WorkflowOrchestrator()
history = orch.get_workflow_history()
for wf in history:
    print(f'{wf[\"cycle_id\"]} | {wf[\"symbol\"]} | {wf[\"phase\"]} | {wf[\"duration_seconds\"]}s')
"
```

---

## Development Commands

### Run Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_workflow_orchestrator.py -v

# Run with coverage
pytest --cov=agents tests/
```

### Code Quality Checks

```bash
# Format code
black agents/ utils/

# Lint code
pylint agents/ utils/

# Type checking
mypy agents/ --ignore-missing-imports
```

### Generate Documentation

```bash
# Generate docs from docstrings
python -m pydoc -w agents.workflow_orchestrator
```

---

## Database Commands

### Initialize Database

```bash
# Create tables
python -c "from database.db_manager import db_manager; db_manager.create_tables()"

# Verify tables created
sqlite3 trading.db ".tables"
```

### Query Trade History

```bash
# View all trades
sqlite3 trading.db "SELECT * FROM trades LIMIT 10;"

# View today's trades
sqlite3 trading.db "SELECT * FROM trades WHERE date(created_at) = date('now');"

# Get trade statistics
sqlite3 trading.db "SELECT symbol, COUNT(*) as count, AVG(profit) as avg_profit FROM trades GROUP BY symbol;"
```

---

## Environment Variables Quick Reference

```bash
# Trading Configuration
TRADING_PAIRS=EURUSD,GBPUSD,AUDUSD    # Comma-separated pairs
TRADING_INTERVAL_MINUTES=15           # Cycle interval

# MT5 Credentials
MT5_ENABLED=true
MT5_ACCOUNT=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Risk Management
RISK_PER_TRADE=0.02                   # 2% per trade
MAX_CONCURRENT_TRADES=3               # Max open positions
MAX_DAILY_DRAWDOWN=0.05               # 5% max loss per day

# System Configuration
DEBUG_MODE=false                       # Enable verbose logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT=production                # development or production
DATABASE_URL=sqlite:///./trading.db   # Database path
```

---

## Quick Start (5 Minutes)

```bash
# 1. Setup
cd c:\Users\erick\Downloads\Trading_Agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
echo MT5_ACCOUNT=your_account >> .env
echo MT5_PASSWORD=your_password >> .env
echo MT5_SERVER=your_server >> .env

# 3. Test
python test_mt5_integration.py

# 4. Run
python main_enhanced.py

# 5. Select pairs interactively and start trading!
```

---

## Common Workflows

### Single Pair Analysis (EURUSD only)

```bash
export TRADING_PAIRS=EURUSD
python main_enhanced.py
```

### Major Pairs Portfolio

```bash
export TRADING_PAIRS=EURUSD,GBPUSD,USDJPY,AUDUSD
python main_enhanced.py
```

### Crypto Trading

```bash
export TRADING_PAIRS=BTCUSD,ETHUSD
python main_enhanced.py
```

### Commodity Focus

```bash
export TRADING_PAIRS=XAUUSD,WTIUSD
python main_enhanced.py
```

### Mixed Strategy

```bash
export TRADING_PAIRS=EURUSD,XAUUSD,BTCUSD
python main_enhanced.py
```

---

**Version:** 2.0  
**Last Updated:** May 3, 2026  
**Status:** Production Ready
