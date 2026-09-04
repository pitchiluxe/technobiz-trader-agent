"""
TechnobizTrader Desktop Launcher

Entry point for the PyInstaller-bundled Windows .exe.
Starts the FastAPI backend (gui_server.py) in a background thread, then
opens the user's default browser to the dashboard.  Both stay alive until
the user closes the terminal window or hits Ctrl+C.
"""

from __future__ import annotations

import os
import sys
import socket
import threading
import time
import webbrowser
from pathlib import Path

# When bundled with PyInstaller, sys._MEIPASS points to the extraction dir.
# When running as a script, the project root is the script's directory.
if getattr(sys, "frozen", False):
    # PyInstaller bundle — resources live next to the .exe
    BUNDLE_DIR = Path(sys._MEIPASS)
    EXE_DIR    = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent
    EXE_DIR    = BUNDLE_DIR

# Ensure the bundle dir is on sys.path so we can import the project modules
sys.path.insert(0, str(BUNDLE_DIR))

import uvicorn  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765


def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


def _wait_for_server(url: str, timeout: float = 30.0) -> bool:
    """Poll |url| every 0.25s until it returns or |timeout| elapses."""
    import urllib.request
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status in (200, 401):   # 401 = server up, auth required
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def main() -> int:
    # Show a console banner for the user
    print("=" * 64)
    print("  TechnobizTrader — AI Trading Agency")
    print("  Multi-agent ICT trading system  ·  v1.0.0")
    print("=" * 64)
    print()

    if _port_in_use(PORT):
        print(f"[launcher] Port {PORT} already in use — assuming server is running")
    else:
        # Import the FastAPI app from gui_server
        from gui_server import app, logger  # noqa: F401

        config = uvicorn.Config(
            app=app,
            host=HOST,
            port=PORT,
            log_level="info",
            access_log=False,
        )
        server = uvicorn.Server(config)
        t = threading.Thread(target=server.run, daemon=True, name="uvicorn")
        t.start()
        print(f"[launcher] Starting backend on http://{HOST}:{PORT} ...")

    url = f"http://{HOST}:{PORT}/"
    if _wait_for_server(url, timeout=30):
        print(f"[launcher] Backend ready — opening browser at {url}")
        try:
            webbrowser.open(url)
        except Exception as exc:
            print(f"[launcher] Could not open browser: {exc}")
            print(f"[launcher] Open {url} manually in your browser.")
    else:
        print("[launcher] Backend did not become ready in 30s.")
        print(f"[launcher] Try opening {url} manually in a few seconds.")
        return 1

    print()
    print("Dashboard is running. Close this window or press Ctrl+C to stop.")
    print()

    # Keep the launcher alive so the backend thread isn't killed.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[launcher] Shutting down...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
