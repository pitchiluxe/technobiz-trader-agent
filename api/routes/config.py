"""Config / credentials management route — GET|POST /api/config/*."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

# Credentials are persisted in a JSON file next to the .env
# (kept out of source control via .gitignore)
# In production, Electron passes CREDS_FILE_PATH pointing to %APPDATA%
_creds_env = os.environ.get("CREDS_FILE_PATH")
_CREDS_FILE = Path(_creds_env) if _creds_env else Path(__file__).parents[2] / "gui_credentials.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_credentials() -> Dict[str, Any]:
    if _CREDS_FILE.exists():
        try:
            return json.loads(_CREDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_credentials(data: Dict[str, Any]) -> None:
    _CREDS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _mask(value: str) -> str:
    """Return masked string for display."""
    if not value or len(value) < 6:
        return "•" * 8
    return value[:3] + "•" * (len(value) - 6) + value[-3:]


# ── Pydantic models ───────────────────────────────────────────────────────────

class CredentialPayload(BaseModel):
    # Claude
    claude_api_key: Optional[str] = None
    # MT5
    mt5_account: Optional[str] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    # TradingView
    tradingview_api_type: Optional[str] = None  # "free" | "premium"
    tradingview_exchange: Optional[str] = None
    # Foundry / Azure (optional)
    foundry_endpoint: Optional[str] = None
    foundry_model: Optional[str] = None
    foundry_api_key: Optional[str] = None
    # Trading params
    account_balance: Optional[float] = None
    trading_pairs: Optional[str] = None
    max_risk_per_trade: Optional[float] = None
    # Database
    database_url: Optional[str] = None
    # Data provider
    data_provider: Optional[str] = None  # "mt5" | "tradingview" | "hybrid"


class StatusResponse(BaseModel):
    is_first_run: bool
    claude_configured: bool
    mt5_configured: bool
    tradingview_configured: bool
    foundry_configured: bool
    database_configured: bool
    data_provider: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=StatusResponse)
async def get_config_status():
    """Check which APIs are currently configured (for first-run detection)."""
    creds = _load_credentials()
    return StatusResponse(
        is_first_run=len(creds) == 0,
        claude_configured=bool(
            os.getenv("ANTHROPIC_AUTH_TOKEN") or
            os.getenv("ANTHROPIC_API_KEY") or
            creds.get("claude_api_key")
        ),
        mt5_configured=bool(
            creds.get("mt5_account") and creds.get("mt5_password") and creds.get("mt5_server")
        ),
        tradingview_configured=bool(creds.get("tradingview_api_type")),
        foundry_configured=bool(creds.get("foundry_endpoint") and creds.get("foundry_api_key")),
        database_configured=bool(creds.get("database_url")),
        data_provider=creds.get("data_provider", "mt5"),
    )


@router.post("/credentials")
async def save_credentials(body: CredentialPayload):
    """Save (upsert) credential values. Existing keys are overwritten; omitted keys are unchanged."""
    creds = _load_credentials()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    creds.update(updates)
    _save_credentials(creds)
    # Apply to running environment so they take effect without restart
    _apply_env(creds)
    return {"success": True, "updated_keys": list(updates.keys())}


@router.get("/credentials/masked")
async def get_masked_credentials():
    """Return credential keys with masked values (safe to display in UI)."""
    creds = _load_credentials()
    masked = {}
    sensitive = {"claude_api_key", "mt5_password", "foundry_api_key", "database_url"}
    for key, value in creds.items():
        if not isinstance(value, str):
            masked[key] = value
        elif key in sensitive:
            masked[key] = _mask(str(value))
        else:
            masked[key] = value
    return {"credentials": masked}


@router.post("/validate")
async def validate_connections():
    """Test connectivity for each configured provider and return per-service status."""
    creds = _load_credentials()
    results: Dict[str, Any] = {}

    # AI key — accept Anthropic (sk-ant-) or OpenRouter (sk-or-v1-) keys
    ai_key = (
        os.getenv("ANTHROPIC_AUTH_TOKEN") or
        os.getenv("ANTHROPIC_API_KEY") or
        creds.get("claude_api_key") or ""
    )
    if ai_key.startswith("sk-ant-"):
        results["claude"] = {"ok": True, "message": "Anthropic API key configured"}
    elif ai_key.startswith("sk-or-v1-"):
        results["claude"] = {"ok": True, "message": "OpenRouter API key configured"}
    elif ai_key:
        results["claude"] = {"ok": False, "message": "Unrecognised key format"}
    else:
        results["claude"] = {"ok": False, "message": "Not configured"}

    # MT5
    if creds.get("mt5_account") and creds.get("mt5_server"):
        try:
            import MetaTrader5 as mt5  # noqa: PLC0415
            if mt5.initialize():
                ok = mt5.login(
                    login=int(creds["mt5_account"]),
                    password=creds.get("mt5_password", ""),
                    server=creds["mt5_server"],
                )
                mt5.shutdown()
                results["mt5"] = {"ok": ok, "message": "Connected" if ok else "Login failed"}
            else:
                results["mt5"] = {"ok": False, "message": "MT5 terminal not running"}
        except ImportError:
            results["mt5"] = {"ok": False, "message": "MetaTrader5 package not installed"}
        except Exception as exc:
            results["mt5"] = {"ok": False, "message": str(exc)}
    else:
        results["mt5"] = {"ok": False, "message": "Not configured"}

    # TradingView — check package is importable and api_type is set
    if creds.get("tradingview_api_type"):
        try:
            import tradingview_ta  # noqa: PLC0415, F401
            results["tradingview"] = {"ok": True, "message": "Package ready"}
        except ImportError:
            results["tradingview"] = {"ok": False, "message": "tradingview-ta package not installed"}
    else:
        results["tradingview"] = {"ok": False, "message": "Not configured (set API Type field)"}

    # Database — use creds value or fall back to DATABASE_URL env var
    db_url = creds.get("database_url") or os.getenv("DATABASE_URL", "")
    if db_url:
        try:
            from sqlalchemy import create_engine, text  # noqa: PLC0415
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["database"] = {"ok": True, "message": "Connected"}
        except Exception as exc:
            results["database"] = {"ok": False, "message": str(exc)}
    else:
        results["database"] = {"ok": False, "message": "Not configured"}

    return {"results": results}


# ── Claude interpret endpoint ─────────────────────────────────────────────────

class InterpretRequest(BaseModel):
    command: str
    agent_context: str  # "trend_master" | "analyse_master" | "trader_master"


@router.post("/claude/interpret")
async def claude_interpret(body: InterpretRequest):
    """
    Pass user free-text command through Claude to get:
    - Structured agent action (symbol, timeframes, parameters)
    - Market insight / explanation
    """
    # Prefer env-based keys (OpenRouter / Anthropic) over stored credential
    creds = _load_credentials()
    api_key = (
        os.getenv("ANTHROPIC_AUTH_TOKEN") or
        os.getenv("ANTHROPIC_API_KEY") or
        creds.get("claude_api_key") or
        os.getenv("CLAUDE_API_KEY", "")
    )
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="AI API key not configured. Set ANTHROPIC_AUTH_TOKEN in .env.local",
        )

    # Lazy import — anthropic is optional; backend must start even if not installed
    try:
        import anthropic as _anthropic
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="anthropic package is not installed. Run: pip install anthropic>=0.25.0",
        )

    base_url = os.getenv("ANTHROPIC_BASE_URL") or None
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    try:
        client_kwargs: dict = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = _anthropic.Anthropic(**client_kwargs)

        system_prompt = (
            "You are TechnobizTrader's AI assistant. "
            "You translate trader instructions into structured JSON actions for the agents. "
            "The system uses ICT methodology (Liquidity Sweep, Break of Structure, Imbalance/Order Block, Pullback). "
            "Always respond with valid JSON in this format:\n"
            '{"action": "<analyze|execute|reset>", "symbol": "<PAIR>", '
            '"timeframes": ["1d","4h","1h"], "insight": "<brief market insight>", '
            '"instructions": "<what the agent should do>"}'
        )

        context_hints = {
            "trend_master": "The user is talking to Trend-Master who analyzes macro trends.",
            "analyse_master": "The user is talking to Analyse-Master who detects ICT patterns and generates signals.",
            "trader_master": "The user is talking to Trader-Master who executes trades with risk management.",
        }

        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=system_prompt + "\n\n" + context_hints.get(body.agent_context, ""),
            messages=[{"role": "user", "content": body.command}],
        )

        raw = response.content[0].text.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"action": "analyze", "symbol": "EURUSD", "insight": raw, "instructions": raw}

        return {"success": True, "result": parsed}

    except _anthropic.AuthenticationError:
        logger.warning("[AI] Invalid API key")
        raise HTTPException(status_code=401, detail="Invalid API key. Please check your ANTHROPIC_AUTH_TOKEN in .env.local.")
    except _anthropic.APIConnectionError as exc:
        logger.warning("[AI] Connection error: %s", exc)
        raise HTTPException(status_code=503, detail="Could not reach AI provider. Check your internet connection.")
    except Exception as exc:
        logger.exception("[AI] Interpretation failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Internal helpers ──────────────────────────────────────────────────────────

def _apply_env(creds: Dict[str, Any]) -> None:
    """Apply saved credentials to os.environ for the running process."""
    mapping = {
        "claude_api_key": "CLAUDE_API_KEY",
        "mt5_account": "MT5_ACCOUNT",
        "mt5_password": "MT5_PASSWORD",
        "mt5_server": "MT5_SERVER",
        "tradingview_api_type": "TRADINGVIEW_API_TYPE",
        "tradingview_exchange": "TRADINGVIEW_EXCHANGE",
        "foundry_endpoint": "FOUNDRY_PROJECT_ENDPOINT",
        "foundry_model": "FOUNDRY_MODEL_DEPLOYMENT_NAME",
        "foundry_api_key": "FOUNDRY_API_KEY",
        "account_balance": "ACCOUNT_BALANCE",
        "trading_pairs": "TRADING_PAIRS",
        "max_risk_per_trade": "MAX_RISK_PER_TRADE",
        "database_url": "DATABASE_URL",
        "data_provider": "DATA_PROVIDER",
    }
    for cred_key, env_key in mapping.items():
        if creds.get(cred_key) is not None:
            os.environ[env_key] = str(creds[cred_key])
