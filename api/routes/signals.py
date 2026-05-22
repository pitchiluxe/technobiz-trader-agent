"""Analyse-Master route — POST /api/signals/analyze."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents.analyse_master.analyse_master import AnalyseMaster

logger = logging.getLogger(__name__)
router = APIRouter()
_analyse_master: Optional[AnalyseMaster] = None


def _get_agent() -> AnalyseMaster:
    global _analyse_master
    if _analyse_master is None:
        _analyse_master = AnalyseMaster(verbose=False)
    return _analyse_master


# ── Pydantic models ───────────────────────────────────────────────────────────

class SignalAnalysisRequest(BaseModel):
    symbol: str
    trend_report: Dict[str, Any]
    candle_data: Dict[str, List[Dict[str, Any]]] = {}


class SignalAnalysisResponse(BaseModel):
    success: bool
    symbol: str
    data: Dict[str, Any] = {}
    has_signal: bool = False
    error: Optional[str] = None


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=SignalAnalysisResponse)
async def analyze_signal(body: SignalAnalysisRequest, request: Request):
    """
    Run Analyse-Master to detect ICT patterns and generate a TradeSignal.
    Requires a TrendReport dict (from /api/trends/analyze).
    """
    manager = request.app.state.manager
    agent = _get_agent()

    await manager.send_agent_status(
        "analyse_master", "analyzing", f"Scanning ICT patterns for {body.symbol}…"
    )

    try:
        trade_signal = await agent.analyze(body.trend_report, body.candle_data)

        if trade_signal is None:
            await manager.send_agent_status(
                "analyse_master", "idle", "No valid ICT setup detected — holding"
            )
            return SignalAnalysisResponse(
                success=True,
                symbol=body.symbol,
                has_signal=False,
                error="No ICT setup confirmed (waiting for all 4 elements)",
            )

        result = trade_signal.to_dict()
        await manager.send_agent_status(
            "analyse_master",
            "success",
            f"Signal generated — confidence {result.get('confidence', 0):.0f}%",
            result,
        )
        return SignalAnalysisResponse(
            success=True, symbol=body.symbol, has_signal=True, data=result
        )

    except Exception as exc:
        logger.exception("[Signal] Analysis failed for %s", body.symbol)
        await manager.send_agent_status("analyse_master", "error", str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
async def reset_agent(request: Request):
    global _analyse_master
    _analyse_master = None
    await request.app.state.manager.send_agent_status("analyse_master", "idle", "Agent reset")
    return {"success": True}
