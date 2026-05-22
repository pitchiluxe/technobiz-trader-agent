"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class OHLCData:
    """OHLC (Open, High, Low, Close) data point."""

    def __init__(
        self,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ):
        self.timestamp = timestamp
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class Candle:
    """Candle data with analysis properties."""

    def __init__(self, ohlc: OHLCData):
        self.ohlc = ohlc
        self.body_size = abs(ohlc.close - ohlc.open)
        self.wick_upper = ohlc.high - max(ohlc.close, ohlc.open)
        self.wick_lower = min(ohlc.close, ohlc.open) - ohlc.low
        self.is_bullish = ohlc.close > ohlc.open
        self.is_bearish = ohlc.close < ohlc.open
        self.is_doji = self.body_size < 0.001  # Adjust threshold as needed


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> List[OHLCData]:
        """
        Get historical candle data.

        Args:
            symbol: Trading pair (e.g., "EURUSD")
            timeframe: Candle timeframe (e.g., "D", "4H", "1H")
            limit: Number of candles to retrieve

        Returns:
            List of OHLCData objects
        """
        pass

    @abstractmethod
    async def get_current_price(self, symbol: str) -> float:
        """
        Get current bid/ask price.

        Args:
            symbol: Trading pair

        Returns:
            Current price
        """
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to market data provider.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from market data provider.

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check connection status.

        Returns:
            True if connected
        """
        pass
