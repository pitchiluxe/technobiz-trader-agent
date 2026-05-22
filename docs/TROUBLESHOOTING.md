# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Python Module Not Found

**Error**: `ModuleNotFoundError: No module named 'agents'`

**Solution**:
1. Ensure you're in the project root directory
2. Verify virtual environment is activated
3. Check Python path includes project root:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # macOS/Linux
   set PYTHONPATH=%PYTHONPATH%;%cd%           # Windows
   ```

---

### Issue: MT5 Connection Fails

**Error**: `MT5 connection error: Failed to initialize`

**Solution**:
1. Ensure MetaTrader 5 terminal is running and logged in
2. Verify account credentials in `.env`:
   ```
   MT5_ACCOUNT=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=MetaQuotes-Demo  # or your broker's server
   ```
3. Test connection manually in MT5 terminal first
4. Check firewall isn't blocking connections

---

### Issue: Database File Locked

**Error**: `database is locked` or `unable to open database file`

**Solution**:
1. Ensure only one instance is running
2. For SQLite, close the database gracefully:
   ```bash
   # Kill any lingering Python processes
   pkill -f main.py  # macOS/Linux
   taskkill /f /im python.exe  # Windows
   ```
3. Delete corrupted database:
   ```bash
   rm technobiz_trader.db
   python -c "from database.db_manager import db_manager; db_manager.create_tables()"
   ```

---

### Issue: PostgreSQL Connection Refused

**Error**: `connection refused` or `could not connect to server`

**Solution**:
1. Verify PostgreSQL is running:
   ```bash
   # macOS
   brew services list | grep postgres
   
   # Linux
   sudo systemctl status postgresql
   ```
2. Check connection string format:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/technobiz_trader
   ```
3. Verify database exists:
   ```bash
   createdb technobiz_trader
   ```
4. Test connection:
   ```bash
   psql postgresql://user:password@localhost:5432/technobiz_trader
   ```

---

### Issue: Foundry/Azure AI Authentication Failed

**Error**: `Authentication failed` or `Invalid credentials`

**Solution**:
1. Verify Azure credentials are set:
   ```bash
   az login
   ```
2. Check `.env` variables:
   - `FOUNDRY_PROJECT_ENDPOINT` - Full URL
   - `FOUNDRY_MODEL_DEPLOYMENT_NAME` - Exact name
   - `FOUNDRY_API_KEY` - Valid key from Azure Portal
3. Test endpoint connectivity:
   ```bash
   curl -X GET https://your-endpoint/health
   ```

---

### Issue: Insufficient Memory During Analysis

**Error**: `MemoryError` or application becomes slow

**Solution**:
1. Reduce number of candles analyzed:
   ```python
   # In config/trading_params.py
   CANDLES_PER_TIMEFRAME = 100  # Reduce from 500
   ```
2. Reduce concurrent trades:
   ```
   MAX_CONCURRENT_TRADES=1
   ```
3. Clear logs periodically:
   ```bash
   rm logs/*.log
   ```
4. Monitor memory usage:
   ```bash
   # macOS/Linux
   top -p $(pgrep -f main.py)
   
   # Windows
   tasklist | find "python"
   ```

---

### Issue: Trades Not Executing

**Problem**: Agent generates signals but no trades execute

**Diagnosis**:
1. Check signal confidence: Must be ≥ 75%
   ```python
   logger.debug(f"Signal confidence: {signal.confidence}")
   ```
2. Verify account balance and risk constraints:
   ```python
   # Check logs for: "Portfolio risk exceeds limit"
   ```
3. Check market hours - may be in closed market
4. Verify kill zone hasn't expired

**Solution**:
1. Increase `MIN_CONFIDENCE_THRESHOLD` if needed
2. Check account funding
3. Verify trading hours for chosen pairs
4. Add logging to understand why signal rejected

---

### Issue: Tests Fail with Async Errors

**Error**: `RuntimeError: Event loop is closed`

**Solution**:
1. Ensure pytest-asyncio is installed:
   ```bash
   pip install pytest-asyncio
   ```
2. Run tests with proper markers:
   ```bash
   pytest tests/ -v --asyncio-mode=auto
   ```
3. Check test structure includes `@pytest.mark.asyncio`

---

### Issue: High Slippage on Entries

**Problem**: Actual entry price far from signal price

**Solution**:
1. Check entry execution method:
   - Use limit orders instead of market orders
   - Adjust `ENTRY_TIMEOUT_MINUTES` if too short
2. Verify liquidity at entry level:
   ```python
   # Check bid-ask spread in logs
   ```
3. Reduce position size to improve fill:
   ```
   MAX_RISK_PER_TRADE=0.01  # Reduce to 1%
   ```
4. Trade during peak liquidity hours only

---

### Issue: Logs Not Being Created

**Error**: No log files in `logs/` directory

**Solution**:
1. Create logs directory:
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```
2. Verify `LOG_FILE` path in `.env`:
   ```
   LOG_FILE=logs/technobiz_trader.log
   ```
3. Check file permissions:
   ```bash
   chmod 666 logs/*  # macOS/Linux
   ```

---

### Issue: Signal False Rate Too High

**Problem**: Too many losing trades

**Diagnosis**:
1. Review pattern confirmation in logs
2. Check if all ICT elements are truly confirmed
3. Analyze recent trades for issues

**Solutions**:
1. Increase minimum confidence threshold:
   ```
   MIN_CONFIDENCE_THRESHOLD=80
   ```
2. Require more timeframe confluence:
   ```python
   MIN_CONFLUENCE_TIMEFRAMES=3  # Require 3 instead of 2
   ```
3. Add additional filters:
   - Volume profile confirmation
   - Volatility checks (ATR)
   - News event avoidance

---

### Issue: Docker Container Won't Start

**Error**: `docker-compose up` fails

**Solution**:
1. Check logs:
   ```bash
   docker-compose logs technobiz-trader
   ```
2. Verify Docker is running:
   ```bash
   docker ps
   ```
3. Rebuild container:
   ```bash
   docker-compose down
   docker-compose up --build
   ```
4. Check `.env` variables are accessible:
   ```bash
   cat .env  # Ensure file exists and is readable
   ```

---

## Debugging Tips

### Enable Debug Logging
```bash
DEBUG=True LOG_LEVEL=DEBUG python main.py
```

### Add Breakpoints (Python Debugger)
```python
# In your code
import pdb
pdb.set_trace()

# Run with debugger
python -m pdb main.py
```

### Monitor Live Execution
```bash
# Watch logs in real-time
tail -f logs/technobiz_trader.log

# Watch database changes
sqlite3 technobiz_trader.db "SELECT * FROM trade_executions;"
```

### Performance Profiling
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... run code ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## Support Resources

- **Documentation**: See `/docs` folder
- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md)
- **Setup Guide**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **ICT Methodology**: [ICT_METHODOLOGY.md](./ICT_METHODOLOGY.md)

---

For additional help, please check the project repository or contact support.
