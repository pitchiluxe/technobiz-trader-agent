"""
TechnobizTrader — Main Entry Point

Strict workflow: Trend-Master → Analyse-Master → Trader-Master
Improvements vs initial version:
  - Symbol whitelist validation (prevents prompt injection via symbol strings)
  - Kill switch checked at every cycle start
  - Exponential reconnect back-off (5s → 10s → 30s → 60s → 300s)
  - Candle cache (TTL-based, avoids re-fetching unchanged HTF data)
  - Per-cycle WorkflowState isolation (no state bleed across pairs)
  - open_trades reconciled from MT5 on startup (crash recovery)
"""

import asyncio
import logging
import os
import signal
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv(override=False)
load_dotenv(".env.local", override=True)  # local overrides (OpenRouter / Ollama)

from utils.logger import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

from agents.workflow import TradingWorkflow
from agents.workflow_orchestrator import WorkflowOrchestrator
from config.constants import ALLOWED_SYMBOLS, RECONNECT_DELAYS, TIMEFRAME_MINUTES
from config.kill_switch import KillSwitch
from config.settings import settings
from config.trading_pairs_config import TradingPair
from database.db_manager import db_manager
from market_data.mt5_provider import MT5Provider
from utils.candle_cache import CandleCache
from utils.startup_validator import StartupValidator
from utils.interactive_trading_manager import InteractiveTradingManager

TRADING_INTERVAL_SECONDS = int(os.getenv("TRADING_INTERVAL_MINUTES", "15")) * 60

# Module-level candle cache (shared across cycles, all pairs)
_candle_cache = CandleCache()


# ──────────────────────────────────────────────────────────────────────────────
# Symbol validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_symbol(symbol: str) -> str:
    """
    Whitelist-validate and normalise a trading symbol.
    Raises ValueError for unknown or potentially injected symbols.
    """
    clean = symbol.strip().upper()
    if not clean.isalnum():
        raise ValueError(f"Symbol '{clean}' contains non-alphanumeric characters")
    if clean not in ALLOWED_SYMBOLS:
        raise ValueError(
            f"Symbol '{clean}' not in allowed list. "
            f"Allowed: {sorted(ALLOWED_SYMBOLS)}"
        )
    return clean


# ──────────────────────────────────────────────────────────────────────────────
# Market data fetch (with TTL cache)
# ──────────────────────────────────────────────────────────────────────────────

async def fetch_market_data(
    provider: MT5Provider,
    symbol: str,
    cache: CandleCache,
) -> Optional[dict]:
    """
    Fetch OHLCV data across multiple timeframes, using the candle cache
    for unchanged higher-timeframe data (Daily, 4H).

    Returns None if any required timeframe is missing.
    """
    # (display_key, mt5_tf_key, candle_limit)
    timeframes = [
        ("daily",  "D",   100),
        ("4h",     "4H",  100),
        ("1h",     "1H",   50),
    ]

    market_data: dict = {}

    for key, tf, limit in timeframes:
        # Try cache first (HTF data changes rarely)
        cached = cache.get(symbol, tf)
        if cached is not None:
            market_data[key] = cached
            continue

        try:
            candles = await provider.get_candles(symbol, tf, limit=limit)
        except Exception as exc:
            logger.error("[DATA] Error fetching %s %s: %s", symbol, tf, exc)
            candles = []

        if candles:
            market_data[key] = candles
            cache.set(symbol, tf, candles)
            logger.info("[DATA] ✓ %s %s: %d candles", symbol, tf, len(candles))
        else:
            logger.warning("[DATA] ✗ No %s candles for %s", tf, symbol)

    if not all(market_data.get(k) for k in ("daily", "4h", "1h")):
        logger.error("[DATA] Insufficient data for %s — missing timeframe(s)", symbol)
        return None

    return market_data


# ──────────────────────────────────────────────────────────────────────────────
# Single trading cycle
# ──────────────────────────────────────────────────────────────────────────────

async def execute_trading_cycle(
    workflow:    TradingWorkflow,
    provider:    MT5Provider,
    pair:        TradingPair,
    cache:       CandleCache,
) -> bool:
    """
    Execute one complete Trend → Signal → Execution cycle for a single pair.

    Each cycle creates its own WorkflowOrchestrator so state never bleeds
    between pairs or concurrent calls.
    """
    symbol = validate_symbol(pair.symbol)

    # Kill-switch check — raises RuntimeError if paused
    try:
        KillSwitch.check(cycle_label=symbol)
    except RuntimeError as exc:
        logger.warning("[CYCLE] %s", exc)
        return False

    # Fresh orchestrator per cycle — no shared mutable state between pairs
    orchestrator = WorkflowOrchestrator()
    state = orchestrator.start_cycle(symbol)

    try:
        # ── Phase 1: Trend-Master ──────────────────────────────────────
        if not orchestrator.begin_trend_analysis():
            return False

        market_data = await fetch_market_data(provider, symbol, cache)
        if not market_data:
            return False

        trend_report = await workflow.trend_master.analyze(market_data)
        if not trend_report:
            logger.warning("[CYCLE] Trend-Master: No report for %s", symbol)
            return False

        if not orchestrator.complete_trend_analysis(trend_report.to_dict()):
            return False

        logger.info("[CYCLE] Trend: %s  Confidence: %.1f%%",
                    trend_report.bias, trend_report.confidence)

        # ── Phase 2: Analyse-Master ────────────────────────────────────
        if not orchestrator.begin_signal_generation():
            return False

        trade_signal = await workflow.analyse_master.analyze(
            trend_report.to_dict(),
            candle_data=market_data,
            symbol=symbol,
        )

        if not trade_signal:
            logger.info("[CYCLE] Analyse-Master: No ICT signal for %s", symbol)
            orchestrator.complete_trade_execution(None)
            return True   # normal — no signal ≠ error

        if not orchestrator.complete_signal_generation(trade_signal.to_dict()):
            return False

        logger.info("[CYCLE] Signal: %s @ %.5f  Confidence: %.1f%%",
                    trade_signal.direction, trade_signal.entry_level,
                    trade_signal.confidence)

        # ── Phase 3: Trader-Master ─────────────────────────────────────
        if not orchestrator.begin_trade_execution():
            return False

        execution_record = await workflow.trader_master.analyze(
            trade_signal.to_dict(),
            market_data=market_data,
        )

        orchestrator.complete_trade_execution(
            execution_record.to_dict() if execution_record else None
        )

        if execution_record:
            logger.info("[CYCLE] Trade executed — ticket=%s status=%s",
                        execution_record.mt5_ticket, execution_record.status)
        else:
            logger.info("[CYCLE] Trade rejected by risk management")

        return True

    except ValueError as exc:
        logger.error("[CYCLE] Invalid symbol: %s", exc)
        return False
    except Exception as exc:
        logger.error("[CYCLE] Unhandled exception: %s", exc, exc_info=True)
        state.errors.append(str(exc))
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Continuous trading loop with exponential reconnect back-off
# ──────────────────────────────────────────────────────────────────────────────

async def trading_loop(
    provider: MT5Provider,
    workflow: TradingWorkflow,
    pairs:    List[TradingPair],
    cache:    CandleCache,
) -> None:
    logger.info(
        "[LOOP] Started — %d pair(s), interval=%d min",
        len(pairs), TRADING_INTERVAL_SECONDS // 60,
    )

    pair_index    = 0
    cycle_count   = 0
    reconnect_idx = 0   # index into RECONNECT_DELAYS

    while True:
        try:
            # ── MT5 health check with exponential back-off ─────────────
            if not await provider.is_connected():
                delay = RECONNECT_DELAYS[min(reconnect_idx, len(RECONNECT_DELAYS) - 1)]
                logger.warning("[LOOP] MT5 connection lost — reconnecting in %ds", delay)
                await asyncio.sleep(delay)

                if await provider.connect():
                    reconnect_idx = 0
                    logger.info("[LOOP] MT5 reconnected")
                else:
                    reconnect_idx += 1
                    logger.error("[LOOP] Reconnect attempt %d failed", reconnect_idx)
                    continue

            reconnect_idx = 0  # reset back-off on successful connection

            # ── Execute cycle ──────────────────────────────────────────
            current_pair = pairs[pair_index]
            cycle_count += 1
            logger.info("[LOOP] Cycle #%d — %s", cycle_count, current_pair.symbol)

            await execute_trading_cycle(workflow, provider, current_pair, cache)

            # Round-robin pair rotation
            if len(pairs) > 1:
                pair_index = (pair_index + 1) % len(pairs)

        except asyncio.CancelledError:
            logger.info("[LOOP] Cancelled")
            break
        except Exception as exc:
            logger.error("[LOOP] Unhandled: %s", exc, exc_info=True)

        logger.info("[LOOP] Sleeping %d min…", TRADING_INTERVAL_SECONDS // 60)
        try:
            await asyncio.sleep(TRADING_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            break


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    logger.info("=" * 70)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment: %s", settings.ENVIRONMENT.upper())
    logger.info("=" * 70)

    provider:  Optional[MT5Provider] = None
    loop_task: Optional[asyncio.Task] = None

    try:
        # ── Step 0: Interactive pair selection ─────────────────────────
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

        # Whitelist-validate all selected pairs up front
        for pair in selected_pairs:
            try:
                pair.symbol = validate_symbol(pair.symbol)
            except ValueError as exc:
                logger.error("[STARTUP] %s", exc)
                return

        # ── Step 1: Startup validation ─────────────────────────────────
        if not StartupValidator.validate():
            if settings.ENVIRONMENT == "production":
                logger.error("[STARTUP] Validation failed in production")
                return
            logger.warning("[STARTUP] Validation warnings (non-blocking in dev)")

        # ── Step 2: Database ───────────────────────────────────────────
        db_manager.create_tables()
        logger.info("[STARTUP] Database ready: %s", settings.DATABASE_URL)

        # ── Step 3: MT5 connection ─────────────────────────────────────
        provider = MT5Provider(
            account  = settings.MT5_ACCOUNT,
            password = settings.MT5_PASSWORD,
            server   = settings.MT5_SERVER,
        )
        if not await provider.connect():
            logger.error("[STARTUP] Failed to connect to MetaTrader 5")
            return
        logger.info("[STARTUP] MT5 connected")

        # ── Step 4: Agents ─────────────────────────────────────────────
        verbose_mode = settings.DEBUG and settings.ENVIRONMENT != "production"
        workflow = TradingWorkflow(verbose=verbose_mode, mt5_provider=provider)
        cache    = CandleCache()

        # Reconcile open trades from MT5 (crash recovery)
        await workflow.trader_master.reconcile_open_trades()

        logger.info("[STARTUP] Agents ready (Trend / Analyse / Trader)")

        # ── Step 5: Graceful shutdown ──────────────────────────────────
        ev_loop       = asyncio.get_running_loop()
        shutdown_event = asyncio.Event()

        def _request_shutdown(*_):
            logger.info("[MAIN] Shutdown signal received (Ctrl+C)")
            shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                ev_loop.add_signal_handler(sig, _request_shutdown)
            except (NotImplementedError, OSError):
                pass

        # ── Step 6: Trading loop ───────────────────────────────────────
        logger.info(
            "[STARTUP] Starting trading loop (%d min interval)…  Press Ctrl+C to stop",
            TRADING_INTERVAL_SECONDS // 60,
        )

        loop_task = asyncio.create_task(
            trading_loop(provider, workflow, selected_pairs, cache)
        )

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

    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(1)
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
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
        logger.info("[SHUTDOWN] Complete")


if __name__ == "__main__":
    asyncio.run(main())
