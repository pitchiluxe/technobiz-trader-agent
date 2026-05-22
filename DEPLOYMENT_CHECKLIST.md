# TechnobizTrader - Production Deployment Checklist

**Version:** 1.0.0  
**Last Updated:** April 25, 2026  
**Status:** ✅ Ready for Deployment

---

## ✅ Pre-Deployment Phase (Before First Trade)

### Environment Setup

- [ ] **Python Environment**
  - [ ] Python 3.10+ installed: `python --version`
  - [ ] Virtual environment created: `python -m venv venv`
  - [ ] Virtual environment activated: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
  - [ ] All dependencies installed: `pip install -r requirements.txt`
  - [ ] No dependency conflicts: `pip check`

### Configuration

- [ ] **.env File Created**
  - [ ] Copied from .env.template: `cp .env.template .env`
  - [ ] All required fields populated:
    - [ ] MT5_ACCOUNT = (your account number)
    - [ ] MT5_PASSWORD = (your MT5 password)
    - [ ] MT5_SERVER = (your broker server)
    - [ ] ACCOUNT_BALANCE = (actual balance in USD)
    - [ ] DATABASE_URL = postgresql://... (PostgreSQL required)
    - [ ] FOUNDRY_PROJECT_ENDPOINT = (your Azure endpoint)
    - [ ] FOUNDRY_MODEL_DEPLOYMENT_NAME = (your model name)
    - [ ] FOUNDRY_API_KEY = (your API key)
  - [ ] No test/placeholder values remaining
  - [ ] .env is in .gitignore (never commit credentials)
  - [ ] ENVIRONMENT = "production" for live trading

- [ ] **Trading Parameters**
  - [ ] TRADING_PAIRS = valid pairs (EURUSD,GBPUSD,XAUUSD)
  - [ ] MAX_CONCURRENT_TRADES = 3 (conservative start)
  - [ ] MAX_RISK_PER_TRADE = 0.02 (2% per trade)
  - [ ] MIN_CONFIDENCE_THRESHOLD = 75 (high quality only)
  - [ ] ACCOUNT_BALANCE > 0 (not zero or placeholder)

### System Validation

- [ ] **Startup Validation Passes**
  ```bash
  python -c "from utils.startup_validator import StartupValidator; \
             StartupValidator.full_startup_check()"
  ```
  Expected output:
  ```
  ✅ Environment Variables....... PASS
  ✅ MetaTrader 5 Terminal........ PASS
  ✅ Database Connection.......... PASS
  ✅ All checks passed!
  ```

- [ ] **MetaTrader 5 Setup**
  - [ ] MT5 desktop application installed
  - [ ] Account created and funded (demo or live)
  - [ ] MT5 terminal is running and logged in
  - [ ] Account shows "connected" status (bottom right of MT5)
  - [ ] All desired trading pairs are in Market Watch
  - [ ] MT5 Python SDK installed: `pip install MetaTrader5`
  - [ ] Connection test passes:
    ```bash
    python -c "import MetaTrader5; print('MT5 version:', MetaTrader5.__version__)"
    ```

- [ ] **Database Setup**
  - [ ] PostgreSQL is installed and running
  - [ ] Database created: `createdb technobiz_trader`
  - [ ] User created with permissions
  - [ ] Connection test passes:
    ```bash
    psql -U trader -d technobiz_trader -c "SELECT version();"
    ```
  - [ ] Tables created (if new database):
    ```bash
    python -c "from database.db_manager import db_manager; db_manager.create_tables()"
    ```

- [ ] **Azure AI Foundry Setup** (if using Foundry)
  - [ ] Foundry project created
  - [ ] Model deployed (gpt-4 or equivalent recommended)
  - [ ] API endpoint is accessible
  - [ ] API key is valid and has required permissions
  - [ ] Connection test passes:
    ```bash
    curl -H "Authorization: Bearer $FOUNDRY_API_KEY" \
         https://$FOUNDRY_PROJECT_ENDPOINT/health
    ```

### Logging & Monitoring

- [ ] **Logging Setup**
  - [ ] logs/ directory exists: `mkdir -p logs`
  - [ ] Permissions are correct (writable by application)
  - [ ] Log rotation is configured (in utils/logger.py)
  - [ ] First log file created: `touch logs/technobiz_trader.log`
  - [ ] Log format is readable

- [ ] **Backup Setup**
  - [ ] Database backup script created
  - [ ] Backup location configured
  - [ ] Backup permissions verified
  - [ ] Test backup runs successfully:
    ```bash
    pg_dump technobiz_trader > backup_test.sql
    ```

---

## 🧪 Testing Phase (Demo/Paper Trading)

### Functional Tests

- [ ] **Startup Test**
  ```bash
  python main.py
  ```
  - [ ] Application starts without errors
  - [ ] All agents initialize successfully
  - [ ] Market data fetches successfully
  - [ ] Logs show all initialization steps
  - [ ] Application gracefully exits (Ctrl+C)

- [ ] **Market Data Test**
  - [ ] Can fetch Daily candles for EURUSD
  - [ ] Can fetch 4H candles for EURUSD
  - [ ] Can fetch 1H candles for EURUSD
  - [ ] Candles have valid OHLC data
  - [ ] Timestamps are in chronological order
  - [ ] No missing data gaps

- [ ] **Trend Analysis Test**
  - [ ] Trend-Master generates trend reports
  - [ ] TrendReport contains valid bias (BULLISH/BEARISH/NEUTRAL)
  - [ ] Confidence score is 0-100%
  - [ ] Support/resistance levels are numerical
  - [ ] Liquidity zones are identified

- [ ] **Signal Generation Test**
  - [ ] Analyse-Master generates trade signals
  - [ ] Trade signals include all required fields:
    - [ ] Entry price
    - [ ] Stop loss
    - [ ] Take profit (3 levels)
    - [ ] Confidence score
    - [ ] Risk/reward ratio
    - [ ] ICT elements confirmation
  - [ ] Signals have confidence ≥75%
  - [ ] Risk/reward ratio ≥1:2
  - [ ] All 4 ICT elements confirmed

- [ ] **Approval Gateway Test**
  - [ ] Approval screen displays correctly
  - [ ] All trade details are visible
  - [ ] User can input choice [A/R/V]
  - [ ] System accepts all three choices
  - [ ] Approval is logged to database

- [ ] **Trade Execution Test (Demo Account)**
  - [ ] Approve a trade in approval screen
  - [ ] Trade executes successfully on MT5
  - [ ] Order appears in MT5 terminal
  - [ ] ExecutionRecord is created in database
  - [ ] Trade is logged with all details

### Performance Tests

- [ ] **Speed Tests**
  - [ ] Market data fetch: < 5 seconds
  - [ ] Trend analysis: < 15 seconds
  - [ ] Signal generation: < 15 seconds
  - [ ] Total cycle time: < 1 minute
  - [ ] No memory leaks (monitor with `top` or Task Manager)

- [ ] **Stability Tests**
  - [ ] System runs for 1 hour without errors
  - [ ] System runs for 4 hours without errors
  - [ ] System runs for 24 hours without errors
  - [ ] No connection drops
  - [ ] No database locks
  - [ ] Logs remain readable

- [ ] **Data Integrity Tests**
  - [ ] All trades recorded in database
  - [ ] Trade details match MT5 executions
  - [ ] Calculations are accurate:
    - [ ] Position size = (Account × 2%) / Stop loss pips
    - [ ] Risk/reward = (Entry - SL) / (TP - Entry)
  - [ ] No duplicate records
  - [ ] No missing fields

### Trade Quality Tests

- [ ] **Signal Quality (Paper Trading)**
  - [ ] Trade signals are generating (not all rejected)
  - [ ] Signals have good confluence (2+ timeframes align)
  - [ ] Confidence scores are realistic (not always 99%)
  - [ ] ICT elements are being confirmed
  - [ ] Win rate is realistic (40-60%)

- [ ] **Risk Management Tests**
  - [ ] Position sizing is correct
  - [ ] Max 2% risk per trade enforced
  - [ ] Max 3 concurrent trades enforced
  - [ ] Stop loss is set on every trade
  - [ ] Take profits are tiered (50/30/20%)
  - [ ] Account drawdown tracked

---

## 🔐 Security Phase (Before Live Trading)

### Credentials & Access

- [ ] **API Keys & Passwords**
  - [ ] All keys are stored in .env (never in code)
  - [ ] .env is in .gitignore
  - [ ] No credentials logged to console
  - [ ] No credentials in database
  - [ ] API keys have minimal required permissions
  - [ ] Keys can be rotated without code changes

- [ ] **Database Security**
  - [ ] PostgreSQL password is strong (20+ chars)
  - [ ] Database user has minimal permissions (not superuser)
  - [ ] SSH access is required (not open internet)
  - [ ] Database backups are encrypted
  - [ ] Database is backed up daily

- [ ] **MT5 Account Security**
  - [ ] Two-factor authentication enabled (if available)
  - [ ] API access limited to specific IPs (if available)
  - [ ] Demo account used for testing (not live)
  - [ ] Trading password is strong
  - [ ] Master password is secure

- [ ] **Code Security**
  - [ ] No hardcoded credentials in any file
  - [ ] No secrets in comments
  - [ ] No test API keys committed
  - [ ] Dependencies are from trusted sources
  - [ ] Requirements.txt pinned to specific versions
  - [ ] No vulnerable dependencies: `pip audit`

### Access Control

- [ ] **Application Access**
  - [ ] Only authorized users can access .env
  - [ ] Only authorized users can access database
  - [ ] Only authorized users can start the application
  - [ ] Logs are readable only by authorized users
  - [ ] Backups are accessible only to administrators

---

## 💰 Live Trading Phase (Go-Live)

### Pre-Live Checklist

- [ ] **Final Validation**
  - [ ] All tests pass in demo environment
  - [ ] Paper trading results are acceptable
  - [ ] Win rate ≥ 40% over 20+ trades
  - [ ] Risk management is working perfectly
  - [ ] No false signals or anomalies
  - [ ] Documentation is up to date

- [ ] **Account Setup**
  - [ ] Live MT5 account created (or demo preserved)
  - [ ] Account has minimum balance ($1000+ recommended)
  - [ ] Account is verified and approved
  - [ ] Trading hours are known
  - [ ] Leverage is set appropriately
  - [ ] Commission/spread structure understood

- [ ] **Monitoring Setup**
  - [ ] Daily monitoring schedule established
  - [ ] Alert system configured (email/SMS/Telegram)
  - [ ] Backup alert contacts identified
  - [ ] Emergency contact list prepared
  - [ ] Escalation procedures documented

### First Live Trade Process

1. [ ] **Pre-Trade**
   - [ ] Review all settings one final time
   - [ ] Check account balance is correct
   - [ ] Verify MT5 is running and connected
   - [ ] Check database is accessible
   - [ ] Review logs for any errors
   - [ ] Take a screenshot of account state

2. [ ] **During Trade**
   - [ ] Monitor all approval screens carefully
   - [ ] Review each trade signal thoroughly
   - [ ] Only approve trades you understand
   - [ ] Watch for unexpected behavior
   - [ ] Monitor logs in real-time
   - [ ] Keep MT5 visible

3. [ ] **Post-Trade**
   - [ ] Verify trade executed correctly on MT5
   - [ ] Check trade was recorded in database
   - [ ] Review trade details match signal
   - [ ] Monitor trade movement
   - [ ] Document any issues
   - [ ] Take end-of-day screenshot

### Ongoing Monitoring

- [ ] **Daily Checks**
  - [ ] Review logs: `tail logs/technobiz_trader.log`
  - [ ] Check database for new trades: `SELECT * FROM trade_execution ORDER BY entry_time DESC LIMIT 5;`
  - [ ] Verify account balance matches
  - [ ] Confirm no errors or warnings
  - [ ] Check win rate trend
  - [ ] Monitor drawdown

- [ ] **Weekly Reviews**
  - [ ] Analyze performance metrics
  - [ ] Review all executed trades
  - [ ] Calculate Profit Factor
  - [ ] Review signal quality
  - [ ] Check for any anomalies
  - [ ] Update risk management parameters if needed

- [ ] **Monthly Deep Dives**
  - [ ] Statistical analysis of all trades
  - [ ] Compare results to targets
  - [ ] Identify top/bottom performing pairs
  - [ ] Review all rejection decisions
  - [ ] Backtest new parameters
  - [ ] Plan adjustments for next month

---

## 🚨 Incident Response

### Emergency Stop Procedures

**If system behaves unexpectedly:**

1. [ ] Press Ctrl+C to stop the application
2. [ ] Manually close any open trades in MT5
3. [ ] Review logs: `tail -200 logs/technobiz_trader.log`
4. [ ] Check database for corrupted records
5. [ ] Investigate the cause
6. [ ] Fix the issue
7. [ ] Resume only after verification

### Common Issues & Recovery

| Issue | Solution |
|-------|----------|
| MT5 Connection Lost | Restart MT5, check internet, verify credentials |
| Database Connection Lost | Check PostgreSQL status, verify connection string |
| API Key Invalid | Regenerate key in Azure, update .env, restart |
| Memory Leak | Check logs, restart application if > 1GB RAM |
| No Trade Signals | Check market conditions, verify ICT elements being found |
| False Approvals | Review logs, adjust confidence threshold if needed |

### Rollback Procedures

**If live trading must stop:**

1. [ ] Modify .env: `ENVIRONMENT=maintenance`
2. [ ] Stop the application
3. [ ] Manually close all open trades in MT5
4. [ ] Review what went wrong in logs
5. [ ] Fix issues in code if needed
6. [ ] Run full test suite again
7. [ ] Only resume when confident

---

## 📊 Performance Targets

### Minimum Acceptable Performance

| Metric | Minimum Target | How to Verify |
|--------|---|---|
| Win Rate | 40% | `SELECT COUNT(*) WHERE p_and_l > 0` / total |
| Risk/Reward | 1:2 | Approval screen shows ratio |
| Uptime | 99% | Monitor logs |
| Data Accuracy | 100% | Compare MT5 vs database |
| Response Time | < 1 min | Monitor cycle times |

### Targets for Growth

| Metric | Target | Timeline |
|--------|--------|----------|
| Win Rate | 60% | Month 2-3 |
| Profit Factor | 1.5 | Month 2-3 |
| Max Drawdown | 5% | Ongoing |
| Signal Quality | 85%+ | Month 1-2 |

---

## 🔄 Maintenance Schedule

### Daily (5 minutes)

- [ ] Check logs for errors
- [ ] Review account balance
- [ ] Verify no open trades stuck

### Weekly (30 minutes)

- [ ] Analyze performance metrics
- [ ] Review all trades
- [ ] Check system health
- [ ] Update documentation if needed

### Monthly (1 hour)

- [ ] Deep statistical analysis
- [ ] Performance review meeting
- [ ] Parameter optimization
- [ ] Database maintenance
- [ ] Backup verification

### Quarterly (2 hours)

- [ ] Full system audit
- [ ] Security review
- [ ] Code review
- [ ] Upgrade dependencies
- [ ] Update documentation

---

## 📋 Sign-Off

**Deployment authorized by:**

- [ ] **System Admin**: _________________ Date: _______
- [ ] **Security Review**: _____________ Date: _______
- [ ] **Trading Owner**: ______________ Date: _______

**Go-Live Date**: ________________  
**First Live Trade Date**: ________________  
**Support Contact**: ________________  

---

**Production Deployment Checklist v1.0.0**  
**Last Updated:** April 25, 2026  
**Status:** ✅ Ready for Deployment
