#!/usr/bin/env python3
"""
Generate TechnobizTrader app icons.

Produces:
  gui/assets/icon.png    — 1024×1024 (base, also used for Linux)
  gui/assets/icon.ico    — Windows multi-size
  gui/assets/icon.icns   — macOS (requires macOS + iconutil, or pillow-icns)

Run from repo root:
  python scripts/generate_icons.py
"""

from __future__ import annotations

import os
import struct
import zlib
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("Pillow is required: pip install Pillow")

ASSETS = Path(__file__).parents[1] / "gui" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = (10, 10, 20, 255)
PANEL   = (15, 15, 30, 255)
INDIGO  = (79, 70, 229, 255)
CYAN    = (14, 165, 233, 255)
GREEN   = (34, 197, 94, 255)
GOLD    = (245, 158, 11, 255)
WHITE   = (255, 255, 255, 255)


def draw_icon(size: int) -> Image.Image:
    """Draw a pixel-art TechnobizTrader icon at the given square size."""
    img = Image.new("RGBA", (size, size), BG)
    d   = ImageDraw.Draw(img)

    s = size / 100  # scale factor

    # Background circle / glow
    cx, cy = size // 2, size // 2
    r = int(44 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PANEL)

    # Outer ring
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=INDIGO, width=max(2, int(3 * s)))

    # --- Candlestick chart (background detail) ---
    candle_data = [
        (35, 42, 38, 45),
        (39, 50, 36, 48),
        (42, 55, 41, 52),
        (47, 58, 44, 56),
        (52, 62, 50, 65),
    ]
    for i, (lo, hi, o, c) in enumerate(candle_data):
        x = int((20 + i * 12) * s)
        y_lo = int((90 - lo) * s)
        y_hi = int((90 - hi) * s)
        y_o  = int((90 - o) * s)
        y_c  = int((90 - c) * s)
        color = GREEN if c > o else GOLD
        d.line([x, y_lo, x, y_hi], fill=color, width=max(1, int(s)))
        y_top, y_bot = min(y_o, y_c), max(y_o, y_c)
        if y_bot == y_top:
            y_bot = y_top + max(1, int(s))
        d.rectangle([x - int(3 * s), y_top, x + int(3 * s), y_bot], fill=color)

    # --- Three pixel agent icons ---
    agent_specs = [
        (int(30 * s), int(42 * s), INDIGO, "T"),
        (int(50 * s), int(38 * s), CYAN,   "A"),
        (int(70 * s), int(42 * s), GREEN,  "X"),
    ]
    dot_r = max(7, int(10 * s))
    for ax, ay, color, _ in agent_specs:
        d.ellipse([ax - dot_r, ay - dot_r, ax + dot_r, ay + dot_r], fill=color)
        d.ellipse(
            [ax - dot_r + max(1, int(s)), ay - dot_r + max(1, int(s)),
             ax + dot_r - max(1, int(s)), ay + dot_r - max(1, int(s))],
            fill=PANEL,
        )
        inner = max(3, int(5 * s))
        d.ellipse([ax - inner, ay - inner, ax + inner, ay + inner], fill=color)

    # Connector lines
    a0 = agent_specs[0][:2]
    a1 = agent_specs[1][:2]
    a2 = agent_specs[2][:2]
    d.line([a0[0], a0[1], a1[0], a1[1]], fill=(*INDIGO[:3], 180), width=max(1, int(s)))
    d.line([a1[0], a1[1], a2[0], a2[1]], fill=(*CYAN[:3], 180),   width=max(1, int(s)))

    # --- "T" letter watermark ---
    font_size = max(16, int(18 * s))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    text = "T"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw // 2, int(68 * s)), text, fill=(*WHITE[:3], 160), font=font)

    return img


def save_ico(base: Image.Image) -> None:
    """Save Windows .ico with 16/32/48/64/128/256 px layers (256 as primary)."""
    sizes = [16, 32, 48, 64, 128, 256]
    ico_path = ASSETS / "icon.ico"
    # Save from the large base so Pillow can resize down accurately.
    # Pass the 256-px image as the root frame so electron-builder reads 256×256.
    img_256 = base.resize((256, 256), Image.LANCZOS)
    img_256.save(ico_path, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"  ✓ {ico_path}")


def save_icns(base: Image.Image) -> None:
    """
    Save a minimal macOS .icns containing ic07 (128) and ic08 (256) icons.
    For production builds on macOS, `iconutil` produces a more complete .icns.
    """
    icns_sizes = {
        b"icp4": 16,
        b"icp5": 32,
        b"ic07": 128,
        b"ic08": 256,
        b"ic09": 512,
        b"ic10": 1024,
    }
    import io

    icns_data = b"icns"
    blocks = b""
    for tag, sz in icns_sizes.items():
        frame = base.resize((sz, sz), Image.LANCZOS)
        buf = io.BytesIO()
        frame.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        block_size = 8 + len(png_bytes)
        blocks += tag + struct.pack(">I", block_size) + png_bytes

    total = 8 + len(blocks)
    icns_path = ASSETS / "icon.icns"
    icns_path.write_bytes(icns_data + struct.pack(">I", total) + blocks)
    print(f"  ✓ {icns_path}")


def main() -> None:
    print("Generating TechnobizTrader icons…")

    base = draw_icon(1024)

    png_path = ASSETS / "icon.png"
    base.save(png_path, format="PNG")
    print(f"  ✓ {png_path}")

    save_ico(base)
    save_icns(base)

    print("Done.")


if __name__ == "__main__":
    main()
