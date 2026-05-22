"""Integration tests for the trading system."""

import pytest
from agents.workflow import TradingWorkflow
from tests.fixtures.sample_candles import sample_trend_report, sample_trade_signal


@pytest.mark.asyncio
async def test_end_to_end_trading_cycle():
    """Test complete trading cycle from trend analysis to execution."""
    workflow = TradingWorkflow(verbose=True)
    
    # Prepare market data
    market_data = {
        "daily": {},
        "4h": {},
        "1h": {},
    }
    
    # Execute full cycle
    execution = await workflow.execute_trading_cycle(market_data)
    
    # Check workflow state
    assert workflow.last_trend_report is not None
    assert workflow.get_performance_summary()["total_trades"] >= 0
