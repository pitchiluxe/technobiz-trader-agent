"""Risk-Sentinel Agent — real-time portfolio gatekeeper.

Responsibilities:
  1. Evaluate portfolio risk before every new trade.
  2. Hard-block if daily loss limit or concurrent trade limit is exceeded.
  3. Assess correlation risk (avoid stacking positions in correlated pairs).
  4. Apply equity-curve protection when equity dips from its peak.
  5. Apply consecutive-loss size reduction.
  6. Scale size by AI confidence score (optional).
  7. Apply session-based and volatility-based risk scaling.

Returns a RiskAssessment that Trader-Master MUST respect.
User settings from RiskSettingsManager are read at call time, so UI changes
take effect on the very next cycle without a process restart.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..base_agent import BaseAgent
from config.constants import KILL_ZONES_UTC
from config.user_risk_settings import RiskSettingsManager

logger = logging.getLogger(__name__)

# Correlated pair clusters — only one open position allowed per cluster
_CORRELATION_CLUSTERS: List[frozenset] = [
    frozenset({"EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"}),   # USD-negative majors
    frozenset({"USDJPY", "USDCAD", "USDCHF"}),              # USD-positive majors
    frozenset({"GBPJPY", "EURJPY", "AUDJPY", "CADJPY"}),   # JPY crosses
    frozenset({"XAUUSD", "EURUSD"}),                         # Gold / EUR correlation
    frozenset({"NASDAQ", "US30"}),                           # US equity indices
]


class RiskAssessment:
    """Output model for Risk-Sentinel."""

    def __init__(
        self,
        approved:           bool,
        risk_multiplier:    float,
        adjusted_risk_pct:  float,
        warnings:           List[str],
        block_reason:       Optional[str] = None,
        timestamp:          Optional[datetime] = None,
    ) -> None:
        self.approved           = approved
        self.risk_multiplier    = risk_multiplier    # 0.0–1.0 (1.0 = full size)
        self.adjusted_risk_pct  = adjusted_risk_pct  # effective risk % after all adjustments
        self.warnings           = warnings
        self.block_reason       = block_reason
        self.timestamp          = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved":          self.approved,
            "risk_multiplier":   round(self.risk_multiplier, 4),
            "adjusted_risk_pct": round(self.adjusted_risk_pct, 3),
            "warnings":          self.warnings,
            "block_reason":      self.block_reason,
            "timestamp":         self.timestamp.isoformat(),
        }

    @staticmethod
    def blocked(reason: str) -> "RiskAssessment":
        return RiskAssessment(
            approved=False, risk_multiplier=0.0,
            adjusted_risk_pct=0.0, warnings=[], block_reason=reason,
        )


class RiskSentinel(BaseAgent):
    """
    Risk-Sentinel Agent.

    Does not place orders. Produces a pass/fail + composite risk multiplier
    that gates and scales Trader-Master execution.
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__(
            name="Risk-Sentinel",
            instructions=(
                "You are the Risk-Sentinel. Gate and scale every trade by portfolio "
                "risk. Respect user settings from RiskSettingsManager. Block trades "
                "that violate drawdown, correlation, or equity-protection rules."
            ),
            verbose=verbose,
        )
        self._peak_equity: float = 0.0   # high-water mark for equity-curve protection

    async def analyze(self, *args: Any, **kwargs: Any) -> Any:
        """Satisfy BaseAgent abstract requirement — delegates to assess()."""
        return await self.assess(*args, **kwargs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _correlation_check(
        self, symbol: str, open_trades: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Block if a correlated pair is already open."""
        open_symbols = {t.get("symbol", "") for t in open_trades
                        if t.get("status") in ("PENDING", "OPEN")}
        for cluster in _CORRELATION_CLUSTERS:
            if symbol in cluster:
                conflicts = cluster & open_symbols - {symbol}
                if conflicts:
                    return False, (
                        f"Correlation block: {symbol} conflicts with open "
                        f"position(s) in {', '.join(sorted(conflicts))}"
                    )
        return True, None

    def _session_multiplier(self) -> Tuple[float, Optional[str]]:
        """Return (multiplier, warning) — halves size outside London/NY."""
        now = datetime.now(timezone.utc)
        for name, (h_start, h_end) in KILL_ZONES_UTC.items():
            if name == "asian":
                continue
            if h_start <= now.hour < h_end:
                return 1.0, None
        return 0.5, "Outside core kill zone — session risk reduction applied (×0.5)"

    def _equity_multiplier(
        self, current_equity: float, s: Any
    ) -> Tuple[float, Optional[str]]:
        """Reduce size when equity dips from peak beyond threshold."""
        if not s.equity_curve_protection or current_equity <= 0:
            return 1.0, None
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
        if self._peak_equity == 0:
            return 1.0, None
        dip_pct = (self._peak_equity - current_equity) / self._peak_equity * 100.0
        if dip_pct >= s.equity_dip_threshold_pct:
            factor = s.equity_reduced_risk_factor
            return factor, (
                f"Equity dip {dip_pct:.1f}% from peak — "
                f"size reduced to {factor*100:.0f}%"
            )
        return 1.0, None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def assess(
        self,
        symbol:                   str,
        open_trades:              List[Dict[str, Any]],
        daily_loss_pct:           float,
        consecutive_losses:       int,
        current_equity:           float = 0.0,
        reduced_sizing_remaining: int   = 0,
        signal_confidence:        float = 100.0,
    ) -> RiskAssessment:
        """
        Evaluate whether a new trade may be opened and at what size.

        Args:
            symbol:                   Trading symbol
            open_trades:              Currently open/pending positions
            daily_loss_pct:           Today's realised loss as a fraction (0.05 = 5%)
            consecutive_losses:       Streak of consecutive losing trades
            current_equity:           Live account equity (0 = not available)
            reduced_sizing_remaining: Trades remaining in reduced-size window
            signal_confidence:        Analyse-Master confidence score (0–100)

        Returns:
            RiskAssessment with approved flag and composite risk_multiplier.
        """
        if not RiskSettingsManager.get().auto_risk_management:
            # Risk management disabled by user — allow with full size
            s = RiskSettingsManager.get()
            return RiskAssessment(
                approved=True, risk_multiplier=1.0,
                adjusted_risk_pct=s.risk_pct, warnings=["Auto risk management disabled"],
            )

        s         = RiskSettingsManager.get()
        warnings: List[str] = []
        multiplier = 1.0

        # ── 1. Daily drawdown hard stop ────────────────────────────────
        if daily_loss_pct >= (s.max_daily_loss_pct / 100.0):
            return RiskAssessment.blocked(
                f"Daily loss {daily_loss_pct*100:.1f}% ≥ limit "
                f"{s.max_daily_loss_pct:.1f}% — trading paused"
            )

        # ── 2. Maximum concurrent trades ───────────────────────────────
        active = [t for t in open_trades if t.get("status") in ("PENDING", "OPEN")]
        if len(active) >= s.max_concurrent_trades:
            return RiskAssessment.blocked(
                f"Max concurrent trades ({s.max_concurrent_trades}) reached"
            )

        # ── 3. Correlation block ───────────────────────────────────────
        corr_ok, corr_warn = self._correlation_check(symbol, open_trades)
        if not corr_ok:
            return RiskAssessment.blocked(corr_warn)

        # ── 4. Consecutive-loss size reduction ─────────────────────────
        if reduced_sizing_remaining > 0:
            multiplier *= s.consecutive_loss_size_factor
            warnings.append(
                f"Consecutive loss protection: size ×{s.consecutive_loss_size_factor:.1f} "
                f"({reduced_sizing_remaining} trades remaining)"
            )

        # ── 5. Session-based risk scaling (optional) ───────────────────
        if s.session_risk_reduction:
            sess_mult, sess_warn = self._session_multiplier()
            if sess_warn:
                multiplier *= sess_mult
                warnings.append(sess_warn)

        # ── 6. Equity-curve protection ─────────────────────────────────
        eq_mult, eq_warn = self._equity_multiplier(current_equity, s)
        if eq_warn:
            multiplier *= eq_mult
            warnings.append(eq_warn)

        # ── 7. AI confidence-weighted sizing ───────────────────────────
        if s.ai_confidence_weighted_sizing and s.ai_risk_optimization:
            # Confidence 75 → 0.925, confidence 100 → 1.0
            conf_mult = 0.75 + (min(signal_confidence, 100.0) / 100.0) * 0.25
            multiplier *= conf_mult
            if signal_confidence < 85.0:
                warnings.append(
                    f"Confidence {signal_confidence:.0f}% — "
                    f"size scaled to {conf_mult*100:.0f}%"
                )

        # ── 8. Adaptive volatility risk reduction (optional) ───────────
        if s.adaptive_volatility_risk:
            proximity = daily_loss_pct / max((s.max_daily_loss_pct / 100.0), 0.001)
            if proximity >= 0.5:
                multiplier *= 0.75
                warnings.append(
                    f"Approaching daily limit ({proximity*100:.0f}%) — "
                    "adaptive volatility reduction applied (×0.75)"
                )

        final_risk_pct = s.risk_pct * multiplier

        self.logger.info(
            "[RISK-SENTINEL] %s ✓  risk_pct=%.2f%%  multiplier=%.3f  warnings=%d",
            symbol, final_risk_pct, multiplier, len(warnings),
        )
        for w in warnings:
            self.logger.info("[RISK-SENTINEL]   ⚠ %s", w)

        return RiskAssessment(
            approved          = True,
            risk_multiplier   = round(multiplier, 4),
            adjusted_risk_pct = round(final_risk_pct, 3),
            warnings          = warnings,
        )
