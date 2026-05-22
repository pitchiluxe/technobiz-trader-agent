"""Market-Regime Agent — current market environment classifier.

Classifies the market into one of four regimes using multi-timeframe
price structure and volatility analysis:

  TRENDING   — clear Higher-High / Higher-Low (or Lower sequences) on ≥2 TFs
               → full risk, proceed at user RR setting
  RANGING    — price oscillating between S/R without BOS on any TF
               → reduce position size, widen TP targets
  VOLATILE   — ATR > 2× long-term average; erratic large moves
               → hard-block or severe size reduction
  TRANSITION — conflicting signals between timeframes
               → reduce size, require higher confidence

Returns a MarketRegimeReport that carries:
  regime                : str    — TRENDING | RANGING | VOLATILE | TRANSITION
  confidence            : float  — 0–100
  risk_multiplier       : float  — recommended lot-size multiplier
  recommended_rr        : float  — regime-appropriate RR floor
  recommended_risk_pct  : float  — regime-scaled risk %
  description           : str    — human-readable explanation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from market_data.data_provider import OHLCData
from config.constants import (
    ATR_PERIOD,
    ATR_LONG_PERIOD,
    HIGH_VOL_MULTIPLIER,
    SWING_WINDOWS,
    DEFAULT_SWING_WINDOW,
)
from config.user_risk_settings import RiskSettingsManager

logger = logging.getLogger(__name__)


class MarketRegimeReport:
    """Output model for Market-Regime Agent."""

    def __init__(
        self,
        regime:               str,
        confidence:           float,
        risk_multiplier:      float,
        recommended_rr:       float,
        recommended_risk_pct: float,
        description:          str,
        tf_structures:        Optional[Dict[str, str]] = None,
        timestamp:            Optional[datetime] = None,
    ) -> None:
        self.regime               = regime               # TRENDING|RANGING|VOLATILE|TRANSITION
        self.confidence           = confidence           # 0–100
        self.risk_multiplier      = risk_multiplier      # 0.0–1.0
        self.recommended_rr       = recommended_rr       # minimum RR for this regime
        self.recommended_risk_pct = recommended_risk_pct # risk % suggestion
        self.description          = description
        self.tf_structures        = tf_structures or {}
        self.timestamp            = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime":               self.regime,
            "confidence":           round(self.confidence, 1),
            "risk_multiplier":      round(self.risk_multiplier, 3),
            "recommended_rr":       round(self.recommended_rr, 1),
            "recommended_risk_pct": round(self.recommended_risk_pct, 2),
            "description":          self.description,
            "tf_structures":        self.tf_structures,
            "timestamp":            self.timestamp.isoformat(),
        }


class MarketRegimeAgent(BaseAgent):
    """
    Market-Regime Agent.

    Reads OHLC candle lists across timeframes and returns a MarketRegimeReport
    that the Trader-Master uses to scale position size and adjust RR targets.
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="Market-Regime",
            instructions=(
                "You are the Market-Regime Agent. Classify the current market "
                "environment as TRENDING, RANGING, VOLATILE, or TRANSITION. "
                "Return a risk_multiplier and recommended RR ratio appropriate "
                "for the detected regime."
            ),
            verbose=verbose,
        )

    # ------------------------------------------------------------------
    # ATR
    # ------------------------------------------------------------------

    def _atr(self, candles: List[OHLCData], period: int = ATR_PERIOD) -> float:
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

    # ------------------------------------------------------------------
    # Swing structure
    # ------------------------------------------------------------------

    def _swings(
        self, candles: List[OHLCData], timeframe: str = "1H"
    ) -> Tuple[List[float], List[float]]:
        window = SWING_WINDOWS.get(timeframe.upper(), DEFAULT_SWING_WINDOW)
        highs, lows = [], []
        for i in range(window, len(candles) - window):
            h = candles[i].high
            if all(h >= candles[j].high for j in range(i - window, i + window + 1) if j != i):
                highs.append(h)
            l = candles[i].low
            if all(l <= candles[j].low for j in range(i - window, i + window + 1) if j != i):
                lows.append(l)
        return highs, lows

    def _structure(self, highs: List[float], lows: List[float]) -> str:
        if len(highs) < 2 or len(lows) < 2:
            return "NEUTRAL"
        rh, rl = highs[-3:], lows[-3:]
        if (all(rh[i] > rh[i-1] for i in range(1, len(rh))) and
                all(rl[i] > rl[i-1] for i in range(1, len(rl)))):
            return "BULLISH"
        if (all(rh[i] < rh[i-1] for i in range(1, len(rh))) and
                all(rl[i] < rl[i-1] for i in range(1, len(rl)))):
            return "BEARISH"
        return "NEUTRAL"

    # ------------------------------------------------------------------
    # Range detection (ATR-relative chop)
    # ------------------------------------------------------------------

    def _is_ranging(self, candles: List[OHLCData], atr: float) -> bool:
        """True if price is oscillating within a tight band (choppy)."""
        if atr == 0 or len(candles) < 20:
            return False
        recent = candles[-20:]
        rng = max(c.high for c in recent) - min(c.low for c in recent)
        # If the full 20-candle range is < 3× ATR, the market is ranging
        return rng < atr * 3.0

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze(
        self,
        market_data: Dict[str, Any],
    ) -> MarketRegimeReport:
        """
        Classify the market regime from multi-TF candle data.

        market_data keys: "weekly"(opt), "daily", "4h", "1h"
        Returns MarketRegimeReport.
        """
        s = RiskSettingsManager.get()

        daily:  List[OHLCData] = market_data.get("daily", [])
        h4:     List[OHLCData] = market_data.get("4h",    [])
        h1:     List[OHLCData] = market_data.get("1h",    [])

        # ── Volatility assessment (1H ATR) ─────────────────────────────
        cur_atr  = self._atr(h1, ATR_PERIOD)
        long_atr = self._atr(h1, min(ATR_LONG_PERIOD, max(len(h1) - 1, 1)))
        vol_ratio = (cur_atr / long_atr) if long_atr > 0 else 1.0

        # ── Structure per timeframe ─────────────────────────────────────
        tf_structs: Dict[str, str] = {}
        for label, candles, tf_key in [
            ("D",  daily, "D"),
            ("4H", h4,    "4H"),
            ("1H", h1,    "1H"),
        ]:
            if len(candles) >= SWING_WINDOWS.get(tf_key, 5) * 2 + 1:
                sh, sl = self._swings(candles, tf_key)
                tf_structs[label] = self._structure(sh, sl)
            else:
                tf_structs[label] = "NEUTRAL"

        structs = list(tf_structs.values())
        bullish  = structs.count("BULLISH")
        bearish  = structs.count("BEARISH")
        neutral  = structs.count("NEUTRAL")

        # ── Classify regime ─────────────────────────────────────────────
        if vol_ratio >= HIGH_VOL_MULTIPLIER * 1.3:
            regime          = "VOLATILE"
            risk_mult       = 0.25
            rr              = max(s.rr_ratio, 3.0)   # require wider RR in chaos
            confidence      = min(90.0, vol_ratio * 20.0)
            desc = (
                f"Extreme volatility — ATR {vol_ratio:.1f}× long-term average. "
                "Position size severely reduced. Require wide RR."
            )

        elif (bullish >= 2 or bearish >= 2) and neutral <= 1:
            regime          = "TRENDING"
            risk_mult       = 1.0
            rr              = s.rr_ratio
            trend_dir       = "BULLISH" if bullish > bearish else "BEARISH"
            tfs_aligned     = bullish if trend_dir == "BULLISH" else bearish
            confidence      = 50.0 + tfs_aligned * 15.0
            desc = (
                f"{trend_dir} trend confirmed on {tfs_aligned}/3 timeframes. "
                "Full risk permitted."
            )

        elif neutral >= 2 or (bullish > 0 and bearish > 0):
            regime          = "TRANSITION"
            risk_mult       = 0.60
            rr              = max(s.rr_ratio, 2.5)
            confidence      = 55.0
            desc = (
                "Conflicting signals across timeframes — market in transition. "
                "Reduced size and elevated RR threshold applied."
            )

        else:
            # Mostly neutral with low volatility → ranging
            if h1 and self._is_ranging(h1, cur_atr):
                regime      = "RANGING"
                risk_mult   = 0.50
                rr          = max(s.rr_ratio, 2.0)
                confidence  = 60.0
                desc = (
                    "Low-volatility range — price oscillating inside a tight band. "
                    "Reduced position size. Fade-the-range setups only."
                )
            else:
                regime      = "TRANSITION"
                risk_mult   = 0.70
                rr          = s.rr_ratio
                confidence  = 50.0
                desc = "Market structure unclear — conservative sizing applied."

        recommended_risk_pct = s.risk_pct * risk_mult

        self.logger.info(
            "[MARKET-REGIME] %s  conf=%.0f%%  risk_mult=%.2f  rr≥%.1f  "
            "vol_ratio=%.1f  D=%s 4H=%s 1H=%s",
            regime, confidence, risk_mult, rr, vol_ratio,
            tf_structs.get("D", "?"), tf_structs.get("4H", "?"), tf_structs.get("1H", "?"),
        )

        return MarketRegimeReport(
            regime               = regime,
            confidence           = round(confidence, 1),
            risk_multiplier      = round(risk_mult, 3),
            recommended_rr       = round(rr, 1),
            recommended_risk_pct = round(recommended_risk_pct, 3),
            description          = desc,
            tf_structures        = tf_structs,
        )
