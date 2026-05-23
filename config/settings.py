"""Environment settings and configuration."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent  # project / backend root
load_dotenv(override=False)
load_dotenv(str(_ROOT / ".env.local"), override=True)  # AI config (OpenRouter / Ollama)
# Also honour a userData override (set by Electron's TECHNOBIZ_USERDATA)
_userdata_env = os.getenv("TECHNOBIZ_USERDATA", "")
if _userdata_env:
    load_dotenv(os.path.join(_userdata_env, ".env.local"), override=True)

_log = logging.getLogger(__name__)


class Settings:
    """Application settings from environment variables."""

    # Application
    APP_NAME = "TechnobizTrader"
    APP_VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
    DEBUG = ENVIRONMENT != "production" and os.getenv("DEBUG", "False").lower() == "true"

    # AI Provider — openrouter | claude | ollama
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter").lower()

    # AI Configuration — OpenRouter / Anthropic direct
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")           # e.g. https://openrouter.ai/api
    ANTHROPIC_AUTH_TOKEN = (
        os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY", "")
    )
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Ollama (local) configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

    # Foundry/AI Configuration (legacy — kept for backwards compatibility)
    FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", "")
    FOUNDRY_MODEL_DEPLOYMENT_NAME = os.getenv("FOUNDRY_MODEL_DEPLOYMENT_NAME", "")
    FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY", "")

    # Data Provider Selection (mt5, tradingview, or hybrid)
    DATA_PROVIDER = os.getenv("DATA_PROVIDER", "mt5").lower()
    if DATA_PROVIDER not in ["mt5", "tradingview", "hybrid"]:
        _log.warning(
            "Invalid DATA_PROVIDER '%s' — defaulting to 'mt5'. "
            "Set DATA_PROVIDER=mt5|tradingview|hybrid in your .env file.",
            DATA_PROVIDER,
        )
        DATA_PROVIDER = "mt5"

    # TradingView Configuration (Optional, if using TradingView provider)
    TRADINGVIEW_API_TYPE = os.getenv("TRADINGVIEW_API_TYPE", "free").lower()
    TRADINGVIEW_EXCHANGE = os.getenv("TRADINGVIEW_EXCHANGE", "FOREX")

    # Market Data (MT5 - Optional if using TradingView)
    MT5_ACCOUNT = os.getenv("MT5_ACCOUNT", "")
    MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER = os.getenv("MT5_SERVER", "")

    # Market Data (MT4 — uses same MT5 Python library via broker bridge)
    MT4_ACCOUNT = os.getenv("MT4_ACCOUNT", "")
    MT4_PASSWORD = os.getenv("MT4_PASSWORD", "")
    MT4_SERVER = os.getenv("MT4_SERVER", "")

    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")

    # Trading Parameters
    TRADING_PAIRS = os.getenv("TRADING_PAIRS", "EURUSD,GBPUSD").split(",")
    MAX_CONCURRENT_TRADES = int(os.getenv("MAX_CONCURRENT_TRADES", "3"))
    MAX_RISK_PER_TRADE = float(os.getenv("MAX_RISK_PER_TRADE", "0.02"))
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "75"))
    ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "0.0"))

    # Database — default to SQLite in userData so the app works with no config
    _userdata_db = os.getenv("TECHNOBIZ_USERDATA", "")
    _default_db  = (
        f"sqlite:///{os.path.join(_userdata_db, 'technobiz.db')}"
        if _userdata_db else "sqlite:///technobiz.db"
    )
    DATABASE_URL = os.getenv("DATABASE_URL", _default_db)
    SQLALCHEMY_ECHO = DEBUG and ENVIRONMENT == "development"

    # SQLite is allowed in all environments for this desktop app.
    # For cloud/server deployments, set DATABASE_URL to a PostgreSQL connection string.
    if ENVIRONMENT == "production" and DATABASE_URL.startswith("sqlite"):
        _log.warning(
            "Running in production with SQLite. For cloud deployments, "
            "set DATABASE_URL to a PostgreSQL connection string."
        )

    # Logging — write to writable userData dir when installed, else local logs/
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    _userdata = os.getenv("TECHNOBIZ_USERDATA", "")
    LOG_FILE = os.getenv(
        "LOG_FILE",
        os.path.join(_userdata, "technobiz_trader.log") if _userdata else "logs/technobiz_trader.log"
    )

    # Notification
    ENABLE_EMAIL_NOTIFICATIONS = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "False").lower() == "true"
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
    ENABLE_TELEGRAM_NOTIFICATIONS = os.getenv("ENABLE_TELEGRAM_NOTIFICATIONS", "False").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Agent conversation recaps
    ENABLE_RECAPS = os.getenv("ENABLE_RECAPS", "False").lower() == "true"


settings = Settings()
