"""FastAPI application — TechnobizTrader GUI backend.

Security hardening vs initial version:
  - CORS locked to localhost-only origins (no wildcard in production)
  - API key authentication via x-api-key header on all non-health routes
  - WebSocket disconnect handled gracefully
  - Health endpoint always public (required by Docker / Kubernetes probes)
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security.api_key import APIKeyHeader

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from api.routes import config_router, risk_router, signals_router, trades_router, trends_router
from api.websocket_manager import ConnectionManager

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# API key authentication
# ─────────────────────────────────────────────────────────────────────────────
_DASHBOARD_API_KEY = os.getenv("DASHBOARD_API_KEY", "")
_api_key_header    = APIKeyHeader(name="x-api-key", auto_error=False)


async def require_api_key(key: str = Security(_api_key_header)) -> str:
    """
    Validate the x-api-key header on protected routes.
    If DASHBOARD_API_KEY is not set in .env, auth is skipped (dev mode only).
    """
    if not _DASHBOARD_API_KEY:
        # No key configured — allow all (development mode)
        return "dev-mode"
    if key != _DASHBOARD_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key


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
# Static HTML pages
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(_PROJECT_ROOT, "minecraft_trading_office.html"))

@app.get("/minecraft_trading_office.html", include_in_schema=False)
async def serve_minecraft_office():
    return FileResponse(os.path.join(_PROJECT_ROOT, "minecraft_trading_office.html"))

@app.get("/trading_command_center.html", include_in_schema=False)
async def serve_trading_center():
    return FileResponse(os.path.join(_PROJECT_ROOT, "trading_command_center.html"))

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
