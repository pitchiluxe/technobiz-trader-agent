"""SQLAlchemy ORM models for trading data."""

from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, JSON, String,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TrendAnalysis(Base):
    __tablename__ = "trend_analysis"

    id               = Column(Integer, primary_key=True, index=True)
    timestamp        = Column(DateTime, default=datetime.utcnow, index=True)
    pair             = Column(String, index=True)
    timeframe        = Column(String)
    bias             = Column(String)           # BULLISH | BEARISH | NEUTRAL
    confidence       = Column(Float)
    support_levels   = Column(JSON)
    resistance_levels= Column(JSON)
    liquidity_levels = Column(JSON)

    __table_args__ = (
        Index("ix_trend_pair_ts", "pair", "timestamp"),
    )


class TradeSignalRecord(Base):
    __tablename__ = "trade_signals"

    id                = Column(Integer, primary_key=True, index=True)
    timestamp         = Column(DateTime, default=datetime.utcnow, index=True)
    pair              = Column(String, index=True)
    direction         = Column(String)          # BUY | SELL
    entry_level       = Column(Float)
    stop_loss         = Column(Float)
    take_profit_1     = Column(Float)
    take_profit_2     = Column(Float)
    take_profit_3     = Column(Float)
    risk_reward_ratio = Column(Float)
    confidence        = Column(Float)
    pattern_elements  = Column(JSON)
    entry_type        = Column(String)          # ORDER_BLOCK | BREAKER_BLOCK | FVG
    session           = Column(String)          # london | new_york
    executed          = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_signal_pair_ts", "pair", "timestamp"),
    )


class TradeExecution(Base):
    __tablename__ = "trade_executions"

    id             = Column(Integer, primary_key=True, index=True)
    signal_id      = Column(Integer, ForeignKey("trade_signals.id"), index=True)
    timestamp      = Column(DateTime, default=datetime.utcnow, index=True)
    pair           = Column(String, index=True)
    direction      = Column(String)             # BUY | SELL
    entry_price    = Column(Float)
    entry_time     = Column(DateTime)
    position_size  = Column(Float)
    stop_loss      = Column(Float)
    take_profit_1  = Column(Float)
    take_profit_2  = Column(Float)
    take_profit_3  = Column(Float)
    mt5_ticket     = Column(Integer, nullable=True)
    status         = Column(String)             # PENDING | OPEN | CLOSED
    tp1_hit        = Column(Boolean, default=False)
    tp2_hit        = Column(Boolean, default=False)
    exit_price     = Column(Float, nullable=True)
    exit_time      = Column(DateTime, nullable=True)
    exit_reason    = Column(String, nullable=True)  # TP_HIT | SL_HIT | MANUAL_CLOSE
    pnl            = Column(Float, nullable=True)
    slippage       = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_exec_pair_ts", "pair", "timestamp"),
        Index("ix_exec_ticket", "mt5_ticket"),
    )


class OrderBlockCache(Base):
    """
    Persisted Order Blocks — prevents repainting.

    Once an OB is identified on a specific candle timestamp, it is stored here.
    On subsequent cycles we load these and only scan for NEW OBs since the
    latest stored timestamp.  An OB is expired after OB_PERSISTENCE_HOURS.
    """
    __tablename__ = "order_block_cache"

    id            = Column(Integer, primary_key=True, index=True)
    pair          = Column(String, index=True)
    timeframe     = Column(String)
    direction     = Column(String)              # BULLISH | BEARISH
    ob_type       = Column(String)              # ORDER_BLOCK | BREAKER_BLOCK | FVG
    zone_low      = Column(Float)
    zone_high     = Column(Float)
    candle_ts     = Column(DateTime, index=True)    # timestamp of the candle that formed this OB
    detected_at   = Column(DateTime, default=datetime.utcnow)
    expires_at    = Column(DateTime, index=True)
    is_active     = Column(Boolean, default=True, index=True)
    hit_count     = Column(Integer, default=0)  # how many times price retested

    __table_args__ = (
        Index("ix_ob_pair_tf_active", "pair", "timeframe", "is_active"),
    )


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id             = Column(Integer, primary_key=True, index=True)
    date           = Column(String, index=True)
    total_trades   = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades  = Column(Integer)
    win_rate       = Column(Float)
    daily_pnl      = Column(Float)
    total_pnl      = Column(Float)
    max_drawdown   = Column(Float)
    profit_factor  = Column(Float)
