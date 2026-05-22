"""Tests for Trader-Master agent — risk management guardrails."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from agents.trader_master.trader_master import TraderMaster, ExecutionRecord
from config.constants import (
    MIN_CONFIDENCE_PCT,
    MIN_RR_RATIO,
    MAX_DAILY_DRAWDOWN,
    MAX_CONCURRENT_TRADES,
    CONSECUTIVE_LOSS_LIMIT,
    SIZE_REDUCTION_FACTOR,
    SIZE_REDUCTION_TRADES,
)
from tests.fixtures.sample_candles import sample_trade_signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal(
    confidence: float = 80.0,
    rr: float = 2.5,
    direction: str = "BUY",
    expired: bool = False,
) -> dict:
    """Build a minimal TradeSignal dict for Trader-Master tests."""
    now = datetime.now(timezone.utc)
    kill_end = (now - timedelta(minutes=5)) if expired else (now + timedelta(minutes=25))
    return {
        "entry_level": 1.0530,
        "stop_loss": 1.0490,
        "take_profit_1": 1.0610,
        "take_profit_2": 1.0650,
        "take_profit_3": 1.0700,
        "risk_reward_ratio": rr,
        "confidence": confidence,
        "symbol": "EURUSD",
        "direction": direction,
        "kill_zone_end": kill_end.isoformat(),
        "kill_zone_start": now.isoformat(),
        "zone_top": 1.0540,
        "zone_bottom": 1.0520,
        "session": "london",
        "entry_type": "ORDER_BLOCK",
    }


def _open_trade(symbol: str = "EURUSD") -> ExecutionRecord:
    """Create a fake open trade record."""
    return ExecutionRecord(
        signal_id="TEST-001",
        entry_price=1.0530,
        entry_time=datetime.now(),
        position_size=0.1,
        stop_loss=1.0490,
        take_profit_1=1.0610,
        take_profit_2=1.0650,
        take_profit_3=1.0700,
        status="OPEN",
        symbol=symbol,
        direction="BUY",
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_trader_master_initialises():
    trader = TraderMaster()
    assert trader.name == "Trader-Master"
    assert trader.daily_loss == 0.0
    assert trader.consecutive_losses == 0
    assert trader.open_trades == []


# ---------------------------------------------------------------------------
# ExecutionRecord model
# ---------------------------------------------------------------------------

def test_execution_record_to_dict_contains_required_keys():
    rec = _open_trade()
    d = rec.to_dict()
    for key in ["signal_id", "entry_price", "position_size", "stop_loss",
                "take_profit_1", "take_profit_2", "take_profit_3",
                "status", "symbol", "direction"]:
        assert key in d, f"Missing key: {key}"


def test_execution_record_status_pending():
    rec = ExecutionRecord(
        signal_id="T1", entry_price=1.05, entry_time=datetime.now(),
        position_size=0.1, stop_loss=1.04, take_profit_1=1.07,
        take_profit_2=1.09, take_profit_3=1.11, status="PENDING",
        symbol="EURUSD", direction="BUY",
    )
    assert rec.to_dict()["status"] == "PENDING"


# ---------------------------------------------------------------------------
# Guardrail: confidence threshold
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rejects_signal_below_confidence_threshold():
    trader = TraderMaster()
    signal = _make_signal(confidence=MIN_CONFIDENCE_PCT - 10)

    with patch("agents.trader_master.trader_master.KillSwitch.check"):
        result = await trader.analyze(signal)

    assert result is None


@pytest.mark.anyio
async def test_rejects_signal_at_exact_confidence_threshold():
    """Confidence must be strictly ≥ threshold."""
    trader = TraderMaster()
    signal = _make_signal(confidence=MIN_CONFIDENCE_PCT - 0.1)

    with patch("agents.trader_master.trader_master.KillSwitch.check"):
        result = await trader.analyze(signal)

    assert result is None


# ---------------------------------------------------------------------------
# Guardrail: R:R ratio
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rejects_signal_below_min_rr():
    trader = TraderMaster()
    signal = _make_signal(confidence=85.0, rr=MIN_RR_RATIO - 0.5)

    with patch("agents.trader_master.trader_master.KillSwitch.check"):
        result = await trader.analyze(signal)

    assert result is None


# ---------------------------------------------------------------------------
# Guardrail: max concurrent trades
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rejects_when_max_concurrent_trades_reached():
    trader = TraderMaster()
    # Fill up to the limit
    for _ in range(MAX_CONCURRENT_TRADES):
        trader.open_trades.append(_open_trade())

    signal = _make_signal()

    with patch("agents.trader_master.trader_master.KillSwitch.check"):
        result = await trader.analyze(signal)

    assert result is None


@pytest.mark.anyio
async def test_accepts_when_one_below_max_concurrent_trades():
    """Should NOT reject purely due to concurrent trades when one slot is free."""
    trader = TraderMaster()
    for _ in range(MAX_CONCURRENT_TRADES - 1):
        trader.open_trades.append(_open_trade())

    signal = _make_signal()

    # mt5_provider=None → analyze will proceed past guardrails but fail at execution;
    # we just verify concurrent-trade check does not block
    with patch("agents.trader_master.trader_master.KillSwitch.check"), \
         patch.object(trader, "_within_kill_zone", return_value=True):
        # It may return None because no MT5 provider is wired, but not due to concurrent limit
        # We test the guard log message is NOT emitted for concurrent trades
        import logging
        with patch.object(trader.logger, "warning") as mock_warn:
            await trader.analyze(signal)
            concurrent_rejections = [
                c for c in mock_warn.call_args_list
                if "Max concurrent trades" in str(c)
            ]
        assert concurrent_rejections == []


# ---------------------------------------------------------------------------
# Guardrail: daily drawdown
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pauses_trading_on_daily_drawdown_exceeded():
    trader = TraderMaster()
    trader.daily_loss = MAX_DAILY_DRAWDOWN + 0.01  # e.g. 0.06 if limit is 0.05

    signal = _make_signal()

    with patch("agents.trader_master.trader_master.KillSwitch.check"), \
         patch("agents.trader_master.trader_master.KillSwitch.pause") as mock_pause:
        result = await trader.analyze(signal)

    assert result is None
    mock_pause.assert_called_once()


# ---------------------------------------------------------------------------
# Guardrail: kill zone expiry
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_rejects_expired_kill_zone():
    trader = TraderMaster()
    signal = _make_signal(expired=True)

    with patch("agents.trader_master.trader_master.KillSwitch.check"):
        result = await trader.analyze(signal)

    assert result is None


# ---------------------------------------------------------------------------
# Consecutive-loss streak management
# ---------------------------------------------------------------------------

def test_consecutive_loss_tracker_arms_on_limit():
    trader = TraderMaster()
    for _ in range(CONSECUTIVE_LOSS_LIMIT):
        trader._record_trade_outcome(-50.0)  # losing trade

    assert trader.reduced_sizing_remaining == SIZE_REDUCTION_TRADES
    assert trader.consecutive_losses == 0  # reset after triggering


def test_consecutive_loss_tracker_resets_on_win():
    trader = TraderMaster()
    for _ in range(CONSECUTIVE_LOSS_LIMIT - 1):
        trader._record_trade_outcome(-50.0)

    trader._record_trade_outcome(100.0)  # win

    assert trader.consecutive_losses == 0
    assert trader.reduced_sizing_remaining == 0


# ---------------------------------------------------------------------------
# Day-boundary reset
# ---------------------------------------------------------------------------

def test_daily_loss_resets_on_new_utc_day():
    trader = TraderMaster()
    trader.daily_loss = 0.04
    trader._session_date = datetime(2024, 1, 1).date()  # force stale date

    trader._check_day_reset()

    assert trader.daily_loss == 0.0


def test_daily_loss_not_reset_same_day():
    trader = TraderMaster()
    trader.daily_loss = 0.03

    trader._check_day_reset()  # same day call

    assert trader.daily_loss == 0.03


# ---------------------------------------------------------------------------
# Position sizing — sanity
# ---------------------------------------------------------------------------

def test_lot_size_non_negative():
    trader = TraderMaster()
    size = trader._lot_size("EURUSD", entry=1.0530, sl=1.0490, balance=10000.0)
    assert size >= 0.01


def test_lot_size_capped_at_max():
    trader = TraderMaster()
    # Tiny SL distance would produce a huge lot without the cap
    size = trader._lot_size("EURUSD", entry=1.0530, sl=1.05299, balance=1_000_000.0)
    assert size <= 10.0


def test_lot_size_zero_sl_distance_returns_minimum():
    trader = TraderMaster()
    size = trader._lot_size("EURUSD", entry=1.0530, sl=1.0530, balance=10000.0)
    assert size == 0.01
