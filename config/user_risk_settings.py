"""
User-controlled risk/reward settings — single source of truth.

Persisted to risk_settings.json in the project root.
All agents call RiskSettingsManager.get() at runtime so UI changes
take effect immediately without restarting the process.

Priority rule: user-defined values ALWAYS override agent defaults.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_SETTINGS_ENV  = os.environ.get("RISK_SETTINGS_PATH")
_SETTINGS_FILE = (
    Path(_SETTINGS_ENV)
    if _SETTINGS_ENV
    else Path(__file__).parents[1] / "risk_settings.json"
)


@dataclass
class UserRiskSettings:
    """All user-configurable risk parameters with safe defaults."""

    # ── Core risk ─────────────────────────────────────────────────────────────
    risk_pct:              float = 2.0   # % of account risked per trade  (0.1 – 10.0)
    rr_ratio:              float = 2.0   # Minimum reward-to-risk ratio   (1.0 – 10.0)
    max_concurrent_trades: int   = 3     # Max open positions at once      (1 – 10)
    max_daily_loss_pct:    float = 5.0   # Daily loss ceiling as %         (1.0 – 20.0)
    min_confidence_pct:    float = 75.0  # Min signal confidence to execute (50 – 95)

    # ── Position sizing mode ──────────────────────────────────────────────────
    # "fixed"          → always use fixed_lot_size
    # "percentage"     → account_balance × risk_pct / stop_distance   (default)
    # "volatility"     → scale inversely with current ATR
    # "equity_scaling" → reduce size proportionally as drawdown grows
    sizing_mode:    str   = "percentage"
    fixed_lot_size: float = 0.10   # Used only when sizing_mode == "fixed"

    # ── Core feature toggles ──────────────────────────────────────────────────
    auto_risk_management:   bool = True   # Master kill switch for all risk logic
    smart_position_sizing:  bool = True   # Dynamic lot-size calculation
    dynamic_stop_loss:      bool = True   # ATR-adjusted SL placement
    dynamic_take_profit:    bool = True   # ATR-adjusted TP placement
    ai_risk_optimization:   bool = True   # Enable AI confidence weighting

    # ── Advanced features ─────────────────────────────────────────────────────
    adaptive_volatility_risk:      bool = False  # Reduce risk % in high-vol sessions
    session_risk_reduction:        bool = False  # Halve size outside London/NY KZ
    news_event_filter:             bool = True   # Block trades near high-impact news
    ai_confidence_weighted_sizing: bool = True   # Scale lots by confidence score
    news_buffer_minutes:           int  = 30     # Minutes before/after news to avoid

    # ── Equity-curve protection ───────────────────────────────────────────────
    equity_curve_protection:    bool  = True
    equity_dip_threshold_pct:   float = 10.0  # % dip from peak triggers reduction
    equity_reduced_risk_factor: float = 0.5   # Multiply risk_pct by this on dip

    # ── Consecutive-loss protection ───────────────────────────────────────────
    consecutive_loss_limit:            int   = 3    # Losses before size reduction
    consecutive_loss_size_factor:      float = 0.5  # Lot multiplier during streak
    consecutive_loss_recovery_trades:  int   = 5    # Trades before returning to normal

    # ──────────────────────────────────────────────────────────────────────────

    def validate(self) -> "UserRiskSettings":
        """Clamp every value to its legal range. Returns self."""
        self.risk_pct               = max(0.1,  min(10.0,  self.risk_pct))
        self.rr_ratio               = max(1.0,  min(10.0,  self.rr_ratio))
        self.max_concurrent_trades  = max(1,    min(10,    self.max_concurrent_trades))
        self.max_daily_loss_pct     = max(1.0,  min(20.0,  self.max_daily_loss_pct))
        self.min_confidence_pct     = max(50.0, min(95.0,  self.min_confidence_pct))
        self.fixed_lot_size         = max(0.01, min(100.0, self.fixed_lot_size))
        self.news_buffer_minutes    = max(5,    min(120,   self.news_buffer_minutes))
        self.equity_dip_threshold_pct       = max(5.0, min(50.0, self.equity_dip_threshold_pct))
        self.equity_reduced_risk_factor     = max(0.1, min(1.0,  self.equity_reduced_risk_factor))
        self.consecutive_loss_limit         = max(1,   min(10,   self.consecutive_loss_limit))
        self.consecutive_loss_size_factor   = max(0.1, min(1.0,  self.consecutive_loss_size_factor))
        self.consecutive_loss_recovery_trades = max(1, min(20,   self.consecutive_loss_recovery_trades))
        valid_modes = ("fixed", "percentage", "volatility", "equity_scaling")
        if self.sizing_mode not in valid_modes:
            self.sizing_mode = "percentage"
        return self

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserRiskSettings":
        valid_fields = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


class RiskSettingsManager:
    """
    Singleton loader/saver for UserRiskSettings.

    Usage in any agent:
        from config.user_risk_settings import RiskSettingsManager
        s = RiskSettingsManager.get()
        lots = account * s.risk_pct / 100 / stop_pips
    """

    _instance: Optional["RiskSettingsManager"] = None
    _settings: UserRiskSettings

    def __new__(cls) -> "RiskSettingsManager":
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._settings = UserRiskSettings()
            inst._load()
            cls._instance = inst
        return cls._instance

    def _load(self) -> None:
        if _SETTINGS_FILE.exists():
            try:
                raw = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
                self._settings = UserRiskSettings.from_dict(raw).validate()
                logger.info("[RISK-SETTINGS] Loaded from %s", _SETTINGS_FILE)
                return
            except Exception as exc:
                logger.warning("[RISK-SETTINGS] Load failed (%s) — using defaults", exc)
        self._settings = UserRiskSettings()
        self._save()

    def _save(self) -> None:
        try:
            _SETTINGS_FILE.write_text(
                json.dumps(self._settings.to_dict(), indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("[RISK-SETTINGS] Save failed: %s", exc)

    @classmethod
    def get(cls) -> UserRiskSettings:
        """Return current settings (loads from disk on first call)."""
        return cls()._settings

    @classmethod
    def update(cls, partial: Dict[str, Any]) -> UserRiskSettings:
        """Merge partial dict into settings, validate, persist, return updated copy."""
        mgr = cls()
        merged = mgr._settings.to_dict()
        merged.update(partial)
        mgr._settings = UserRiskSettings.from_dict(merged).validate()
        mgr._save()
        logger.info("[RISK-SETTINGS] Updated keys: %s", sorted(partial.keys()))
        return mgr._settings

    @classmethod
    def reset(cls) -> UserRiskSettings:
        """Reset to factory defaults and persist."""
        mgr = cls()
        mgr._settings = UserRiskSettings()
        mgr._save()
        logger.info("[RISK-SETTINGS] Reset to defaults")
        return mgr._settings
