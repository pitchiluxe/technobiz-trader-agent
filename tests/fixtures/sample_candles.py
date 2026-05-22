"""Sample fixtures and test data."""

from datetime import datetime
from market_data.data_provider import OHLCData


def sample_ohlc_data():
    """Generate sample OHLC data for testing."""
    return [
        OHLCData(
            timestamp=datetime(2024, 4, 1, 0, 0),
            open_price=1.0500,
            high_price=1.0520,
            low_price=1.0490,
            close_price=1.0510,
            volume=1000000.0,
        ),
        OHLCData(
            timestamp=datetime(2024, 4, 1, 4, 0),
            open_price=1.0510,
            high_price=1.0550,
            low_price=1.0500,
            close_price=1.0540,
            volume=1200000.0,
        ),
        OHLCData(
            timestamp=datetime(2024, 4, 1, 8, 0),
            open_price=1.0540,
            high_price=1.0580,
            low_price=1.0520,
            close_price=1.0560,
            volume=1100000.0,
        ),
    ]


def sample_trend_report():
    """Generate sample trend report for testing."""
    return {
        "bias": "BULLISH",
        "confidence": 80.0,
        "timeframes_analyzed": ["D", "4H", "1H"],
        "support_resistance": {
            "support_levels": [1.0450, 1.0400],
            "resistance_levels": [1.0600, 1.0650],
        },
        "swing_structure": {
            "recent_higher_lows": True,
            "recent_lower_highs": False,
        },
        "liquidity_levels": [1.0500, 1.0600],
        "risk_level": "MEDIUM",
        "timestamp": datetime.now().isoformat(),
    }


def sample_trade_signal():
    """Generate sample trade signal for testing."""
    return {
        "entry_level": 1.0530,
        "stop_loss": 1.0480,
        "take_profit_1": 1.0580,
        "take_profit_2": 1.0630,
        "take_profit_3": 1.0680,
        "risk_reward_ratio": 2.5,
        "confidence": 82.0,
        "pattern_elements": {
            "liquidity_sweep": True,
            "break_of_structure": True,
            "imbalance": True,
            "pullback": True,
        },
        "kill_zone_start": datetime.now().isoformat(),
        "kill_zone_end": datetime.now().isoformat(),
    }
