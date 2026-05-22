"""Trader-Master route — POST /api/trades/execute (requires prior approval)."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agents.trader_master.trader_master import TraderMaster

logger = logging.getLogger(__name__)
router = APIRouter()
_trader_master: Optional[TraderMaster] = None


def _get_agent() -> TraderMaster:
    global _trader_master
    if _trader_master is None:
        _trader_master = TraderMaster(verbose=False)
    return _trader_master


# ── Pydantic models ───────────────────────────────────────────────────────────

class TradeExecutionRequest(BaseModel):
    symbol: str
    trade_signal: Dict[str, Any]
    user_approved: bool = False   # GUI sets this after user clicks Approve


class TradeExecutionResponse(BaseModel):
    success: bool
    symbol: str
    data: Dict[str, Any] = {}
    rejected_reason: Optional[str] = None
    error: Optional[str] = None


class ApprovalRequest(BaseModel):
    trade_signal: Dict[str, Any]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/request-approval")
async def request_approval(body: ApprovalRequest, request: Request):
    """
    Send the TradeSignal to the GUI for display in the approval modal.
    The GUI will call /execute once the user approves or rejects.
    """
    manager = request.app.state.manager
    await manager.send_agent_status(
        "trader_master",
        "waiting_approval",
        "Waiting for user approval…",
        body.trade_signal,
    )
    return {
        "success": True,
        "message": "Trade signal sent to GUI approval modal",
        "trade_signal": body.trade_signal,
    }


@router.post("/execute", response_model=TradeExecutionResponse)
async def execute_trade(body: TradeExecutionRequest, request: Request):
    """
    Execute (or reject) a previously approved TradeSignal.
    `user_approved` must be True — enforced server-side as a safety gate.
    """
    manager = request.app.state.manager
    agent = _get_agent()

    if not body.user_approved:
        await manager.send_agent_status("trader_master", "idle", "Trade rejected by user")
        return TradeExecutionResponse(
            success=False,
            symbol=body.symbol,
            rejected_reason="User did not approve the trade",
        )

    await manager.send_agent_status(
        "trader_master", "analyzing", f"Executing trade for {body.symbol}…"
    )

    try:
        execution_record = await agent.analyze(body.trade_signal)

        if execution_record is None:
            await manager.send_agent_status(
                "trader_master", "error", "Trader-Master rejected execution (risk constraints)"
            )
            return TradeExecutionResponse(
                success=False,
                symbol=body.symbol,
                rejected_reason="Risk management constraints rejected the trade",
            )

        result = execution_record.to_dict()
        await manager.send_agent_status(
            "trader_master",
            "success",
            f"Trade executed — status: {result.get('status', 'N/A')}",
            result,
        )
        return TradeExecutionResponse(success=True, symbol=body.symbol, data=result)

    except Exception as exc:
        logger.exception("[Trade] Execution failed for %s", body.symbol)
        await manager.send_agent_status("trader_master", "error", str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reset")
async def reset_agent(request: Request):
    global _trader_master
    _trader_master = None
    await request.app.state.manager.send_agent_status("trader_master", "idle", "Agent reset")
    return {"success": True}
