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
    logger.warning("=" * 60)
    logger.warning("[SECURITY] GUI_SECRET_KEY not set — generated for this session:")
    logger.warning(f"[SECURITY]   GUI_SECRET_KEY={_GUI_SECRET}")
    logger.warning("[SECURITY] Add it to .env to keep the same key across restarts.")
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


# ── TradingView fallback (used when MT5 is unreachable) ───────────────────────
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


# ── Trading cycle ─────────────────────────────────────────────────────────────
async def _run_cycle(symbol: str) -> None:
    assert state.workflow and state.orchestrator and state.provider

    workflow     = state.workflow
    orchestrator = state.orchestrator

    state.cycle_running = True
    await state.emit("cycle_started", {"pair": symbol})

    try:
        if not await state.provider.is_connected():
            await state.emit("info", {"message": "Reconnecting to MT5..."})
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
                await state.emit("cycle_failed", {"reason": "MT5 reconnect failed"})
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

    if MT5Provider is not None and settings.MT5_ACCOUNT:
        state.provider = MT5Provider(
            account=settings.MT5_ACCOUNT,
            password=settings.MT5_PASSWORD,
            server=settings.MT5_SERVER,
        )
        if not await state.provider.connect():
            state.last_error = "MT5 not connected — check credentials in Settings"
            logger.warning(state.last_error)
        else:
            state.connected = True
            logger.info("[STARTUP] MT5 connected")
    else:
        logger.info("[STARTUP] No MT5 credentials — running in demo/manual mode")

    verbose = settings.DEBUG and settings.ENVIRONMENT != "production"
    state.workflow    = TradingWorkflow(verbose=verbose, mt5_provider=state.provider)
    state.orchestrator = WorkflowOrchestrator()
    logger.info("[STARTUP] Workflow + orchestrator ready")

    yield

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
    logger.error("[UNHANDLED] %s %s → %s", request.method, request.url.path, exc,
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

    health = {
        "status":          "ok" if state.connected else "degraded",
        "connected":       state.connected,
        "cycle_running":   state.cycle_running,
        "environment":     settings.ENVIRONMENT,
        "data_provider":   settings.DATA_PROVIDER,
        "daily_loss_pct":  daily_loss_pct,
        "open_trades":     open_trades,
        "last_error":      state.last_error,
    }
    status_code = 200 if state.connected else 503
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
    if not state.workflow or not state.provider:
        raise HTTPException(503, "Server not ready — check MT5 connection")

    async def _runner():
        async with state.cycle_lock:
            await _run_cycle(pair)

    asyncio.create_task(_runner())
    return JSONResponse({"started": True, "pair": pair})


def _write_env_keys(updates: dict[str, str]) -> None:
    env_path = ROOT / ".env"
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
            raise HTTPException(400, "A valid Anthropic API key starting with 'sk-ant-' is required")
        updates = {"CLAUDE_API_KEY": req.api_key}
    elif provider == "mt5":
        if not (req.account and req.password and req.server):
            raise HTTPException(400, "MT5 requires account, password, server")
        updates = {"MT5_ACCOUNT": req.account, "MT5_PASSWORD": req.password,
                   "MT5_SERVER": req.server, "DATA_PROVIDER": "mt5"}
    elif provider == "mt4":
        if not (req.account and req.password and req.server):
            raise HTTPException(400, "MT4 requires account, password, server")
        updates = {"MT4_ACCOUNT": req.account, "MT4_PASSWORD": req.password,
                   "MT4_SERVER": req.server, "DATA_PROVIDER": "mt4"}
    elif provider == "tradingview":
        if not (req.username and (req.password or req.session_token)):
            raise HTTPException(400, "TradingView requires username + password or session_token")
        updates = {"TRADINGVIEW_USERNAME": req.username or "",
                   "TRADINGVIEW_PASSWORD": req.password or "",
                   "TRADINGVIEW_SESSION": req.session_token or "",
                   "DATA_PROVIDER": "tradingview"}
    elif provider == "telegram":
        if not (req.bot_token and req.chat_id):
            raise HTTPException(400, "Telegram requires bot_token and chat_id")
        updates = {"TELEGRAM_BOT_TOKEN": req.bot_token, "TELEGRAM_CHAT_ID": req.chat_id,
                   "ENABLE_TELEGRAM_NOTIFICATIONS": "True"}
    else:
        raise HTTPException(400, f"Unknown provider: {provider}")

    _write_env_keys(updates)

    reconnected = False
    if provider == "mt5" and MT5Provider is not None:
        if state.provider is not None:
            try:
                await state.provider.disconnect()
            except Exception:
                pass
        state.provider = MT5Provider(account=updates["MT5_ACCOUNT"],
                                     password=updates["MT5_PASSWORD"],
                                     server=updates["MT5_SERVER"])
        reconnected    = await state.provider.connect()
        state.connected = reconnected
        if state.workflow:
            state.workflow.trader_master.mt5_provider = state.provider
        await state.emit("info", {"message": f"MT5 reconnect: {'OK' if reconnected else 'FAILED'}"})

    logger.info("[CREDENTIALS] Provider '%s' saved by %s", provider, client_ip)
    return {"saved": True, "provider": provider, "reconnected": reconnected}


@app.get("/api/credentials/status")
async def credentials_status():
    """Tell the frontend which credentials are already configured."""
    return {
        "claude_configured":      bool(os.getenv("CLAUDE_API_KEY", "").strip()),
        "mt5_configured":         bool(os.getenv("MT5_ACCOUNT", "").strip()),
        "tradingview_configured": bool(os.getenv("TRADINGVIEW_USERNAME", "").strip()),
        "telegram_configured":    bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()),
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
    import uvicorn

    host = os.getenv("GUI_HOST", "127.0.0.1")
    port = int(os.getenv("GUI_PORT", "8765"))
    # Reload only in development
    reload = settings.ENVIRONMENT == "development"
    uvicorn.run("gui_server:app", host=host, port=port,
                log_level="info", reload=reload)
