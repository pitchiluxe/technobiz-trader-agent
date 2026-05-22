"""Backtester Agent — historical signal performance analyser.

Reads closed trade records from the database and produces a BacktestSummary
that the workflow uses to:
  1. Adjust signal confidence based on historical win rate for this setup type.
  2. Inform the Risk-Sentinel of the system's recent performance trajectory.
  3. Provide the GUI with P&L attribution and Monte Carlo projections.

Key metrics produced:
  overall_win_rate       : float   — across all closed trades
  session_win_rates      : dict    — by session (london, new_york)
  pattern_win_rates      : dict    — by entry type (ORDER_BLOCK, FVG, BREAKER_BLOCK)
  symbol_win_rates       : dict    — per trading pair
  avg_rr_achieved        : float   — actual realised R:R (not predicted)
  profit_factor          : float   — gross_profit / gross_loss
  confidence_multiplier  : float   — adjustment to apply to live signal confidence
  monte_carlo_max_dd     : float   — 95th-percentile max drawdown from MC simulation
  consecutive_loss_risk  : float   — probability of hitting N consecutive losses
  sample_size            : int     — number of closed trades analysed
"""

from __future__ import annotations

import logging
import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

_MIN_SAMPLE = 10   # minimum trades needed for meaningful statistics


class BacktestSummary:
    """Output model for Backtester Agent."""

    def __init__(
        self,
        overall_win_rate:      float,
        session_win_rates:     Dict[str, float],
        pattern_win_rates:     Dict[str, float],
        symbol_win_rates:      Dict[str, float],
        avg_rr_achieved:       float,
        profit_factor:         float,
        confidence_multiplier: float,
        monte_carlo_max_dd:    float,
        consecutive_loss_risk: float,
        sample_size:           int,
        timestamp:             Optional[datetime] = None,
    ) -> None:
        self.overall_win_rate      = overall_win_rate
        self.session_win_rates     = session_win_rates
        self.pattern_win_rates     = pattern_win_rates
        self.symbol_win_rates      = symbol_win_rates
        self.avg_rr_achieved       = avg_rr_achieved
        self.profit_factor         = profit_factor
        self.confidence_multiplier = confidence_multiplier
        self.monte_carlo_max_dd    = monte_carlo_max_dd
        self.consecutive_loss_risk = consecutive_loss_risk
        self.sample_size           = sample_size
        self.timestamp             = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_win_rate":      round(self.overall_win_rate, 3),
            "session_win_rates":     self.session_win_rates,
            "pattern_win_rates":     self.pattern_win_rates,
            "symbol_win_rates":      self.symbol_win_rates,
            "avg_rr_achieved":       round(self.avg_rr_achieved, 2),
            "profit_factor":         round(self.profit_factor, 2),
            "confidence_multiplier": round(self.confidence_multiplier, 3),
            "monte_carlo_max_dd":    round(self.monte_carlo_max_dd, 4),
            "consecutive_loss_risk": round(self.consecutive_loss_risk, 3),
            "sample_size":           self.sample_size,
            "timestamp":             self.timestamp.isoformat(),
        }

    @staticmethod
    def insufficient_data() -> "BacktestSummary":
        """Neutral summary when trade history is too thin for reliable statistics."""
        return BacktestSummary(
            overall_win_rate=0.0, session_win_rates={}, pattern_win_rates={},
            symbol_win_rates={}, avg_rr_achieved=0.0, profit_factor=1.0,
            confidence_multiplier=1.0, monte_carlo_max_dd=0.0,
            consecutive_loss_risk=0.0, sample_size=0,
        )


class Backtester(BaseAgent):
    """
    Backtester Agent — reads closed trade history from DB and returns
    performance analytics that gate and scale live trading decisions.
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="Backtester",
            instructions=(
                "You are the Backtester Agent. Read historical closed-trade records "
                "and return statistical performance summaries. Compute win rate, "
                "profit factor, Monte Carlo drawdown projections, and a "
                "confidence_multiplier that the workflow applies to live signals."
            ),
            verbose=verbose,
        )

    # ------------------------------------------------------------------
    # DB load
    # ------------------------------------------------------------------

    def _load_closed_trades(self) -> List[Dict[str, Any]]:
        """Load closed trade execution records from DB."""
        try:
            from database.db_manager import db_manager
            from database.models import TradeExecution

            session = db_manager.get_session()
            try:
                rows = (
                    session.query(TradeExecution)
                    .filter(TradeExecution.status == "CLOSED")
                    .order_by(TradeExecution.timestamp.desc())
                    .limit(500)
                    .all()
                )
                result = []
                for r in rows:
                    result.append({
                        "symbol":     r.pair or "",
                        "session":    "",        # TradeExecution doesn't store session; signal join needed
                        "entry_type": "",        # same
                        "pnl":        r.pnl or 0.0,
                        "tp1_hit":    r.tp1_hit,
                        "tp2_hit":    r.tp2_hit,
                        "sl":         r.stop_loss,
                        "entry":      r.entry_price,
                        "exit":       r.exit_price or r.entry_price,
                        "direction":  r.direction or "BUY",
                    })
                return result
            finally:
                session.close()
        except Exception as exc:
            self.logger.warning("[BACKTESTER] DB load failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def _win_rate(self, trades: List[Dict[str, Any]]) -> float:
        if not trades:
            return 0.0
        winners = sum(1 for t in trades if t["pnl"] > 0)
        return winners / len(trades)

    def _profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        gross_profit = sum(t["pnl"] for t in trades if t["pnl"] > 0)
        gross_loss   = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0))
        return (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit or 1.0)

    def _avg_rr(self, trades: List[Dict[str, Any]]) -> float:
        """Compute average realised R:R from pnl relative to SL distance."""
        rr_vals = []
        for t in trades:
            risk = abs(t["entry"] - t["sl"])
            if risk > 0:
                rr_vals.append(abs(t["pnl"]) / risk)
        return sum(rr_vals) / len(rr_vals) if rr_vals else 0.0

    def _group_win_rates(
        self, trades: List[Dict[str, Any]], key: str
    ) -> Dict[str, float]:
        groups: Dict[str, List[Dict]] = {}
        for t in trades:
            k = t.get(key, "unknown") or "unknown"
            groups.setdefault(k, []).append(t)
        return {k: self._win_rate(v) for k, v in groups.items()}

    # ------------------------------------------------------------------
    # Monte Carlo
    # ------------------------------------------------------------------

    def _monte_carlo_max_dd(
        self,
        win_rate: float,
        avg_win:  float,
        avg_loss: float,
        n_trades: int = 200,
        n_sims:   int = 1000,
        risk_pct: float = 0.02,
    ) -> float:
        """
        Simulate n_sims equity curves of n_trades each.
        Returns the 95th-percentile maximum drawdown as a fraction.
        """
        if avg_loss == 0 or win_rate <= 0:
            return 0.0

        max_dds = []
        for _ in range(n_sims):
            equity     = 1.0
            peak       = 1.0
            max_dd     = 0.0
            for _ in range(n_trades):
                win = random.random() < win_rate
                equity *= (1 + risk_pct * avg_win) if win else (1 - risk_pct)
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd
            max_dds.append(max_dd)

        max_dds.sort()
        return max_dds[int(0.95 * len(max_dds))]

    def _consecutive_loss_risk(self, win_rate: float, n: int = 3) -> float:
        """Probability of hitting n consecutive losses in a 100-trade sequence."""
        if win_rate >= 1.0:
            return 0.0
        loss_rate = 1.0 - win_rate
        # P(at least one streak of n) ≈ 1 - (1 - loss_rate^n)^(100/n)
        p_streak = loss_rate ** n
        return 1.0 - (1.0 - p_streak) ** max(1, 100 // n)

    # ------------------------------------------------------------------
    # Confidence multiplier
    # ------------------------------------------------------------------

    def _confidence_multiplier(
        self, win_rate: float, profit_factor: float, sample_size: int
    ) -> float:
        """
        Scale factor to apply to live signal confidence.
        > 1.0 : system is performing above the 60% target → boost
        = 1.0 : system is performing at target
        < 1.0 : system is underperforming → reduce
        Clamped to [0.60, 1.20].
        """
        if sample_size < _MIN_SAMPLE:
            return 1.0   # no adjustment without enough data
        target_wr = 0.60
        wr_factor  = win_rate / target_wr          # 1.0 at target
        pf_factor  = min(profit_factor / 1.5, 1.5)  # 1.0 at PF=1.5
        raw = (wr_factor * 0.7) + (pf_factor * 0.3)
        return round(max(0.60, min(1.20, raw)), 3)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def analyze(
        self,
        symbol:     Optional[str] = None,
        session:    Optional[str] = None,
        entry_type: Optional[str] = None,
    ) -> BacktestSummary:
        """
        Compute performance statistics for the system (optionally filtered).

        Args:
            symbol:     If provided, also compute stats for this pair specifically.
            session:    "london" | "new_york" — filter context
            entry_type: "ORDER_BLOCK" | "BREAKER_BLOCK" | "FVG"
        """
        trades = self._load_closed_trades()

        if len(trades) < _MIN_SAMPLE:
            self.logger.info(
                "[BACKTESTER] Only %d closed trade(s) — insufficient for statistics",
                len(trades),
            )
            return BacktestSummary.insufficient_data()

        wr      = self._win_rate(trades)
        pf      = self._profit_factor(trades)
        avg_rr  = self._avg_rr(trades)
        n       = len(trades)

        # Per-session and per-pattern rates (from signal join — may be empty)
        session_rates = self._group_win_rates(trades, "session")
        pattern_rates = self._group_win_rates(trades, "entry_type")
        symbol_rates  = self._group_win_rates(trades, "symbol")

        # Monte Carlo
        winners  = [t["pnl"] for t in trades if t["pnl"] > 0]
        avg_win  = (sum(winners) / len(winners)) if winners else 0.0
        mc_dd    = self._monte_carlo_max_dd(wr, avg_win, 1.0, n_trades=200)

        cl_risk  = self._consecutive_loss_risk(wr, 3)
        conf_mul = self._confidence_multiplier(wr, pf, n)

        self.logger.info(
            "[BACKTESTER] WR=%.0f%%  PF=%.2f  AvgRR=%.2f  Conf×%.2f  "
            "MC_DD=%.1f%%  CL_Risk=%.0f%%  n=%d",
            wr * 100, pf, avg_rr, conf_mul, mc_dd * 100, cl_risk * 100, n,
        )

        return BacktestSummary(
            overall_win_rate      = round(wr, 3),
            session_win_rates     = {k: round(v, 3) for k, v in session_rates.items()},
            pattern_win_rates     = {k: round(v, 3) for k, v in pattern_rates.items()},
            symbol_win_rates      = {k: round(v, 3) for k, v in symbol_rates.items()},
            avg_rr_achieved       = round(avg_rr, 2),
            profit_factor         = round(pf, 2),
            confidence_multiplier = conf_mul,
            monte_carlo_max_dd    = round(mc_dd, 4),
            consecutive_loss_risk = round(cl_risk, 3),
            sample_size           = n,
        )
