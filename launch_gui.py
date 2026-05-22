#!/usr/bin/env python3
"""
TechnobizTrader GUI Launcher

Starts the FastAPI backend then launches the Electron GUI.

Usage (dev mode):
  python launch_gui.py

Usage (skip Electron, API only):
  python launch_gui.py --api-only
"""

import argparse
import subprocess
import sys
import time
import os
from pathlib import Path

ROOT = Path(__file__).parent
GUI_DIR = ROOT / "gui"


def wait_for_backend(port: int = 8765, timeout: int = 30) -> bool:
    import urllib.request
    import urllib.error

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def start_backend() -> subprocess.Popen:
    python = sys.executable
    proc = subprocess.Popen(
        [python, "-m", "uvicorn", "api.main:app",
         "--host", "127.0.0.1", "--port", "8765"],
        cwd=str(ROOT),
    )
    return proc


def start_electron() -> subprocess.Popen:
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    # First ensure node_modules exist
    node_modules = GUI_DIR / "node_modules"
    if not node_modules.exists():
        print("[launcher] Installing GUI dependencies (npm install)…")
        subprocess.run([npm_cmd, "install"], cwd=str(GUI_DIR), check=True)

    proc = subprocess.Popen(
        [npm_cmd, "run", "electron"],
        cwd=str(GUI_DIR),
    )
    return proc


def main():
    parser = argparse.ArgumentParser(description="TechnobizTrader GUI Launcher")
    parser.add_argument("--api-only", action="store_true", help="Start only the FastAPI backend")
    args = parser.parse_args()

    print("[launcher] Starting TechnobizTrader backend…")
    backend = start_backend()

    print("[launcher] Waiting for backend to be ready…")
    ready = wait_for_backend()
    if not ready:
        print("[launcher] Backend did not start in time — check for errors above")
        backend.kill()
        sys.exit(1)
    print("[launcher] Backend ready at http://127.0.0.1:8765")

    if args.api_only:
        print("[launcher] --api-only: running in API-only mode. Press Ctrl+C to stop.")
        try:
            backend.wait()
        except KeyboardInterrupt:
            backend.terminate()
        return

    print("[launcher] Launching Electron GUI…")
    electron = start_electron()

    try:
        electron.wait()
    except KeyboardInterrupt:
        pass
    finally:
        backend.terminate()
        electron.terminate()


if __name__ == "__main__":
    main()
