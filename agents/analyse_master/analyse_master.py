"""Analyse-Master Agent — ICT entry signal generator.

Pattern hierarchy (ICT methodology):
    1. Liquidity Sweep  — price raids a swing high/low, close reverses inside
    2. Break of Structure (BoS) — confirms directional intent after sweep
    3. Entry zone — one of:
         a. Order Block  (last opposing candle before the impulse)
         b. Breaker Block (old OB that price broke through; now opposite S/R)
         c. Fair Value Gap / FVG (imbalance between three consecutive candles)
    4. Pullback — price retraces into the entry zone on 1H

Sprint 2 additions:
    - Order Block persistence (anti-repainting): detected OBs stored to DB;
      on subsequent cycles, persisted OBs are loaded first before re-scanning.
    - Asian Session Range (ASR): session high/low built 00:00-08:00 UTC.
      At London open the expected sweep direction is derived from ASR context.
    - Volume spike confirmation at sweep candle (bonus confidence).
    - ATR-relative impulse validation (no more fixed 0.0005 threshold).
    - FVG minimum size check (instrument-aware, from constants).
    - OTE Fibonacci entry: after zone identified, entry refined to 70.5%
      retracement of the impulse swing rather than zone midpoint.
    - Displacement candle detection: large-body impulse = stronger signal.
    - Time-in-zone freshness: pullback older than 2 bars is rejected.

Kill-zone gate (UTC):
    London   08:00–11:00
    New York 13:00–16:00
Signals outside these windows are rejected.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from market_data.data_provider import OHLCData
from config.constants import (
    get_instrument_spec,
    KILL_ZONES_UTC,
    ACTIVE_KILL_ZONES,
    OB_LOOKBACK_CANDLES,
    OB_LOOKBACK_BREAKER,
    OB_PERSISTENCE_HOURS,
    ASR_START_HOUR_UTC,
    ASR_END_HOUR_UTC,
    OTE_FIB_LOW,
    OTE_FIB_HIGH,
    OTE_FIB_ENTRY,
    VOLUME_SPIKE_FACTOR,
    VOLUME_LOOKBACK,
    DISPLACEMENT_BODY_RATIO,
    SWING_WINDOWS,
    DEFAULT_SWING_WINDOW,
    MIN_RR_RATIO,
    MIN_CONFIDENCE_PCT,
    ATR_PERIOD,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────────

class TradeSignal:
    """Output model for Analyse-Master."""

    def __init__(
        self,
        entry_level:       float,
        stop_loss:         float,
        take_profit_1:     float,
        take_profit_2:     float,
        take_profit_3:     float,
        risk_reward_ratio: float,
        confidence:        float,
        pattern_elements:  Dict[str, bool],
        kill_zone_start:   datetime,
        kill_zone_end:     datetime,
        zone_top:          float,
        zone_bottom:       float,
        entry_type:        str = "ORDER_BLOCK",
        session:           str = "london",
        symbol:            str = "",
        direction:         str = "BUY",
        asr_high:          Optional[float] = None,
        asr_low:           Optional[float] = None,
        displacement:      bool = False,
        volume_confirmed:  bool = False,
        ote_entry:         bool = False,
        timestamp:         Optional[datetime] = None,
    ) -> None:
        self.entry_level       = entry_level
        self.stop_loss         = stop_loss
        self.take_profit_1     = take_profit_1
        self.take_profit_2     = take_profit_2
        self.take_profit_3     = take_profit_3
        self.risk_reward_ratio = risk_reward_ratio
        self.confidence        = confidence
        self.pattern_elements  = pattern_elements
        self.kill_zone_start   = kill_zone_start
        self.kill_zone_end     = kill_zone_end
        self.zone_top          = zone_top
        self.zone_bottom       = zone_bottom
        self.entry_type        = entry_type
        self.session           = session
        self.symbol            = symbol
        self.direction         = direction
        self.asr_high          = asr_high
        self.asr_low           = asr_low
        self.displacement      = displacement
        self.volume_confirmed  = volume_confirmed
        self.ote_entry         = ote_entry
        self.timestamp         = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_level":       self.entry_level,
            "stop_loss":         self.stop_loss,
            "take_profit_1":     self.take_profit_1,
            "take_profit_2":     self.take_profit_2,
            "take_profit_3":     self.take_profit_3,
            "risk_reward_ratio": self.risk_reward_ratio,
            "confidence":        self.confidence,
            "pattern_elements":  self.pattern_elements,
            "kill_zone_start":   self.kill_zone_start.isoformat(),
            "kill_zone_end":     self.kill_zone_end.isoformat(),
            "zone_top":          self.zone_top,
            "zone_bottom":       self.zone_bottom,
            "entry_type":        self.entry_type,
            "session":           self.session,
            "symbol":            self.symbol,
            "direction":         self.direction,
            "asr_high":          self.asr_high,
            "asr_low":           self.asr_low,
            "displacement":      self.displacement,
            "volume_confirmed":  self.volume_confirmed,
            "ote_entry":         self.ote_entry,
            "timestamp":         self.timestamp.isoformat(),
        }


# ──────────────────────────────────────────────────────────────────────────────
# Agent
# ──────────────────────────────────────────────────────────────────────────────

class AnalyseMaster(BaseAgent):
    """
    Analyse-Master Agent — Entry Signal Generator.

    Works exclusively during London and New York kill zones.
    Requires all 4 ICT elements before producing a signal.
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="Analyse-Master",
            instructions=(
                "You are the Analyse-Master Agent. Operate only during London "
                "(08-11 UTC) and New York (13-16 UTC) kill zones. Confirm all "
                "four ICT elements (Sweep, BoS, Zone, Pullback) before signalling. "
                "Entry zone priority: Order Block > Breaker Block > FVG. "
                "Refine entry to OTE Fibonacci (61.8-79%) when possible."
            ),
            verbose=verbose,
        )

    # ------------------------------------------------------------------
    # Kill zone gate
    # ------------------------------------------------------------------

    def _kill_zone(self) -> Tuple[bool, str, datetime, datetime]:
        """Return (active, session_name, window_start, window_end) in UTC."""
        now = datetime.now(timezone.utc)
        for name in ACTIVE_KILL_ZONES:
            h_start, h_end = KILL_ZONES_UTC[name]
            win_start = now.replace(hour=h_start, minute=0, second=0, microsecond=0)
            win_end   = now.replace(hour=h_end,   minute=0, second=0, microsecond=0)
            if win_start <= now < win_end:
                return True, name, win_start, win_end
        return False, "", datetime.now(timezone.utc), datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Asian Session Range (ASR)
    # ------------------------------------------------------------------

    def _asian_session_range(
        self, h1_candles: List[OHLCData]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Compute the high and low of the Asian session (00:00–08:00 UTC)
        from the most recent session in the 1H candle list.
        Returns (asr_high, asr_low) or (None, None) if no Asian candles found.
        """
        asian_candles = []
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)

        for c in h1_candles:
            ts = c.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            c_date = ts.date()
            # Include Asian session from today OR yesterday (covers overnight)
            if c_date in (today, yesterday):
                if ASR_START_HOUR_UTC <= ts.hour < ASR_END_HOUR_UTC:
                    asian_candles.append(c)

        if not asian_candles:
            return None, None

        asr_high = max(c.high for c in asian_candles)
        asr_low  = min(c.low  for c in asian_candles)
        self.logger.debug(
            "[ANALYSE] ASR %.5f – %.5f (%d candles)", asr_low, asr_high, len(asian_candles)
        )
        return round(asr_high, 5), round(asr_low, 5)

    def _asr_directional_bias(
        self,
        bias:     str,
        asr_high: Optional[float],
        asr_low:  Optional[float],
        current:  float,
    ) -> bool:
        """
        Returns True if the current price position is consistent with the
        expected Judas Swing direction relative to the Asian range.

        Bullish: price swept below ASR low → expect London rally
        Bearish: price swept above ASR high → expect London sell-off
        """
        if asr_high is None or asr_low is None:
            return True   # no ASR data — do not penalise
        if bias == "BULLISH":
            return current < asr_high     # in lower half or below ASR
        if bias == "BEARISH":
            return current > asr_low      # in upper half or above ASR
        return True

    # ------------------------------------------------------------------
    # ATR helper
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
    # Swing detection (adaptive window from constants)
    # ------------------------------------------------------------------

    def _swing_highs(
        self, candles: List[OHLCData], timeframe: str = "1H"
    ) -> List[float]:
        window = SWING_WINDOWS.get(timeframe.upper(), DEFAULT_SWING_WINDOW)
        out: List[float] = []
        for i in range(window, len(candles) - window):
            v = candles[i].high
            if all(v >= candles[j].high for j in range(i - window, i + window + 1) if j != i):
                out.append(v)
        return out

    def _swing_lows(
        self, candles: List[OHLCData], timeframe: str = "1H"
    ) -> List[float]:
        window = SWING_WINDOWS.get(timeframe.upper(), DEFAULT_SWING_WINDOW)
        out: List[float] = []
        for i in range(window, len(candles) - window):
            v = candles[i].low
            if all(v <= candles[j].low for j in range(i - window, i + window + 1) if j != i):
                out.append(v)
        return out

    # ------------------------------------------------------------------
    # Volume spike detection
    # ------------------------------------------------------------------

    def _volume_spike(self, candles: List[OHLCData], candle_idx: int) -> bool:
        """Return True if the candle at candle_idx has a volume spike."""
        if len(candles) < VOLUME_LOOKBACK + 1:
            return False
        baseline = candles[max(0, candle_idx - VOLUME_LOOKBACK) : candle_idx]
        if not baseline:
            return False
        avg_vol = sum(c.volume for c in baseline) / len(baseline)
        if avg_vol == 0:
            return False
        return candles[candle_idx].volume >= avg_vol * VOLUME_SPIKE_FACTOR

    # ------------------------------------------------------------------
    # Displacement candle detection
    # ------------------------------------------------------------------

    def _is_displacement(self, candle: OHLCData) -> bool:
        """True if the candle body is ≥70% of its total range (strong impulse)."""
        total = candle.high - candle.low
        if total == 0:
            return False
        body = abs(candle.close - candle.open)
        return (body / total) >= DISPLACEMENT_BODY_RATIO

    # ------------------------------------------------------------------
    # 1. Liquidity Sweep detection
    # ------------------------------------------------------------------

    def _detect_sweep(
        self,
        candles:     List[OHLCData],
        swing_highs: List[float],
        swing_lows:  List[float],
        bias:        str,
        symbol:      str,
    ) -> Tuple[bool, float, int, bool]:
        """
        Returns (sweep_ok, sweep_level, candle_idx, volume_confirmed).
        """
        spec      = get_instrument_spec(symbol)
        threshold = spec["pip_threshold"]

        if len(candles) < 3:
            return False, 0.0, -1, False

        recent = candles[-8:]

        if bias == "BULLISH" and swing_lows:
            key = min(swing_lows[-3:]) if len(swing_lows) >= 3 else min(swing_lows)
            for i, c in enumerate(recent):
                if c.low < key - threshold and c.close > key:
                    abs_idx = len(candles) - 8 + i
                    vol_ok  = self._volume_spike(candles, abs_idx)
                    self.logger.debug("[ANALYSE] Bullish sweep @ %.5f vol=%s", key, vol_ok)
                    return True, key, abs_idx, vol_ok

        elif bias == "BEARISH" and swing_highs:
            key = max(swing_highs[-3:]) if len(swing_highs) >= 3 else max(swing_highs)
            for i, c in enumerate(recent):
                if c.high > key + threshold and c.close < key:
                    abs_idx = len(candles) - 8 + i
                    vol_ok  = self._volume_spike(candles, abs_idx)
                    self.logger.debug("[ANALYSE] Bearish sweep @ %.5f vol=%s", key, vol_ok)
                    return True, key, abs_idx, vol_ok

        return False, 0.0, -1, False

    # ------------------------------------------------------------------
    # 2. Break of Structure (BoS)
    # ------------------------------------------------------------------

    def _detect_bos(
        self,
        candles:     List[OHLCData],
        swing_highs: List[float],
        swing_lows:  List[float],
        bias:        str,
        symbol:      str,
    ) -> Tuple[bool, float]:
        spec      = get_instrument_spec(symbol)
        threshold = spec["pip_threshold"]

        if len(candles) < 3:
            return False, 0.0

        last_close = candles[-1].close

        if bias == "BULLISH" and len(swing_highs) >= 2:
            prev_high = sorted(swing_highs)[-2]
            if last_close > prev_high + threshold:
                self.logger.debug("[ANALYSE] Bullish BoS above %.5f", prev_high)
                return True, prev_high

        elif bias == "BEARISH" and len(swing_lows) >= 2:
            prev_low = sorted(swing_lows)[1]
            if last_close < prev_low - threshold:
                self.logger.debug("[ANALYSE] Bearish BoS below %.5f", prev_low)
                return True, prev_low

        return False, 0.0

    # ------------------------------------------------------------------
    # 3a. Order Block detection (ATR-relative impulse)
    # ------------------------------------------------------------------

    def _detect_order_block(
        self,
        candles: List[OHLCData],
        bias:    str,
        symbol:  str,
    ) -> Tuple[bool, Optional[float], Optional[float], bool]:
        """Returns (ob_ok, zone_low, zone_high, displacement_confirmed)."""
        spec           = get_instrument_spec(symbol)
        min_imp_factor = spec["min_impulse_factor"]

        search = candles[-OB_LOOKBACK_CANDLES:] if len(candles) > OB_LOOKBACK_CANDLES else candles[:]
        atr    = self._atr(search)
        min_impulse = max(spec["pip_threshold"] * 5, atr * min_imp_factor)

        for i in range(len(search) - 4, 0, -1):
            curr    = search[i]
            impulse = search[i + 1 : i + 4]
            displ   = any(self._is_displacement(c) for c in impulse)

            if bias == "BULLISH" and curr.close < curr.open:           # bearish OB candle
                move = sum(c.close - c.open for c in impulse if c.close > c.open)
                if move >= min_impulse:
                    self.logger.debug("[ANALYSE] Bullish OB [%.5f–%.5f] disp=%s",
                                      curr.low, curr.high, displ)
                    return True, round(curr.low, 5), round(curr.high, 5), displ

            elif bias == "BEARISH" and curr.close > curr.open:         # bullish OB candle
                move = sum(c.open - c.close for c in impulse if c.close < c.open)
                if move >= min_impulse:
                    self.logger.debug("[ANALYSE] Bearish OB [%.5f–%.5f] disp=%s",
                                      curr.low, curr.high, displ)
                    return True, round(curr.low, 5), round(curr.high, 5), displ, curr.timestamp

        return False, None, None, False, None

    # ------------------------------------------------------------------
    # 3b. Breaker Block detection
    # ------------------------------------------------------------------

    def _detect_breaker_block(
        self,
        candles: List[OHLCData],
        bias:    str,
        symbol:  str,
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        spec           = get_instrument_spec(symbol)
        min_imp_factor = spec["min_impulse_factor"]
        sl_buf         = spec["sl_buffer"]

        search = candles[-OB_LOOKBACK_BREAKER:] if len(candles) > OB_LOOKBACK_BREAKER else candles[:]
        atr    = self._atr(search)
        min_impulse   = max(spec["pip_threshold"] * 5, atr * min_imp_factor)
        current_price = candles[-1].close

        for i in range(len(search) - 6, 0, -1):
            curr    = search[i]
            impulse = search[i + 1 : i + 4]

            if bias == "BEARISH" and curr.close > curr.open:
                move = sum(c.open - c.close for c in impulse if c.close < c.open)
                if move < min_impulse:
                    continue
                ob_bot = curr.low
                ob_top = curr.high
                broke  = any(c.close < ob_bot for c in search[i + 4:])
                retest = ob_bot <= current_price <= ob_top + sl_buf
                if broke and retest:
                    self.logger.debug("[ANALYSE] Bearish Breaker [%.5f–%.5f]", ob_bot, ob_top)
                    return True, round(ob_bot, 5), round(ob_top, 5), curr.timestamp

            elif bias == "BULLISH" and curr.close < curr.open:
                move = sum(c.close - c.open for c in impulse if c.close > c.open)
                if move < min_impulse:
                    continue
                ob_bot = curr.low
                ob_top = curr.high
                broke  = any(c.close > ob_top for c in search[i + 4:])
                retest = ob_bot - sl_buf <= current_price <= ob_top
                if broke and retest:
                    self.logger.debug("[ANALYSE] Bullish Breaker [%.5f–%.5f]", ob_bot, ob_top)
                    return True, round(ob_bot, 5), round(ob_top, 5), curr.timestamp

        return False, None, None, None

    # ------------------------------------------------------------------
    # 3c. Fair Value Gap (FVG) — with minimum size filter
    # ------------------------------------------------------------------

    def _detect_fvg(
        self,
        candles: List[OHLCData],
        bias:    str,
        symbol:  str,
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        spec         = get_instrument_spec(symbol)
        min_gap      = spec["pip_size"] * spec["min_fvg_pips"]
        pip_threshold = spec["pip_threshold"]

        start = max(1, len(candles) - 30)
        for i in range(len(candles) - 2, start, -1):
            prev = candles[i - 1]
            nxt  = candles[i + 1]

            if bias == "BULLISH":
                gap_bot = prev.high
                gap_top = nxt.low
                # Both min-size AND pip-threshold must pass
                if gap_top > gap_bot + max(min_gap, pip_threshold):
                    self.logger.debug("[ANALYSE] Bullish FVG [%.5f–%.5f]", gap_bot, gap_top)
                    return True, round(gap_bot, 5), round(gap_top, 5), candles[i].timestamp

            elif bias == "BEARISH":
                gap_top = prev.low
                gap_bot = nxt.high
                if gap_top > gap_bot + max(min_gap, pip_threshold):
                    self.logger.debug("[ANALYSE] Bearish FVG [%.5f–%.5f]", gap_bot, gap_top)
                    return True, round(gap_bot, 5), round(gap_top, 5), candles[i].timestamp

        return False, None, None, None

    # ------------------------------------------------------------------
    # 4. Pullback into zone (with freshness check)
    # ------------------------------------------------------------------

    def _detect_pullback(
        self,
        candles:  List[OHLCData],
        bias:     str,
        zone_bot: float,
        zone_top: float,
        symbol:   str,
        max_bars: int = 2,
    ) -> Tuple[bool, int]:
        """
        Returns (pullback_ok, bars_ago).
        max_bars: reject pullbacks older than this many candles (stale).
        """
        spec = get_instrument_spec(symbol)
        buf  = spec["sl_buffer"]

        if not candles:
            return False, -1

        for bars_ago, c in enumerate(reversed(candles[-max_bars - 1:])):
            if bias == "BULLISH":
                if c.low <= zone_top + buf and c.low >= zone_bot - buf:
                    return True, bars_ago
            elif bias == "BEARISH":
                if c.high >= zone_bot - buf and c.high <= zone_top + buf:
                    return True, bars_ago

        return False, -1

    # ------------------------------------------------------------------
    # OTE Fibonacci entry refinement
    # ------------------------------------------------------------------

    def _ote_entry(
        self,
        bias:     str,
        candles:  List[OHLCData],
        zone_bot: float,
        zone_top: float,
    ) -> Tuple[float, bool]:
        """
        Calculate the Optimal Trade Entry price using Fibonacci retracement.

        For a bullish setup:
            - Find the swing low (A) and swing high (B) that created the move
            - OTE zone = 61.8%–79% retracement back from B toward A
            - Entry = ~70.5% level

        Returns (entry_price, ote_used).
        """
        if len(candles) < 10:
            return (zone_bot + zone_top) / 2.0, False

        # Use zone as proxy for the OB/FVG range — derive the impulse swing
        # from recent swing extremes in the candle window
        recent = candles[-20:]
        if bias == "BULLISH":
            swing_low  = min(c.low  for c in recent)
            swing_high = max(c.high for c in recent)
            if swing_high <= swing_low:
                return (zone_bot + zone_top) / 2.0, False
            move_size = swing_high - swing_low
            # OTE entry = swing_high - (move_size * OTE_FIB_ENTRY)
            entry = swing_high - (move_size * OTE_FIB_ENTRY)
            # Clamp to zone
            entry = max(zone_bot, min(zone_top, entry))
            return round(entry, 5), True

        else:  # BEARISH
            swing_low  = min(c.low  for c in recent)
            swing_high = max(c.high for c in recent)
            if swing_high <= swing_low:
                return (zone_bot + zone_top) / 2.0, False
            move_size = swing_high - swing_low
            # OTE entry = swing_low + (move_size * OTE_FIB_ENTRY)
            entry = swing_low + (move_size * OTE_FIB_ENTRY)
            entry = max(zone_bot, min(zone_top, entry))
            return round(entry, 5), True

    # ------------------------------------------------------------------
    # Trade level calculation
    # ------------------------------------------------------------------

    def _trade_levels(
        self,
        bias:     str,
        entry:    float,
        zone_bot: float,
        zone_top: float,
        symbol:   str,
    ) -> Tuple[float, float, float, float, float]:
        """Return (stop_loss, tp1, tp2, tp3, rr)."""
        spec = get_instrument_spec(symbol)
        buf  = spec["sl_buffer"]

        sl = (zone_bot - buf) if bias == "BULLISH" else (zone_top + buf)

        risk = abs(entry - sl)
        if risk == 0:
            risk = buf * 2

        if bias == "BULLISH":
            tp1 = entry + risk * 1.0
            tp2 = entry + risk * 2.0
            tp3 = entry + risk * 3.0
        else:
            tp1 = entry - risk * 1.0
            tp2 = entry - risk * 2.0
            tp3 = entry - risk * 3.0

        rr = risk / max(risk, 0.00001) * 2.0   # always 2.0 (TP2 = 2R)
        return sl, tp1, tp2, tp3, rr

    # ------------------------------------------------------------------
    # Confidence scoring (weighted multiplicative model)
    # ------------------------------------------------------------------

    def _score_confidence(
        self,
        elements:          Dict[str, bool],
        rr:                float,
        trend_confidence:  float,
        entry_type:        str,
        displacement:      bool,
        volume_confirmed:  bool,
        ote_used:          bool,
        asr_aligned:       bool,
    ) -> float:
        # Base probability per element (independent joint probability model)
        p_sweep    = 0.90 if elements.get("liquidity_sweep")    else 0.50
        p_bos      = 0.90 if elements.get("break_of_structure") else 0.50
        p_zone     = 0.90 if elements.get("entry_zone")         else 0.50
        p_pullback = 0.88 if elements.get("pullback")           else 0.50

        p_type = {"ORDER_BLOCK": 1.00, "BREAKER_BLOCK": 0.95, "FVG": 0.88}.get(entry_type, 0.85)

        base = p_sweep * p_bos * p_zone * p_pullback * p_type * 100.0

        # Bonus multipliers for additional confirmations
        if displacement:   base *= 1.08
        if volume_confirmed: base *= 1.06
        if ote_used:       base *= 1.05
        if asr_aligned:    base *= 1.07
        if rr >= 3.0:      base *= 1.04

        # Scale by HTF confidence
        final = base * (trend_confidence / 100.0)
        return round(max(0.0, min(100.0, final)), 1)

    # ------------------------------------------------------------------
    # Order Block persistence (anti-repainting)
    # ------------------------------------------------------------------

    def _load_persisted_obs(
        self,
        symbol:    str,
        timeframe: str,
        bias:      str,
    ) -> List[Any]:
        """Load active, non-expired OBs from the DB for this symbol/TF/direction."""
        from database.db_manager import db_manager
        from database.models import OrderBlockCache as OBCache

        direction = "BULLISH" if bias == "BULLISH" else "BEARISH"
        now = datetime.utcnow()
        session = db_manager.get_session()
        try:
            return (
                session.query(OBCache)
                .filter(
                    OBCache.pair       == symbol,
                    OBCache.timeframe  == timeframe,
                    OBCache.direction  == direction,
                    OBCache.is_active.is_(True),
                    OBCache.expires_at  > now,
                )
                .order_by(OBCache.detected_at.desc())
                .limit(5)
                .all()
            )
        except Exception as exc:
            self.logger.warning("[ANALYSE] DB load OB failed: %s", exc)
            return []
        finally:
            session.close()

    def _persist_ob(
        self,
        symbol:    str,
        timeframe: str,
        bias:      str,
        ob_type:   str,
        zone_low:  float,
        zone_high: float,
        candle_ts: Optional[datetime],
    ) -> Optional[int]:
        """
        Persist a newly detected OB; idempotent — deduplicates by zone proximity.
        Returns the row ID on insert, None on duplicate or error.
        """
        if candle_ts is None:
            return None
        from database.db_manager import db_manager
        from database.models import OrderBlockCache as OBCache

        direction = "BULLISH" if bias == "BULLISH" else "BEARISH"
        spec      = get_instrument_spec(symbol)
        tol       = spec["pip_threshold"] * 5          # 5-pip dedup tolerance

        now        = datetime.utcnow()
        expires_at = now + timedelta(hours=OB_PERSISTENCE_HOURS)
        ts_naive   = candle_ts.replace(tzinfo=None) if candle_ts.tzinfo else candle_ts

        session = db_manager.get_session()
        try:
            existing = (
                session.query(OBCache)
                .filter(
                    OBCache.pair      == symbol,
                    OBCache.timeframe == timeframe,
                    OBCache.direction == direction,
                    OBCache.is_active.is_(True),
                )
                .all()
            )
            for row in existing:
                if (abs(row.zone_low - zone_low) <= tol and
                        abs(row.zone_high - zone_high) <= tol):
                    return None     # duplicate — skip

            ob = OBCache(
                pair        = symbol,
                timeframe   = timeframe,
                direction   = direction,
                ob_type     = ob_type,
                zone_low    = zone_low,
                zone_high   = zone_high,
                candle_ts   = ts_naive,
                detected_at = now,
                expires_at  = expires_at,
                is_active   = True,
                hit_count   = 0,
            )
            session.add(ob)
            session.commit()
            session.refresh(ob)
            self.logger.info(
                "[ANALYSE] OB persisted id=%d [%.5f–%.5f] %s %s",
                ob.id, zone_low, zone_high, ob_type, direction,
            )
            return ob.id
        except Exception as exc:
            self.logger.warning("[ANALYSE] DB persist OB failed: %s", exc)
            session.rollback()
            return None
        finally:
            session.close()

    def _mark_ob_hit(self, ob_id: int) -> None:
        """Increment hit_count when price retests a persisted OB."""
        from database.db_manager import db_manager
        from database.models import OrderBlockCache as OBCache

        session = db_manager.get_session()
        try:
            row = session.get(OBCache, ob_id)
            if row:
                row.hit_count += 1
                session.commit()
        except Exception as exc:
            self.logger.warning("[ANALYSE] DB mark OB hit failed: %s", exc)
            session.rollback()
        finally:
            session.close()

    def _deactivate_ob(self, ob_id: int) -> None:
        """Mark an OB inactive after price decisively closes through the zone."""
        from database.db_manager import db_manager
        from database.models import OrderBlockCache as OBCache

        session = db_manager.get_session()
        try:
            row = session.get(OBCache, ob_id)
            if row:
                row.is_active = False
                session.commit()
        except Exception as exc:
            self.logger.warning("[ANALYSE] DB deactivate OB failed: %s", exc)
            session.rollback()
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze(
        self,
        trend_report: Dict[str, Any],
        candle_data:  Optional[Dict[str, Any]] = None,
        symbol:       str = "",
    ) -> Optional[TradeSignal]:
        """
        Generate a TradeSignal when all ICT conditions are met.

        Args:
            trend_report: TrendReport.to_dict() from Trend-Master
            candle_data:  Market data dict (keys: "daily", "4h", "1h")
            symbol:       Trading pair identifier
        """
        # ── 0. Input validation ────────────────────────────────────────
        if not await self.validate_input(trend_report, ["bias", "confidence"]):
            self.logger.warning("[ANALYSE-MASTER] Invalid trend report")
            return None

        bias:             str   = trend_report["bias"]
        trend_confidence: float = float(trend_report.get("confidence", 75.0))
        risk_level:       str   = trend_report.get("risk_level", "MEDIUM")

        if bias == "NEUTRAL":
            self.logger.info("[ANALYSE-MASTER] Neutral bias — no signal")
            return None

        if risk_level == "HIGH":
            self.logger.warning("[ANALYSE-MASTER] High volatility — skipping")
            return None

        # ── 1. Kill zone gate ──────────────────────────────────────────
        active, session, kz_start, kz_end = self._kill_zone()
        if not active:
            now_utc = datetime.now(timezone.utc)
            self.logger.info(
                "[ANALYSE-MASTER] Outside kill zone (UTC %02d:%02d) — skipping",
                now_utc.hour, now_utc.minute,
            )
            return None

        self.logger.info("[ANALYSE-MASTER] Kill zone: %s  bias=%s", session.upper(), bias)

        # ── 2. Candle data ─────────────────────────────────────────────
        h4_candles: List[OHLCData] = []
        h1_candles: List[OHLCData] = []
        if candle_data:
            h4_candles = candle_data.get("4h", [])
            h1_candles = candle_data.get("1h", [])

        min_c = SWING_WINDOWS.get("1H", 5) * 2 + 1
        if len(h1_candles) < min_c:
            self.logger.warning("[ANALYSE-MASTER] Insufficient 1H candles (%d < %d)",
                                len(h1_candles), min_c)
            return None

        # ── 3. Asian Session Range ─────────────────────────────────────
        asr_high, asr_low = self._asian_session_range(h1_candles)
        current_price     = h1_candles[-1].close
        asr_aligned       = self._asr_directional_bias(bias, asr_high, asr_low, current_price)
        if not asr_aligned:
            self.logger.info("[ANALYSE-MASTER] ASR context misaligned — signal penalty applied")

        # ── 4. Swing levels ────────────────────────────────────────────
        sh_4h = self._swing_highs(h4_candles, "4H") if len(h4_candles) >= min_c else []
        sl_4h = self._swing_lows( h4_candles, "4H") if len(h4_candles) >= min_c else []
        sh_1h = self._swing_highs(h1_candles, "1H")
        sl_1h = self._swing_lows( h1_candles, "1H")

        sweep_highs = sh_4h if sh_4h else sh_1h
        sweep_lows  = sl_4h if sl_4h else sl_1h

        # ── 5. Liquidity Sweep ─────────────────────────────────────────
        sweep_ok, sweep_level, sweep_idx, volume_confirmed = self._detect_sweep(
            h1_candles, sweep_highs, sweep_lows, bias, symbol
        )

        # ── 6. Break of Structure ──────────────────────────────────────
        bos_ok, bos_level = self._detect_bos(h1_candles, sh_1h, sl_1h, bias, symbol)

        # ── 7. Entry zone: persisted OB first, then fresh scan ────────
        ob_timeframe  = "4H" if len(h4_candles) >= min_c else "1H"
        ob_candles    = h4_candles if ob_timeframe == "4H" else h1_candles
        entry_type                           = "NONE"
        zone_bot: Optional[float]            = None
        zone_top: Optional[float]            = None
        zone_candle_ts: Optional[datetime]   = None
        displacement                         = False
        persisted_ob_used: Optional[Any]     = None

        # ── 7a. Load persisted OBs and deactivate any that are breached ──
        persisted_obs = self._load_persisted_obs(symbol, ob_timeframe, bias)
        spec = get_instrument_spec(symbol)

        for pob in persisted_obs:
            pob_ts = pob.candle_ts if pob.candle_ts.tzinfo is None else pob.candle_ts.replace(tzinfo=None)
            breached = False
            for c in ob_candles:
                c_ts = c.timestamp if c.timestamp.tzinfo is None else c.timestamp.replace(tzinfo=None)
                if c_ts <= pob_ts:
                    continue
                if pob.direction == "BULLISH" and c.close < pob.zone_low - spec["sl_buffer"]:
                    breached = True
                    break
                if pob.direction == "BEARISH" and c.close > pob.zone_high + spec["sl_buffer"]:
                    breached = True
                    break
            if breached:
                self._deactivate_ob(pob.id)
                self.logger.info("[ANALYSE] Persisted OB id=%d breached — deactivated", pob.id)
            elif persisted_ob_used is None:
                persisted_ob_used = pob

        if persisted_ob_used is not None:
            zone_bot   = persisted_ob_used.zone_low
            zone_top   = persisted_ob_used.zone_high
            entry_type = persisted_ob_used.ob_type
            self.logger.info(
                "[ANALYSE] Using persisted OB id=%d type=%s [%.5f–%.5f]",
                persisted_ob_used.id, entry_type, zone_bot, zone_top,
            )
        else:
            # ── 7b. Fresh scan: OB → Breaker → FVG ───────────────────────
            ob_ok, ob_bot, ob_top, displacement, ob_ts = self._detect_order_block(
                ob_candles, bias, symbol,
            )
            if ob_ok:
                zone_bot, zone_top = ob_bot, ob_top
                entry_type = "ORDER_BLOCK"
                zone_candle_ts = ob_ts
            else:
                brk_ok, brk_bot, brk_top, brk_ts = self._detect_breaker_block(
                    ob_candles, bias, symbol,
                )
                if brk_ok:
                    zone_bot, zone_top = brk_bot, brk_top
                    entry_type = "BREAKER_BLOCK"
                    zone_candle_ts = brk_ts
                else:
                    fvg_ok, fvg_bot, fvg_top, fvg_ts = self._detect_fvg(
                        h1_candles, bias, symbol,
                    )
                    if fvg_ok:
                        zone_bot, zone_top = fvg_bot, fvg_top
                        entry_type = "FVG"
                        zone_candle_ts = fvg_ts

            # Persist any newly detected zone for future cycles
            if zone_bot is not None:
                self._persist_ob(
                    symbol, ob_timeframe, bias, entry_type,
                    zone_bot, zone_top, zone_candle_ts,
                )

        zone_confirmed = (zone_bot is not None and zone_top is not None)

        # ── 8. Pullback (with freshness gate) ─────────────────────────
        pullback_ok = False
        if zone_confirmed:
            pullback_ok, bars_ago = self._detect_pullback(
                h1_candles, bias, zone_bot, zone_top, symbol, max_bars=2
            )
            if pullback_ok and persisted_ob_used is not None:
                self._mark_ob_hit(persisted_ob_used.id)
            if not pullback_ok:
                self.logger.debug("[ANALYSE-MASTER] No fresh pullback into zone (< 2 bars)")

        # ── 9. All-or-nothing ICT checklist ───────────────────────────
        pattern_elements = {
            "liquidity_sweep":    sweep_ok,
            "break_of_structure": bos_ok,
            "entry_zone":         zone_confirmed,
            "pullback":           pullback_ok,
        }

        missing = [k for k, v in pattern_elements.items() if not v]
        if missing:
            self.logger.info("[ANALYSE-MASTER] Signal rejected — missing: %s", missing)
            return None

        # ── 10. OTE Fibonacci entry (preferred over zone midpoint) ─────
        entry, ote_used = self._ote_entry(bias, h1_candles, zone_bot, zone_top)

        # ── 11. Trade levels ───────────────────────────────────────────
        sl, tp1, tp2, tp3, rr = self._trade_levels(bias, entry, zone_bot, zone_top, symbol)

        if rr < MIN_RR_RATIO:
            self.logger.warning("[ANALYSE-MASTER] R:R %.2f < %.2f — rejected", rr, MIN_RR_RATIO)
            return None

        # ── 12. Confidence ─────────────────────────────────────────────
        confidence = self._score_confidence(
            elements         = pattern_elements,
            rr               = rr,
            trend_confidence = trend_confidence,
            entry_type       = entry_type,
            displacement     = displacement,
            volume_confirmed = volume_confirmed,
            ote_used         = ote_used,
            asr_aligned      = asr_aligned,
        )

        if confidence < MIN_CONFIDENCE_PCT:
            self.logger.warning(
                "[ANALYSE-MASTER] Confidence %.1f%% < %.1f%% — rejected",
                confidence, MIN_CONFIDENCE_PCT,
            )
            return None

        direction = "BUY" if bias == "BULLISH" else "SELL"

        signal = TradeSignal(
            entry_level       = round(entry, 5),
            stop_loss         = round(sl,    5),
            take_profit_1     = round(tp1,   5),
            take_profit_2     = round(tp2,   5),
            take_profit_3     = round(tp3,   5),
            risk_reward_ratio = round(rr,    2),
            confidence        = confidence,
            pattern_elements  = pattern_elements,
            kill_zone_start   = kz_start,
            kill_zone_end     = kz_end,
            zone_top          = round(zone_top,  5),
            zone_bottom       = round(zone_bot,  5),
            entry_type        = entry_type,
            session           = session,
            symbol            = symbol,
            direction         = direction,
            asr_high          = asr_high,
            asr_low           = asr_low,
            displacement      = displacement,
            volume_confirmed  = volume_confirmed,
            ote_entry         = ote_used,
        )

        self.logger.info(
            "[ANALYSE-MASTER] Signal ✓  Session=%s  Type=%s  Dir=%s  "
            "Entry=%.5f  SL=%.5f  TP2=%.5f  RR=%.1f  Conf=%.1f%%  "
            "OTE=%s  Disp=%s  Vol=%s  ASR=%s",
            session.upper(), entry_type, direction,
            signal.entry_level, signal.stop_loss, signal.take_profit_2,
            rr, confidence,
            "✓" if ote_used else "✗",
            "✓" if displacement else "✗",
            "✓" if volume_confirmed else "✗",
            "✓" if asr_aligned else "~",
        )
        return signal
