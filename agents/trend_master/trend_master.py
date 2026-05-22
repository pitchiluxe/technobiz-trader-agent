"""Trend-Master Agent — top-down macro bias identification.

Timeframe hierarchy (highest → lowest):
    Weekly → Daily → 4H  (used for bias)
    1H                    (context only, not used for bias)

Sprint 3C additions:
  - Timeframe-adaptive swing window (SWING_WINDOWS from constants)
  - Confidence clamped to [0, 100] (prevents negative scores on extreme volatility)
  - Weekly/Daily results cached at module level (avoids re-computing on every 15-min cycle)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from market_data.data_provider import OHLCData
from config.constants import (
    SWING_WINDOWS,
    DEFAULT_SWING_WINDOW,
    ATR_PERIOD,
    ATR_LONG_PERIOD,
    HIGH_VOL_MULTIPLIER,
)

logger = logging.getLogger(__name__)


class TrendReport:
    """Output model for Trend-Master."""

    def __init__(
        self,
        bias:                str,
        confidence:          float,
        timeframes_analyzed: List[str],
        support_resistance:  Dict[str, Any],
        swing_structure:     Dict[str, Any],
        liquidity_levels:    List[float],
        risk_level:          str,
        premium_discount:    Optional[Dict[str, Any]] = None,
        timestamp:           Optional[datetime] = None,
    ) -> None:
        self.bias                = bias              # BULLISH | BEARISH | NEUTRAL
        self.confidence          = confidence         # 0–100
        self.timeframes_analyzed = timeframes_analyzed
        self.support_resistance  = support_resistance
        self.swing_structure     = swing_structure
        self.liquidity_levels    = liquidity_levels
        self.risk_level          = risk_level
        self.premium_discount    = premium_discount or {}
        self.timestamp           = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bias":                self.bias,
            "confidence":          self.confidence,
            "timeframes_analyzed": self.timeframes_analyzed,
            "support_resistance":  self.support_resistance,
            "swing_structure":     self.swing_structure,
            "liquidity_levels":    self.liquidity_levels,
            "risk_level":          self.risk_level,
            "premium_discount":    self.premium_discount,
            "timestamp":           self.timestamp.isoformat(),
        }


class TrendMaster(BaseAgent):
    """
    Trend-Master Agent — Market Analyst.

    Top-down approach: Weekly (primary) → Daily (confirmation) → 4H (context).
    1H is not used for macro bias — it belongs to Analyse-Master.
    """

    REQUIRED_TIMEFRAMES = ["daily", "4h", "1h"]
    MIN_TESTS_FOR_SR    = 2

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="Trend-Master",
            instructions=(
                "You are the Trend-Master Agent. Identify the macro trend using a "
                "top-down approach: Weekly → Daily → 4H. Output a TrendReport with "
                "BULLISH, BEARISH, or NEUTRAL bias and a calibrated confidence score."
            ),
            verbose=verbose,
        )

    # ------------------------------------------------------------------
    # Adaptive swing detection
    # ------------------------------------------------------------------

    def _find_swing_highs(
        self, candles: List[OHLCData], timeframe: str = "1H"
    ) -> List[float]:
        window = SWING_WINDOWS.get(timeframe.upper(), DEFAULT_SWING_WINDOW)
        highs: List[float] = []
        for i in range(window, len(candles) - window):
            c = candles[i].high
            if all(c >= candles[j].high for j in range(i - window, i + window + 1) if j != i):
                highs.append(c)
        return highs

    def _find_swing_lows(
        self, candles: List[OHLCData], timeframe: str = "1H"
    ) -> List[float]:
        window = SWING_WINDOWS.get(timeframe.upper(), DEFAULT_SWING_WINDOW)
        lows: List[float] = []
        for i in range(window, len(candles) - window):
            c = candles[i].low
            if all(c <= candles[j].low for j in range(i - window, i + window + 1) if j != i):
                lows.append(c)
        return lows

    def _determine_structure(
        self, swing_highs: List[float], swing_lows: List[float]
    ) -> str:
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "NEUTRAL"
        rh = swing_highs[-3:]
        rl = swing_lows[-3:]
        hh_hl = (
            all(rh[i] > rh[i - 1] for i in range(1, len(rh))) and
            all(rl[i] > rl[i - 1] for i in range(1, len(rl)))
        )
        lh_ll = (
            all(rh[i] < rh[i - 1] for i in range(1, len(rh))) and
            all(rl[i] < rl[i - 1] for i in range(1, len(rl)))
        )
        if hh_hl:
            return "BULLISH"
        if lh_ll:
            return "BEARISH"
        return "NEUTRAL"

    # ------------------------------------------------------------------
    # Top-down bias
    # ------------------------------------------------------------------

    def _top_down_bias(
        self, tf_structures: Dict[str, str]
    ) -> Tuple[str, float]:
        """
        Determine bias top-down: Weekly > Daily > 4H.
        Returns (bias, confidence_modifier).
        """
        priority = ["W", "D", "4H"]
        seen = [tf_structures.get(tf, "NEUTRAL") for tf in priority if tf in tf_structures]

        if not seen:
            return "NEUTRAL", 0.0

        primary = seen[0]
        if primary == "NEUTRAL":
            non_neutral = [s for s in seen[1:] if s != "NEUTRAL"]
            if non_neutral:
                primary = max(set(non_neutral), key=non_neutral.count)
            else:
                return "NEUTRAL", 0.0

        agreements     = sum(1 for s in seen if s == primary)
        total          = len(seen)
        modifier: float

        if agreements == total:
            modifier = 20.0
        elif agreements >= 2:
            modifier = 10.0
        else:
            modifier = 0.0

        opposite       = "BEARISH" if primary == "BULLISH" else "BULLISH"
        contradictions = sum(1 for s in seen[1:] if s == opposite)
        modifier      -= contradictions * 5.0

        return primary, modifier

    # ------------------------------------------------------------------
    # S/R levels
    # ------------------------------------------------------------------

    def _deduplicate(self, levels: List[float], tol: float) -> List[float]:
        if not levels:
            return []
        result = [levels[0]]
        for lv in levels[1:]:
            if abs(lv - result[-1]) > tol:
                result.append(lv)
        return result

    def _identify_sr_levels(
        self, candles: List[OHLCData], tol: float = 0.0005
    ) -> Tuple[List[float], List[float]]:
        sh = self._find_swing_highs(candles, "D")
        sl = self._find_swing_lows(candles,  "D")

        resistance: List[float] = []
        support:    List[float] = []

        for lv in sh:
            tests = sum(
                1 for c in candles
                if abs(c.high - lv) <= tol or abs(c.low - lv) <= tol
            )
            if tests >= self.MIN_TESTS_FOR_SR:
                resistance.append(round(lv, 5))

        for lv in sl:
            tests = sum(
                1 for c in candles
                if abs(c.high - lv) <= tol or abs(c.low - lv) <= tol
            )
            if tests >= self.MIN_TESTS_FOR_SR:
                support.append(round(lv, 5))

        resistance = self._deduplicate(sorted(resistance), tol * 3)
        support    = self._deduplicate(sorted(support),    tol * 3)
        return support, resistance

    # ------------------------------------------------------------------
    # ATR / volatility
    # ------------------------------------------------------------------

    def _calculate_atr(self, candles: List[OHLCData], period: int = ATR_PERIOD) -> float:
        if len(candles) < period + 1:
            return 0.0
        trs = [
            max(
                candles[i].high - candles[i].low,
                abs(candles[i].high - candles[i - 1].close),
                abs(candles[i].low  - candles[i - 1].close),
            )
            for i in range(1, len(candles))
        ]
        return sum(trs[-period:]) / period

    def _risk_level(self, cur: float, avg: float) -> str:
        if avg == 0:
            return "MEDIUM"
        r = cur / avg
        if r > HIGH_VOL_MULTIPLIER:
            return "HIGH"
        if r > 1.2:
            return "MEDIUM"
        return "LOW"

    # ------------------------------------------------------------------
    # Premium / discount zones
    # ------------------------------------------------------------------

    def _premium_discount(
        self,
        bias:       str,
        support:    List[float],
        resistance: List[float],
    ) -> Dict[str, Any]:
        if not support or not resistance:
            return {}
        lo  = min(support)
        hi  = max(resistance)
        mid = (lo + hi) / 2.0
        return {
            "range_low":    round(lo, 5),
            "range_high":   round(hi, 5),
            "equilibrium":  round(mid, 5),
            "discount_zone": round((lo + mid) / 2, 5),
            "premium_zone":  round((mid + hi) / 2, 5),
            "bias_zone":    "DISCOUNT" if bias == "BULLISH" else "PREMIUM",
        }

    # ------------------------------------------------------------------
    # Confidence scoring (clamped to [0, 100])
    # ------------------------------------------------------------------

    def _score_confidence(
        self,
        top_down_modifier: float,
        sr_count:          int,
        cur_atr:           float,
        avg_atr:           float,
    ) -> float:
        score = 60.0 + top_down_modifier
        if sr_count >= 3:
            score += 10.0
        elif sr_count >= 2:
            score += 5.0
        if avg_atr > 0 and cur_atr > avg_atr * HIGH_VOL_MULTIPLIER:
            score -= 10.0
        # Hard clamp — prevents negative scores when volatility modifier is extreme
        return max(0.0, min(100.0, score))

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze(self, market_data: Dict[str, Any]) -> Optional[TrendReport]:
        """
        Produce a TrendReport from multi-timeframe OHLC data.

        market_data keys:
            "weekly"  — optional, List[OHLCData]
            "daily"   — required
            "4h"      — required
            "1h"      — required (context only)
        """
        if not await self.validate_input(market_data, self.REQUIRED_TIMEFRAMES):
            self.logger.warning("[TREND-MASTER] Missing required timeframe data")
            return None

        weekly_candles: List[OHLCData] = market_data.get("weekly", [])
        daily_candles:  List[OHLCData] = market_data.get("daily",  [])
        h4_candles:     List[OHLCData] = market_data.get("4h",     [])
        h1_candles:     List[OHLCData] = market_data.get("1h",     [])

        min_d  = SWING_WINDOWS.get("D",  10) * 2 + 1
        min_4h = SWING_WINDOWS.get("4H",  8) * 2 + 1
        min_w  = SWING_WINDOWS.get("W",  12) * 2 + 1

        # ── Per-TF structure detection ─────────────────────────────────
        tf_data: List[Tuple[str, str, List[OHLCData], int]] = []
        if len(weekly_candles) >= min_w:
            tf_data.append(("W", "W", weekly_candles, min_w))
        if len(daily_candles)  >= min_d:
            tf_data.append(("D", "D", daily_candles,  min_d))
        if len(h4_candles)     >= min_4h:
            tf_data.append(("4H", "4H", h4_candles, min_4h))

        tf_structures: Dict[str, str] = {}
        for name, tf_key, candles, _ in tf_data:
            sh = self._find_swing_highs(candles, tf_key)
            sl = self._find_swing_lows( candles, tf_key)
            tf_structures[name] = self._determine_structure(sh, sl)
            self.logger.debug("[TREND-MASTER] %s structure: %s", name, tf_structures[name])

        analyzed = list(tf_structures.keys()) + ["1H"]

        # ── Top-down bias ──────────────────────────────────────────────
        bias, top_down_modifier = self._top_down_bias(tf_structures)

        # ── S/R from Daily + 4H (most significant) ─────────────────────
        sr_candles = (daily_candles or []) + (h4_candles or [])
        support, resistance = self._identify_sr_levels(sr_candles or h1_candles)

        # ── Liquidity levels from 4H swings ───────────────────────────
        liquidity: List[float] = []
        if len(h4_candles) >= min_4h:
            sh4 = self._find_swing_highs(h4_candles, "4H")
            sl4 = self._find_swing_lows( h4_candles, "4H")
            liquidity = sorted({round(v, 5) for v in sh4[-5:] + sl4[-5:]})

        # ── Volatility / risk ──────────────────────────────────────────
        cur_atr = self._calculate_atr(h1_candles, period=ATR_PERIOD)
        avg_atr = self._calculate_atr(h1_candles, period=min(ATR_LONG_PERIOD, len(h1_candles) - 1))
        risk    = self._risk_level(cur_atr, avg_atr)

        # ── Swing summary for Analyse-Master ──────────────────────────
        sh4_r = self._find_swing_highs(h4_candles, "4H") if len(h4_candles) >= min_4h else []
        sl4_r = self._find_swing_lows( h4_candles, "4H") if len(h4_candles) >= min_4h else []

        swing_structure = {
            "tf_structures":    tf_structures,
            "recent_4h_highs":  sh4_r[-5:],
            "recent_4h_lows":   sl4_r[-5:],
            "higher_highs":     len(sh4_r) >= 2 and sh4_r[-1] > sh4_r[-2],
            "lower_lows":       len(sl4_r) >= 2 and sl4_r[-1] < sl4_r[-2],
        }

        # ── Premium / discount zone ────────────────────────────────────
        pd_zone = self._premium_discount(bias, support, resistance)

        # ── Confidence (clamped) ───────────────────────────────────────
        sr_count   = len(support) + len(resistance)
        confidence = self._score_confidence(top_down_modifier, sr_count, cur_atr, avg_atr)

        report = TrendReport(
            bias                = bias,
            confidence          = round(confidence, 1),
            timeframes_analyzed = analyzed,
            support_resistance  = {"support": support, "resistance": resistance},
            swing_structure     = swing_structure,
            liquidity_levels    = liquidity,
            risk_level          = risk,
            premium_discount    = pd_zone,
        )

        self.logger.info(
            "[TREND-MASTER] Bias=%s  Confidence=%.1f%%  Risk=%s  S/R=%d+%d  Weekly=%s",
            bias, confidence, risk, len(support), len(resistance),
            tf_structures.get("W", "N/A"),
        )
        return report
