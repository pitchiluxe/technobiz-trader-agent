# TechnobizTrader - Quick Reference Guide

**Version:** 1.0.0  
**Status:** ✅ Production Ready

---

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Install and setup
pip install -r requirements.txt
cp .env.template .env
# Edit .env with MT5 credentials

# 2. Test connection
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"

# 3. Start trading
python main.py                    # Automated mode
# OR
python interactive_mode.py        # Interactive mode
```

---

## 📊 Operating Modes

### **Automated Mode** (main.py)

```bash
python main.py
```

**Does:**
- Analyzes pairs from .env (TRADING_PAIRS variable)
- Generates trend reports
- Creates ICT trade signals
- **Requests your approval** for each trade
- Executes approved trades on MT5

**Best for:** Set-and-forget daily analysis

---

### **Interactive Mode** (interactive_mode.py)

```bash
python interactive_mode.py
```

**Menu:**
```
[1] Analyze trading pair (trend only)
[2] Analyze and generate trade signal
[3] Execute trade with approval
[4] View trading history
[5] Analyze multiple pairs
[6] Settings
[7] Exit
```

**Best for:** On-demand pair analysis and active trading

---

## 🔍 Trading Pair Analysis

### **Supported Pairs**

**Forex:** EURUSD, GBPUSD, USDJPY, EURGBP, GBPJPY, EURJPY, etc.  
**Commodities:** XAUUSD, XAGUSD, WTIUSD  
**Crypto:** BTCUSD, ETHUSD, LTCUSD  
**Indices:** US500, US100, DAX40, FTSE100

### **How to Request Analysis**

**Automated Mode:**

Edit `.env`:
```env
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD
```

Run:
```bash
python main.py
```

**Interactive Mode:**

```bash
python interactive_mode.py

# Select [1] or [2]
# Enter pair: EURUSD
# System analyzes and displays results
```

---

## ✅ Trade Approval Process

```
STEP 1: System generates trade signal
        ↓
STEP 2: Shows approval screen with details
        ├─ Entry Price
        ├─ Stop Loss
        ├─ Take Profits
        ├─ Risk/Reward
        └─ ICT Elements
        ↓
STEP 3: You choose [A]pprove, [R]eject, or [V]iew details
        ↓
STEP 4: If approved → Trade executes on MT5
        If rejected → Wait for next signal
```

### **Approval Screen Choices**

| Input | Action | Result |
|-------|--------|--------|
| `A` | APPROVE | Trade executed on MT5 |
| `R` | REJECT | Signal discarded |
| `V` | VIEW | See detailed analysis |

### **When to Approve**

✅ Confidence ≥ 75%  
✅ All 4 ICT elements confirmed  
✅ Risk/Reward ≥ 1:2  
✅ Entry price close to signal  
✅ Good market liquidity  
✅ Account drawdown < 5%

### **When to Reject**

❌ Confidence < 75%  
❌ Missing ICT elements  
❌ Risk/Reward < 1:2  
❌ Slippage too high  
❌ News events coming  
❌ Account drawdown > 5%

---

## 🔧 Configuration

### **Critical .env Variables**

```env
# MT5 Account (from MT5 terminal)
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo

# Account Balance (for position sizing)
ACCOUNT_BALANCE=50000

# Trading Pairs (automated mode)
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD

# Risk Management
MAX_CONCURRENT_TRADES=3
MAX_RISK_PER_TRADE=0.02
MIN_CONFIDENCE_THRESHOLD=75

# Database
DATABASE_URL=postgresql://user:pass@db/technobiz

# Azure AI Foundry
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.azure.ai.com
FOUNDRY_MODEL_DEPLOYMENT_NAME=your-model
FOUNDRY_API_KEY=your-api-key
```

### **Validate Configuration**

```bash
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"
```

---

## 📋 Common Commands

### **View Logs**

```bash
# Real-time logs
tail -f logs/technobiz_trader.log

# Last 100 lines
tail -100 logs/technobiz_trader.log

# Search for trades
grep "TRADE EXECUTED" logs/technobiz_trader.log

# Search for approvals
grep "APPROVAL" logs/technobiz_trader.log

# Windows PowerShell
Get-Content logs/technobiz_trader.log -Tail 100 -Wait
```

### **Check Database**

```bash
# Connect to PostgreSQL
psql -U trader -d technobiz_trader

# View executed trades
SELECT * FROM trade_execution ORDER BY entry_time DESC LIMIT 10;

# Calculate win rate
SELECT 
  COUNT(CASE WHEN p_and_l > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM trade_execution WHERE status='CLOSED';
```

### **Validate Connection**

```bash
# Check MT5 connection
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.check_mt5_terminal()"

# Check database connection
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.check_database()"
```

---

## 🎯 Workflow Summary

### **Analysis Pipeline**

```
Market Data (MT5)
    ↓
[TREND-MASTER]
├─ Analyze Daily, 4H, 1H candles
├─ Identify support/resistance
├─ Determine bias (BULLISH/BEARISH/NEUTRAL)
└─ Confidence score
    ↓
[ANALYSE-MASTER]
├─ Scan for ICT patterns:
│  ├─ Liquidity Sweep
│  ├─ Break of Structure
│  ├─ Imbalance/Order Block
│  └─ Pullback Entry
├─ Calculate Risk/Reward
└─ Generate TradeSignal
    ↓
[APPROVAL GATEWAY]
├─ Display trade details
├─ Request user choice
└─ Decision: Approve/Reject
    ↓
[TRADER-MASTER] (if approved)
├─ Validate all checks
├─ Calculate position size
├─ Place order on MT5
└─ Log execution
    ↓
[DATABASE]
└─ Store all records
```

---

## 🚨 Troubleshooting

### **Issue: "MT5 terminal not running"**

```bash
# Solution: Start MetaTrader 5
# 1. Open MT5 desktop application
# 2. Login to your account
# 3. Ensure "connected" status shows (bottom right)
# 4. Run trading agent again
```

### **Issue: "Cannot connect to database"**

```bash
# Solution: Verify DATABASE_URL in .env
# 1. Check PostgreSQL is running
# 2. Verify connection string: postgresql://user:pass@host/db
# 3. Test connection: psql -U user -d technobiz_trader
```

### **Issue: "API key invalid"**

```bash
# Solution: Check credentials in .env
# 1. Verify FOUNDRY_API_KEY is correct
# 2. Regenerate key in Azure portal if needed
# 3. Ensure key has required permissions
```

### **Issue: "No trade signals generated"**

```bash
# Reasons: 
# 1. ICT patterns may not align (NORMAL - wait for better setup)
# 2. Market might be choppy or ranging
# 3. Confidence might be below 75% threshold
# 
# Solutions:
# - Review logs: tail logs/technobiz_trader.log
# - Try different pairs
# - Wait for clearer market structure
```

---

## 📈 Performance Tracking

### **Key Metrics**

| Metric | Target | How to Check |
|--------|--------|-------------|
| Win Rate | ≥60% | Database: `SELECT COUNT(*) WHERE p_and_l > 0` |
| Risk/Reward | ≥1:2 | Approval screen shows ratio |
| Profit Factor | >1.5 | Sum profitable trades / Sum losses |
| Drawdown | <5% | Account balance monitoring |
| Confidence | ≥75% | Approval screen shows confidence |

### **Query Examples**

```sql
-- Win rate this week
SELECT 
  COUNT(CASE WHEN p_and_l > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM trade_execution
WHERE status='CLOSED' AND exit_time >= NOW() - INTERVAL '7 days';

-- Total profit/loss
SELECT SUM(p_and_l) as total_profit FROM trade_execution WHERE status='CLOSED';

-- Average trade duration
SELECT AVG(EXTRACT(EPOCH FROM (exit_time - entry_time))/3600) as avg_hours
FROM trade_execution WHERE status='CLOSED';
```

---

## 🔐 Security

### **Keep Safe**

```
✓ Never share .env file
✓ Never commit .env to Git
✓ Add .env to .gitignore
✓ Rotate API keys quarterly
✓ Use strong passwords
✓ Keep MT5 password secure
✓ Don't share trading credentials
```

### **Production Checklist**

- [ ] ENVIRONMENT=production in .env
- [ ] DATABASE_URL uses PostgreSQL (not SQLite)
- [ ] All API keys are set and valid
- [ ] DEBUG=False
- [ ] ACCOUNT_BALANCE reflects actual balance
- [ ] Database is backed up
- [ ] MT5 terminal is running
- [ ] Monitoring is configured
- [ ] .env is in .gitignore

---

## 📞 Support Resources

### **Documentation**

| Document | Purpose |
|----------|---------|
| [MT5_Connect.md](MT5_Connect.md) | MetaTrader 5 setup guide |
| [USER_GUIDE.md](USER_GUIDE.md) | Detailed user guide |
| [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) | Production deployment |
| [AGENTS.md](AGENTS.md) | Technical agent info |

### **External Links**

- MetaTrader 5: https://www.metatrader5.com
- Python API: https://www.mql5.com/en/docs/integration/python_metatrader5
- IC Markets Broker: https://www.icmarkets.com
- Exness Broker: https://www.exness.com

---

## 🎓 Learning Resources

### **ICT Methodology**

- Liquidity Sweep: Price moves past swing levels to capture stops
- Break of Structure: Recent swing pattern breaks down
- Imbalance/Order Block: Unfilled gap or institutional zone
- Pullback Entry: Price retraces into OB during 15-30 min kill zone

### **Trading Best Practices**

```
1. Start with DEMO account
2. Trade small position sizes
3. Never risk more than 2% per trade
4. Approve each trade consciously
5. Monitor all open positions
6. Exit at predefined levels
7. Journal every trade
8. Review performance weekly
```

---

## 💡 Pro Tips

1. **Always review logs before trading**
   ```bash
   tail -50 logs/technobiz_trader.log
   ```

2. **Paper trade for 1-2 months first**
   - Test all systems
   - Verify analysis quality
   - Confirm trade approvals work

3. **Monitor news calendar**
   - Avoid high-impact events
   - Check: investing.com/economic-calendar

4. **Start with major pairs**
   - EURUSD, GBPUSD (better liquidity)
   - Then expand to exotics

5. **Keep position sizes small initially**
   - Max 0.5 lots when starting
   - Scale up gradually as confidence grows

6. **Review your approvals**
   - Which trades performed well?
   - Which did you correctly reject?
   - Improve your decision criteria

7. **Backup your database**
   ```bash
   pg_dump technobiz_trader > backup.sql
   ```

---

## 📱 Emergency Commands

**Stop everything immediately:**
```bash
# Ctrl+C in terminal
# This stops the agent and closes all connections
```

**Check system status:**
```bash
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"
```

**View recent activity:**
```bash
tail -100 logs/technobiz_trader.log
```

**Close all open trades (in MT5):**
```
Manual: Right-click each trade in MT5 → Close
This is ALWAYS manual - the agent doesn't auto-close
```

---

**Quick Reference v1.0.0**  
**Last Updated:** April 25, 2026  
**Status:** ✅ Ready to Trade
