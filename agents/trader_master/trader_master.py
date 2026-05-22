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
            if pos.get("magic") == 202600 or True:   # accept all our positions
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
        """Update streak counters.  Call after each trade closes."""
        if pnl < 0:
            self.consecutive_losses += 1
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
    ) -> float:
        """
        Calculate position size respecting user risk settings.

        Priority:
          1. adjusted_pct from Risk-Sentinel (already incorporates user risk_pct)
          2. User risk_pct from RiskSettingsManager
          3. Constants fallback (MAX_RISK_PER_TRADE)

        sizing_mode in {"fixed", "percentage", "volatility", "equity_scaling"}.
        """
        s    = RiskSettingsManager.get()
        spec = get_instrument_spec(symbol)

        # ── Fixed lot mode ─────────────────────────────────────────────
        if s.sizing_mode == "fixed":
            return round(max(0.01, min(10.0, s.fixed_lot_size * risk_mult)), 2)

        pip_size = spec["pip_size"]
        pip_val  = spec["pip_value_per_lot"]
        risk_price = abs(entry - sl)
        if risk_price == 0:
            return 0.01
        risk_pips = risk_price / pip_size
        if risk_pips == 0:
            return 0.01

        # Effective risk % — prefer Risk-Sentinel adjusted value
        effective_pct = (
            adjusted_pct
            if adjusted_pct is not None
            else s.risk_pct / 100.0
        )
        dollars = balance * effective_pct
        raw     = dollars / (risk_pips * pip_val)

        # ── Volatility mode: scale down when ATR is elevated ──────────
        if s.sizing_mode == "volatility":
            raw *= 0.80   # conservative without live ATR here; agents apply full scaling

        raw = round(max(0.01, min(10.0, raw * risk_mult)), 2)
        return raw

    # ------------------------------------------------------------------
    # Kill-zone validity check
    # ------------------------------------------------------------------

    def _within_kill_zone(self, signal: Dict[str, Any]) -> bool:
        try:
            end = datetime.fromisoformat(signal["kill_zone_end"])
            now = datetime.now(end.tzinfo) if end.tzinfo else datetime.now()
            return now <= end
        except (KeyError, ValueError):
            return True

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

        while True:
            await asyncio.sleep(POLL_INTERVAL)

            if self.mt5_provider is None:
                break

            try:
                pos = await self.mt5_provider.get_position_by_ticket(execution.mt5_ticket)
            except Exception as exc:
                self.logger.warning("[MONITOR] ticket=%d poll error: %s",
                                    execution.mt5_ticket, exc)
                continue

            if pos is None:
                # Position closed by broker (SL/TP/trail)
                execution.status = "CLOSED"
                execution.exit_time = datetime.now()
                execution.exit_reason = "BROKER_CLOSE"
                self.logger.info(
                    "[MONITOR] ticket=%d %s %s — position closed by broker",
                    execution.mt5_ticket, execution.direction, execution.symbol,
                )
                self._record_trade_outcome(execution.p_and_l or 0.0)
                break

            current_price = float(pos.get("price_current", pos["price_open"]))

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
                            await self.mt5_provider.modify_sl(
                                ticket = execution.mt5_ticket,
                                symbol = execution.symbol,
                                new_sl = execution.entry_price,   # move to break-even
                            )
                            self.logger.info(
                                "[MONITOR] TP1 hit — closed 50%% @ %.5f, SL → BE %.5f (ticket=%d)",
                                execution.take_profit_1, execution.entry_price,
                                execution.mt5_ticket,
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
                            self.logger.info(
                                "[MONITOR] TP2 hit — closed 30%% @ %.5f (ticket=%d)",
                                execution.take_profit_2, execution.mt5_ticket,
                            )
                            # Remaining 20% rides with trailing stop (set via MT5 terminal)

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

        active = [t for t in self.open_trades if t.status in ("PENDING", "OPEN")]
        if len(active) >= effective_max_ct:
            self.logger.warning(
                "[TRADER-MASTER] Max concurrent trades (%d) reached — rejected",
                effective_max_ct,
            )
            return None

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

        # ── Position size (user settings + Risk-Sentinel multiplier) ──
        raw_lots = self._lot_size(
            symbol,
            entry_price,
            stop_loss,
            balance,
            risk_mult    = risk_mult,
            adjusted_pct = ext_adjusted_pct,
        )
        lots = round(max(0.01, min(10.0, raw_lots)), 2)

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

        self.open_trades.append(execution)

        self.logger.info(
            "[TRADER-MASTER] ✓ %s | %s | Session=%s | Entry=%.5f | SL=%.5f | "
            "TP2=%.5f | Size=%.2f lots | Conf=%.1f%%",
            signal_id, entry_type, session.upper(),
            entry_price, stop_loss, execution.take_profit_2, lots, confidence,
        )
        return execution
