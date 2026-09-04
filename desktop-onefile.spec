# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller ONE-FILE spec for TechnobizTrader Windows installer.
Run:  pyinstaller desktop-onefile.spec
Output:  dist/TechnobizTrader-Setup-1.0.0.exe  (single self-extracting executable)
"""

import os
import sys
from pathlib import Path

block_cipher = None

_spec_path = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path.cwd()
ROOT = _spec_path.parent.resolve()

hidden_imports = [
    "starlette", "starlette.applications", "starlette.routing",
    "starlette.middleware", "starlette.middleware.cors", "starlette.middleware.base",
    "starlette.responses", "starlette.staticfiles",
    "fastapi", "fastapi.applications", "fastapi.middleware", "fastapi.middleware.cors",
    "fastapi.responses", "fastapi.security", "fastapi.security.api_key",
    "pydantic", "pydantic.main", "pydantic.fields", "pydantic_settings",
    "uvicorn", "uvicorn.config", "uvicorn.server", "uvicorn.structures",
    "sse_starlette", "sse_starlette.sse",
    "python_multipart", "multipart",
    "agents.base_agent",
    "agents.trend_master.trend_master",
    "agents.analyse_master.analyse_master",
    "agents.trader_master.trader_master",
    "agents.workflow", "agents.workflow_orchestrator",
    "config.settings", "config.constants", "config.kill_switch",
    "config.user_risk_settings", "config.news_blackout",
    "database.db_manager", "database.models",
    "utils.logger", "utils.chart_analyzer", "utils.notification", "utils.performance_tracker",
    "api.main", "api.routes", "api.websocket_manager",
    "anthropic", "anthropic._client",
    "httpx", "httpx._client",
    "websockets", "websockets.client",
    "pandas", "numpy",
    "sqlalchemy", "sqlalchemy.orm", "sqlalchemy.engine", "sqlalchemy.dialects.sqlite",
    "psycopg2",
    "dotenv", "python_dateutil", "pytz",
    "PIL", "Pillow",
    "mt5_py", "MetaTrader5",
]

a = Analysis(
    [str(ROOT / "desktop_launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "minecraft_trading_office.html"), "."),
        (str(ROOT / "Erick.jpg"), "."),
        (str(ROOT / "config"),  "config"),
        (str(ROOT / "agents"),  "agents"),
        (str(ROOT / "database"), "database"),
        (str(ROOT / "utils"),   "utils"),
        (str(ROOT / "api"),     "api"),
        (str(ROOT / ".env.template"), "."),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    keys=[],
    exclude_binaries=False,
    name="TechnobizTrader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TechnobizTrader-Setup-1.0.0",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
