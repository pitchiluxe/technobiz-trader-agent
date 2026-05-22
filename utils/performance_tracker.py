"""Trade performance tracking and metrics."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json


@dataclass
class TradeMetrics:
    """Container for trade performance metrics."""
    
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    total_pnl: float = 0.0
    average_pnl_per_trade: float = 0.0
    profit_factor: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    max_consecutive_losses: int = 0
    max_drawdown: float = 0.0


class PerformanceTracker:
    """Track trading performance and calculate metrics."""

    def __init__(self):
        """Initialize performance tracker."""
        self.trades: List[Dict[str, Any]] = []
        self.daily_pnl: Dict[str, float] = {}

    def record_trade(
        self,
        entry_price: float,
        exit_price: float,
        position_size: float,
        exit_reason: str,
        timestamp: datetime = None,
    ):
        """
        Record a completed trade.

        Args:
            entry_price: Trade entry price
            exit_price: Trade exit price
            position_size: Position size (in lots)
            exit_reason: Reason for trade exit
            timestamp: Trade timestamp
        """
        timestamp = timestamp or datetime.now()
        pnl = (exit_price - entry_price) * position_size * 100000  # Simplified P&L calculation
        
        trade = {
            "entry_price": entry_price,
            "exit_price": exit_price,
            "position_size": position_size,
            "pnl": pnl,
            "exit_reason": exit_reason,
            "timestamp": timestamp,
            "is_win": pnl > 0,
        }
        
        self.trades.append(trade)

        # Update daily P&L
        date_key = timestamp.date().isoformat()
        self.daily_pnl[date_key] = self.daily_pnl.get(date_key, 0.0) + pnl

    def calculate_metrics(self) -> TradeMetrics:
        """
        Calculate comprehensive performance metrics.

        Returns:
            TradeMetrics object with all calculations
        """
        if not self.trades:
            return TradeMetrics()

        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t["is_win"])
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t["pnl"] for t in self.trades)
        wins = [t["pnl"] for t in self.trades if t["is_win"]]
        losses = [t["pnl"] for t in self.trades if not t["is_win"]]

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0.0
        
        average_pnl = total_pnl / total_trades if total_trades > 0 else 0.0
        average_win = sum(wins) / len(wins) if wins else 0.0
        average_loss = sum(losses) / len(losses) if losses else 0.0
        
        # Profit factor: Gross profit / Gross loss
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 1.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Max consecutive losses
        max_consecutive = 0
        current_consecutive = 0
        for trade in self.trades:
            if not trade["is_win"]:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return TradeMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            loss_rate=loss_rate,
            total_pnl=total_pnl,
            average_pnl_per_trade=average_pnl,
            profit_factor=profit_factor,
            largest_win=max(wins) if wins else 0.0,
            largest_loss=min(losses) if losses else 0.0,
            average_win=average_win,
            average_loss=average_loss,
            max_consecutive_losses=max_consecutive,
        )

    def get_daily_summary(self) -> Dict[str, float]:
        """Get daily P&L summary."""
        return self.daily_pnl

    def export_trades_json(self, filepath: str):
        """Export trades to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.trades, f, indent=2, default=str)
