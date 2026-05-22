"""Seven-agent trading workflow orchestration.

Pipeline (strict sequence):

  Pre-cycle intelligence:
    0a. Market-Regime   — classify market environment, derive risk multipliers
    0b. Backtester      — load historical win rate, compute confidence_multiplier
    0c. News-Sentinel   — check for upcoming high-impact economic events
    0d. Risk-Sentinel   — evaluate portfolio risk, approve or block trade

  Core ICT cycle:
    1.  Trend-Master    — top-down macro bias (Weekly → Daily → 4H)
    2.  Analyse-Master  — ICT pattern detection during London / NY kill zones
    3.  Trader-Master   — LTF entry refinement + MT5 execution

User risk settings from RiskSettingsManager are read at runtime so that UI
changes take effect immediately without restarting agents.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agents.trend_master.trend_master         import TrendMaster,        TrendReport
from agents.analyse_master.analyse_master     import AnalyseMaster,      TradeSignal
from agents.trader_master.trader_master       import TraderMaster,        ExecutionRecord
from agents.risk_sentinel.risk_sentinel       import RiskSentinel,        RiskAssessment
from agents.news_sentinel.news_sentinel       import NewsSentinel,        NewsWindow
from agents.backtester.backtester             import Backtester,          BacktestSummary
from agents.market_regime.market_regime       import MarketRegimeAgent,   MarketRegimeReport

if TYPE_CHECKING:
    from market_data.mt5_provider import MT5Provider

logger = logging.getLogger(__name__)


class TradingWorkflow:
    """
    Orchestrates all seven agents.

    Pre-cycle agents (0a-0d) run before the main ICT pipeline.
    They can block, scale, or annotate the main cycle output.
    """

    def __init__(
        self,
        verbose:      bool = False,
        mt5_provider: Optional["MT5Provider"] = None,
    ) -> None:
        # ── Core ICT agents ────────────────────────────────────────────
        self.trend_master    = TrendMaster(verbose=verbose)
        self.analyse_master  = AnalyseMaster(verbose=verbose)
        self.trader_master   = TraderMaster(verbose=verbose, mt5_provider=mt5_provider)

        # ── Pre-cycle intelligence agents ──────────────────────────────
        self.risk_sentinel   = RiskSentinel(verbose=verbose)
        self.news_sentinel   = NewsSentinel(verbose=verbose)
        self.backtester      = Backtester(verbose=verbose)
        self.market_regime   = MarketRegimeAgent(verbose=verbose)

        self.verbose         = verbose

        # ── State ──────────────────────────────────────────────────────
        self.last_trend_report:   Optional[TrendReport]       = None
        self.last_trade_signal:   Optional[TradeSignal]        = None
        self.last_risk_assessment: Optional[RiskAssessment]   = None
        self.last_regime_report:  Optional[MarketRegimeReport] = None
        self.last_backtest:       Optional[BacktestSummary]    = None
        self.execution_records:   List[ExecutionRecord]        = []

    # ------------------------------------------------------------------
    # Pre-cycle intelligence (always runs)
    # ------------------------------------------------------------------

    async def run_pre_cycle(
        self,
        symbol:     str,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run the four pre-cycle intelligence agents.

        Returns a dict with keys:
          regime      : MarketRegimeReport
          backtest    : BacktestSummary
          news        : NewsWindow
          risk        : RiskAssessment | None  (None = not yet evaluated; needs open_trades)
          approved    : bool (False = pre-cycle blocked the cycle)
          block_reason: Optional[str]
        """
        result: Dict[str, Any] = {
            "regime":       None,
            "backtest":     None,
            "news":         None,
            "risk":         None,
            "approved":     True,
            "block_reason": None,
        }

        # ── 0a. Market Regime ──────────────────────────────────────────
        try:
            regime = await self.market_regime.analyze(market_data)
            self.last_regime_report = regime
            result["regime"] = regime
            logger.info(
                "[WORKFLOW] Market Regime: %s  risk_mult=%.2f  rr≥%.1f",
                regime.regime, regime.risk_multiplier, regime.recommended_rr,
            )
            if regime.regime == "VOLATILE":
                result["approved"]     = False
                result["block_reason"] = (
                    f"Market Regime VOLATILE — trading blocked. {regime.description}"
                )
                return result
        except Exception as exc:
            logger.warning("[WORKFLOW] Market-Regime failed (non-blocking): %s", exc)

        # ── 0b. Backtester ─────────────────────────────────────────────
        try:
            bt = await self.backtester.analyze(symbol=symbol)
            self.last_backtest = bt
            result["backtest"] = bt
            logger.info(
                "[WORKFLOW] Backtest WR=%.0f%%  PF=%.2f  Conf×%.2f  n=%d",
                bt.overall_win_rate * 100, bt.profit_factor,
                bt.confidence_multiplier, bt.sample_size,
            )
        except Exception as exc:
            logger.warning("[WORKFLOW] Backtester failed (non-blocking): %s", exc)

        # ── 0c. News-Sentinel ──────────────────────────────────────────
        try:
            news = await self.news_sentinel.check(symbol=symbol)
            result["news"] = news
            logger.info(
                "[WORKFLOW] News: %s  next='%s' in %.0f min",
                news.risk_level, news.next_event_name, news.minutes_until,
            )
            if not news.safe:
                result["approved"]     = False
                result["block_reason"] = (
                    f"News-Sentinel DANGER — '{news.next_event_name}' "
                    f"in {news.minutes_until:.0f} min"
                )
                return result
        except Exception as exc:
            logger.warning("[WORKFLOW] News-Sentinel failed (non-blocking): %s", exc)

        return result

    async def run_risk_check(
        self,
        symbol:     str,
        pre_result: Dict[str, Any],
        confidence: float,
    ) -> RiskAssessment:
        """
        Run Risk-Sentinel after a signal has been produced (needs confidence score).
        """
        open_trades  = [t.to_dict() for t in self.trader_master.open_trades]
        daily_loss   = self.trader_master.daily_loss
        consec       = self.trader_master.consecutive_losses
        reduced_rem  = self.trader_master.reduced_sizing_remaining

        try:
            from market_data.mt5_provider import MT5Provider
            equity = 0.0
            if self.trader_master.mt5_provider is not None:
                equity = await self.trader_master.mt5_provider.get_account_balance()
        except Exception:
            equity = 0.0

        assessment = await self.risk_sentinel.assess(
            symbol                   = symbol,
            open_trades              = open_trades,
            daily_loss_pct           = daily_loss,
            consecutive_losses       = consec,
            current_equity           = equity,
            reduced_sizing_remaining = reduced_rem,
            signal_confidence        = confidence,
        )
        self.last_risk_assessment = assessment
        return assessment

    # ------------------------------------------------------------------
    # Full trading cycle
    # ------------------------------------------------------------------

    async def execute_trading_cycle(
        self,
        market_data: Dict[str, Any],
        symbol:      str = "",
    ) -> Optional[ExecutionRecord]:
        """
        Run the complete 7-agent pipeline for one symbol.

        Returns ExecutionRecord if a trade was placed, None otherwise.
        """
        logger.info("=" * 60)
        logger.info("Trading cycle START — %s", symbol)
        logger.info("=" * 60)

        try:
            # ── Pre-cycle intelligence ─────────────────────────────────
            pre = await self.run_pre_cycle(symbol, market_data)
            if not pre["approved"]:
                logger.warning("[WORKFLOW] Pre-cycle BLOCKED — %s", pre["block_reason"])
                return None

            regime: Optional[MarketRegimeReport] = pre.get("regime")
            bt:     Optional[BacktestSummary]    = pre.get("backtest")

            # ── Step 1: Trend-Master ───────────────────────────────────
            logger.info("[STEP 1] Trend-Master — macro bias identification")
            trend_report = await self.trend_master.analyze(market_data)
            self.last_trend_report = trend_report

            if not trend_report:
                logger.warning("[STEP 1] Trend-Master returned no report")
                return None

            logger.info(
                "[STEP 1] Bias=%s  Confidence=%.1f%%  Risk=%s",
                trend_report.bias, trend_report.confidence, trend_report.risk_level,
            )

            # ── Step 2: Analyse-Master ─────────────────────────────────
            logger.info("[STEP 2] Analyse-Master — ICT signal detection")

            # Apply regime's recommended RR to Analyse-Master via trend_report augmentation
            trend_dict = trend_report.to_dict()
            if regime is not None:
                trend_dict["_regime_rr_floor"]       = regime.recommended_rr
                trend_dict["_regime_risk_multiplier"] = regime.risk_multiplier

            trade_signal = await self.analyse_master.analyze(
                trend_dict,
                candle_data=market_data,
                symbol=symbol,
            )
            self.last_trade_signal = trade_signal

            if not trade_signal:
                logger.info("[STEP 2] No signal (kill zone / pattern conditions not met)")
                return None

            # Apply backtester confidence multiplier
            effective_confidence = trade_signal.confidence
            if bt is not None and bt.sample_size >= 10:
                effective_confidence = round(
                    trade_signal.confidence * bt.confidence_multiplier, 1
                )
                if effective_confidence != trade_signal.confidence:
                    logger.info(
                        "[STEP 2] Confidence adjusted by backtest: %.1f%% → %.1f%%",
                        trade_signal.confidence, effective_confidence,
                    )
                trade_signal.confidence = effective_confidence

            logger.info(
                "[STEP 2] Signal ✓  %s  %s  Entry=%.5f  Conf=%.1f%%",
                trade_signal.entry_type, trade_signal.direction,
                trade_signal.entry_level, trade_signal.confidence,
            )

            # ── Risk-Sentinel (now we have confidence) ─────────────────
            assessment = await self.run_risk_check(
                symbol, pre, trade_signal.confidence
            )
            if not assessment.approved:
                logger.warning(
                    "[WORKFLOW] Risk-Sentinel BLOCKED — %s", assessment.block_reason
                )
                return None

            for w in assessment.warnings:
                logger.info("[WORKFLOW] ⚠ Risk warning: %s", w)

            # ── Step 3: Trader-Master ──────────────────────────────────
            logger.info("[STEP 3] Trader-Master — LTF confirmation + execution")

            # Pass risk multiplier and regime data through signal dict
            signal_dict = trade_signal.to_dict()
            signal_dict["_risk_multiplier"]  = assessment.risk_multiplier
            signal_dict["_adjusted_risk_pct"] = assessment.adjusted_risk_pct
            if regime is not None:
                signal_dict["_regime_risk_multiplier"] = regime.risk_multiplier

            execution = await self.trader_master.analyze(
                signal_dict,
                market_data=market_data,
            )

            if not execution:
                logger.warning("[STEP 3] Trader-Master did not execute")
                return None

            logger.info(
                "[STEP 3] Executed — ID=%s  Status=%s",
                execution.signal_id, execution.status,
            )
            self.execution_records.append(execution)

            logger.info("=" * 60)
            logger.info("Trading cycle COMPLETE — %s", symbol)
            logger.info("=" * 60)
            return execution

        except Exception as exc:
            logger.error("Unhandled error in trading cycle: %s", exc, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Performance summary
    # ------------------------------------------------------------------

    def get_performance_summary(self) -> Dict[str, Any]:
        if not self.execution_records:
            return {
                "total_trades": 0, "winning_trades": 0,
                "losing_trades": 0, "win_rate": 0.0,
            }

        total   = len(self.execution_records)
        closed  = [t for t in self.execution_records if t.status == "CLOSED"]
        winners = [t for t in closed if (t.p_and_l or 0) > 0]
        losers  = [t for t in closed if (t.p_and_l or 0) <= 0]

        return {
            "total_trades":   total,
            "closed_trades":  len(closed),
            "open_trades":    total - len(closed),
            "winning_trades": len(winners),
            "losing_trades":  len(losers),
            "win_rate":       len(winners) / len(closed) if closed else 0.0,
            "total_pnl":      sum(t.p_and_l or 0 for t in closed),
        }
