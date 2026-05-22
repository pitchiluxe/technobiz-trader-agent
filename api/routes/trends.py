"""Trend-Master route — POST /api/trends/analyze."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents.trend_master.trend_master import TrendMaster

logger = logging.getLogger(__name__)
router = APIRouter()
_trend_master: Optional[TrendMaster] = None


def _get_agent() -> TrendMaster:
    global _trend_master
    if _trend_master is None:
        _trend_master = TrendMaster(verbose=False)
    return _trend_master


# ── Pydantic request/response models ─────────────────────────────────────────

class CandleData(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class TrendAnalysisRequest(BaseModel):
    symbol: str
    daily: List[CandleData] = []
    h4: List[CandleData] = []
    h1: List[CandleData] = []


class TrendAnalysisResponse(BaseModel):
    success: bool
    symbol: str
    data: Dict[str, Any] = {}
    error: Optional[str] = None


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=TrendAnalysisResponse)
async def analyze_trend(body: TrendAnalysisRequest, request: Request):
    """
    Run Trend-Master analysis for a given symbol.
    Broadcasts real-time status to WebSocket clients.
    """
    manager = request.app.state.manager
    agent = _get_agent()

    await manager.send_agent_status(
        "trend_master", "analyzing", f"Analyzing {body.symbol}…"
    )

    try:
        # Convert Pydantic models to dicts that TrendMaster understands
        market_data = {
            "symbol": body.symbol,
            "daily": [c.model_dump() for c in body.daily],
            "4h": [c.model_dump() for c in body.h4],
            "1h": [c.model_dump() for c in body.h1],
        }

        trend_report = await agent.analyze(market_data)

        if trend_report is None:
            await manager.send_agent_status(
                "trend_master", "error", "No trend signal — conditions not met"
            )
            return TrendAnalysisResponse(
                success=False,
                symbol=body.symbol,
                error="Trend-Master returned no signal (conditions not met)",
            )

        result = trend_report.to_dict()
        await manager.send_agent_status(
            "trend_master", "success", f"{body.symbol} trend: {result.get('bias', 'N/A')}", result
        )
        return TrendAnalysisResponse(success=True, symbol=body.symbol, data=result)

    except Exception as exc:
        logger.exception("[Trend] Analysis failed for %s", body.symbol)
        await manager.send_agent_status("trend_master", "error", str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
async def reset_agent(request: Request):
    """Reset (re-instantiate) the Trend-Master agent."""
    global _trend_master
    _trend_master = None
    await request.app.state.manager.send_agent_status("trend_master", "idle", "Agent reset")
    return {"success": True}
