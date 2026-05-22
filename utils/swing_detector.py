"""Shared swing high/low detection — used by TrendMaster and AnalyseMaster."""

from typing import List
from market_data.data_provider import OHLCData


def find_swing_highs(candles: List[OHLCData], window: int = 5) -> List[float]:
    """
    Return chronologically-ordered swing highs.
    candle[i].high must be >= every high within `window` bars on each side.
    """
    highs: List[float] = []
    for i in range(window, len(candles) - window):
        candidate = candles[i].high
        if all(
            candidate >= candles[j].high
            for j in range(i - window, i + window + 1)
            if j != i
        ):
            highs.append(candidate)
    return highs


def find_swing_lows(candles: List[OHLCData], window: int = 5) -> List[float]:
    """
    Return chronologically-ordered swing lows.
    candle[i].low must be <= every low within `window` bars on each side.
    """
    lows: List[float] = []
    for i in range(window, len(candles) - window):
        candidate = candles[i].low
        if all(
            candidate <= candles[j].low
            for j in range(i - window, i + window + 1)
            if j != i
        ):
            lows.append(candidate)
    return lows
