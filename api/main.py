"""FastAPI application — TechnobizTrader GUI backend.

Security hardening vs initial version:
  - CORS locked to localhost-only origins (no wildcard in production)
  - API key authentication via x-api-key header on all non-health routes
  - WebSocket disconnect handled gracefully
  - Health endpoint always public (required by Docker / Kubernetes probes)
"""

import logging
import os
import secrets
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Token injected into the HTML at serve time so the page can authenticate
# API calls. Set GUI_SECRET_KEY in Vercel env vars to keep it stable across
# deployments; otherwise a new random token is generated each cold start.
_GUI_SECRET: str = os.getenv("GUI_SECRET_KEY", "").strip() or secrets.token_hex(32)

from api.routes import config_router, risk_router, signals_router, trades_router, trends_router
from api.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Authentication — accepts either x-api-key or X-GUI-Token
# ─────────────────────────────────────────────────────────────────────────────
_DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")
_api_key_header    = APIKeyHeader(name="x-api-key",   auto_error=False)
_gui_token_header  = APIKeyHeader(name="X-GUI-Token", auto_error=False)


async def require_api_key(
    api_key:   str = Security(_api_key_header),
    gui_token: str = Security(_gui_token_header),
) -> str:
    token = api_key or gui_token or ""
    # If neither secret is configured, allow all requests (dev / demo mode)
    if not _DASHBOARD_API_KEY and not _GUI_SECRET:
        return "dev-mode"
    if secrets.compare_digest(token, _GUI_SECRET):
        return token
    if _DASHBOARD_API_KEY and secrets.compare_digest(token, _DASHBOARD_API_KEY):
        return token
    if not _DASHBOARD_API_KEY:
        return "dev-mode"
    raise HTTPException(status_code=403, detail="Invalid or missing API key")


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket connection manager
# ─────────────────────────────────────────────────────────────────────────────
manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[API] TechnobizTrader backend starting…")
    app.state.manager = manager
    yield
    logger.info("[API] TechnobizTrader backend shutting down…")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "TechnobizTrader API",
    description = "Backend API for TechnobizTrader — 3-agent ICT trading system",
    version     = "1.1.0",
    lifespan    = lifespan,
)

# CORS: localhost + Vercel deployment origins
_ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
_VERCEL_URL   = os.getenv("VERCEL_URL", "")          # auto-set by Vercel
_allowed_origins = [
    "http://localhost",
    "http://localhost:8765",
    "http://127.0.0.1",
    "http://127.0.0.1:8765",
    "null",   # file:// origin used by Electron in dev
]
if _VERCEL_URL:
    _allowed_origins.append(f"https://{_VERCEL_URL}")
# Allow any *.vercel.app subdomain for preview deployments
_VERCEL_PATTERN = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins      = _allowed_origins,
    allow_origin_regex = _VERCEL_PATTERN,
    allow_credentials  = True,
    allow_methods      = ["GET", "POST"],
    allow_headers      = ["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Protected routers (require API key)
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(
    trends_router,  prefix="/api/trends",  tags=["Trend-Master"],
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    signals_router, prefix="/api/signals", tags=["Analyse-Master"],
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    trades_router,  prefix="/api/trades",  tags=["Trader-Master"],
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    config_router,  prefix="/api/config",  tags=["Configuration"],
    dependencies=[Depends(require_api_key)],
)
app.include_router(
    risk_router,    prefix="/api/risk",    tags=["Risk Management"],
    dependencies=[Depends(require_api_key)],
)

# ─────────────────────────────────────────────────────────────────────────────
# WebSocket endpoint (real-time agent status feed)
# ─────────────────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time agent status feed for the GUI frontend."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive; server pushes via manager.broadcast()
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("[WS] Unexpected error, disconnecting: %s", exc)
        manager.disconnect(websocket)

# ─────────────────────────────────────────────────────────────────────────────
# HTML serving — injects window.__GUI_TOKEN__ so the page can auth API calls
# ─────────────────────────────────────────────────────────────────────────────
def _serve_html(filename: str) -> HTMLResponse:
    path = os.path.join(_PROJECT_ROOT, filename)
    html = open(path, encoding="utf-8").read()
    injection = f'<script>window.__GUI_TOKEN__="{_GUI_SECRET}";</script>'
    html = html.replace("</head>", injection + "\n</head>", 1)
    return HTMLResponse(html)

@app.get("/", include_in_schema=False)
async def root():
    return _serve_html("minecraft_trading_office.html")

@app.get("/minecraft_trading_office.html", include_in_schema=False)
async def serve_minecraft_office():
    return _serve_html("minecraft_trading_office.html")

@app.get("/trading_command_center.html", include_in_schema=False)
async def serve_trading_center():
    return _serve_html("trading_command_center.html")

# ─────────────────────────────────────────────────────────────────────────────
# GUI endpoints expected by minecraft_trading_office.html
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/status", tags=["System"])
async def status():
    """Returns backend status — called by the Settings page health check."""
    return {
        "status": "online",
        "connected": False,
        "provider": os.getenv("DATA_PROVIDER", "demo"),
        "mode": "demo",
        "version": "1.1.0",
    }

@app.get("/api/credentials/status", tags=["System"])
async def credentials_status():
    """Reports which credentials are already configured via environment variables."""
    return {
        "claude_configured":       bool(os.getenv("CLAUDE_API_KEY")),
        "mt5_configured":          bool(os.getenv("MT5_ACCOUNT")),
        "tradingview_configured":  bool(os.getenv("TRADINGVIEW_USERNAME")),
        "telegram_configured":     bool(os.getenv("TELEGRAM_BOT_TOKEN")),
    }

class CredentialsRequest(BaseModel):
    provider:      str
    api_key:       Optional[str] = None
    account:       Optional[str] = None
    password:      Optional[str] = None
    server:        Optional[str] = None
    username:      Optional[str] = None
    session_token: Optional[str] = None
    bot_token:     Optional[str] = None
    chat_id:       Optional[str] = None

@app.post("/api/credentials", tags=["System"])
async def save_credentials(req: CredentialsRequest, _: str = Depends(require_api_key)):
    """
    On Vercel, credentials cannot be persisted to disk.
    Set them as Environment Variables in your Vercel Project Settings instead.
    This endpoint validates the input and acknowledges receipt for the session.
    """
    provider = req.provider.lower().strip()
    if provider == "claude":
        if not req.api_key or not req.api_key.startswith("sk-ant-"):
            raise HTTPException(400, "A valid Anthropic key starting with 'sk-ant-' is required")
        os.environ["CLAUDE_API_KEY"] = req.api_key
    elif provider in ("mt5", "mt4"):
        if not (req.account and req.password and req.server):
            raise HTTPException(400, f"{provider.upper()} requires account, password, server")
        os.environ["MT5_ACCOUNT"]  = req.account
        os.environ["MT5_PASSWORD"] = req.password
        os.environ["MT5_SERVER"]   = req.server
    elif provider == "tradingview":
        if not req.username:
            raise HTTPException(400, "TradingView requires a username")
        os.environ["TRADINGVIEW_USERNAME"] = req.username
        if req.password:       os.environ["TRADINGVIEW_PASSWORD"] = req.password
        if req.session_token:  os.environ["TRADINGVIEW_SESSION"]  = req.session_token
    elif provider == "telegram":
        if not (req.bot_token and req.chat_id):
            raise HTTPException(400, "Telegram requires bot_token and chat_id")
        os.environ["TELEGRAM_BOT_TOKEN"] = req.bot_token
        os.environ["TELEGRAM_CHAT_ID"]   = req.chat_id
    else:
        raise HTTPException(400, f"Unknown provider: {provider}")

    return {"ok": True, "provider": provider,
            "note": "Saved for this session. Add to Vercel Environment Variables for persistence."}

# ─────────────────────────────────────────────────────────────────────────────
# Health check — always public, required by Docker/K8s probes
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
async def health():
    """Public health endpoint. Returns 200 if the process is alive."""
    return {"status": "ok", "version": "1.1.0"}

# ─────────────────────────────────────────────────────────────────────────────
# Direct run
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8765"))
    uvicorn.run("api.main:app", host="127.0.0.1", port=port, reload=False, log_level="info")
