# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for TechnobizTrader Windows installer.
Run:  pyinstaller desktop.spec
Output:  dist/TechnobizTrader-Setup-1.0.0.exe
"""

import os
import sys
from pathlib import Path

block_cipher = None

# The project root (where this .spec file lives) — PyInstaller exec() context
# has no __file__, so derive it from the script's argv.
_spec_path = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path.cwd()
ROOT = _spec_path.parent.resolve()

# Collect all hidden imports that PyInstaller can't detect statically
# (reflection-heavy libraries, optional providers, etc.)
hidden_imports = [
    # FastAPI / Starlette
    "starlette",
    "starlette.applications",
    "starlette.routing",
    "starlette.middleware",
    "starlette.middleware.cors",
    "starlette.middleware.base",
    "starlette.responses",
    "starlette.staticfiles",
    "fastapi",
    "fastapi.applications",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "fastapi.responses",
    "fastapi.security",
    "fastapi.security.api_key",
    "pydantic",
    "pydantic.main",
    "pydantic.fields",
    "pydantic_settings",
    "uvicorn",
    "uvicorn.config",
    "uvicorn.server",
    "uvicorn.structures",
    "sse_starlette",
    "sse_starlette.sse",
    "python_multipart",
    "multipart",
    # GUI
    "pydantic",
    # Agents & core
    "agents.base_agent",
    "agents.trend_master.trend_master",
    "agents.analyse_master.analyse_master",
    "agents.trader_master.trader_master",
    "agents.workflow",
    "agents.workflow_orchestrator",
    "config.settings",
    "config.constants",
    "config.kill_switch",
    "config.user_risk_settings",
    "config.news_blackout",
    "database.db_manager",
    "database.models",
    "utils.logger",
    "utils.chart_analyzer",
    "utils.notification",
    "utils.performance_tracker",
    "api.main",
    "api.routes",
    "api.websocket_manager",
    # AI clients
    "anthropic",
    "anthropic._client",
    "httpx",
    "httpx._client",
    "websockets",
    "websockets.client",
    # Data & math
    "pandas",
    "pandas._libs.tslibs.timestamps",
    "numpy",
    "numpy.core._multiarray_umath",
    "sqlalchemy",
    "sqlalchemy.orm",
    "sqlalchemy.engine",
    "sqlalchemy.dialects.sqlite",
    "psycopg2",
    "dotenv",
    "python_dateutil",
    "pytz",
    "PIL",
    "PIL._imaging",
    "Pillow",
    # MT5 (may not be importable without the MT5 DLLs; make it optional)
    "mt5_py",
    "MetaTrader5",
]

a = Analysis(
    [str(ROOT / "desktop_launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle the HTML UI and creator photo into the package
        (str(ROOT / "minecraft_trading_office.html"), "."),
        (str(ROOT / "Erick.jpg"),                 "."),
        # Config files
        (str(ROOT / "config"),  "config"),
        (str(ROOT / "agents"),  "agents"),
        (str(ROOT / "database"), "database"),
        (str(ROOT / "utils"),   "utils"),
        (str(ROOT / "api"),     "api"),
        # .env templates
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
    upx_exclude=[],
    console=True,      # show console window so users can see logs
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
    [],
    exclude_binaries=True,
    name="TechnobizTrader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TechnobizTrader",
)

# ── Windows onefile shortcut (not needed — we use COLLECT for cleaner dirs) ──
