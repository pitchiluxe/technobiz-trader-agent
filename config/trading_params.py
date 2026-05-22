"""Trading parameters and constants."""

from enum import Enum
from typing import List


class Timeframe(Enum):
    """Supported trading timeframes."""
    
    DAILY = "D"
    FOUR_HOUR = "4H"
    ONE_HOUR = "1H"
    FIFTEEN_MIN = "15M"
    FIVE_MIN = "5M"


class TrendType(Enum):
    """Market trend types."""
    
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    RANGING = "RANGING"
    NEUTRAL = "NEUTRAL"


class Signal(Enum):
    """Trade signal types."""
    
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TradeStatus(Enum):
    """Trade execution status."""
    
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class ExitReason(Enum):
    """Reasons for trade exit."""
    
    TP_HIT = "TP_HIT"
    SL_HIT = "SL_HIT"
    MANUAL_CLOSE = "MANUAL_CLOSE"
    TIMEOUT = "TIMEOUT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class TradingParams:
    """Trading parameters and constraints."""

    # Analysis timeframes (minimum)
    ANALYSIS_TIMEFRAMES: List[Timeframe] = [
        Timeframe.DAILY,
        Timeframe.FOUR_HOUR,
        Timeframe.ONE_HOUR,
    ]

    # ICT Elements
    ICT_ELEMENTS = ["liquidity_sweep", "break_of_structure", "imbalance", "pullback"]
    REQUIRED_ICT_ELEMENTS = 4

    # Kill Zone
    KILL_ZONE_DURATION_MIN = 15
    KILL_ZONE_DURATION_MAX = 30

    # Risk Management
    MAX_CONCURRENT_TRADES = 3
    MAX_RISK_PER_TRADE = 0.02  # 2%
    MIN_RISK_REWARD_RATIO = 2.0  # 1:2
    MAX_DAILY_DRAWDOWN = 0.05  # 5%
    MIN_CONFIDENCE_THRESHOLD = 75.0

    # Signal Validation
    SIGNAL_VALIDITY_MINUTES = 30
    MIN_CONFLUENCE_TIMEFRAMES = 2

    # Entry Execution
    ENTRY_TIMEOUT_MINUTES = 5
    MAX_SLIPPAGE_PIPS = 2
    MIN_WIN_RATE = 0.40  # 40%

    # Position Sizing
    POSITION_SIZE_MULTIPLIER = 1.0
