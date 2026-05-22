# TechnobizTrader - AI Trading Agency Blueprint

## Project Overview

**TechnobizTrader** is a sophisticated multi-agent AI trading system built on the **ICT (Inner Circle Trading) Methodology** by Michael S. Specifically, the system leverages:
- **Liquidity Sweep** detection
- **Break of Structure (BoS)** identification  
- **Imbalance & Order Block** creation analysis
- **Pullback Entry** at key levels

The agency operates as an autonomous trading orchestrator with 3 specialized agents working in sequence, each with distinct responsibilities. The system prioritizes **accuracy over trade frequency** and is designed to eliminate false signals through rigorous multi-layer validation.

---

## Architecture & Agent Responsibilities

### 1. **Trend-Master Agent** (Market Analyst)
**Responsibility:** Macro trend identification and directional bias establishment

**Detailed Workflow:**
- Analyze price action across multiple timeframes (Daily, 4H, 1H as minimum)
- Identify the current market structure (Uptrend, Downtrend, Ranging/Sideways)
- Detect major support/resistance levels and their significance
- Track swing highs and swing lows to confirm trend direction
- Monitor liquidity levels where institutional traders concentrate orders
- Generate a **TrendReport** containing:
  - Overall directional bias (BULLISH / BEARISH / NEUTRAL)
  - Confidence score (0-100%)
  - Key Support/Resistance zones with liquidity levels
  - Swing structure (recent higher lows for uptrends / lower highs for downtrends)
  - Timeframe-specific observations
  - Risk level assessment

**Output:** Passes structured TrendReport to Analyse-Master

**Key Rules:**
- Must analyze at least 3 timeframes minimum
- Support/Resistance zones must have historical validation (tested at least 2 times)
- Liquidity levels identified from recent swing points
- Trend confirmation requires observable break of structure

---

### 2. **Analyse-Master Agent** (Entry Signal Generator)
**Responsibility:** Identify trade entry opportunities during "kill zones" using ICT methodology

**Detailed Workflow:**
- Receives TrendReport from Trend-Master
- Scans for **Liquidity Sweep** patterns:
  - Price moves beyond previous swing high/low (capturing stop orders)
  - Reversal signal at these levels indicates manipulation
  - Confirms liquidity pool exhaustion
  
- Detects **Break of Structure (BoS)**:
  - On uptrend: Lower low breaks below recent structure
  - On downtrend: Higher high breaks above recent structure
  - Signals potential reversal or continuation depending on context

- Identifies **Imbalance & Order Blocks**:
  - Imbalance: Gap in price action (unfilled area on chart)
  - Order Block: Price rejection zone where institutions entered
  - These areas act as magnets for price retesting

- Locates **Pullback Entry Opportunities** (Kill Zone):
  - After liquidity sweep and break of structure
  - Price retraces into order block/imbalance area
  - Monitors for micro structure within pullback for precision entry
  - **Kill Zone Definition**: The 15-30 minute window after order block identification where price typically retraces into the identified zone

- Generates **TradeSignal** containing:
  - Entry level (exact price with pip precision)
  - Stop loss placement (beyond order block/imbalance)
  - Take profit targets (1st, 2nd, 3rd levels based on risk/reward)
  - Risk/Reward ratio (minimum 1:2 required)
  - Signal confidence score (0-100%)
  - Pattern confirmation checklist
  - Time window validity (when signal expires if not filled)

**Output:** Passes validated TradeSignal to Trader-Master

**Kill Zone Validation Checklist:**
- ✓ Liquidity Sweep confirmed
- ✓ Break of Structure identified
- ✓ Imbalance/Order Block marked
- ✓ Risk/Reward ratio ≥ 1:2
- ✓ Confluence with support/resistance
- ✓ Volume profile confirmation
- ✓ Time-based entry window valid

**Key Rules:**
- NO signal generation without all 4 ICT elements (Sweep, BoS, Imbalance, Pullback)
- Minimum 1:2 Risk/Reward ratio mandatory
- Signal expires after 30 minutes if market conditions change
- Multiple timeframe confluence required (at least 2 timeframes must align)
- False signal prevention: Cross-validate with volume and price action micro-structure

---

### 3. **Trader-Master Agent** (Execution Engine)
**Responsibility:** Execute trades based on validated signals with risk management

**Detailed Workflow:**
- Receives TradeSignal from Analyse-Master
- Performs final pre-execution validation:
  - Verify signal is still within kill zone time window
  - Confirm current price action aligns with predicted movement
  - Check portfolio risk exposure (max 2% per trade)
  - Verify liquidity at entry level
  - Check for conflicting macroeconomic events (news/data releases)

- Executes trade with parameters:
  - Entry: Limit order at specified level (wait up to 5 minutes for fill)
  - Stop Loss: Hard stop at predetermined level
  - Take Profit: Tiered exit strategy
    - TP1 (50% position): 1st target
    - TP2 (30% position): 2nd target
    - TP3 (20% position): 3rd target trailing stop

- Trade Execution Record includes:
  - Entry time and price
  - Position size
  - Stop loss level and distance (pips)
  - All three take profit levels
  - Trade ID for tracking
  - Execution quality score

- Post-execution monitoring:
  - Track trade journey from entry to exit
  - Record actual entry vs. signal entry (slippage analysis)
  - Capture exit prices and reasons (TP hit, SL hit, manual close)
  - Document trade outcome (Win/Loss) and P&L

**Trade Execution Rules:**
- Only execute if TradeSignal confidence ≥ 75%
- Position size: Dynamic based on account balance and risk percentage (2% max per trade)
- Entry method: Limit orders preferred; market order only if signal high urgency
- Stop loss: NEVER trade without hard stop
- Risk/Reward must be ≥ 1:2 at execution
- Maximum 3 simultaneous open trades per account
- Trade timeout: Close unfilled limit orders after 5 minutes

**Exit Strategy:**
- TP1: 1st resistance/swing level (50% of position)
- TP2: 2nd resistance/swing level (30% of position)  
- TP3: Trailing stop at 10 pips (20% of position)
- SL: Below imbalance/order block (hard stop, non-negotiable)

**Risk Management Override Rules:**
- If portfolio drawdown > 5% for the day: PAUSE all trading until next day
- If daily win rate < 40% for 5 consecutive trades: STOP and call for Trend-Master re-analysis
- If 3 consecutive losing trades: Reduce position size by 50% for next 5 trades

---

## Folder Structure

```
Trading_Agent/
│
├── claude.md                              # This blueprint document
├── README.md                              # Project setup and quick start guide
│
├── agents/                                # Multi-agent system core
│   ├── __init__.py
│   ├── base_agent.py                     # Base agent class with common methods
│   │
│   ├── trend_master/
│   │   ├── __init__.py
│   │   ├── trend_master.py               # Trend-Master agent implementation
│   │   ├── instructions.md               # Detailed system prompts
│   │   ├── analysis_tools.py             # Technical analysis utilities
│   │   └── models.py                     # TrendReport data model
│   │
│   ├── analyse_master/
│   │   ├── __init__.py
│   │   ├── analyse_master.py             # Analyse-Master agent implementation
│   │   ├── instructions.md               # ICT methodology prompts
│   │   ├── ict_analyzer.py               # ICT pattern detection logic
│   │   ├── entry_finder.py               # Kill zone identification
│   │   └── models.py                     # TradeSignal data model
│   │
│   ├── trader_master/
│   │   ├── __init__.py
│   │   ├── trader_master.py              # Trader-Master agent implementation
│   │   ├── instructions.md               # Execution rules and guidelines
│   │   ├── execution_engine.py           # Trade execution logic
│   │   ├── risk_manager.py               # Position sizing & risk management
│   │   └── models.py                     # ExecutionRecord data model
│   │
│   └── workflow.py                       # Orchestration of agent workflow
│
├── config/                               # Configuration management
│   ├── __init__.py
│   ├── settings.py                       # Environment settings and constants
│   ├── api_config.py                     # Market data API configuration
│   ├── trading_params.py                 # Trading parameters (timeframes, pairs, etc.)
│   └── secrets.py                        # API keys and credentials (gitignore)
│
├── market_data/                          # Market data integration
│   ├── __init__.py
│   ├── data_provider.py                  # Abstract data provider interface
│   ├── mt5_provider.py                   # MetaTrader 5 integration
│   ├── alpaca_provider.py                # Alpaca API integration (alternative)
│   ├── cache.py                          # Price data caching layer
│   └── models.py                         # Candle, OHLC data models
│
├── utils/                                # Utility functions
│   ├── __init__.py
│   ├── logger.py                         # Logging configuration
│   ├── validation.py                     # Input validation helpers
│   ├── chart_analyzer.py                 # Chart pattern analysis utilities
│   ├── notification.py                   # Alert/notification system (email, telegram)
│   └── performance_tracker.py            # Trade performance metrics
│
├── database/                             # Data persistence
│   ├── __init__.py
│   ├── db_manager.py                     # Database connection manager
│   ├── models.py                         # SQLAlchemy ORM models
│   ├── migrations/                       # Database migration scripts
│   └── schemas.py                        # Database table schemas
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── test_trend_master.py
│   ├── test_analyse_master.py
│   ├── test_trader_master.py
│   ├── test_ict_patterns.py
│   ├── test_workflow.py
│   ├── fixtures/                         # Test data fixtures
│   │   ├── sample_candles.py
│   │   ├── sample_signals.py
│   │   └── mock_market_data.py
│   └── integration/                      # Integration tests
│       └── test_end_to_end.py
│
├── docs/                                 # Documentation
│   ├── ICT_METHODOLOGY.md                # Detailed ICT strategy guide
│   ├── API_REFERENCE.md                  # Agent APIs and interfaces
│   ├── SETUP_GUIDE.md                    # Installation and configuration
│   ├── TROUBLESHOOTING.md                # Common issues and solutions
│   └── EXAMPLES.md                       # Usage examples
│
├── .env.template                         # Environment variables template
├── requirements.txt                      # Python dependencies
├── pyproject.toml                        # Project metadata (optional for modern Python)
├── Dockerfile                            # Container support
├── docker-compose.yml                    # Docker compose for full stack
├── .gitignore                            # Git ignore rules
└── main.py                               # Entry point for the trading agency

```

---

## Rules & Guardrails

### Signal Quality Requirements (Mandatory)

1. **False Signal Prevention**
   - Analyse-Master MUST confirm all 4 ICT elements before generating signal
   - Minimum 2-timeframe confluence required
   - Confidence score must be ≥ 75% for Trader-Master execution
   - No signals during high volatility periods (ATR > 3-month average × 1.5)

2. **Risk Management Constraints**
   - Maximum risk per trade: 2% of account balance
   - Minimum Risk/Reward ratio: 1:2 (1 risk : 2 potential reward)
   - Maximum concurrent trades: 3 open positions
   - Daily maximum loss: 5% (auto-pause if exceeded)
   - Position size dynamically calculated: Account × Risk% / Stop Loss Pips

3. **Liquidity Requirements**
   - Only trade during peak liquidity hours for chosen market/pair
   - Minimum bid-ask spread threshold respected
   - Avoid trading during economic news events (± 5 minutes)
   - Slippage tolerance: Max 2 pips deviation from target entry

4. **Time-Based Constraints**
   - Trade signals valid only for 30 minutes (kill zone window)
   - Entry execution timeout: 5 minutes (cancel unfilled orders)
   - Minimum holding time: 5 minutes (avoid scalping)
   - No new signals within 15 minutes of previous trade close

5. **Validation Checklist Before Execution**
   - ✓ TrendReport current (< 30 minutes old)
   - ✓ TradeSignal confidence ≥ 75%
   - ✓ Portfolio risk ≤ 2% per trade
   - ✓ Account drawdown < 5%
   - ✓ Win rate check (≥ 40% minimum)
   - ✓ No conflicting news events in next 1 hour
   - ✓ Market is in active trading hours

### Agent Behavior Guardrails

1. **Trend-Master**
   - Analyze minimum 3 timeframes (Daily, 4H, 1H)
   - Support/Resistance zones must have ≥ 2 historical tests
   - No trend signals on choppy/ranging markets without confirmation
   - Update trend analysis every 4 hours minimum

2. **Analyse-Master**
   - Reject signals if any ICT element is missing (Sweep, BoS, Imbalance, Pullback)
   - Verify imbalance size: Minimum 50 pips, maximum 500 pips (currency-dependent)
   - Order block size validation: Must contain at least 2 candles
   - No signals outside kill zone time window
   - Cross-validate with volume profile for confirmation

3. **Trader-Master**
   - Refuse execution if signal confidence < 75%
   - Enforce hard stop loss (non-negotiable)
   - No averaging down or martingale strategies
   - Exit at predefined levels (TP1, TP2, TP3, SL)
   - Log all trades with full audit trail

### System-Level Guardrails

1. **Data Integrity**
   - Verify price data from multiple sources before analysis
   - Discard corrupted/gap-filled candles from analysis
   - Use only official market hours data (exclude pre/post-market if applicable)

2. **Failsafe Mechanisms**
   - Circuit breaker: Auto-stop if 3 consecutive losses
   - Volatility check: Refuse signals during extreme volatility
   - Account protection: Pause all trading if drawdown > 5%
   - Connectivity failsafe: Reconnect market data every 5 minutes

3. **Performance Monitoring**
   - Track win rate, loss rate, average profit factor
   - Alert if win rate drops below 40% for 5 consecutive trades
   - Monitor daily/weekly/monthly performance
   - Analyze slippage and execution quality

---

## Tech Stack

### Core Framework
- **Python 3.10+** - Agent development language
- **Microsoft Agent Framework (v1.0.0rc6)** - Multi-agent orchestration
- **Azure AI Foundry** - Model hosting and inference
  - Optional alternative: OpenAI API / Anthropic Claude API
- **FoundryChatClient** - Default AI client for agent interactions

### Market Data & Trading
- **MetaTrader 5 (MT5) SDK** - Real-time market data and trade execution
  - Alternative: Alpaca Markets API for US equities
- **TA-Lib / pandas-ta** - Technical analysis library for indicators
- **numpy, pandas** - Data manipulation and analysis
- **scipy** - Statistical analysis for pattern detection

### Database & Storage
- **SQLAlchemy** - ORM for database abstraction
- **PostgreSQL** or **SQLite** (development) - Trade history and signals storage
- **Redis** (optional) - Caching market data for performance

### Hosting & Deployment
- **FastAPI** / **Starlette** - HTTP server for agent hosting
- **Azure App Service** or **Azure Container Apps** - Production deployment
- **Docker** - Containerization
- **Kubernetes** (optional) - Orchestration for high-scale

### Monitoring & Logging
- **Python Logging** - System-level logging
- **Azure Application Insights** - Performance monitoring and diagnostics
- **Prometheus** (optional) - Metrics collection
- **Grafana** (optional) - Dashboard visualization

### Development Tools
- **VS Code** - IDE with AI Toolkit extension
- **agentdev CLI** - Agent development and testing
- **pytest** - Unit and integration testing
- **Black, Pylint** - Code quality and formatting
- **Git** - Version control

### Dependencies Summary (requirements.txt)
```
# Agent Framework
agent-framework-core==1.0.0rc6
agent-framework-foundry==1.0.0rc6
agent-framework-openai==1.0.0rc6
azure-ai-agentserver-agentframework==1.0.0b16
azure-ai-agentserver-core==1.0.0b16
agent-dev-cli==0.0.1b260316

# Azure & Cloud
azure-identity
azure-storage-blob

# Market Data
mt5-py==5.0.37
alpaca-trade-api==3.1.1

# Data Science
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
ta-lib  # or pandas-ta as alternative

# Database
sqlalchemy>=2.0.0
psycopg2-binary  # PostgreSQL adapter
python-dotenv

# Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0

# Utilities
python-dateutil
pytz
requests
httpx

# Logging & Monitoring
python-json-logger
```

---

## Project Workflow & Execution Flow

### 1. **Initialization Phase**
```
System Start
    ↓
Load Configuration (.env, settings.py)
    ↓
Connect to Market Data Provider (MT5/Alpaca)
    ↓
Initialize Database (Trend History, Trade Logs)
    ↓
Agents Ready: Trend-Master, Analyse-Master, Trader-Master
```

### 2. **Continuous Analysis Loop**
```
Every Analysis Cycle (15-minute interval):
    ↓
[TREND-MASTER]
    Fetch latest OHLC data (Daily, 4H, 1H)
    ↓
    Analyze trend, support/resistance, liquidity
    ↓
    Generate TrendReport
    ↓
    Store in database
    ↓
    Publish to Analyse-Master
    ↓
[ANALYSE-MASTER]
    Receive TrendReport
    ↓
    Scan for ICT patterns (Sweep, BoS, Imbalance)
    ↓
    Identify Kill Zone entry opportunities
    ↓
    Calculate Risk/Reward ratios
    ↓
    Generate TradeSignal (if all conditions met)
    ↓
    Confidence check (≥ 75%?)
    ↓
    Publish validated TradeSignal
    ↓
[TRADER-MASTER]
    Receive TradeSignal
    ↓
    Final validation:
        - Kill zone time window still valid?
        - Account risk ≤ 2%?
        - Portfolio drawdown < 5%?
        - Market conditions unchanged?
    ↓
    Execute Trade
        - Place limit order at entry
        - Set stop loss
        - Set take profits (3 levels)
    ↓
    Monitor execution:
        - Track entry fill
        - Record slippage
        - Monitor P&L in real-time
    ↓
    Exit at TP levels or SL
    ↓
    Log trade outcome
    ↓
    Update performance metrics
```

### 3. **Performance Tracking**
```
After Each Trade:
    - Record entry/exit prices
    - Calculate P&L and % return
    - Update win rate
    - Track slippage
    - Store in database for analysis
    
Daily Review (End of Day):
    - Calculate daily P&L
    - Check drawdown
    - Verify win rate ≥ 40%
    - Review false signals
    - Prepare report for next day
```

---

## Key Performance Indicators (KPIs)

1. **Trading Metrics**
   - Win Rate: Target ≥ 60% (initially 40% minimum threshold)
   - Risk/Reward Ratio: Minimum 1:2 (ideal 1:3)
   - Profit Factor: (Gross Profit / Gross Loss) > 1.5
   - Maximum Consecutive Losses: ≤ 3
   - Average Trade Duration: 30 min - 4 hours

2. **Signal Quality Metrics**
   - False Signal Rate: < 15% (signals that don't move as predicted)
   - Signal Accuracy: ≥ 75% confidence average
   - Kill Zone Hit Rate: > 80% (price reaches entry zone within 30 min window)
   - Pattern Confirmation Rate: > 90% (ICT elements confirmed)

3. **Execution Metrics**
   - Slippage Average: < 2 pips
   - Order Fill Rate: > 95% (limit orders successfully filled)
   - Execution Speed: Entry within 5 minutes of signal
   - Risk Management Compliance: 100% (no trades without SL)

4. **System Metrics**
   - Uptime: > 99.5%
   - Data Freshness: Updated every 1 minute
   - Analysis Latency: < 5 seconds from data to signal
   - Error Recovery Time: < 2 minutes

---

## Getting Started Checklist

- [ ] Set up Python 3.10+ environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure `.env` with API keys (MT5 account / Alpaca keys)
- [ ] Set up database (PostgreSQL or SQLite)
- [ ] Run migrations: `python -m alembic upgrade head`
- [ ] Configure Azure AI Foundry or OpenAI credentials
- [ ] Test market data connection: `python test_market_data.py`
- [ ] Deploy agents to Azure App Service or Container Apps
- [ ] Run backtest suite: `pytest tests/ -v`
- [ ] Enable monitoring: Application Insights integration
- [ ] Start trading agency: `python main.py`

---

## Risk Disclaimer

**TechnobizTrader** is an AI-powered trading system designed for educational and research purposes. Trading forex, stocks, commodities, or other financial instruments involves substantial risk of loss. Past performance does not guarantee future results. The system operates based on algorithmic pattern recognition and may not account for unprecedented market conditions or geopolitical events.

**Always:**
- Trade with capital you can afford to lose
- Start with small position sizes
- Monitor the system regularly
- Maintain manual override capabilities
- Validate signals independently before execution

---

## References & Resources

1. **ICT Strategy Documentation**
   - Michael S. Inner Circle Trading methodology
   - Liquidity sweep patterns and manipulation detection
   - Order block and imbalance analysis

2. **Technical Implementation**
   - Microsoft Agent Framework Documentation
   - MetaTrader 5 Python API Reference
   - Azure AI Foundry Best Practices

3. **Risk Management**
   - Ralph Vince: Position Sizing
   - Van K. Tharp: Risk Management Framework
   - Anthony Robbins: Optimal Position Sizing

---

**Document Version:** 1.0  
**Last Updated:** April 22, 2026  
**Status:** Blueprint Ready for Implementation
