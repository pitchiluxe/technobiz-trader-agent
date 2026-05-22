# TechnobizTrader - AI Trading Agency

**Multi-agent trading system powered by ICT (Inner Circle Trading) methodology**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Framework](https://img.shields.io/badge/Framework-Microsoft%20Agent%20Framework-0078d4)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

---

## 🎯 What is TechnobizTrader?

**TechnobizTrader** is a sophisticated AI-powered trading system that automatically analyzes forex, commodities, crypto, and indices using institutional-grade **ICT (Inner Circle Trading)** methodology. The system operates as a multi-agent orchestration platform where:

1. **Trend-Master** analyzes market structure across multiple timeframes
2. **Analyse-Master** detects precise ICT patterns for trade entry
3. **Trader-Master** executes trades with strict risk management
4. **You** approve every trade before execution (safety-first approach)

### Key Features

✅ **Any Trading Pair** - Analyze EURUSD, GBPJPY, XAUUSD, BTCUSD, or any symbol  
✅ **Automated Analysis** - Trend-Master → Analyse-Master → Trader-Master pipeline  
✅ **User Approval** - Mandatory approval before every trade execution  
✅ **Real Market Data** - Live data from MetaTrader 5  
✅ **ICT Methodology** - Detects Liquidity Sweep, Break of Structure, Imbalance, Pullback  
✅ **Risk Management** - Position sizing (2% max), hard stop loss, tiered take profits  
✅ **Full Transparency** - See all analysis, reasoning, and trade details  
✅ **Database Logging** - Complete trade history and performance metrics  
✅ **Production Ready** - Startup validation, error handling, monitoring

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites

- Python 3.10+
- MetaTrader 5 (download: https://www.metatrader5.com)
- PostgreSQL database
- Azure AI Foundry account (or OpenAI)

### Installation

```bash
# 1. Clone and setup
git clone https://github.com/your-org/TechnobizTrader.git
cd TechnobizTrader
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.template .env
# Edit .env with your MT5 credentials (see MT5_Connect.md)

# 4. Validate setup
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"

# 5. Start trading!
python main.py              # Automated mode
# OR
python interactive_mode.py  # Interactive mode
```

✅ **That's it!** The system will analyze market data and request your approval for trades.

---

## 📖 Documentation - Start Here

**Quick Navigation:**

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ← **START HERE** (5 min read)
2. **[DATA_PROVIDERS.md](DATA_PROVIDERS.md)** - Choose MT5, TradingView, or Hybrid
3. **[MT5_Connect.md](MT5_Connect.md)** - MetaTrader 5 step-by-step setup
4. **[TradingView_Connect.md](TradingView_Connect.md)** - TradingView step-by-step setup
5. **[USER_GUIDE.md](USER_GUIDE.md)** - Comprehensive guide with examples
6. **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Production deployment

**Technical Documentation:**

7. **[AGENTS.md](AGENTS.md)** - Technical agent architecture
8. **[claude.md](claude.md)** - Full system blueprint

---

## � Three Data Provider Options

Choose the best fit for your trading style:

### **Option 1: MT5 (MetaTrader 5)** - Direct Trading Execution
- ✅ Real-time market data
- ✅ Direct trade execution on MT5
- ✅ Simple, single-platform setup
- ❌ Limited technical indicators
- **Best for:** Traders who want simple execution

### **Option 2: TradingView** - Advanced Technical Analysis
- ✅ Best-in-class charting and analysis
- ✅ 100+ technical indicators
- ✅ All markets (stocks, crypto, forex)
- ✅ Huge community and scripts
- ❌ No direct execution
- **Best for:** Analysts and signal generators

### **Option 3: Hybrid (RECOMMENDED)** ⭐ - Best of Both
- ✅ TradingView analysis (excellent indicators)
- ✅ MT5 execution (reliable trading)
- ✅ Real-time data combined
- ✅ All markets explorable
- ⚠️ Requires both accounts
- **Best for:** Professional traders who want everything

**See [DATA_PROVIDERS.md](DATA_PROVIDERS.md) for detailed comparison and setup instructions.**

---

### Automated Mode (main.py)

```bash
python main.py
```

Analyzes configured pairs from `.env` and requests approval for each trade.

### Interactive Mode (interactive_mode.py)

```bash
python interactive_mode.py
```

Menu-driven interface for on-demand pair analysis and trading.

---

## ✅ Trade Approval Flow

```
Market Data → Trend Analysis → Signal Detection
    ↓
╔════════════════════════════════════════════╗
║    APPROVAL GATEWAY (You Decide)           ║
║  Shows: Entry, SL, TPs, Confidence, R/R   ║
║  Your Choice: [A]pprove [R]eject [V]iew   ║
╚════════════════════════════════════════════╝
    ↓ (if approved)
Trade Execution → Database Logging
```

---

## 📊 Architecture

**Three-Agent System:**

```
Market Data (Daily/4H/1H)
    ↓
[TREND-MASTER]  → Identifies market structure
    ↓
[ANALYSE-MASTER] → Detects ICT patterns
    ↓
[USER APPROVAL]  → You approve/reject
    ↓
[TRADER-MASTER]  → Executes on MT5
    ↓
Database & Logs
```

---

## 🔧 Quick Configuration

**.env essentials:**

```env
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=ICMarkets-Demo
ACCOUNT_BALANCE=50000
TRADING_PAIRS=EURUSD,GBPUSD,XAUUSD
DATABASE_URL=postgresql://user:pass@host/technobiz
```

**Validate:**

```bash
python -c "from utils.startup_validator import StartupValidator; \
           StartupValidator.full_startup_check()"
```

---

## 📈 Supported Trading Pairs

**Forex:** EURUSD, GBPUSD, USDJPY, EURGBP, EURJPY, GBPJPY, etc.  
**Commodities:** XAUUSD, XAGUSD, WTIUSD  
**Crypto:** BTCUSD, ETHUSD, LTCUSD  
**Indices:** US500, US100, DAX40, FTSE100

---

## 🔐 Security

✅ Keep .env private (add to .gitignore)  
✅ Never commit credentials to Git  
✅ Use strong passwords (20+ chars)  
✅ Rotate API keys quarterly  
✅ Enable 2FA on MT5 if available

---

## ⚖️ Risk Disclaimer

**TechnobizTrader** is an AI-powered trading system for **educational purposes**.

⚠️ Trading involves substantial risk of loss. Always:
- Trade with capital you can afford to lose
- Start with demo account for 1-2 months
- Monitor the system daily
- Never trade money you can't afford to lose

---

## 💡 Next Steps

1. **Read:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
2. **Setup:** [MT5_Connect.md](MT5_Connect.md) (20 min)
3. **Test:** Run `python main.py` on demo account (10 min)
4. **Learn:** Review [USER_GUIDE.md](USER_GUIDE.md) (30 min)
5. **Practice:** Paper trade for 1-2 weeks

---

## 📞 Support

| Need | Resource |
|------|----------|
| Quick Commands | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| User Guide | [USER_GUIDE.md](USER_GUIDE.md) |
| MT5 Setup | [MT5_Connect.md](MT5_Connect.md) |
| Deployment | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| Troubleshooting | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Technical Details | [AGENTS.md](AGENTS.md) |

---

**Version:** 1.0.0 • **Status:** ✅ Production Ready • **Last Updated:** April 25, 2026
