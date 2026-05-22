"""Risk management API routes — GET|POST /api/risk/*."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator

from config.user_risk_settings import RiskSettingsManager, UserRiskSettings

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────────

class RiskSettingsPayload(BaseModel):
    """Partial or full update payload for risk settings."""
    risk_pct:              Optional[float] = Field(None, ge=0.1,  le=10.0)
    rr_ratio:              Optional[float] = Field(None, ge=1.0,  le=10.0)
    max_concurrent_trades: Optional[int]   = Field(None, ge=1,    le=10)
    max_daily_loss_pct:    Optional[float] = Field(None, ge=1.0,  le=20.0)
    min_confidence_pct:    Optional[float] = Field(None, ge=50.0, le=95.0)
    sizing_mode:           Optional[str]   = None
    fixed_lot_size:        Optional[float] = Field(None, ge=0.01, le=100.0)

    # Toggles
    auto_risk_management:          Optional[bool] = None
    smart_position_sizing:         Optional[bool] = None
    dynamic_stop_loss:             Optional[bool] = None
    dynamic_take_profit:           Optional[bool] = None
    ai_risk_optimization:          Optional[bool] = None

    # Advanced
    adaptive_volatility_risk:      Optional[bool]  = None
    session_risk_reduction:        Optional[bool]  = None
    news_event_filter:             Optional[bool]  = None
    ai_confidence_weighted_sizing: Optional[bool]  = None
    news_buffer_minutes:           Optional[int]   = Field(None, ge=5, le=120)

    # Equity protection
    equity_curve_protection:       Optional[bool]  = None
    equity_dip_threshold_pct:      Optional[float] = Field(None, ge=5.0,  le=50.0)
    equity_reduced_risk_factor:    Optional[float] = Field(None, ge=0.1,  le=1.0)

    # Consecutive loss
    consecutive_loss_limit:             Optional[int]   = Field(None, ge=1, le=10)
    consecutive_loss_size_factor:       Optional[float] = Field(None, ge=0.1, le=1.0)
    consecutive_loss_recovery_trades:   Optional[int]   = Field(None, ge=1, le=20)

    @validator("sizing_mode")
    def _valid_mode(cls, v):
        valid = ("fixed", "percentage", "volatility", "equity_scaling")
        if v is not None and v not in valid:
            raise ValueError(f"sizing_mode must be one of {valid}")
        return v


class PositionPreviewRequest(BaseModel):
    symbol:  str
    entry:   float = Field(..., gt=0)
    sl:      float = Field(..., gt=0)
    balance: float = Field(..., gt=0)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_risk_settings():
    """Return current user risk settings."""
    return {"settings": RiskSettingsManager.get().to_dict()}


@router.post("/settings")
async def update_risk_settings(body: RiskSettingsPayload):
    """
    Merge partial risk settings payload into persisted settings.
    Only supplied (non-null) keys are updated.
    Changes take effect on the very next trading cycle.
    """
    updates: Dict[str, Any] = {
        k: v for k, v in body.dict().items() if v is not None
    }
    if not updates:
        raise HTTPException(status_code=400, detail="No settings provided")

    updated = RiskSettingsManager.update(updates)
    logger.info("[RISK-API] Settings updated: %s", sorted(updates.keys()))
    return {
        "success":       True,
        "updated_keys":  sorted(updates.keys()),
        "settings":      updated.to_dict(),
    }


@router.post("/reset")
async def reset_risk_settings():
    """Reset all risk settings to factory defaults."""
    defaults = RiskSettingsManager.reset()
    return {"success": True, "settings": defaults.to_dict()}


@router.get("/preview")
async def position_size_preview(
    symbol:  str,
    entry:   float,
    sl:      float,
    balance: float,
):
    """
    Calculate position size preview given current risk settings.
    Useful for the GUI to show real-time sizing before a trade fires.
    """
    from config.constants import get_instrument_spec

    s    = RiskSettingsManager.get()
    spec = get_instrument_spec(symbol)

    risk_price = abs(entry - sl)
    if risk_price == 0:
        raise HTTPException(status_code=400, detail="entry and sl cannot be equal")

    # ── Percentage-based sizing ────────────────────────────────────────
    risk_dollars = balance * (s.risk_pct / 100.0)
    risk_pips    = risk_price / spec["pip_size"]
    pct_lots     = risk_dollars / (risk_pips * spec["pip_value_per_lot"]) if risk_pips > 0 else 0.01

    # ── Fixed lot sizing ───────────────────────────────────────────────
    fixed_lots   = s.fixed_lot_size

    # ── Volatility-adjusted sizing (ATR not available here — approximation) ──
    vol_lots     = pct_lots * 0.8   # conservative placeholder without live ATR

    # ── Select active lots per mode ────────────────────────────────────
    mode_map = {
        "fixed":          fixed_lots,
        "percentage":     pct_lots,
        "volatility":     vol_lots,
        "equity_scaling": pct_lots,  # equity scaling uses same base; multiplier in agent
    }
    active_lots = round(max(0.01, min(100.0, mode_map.get(s.sizing_mode, pct_lots))), 2)

    rr = s.rr_ratio
    if entry > sl:   # BUY
        tp1 = entry + risk_price * 1.0
        tp2 = entry + risk_price * rr
        tp3 = entry + risk_price * (rr + 1)
    else:            # SELL
        tp1 = entry - risk_price * 1.0
        tp2 = entry - risk_price * rr
        tp3 = entry - risk_price * (rr + 1)

    projected_loss   = round(active_lots * risk_pips * spec["pip_value_per_lot"], 2)
    projected_profit = round(projected_loss * rr, 2)
    margin_est       = round(active_lots * entry * 0.01, 2)   # 1:100 margin approximation

    return {
        "symbol":          symbol,
        "sizing_mode":     s.sizing_mode,
        "active_lots":     active_lots,
        "risk_pct":        s.risk_pct,
        "rr_ratio":        rr,
        "risk_dollars":    round(risk_dollars, 2),
        "risk_pips":       round(risk_pips, 1),
        "projected_loss":  projected_loss,
        "projected_profit":projected_profit,
        "margin_est":      margin_est,
        "entry":           entry,
        "stop_loss":       sl,
        "take_profit_1":   round(tp1, 5),
        "take_profit_2":   round(tp2, 5),
        "take_profit_3":   round(tp3, 5),
        "all_sizes": {
            "fixed":          round(max(0.01, fixed_lots), 2),
            "percentage":     round(max(0.01, min(100.0, pct_lots)), 2),
            "volatility":     round(max(0.01, min(100.0, vol_lots)), 2),
            "equity_scaling": round(max(0.01, min(100.0, pct_lots)), 2),
        },
    }


@router.get("/summary")
async def risk_summary():
    """Return a human-readable risk configuration summary."""
    s = RiskSettingsManager.get()
    return {
        "risk_per_trade":      f"{s.risk_pct}%",
        "min_rr":              f"1:{s.rr_ratio}",
        "max_trades":          s.max_concurrent_trades,
        "daily_loss_limit":    f"{s.max_daily_loss_pct}%",
        "sizing_mode":         s.sizing_mode,
        "news_filter":         s.news_event_filter,
        "equity_protection":   s.equity_curve_protection,
        "confidence_weighted": s.ai_confidence_weighted_sizing,
        "session_reduction":   s.session_risk_reduction,
    }
