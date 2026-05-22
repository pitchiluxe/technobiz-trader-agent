"""
Trading Pairs Configuration & Management

Supports any forex, crypto, commodity, or stock pairs with dynamic configuration.
"""

from typing import List, Dict, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AssetClass(Enum):
    """Supported asset classes."""

    FOREX = "FOREX"           # Currency pairs: EURUSD, GBPUSD, etc.
    CRYPTO = "CRYPTO"         # Cryptocurrencies: BTCUSD, ETHUSD, etc.
    COMMODITIES = "COMMODITIES"  # Oil, Gold, Silver, etc.
    INDICES = "INDICES"       # Stock indices: SPX500, DAX40, etc.
    STOCKS = "STOCKS"         # Individual stocks


class TradingPair:
    """Represents a tradeable pair with metadata."""

    def __init__(
        self,
        symbol: str,
        asset_class: AssetClass,
        pip_value: float = 0.0001,
        min_lot_size: float = 0.01,
        max_lot_size: float = 100.0,
        description: str = "",
    ):
        """
        Initialize a trading pair.

        Args:
            symbol: Pair symbol (e.g., "EURUSD")
            asset_class: Type of asset
            pip_value: Price of one pip (0.0001 for most forex)
            min_lot_size: Minimum lot size for orders
            max_lot_size: Maximum lot size for orders
            description: User-friendly description
        """
        self.symbol = symbol.upper()
        self.asset_class = asset_class
        self.pip_value = pip_value
        self.min_lot_size = min_lot_size
        self.max_lot_size = max_lot_size
        self.description = description or f"{symbol} trading pair"

    def __repr__(self) -> str:
        return f"TradingPair({self.symbol} | {self.asset_class.value})"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'asset_class': self.asset_class.value,
            'pip_value': self.pip_value,
            'min_lot_size': self.min_lot_size,
            'max_lot_size': self.max_lot_size,
            'description': self.description,
        }


class TradingPairsRegistry:
    """Registry of supported trading pairs."""

    # ─────────────────────────────────────────────────────────────
    # MAJOR FOREX PAIRS
    # ─────────────────────────────────────────────────────────────

    EURUSD = TradingPair(
        "EURUSD",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Euro vs US Dollar (most liquid forex pair)",
    )

    GBPUSD = TradingPair(
        "GBPUSD",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="British Pound vs US Dollar",
    )

    USDJPY = TradingPair(
        "USDJPY",
        AssetClass.FOREX,
        pip_value=0.01,  # Yen pairs have different pip value
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="US Dollar vs Japanese Yen",
    )

    AUDUSD = TradingPair(
        "AUDUSD",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Australian Dollar vs US Dollar",
    )

    USDCHF = TradingPair(
        "USDCHF",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="US Dollar vs Swiss Franc",
    )

    NZDUSD = TradingPair(
        "NZDUSD",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="New Zealand Dollar vs US Dollar",
    )

    # ─────────────────────────────────────────────────────────────
    # CROSS PAIRS
    # ─────────────────────────────────────────────────────────────

    EURGBP = TradingPair(
        "EURGBP",
        AssetClass.FOREX,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Euro vs British Pound",
    )

    EURJPY = TradingPair(
        "EURJPY",
        AssetClass.FOREX,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Euro vs Japanese Yen",
    )

    GBPJPY = TradingPair(
        "GBPJPY",
        AssetClass.FOREX,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="British Pound vs Japanese Yen",
    )

    AUDJPY = TradingPair(
        "AUDJPY",
        AssetClass.FOREX,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Australian Dollar vs Japanese Yen",
    )

    # ─────────────────────────────────────────────────────────────
    # COMMODITIES
    # ─────────────────────────────────────────────────────────────

    GOLD = TradingPair(
        "XAUUSD",
        AssetClass.COMMODITIES,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Gold vs US Dollar",
    )

    OIL_WTI = TradingPair(
        "WTIUSD",
        AssetClass.COMMODITIES,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="WTI Crude Oil vs US Dollar",
    )

    OIL_BRENT = TradingPair(
        "BRENTUSD",
        AssetClass.COMMODITIES,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Brent Crude Oil vs US Dollar",
    )

    SILVER = TradingPair(
        "XAGUSD",
        AssetClass.COMMODITIES,
        pip_value=0.0001,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Silver vs US Dollar",
    )

    # ─────────────────────────────────────────────────────────────
    # CRYPTOCURRENCIES
    # ─────────────────────────────────────────────────────────────

    BITCOIN = TradingPair(
        "BTCUSD",
        AssetClass.CRYPTO,
        pip_value=0.01,
        min_lot_size=0.001,
        max_lot_size=10.0,
        description="Bitcoin vs US Dollar",
    )

    ETHEREUM = TradingPair(
        "ETHUSD",
        AssetClass.CRYPTO,
        pip_value=0.01,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="Ethereum vs US Dollar",
    )

    # ─────────────────────────────────────────────────────────────
    # INDICES
    # ─────────────────────────────────────────────────────────────

    SP500 = TradingPair(
        "SPX500",
        AssetClass.INDICES,
        pip_value=0.1,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="S&P 500 Index",
    )

    DAX = TradingPair(
        "DAX40",
        AssetClass.INDICES,
        pip_value=0.1,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="German DAX 40 Index",
    )

    FTSE = TradingPair(
        "FTSE100",
        AssetClass.INDICES,
        pip_value=0.1,
        min_lot_size=0.01,
        max_lot_size=100.0,
        description="UK FTSE 100 Index",
    )

    def __init__(self):
        """Initialize registry of supported pairs."""
        self._custom_pairs: Dict[str, TradingPair] = {}
        self._active_pairs: Set[str] = set()

        logger.info("[PAIRS] Trading Pairs Registry initialized")

    def register_custom_pair(
        self,
        symbol: str,
        asset_class: AssetClass,
        pip_value: float = 0.0001,
        min_lot_size: float = 0.01,
        max_lot_size: float = 100.0,
        description: str = "",
    ) -> TradingPair:
        """
        Register a custom trading pair not in the default registry.

        Args:
            symbol: Pair symbol (e.g., "CUSTOMUSD")
            asset_class: Type of asset
            pip_value: Price of one pip
            min_lot_size: Minimum lot size
            max_lot_size: Maximum lot size
            description: Description

        Returns:
            Registered TradingPair
        """
        pair = TradingPair(
            symbol=symbol,
            asset_class=asset_class,
            pip_value=pip_value,
            min_lot_size=min_lot_size,
            max_lot_size=max_lot_size,
            description=description,
        )
        self._custom_pairs[symbol.upper()] = pair
        logger.info(f"[PAIRS] Registered custom pair: {pair}")
        return pair

    def get_pair(self, symbol: str) -> Optional[TradingPair]:
        """Get a trading pair by symbol."""
        symbol = symbol.upper()

        # Check custom pairs first
        if symbol in self._custom_pairs:
            return self._custom_pairs[symbol]

        # Check built-in pairs
        if hasattr(self, symbol):
            return getattr(self, symbol)

        logger.warning(f"[PAIRS] Pair not found: {symbol}")
        return None

    def set_active_pairs(self, symbols: List[str]) -> bool:
        """
        Set active trading pairs for this session.

        Args:
            symbols: List of pair symbols to trade

        Returns:
            True if all pairs are valid, False otherwise
        """
        self._active_pairs.clear()
        invalid_pairs = []

        for symbol in symbols:
            pair = self.get_pair(symbol)
            if pair:
                self._active_pairs.add(pair.symbol)
            else:
                invalid_pairs.append(symbol)

        if invalid_pairs:
            logger.error(f"[PAIRS] Invalid pairs: {', '.join(invalid_pairs)}")
            return False

        logger.info(f"[PAIRS] Active pairs set: {', '.join(self._active_pairs)}")
        return True

    def get_active_pairs(self) -> List[TradingPair]:
        """Get list of active trading pairs."""
        return [
            self.get_pair(symbol) for symbol in self._active_pairs
            if self.get_pair(symbol) is not None
        ]

    def get_pairs_by_asset_class(self, asset_class: AssetClass) -> List[TradingPair]:
        """Get all pairs of a specific asset class."""
        pairs = []

        # Check built-in pairs
        for name in dir(self):
            attr = getattr(self, name)
            if isinstance(attr, TradingPair) and attr.asset_class == asset_class:
                pairs.append(attr)

        # Check custom pairs
        for pair in self._custom_pairs.values():
            if pair.asset_class == asset_class:
                pairs.append(pair)

        return pairs

    def list_all_pairs(self) -> List[TradingPair]:
        """List all available pairs."""
        pairs = []

        # Collect built-in pairs
        for name in dir(self):
            if name.startswith('_'):
                continue
            attr = getattr(self, name)
            if isinstance(attr, TradingPair):
                pairs.append(attr)

        # Add custom pairs
        pairs.extend(self._custom_pairs.values())

        return sorted(pairs, key=lambda p: p.symbol)


# Global registry instance
pairs_registry = TradingPairsRegistry()
