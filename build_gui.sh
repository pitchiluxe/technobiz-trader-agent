#!/usr/bin/env bash
# build_gui.sh — Build TechnobizTrader distributables on macOS / Linux
# Usage: ./build_gui.sh [win|mac|linux|all]

set -euo pipefail

TARGET="${1:-all}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUI_DIR="$ROOT/gui"
PYTHON="${PYTHON:-python3}"

echo ""
echo "=== TechnobizTrader GUI Build ==="

# 1. Generate icons
echo "[1/4] Generating icons…"
"$PYTHON" "$ROOT/scripts/generate_icons.py"

# 2. Python deps
echo "[2/4] Installing Python dependencies…"
"$PYTHON" -m pip install -r "$ROOT/requirements.txt" -q

# 3. npm deps
echo "[3/4] Installing GUI npm packages…"
cd "$GUI_DIR" && npm install && cd "$ROOT"

# 4. Build
echo "[4/4] Building Electron app (target: $TARGET)…"
cd "$GUI_DIR"
case "$TARGET" in
  win)   npm run build:win   ;;
  mac)   npm run build:mac   ;;
  linux) npm run build:linux ;;
  *)     npm run build:all   ;;
esac
cd "$ROOT"

echo ""
echo "=== Build complete! Distributables in gui/dist/ ==="
