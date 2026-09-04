"""Trader-Master Agent — Execution Engine.

Receives a validated TradeSignal from Analyse-Master and:
  1. Pre-execution checks: confidence, R:R, drawdown, concurrent trades, kill switch
  2. Rebuilds open_trades from MT5 on first run (crash-recovery)
  3. Zooms into 15m/5m candles for precise LTF confirmation candle entry
  4. Calculates dynamic lot size (2% risk, instrument-aware, streak-adjusted)
  5. Places order via MT5 with retry logic
  6. Launches a background monitor task that:
       - Polls MT5 every 60s
       - Closes 50% at TP1 and moves SL to break-even
       - Closes 30% at TP2
       - Records close on SL or TP3 trail
  7. Resets daily_loss at day boundary (UTC)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from config.settings import settings
from config.constants import (
    get_instrument_spec,
    MAX_RISK_PER_TRADE,
    MAX_DAILY_DRAWDOWN,
    MAX_CONCURRENT_TRADES,
    MIN_RR_RATIO,
    MIN_CONFIDENCE_PCT,
    CONSECUTIVE_LOSS_LIMIT,
    SIZE_REDUCTION_FACTOR,
    SIZE_REDUCTION_TRADES,
    LOWER_TF_LOOKBACK,
)
from config.kill_switch import KillSwitch
from config.user_risk_settings import RiskSettingsManager

if TYPE_CHECKING:
    from market_data.mt5_provider import MT5Provider
    from market_data.data_provider import OHLCData

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────────

class ExecutionRecord:
    """Full audit record for one trade execution."""

    def __init__(
        self,
        signal_id:     str,
        entry_price:   float,
        entry_time:    datetime,
        position_size: float,
        stop_loss:     float,
        take_profit_1: float,
        take_profit_2: float,
        take_profit_3: float,
        status:        str,
        entry_type:    str = "ORDER_BLOCK",
        session:       str = "london",
        symbol:        str = "",
        direction:     str = "BUY",
        mt5_ticket:    Optional[int] = None,
        exit_price:    Optional[float] = None,
        exit_time:     Optional[datetime] = None,
        exit_reason:   Optional[str] = None,
        p_and_l:       Optional[float] = None,
        slippage:      Optional[float] = None,
        timestamp:     Optional[datetime] = None,
    ) -> None:
        self.signal_id     = signal_id
        self.entry_price   = entry_price
        self.entry_time    = entry_time
        self.position_size = position_size
        self.stop_loss     = stop_loss
        self.take_profit_1 = take_profit_1
        self.take_profit_2 = take_profit_2
        self.take_profit_3 = take_profit_3
        self.status        = status        # PENDING | OPEN | CLOSED
        self.entry_type    = entry_type
        self.session       = session
        self.symbol        = symbol
        self.direction     = direction
        self.mt5_ticket    = mt5_ticket
        self.exit_price    = exit_price
        self.exit_time     = exit_time
        self.exit_reason   = exit_reason   # TP_HIT | SL_HIT | MANUAL_CLOSE
        self.p_and_l       = p_and_l
        self.slippage      = slippage
        self.timestamp     = timestamp or datetime.now()
        # Monitor flags — set by _monitor_trade background task
        self.tp1_hit: bool = False
        self.tp2_hit: bool = False
        # Trailing stop state for the remaining 20% position after TP2
        self.trail_sl: Optional[float] = None
        self.trail_high_water: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id":     self.signal_id,
            "entry_price":   self.entry_price,
            "entry_time":    self.entry_time.isoformat(),
            "position_size": self.position_size,
            "stop_loss":     self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "status":        self.status,
            "entry_type":    self.entry_type,
            "session":       self.session,
            "symbol":        self.symbol,
            "direction":     self.direction,
            "mt5_ticket":    self.mt5_ticket,
            "exit_price":    self.exit_price,
            "exit_time":     self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason":   self.exit_reason,
            "p_and_l":       self.p_and_l,
            "slippage":      self.slippage,
            "tp1_hit":       self.tp1_hit,
            "tp2_hit":       self.tp2_hit,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Agent
# ──────────────────────────────────────────────────────────────────────────────

class TraderMaster(BaseAgent):
    """
    Trader-Master Agent — Execution Engine with full lifecycle management.

    Key fixes vs initial version:
    - daily_loss resets at UTC day boundary (not on process restart)
    - open_trades reconciled from MT5 on startup (crash recovery)
    - consecutive loss streak tracked with reduced-sizing counter
    - background monitor task closes partial positions and moves SL to BE
    - instrument-specific constants (pip size, SL buffer) from config/constants.py
    """

    def __init__(
        self,
        verbose:      bool = False,
        mt5_provider: Optional["MT5Provider"] = None,
    ) -> None:
        super().__init__(
            name="Trader-Master",
            instructions=(
                "You are the Trader-Master Agent. Validate signals, confirm on "
                "15m candles, then place the order via MT5 with a hard SL and "
                "tiered TPs. Enforce 2% risk, 3-trade max, 5% daily drawdown stop."
            ),
            verbose=verbose,
        )
        self.mt5_provider: Optional["MT5Provider"] = mt5_provider
        self.open_trades: List[ExecutionRecord] = []

        # Daily loss tracking — resets at UTC day boundary
        self.daily_loss: float = 0.0
        self._session_date: date = datetime.now(timezone.utc).date()

        # Consecutive-loss position-size reduction
        self.consecutive_losses: int = 0
        self.reduced_sizing_remaining: int = 0

        # Background monitor tasks indexed by MT5 ticket
        self._monitor_tasks: Dict[int, asyncio.Task] = {}

        # Lock for atomic check-and-append of open_trades
        self._trade_lock: asyncio.Lock = asyncio.Lock()

        # Restore daily_loss from DB so circuit breaker works after restart
        self._load_daily_loss()

    # ------------------------------------------------------------------
    # Day-boundary reset
    # ------------------------------------------------------------------

    def _check_day_reset(self) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self._session_date:
            self.logger.info(
                "[TRADER-MASTER] New trading day %s — resetting daily_loss (was %.2f%%)",
                today, self.daily_loss * 100,
            )
            self.daily_loss = 0.0
            self._session_date = today

    # ------------------------------------------------------------------
    # Crash-recovery: rebuild open_trades from MT5 on startup
    # ------------------------------------------------------------------

    async def reconcile_open_trades(self) -> None:
        """
        Called once at startup. Loads open positions from MT5 and reconstructs
        the in-memory open_trades list so concurrent-trade and drawdown guards
        work correctly after a process restart.
        """
        if self.mt5_provider is None:
            return
        try:
            positions = await self.mt5_provider.get_open_positions()
        except Exception as exc:
            self.logger.warning("[TRADER-MASTER] reconcile failed: %s", exc)
            return

        for pos in positions:
            if pos.get("magic") == 202600:   # only positions opened by this system
                rec = ExecutionRecord(
                    signal_id     = f"RECOVERED-{pos['ticket']}",
                    entry_price   = float(pos["price_open"]),
                    entry_time    = datetime.now(),
                    position_size = float(pos["volume"]),
                    stop_loss     = float(pos["sl"]),
                    take_profit_1 = float(pos["tp"]),
                    take_profit_2 = float(pos["tp"]),
                    take_profit_3 = float(pos["tp"]),
                    status        = "OPEN",
                    symbol        = pos["symbol"],
                    direction     = pos["type"],
                    mt5_ticket    = pos["ticket"],
                )
                self.open_trades.append(rec)
                self._launch_monitor(rec)
                self.logger.info(
                    "[TRADER-MASTER] Recovered position: ticket=%d %s %s",
                    pos["ticket"], pos["type"], pos["symbol"],
                )

        if positions:
            self.logger.info("[TRADER-MASTER] Reconciled %d open position(s)", len(positions))

    # ------------------------------------------------------------------
    # Consecutive-loss streak management
    # ------------------------------------------------------------------

    def _record_trade_outcome(self, pnl: float) -> None:
        """Update streak counters and persist daily P&L.  Call after each trade closes."""
        if pnl < 0:
            self.consecutive_losses += 1
            # Accumulate daily loss (as fraction of account) so circuit breaker works
            balance = max(getattr(settings, "ACCOUNT_BALANCE", 10000.0), 1.0)
            self.daily_loss += abs(pnl) / balance
            if self.consecutive_losses >= CONSECUTIVE_LOSS_LIMIT:
                self.reduced_sizing_remaining = SIZE_REDUCTION_TRADES
                self.consecutive_losses = 0
                self.logger.warning(
                    "[TRADER-MASTER] %d consecutive losses — position size halved "
                    "for next %d trades",
                    CONSECUTIVE_LOSS_LIMIT, SIZE_REDUCTION_TRADES,
                )
        else:
            self.consecutive_losses = 0

        # Persist daily P&L to DB so it survives process restarts
        self._persist_daily_loss(pnl)

    def _persist_daily_loss(self, pnl: float) -> None:
        """Write today's running P&L to the database for crash-recovery."""
        try:
            from database.db_manager import db_manager
            from database.models import PerformanceMetric
            from datetime import datetime
            today = datetime.utcnow().strftime("%Y-%m-%d")
            session = db_manager.get_session()
            try:
                row = session.query(PerformanceMetric).filter_by(date=today).first()
                if row:
                    row.daily_pnl = (row.daily_pnl or 0.0) + pnl
                else:
                    session.add(PerformanceMetric(date=today, daily_pnl=pnl))
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
        except Exception as exc:
            # Don't crash the trade flow on a DB write failure — log and continue
            self.logger.debug("[TRADER-MASTER] daily_loss persist skipped: %s", exc)

    def _load_daily_loss(self) -> None:
        """Restore today's running P&L from DB on startup."""
        try:
            from database.db_manager import db_manager
            from database.models import PerformanceMetric
            from datetime import datetime
            today = datetime.utcnow().strftime("%Y-%m-%d")
            session = db_manager.get_session()
            try:
                row = session.query(PerformanceMetric).filter_by(date=today).first()
                if row and row.daily_pnl is not None:
                    balance = max(getattr(settings, "ACCOUNT_BALANCE", 10000.0), 1.0)
                    self.daily_loss = abs(row.daily_pnl) / balance
                    self.logger.info(
                        "[TRADER-MASTER] Restored daily_loss=%.2f%% from DB (today=%s)",
                        self.daily_loss * 100, today,
                    )
            finally:
                session.close()
        except Exception as exc:
            self.logger.debug("[TRADER-MASTER] daily_loss restore skipped: %s", exc)

    # ------------------------------------------------------------------
    # Position sizing (instrument-aware)
    # ------------------------------------------------------------------

    def _lot_size(
        self,
        symbol:       str,
        entry:        float,
        sl:           float,
        balance:      float,
        risk_mult:    float = 1.0,
        adjusted_pct: Optional[float] = None,
        atr:          Optional[float] = None,
    ) -> float:
        """
        Calculate position size respecting user risk settings.

        Priority:
          1. adjusted_pct from Risk-Sentinel (already incorporates user risk_pct)
          2. User risk_pct from RiskSettingsManager
          3. Constants fallback (MAX_RISK_PER_TRADE)

        sizing_mode in {"fixed", "percentage", "volatility", "equity_scaling"}.

        `atr` (current H1 ATR) is required when sizing_mode == "volatility";
        when omitted, falls back to 0.80 haircut with a warning.
        """
        s    = RiskSettingsManager.get()
        spec = get_instrument_spec(symbol)
        max_lots = spec.get("max_lot_size", 100.0)
        min_lots = spec.get("min_lot_size", 0.01)

        # ── Fixed lot mode ─────────────────────────────────────────────
        if s.sizing_mode == "fixed":
            return round(max(min_lots, min(max_lots, s.fixed_lot_size * risk_mult)), 2)

        pip_size = spec["pip_size"]
        pip_val  = spec["pip_value_per_lot"]
        risk_price = abs(entry - sl)
        if risk_price == 0:
            return min_lots
        risk_pips = risk_price / pip_size
        if risk_pips == 0:
            return min_lots

        # Effective risk % — prefer Risk-Sentinel adjusted value
        effective_pct = (
            adjusted_pct
            if adjusted_pct is not None
            else s.risk_pct / 100.0
        )
        dollars = balance * effective_pct
        raw     = dollars / (risk_pips * pip_val)

        # ── Volatility mode: scale inversely to ATR vs. average ATR ────
        if s.sizing_mode == "volatility":
            if atr and atr > 0:
                # avg_atr: typical 14-period ATR for the symbol's pip threshold.
                # Scale lots down when current ATR is above average (hot market),
                # scale up when ATR is below average (calm market).
                avg_atr = spec["pip_threshold"] * 100  # heuristic baseline
                vol_mult = max(0.25, min(1.5, avg_atr / atr))
                raw *= vol_mult
            else:
                self.logger.warning(
                    "[TRADER] volatility mode but no ATR provided — using 0.80 haircut"
                )
                raw *= 0.80

        raw = round(max(min_lots, min(max_lots, raw * risk_mult)), 2)
        return raw

    # ------------------------------------------------------------------
    # Kill-zone validity check
    # ------------------------------------------------------------------

    def _within_kill_zone(self, signal: Dict[str, Any]) -> bool:
        try:
            end = datetime.fromisoformat(signal["kill_zone_end"])
            now = datetime.now(end.tzinfo) if end.tzinfo else datetime.now()
            return now < end
        except (KeyError, ValueError):
            self.logger.warning("[TRADER] kill_zone_end missing/malformed — rejecting trade")
            return False

    # ------------------------------------------------------------------
    # ATR helper (same formula as Analyse-Master)
    # ------------------------------------------------------------------

    def _atr(self, candles: List["OHLCData"], period: int = 14) -> float:
        """Compute ATR from a list of OHLCData candles."""
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
        return sum(trs[-period:]) / period if len(trs) >= period else sum(trs) / max(len(trs), 1)

    # ------------------------------------------------------------------
    # Lower-timeframe entry confirmation
    # ------------------------------------------------------------------

    def _lower_tf_entry(
        self,
        candles:  "List[OHLCData]",
        bias:     str,
        zone_bot: float,
        zone_top: float,
        symbol:   str,
    ) -> Tuple[bool, float]:
        """Find a confirmation candle within the OB/FVG zone on 15m or 5m."""
        if not candles or zone_bot is None or zone_top is None:
            return False, 0.0

        spec   = get_instrument_spec(symbol)
        buf    = spec["sl_buffer"]
        recent = candles[-LOWER_TF_LOOKBACK:]

        for c in reversed(recent):
            if bias == "BULLISH":
                in_zone = c.low <= zone_top + buf and c.low >= zone_bot - buf
                if in_zone and c.close > zone_bot:
                    return True, round(c.close, 5)
            elif bias == "BEARISH":
                in_zone = c.high >= zone_bot - buf and c.high <= zone_top + buf
                if in_zone and c.close < zone_top:
                    return True, round(c.close, 5)

        return False, 0.0

    # ------------------------------------------------------------------
    # Background position monitor (TP1 partial close + BE move)
    # ------------------------------------------------------------------

    def _launch_monitor(self, execution: ExecutionRecord) -> None:
        """Start the background monitoring task for a live trade."""
        if execution.mt5_ticket is None or self.mt5_provider is None:
            return
        task = asyncio.create_task(
            self._monitor_trade(execution),
            name=f"monitor-{execution.mt5_ticket}",
        )
        self._monitor_tasks[execution.mt5_ticket] = task
        self.logger.info(
            "[TRADER-MASTER] Monitor launched for ticket=%d %s %s",
            execution.mt5_ticket, execution.direction, execution.symbol,
        )

    async def _monitor_trade(self, execution: ExecutionRecord) -> None:
        """
        Poll MT5 every 60 seconds.  Handles:
        - TP1: close 50% of position, move SL to break-even
        - TP2: close 30% of remaining position
        - Position no longer found: record as closed (SL or TP3 trail)
        """
        POLL_INTERVAL = 60
        TRAILING_STOP_PIPS = 10   # pips to trail behind the running high/low
        MAX_CONSECUTIVE_ERRORS = 10
        consecutive_errors = 0

        # Track last known price so we can compute P&L if the position disappears
        last_known_price: float = execution.entry_price

        while True:
            await asyncio.sleep(POLL_INTERVAL)

            if self.mt5_provider is None:
                break

            try:
                pos = await self.mt5_provider.get_position_by_ticket(execution.mt5_ticket)
                consecutive_errors = 0  # reset on success
            except Exception as exc:
                consecutive_errors += 1
                self.logger.warning("[MONITOR] ticket=%d poll error %d/%d: %s",
                                    execution.mt5_ticket, consecutive_errors,
                                    MAX_CONSECUTIVE_ERRORS, exc)
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    self.logger.error(
                        "[MONITOR] ticket=%d aborted after %d consecutive errors",
                        execution.mt5_ticket, MAX_CONSECUTIVE_ERRORS,
                    )
                    self._monitor_tasks.pop(execution.mt5_ticket, None)
                    return
                continue

            if pos is None:
                # Position closed by broker (SL/TP/trail). Compute P&L from the
                # last observed price so the daily-drawdown circuit breaker and
                # consecutive-loss counter actually fire.
                # remaining_volume: only the portion still open is settled
                remaining_vol = execution.position_size
                if execution.tp1_hit:
                    remaining_vol -= round(execution.position_size * 0.50, 2)
                if execution.tp2_hit:
                    remaining_vol -= round(execution.position_size * 0.30, 2)
                remaining_vol = max(remaining_vol, 0.0)

                if execution.direction == "BUY":
                    closed_pnl = (last_known_price - execution.entry_price) * remaining_vol
                else:
                    closed_pnl = (execution.entry_price - last_known_price) * remaining_vol

                execution.p_and_l = (execution.p_and_l or 0.0) + closed_pnl
                execution.exit_price = last_known_price
                execution.status = "CLOSED"
                execution.exit_time = datetime.now()
                execution.exit_reason = "BROKER_CLOSE"
                self.logger.info(
                    "[MONITOR] ticket=%d %s %s — closed by broker @ %.5f (P&L=%.2f)",
                    execution.mt5_ticket, execution.direction, execution.symbol,
                    last_known_price, closed_pnl,
                )
                self._record_trade_outcome(execution.p_and_l)
                self._monitor_tasks.pop(execution.mt5_ticket, None)
                break

            current_price = float(pos.get("price_current", pos["price_open"]))
            last_known_price = current_price

            # ── TP1 check ──────────────────────────────────────────────
            if not execution.tp1_hit:
                tp1_reached = (
                    (execution.direction == "BUY"  and current_price >= execution.take_profit_1) or
                    (execution.direction == "SELL" and current_price <= execution.take_profit_1)
                )
                if tp1_reached:
                    half_vol = round(execution.position_size * 0.50, 2)
                    if half_vol >= 0.01:
                        ok = await self.mt5_provider.close_position(
                            ticket     = execution.mt5_ticket,
                            symbol     = execution.symbol,
                            volume     = half_vol,
                            order_type = execution.direction,
                        )
                        if ok:
                            execution.tp1_hit = True
                            sl_ok = await self.mt5_provider.modify_sl(
                                ticket = execution.mt5_ticket,
                                symbol = execution.symbol,
                                new_sl = execution.entry_price,   # move to break-even
                            )
                            if sl_ok:
                                self.logger.info(
                                    "[MONITOR] TP1 hit — closed 50%% @ %.5f, SL → BE %.5f (ticket=%d)",
                                    execution.take_profit_1, execution.entry_price,
                                    execution.mt5_ticket,
                                )
                            else:
                                self.logger.error(
                                    "[MONITOR] TP1 hit — closed 50%% @ %.5f but FAILED to move SL to BE "
                                    "(ticket=%d). Remaining 50%% riding with ORIGINAL SL %.5f — manual review required.",
                                    execution.take_profit_1, execution.mt5_ticket,
                                    execution.stop_loss,
                                )

            # ── TP2 check ──────────────────────────────────────────────
            elif not execution.tp2_hit:
                tp2_reached = (
                    (execution.direction == "BUY"  and current_price >= execution.take_profit_2) or
                    (execution.direction == "SELL" and current_price <= execution.take_profit_2)
                )
                if tp2_reached:
                    # Close 30% of the ORIGINAL size (≈ 60% of remaining half)
                    close_vol = round(execution.position_size * 0.30, 2)
                    if close_vol >= 0.01:
                        ok = await self.mt5_provider.close_position(
                            ticket     = execution.mt5_ticket,
                            symbol     = execution.symbol,
                            volume     = close_vol,
                            order_type = execution.direction,
                        )
                        if ok:
                            execution.tp2_hit = True
                            # Initialise the trailing-stop state for the
                            # remaining 20% of the position.
                            execution.trail_high_water = current_price
                            execution.trail_sl = self._calc_trail_sl(
                                current_price, execution.direction, execution.symbol,
                                TRAILING_STOP_PIPS,
                            )
                            self.logger.info(
                                "[MONITOR] TP2 hit — closed 30%% @ %.5f; trailing 20%% with "
                                "SL=%.5f (ticket=%d)",
                                execution.take_profit_2, execution.trail_sl,
                                execution.mt5_ticket,
                            )
                            # Don't return — keep monitoring the trailing 20%.

            # ── Trailing stop on remaining 20% (after TP2) ─────────────
            if execution.tp2_hit and execution.tp1_hit:
                if execution.direction == "BUY":
                    if current_price > (execution.trail_high_water or 0):
                        execution.trail_high_water = current_price
                    new_sl = self._calc_trail_sl(
                        execution.trail_high_water, "BUY", execution.symbol,
                        TRAILING_STOP_PIPS,
                    )
                    if new_sl > (execution.trail_sl or 0):
                        ok = await self.mt5_provider.modify_sl(
                            ticket=execution.mt5_ticket,
                            symbol=execution.symbol,
                            new_sl=new_sl,
                        )
                        if ok:
                            execution.trail_sl = new_sl
                            self.logger.info(
                                "[MONITOR] Trailing SL raised → %.5f (ticket=%d)",
                                new_sl, execution.mt5_ticket,
                            )
                else:  # SELL
                    if execution.trail_high_water is None or current_price < execution.trail_high_water:
                        execution.trail_high_water = current_price
                    new_sl = self._calc_trail_sl(
                        execution.trail_high_water, "SELL", execution.symbol,
                        TRAILING_STOP_PIPS,
                    )
                    # For SELL, trail_sl is above price — new_sl < current means
                    # tighten (lower) the SL as price falls.
                    if execution.trail_sl is None or new_sl < execution.trail_sl:
                        ok = await self.mt5_provider.modify_sl(
                            ticket=execution.mt5_ticket,
                            symbol=execution.symbol,
                            new_sl=new_sl,
                        )
                        if ok:
                            execution.trail_sl = new_sl
                            self.logger.info(
                                "[MONITOR] Trailing SL lowered → %.5f (ticket=%d)",
                                new_sl, execution.mt5_ticket,
                            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze(
        self,
        trade_signal: Dict[str, Any],
        market_data:  Optional[Dict[str, Any]] = None,
    ) -> Optional[ExecutionRecord]:
        """
        Validate and execute a trade from a confirmed TradeSignal.

        Args:
            trade_signal: TradeSignal.to_dict() from Analyse-Master
            market_data:  Full market data dict for 15m/5m LTF entry refinement
        """
        # ── Day-boundary reset ─────────────────────────────────────────
        self._check_day_reset()

        # ── Kill switch ────────────────────────────────────────────────
        try:
            KillSwitch.check()
        except RuntimeError as exc:
            self.logger.warning("[TRADER-MASTER] %s", exc)
            return None

        # ── Input validation ───────────────────────────────────────────
        if not await self.validate_input(
            trade_signal, ["entry_level", "stop_loss", "confidence", "symbol", "direction"]
        ):
            self.logger.warning("[TRADER-MASTER] Invalid signal — rejected")
            return None

        entry_price: float = float(trade_signal["entry_level"])
        stop_loss:   float = float(trade_signal["stop_loss"])
        confidence:  float = float(trade_signal.get("confidence", 0))
        rr:          float = float(trade_signal.get("risk_reward_ratio", 0))
        symbol:      str   = trade_signal["symbol"]
        direction:   str   = trade_signal["direction"]
        bias:        str   = "BULLISH" if direction == "BUY" else "BEARISH"
        entry_type:  str   = trade_signal.get("entry_type", "ORDER_BLOCK")
        session:     str   = trade_signal.get("session", "")
        zone_top:    float = float(trade_signal.get("zone_top",    entry_price))
        zone_bot:    float = float(trade_signal.get("zone_bottom", entry_price))

        # ── User risk settings (always read fresh — UI changes apply immediately) ──
        s = RiskSettingsManager.get()
        effective_min_conf = s.min_confidence_pct if s.auto_risk_management else MIN_CONFIDENCE_PCT
        effective_min_rr   = s.rr_ratio           if s.auto_risk_management else MIN_RR_RATIO
        effective_max_dd   = s.max_daily_loss_pct / 100.0 if s.auto_risk_management else MAX_DAILY_DRAWDOWN
        effective_max_ct   = s.max_concurrent_trades      if s.auto_risk_management else MAX_CONCURRENT_TRADES

        # ── Risk-Sentinel override values (passed via signal dict) ─────
        ext_risk_mult    = float(trade_signal.get("_risk_multiplier",   1.0))
        ext_adjusted_pct = trade_signal.get("_adjusted_risk_pct")       # may be None
        regime_mult      = float(trade_signal.get("_regime_risk_multiplier", 1.0))

        if ext_adjusted_pct is not None:
            ext_adjusted_pct = float(ext_adjusted_pct) / 100.0   # convert % to fraction

        # ── Pre-execution guardrails ───────────────────────────────────
        if confidence < effective_min_conf:
            self.logger.warning(
                "[TRADER-MASTER] Confidence %.1f%% < %.1f%% (user setting) — rejected",
                confidence, effective_min_conf,
            )
            return None

        if rr < effective_min_rr:
            self.logger.warning(
                "[TRADER-MASTER] R:R %.2f < %.2f (user setting) — rejected",
                rr, effective_min_rr,
            )
            return None

        async with self._trade_lock:
            active = [t for t in self.open_trades if t.status in ("PENDING", "OPEN")]
            if len(active) >= effective_max_ct:
                self.logger.warning(
                    "[TRADER-MASTER] Max concurrent trades (%d) reached — rejected",
                    effective_max_ct,
                )
                return None

            # ── Daily drawdown ─────────────────────────────────────────
            if self.daily_loss >= effective_max_dd:
                self.logger.warning(
                    "[TRADER-MASTER] Daily drawdown %.1f%% ≥ limit %.1f%% — pausing",
                    self.daily_loss * 100, effective_max_dd * 100,
                )
                KillSwitch.pause(f"Daily drawdown {self.daily_loss*100:.1f}% exceeded")
                return None

            if not self._within_kill_zone(trade_signal):
                self.logger.warning("[TRADER-MASTER] Kill zone expired — rejected")
                return None

        # ── Consecutive loss sizing adjustment ─────────────────────────
        # ext_risk_mult from Risk-Sentinel already incorporates consecutive-loss
        # scaling; if not provided fall back to the legacy counter.
        risk_mult = ext_risk_mult * regime_mult
        if ext_risk_mult == 1.0 and self.reduced_sizing_remaining > 0:
            risk_mult = s.consecutive_loss_size_factor * regime_mult
            self.reduced_sizing_remaining -= 1
            self.logger.info(
                "[TRADER-MASTER] Reduced sizing active — %.0f%% size (%d trades remaining)",
                risk_mult * 100, self.reduced_sizing_remaining,
            )

        # ── Lower-TF entry refinement ──────────────────────────────────
        lower_tf_confirmed = False
        if market_data:
            for tf_key in ("15m", "5m"):
                tf_candles = market_data.get(tf_key, [])
                if tf_candles:
                    confirmed, precise_entry = self._lower_tf_entry(
                        tf_candles, bias, zone_bot, zone_top, symbol
                    )
                    if confirmed:
                        self.logger.info(
                            "[TRADER-MASTER] %s LTF confirmation on %s → %.5f (was %.5f)",
                            entry_type, tf_key.upper(), precise_entry, entry_price,
                        )
                        entry_price = precise_entry
                        lower_tf_confirmed = True
                        break

        if not lower_tf_confirmed:
            self.logger.info(
                "[TRADER-MASTER] No LTF confirmation — using zone midpoint %.5f", entry_price
            )

        # ── Account balance ────────────────────────────────────────────
        balance: float = settings.ACCOUNT_BALANCE
        if self.mt5_provider is not None:
            live = await self.mt5_provider.get_account_balance()
            if live > 0:
                balance = live

        # ── Current ATR (for volatility-mode sizing) ───────────────────
        current_atr: Optional[float] = None
        if market_data:
            h1 = market_data.get("1h", [])
            if len(h1) >= 15:
                current_atr = self._atr(h1, period=14)

        # ── Position size (user settings + Risk-Sentinel multiplier) ──
        raw_lots = self._lot_size(
            symbol,
            entry_price,
            stop_loss,
            balance,
            risk_mult    = risk_mult,
            adjusted_pct = ext_adjusted_pct,
            atr          = current_atr,
        )
        lots = raw_lots  # _lot_size already clamps to instrument-specific min/max

        # ── Build execution record ─────────────────────────────────────
        signal_id = f"SIG-{uuid.uuid4().hex[:8].upper()}"
        execution = ExecutionRecord(
            signal_id     = signal_id,
            entry_price   = entry_price,
            entry_time    = datetime.now(),
            position_size = lots,
            stop_loss     = stop_loss,
            take_profit_1 = float(trade_signal.get("take_profit_1", 0)),
            take_profit_2 = float(trade_signal.get("take_profit_2", 0)),
            take_profit_3 = float(trade_signal.get("take_profit_3", 0)),
            status        = "PENDING",
            entry_type    = entry_type,
            session       = session,
            symbol        = symbol,
            direction     = direction,
        )

        # ── Send to MT5 ────────────────────────────────────────────────
        if self.mt5_provider is not None:
            ticket = await self.mt5_provider.place_order(
                symbol      = symbol,
                order_type  = direction,
                volume      = lots,
                price       = entry_price,
                stop_loss   = stop_loss,
                take_profit = execution.take_profit_1,
                comment     = f"TechnobizTrader-{signal_id}",
            )
            if ticket is not None:
                execution.mt5_ticket = ticket
                execution.status = "OPEN"
                self.logger.info(
                    "[TRADER-MASTER] Order placed ✓ ticket=%d %s %s %.2f lots @ %.5f",
                    ticket, direction, symbol, lots, entry_price,
                )
                self._launch_monitor(execution)
            else:
                self.logger.error(
                    "[TRADER-MASTER] MT5 order failed — signal %s not placed", signal_id
                )
                return None
        else:
            self.logger.warning(
                "[TRADER-MASTER] No MT5 provider — paper trade (signal %s)", signal_id
            )

        # ── Atomic append with re-check (prevents race after MT5 order) ──
        async with self._trade_lock:
            active = [t for t in self.open_trades if t.status in ("PENDING", "OPEN")]
            if len(active) >= effective_max_ct:
                self.logger.error(
                    "[TRADER-MASTER] Race — concurrent limit (%d) exceeded after MT5 order. "
                    "Ticket=%d placed but NOT tracked. Manual review required.",
                    effective_max_ct, execution.mt5_ticket,
                )
                return None
            self.open_trades.append(execution)

        self.logger.info(
            "[TRADER-MASTER] ✓ %s | %s | Session=%s | Entry=%.5f | SL=%.5f | "
            "TP2=%.5f | Size=%.2f lots | Conf=%.1f%%",
            signal_id, entry_type, session.upper(),
            entry_price, stop_loss, execution.take_profit_2, lots, confidence,
        )
        return execution
