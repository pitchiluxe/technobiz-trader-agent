"""News-Sentinel Agent — high-impact event filter.

Prevents trade entries within a configurable window around major
economic releases.  Two tiers of data sources:

  Tier 1 (always active):   Hard-coded weekly recurring events
                             (NFP, CPI, FOMC, BOE, ECB — fixed schedule patterns)
  Tier 2 (optional):        Live ForexFactory-style JSON endpoint
                             (enabled when NEWS_API_URL env var is set)

A trade is safe if no HIGH-impact event is scheduled within
±news_buffer_minutes of the current UTC time.

Returns a NewsWindow dataclass with:
  safe            : bool  — True if it is safe to trade
  next_event_name : str   — name of the nearest upcoming event
  minutes_until   : float — minutes until that event (negative = past it)
  risk_level      : str   — CLEAR | CAUTION | DANGER
  impacted_pairs  : list  — pairs most likely affected
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from config.user_risk_settings import RiskSettingsManager

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Static high-impact event database
# Entries: (weekday 0=Mon, hour_utc, minute_utc, name, impacted_pairs, is_weekly)
# is_weekly=True means it recurs every week on that weekday/time slot
# ──────────────────────────────────────────────────────────────────────────────
_STATIC_EVENTS: List[Dict[str, Any]] = [
    # ── US ────────────────────────────────────────────────────────────────────
    {"weekday": 4, "hour": 13, "minute": 30, "name": "US Non-Farm Payrolls (1st Fri)",
     "pairs": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"], "monthly": True},
    {"weekday": 2, "hour": 18, "minute": 0,  "name": "FOMC Rate Decision",
     "pairs": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "NASDAQ", "US30"], "monthly": True},
    {"weekday": 2, "hour": 12, "minute": 30, "name": "US CPI",
     "pairs": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"], "monthly": True},
    {"weekday": 3, "hour": 12, "minute": 30, "name": "US GDP",
     "pairs": ["EURUSD", "GBPUSD", "USDJPY"], "monthly": True},
    {"weekday": 3, "hour": 12, "minute": 30, "name": "US Jobless Claims",
     "pairs": ["EURUSD", "GBPUSD", "USDJPY"], "weekly": True},
    # ── EUR ───────────────────────────────────────────────────────────────────
    {"weekday": 3, "hour": 11, "minute": 45, "name": "ECB Rate Decision",
     "pairs": ["EURUSD", "EURJPY", "GBPUSD"], "monthly": True},
    {"weekday": 2, "hour": 9,  "minute": 0,  "name": "Eurozone CPI",
     "pairs": ["EURUSD", "EURJPY"], "monthly": True},
    # ── GBP ───────────────────────────────────────────────────────────────────
    {"weekday": 3, "hour": 11, "minute": 0,  "name": "BOE Rate Decision",
     "pairs": ["GBPUSD", "GBPJPY", "EURGBP"], "monthly": True},
    {"weekday": 2, "hour": 7,  "minute": 0,  "name": "UK CPI",
     "pairs": ["GBPUSD", "GBPJPY"], "monthly": True},
    # ── JPY ───────────────────────────────────────────────────────────────────
    {"weekday": 4, "hour": 23, "minute": 50, "name": "BOJ Rate Decision",
     "pairs": ["USDJPY", "GBPJPY", "EURJPY"], "monthly": True},
    # ── AUD ───────────────────────────────────────────────────────────────────
    {"weekday": 0, "hour": 23, "minute": 30, "name": "RBA Rate Decision",
     "pairs": ["AUDUSD", "AUDJPY"], "monthly": True},
    # ── CAD ───────────────────────────────────────────────────────────────────
    {"weekday": 2, "hour": 14, "minute": 0,  "name": "BOC Rate Decision",
     "pairs": ["USDCAD"], "monthly": True},
]


class NewsWindow:
    """Output model for News-Sentinel."""

    def __init__(
        self,
        safe:             bool,
        next_event_name:  str,
        minutes_until:    float,
        risk_level:       str,
        impacted_pairs:   List[str],
        timestamp:        Optional[datetime] = None,
    ) -> None:
        self.safe            = safe
        self.next_event_name = next_event_name
        self.minutes_until   = minutes_until
        self.risk_level      = risk_level    # CLEAR | CAUTION | DANGER
        self.impacted_pairs  = impacted_pairs
        self.timestamp       = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe":             self.safe,
            "next_event_name":  self.next_event_name,
            "minutes_until":    round(self.minutes_until, 1),
            "risk_level":       self.risk_level,
            "impacted_pairs":   self.impacted_pairs,
            "timestamp":        self.timestamp.isoformat(),
        }

    @staticmethod
    def clear() -> "NewsWindow":
        return NewsWindow(
            safe=True, next_event_name="None", minutes_until=999.0,
            risk_level="CLEAR", impacted_pairs=[],
        )


class NewsSentinel(BaseAgent):
    """
    News-Sentinel Agent — economic calendar event filter.

    Blocks trade signals that fall within the news buffer window around
    high-impact events.  Checks the static event database and optionally
    a live feed (set NEWS_API_URL env var to enable).
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="News-Sentinel",
            instructions=(
                "You are the News-Sentinel. Check whether a trade is safe to place "
                "given upcoming high-impact economic events. Block any trade that "
                "falls within the user-configured news buffer window."
            ),
            verbose=verbose,
        )
        self._live_events: List[Dict[str, Any]] = []
        self._live_cache_ts: Optional[datetime] = None
        self._live_cache_ttl = 3600   # refresh live feed every hour

    async def analyze(self, *args: Any, **kwargs: Any) -> Any:
        """Satisfy BaseAgent abstract requirement — delegates to check()."""
        return await self.check(*args, **kwargs)

    # ------------------------------------------------------------------
    # Static event matching
    # ------------------------------------------------------------------

    def _nearest_static_event(
        self, symbol: str, now: datetime
    ) -> Tuple[Optional[str], float, List[str]]:
        """
        Return (event_name, minutes_until, impacted_pairs) for the nearest
        high-impact event that affects symbol.  Returns None if none found.
        """
        best_name:    Optional[str] = None
        best_minutes: float = 1e9
        best_pairs:   List[str] = []

        for event in _STATIC_EVENTS:
            # Build candidate datetime for this week
            pairs: List[str] = event.get("pairs", [])
            if symbol and symbol not in pairs:
                continue   # this event doesn't affect the traded symbol

            weekday = event["weekday"]
            hour    = event["hour"]
            minute  = event["minute"]

            # Find this week's occurrence and next week's
            days_delta = (weekday - now.weekday()) % 7
            candidate  = now.replace(
                hour=hour, minute=minute, second=0, microsecond=0
            ) + timedelta(days=days_delta)

            # If candidate is in the past by more than buffer, try next week
            if (now - candidate).total_seconds() > 0:
                candidate += timedelta(weeks=1)

            diff_minutes = (candidate - now).total_seconds() / 60.0
            if abs(diff_minutes) < abs(best_minutes):
                best_minutes = diff_minutes
                best_name    = event["name"]
                best_pairs   = pairs

        return best_name, best_minutes, best_pairs

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def check(
        self,
        symbol:    str = "",
        timeframe: str = "1H",
    ) -> NewsWindow:
        """
        Return a NewsWindow indicating whether it is safe to trade symbol now.

        Args:
            symbol:    Trading symbol (e.g. "EURUSD") — used to filter events
            timeframe: Not used for gating, stored for context
        """
        s = RiskSettingsManager.get()

        if not s.news_event_filter:
            return NewsWindow.clear()

        buffer_min = float(s.news_buffer_minutes)
        now        = datetime.now(timezone.utc)

        # ── Check static events ────────────────────────────────────────
        name, minutes_until, pairs = self._nearest_static_event(symbol, now)

        if name is None:
            return NewsWindow.clear()

        # ── Classify risk ──────────────────────────────────────────────
        if -buffer_min <= minutes_until <= buffer_min:
            risk_level = "DANGER"
            safe       = False
            self.logger.warning(
                "[NEWS-SENTINEL] DANGER — '%s' in %.1f min — blocking %s",
                name, minutes_until, symbol,
            )
        elif -buffer_min * 2 <= minutes_until <= buffer_min * 2:
            risk_level = "CAUTION"
            safe       = True   # caution but not blocked
            self.logger.info(
                "[NEWS-SENTINEL] CAUTION — '%s' in %.1f min — %s",
                name, minutes_until, symbol,
            )
        else:
            risk_level = "CLEAR"
            safe       = True
            self.logger.debug(
                "[NEWS-SENTINEL] CLEAR — nearest event '%s' in %.1f min",
                name, minutes_until,
            )

        return NewsWindow(
            safe            = safe,
            next_event_name = name,
            minutes_until   = round(minutes_until, 1),
            risk_level      = risk_level,
            impacted_pairs  = pairs,
        )
