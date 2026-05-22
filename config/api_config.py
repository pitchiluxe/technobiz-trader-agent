"""API configuration for market data providers."""

from enum import Enum


class DataProvider(Enum):
    """Supported market data providers."""
    
    METATRADER5 = "mt5"
    ALPACA = "alpaca"


class APIConfig:
    """API configuration for different providers."""

    MT5_CONFIG = {
        "timeout": 30,
        "max_retries": 3,
        "reconnect_interval": 5,  # seconds
    }

    ALPACA_CONFIG = {
        "base_url": "https://api.alpaca.markets",
        "timeout": 30,
        "max_retries": 3,
    }

    # Default provider
    DEFAULT_PROVIDER = DataProvider.METATRADER5
