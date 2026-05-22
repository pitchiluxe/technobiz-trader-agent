"""
TTL-based in-process candle cache.

Weekly candles change once a week; Daily once a day; 4H every four hours.
Fetching them every 15 minutes wastes MT5 bandwidth and adds latency.
This cache stores fetched data and returns it until it expires.

Usage:
    cache = CandleCache()
    candles = cache.get("EURUSD", "4H")
    if candles is None:
        candles = await provider.get_candles("EURUSD", "4H", 100)
        cache.set("EURUSD", "4H", candles)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from config.constants import TIMEFRAME_MINUTES

logger = logging.getLogger(__name__)


class CandleCache:
    """Simple in-process TTL cache keyed by (symbol, timeframe)."""

    # Cache lifetime = timeframe_interval_seconds × factor
    # 0.9 means a 4H cache expires after 3h 36m (slightly before the next candle)
    TTL_FACTOR = 0.90

    def __init__(self) -> None:
        # key: (symbol_upper, timeframe_upper)
        # value: (candles, stored_at_utc)
        self._store: Dict[Tuple[str, str], Tuple[List, datetime]] = {}

    # ------------------------------------------------------------------

    def _ttl_seconds(self, timeframe: str) -> float:
        minutes = TIMEFRAME_MINUTES.get(timeframe.upper(), 60)
        return minutes * 60 * self.TTL_FACTOR

    def _key(self, symbol: str, timeframe: str) -> Tuple[str, str]:
        return (symbol.strip().upper(), timeframe.strip().upper())

    # ------------------------------------------------------------------

    def get(self, symbol: str, timeframe: str) -> Optional[List]:
        """Return cached candles if still fresh, else None."""
        k = self._key(symbol, timeframe)
        entry = self._store.get(k)
        if entry is None:
            return None
        candles, stored_at = entry
        age = (datetime.now(timezone.utc) - stored_at).total_seconds()
        ttl = self._ttl_seconds(timeframe)
        if age > ttl:
            logger.debug(
                "[CACHE] %s %s expired (age=%.0fs ttl=%.0fs)", symbol, timeframe, age, ttl
            )
            del self._store[k]
            return None
        logger.debug(
            "[CACHE] %s %s hit (age=%.0fs ttl=%.0fs len=%d)",
            symbol, timeframe, age, ttl, len(candles),
        )
        return candles

    def set(self, symbol: str, timeframe: str, candles: List) -> None:
        """Store candles with the current UTC timestamp."""
        k = self._key(symbol, timeframe)
        self._store[k] = (candles, datetime.now(timezone.utc))
        logger.debug("[CACHE] %s %s stored (%d candles)", symbol, timeframe, len(candles))

    def invalidate(self, symbol: str, timeframe: Optional[str] = None) -> None:
        """Invalidate one symbol (all TFs) or a specific (symbol, TF) entry."""
        sym = symbol.strip().upper()
        if timeframe:
            self._store.pop((sym, timeframe.strip().upper()), None)
        else:
            stale = [k for k in self._store if k[0] == sym]
            for k in stale:
                del self._store[k]
            logger.debug("[CACHE] Invalidated %d entries for %s", len(stale), symbol)

    def clear(self) -> None:
        """Wipe the entire cache."""
        self._store.clear()
        logger.debug("[CACHE] Cleared")

    def stats(self) -> Dict[str, int]:
        """Return cache size summary."""
        return {"entries": len(self._store)}
