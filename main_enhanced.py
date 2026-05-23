"""
TechnobizTrader - Enhanced Main Entry Point with Multi-Pair Support

Strict workflow: Trend-Master → Analyse-Master → Trader-Master
Dynamic pair selection with interactive configuration
"""

import asyncio
import logging
import os
import signal
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=False)
load_dotenv(".env.local", override=True)  # local overrides (OpenRouter / Ollama)

# Setup logging
from utils.logger import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

from agents.workflow import TradingWorkflow
from agents.workflow_orchestrator import WorkflowOrchestrator, WorkflowPhase
from agents.trend_master.trend_master import TrendMaster
from agents.analyse_master.analyse_master import AnalyseMaster
from agents.trader_master.trader_master import TraderMaster
from config.settings import settings
from config.trading_pairs_config import TradingPair
from database.db_manager import db_manager
from market_data.mt5_provider import MT5Provider
from utils.startup_validator import StartupValidator
from utils.interactive_trading_manager import InteractiveTradingManager

# Configuration
TRADING_INTERVAL_SECONDS = int(os.getenv("TRADING_INTERVAL_MINUTES", "15")) * 60


async def fetch_market_data(
    provider: MT5Provider, symbol: str
) -> Optional[dict]:
    """
    Fetch OHLC data from MT5 across multiple timeframes.

    Args:
        provider: Authenticated MT5Provider instance
        symbol: Trading pair (e.g., "EURUSD")

    Returns:
        Dictionary with OHLC lists, or None on failure
    """
    market_data = {}
    timeframes = {
        "daily": ("D1", 100),
        "4h": ("H4", 100),
        "1h": ("H1", 50),
    }

    logger.info(f"[DATA] Fetching market data for {symbol}...")

    for key, (tf_symbol, limit) in timeframes.items():
        try:
            candles = await provider.get_candles(symbol, tf_symbol, limit=limit)
            if candles:
                market_data[key] = candles
                logger.info(f"[DATA] ✓ {tf_symbol}: {len(candles)} candles")
            else:
                logger.warning(f"[DATA] ✗ No {tf_symbol} candles")

        except Exception as e:
            logger.error(f"[DATA] Error fetching {tf_symbol}: {e}")

    if not all(market_data.get(k) for k in ("daily", "4h", "1h")):
        logger.error("[DATA] Insufficient data — missing one or more timeframes")
        return None

    return market_data


async def execute_trading_cycle(
    orchestrator: WorkflowOrchestrator,
    workflow: TradingWorkflow,
    provider: MT5Provider,
    pair: TradingPair,
) -> bool:
    """
    Execute complete trading cycle with strict workflow enforcement.

    Phases:
    1. Trend-Master: Market structure analysis
    2. Analyse-Master: ICT pattern detection
    3. Trader-Master: Trade execution

    Args:
        orchestrator: Workflow orchestrator for phase management
        workflow: Three-agent trading workflow
        provider: MT5 data provider
        pair: Trading pair to analyze

    Returns:
        True if cycle completed (with or without trade), False on error
    """
    # Initialize workflow for this cycle
    state = orchestrator.start_cycle(pair.symbol)

    try:
        # ─────────────────────────────────────────────────────────────
        # PHASE 1: TREND-MASTER ANALYSIS
        # ─────────────────────────────────────────────────────────────

        if not orchestrator.begin_trend_analysis():
            logger.error("[CYCLE] Failed to begin trend analysis")
            return False

        # Fetch market data
        market_data = await fetch_market_data(provider, pair.symbol)
        if not market_data:
            logger.error("[CYCLE] Cannot proceed without market data")
            return False

        # Run Trend-Master
        trend_report = await workflow.trend_master.analyze(market_data)

        if not trend_report:
            logger.warning("[CYCLE] Trend-Master: No report generated")
            orchestrator.current_workflow.warnings.append(
                "Trend-Master returned no report"
            )
            return False

        if not orchestrator.complete_trend_analysis(trend_report.to_dict()):
            logger.error("[CYCLE] Failed to store trend report")
            return False

        logger.info(
            f"[CYCLE] Trend: {trend_report.bias} "
            f"(Confidence: {trend_report.confidence}%)"
        )

        # ─────────────────────────────────────────────────────────────
        # PHASE 2: ANALYSE-MASTER SIGNAL GENERATION
        # ─────────────────────────────────────────────────────────────

        if not orchestrator.begin_signal_generation():
            logger.error("[CYCLE] Failed to begin signal generation")
            return False

        # Run Analyse-Master
        trade_signal = await workflow.analyse_master.analyze(
            trend_report.to_dict(),
            candle_data=market_data,
            symbol=pair.symbol,
        )

        if not trade_signal:
            logger.info("[CYCLE] Analyse-Master: No ICT signal generated")
            orchestrator.current_workflow.warnings.append(
                "Analyse-Master generated no signal"
            )
            orchestrator.complete_trade_execution(None)
            return False

        if not orchestrator.complete_signal_generation(trade_signal.to_dict()):
            logger.error("[CYCLE] Failed to store trade signal")
            return False

        logger.info(
            f"[CYCLE] Signal: {trade_signal.direction} @ "
            f"{trade_signal.entry_level} "
            f"(Confidence: {trade_signal.confidence}%)"
        )

        # ─────────────────────────────────────────────────────────────
        # PHASE 3: TRADER-MASTER EXECUTION
        # ─────────────────────────────────────────────────────────────

        if not orchestrator.begin_trade_execution():
            logger.error("[CYCLE] Failed to begin trade execution")
            return False

        # Run Trader-Master
        execution_record = await workflow.trader_master.analyze(
            trade_signal.to_dict()
        )

        if execution_record:
            if not orchestrator.complete_trade_execution(
                execution_record.to_dict()
            ):
                logger.error("[CYCLE] Failed to store execution record")
                return False

            logger.info(
                f"[CYCLE] Trade Executed: {execution_record.status} | "
                f"Ticket: {execution_record.mt5_ticket}"
            )
        else:
            if not orchestrator.complete_trade_execution(None):
                logger.error("[CYCLE] Failed to process trade rejection")
                return False

            logger.info("[CYCLE] Trade rejected by risk management")

        return True

    except Exception as e:
        logger.error(f"[CYCLE] Exception: {e}", exc_info=True)
        orchestrator.current_workflow.errors.append(str(e))
        return False


async def trading_loop(
    provider: MT5Provider,
    workflow: TradingWorkflow,
    orchestrator: WorkflowOrchestrator,
    pairs: list[TradingPair],
) -> None:
    """
    Continuous trading loop — runs cycles for selected pairs.

    Args:
        provider: MT5 data provider
        workflow: Three-agent workflow
        orchestrator: Workflow phase manager
        pairs: List of pairs to trade
    """
    logger.info(
        f"[LOOP] Trading loop started — {len(pairs)} pair(s), "
        f"interval={TRADING_INTERVAL_SECONDS // 60} min"
    )

    pair_index = 0
    cycle_count = 0

    while True:
        try:
            # Reconnect if connection lost
            if not await provider.is_connected():
                logger.warning("[LOOP] MT5 connection lost — reconnecting...")
                if not await provider.connect():
                    logger.error("[LOOP] Reconnect failed — retrying next cycle")
                    await asyncio.sleep(TRADING_INTERVAL_SECONDS)
                    continue

            # Select current pair
            current_pair = pairs[pair_index]

            # Execute trading cycle
            cycle_count += 1
            logger.info(
                f"\n[LOOP] Cycle #{cycle_count} — {current_pair.symbol}"
            )

            success = await execute_trading_cycle(
                orchestrator, workflow, provider, current_pair
            )

            if not success:
                logger.warning(
                    f"[LOOP] Cycle failed for {current_pair.symbol}"
                )

            # Switch to next pair (round-robin)
            if len(pairs) > 1:
                pair_index = (pair_index + 1) % len(pairs)

            # Log performance stats
            stats = orchestrator.get_performance_stats()
            logger.info(
                f"[LOOP] Performance — Cycles: {stats['total_cycles']}, "
                f"Signals: {stats['successful_signals']}, "
                f"Trades: {stats['executed_trades']}"
            )

        except asyncio.CancelledError:
            logger.info("[LOOP] Trading loop cancelled")
            break

        except Exception as e:
            logger.error(f"[LOOP] Unhandled error: {e}", exc_info=True)

        logger.info(
            f"[LOOP] Sleeping {TRADING_INTERVAL_SECONDS // 60} min..."
        )

        try:
            await asyncio.sleep(TRADING_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("[LOOP] Sleep interrupted")
            break


async def main() -> None:
    """Main entry point with multi-pair support."""
    logger.info("=" * 70)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT.upper()}")
    logger.info("=" * 70)

    provider: Optional[MT5Provider] = None
    loop_task: Optional[asyncio.Task] = None

    try:
        # ─────────────────────────────────────────────────────────────
        # STEP 0: Interactive Pair Selection
        # ─────────────────────────────────────────────────────────────

        logger.info("\n[STEP 0] Interactive pair selection...")

        manager = InteractiveTradingManager()
        manager.display_welcome()
        manager.display_quick_start()

        if not manager.display_selection_menu():
            logger.info("[STARTUP] User cancelled pair selection")
            return

        if not manager.validate_pairs():
            logger.error("[STARTUP] Pair validation failed")
            return

        selected_pairs = manager.get_selected_pairs()
        manager.display_selection_summary()

        # ─────────────────────────────────────────────────────────────
        # STEP 1: Startup Validation
        # ─────────────────────────────────────────────────────────────

        logger.info("\n[STEP 1] Running startup validation...")

        if not StartupValidator.validate():
            if settings.ENVIRONMENT == "production":
                logger.error("Startup validation failed in production")
                return
            logger.warning("Startup validation warnings (non-blocking)")

        # ─────────────────────────────────────────────────────────────
        # STEP 2: Database Initialization
        # ─────────────────────────────────────────────────────────────

        logger.info("\n[STEP 2] Initializing database...")
        db_manager.create_tables()
        logger.info(f"  ✓ Database ready: {settings.DATABASE_URL}")

        # ─────────────────────────────────────────────────────────────
        # STEP 3: MT5 Connection
        # ─────────────────────────────────────────────────────────────

        logger.info("\n[STEP 3] Connecting to MetaTrader 5...")

        provider = MT5Provider(
            account=settings.MT5_ACCOUNT,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER,
        )

        if not await provider.connect():
            logger.error("Failed to connect to MetaTrader 5")
            logger.error("  1. Ensure MT5 terminal is running")
            logger.error("  2. Verify MT5 credentials in .env")
            return

        logger.info("  ✓ MT5 connected")

        # ─────────────────────────────────────────────────────────────
        # STEP 4: Initialize Agents & Orchestrator
        # ─────────────────────────────────────────────────────────────

        logger.info("\n[STEP 4] Initializing trading agents...")

        verbose_mode = settings.DEBUG and settings.ENVIRONMENT != "production"
        workflow = TradingWorkflow(verbose=verbose_mode, mt5_provider=provider)
        orchestrator = WorkflowOrchestrator()

        logger.info("  ✓ Trend-Master ready")
        logger.info("  ✓ Analyse-Master ready")
        logger.info("  ✓ Trader-Master ready")
        logger.info("  ✓ Workflow Orchestrator ready")

        # ─────────────────────────────────────────────────────────────
        # STEP 5: Graceful Shutdown Setup
        # ─────────────────────────────────────────────────────────────

        loop = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()

        def _request_shutdown(*_):
            logger.info("\n[MAIN] Shutdown signal received (Ctrl+C)")
            shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _request_shutdown)
            except (NotImplementedError, OSError):
                pass

        # ─────────────────────────────────────────────────────────────
        # STEP 6: Start Trading Loop
        # ─────────────────────────────────────────────────────────────

        logger.info(
            f"\n[STEP 5] Starting trading loop "
            f"({TRADING_INTERVAL_SECONDS // 60} min interval)..."
        )
        logger.info("  Press Ctrl+C to stop gracefully\n")

        loop_task = asyncio.create_task(
            trading_loop(provider, workflow, orchestrator, selected_pairs)
        )

        # Wait for loop or shutdown signal
        done, pending = await asyncio.wait(
            [loop_task, asyncio.create_task(shutdown_event.wait())],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        raise SystemExit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise SystemExit(1)

    finally:
        if loop_task and not loop_task.done():
            loop_task.cancel()
            try:
                await loop_task
            except asyncio.CancelledError:
                pass

        if provider is not None:
            await provider.disconnect()

        db_manager.close()

        logger.info("\n[SHUTDOWN] Complete")


if __name__ == "__main__":
    asyncio.run(main())
