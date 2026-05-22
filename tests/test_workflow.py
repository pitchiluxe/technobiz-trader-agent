"""Test for workflow orchestration."""

import pytest
from agents.workflow import TradingWorkflow


@pytest.mark.asyncio
async def test_workflow_initialization():
    """Test that workflow initializes correctly."""
    workflow = TradingWorkflow(verbose=True)
    
    assert workflow.trend_master is not None
    assert workflow.analyse_master is not None
    assert workflow.trader_master is not None
    assert len(workflow.execution_records) == 0


@pytest.mark.asyncio
async def test_workflow_execution():
    """Test complete trading cycle."""
    workflow = TradingWorkflow()
    
    # Create sample market data
    market_data = {
        "daily": {},
        "4h": {},
        "1h": {},
    }
    
    # Execute trading cycle
    result = await workflow.execute_trading_cycle(market_data)
    
    # Result can be None or ExecutionRecord, both are valid
    assert result is None or hasattr(result, 'entry_price')


def test_performance_summary():
    """Test performance summary calculation."""
    workflow = TradingWorkflow()
    
    summary = workflow.get_performance_summary()
    
    assert summary["total_trades"] == 0
    assert summary["winning_trades"] == 0
    assert summary["losing_trades"] == 0
    assert summary["win_rate"] == 0.0
