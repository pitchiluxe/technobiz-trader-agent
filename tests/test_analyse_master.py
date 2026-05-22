"""Tests for Analyse-Master agent — ICT signal validation rules."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from agents.analyse_master.analyse_master import AnalyseMaster, TradeSignal
from config.constants import MIN_CONFIDENCE_PCT, MIN_RR_RATIO
from tests.fixtures.sample_candles import sample_ohlc_data, sample_trend_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal(
    confidence: float = 80.0,
    rr: float = 2.5,
    direction: str = "BUY",
    all_elements: bool = True,
) -> TradeSignal:
    """Build a minimal valid TradeSignal for assertion tests."""
    now = datetime.now(timezone.utc)
    pattern = {
        "liquidity_sweep": all_elements,
        "break_of_structure": all_elements,
        "imbalance_zone": all_elements,
        "pullback_entry": all_elements,
    }
    return TradeSignal(
        entry_level=1.0530,
        stop_loss=1.0490 if direction == "BUY" else 1.0570,
        take_profit_1=1.0610,
        take_profit_2=1.0650,
        take_profit_3=1.0700,
        risk_reward_ratio=rr,
        confidence=confidence,
        pattern_elements=pattern,
        kill_zone_start=now,
        kill_zone_end=now,
        zone_top=1.0540,
        zone_bottom=1.0520,
        direction=direction,
    )


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_analyse_master_initialises():
    agent = AnalyseMaster()
    assert agent.name == "Analyse-Master"


# ---------------------------------------------------------------------------
# TradeSignal model
# ---------------------------------------------------------------------------

def test_trade_signal_to_dict_contains_required_keys():
    sig = _make_signal()
    d = sig.to_dict()
    required = [
        "entry_level", "stop_loss", "take_profit_1", "take_profit_2", "take_profit_3",
        "risk_reward_ratio", "confidence", "pattern_elements", "direction",
    ]
    for key in required:
        assert key in d, f"Missing key: {key}"


def test_trade_signal_direction_values():
    buy_sig = _make_signal(direction="BUY")
    sell_sig = _make_signal(direction="SELL")
    assert buy_sig.to_dict()["direction"] == "BUY"
    assert sell_sig.to_dict()["direction"] == "SELL"


def test_trade_signal_low_confidence_flag():
    sig = _make_signal(confidence=MIN_CONFIDENCE_PCT - 1)
    assert sig.confidence < MIN_CONFIDENCE_PCT


def test_trade_signal_low_rr_flag():
    sig = _make_signal(rr=MIN_RR_RATIO - 0.5)
    assert sig.risk_reward_ratio < MIN_RR_RATIO


def test_trade_signal_missing_ict_elements():
    sig = _make_signal(all_elements=False)
    elements = sig.pattern_elements
    assert not all(elements.values()), "Expected at least one missing ICT element"


# ---------------------------------------------------------------------------
# Kill-zone check
# ---------------------------------------------------------------------------

def test_kill_zone_outside_hours_returns_false():
    """_kill_zone should return inactive when UTC hour is outside 08-11 and 13-16."""
    agent = AnalyseMaster()
    with patch("agents.analyse_master.analyse_master.datetime") as mock_dt:
        # Simulate 03:00 UTC — outside all kill zones
        fake_now = datetime(2024, 4, 1, 3, 0, tzinfo=timezone.utc)
        mock_dt.now.return_value = fake_now
        mock_dt.fromisoformat = datetime.fromisoformat
        active, session, _, _ = agent._kill_zone()
    assert not active
    assert session == ""


def test_kill_zone_inside_london_hours_returns_true():
    """_kill_zone should be active at 09:00 UTC (London open)."""
    agent = AnalyseMaster()
    with patch("agents.analyse_master.analyse_master.datetime") as mock_dt:
        fake_now = datetime(2024, 4, 1, 9, 0, tzinfo=timezone.utc)
        mock_dt.now.return_value = fake_now
        mock_dt.fromisoformat = datetime.fromisoformat
        active, session, _, _ = agent._kill_zone()
    assert active
    assert "london" in session.lower()


# ---------------------------------------------------------------------------
# ATR helper
# ---------------------------------------------------------------------------

def test_atr_returns_zero_on_insufficient_data():
    agent = AnalyseMaster()
    candles = sample_ohlc_data()  # only 3 candles — less than ATR_PERIOD + 1
    result = agent._atr(candles, period=14)
    assert result == 0.0


def test_atr_positive_on_enough_data():
    agent = AnalyseMaster()
    from market_data.data_provider import OHLCData
    from datetime import timedelta
    base = datetime(2024, 1, 1, 0, 0)
    candles = [
        OHLCData(
            timestamp=base + timedelta(hours=i),
            open_price=1.05 + i * 0.001,
            high_price=1.05 + i * 0.001 + 0.002,
            low_price=1.05 + i * 0.001 - 0.001,
            close_price=1.05 + i * 0.001 + 0.0005,
            volume=100000.0,
        )
        for i in range(25)
    ]
    result = agent._atr(candles, period=14)
    assert result > 0.0


# ---------------------------------------------------------------------------
# Swing detection
# ---------------------------------------------------------------------------

def test_swing_highs_detects_peaks():
    agent = AnalyseMaster()
    from market_data.data_provider import OHLCData
    from datetime import timedelta
    # 1H uses window=5; peak must sit at index >= 5 and < len-5
    # Build 15 candles with the peak at index 7 (middle)
    highs = [1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.5, 1.2, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0]
    base = datetime(2024, 1, 1, 0, 0)
    candles = [
        OHLCData(
            timestamp=base + timedelta(hours=i),
            open_price=h - 0.05,
            high_price=h,
            low_price=h - 0.1,
            close_price=h - 0.02,
            volume=1000.0,
        )
        for i, h in enumerate(highs)
    ]
    result = agent._swing_highs(candles, timeframe="1H")
    assert len(result) >= 1
    assert max(result) == pytest.approx(1.5)


def test_swing_lows_detects_troughs():
    agent = AnalyseMaster()
    from market_data.data_provider import OHLCData
    from datetime import timedelta
    # 1H uses window=5; trough must sit at index >= 5 and < len-5
    lows = [1.1, 1.1, 1.1, 1.1, 1.1, 1.0, 0.9, 0.5, 0.9, 1.0, 1.1, 1.1, 1.1, 1.1, 1.1]
    base = datetime(2024, 1, 1, 0, 0)
    candles = [
        OHLCData(
            timestamp=base + timedelta(hours=i),
            open_price=l + 0.05,
            high_price=l + 0.1,
            low_price=l,
            close_price=l + 0.02,
            volume=1000.0,
        )
        for i, l in enumerate(lows)
    ]
    result = agent._swing_lows(candles, timeframe="1H")
    assert len(result) >= 1
    assert min(result) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Async analyze() — no real provider needed (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_analyze_returns_none_outside_kill_zone():
    """analyze() must return None when called outside kill zone hours."""
    agent = AnalyseMaster()
    trend_report = sample_trend_report()

    candles = sample_ohlc_data() * 34  # enough candles

    with patch.object(agent, "_kill_zone", return_value=(
        False, "", datetime.now(timezone.utc), datetime.now(timezone.utc)
    )):
        result = await agent.analyze(
            trend_report,
            candle_data={"1h": candles, "4h": candles, "daily": candles},
            symbol="EURUSD",
        )
    assert result is None


@pytest.mark.anyio
async def test_analyze_returns_none_on_missing_trend_report():
    """analyze() must return None when the trend report is empty (missing required keys)."""
    agent = AnalyseMaster()
    result = await agent.analyze({}, candle_data={}, symbol="EURUSD")
    assert result is None
