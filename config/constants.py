"""
Instrument-specific trading constants.

All magic numbers that vary per instrument must come from here.
Never hardcode PIP_SIZE, SL_BUFFER, or impulse thresholds in agent code.
"""

from __future__ import annotations
from typing import Any, Dict

# ── Instrument Specifications ──────────────────────────────────────────────────
# pip_size           : Price increment representing one pip
# pip_value_per_lot  : USD value per pip per standard lot
# pip_threshold      : Minimum wick extension to confirm a sweep
# sl_buffer          : Extra price distance beyond zone edge for stop loss
# min_fvg_pips       : Minimum FVG size in pips (filters noise)
# min_impulse_factor : Minimum impulse as fraction of ATR(14)

INSTRUMENT_SPECS: Dict[str, Dict[str, Any]] = {
    "EURUSD": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 10.0,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0003,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "GBPUSD": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 10.0,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0004,
        "min_fvg_pips": 4,
        "min_impulse_factor": 0.25,
    },
    "USDJPY": {
        "pip_size": 0.01,
        "pip_value_per_lot": 9.0,
        "pip_threshold": 0.02,
        "sl_buffer": 0.03,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "GBPJPY": {
        "pip_size": 0.01,
        "pip_value_per_lot": 9.0,
        "pip_threshold": 0.03,
        "sl_buffer": 0.05,
        "min_fvg_pips": 5,
        "min_impulse_factor": 0.30,
    },
    "EURJPY": {
        "pip_size": 0.01,
        "pip_value_per_lot": 9.0,
        "pip_threshold": 0.02,
        "sl_buffer": 0.04,
        "min_fvg_pips": 4,
        "min_impulse_factor": 0.25,
    },
    "AUDUSD": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 10.0,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0003,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "USDCAD": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 7.5,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0003,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "NZDUSD": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 10.0,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0003,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "USDCHF": {
        "pip_size": 0.0001,
        "pip_value_per_lot": 10.0,
        "pip_threshold": 0.0002,
        "sl_buffer": 0.0003,
        "min_fvg_pips": 3,
        "min_impulse_factor": 0.25,
    },
    "XAUUSD": {
        "pip_size": 0.01,
        "pip_value_per_lot": 1.0,
        "pip_threshold": 0.50,
        "sl_buffer": 0.50,
        "min_fvg_pips": 30,
        "min_impulse_factor": 0.40,
    },
    "BTCUSD": {
        "pip_size": 1.0,
        "pip_value_per_lot": 1.0,
        "pip_threshold": 5.0,
        "sl_buffer": 10.0,
        "min_fvg_pips": 100,
        "min_impulse_factor": 0.50,
    },
    "NASDAQ": {
        "pip_size": 0.01,
        "pip_value_per_lot": 1.0,
        "pip_threshold": 0.50,
        "sl_buffer": 1.0,
        "min_fvg_pips": 10,
        "min_impulse_factor": 0.40,
    },
    "US30": {
        "pip_size": 0.01,
        "pip_value_per_lot": 1.0,
        "pip_threshold": 1.0,
        "sl_buffer": 2.0,
        "min_fvg_pips": 20,
        "min_impulse_factor": 0.40,
    },
}

DEFAULT_SPECS: Dict[str, Any] = {
    "pip_size": 0.0001,
    "pip_value_per_lot": 10.0,
    "pip_threshold": 0.0002,
    "sl_buffer": 0.0003,
    "min_fvg_pips": 3,
    "min_impulse_factor": 0.25,
}


def get_instrument_spec(symbol: str) -> Dict[str, Any]:
    """Return instrument specification, falling back to defaults for unknown symbols."""
    sym = symbol.strip().upper()
    if sym in INSTRUMENT_SPECS:
        return INSTRUMENT_SPECS[sym]
    # Try prefix match (e.g. "EURUSDm" → "EURUSD")
    for key in INSTRUMENT_SPECS:
        if sym.startswith(key) or key.startswith(sym[:6]):
            return INSTRUMENT_SPECS[key]
    return DEFAULT_SPECS


# ── Swing Detection Windows (candles, per timeframe) ──────────────────────────
SWING_WINDOWS: Dict[str, int] = {
    "W":   12,
    "D":   10,
    "4H":   8,
    "1H":   5,
    "15M":  3,
    "5M":   2,
    "1M":   2,
}
DEFAULT_SWING_WINDOW = 5

# ── Order Block Detection ──────────────────────────────────────────────────────
OB_LOOKBACK_CANDLES   = 30     # candles to scan backwards for a fresh OB
OB_LOOKBACK_BREAKER   = 60     # extended for breaker block (older OBs)
OB_PERSISTENCE_HOURS  = 168    # persisted OB expires after 7 days

# ── Kill Zone Windows (UTC hour, inclusive start / exclusive end) ──────────────
KILL_ZONES_UTC: Dict[str, tuple] = {
    "asian":    (0,  8),       # 00:00–08:00 UTC  (accumulation / ASR build)
    "london":   (8,  11),      # 08:00–11:00 UTC  (manipulation + direction set)
    "new_york": (13, 16),      # 13:00–16:00 UTC  (continuation or reversal)
}
ACTIVE_KILL_ZONES = ("london", "new_york")  # sessions where signals are generated

# ── Risk Management ────────────────────────────────────────────────────────────
MAX_RISK_PER_TRADE     = 0.02   # 2% of account per trade
MAX_DAILY_DRAWDOWN     = 0.05   # 5% daily drawdown triggers trading pause
MAX_CONCURRENT_TRADES  = 3      # maximum open positions simultaneously
MIN_RR_RATIO           = 2.0    # 1:2 minimum risk-to-reward ratio
MIN_CONFIDENCE_PCT     = 75.0   # minimum signal confidence to execute
CONSECUTIVE_LOSS_LIMIT = 3      # losses before position size reduction kicks in
SIZE_REDUCTION_FACTOR  = 0.50   # multiply lots by this after CONSECUTIVE_LOSS_LIMIT
SIZE_REDUCTION_TRADES  = 5      # number of reduced-size trades before resetting

# ── ATR / Volatility ───────────────────────────────────────────────────────────
ATR_PERIOD          = 14        # ATR period for current session volatility
ATR_LONG_PERIOD     = 84        # 84 1H candles ≈ 1 trading week
HIGH_VOL_MULTIPLIER = 1.5       # ATR ratio above which market is "high volatility"

# ── Signal Timing ─────────────────────────────────────────────────────────────
SIGNAL_EXPIRY_MINUTES  = 30     # signal valid for 30 min from kill zone start
ENTRY_TIMEOUT_MINUTES  = 5      # cancel unfilled limit order after 5 min
MIN_HOLD_MINUTES       = 5      # minimum position hold time
LOWER_TF_LOOKBACK      = 12     # LTF candles to scan for confirmation candle

# ── Staleness Check ────────────────────────────────────────────────────────────
CANDLE_MAX_AGE_FACTOR = 2.5     # newest candle must be < TF_minutes * factor old
TIMEFRAME_MINUTES: Dict[str, int] = {
    "W":   10080,
    "D":   1440,
    "4H":  240,
    "1H":  60,
    "15M": 15,
    "5M":  5,
    "1M":  1,
}

# ── Reconnection Back-off ──────────────────────────────────────────────────────
RECONNECT_DELAYS = [5, 10, 30, 60, 300]    # seconds; exponential back-off steps

# ── Asian Session Range ────────────────────────────────────────────────────────
ASR_START_HOUR_UTC = 0    # Asian session open
ASR_END_HOUR_UTC   = 8    # Asian session close (= London open)

# ── OTE Fibonacci Levels ───────────────────────────────────────────────────────
OTE_FIB_LOW  = 0.618    # 61.8% retracement — OTE zone bottom
OTE_FIB_HIGH = 0.79     # 79%   retracement — OTE zone top
OTE_FIB_ENTRY = 0.705   # midpoint of OTE zone for entry

# ── Volume Confirmation ────────────────────────────────────────────────────────
VOLUME_SPIKE_FACTOR = 1.3   # sweep candle volume must be 1.3× average for confirmation
VOLUME_LOOKBACK     = 20    # candles to compute average volume

# ── Displacement Candle ────────────────────────────────────────────────────────
DISPLACEMENT_BODY_RATIO = 0.70  # body/range ≥ 70% = displacement candle

# ── Allowed Trading Symbols ────────────────────────────────────────────────────
ALLOWED_SYMBOLS = {
    "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "EURJPY",
    "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
    "XAUUSD", "BTCUSD", "NASDAQ", "US30",
}
