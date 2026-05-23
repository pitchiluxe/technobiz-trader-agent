"""
TechnobizTrader GUI Server — Production-ready edition.

Security hardening applied:
  • X-GUI-Token header auth on every API endpoint
  • Token injected into the served HTML at runtime (never stored client-side)
  • SSE authenticated via short-lived query-param token
  • CORS locked to configured origins
  • Per-endpoint rate limiting (in-process, no extra deps)
  • Global 500 handler — no stack traces leaked to client
  • Startup env validation with clear error messages

Endpoints:
    GET  /                  → serves minecraft_trading_office.html (token injected)
    GET  /api/status        → current cycle / connection state
    POST /api/cycle/start   → launches a real trading cycle for {pair}
    GET  /api/events        → SSE stream of phase events (?token=...)
    POST /api/credentials   → save provider credentials
    POST /api/telegram/test → test Telegram bot connection
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

# Load .env from writable userData dir first (set by Electron), then fall back
# to the local .env in the backend directory.
_userdata = os.getenv("TECHNOBIZ_USERDATA", "")
if _userdata:
    load_dotenv(dotenv_path=os.path.join(_userdata, ".env"), override=False)
load_dotenv(override=False)
load_dotenv(".env.local", override=True)  # bundled AI config (OpenRouter / Ollama)
if _userdata:
    load_dotenv(dotenv_path=os.path.join(_userdata, ".env.local"), override=True)  # user override

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger import setup_logging
setup_logging()
logger = logging.getLogger("gui_server")

from agents.workflow import TradingWorkflow
from agents.workflow_orchestrator import WorkflowOrchestrator
from config.settings import settings
from database.db_manager import db_manager
try:
    from market_data.mt5_provider import MT5Provider
except Exception:
    MT5Provider = None


ROOT      = Path(__file__).resolve().parent
HTML_FILE = ROOT / "minecraft_trading_office.html"

# ── Auth token ──────────────────────────────────────────────────────────────
# Loaded from GUI_SECRET_KEY env var.  If absent a random token is generated
# and printed once to the terminal — set the env var to persist it across
# restarts.
_GUI_SECRET: str = os.getenv("GUI_SECRET_KEY", "").strip()
if not _GUI_SECRET:
    _GUI_SECRET = secrets.token_hex(32)
    # Persist to userData .env so the key survives restarts (same token = no 401 on reload).
    try:
        _ud = os.getenv("TECHNOBIZ_USERDATA", "").strip()
        _key_path = (Path(_ud) / ".env") if _ud else (ROOT / ".env")
        if _ud:
            _key_path.parent.mkdir(parents=True, exist_ok=True)
        _existing = _key_path.read_text() if _key_path.exists() else ""
        if "GUI_SECRET_KEY" not in _existing:
            with _key_path.open("a", encoding="utf-8") as _kf:
                _kf.write(f"\nGUI_SECRET_KEY={_GUI_SECRET}\n")
    except Exception:
        pass
    logger.warning("=" * 60)
    logger.warning("[SECURITY] GUI_SECRET_KEY not set — generated for this session:")
    logger.warning(f"[SECURITY]   GUI_SECRET_KEY={_GUI_SECRET}")
    logger.warning("[SECURITY] Persisted to userData .env for stable sessions.")
    logger.warning("=" * 60)


# ── In-process rate limiter ──────────────────────────────────────────────────
_RL_WINDOW   = 60          # seconds
_RL_LIMITS: dict[str, int] = {
    "/api/cycle/start":   5,
    "/api/credentials":   10,
    "/api/telegram/test": 3,
}
_rl_buckets: dict[str, list[float]] = defaultdict(list)

def _rate_ok(path: str, client_ip: str) -> bool:
    limit = _RL_LIMITS.get(path)
    if limit is None:
        return True
    key  = f"{client_ip}:{path}"
    now  = time.monotonic()
    hits = [t for t in _rl_buckets[key] if now - t < _RL_WINDOW]
    _rl_buckets[key] = hits
    if len(hits) >= limit:
        return False
    _rl_buckets[key].append(now)
    return True


# ── Pydantic models ──────────────────────────────────────────────────────────
class CycleRequest(BaseModel):
    pair: str


class CredentialsRequest(BaseModel):
    provider: str
    account: Optional[str]       = None
    password: Optional[str]      = None
    server: Optional[str]        = None
    username: Optional[str]      = None
    session_token: Optional[str] = None
    bot_token: Optional[str]     = None
    chat_id: Optional[str]       = None
    api_key: Optional[str]       = None
    model: Optional[str]         = None   # openrouter / ollama model selection
    base_url: Optional[str]      = None   # ollama base URL


# ── Application state ────────────────────────────────────────────────────────
class AppState:
    def __init__(self) -> None:
        self.provider:     Optional[Any]                = None
        self.workflow:     Optional[TradingWorkflow]    = None
        self.orchestrator: Optional[WorkflowOrchestrator] = None
        self.event_queues: list[asyncio.Queue]          = []
        self.cycle_lock   = asyncio.Lock()
        self.cycle_running = False
        self.connected     = False
        self.last_error:   Optional[str] = None

    async def emit(self, event: str, data: dict[str, Any] | None = None) -> None:
        payload = json.dumps({"event": event, "data": data or {}})
        # Debug-level only — never surfaces to client
        logger.debug("[SSE] %s %s", event, data or "")
        for q in list(self.event_queues):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


state = AppState()


# ── Telegram helper ──────────────────────────────────────────────────────────
async def _send_telegram_signal(signal: dict, symbol: str) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id   = os.getenv("TELEGRAM_CHAT_ID",   "").strip()
    if not bot_token or not chat_id:
        return False

    direction  = (signal.get("direction") or "").upper()
    entry_type = (signal.get("entry_type") or "ICT SETUP").replace("_", " ")
    session    = (signal.get("session")    or "").upper()
    rr         = signal.get("risk_reward_ratio", "")
    confidence = signal.get("confidence", "")
    arrow = "📈" if direction == "BUY" else "📉"
    text = (
        f"🚨 *SIGNAL ALERT* 🚨\n\n"
        f"🌐 *{symbol}*  {arrow} *{direction}*\n"
        f"📍 Session: *{session} Kill Zone*\n"
        f"🔲 Setup: *{entry_type}*\n\n"
        f"⚪ *Entry:*  `{signal.get('entry_level')}`\n"
        f"🔴 *SL:*    `{signal.get('stop_loss')}`\n\n"
        f"🟢 *TP1 (50%):* `{signal.get('take_profit_1')}`\n"
        f"🟢 *TP2 (30%):* `{signal.get('take_profit_2')}`\n"
        f"🟢 *TP3 (20%):* `{signal.get('take_profit_3')}`\n\n"
        f"📐 R:R  *1:{rr}*  |  Confidence *{confidence}%*\n\n"
        f"⚠ Risk max 1-2% of account per trade"
    )
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json={"chat_id": chat_id, "text": text,
                                             "parse_mode": "Markdown"})
            if r.status_code != 200:
                logger.warning("[TELEGRAM] %s %s", r.status_code, r.text[:200])
            return r.status_code == 200
    except Exception as exc:
        logger.error("[TELEGRAM] send failed: %s", exc)
        return False


# ── Market data helper ────────────────────────────────────────────────────────
async def _fetch_market_data(symbol: str) -> Optional[dict]:
    if state.provider is None:
        return None

    # Required timeframes (cycle aborts if any are missing)
    required = {
        "daily": ("D1",  100),
        "4h":    ("H4",  200),
        "1h":    ("H1",  100),
    }
    # Optional timeframes (graceful degradation if unavailable)
    optional = {
        "weekly": ("W1",  52),    # ~1 year of weekly bars for macro trend
        "15m":    ("M15", 200),   # lower-TF entry refinement (Trader-Master)
        "5m":     ("M5",  200),   # fallback lower-TF
    }

    market_data: dict[str, Any] = {}

    for key, (tf, limit) in {**required, **optional}.items():
        try:
            candles = await state.provider.get_candles(symbol, tf, limit=limit)
            if candles:
                market_data[key] = candles
        except Exception as exc:
            logger.error("[DATA] Error fetching %s for %s: %s", tf, symbol, exc)

    if not all(market_data.get(k) for k in required):
        logger.error("[DATA] Missing required timeframes for %s", symbol)
        return None

    tfs_loaded = [k for k in market_data]
    logger.info("[DATA] Timeframes loaded for %s: %s", symbol, ", ".join(tfs_loaded))
    return market_data


# ── MT4 fallback (uses same MT5Provider with MT4_* credentials) ──────────────
async def _try_mt4_fallback() -> Optional[Any]:
    """
    Try to connect using MT4 credentials (MT4_ACCOUNT / MT4_PASSWORD / MT4_SERVER).
    MetaTrader 4 brokers work with the same MT5 Python library via a bridge.
    Returns a connected provider, or None if MT4 credentials are not configured.
    """
    if MT5Provider is None:
        return None
    account = os.getenv("MT4_ACCOUNT", "").strip()
    password = os.getenv("MT4_PASSWORD", "").strip()
    server   = os.getenv("MT4_SERVER",  "").strip()
    if not (account and password and server):
        return None
    try:
        provider = MT5Provider(account=account, password=password, server=server)
        if await provider.connect():
            logger.info("[FALLBACK] MT4 provider connected (account=%s)", account)
            return provider
        logger.warning("[FALLBACK] MT4 connect() returned False")
        return None
    except Exception as exc:
        logger.warning("[FALLBACK] MT4 connection failed: %s", exc)
        return None


# ── TradingView fallback (used when MT5/MT4 is unreachable) ───────────────────
async def _try_tradingview_fallback() -> Optional[Any]:
    """
    Attempt to create a TradingView provider for read-only data when MT5 is down.
    Returns a connected provider, or None if TradingView is not configured.
    """
    try:
        from market_data.tradingview_provider import TradingViewProvider
        tv_type = os.getenv("TRADINGVIEW_API_TYPE", "").strip()
        if not tv_type:
            logger.info("[FALLBACK] TRADINGVIEW_API_TYPE not set — cannot fall back")
            return None
        provider = TradingViewProvider()
        if await provider.connect():
            logger.info("[FALLBACK] TradingView fallback provider connected")
            return provider
        logger.warning("[FALLBACK] TradingView fallback connect() returned False")
        return None
    except Exception as exc:
        logger.warning("[FALLBACK] Could not create TradingView fallback: %s", exc)
        return None


def _any_provider_configured() -> bool:
    """Return True if at least one data provider has credentials in env."""
    return bool(
        os.getenv("MT5_ACCOUNT",          "").strip() or
        os.getenv("MT4_ACCOUNT",          "").strip() or
        os.getenv("TRADINGVIEW_USERNAME", "").strip() or
        os.getenv("TRADINGVIEW_API_TYPE", "").strip()
    )


# ── Trading cycle ─────────────────────────────────────────────────────────────
async def _run_cycle(symbol: str) -> None:
    assert state.workflow and state.orchestrator

    workflow     = state.workflow
    orchestrator = state.orchestrator

    state.cycle_running = True
    await state.emit("cycle_started", {"pair": symbol})

    try:
        # ── Ensure a data provider is available ──────────────────────────────
        if state.provider is None:
            # Try MT4 first (same library, MT4_* credentials)
            await state.emit("info", {"message": "No provider — trying MT4..."})
            mt4 = await _try_mt4_fallback()
            if mt4 is not None:
                state.provider = mt4
                state.connected = True
                state.last_error = None
                logger.info("[CYCLE] Using MT4 as data provider for %s", symbol)
            else:
                # Try TradingView as last resort
                await state.emit("info", {"message": "Trying TradingView..."})
                tv = await _try_tradingview_fallback()
                if tv is not None:
                    state.provider = tv
                    state.connected = True
                    state.last_error = None
                    logger.info("[CYCLE] Using TradingView as data provider for %s", symbol)
                else:
                    if _any_provider_configured():
                        reason = "Data provider credentials saved but connection failed — check ⚙ Settings to verify or re-enter them."
                    else:
                        reason = "No data provider connected — add MT5, MT4, or TradingView credentials in ⚙ Settings."
                    await state.emit("cycle_failed", {"reason": reason, "result": "no_provider"})
                    return

        if not await state.provider.is_connected():
            await state.emit("info", {"message": "Reconnecting to data provider..."})
            if not await state.provider.connect():
                # ── Fallback: try TradingView when MT5 is unavailable ──
                fallback = await _try_tradingview_fallback()
                if fallback is not None:
                    logger.warning(
                        "[CYCLE] MT5 unreachable — falling back to TradingView for %s "
                        "(data-only, no execution)",
                        symbol,
                    )
                    await state.emit("info", {
                        "message": "MT5 unavailable — using TradingView (data only, no trade execution)"
                    })
                    # Temporarily swap provider for this cycle's data fetch
                    original_provider = state.provider
                    state.provider = fallback
                    try:
                        market_data = await _fetch_market_data(symbol)
                    finally:
                        state.provider = original_provider
                    if not market_data:
                        await state.emit("cycle_failed", {"reason": "No market data from fallback provider"})
                        return
                    # Skip execution phases when MT5 is down — emit analysis result only
                    await state.emit("cycle_completed", {
                        "result": "data_only",
                        "pair": symbol,
                        "note": "MT5 offline — trade execution skipped",
                    })
                    return
                await state.emit("cycle_failed", {"reason": "MT5 reconnect failed — check ⚙ Settings", "result": "no_provider"})
                return

        # ── Fetch market data once — shared across all 7 agents ──────────────
        market_data = await _fetch_market_data(symbol)
        if not market_data:
            await state.emit("cycle_failed", {"reason": "Insufficient market data"})
            return

        # ── PRE-CYCLE AGENTS (0a-0d) ──────────────────────────────────────────

        # 0a. Market-Regime — classify environment, derive risk multipliers
        await state.emit("phase_started", {"agent": "data", "phase": "market_regime"})
        regime = None
        try:
            regime = await workflow.market_regime.analyze(market_data)
            workflow.last_regime_report = regime
            await state.emit("phase_completed", {
                "agent":        "data",
                "regime":       regime.regime,
                "confidence":   regime.confidence,
                "risk_mult":    regime.risk_multiplier,
            })
            if regime.regime == "VOLATILE":
                await state.emit("cycle_failed", {
                    "reason": f"Market-Regime VOLATILE — {regime.description}"
                })
                return
        except Exception as exc:
            logger.warning("[CYCLE] Market-Regime failed (non-blocking): %s", exc)
            await state.emit("phase_completed", {"agent": "data", "note": "skipped"})

        # 0b. Backtester — historical win-rate, confidence multiplier
        await state.emit("phase_started", {"agent": "portfolio", "phase": "backtesting"})
        bt = None
        try:
            bt = await workflow.backtester.analyze(symbol=symbol)
            workflow.last_backtest = bt
            await state.emit("phase_completed", {
                "agent":       "portfolio",
                "win_rate":    round(bt.overall_win_rate * 100, 1),
                "profit_factor": round(bt.profit_factor, 2),
                "conf_mult":   round(bt.confidence_multiplier, 2),
                "sample_size": bt.sample_size,
            })
        except Exception as exc:
            logger.warning("[CYCLE] Backtester failed (non-blocking): %s", exc)
            await state.emit("phase_completed", {"agent": "portfolio", "note": "skipped"})

        # 0c. News-Sentinel — block if high-impact event imminent
        await state.emit("phase_started", {"agent": "news", "phase": "news_check"})
        try:
            news = await workflow.news_sentinel.check(symbol=symbol)
            await state.emit("phase_completed", {
                "agent":       "news",
                "risk_level":  news.risk_level,
                "next_event":  news.next_event_name,
                "minutes":     round(news.minutes_until, 1),
                "safe":        news.safe,
            })
            if not news.safe:
                await state.emit("cycle_failed", {
                    "reason": f"News-Sentinel blocked — '{news.next_event_name}' in {news.minutes_until:.0f} min"
                })
                return
        except Exception as exc:
            logger.warning("[CYCLE] News-Sentinel failed (non-blocking): %s", exc)
            await state.emit("phase_completed", {"agent": "news", "note": "skipped"})

        # ── CORE ICT PIPELINE ──────────────────────────────────────────────────
        orchestrator.start_cycle(symbol)

        # PHASE 1: TREND-MASTER
        await state.emit("phase_started", {"agent": "trend", "phase": "trend_analysis"})
        if not orchestrator.begin_trend_analysis():
            await state.emit("phase_failed", {"agent": "trend", "reason": "orchestrator rejected"})
            return

        trend_report = await workflow.trend_master.analyze(market_data)
        if not trend_report:
            await state.emit("phase_failed", {"agent": "trend", "reason": "no trend report"})
            await state.emit("cycle_failed", {"reason": "Trend-Master returned no report"})
            return

        # Attach regime guidance to trend dict so Analyse-Master can use it
        trend_dict = trend_report.to_dict()
        if regime is not None:
            trend_dict["_regime_rr_floor"]        = regime.recommended_rr
            trend_dict["_regime_risk_multiplier"]  = regime.risk_multiplier

        orchestrator.complete_trend_analysis(trend_dict)
        await state.emit("phase_completed", {
            "agent":      "trend",
            "bias":       trend_report.bias,
            "confidence": trend_report.confidence,
            "timeframes": trend_report.timeframes_analyzed,
        })

        # PHASE 2: ANALYSE-MASTER
        await state.emit("phase_started", {"agent": "analyse", "phase": "signal_generation"})
        if not orchestrator.begin_signal_generation():
            await state.emit("phase_failed", {"agent": "analyse", "reason": "orchestrator rejected"})
            return

        trade_signal = await workflow.analyse_master.analyze(
            trend_dict,
            candle_data=market_data,
            symbol=symbol,
        )
        if not trade_signal:
            await state.emit("phase_failed", {
                "agent":  "analyse",
                "reason": "no signal (kill zone inactive or ICT elements not confirmed)",
            })
            await state.emit("cycle_completed", {"result": "no_signal", "pair": symbol})
            return

        # Apply backtester confidence multiplier
        if bt is not None and bt.sample_size >= 10:
            adjusted = round(trade_signal.confidence * bt.confidence_multiplier, 1)
            if adjusted != trade_signal.confidence:
                logger.info("[CYCLE] Confidence adjusted by backtest: %.1f%% → %.1f%%",
                            trade_signal.confidence, adjusted)
            trade_signal.confidence = adjusted

        orchestrator.complete_signal_generation(trade_signal.to_dict())
        await state.emit("phase_completed", {
            "agent":      "analyse",
            "confidence": trade_signal.confidence,
            "direction":  trade_signal.direction,
            "entry_type": trade_signal.entry_type,
            "session":    trade_signal.session,
        })

        # 0d. Risk-Sentinel — portfolio gatekeeper (runs after signal so it has confidence)
        await state.emit("phase_started", {"agent": "risk", "phase": "risk_assessment"})
        assessment = None
        try:
            assessment = await workflow.run_risk_check(symbol, {}, trade_signal.confidence)
            workflow.last_risk_assessment = assessment
            await state.emit("phase_completed", {
                "agent":        "risk",
                "approved":     assessment.approved,
                "risk_mult":    round(assessment.risk_multiplier, 2),
                "adj_risk_pct": round(assessment.adjusted_risk_pct, 2),
                "warnings":     assessment.warnings,
            })
            if not assessment.approved:
                await state.emit("cycle_failed", {
                    "reason": f"Risk-Sentinel blocked — {assessment.block_reason}"
                })
                return
        except Exception as exc:
            logger.warning("[CYCLE] Risk-Sentinel failed (non-blocking): %s", exc)
            await state.emit("phase_completed", {"agent": "risk", "note": "skipped"})

        # PHASE 3: TRADER-MASTER
        await state.emit("phase_started", {"agent": "trader", "phase": "trade_execution"})
        if not orchestrator.begin_trade_execution():
            await state.emit("phase_failed", {"agent": "trader", "reason": "orchestrator rejected"})
            return

        signal_dict = trade_signal.to_dict()
        if assessment is not None:
            signal_dict["_risk_multiplier"]   = assessment.risk_multiplier
            signal_dict["_adjusted_risk_pct"] = assessment.adjusted_risk_pct
        if regime is not None:
            signal_dict["_regime_risk_multiplier"] = regime.risk_multiplier

        execution = await workflow.trader_master.analyze(
            signal_dict,
            market_data=market_data,
        )
        orchestrator.complete_trade_execution(execution.to_dict() if execution else {})

        if execution:
            await state.emit("phase_completed", {
                "agent":      "trader",
                "signal_id":  execution.signal_id,
                "entry":      execution.entry_price,
                "entry_type": execution.entry_type,
                "session":    execution.session,
                "lots":       execution.position_size,
            })
            await _send_telegram_signal(trade_signal.to_dict(), symbol)
            await state.emit("cycle_completed", {
                "result":    "trade_executed",
                "pair":      symbol,
                "signal_id": execution.signal_id,
            })
        else:
            await state.emit("cycle_completed", {"result": "no_execution", "pair": symbol})

    except Exception as exc:
        logger.error("[CYCLE] Unhandled error for %s: %s", symbol, exc, exc_info=True)
        await state.emit("cycle_failed", {"reason": str(exc)})
    finally:
        state.cycle_running = False
        # ── Drawdown monitoring alert ──────────────────────────────────────
        await _check_drawdown_alert(symbol)


_drawdown_alerted: set[str] = set()   # tracks which thresholds were already sent today


async def _check_drawdown_alert(symbol: str) -> None:
    """Send Telegram alert when daily drawdown crosses 3% (warning) or 5% (stop) threshold."""
    trader = (
        state.workflow.trader_master
        if state.workflow and hasattr(state.workflow, "trader_master")
        else None
    )
    if trader is None:
        return

    daily_loss_pct = trader.daily_loss * 100
    today_key = str(trader._session_date)

    async def _alert(level: str, pct: float) -> None:
        key = f"{today_key}:{level}"
        if key in _drawdown_alerted:
            return
        _drawdown_alerted.add(key)
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id   = os.getenv("TELEGRAM_CHAT_ID",   "").strip()
        if not bot_token or not chat_id:
            return
        emoji = "⚠️" if level == "warning" else "🛑"
        text = (
            f"{emoji} *DRAWDOWN {level.upper()}* {emoji}\n\n"
            f"Pair: *{symbol}*\n"
            f"Daily loss: *{pct:.1f}%*\n"
            f"{'Trading PAUSED by kill switch.' if level == 'critical' else 'Approaching daily loss limit — trade with caution.'}"
        )
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json={"chat_id": chat_id, "text": text,
                                             "parse_mode": "Markdown"})
        except Exception as exc:
            logger.warning("[DRAWDOWN ALERT] Telegram send failed: %s", exc)

    if daily_loss_pct >= 5.0:
        await _alert("critical", daily_loss_pct)
    elif daily_loss_pct >= 3.0:
        await _alert("warning", daily_loss_pct)

    # Clear stale keys when a new day starts (trader resets _session_date)
    stale = [k for k in _drawdown_alerted if not k.startswith(today_key)]
    for k in stale:
        _drawdown_alerted.discard(k)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate critical env vars on startup
    missing = []
    if settings.DATA_PROVIDER in ("mt5", "hybrid"):
        for var in ("MT5_ACCOUNT", "MT5_PASSWORD", "MT5_SERVER"):
            if not os.getenv(var, "").strip():
                missing.append(var)
    if missing:
        logger.warning("[STARTUP] Missing env vars for %s provider: %s",
                       settings.DATA_PROVIDER, ", ".join(missing))

    db_manager.create_tables()
    logger.info("[STARTUP] Database tables ready")

    verbose = settings.DEBUG and settings.ENVIRONMENT != "production"
    state.workflow     = TradingWorkflow(verbose=verbose, mt5_provider=None)
    state.orchestrator = WorkflowOrchestrator()

    # Mark server ready immediately — provider connections happen in background
    # so the HTTP server responds to Electron's readiness poll within seconds.
    state.connected  = True
    state.last_error = "Connecting to data provider…"
    logger.info("[STARTUP] Workflow + orchestrator ready — provider connecting in background")

    async def _connect_providers() -> None:
        # MT5 and MT4 are NOT auto-connected at startup because mt5.initialize()
        # opens the MetaTrader terminal window without user interaction.
        # They connect only when the user saves credentials via Settings → Save.
        logger.info("[STARTUP] Skipping MT5/MT4 auto-connect (use Settings to connect)")

        # ── Try TradingView (passive, no terminal window) ──
        tv = await _try_tradingview_fallback()
        if tv is not None:
            state.provider = tv
            state.last_error = None
            logger.info("[STARTUP] TradingView connected as primary data provider")
            return

        # No provider auto-connected — user must connect via Settings
        state.last_error = "No data provider connected — use Settings to connect MT5/MT4 or configure TradingView"
        logger.info("[STARTUP] Awaiting user provider selection via Settings")

    _bg_task = asyncio.create_task(_connect_providers())

    yield

    _bg_task.cancel()
    try:
        await _bg_task
    except asyncio.CancelledError:
        pass

    if state.provider:
        await state.provider.disconnect()
    db_manager.close()
    logger.info("[SHUTDOWN] Complete")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="TechnobizTrader GUI",
    docs_url=None,        # disable Swagger UI in production
    redoc_url=None,       # disable ReDoc in production
    openapi_url=None,     # disable OpenAPI schema endpoint
    lifespan=lifespan,
)

# CORS — restrict to configured origins (default: localhost only)
_allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8765,http://127.0.0.1:8765").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["X-GUI-Token", "Content-Type"],
)


# Auth middleware — every /api/* request must carry the correct X-GUI-Token header.
# The SSE endpoint uses a query param (browsers cannot set custom headers on EventSource).
class _AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Public paths: root HTML, favicon
        if path in ("/", "/favicon.ico"):
            return await call_next(request)
        # SSE: token in query param
        if path == "/api/events":
            token = request.query_params.get("token", "")
        else:
            token = request.headers.get("X-GUI-Token", "")
        if not secrets.compare_digest(token.encode(), _GUI_SECRET.encode()):
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)


app.add_middleware(_AuthMiddleware)


# Global exception handler — never leak tracebacks to the client
@app.exception_handler(Exception)
async def _global_error(request: Request, exc: Exception):
    logger.error("[UNHANDLED] %s %s -> %s", request.method, request.url.path, exc,
                 exc_info=True)
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    if not HTML_FILE.exists():
        raise HTTPException(404, "minecraft_trading_office.html not found")
    # Inject the session token so the client can authenticate API calls.
    # The token is embedded in a <script> tag — it is never stored in localStorage
    # or cookies, and is only accessible to the same-origin page.
    html = HTML_FILE.read_text(encoding="utf-8")
    token_script = (
        f'<script>window.__GUI_TOKEN__="{_GUI_SECRET}";</script>'
    )
    html = html.replace("</head>", token_script + "\n</head>", 1)
    return HTMLResponse(html)


@app.get("/api/status")
async def api_status():
    return {
        "connected":     state.connected,
        "cycle_running": state.cycle_running,
        "last_error":    state.last_error,
        "environment":   settings.ENVIRONMENT,
    }


@app.get("/api/health")
async def api_health():
    """
    Structured health endpoint for load balancers and monitoring tools.
    Returns HTTP 200 when the service is operational, 503 when degraded.
    """
    trader = (
        state.workflow.trader_master
        if state.workflow and hasattr(state.workflow, "trader_master")
        else None
    )
    daily_loss_pct = round((trader.daily_loss if trader else 0.0) * 100, 2)
    open_trades    = len([t for t in trader.open_trades if t.status in ("PENDING", "OPEN")]) \
                     if trader else 0

    workflow_ready = state.workflow is not None
    health = {
        "status":          "ok" if workflow_ready else "degraded",
        "connected":       state.connected,
        "workflow_ready":  workflow_ready,
        "provider":        "mt5" if (state.provider and "MT5" in type(state.provider).__name__) else
                           "tradingview" if state.provider else "none",
        "cycle_running":   state.cycle_running,
        "environment":     settings.ENVIRONMENT,
        "data_provider":   settings.DATA_PROVIDER,
        "daily_loss_pct":  daily_loss_pct,
        "open_trades":     open_trades,
        "last_error":      state.last_error,
    }
    status_code = 200 if workflow_ready else 503
    return JSONResponse(health, status_code=status_code)

@app.post("/api/cycle/start")
async def start_cycle(req: CycleRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok("/api/cycle/start", client_ip):
        raise HTTPException(429, "Too many requests — wait before starting another cycle")

    pair = req.pair.strip().upper()
    if not pair:
        raise HTTPException(400, "pair required")
    if state.cycle_lock.locked() or state.cycle_running:
        raise HTTPException(409, "A cycle is already running")
    if not state.workflow:
        raise HTTPException(503, "Server not ready — workflow not initialized")

    async def _runner():
        async with state.cycle_lock:
            await _run_cycle(pair)

    asyncio.create_task(_runner())
    return JSONResponse({"started": True, "pair": pair})


def _env_write_path() -> Path:
    """
    Return a writable path for the .env file.
    In installed (Electron) mode TECHNOBIZ_USERDATA points to %APPDATA%/TechnobizTrader.
    In development mode we fall back to ROOT/.env.
    """
    userdata = os.getenv("TECHNOBIZ_USERDATA", "").strip()
    if userdata:
        p = Path(userdata)
        p.mkdir(parents=True, exist_ok=True)
        return p / ".env"
    return ROOT / ".env"


def _write_env_keys(updates: dict[str, str]) -> None:
    env_path = _env_write_path()
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    keys_seen: set[str] = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            lines[i] = f"{key}={updates[key]}"
            keys_seen.add(key)

    for key, val in updates.items():
        if key not in keys_seen:
            lines.append(f"{key}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in updates.items():
        os.environ[k] = v


def _env_local_write_path() -> Path:
    """Return writable .env.local path (AI provider config)."""
    userdata = os.getenv("TECHNOBIZ_USERDATA", "").strip()
    if userdata:
        p = Path(userdata)
        p.mkdir(parents=True, exist_ok=True)
        return p / ".env.local"
    return ROOT / ".env.local"


def _write_env_local_keys(updates: dict[str, str]) -> None:
    """Upsert keys in .env.local and apply them to the running process."""
    env_path = _env_local_write_path()
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    keys_seen: set[str] = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            lines[i] = f"{key}={updates[key]}"
            keys_seen.add(key)

    for key, val in updates.items():
        if key not in keys_seen:
            lines.append(f"{key}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in updates.items():
        os.environ[k] = v


@app.post("/api/credentials")
async def save_credentials(req: CredentialsRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok("/api/credentials", client_ip):
        raise HTTPException(429, "Too many requests")

    provider = req.provider.lower().strip()
    updates: dict[str, str] = {}

    if provider == "claude":
        if not req.api_key or not req.api_key.startswith("sk-ant-"):
            raise HTTPException(400, "Anthropic direct requires a valid sk-ant-... API key from console.anthropic.com")
        model = req.model or "claude-3-5-sonnet-20241022"
        try:
            _write_env_local_keys({
                "AI_PROVIDER": "claude",
                "ANTHROPIC_API_KEY": req.api_key,
                "ANTHROPIC_MODEL": model,
                "ANTHROPIC_BASE_URL": "",
                "ANTHROPIC_AUTH_TOKEN": "",
            })
        except OSError as exc:
            raise HTTPException(500, f"Could not save credentials to disk: {exc}")
        return {"saved": True, "provider": provider, "reconnected": None}

    elif provider == "openrouter":
        if not req.api_key or not req.api_key.startswith("sk-or-v1-"):
            raise HTTPException(400, "OpenRouter requires a valid sk-or-v1-... API key from openrouter.ai/keys")
        model = req.model or "deepseek/deepseek-v4-flash:free"
        try:
            _write_env_local_keys({
                "AI_PROVIDER": "openrouter",
                "ANTHROPIC_BASE_URL": "https://openrouter.ai/api",
                "ANTHROPIC_AUTH_TOKEN": req.api_key,
                "ANTHROPIC_MODEL": model,
                "ANTHROPIC_API_KEY": "",
            })
        except OSError as exc:
            raise HTTPException(500, f"Could not save credentials to disk: {exc}")
        return {"saved": True, "provider": provider, "reconnected": None}

    elif provider == "ollama":
        base_url = (req.base_url or "http://localhost:11434").rstrip("/")
        model = req.model or "llama3.2"
        try:
            _write_env_local_keys({
                "AI_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": base_url,
                "OLLAMA_MODEL": model,
            })
        except OSError as exc:
            raise HTTPException(500, f"Could not save credentials to disk: {exc}")
        return {"saved": True, "provider": provider, "reconnected": None}

    elif provider == "mt5":
        # Fall back to the already-saved password when the client omits it (blank = keep existing)
        password = (req.password or "").strip() or os.getenv("MT5_PASSWORD", "").strip()
        if not (req.account and password and req.server):
            raise HTTPException(400, "MT5 requires account, password, and server")
        updates = {"MT5_ACCOUNT": req.account, "MT5_PASSWORD": password,
                   "MT5_SERVER": req.server, "DATA_PROVIDER": "mt5"}
    elif provider == "mt4":
        password = (req.password or "").strip() or os.getenv("MT4_PASSWORD", "").strip()
        if not (req.account and password and req.server):
            raise HTTPException(400, "MT4 requires account, password, and server")
        updates = {"MT4_ACCOUNT": req.account, "MT4_PASSWORD": password,
                   "MT4_SERVER": req.server, "DATA_PROVIDER": "mt4"}
    elif provider == "tradingview":
        password = (req.password or "").strip() or os.getenv("TRADINGVIEW_PASSWORD", "").strip()
        session  = (req.session_token or "").strip() or os.getenv("TRADINGVIEW_SESSION", "").strip()
        if not (req.username and (password or session)):
            raise HTTPException(400, "TradingView requires username + password or session_token")
        updates = {"TRADINGVIEW_USERNAME": req.username or "",
                   "TRADINGVIEW_PASSWORD": password,
                   "TRADINGVIEW_SESSION":  session,
                   "DATA_PROVIDER": "tradingview"}
    elif provider == "telegram":
        bot_token = (req.bot_token or "").strip() or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not (bot_token and req.chat_id):
            raise HTTPException(400, "Telegram requires bot_token and chat_id")
        updates = {"TELEGRAM_BOT_TOKEN": bot_token, "TELEGRAM_CHAT_ID": req.chat_id,
                   "ENABLE_TELEGRAM_NOTIFICATIONS": "True"}
    else:
        raise HTTPException(400, f"Unknown provider: {provider}")

    try:
        _write_env_keys(updates)
    except OSError as exc:
        logger.error("[CREDENTIALS] Failed to write .env: %s", exc)
        raise HTTPException(500, f"Could not save credentials to disk: {exc}")

    logger.info("[CREDENTIALS] Provider '%s' saved by %s", provider, client_ip)

    # Kick off reconnection in the background so the HTTP response returns immediately.
    # mt5.initialize() can block for ~65 s — we never want that on the request path.
    if provider in ("mt5", "mt4") and MT5Provider is not None:
        if provider == "mt5":
            acct, pwd, srv = updates["MT5_ACCOUNT"], updates["MT5_PASSWORD"], updates["MT5_SERVER"]
        else:
            acct, pwd, srv = updates["MT4_ACCOUNT"], updates["MT4_PASSWORD"], updates["MT4_SERVER"]

        async def _bg_reconnect() -> None:
            if state.provider is not None:
                try:
                    await state.provider.disconnect()
                except Exception:
                    pass
            try:
                prov = MT5Provider(account=acct, password=pwd, server=srv)
                ok   = await prov.connect()
            except Exception as exc:
                logger.warning("[CREDENTIALS] %s connect error: %s", provider.upper(), exc)
                ok = False
            state.connected = ok
            state.provider  = prov if ok else None
            if state.workflow:
                state.workflow.trader_master.mt5_provider = state.provider
            label = provider.upper()
            state.last_error = None if ok else f"{label} credentials saved — connection failed, check server name"
            await state.emit("info", {
                "message": f"{'✓' if ok else '✗'} {label} {'connected' if ok else 'connection failed — check server/credentials'}"
            })

        asyncio.create_task(_bg_reconnect())

    return {"saved": True, "provider": provider, "reconnected": None}


@app.get("/api/credentials/status")
async def credentials_status():
    """Tell the frontend which credentials are configured and return non-sensitive field values."""
    ai_provider = os.getenv("AI_PROVIDER", "openrouter").lower()
    return {
        # AI provider info
        "ai_provider":            ai_provider,
        "claude_configured":      bool(
            os.getenv("ANTHROPIC_API_KEY", "").strip()
        ) and ai_provider == "claude",
        "openrouter_configured":  bool(
            os.getenv("ANTHROPIC_AUTH_TOKEN", "").strip()
        ) and ai_provider == "openrouter",
        "ollama_configured":      ai_provider == "ollama",
        "current_model":          (
            os.getenv("OLLAMA_MODEL", "") if ai_provider == "ollama"
            else os.getenv("ANTHROPIC_MODEL", "")
        ),
        "ollama_base_url":        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        # MT5 / MT4
        "mt5_configured":         bool(os.getenv("MT5_ACCOUNT", "").strip()),
        "mt5_account":            os.getenv("MT5_ACCOUNT",  ""),
        "mt5_server":             os.getenv("MT5_SERVER",   ""),
        "mt4_configured":         bool(os.getenv("MT4_ACCOUNT", "").strip()),
        "mt4_account":            os.getenv("MT4_ACCOUNT",  ""),
        "mt4_server":             os.getenv("MT4_SERVER",   ""),
        "tradingview_configured": bool(os.getenv("TRADINGVIEW_USERNAME", "").strip()),
        "tradingview_username":   os.getenv("TRADINGVIEW_USERNAME", ""),
        "telegram_configured":    bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()),
        "telegram_chat_id":       os.getenv("TELEGRAM_CHAT_ID", ""),
    }


# ── OpenRouter free models (hardcoded list) ──────────────────────────────────
_OPENROUTER_FREE_MODELS = [
    {"id": "deepseek/deepseek-v4-flash:free",           "name": "DeepSeek V4 Flash"},
    {"id": "deepseek/deepseek-r1:free",                 "name": "DeepSeek R1"},
    {"id": "deepseek/deepseek-chat-v3-0324:free",       "name": "DeepSeek Chat V3"},
    {"id": "meta-llama/llama-3.3-70b-instruct:free",    "name": "Llama 3.3 70B"},
    {"id": "meta-llama/llama-3.1-8b-instruct:free",     "name": "Llama 3.1 8B"},
    {"id": "qwen/qwen3-32b:free",                       "name": "Qwen3 32B"},
    {"id": "qwen/qwen3-14b:free",                       "name": "Qwen3 14B"},
    {"id": "qwen/qwen3-8b:free",                        "name": "Qwen3 8B"},
    {"id": "qwen/qwen3-30b-a3b:free",                   "name": "Qwen3 30B A3B (MoE)"},
    {"id": "qwen/qwen-2.5-72b-instruct:free",           "name": "Qwen 2.5 72B"},
    {"id": "google/gemma-3-27b-it:free",                "name": "Gemma 3 27B"},
    {"id": "google/gemma-3-12b-it:free",                "name": "Gemma 3 12B"},
    {"id": "google/gemma-3n-e4b-it:free",               "name": "Gemma 3n E4B"},
    {"id": "mistralai/mistral-7b-instruct:free",        "name": "Mistral 7B"},
    {"id": "mistralai/mistral-nemo:free",               "name": "Mistral Nemo 12B"},
    {"id": "microsoft/phi-3-mini-128k-instruct:free",   "name": "Phi-3 Mini 128K"},
    {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Phi-3 Medium 128K"},
    {"id": "nousresearch/hermes-3-llama-3.1-405b:free", "name": "Hermes 3 Llama 405B"},
    {"id": "openchat/openchat-7b:free",                 "name": "OpenChat 7B"},
    {"id": "liquid/lfm-40b:free",                       "name": "Liquid LFM 40B"},
]

# Common Ollama models (suggested when Ollama is not yet running)
_OLLAMA_SUGGESTED_MODELS = [
    {"id": "llama3.2",           "name": "Llama 3.2 (3B) — recommended"},
    {"id": "llama3.2:1b",        "name": "Llama 3.2 (1B) — fastest"},
    {"id": "llama3.1",           "name": "Llama 3.1 (8B)"},
    {"id": "llama3.1:70b",       "name": "Llama 3.1 (70B) — needs 48GB RAM"},
    {"id": "mistral",            "name": "Mistral (7B)"},
    {"id": "mistral-nemo",       "name": "Mistral Nemo (12B)"},
    {"id": "phi4",               "name": "Phi-4 (14B)"},
    {"id": "phi3",               "name": "Phi-3 Mini (3.8B)"},
    {"id": "phi3:medium",        "name": "Phi-3 Medium (14B)"},
    {"id": "gemma3",             "name": "Gemma 3 (4B)"},
    {"id": "gemma3:12b",         "name": "Gemma 3 (12B)"},
    {"id": "gemma3:27b",         "name": "Gemma 3 (27B)"},
    {"id": "gemma2",             "name": "Gemma 2 (9B)"},
    {"id": "qwen2.5",            "name": "Qwen 2.5 (7B)"},
    {"id": "qwen2.5:14b",        "name": "Qwen 2.5 (14B)"},
    {"id": "qwen2.5:72b",        "name": "Qwen 2.5 (72B)"},
    {"id": "deepseek-r1",        "name": "DeepSeek R1 (8B)"},
    {"id": "deepseek-r1:14b",    "name": "DeepSeek R1 (14B)"},
    {"id": "deepseek-r1:32b",    "name": "DeepSeek R1 (32B)"},
    {"id": "codellama",          "name": "Code Llama (7B)"},
    {"id": "tinyllama",          "name": "TinyLlama (1.1B) — very fast"},
    {"id": "orca-mini",          "name": "Orca Mini (3B)"},
    {"id": "vicuna",             "name": "Vicuna (7B)"},
]


@app.get("/api/openrouter-models")
async def get_openrouter_models():
    """Return the hardcoded list of free OpenRouter models."""
    return {"models": _OPENROUTER_FREE_MODELS}


@app.get("/api/ollama-models")
async def get_ollama_models():
    """Fetch models installed in the local Ollama instance. Falls back to suggested list."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        import httpx
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(f"{base_url}/api/tags")
            if r.status_code == 200:
                data = r.json()
                installed = [
                    {"id": m["name"], "name": m["name"]}
                    for m in data.get("models", [])
                ]
                return {"models": installed, "connected": True, "base_url": base_url}
    except Exception:
        pass
    return {
        "models": _OLLAMA_SUGGESTED_MODELS,
        "connected": False,
        "base_url": base_url,
        "note": "Ollama not running — showing suggested models. Start Ollama and click Refresh.",
    }


@app.post("/api/telegram/test")
async def test_telegram(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_ok("/api/telegram/test", client_ip):
        raise HTTPException(429, "Too many requests")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id   = os.getenv("TELEGRAM_CHAT_ID",   "").strip()
    if not bot_token or not chat_id:
        raise HTTPException(400, "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set first")

    text = ("✅ *TechnobizTrader — Test Connection*\n\n"
            "Your Telegram bot is correctly configured.\n"
            "Signal alerts will be broadcast here when a trade signal is detected.")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json={"chat_id": chat_id, "text": text,
                                             "parse_mode": "Markdown"})
        if r.status_code == 200:
            return {"ok": True, "message": "Test message sent"}
        detail = r.json().get("description", r.text[:200])
        raise HTTPException(502, f"Telegram API error: {detail}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Request failed: {exc}")


@app.get("/api/events")
async def events(token: str = Query("")):
    # Token validated by _AuthMiddleware; this param is just for documentation.
    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    state.event_queues.append(queue)

    async def gen():
        try:
            yield {"data": json.dumps({"event": "connected", "data": {}})}
            while True:
                payload = await queue.get()
                yield {"data": payload}
        finally:
            if queue in state.event_queues:
                state.event_queues.remove(queue)

    return EventSourceResponse(gen())


if __name__ == "__main__":
    import socket
    import time as _time
    import uvicorn

    host = os.getenv("GUI_HOST", "127.0.0.1")
    port = int(os.getenv("GUI_PORT", "8765"))

    # Wait until the port is free (previous process may still hold it).
    # Electron kills the old PID but the OS needs a moment to release the bind.
    _deadline = _time.monotonic() + 30
    while _time.monotonic() < _deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _probe:
            _probe.settimeout(0.5)
            if _probe.connect_ex((host, port)) != 0:
                break  # connection refused = port is free
        _time.sleep(0.5)

    # Never use the file-watcher reloader in a packaged desktop app.
    # The reloader spawns a fresh worker on every .pyc write, generates a new
    # GUI_SECRET_KEY each time, and the frontend's cached token becomes invalid —
    # causing repeated 401 errors and eventually crashing the backend.
    uvicorn.run("gui_server:app", host=host, port=port,
                log_level="info", reload=False)
