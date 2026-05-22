# Setup and Installation Guide

## System Requirements

- **Python**: 3.10 or higher
- **OS**: Windows, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 2GB for dependencies and logs

## Installation Steps

### 1. Clone/Download Repository
```bash
git clone https://github.com/yourusername/technobiz-trader.git
cd technobiz-trader
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.template .env
# Edit .env with your settings
```

### 5. Database Setup
```bash
# For SQLite (default) - no setup needed
# For PostgreSQL - create database first
createdb technobiz_trader

# Initialize tables
python -c "from database.db_manager import db_manager; db_manager.create_tables()"
```

### 6. Verify Installation
```bash
pytest tests/ -v
```

## Configuration Guide

### Market Data Providers

#### MetaTrader 5
1. Install MT5 Terminal
2. Create/login to trading account
3. Get account credentials
4. Add to `.env`:
   ```
   MT5_ACCOUNT=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=MetaQuotes-Demo
   ```

#### Alpaca (Alternative for US Equities)
1. Create Alpaca account at alpaca.markets
2. Generate API keys
3. Add to `.env`:
   ```
   ALPACA_API_KEY=your_api_key
   ALPACA_SECRET_KEY=your_secret_key
   ```

### Azure AI Foundry Configuration
1. Create Azure account (if not already)
2. Set up AI Foundry project
3. Create model deployment
4. Add to `.env`:
   ```
   FOUNDRY_PROJECT_ENDPOINT=https://your-project.azure.ai.com
   FOUNDRY_MODEL_DEPLOYMENT_NAME=your-model
   FOUNDRY_API_KEY=your_api_key
   ```

### Database Configuration

#### SQLite (Development)
```
DATABASE_URL=sqlite:///./technobiz_trader.db
```

#### PostgreSQL (Production)
```
DATABASE_URL=postgresql://user:password@localhost:5432/technobiz_trader
```

Install PostgreSQL adapter:
```bash
pip install psycopg2-binary
```

## Running the Application

### Basic Execution
```bash
python main.py
```

### With Debug Logging
```bash
DEBUG=True python main.py
```

### Docker Deployment
```bash
docker-compose up --build
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_workflow.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=agents --cov=config --cov-report=html
```

## Development Workflow

### Code Formatting
```bash
black .
isort .
```

### Code Linting
```bash
pylint agents/ config/ market_data/ utils/
```

### Create New Agent Module
1. Create folder under `agents/your_agent_name/`
2. Add `__init__.py` and agent implementation
3. Inherit from `BaseAgent` class
4. Implement `analyze()` method
5. Add tests in `tests/`

## Troubleshooting

### MT5 Connection Issues
- Ensure MT5 terminal is running
- Verify account credentials are correct
- Check server name matches your broker

### Database Errors
- For SQLite: Check file permissions in logs directory
- For PostgreSQL: Verify connection string and database exists
- Run `db_manager.create_tables()` to initialize schema

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version is 3.10+

### Permission Denied (Linux/macOS)
```bash
chmod +x main.py
python main.py
```

## Performance Tuning

### Optimize Database
```python
# Use PostgreSQL instead of SQLite for production
# Add indexing to frequently queried columns
# Monitor log file size and implement rotation
```

### Improve Analysis Speed
```python
# Cache market data locally
# Reduce number of analyzed timeframes if needed
# Use async/await for concurrent operations
```

## Next Steps

1. Read [ICT_METHODOLOGY.md](./ICT_METHODOLOGY.md) for strategy details
2. Review [API_REFERENCE.md](./API_REFERENCE.md) for agent interfaces
3. Check test examples in `tests/` directory
4. Review logs in `logs/` directory for debugging
5. Backtest with historical data before live trading

---

For additional help, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
