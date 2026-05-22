"""
Generate TechnobizTrader application icon.
Outputs: gui/assets/icon.ico  (multi-size Windows icon)
         gui/assets/icon.png  (512×512 for Linux / notifications)
         gui/assets/icon.icns (macOS — requires additional tool on non-Mac)

Run:  python create_icon.py
"""

import math
import os
from PIL import Image, ImageDraw

# ── Colour palette ─────────────────────────────────────────────────────────────
NAVY_DEEP   = (10,  22,  40,  255)   # #0A1628 — background
NAVY_MID    = (15,  35,  65,  255)   # #0F2341 — inner ring
GOLD        = (240, 180,  40,  255)  # #F0B428 — brand colour / ring
GOLD_LIGHT  = (255, 215,  90,  255)  # #FFD75A — "T" highlight
GREEN       = ( 34, 197,  94,  255)  # #22C55E — bullish candle
GREEN_DARK  = ( 22, 163,  74,  255)  # #16A34A — wick / body shadow
RED         = (239,  68,  68,  255)  # #EF4444 — bearish sweep candle
RED_DARK    = (185,  28,  28,  255)  # #B91C1C — wick shadow
WHITE       = (255, 255, 255,  255)
TRANSPARENT = (  0,   0,   0,    0)


# ── Drawing helpers ────────────────────────────────────────────────────────────

def aa_circle(draw: ImageDraw.ImageDraw, bbox, fill=None, outline=None, width=1):
    """Draw a circle via polygon approximation for smoother edges at any scale."""
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    steps = 180
    pts = [
        (cx + rx * math.cos(2 * math.pi * i / steps),
         cy + ry * math.sin(2 * math.pi * i / steps))
        for i in range(steps)
    ]
    if fill:
        draw.polygon(pts, fill=fill)
    if outline:
        draw.polygon(pts, outline=outline)
        # Extra pass to make ring thicker
        for extra in range(1, width):
            rx2, ry2 = rx - extra, ry - extra
            if rx2 <= 0 or ry2 <= 0:
                break
            pts2 = [
                (cx + rx2 * math.cos(2 * math.pi * i / steps),
                 cy + ry2 * math.sin(2 * math.pi * i / steps))
                for i in range(steps)
            ]
            draw.polygon(pts2, outline=outline)


def draw_candle(draw: ImageDraw.ImageDraw, cx, body_top, body_bot,
                wick_top, wick_bot, half_w, bullish: bool):
    """Draw a single candlestick."""
    body_col  = GREEN      if bullish else RED
    wick_col  = GREEN_DARK if bullish else RED_DARK
    wick_half = max(1, half_w // 3)

    # Wick
    draw.rectangle(
        [cx - wick_half, wick_top, cx + wick_half, wick_bot],
        fill=wick_col,
    )
    # Body
    draw.rectangle(
        [cx - half_w, body_top, cx + half_w, body_bot],
        fill=body_col,
    )


# ── Master render ──────────────────────────────────────────────────────────────

def render(size: int) -> Image.Image:
    """
    Render TechnobizTrader icon at `size`×`size` by drawing at 4× and
    then downsampling with LANCZOS.
    """
    S = size * 4                         # work canvas
    img  = Image.new("RGBA", (S, S), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    pad  = int(S * 0.04)
    full = [pad, pad, S - pad, S - pad]

    # ── 1. Dark background circle ──────────────────────────────────────────
    aa_circle(draw, full, fill=NAVY_DEEP)

    # ── 2. Subtle inner ring to add depth ─────────────────────────────────
    inner_pad = int(S * 0.11)
    inner = [inner_pad, inner_pad, S - inner_pad, S - inner_pad]
    aa_circle(draw, inner, fill=NAVY_MID)

    # ── 3. Gold outer ring ─────────────────────────────────────────────────
    ring_w = max(4, int(S * 0.025))
    aa_circle(draw, full, outline=GOLD, width=ring_w)

    # ── 4. Candle chart ────────────────────────────────────────────────────
    # Chart lives in bottom-right 65% of circle
    #
    # ICT story:  RED sweep candle → green reversal → green momentum → green breakout
    #
    chart_x0 = int(S * 0.18)
    chart_x1 = int(S * 0.87)
    chart_y0 = int(S * 0.36)
    chart_y1 = int(S * 0.88)
    chart_w  = chart_x1 - chart_x0
    chart_h  = chart_y1 - chart_y0

    def cy(frac):   # fraction → y pixel (0=top, 1=bottom)
        return chart_y0 + int(frac * chart_h)

    def cx(frac):   # fraction → x pixel
        return chart_x0 + int(frac * chart_w)

    half_w = max(4, int(chart_w * 0.065))

    # Candle definitions:  (x_frac, body_top, body_bot, wick_top, wick_bot, bullish)
    candles = [
        # Red sweep candle — spikes up to the "liquidity" level then reverses
        (0.10, 0.35, 0.65, 0.15, 0.72, False),
        # Hammer / bullish engulf at the OB
        (0.28, 0.52, 0.75, 0.48, 0.82, True),
        # First green impulse
        (0.46, 0.30, 0.56, 0.25, 0.60, True),
        # Continuation
        (0.64, 0.15, 0.38, 0.10, 0.42, True),
        # Breakout candle — tallest
        (0.82, 0.05, 0.24, 0.02, 0.28, True),
    ]

    for xf, bt, bb, wt, wb, bull in candles:
        draw_candle(draw, cx(xf), cy(bt), cy(bb), cy(wt), cy(wb), half_w, bull)

    # Trend line (gold) connecting green candle body tops
    green_tops = [(cx(xf), cy(bt)) for xf, bt, bb, wt, wb, bull in candles if bull]
    if len(green_tops) >= 2:
        lw = max(2, int(S * 0.010))
        for i in range(len(green_tops) - 1):
            draw.line([green_tops[i], green_tops[i + 1]], fill=GOLD, width=lw)

    # Dashed "liquidity" level line at the sweep high
    liq_y  = cy(0.15)
    dash_w = max(2, int(S * 0.008))
    dash_len = int(S * 0.04)
    gap_len  = int(S * 0.02)
    x = chart_x0
    while x < chart_x1:
        draw.line([(x, liq_y), (min(x + dash_len, chart_x1), liq_y)],
                  fill=GOLD, width=dash_w)
        x += dash_len + gap_len

    # ── 5. "T" monogram (top-left area) ────────────────────────────────────
    T_cx  = int(S * 0.355)
    T_cy  = int(S * 0.245)
    T_r   = int(S * 0.145)            # radius of the monogram circle

    # Monogram backing circle
    aa_circle(draw,
              [T_cx - T_r, T_cy - T_r, T_cx + T_r, T_cy + T_r],
              fill=NAVY_DEEP)
    aa_circle(draw,
              [T_cx - T_r, T_cy - T_r, T_cx + T_r, T_cy + T_r],
              outline=GOLD_LIGHT, width=max(2, int(S * 0.012)))

    # Geometric "T"
    t_half  = int(T_r * 0.72)
    t_thick = max(3, int(T_r * 0.28))
    # Crossbar
    draw.rectangle(
        [T_cx - t_half, T_cy - t_half,
         T_cx + t_half, T_cy - t_half + t_thick],
        fill=GOLD_LIGHT,
    )
    # Stem
    stem_half = t_thick // 2
    draw.rectangle(
        [T_cx - stem_half, T_cy - t_half,
         T_cx + stem_half, T_cy + int(t_half * 0.75)],
        fill=GOLD_LIGHT,
    )

    # ── 6. Downscale ───────────────────────────────────────────────────────
    out = img.resize((size, size), Image.LANCZOS)
    return out


# ── Save ───────────────────────────────────────────────────────────────────────

def main():
    out_dir = os.path.join(os.path.dirname(__file__), "gui", "assets")
    os.makedirs(out_dir, exist_ok=True)

    # Render the master at 256 px; PIL will downscale to every listed size.
    # The 256-px image must be the *first* argument so electron-builder sees it.
    img_256 = render(256)
    ico_path = os.path.join(out_dir, "icon.ico")
    img_256.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)],
    )
    print(f"  OK  {ico_path}")

    # 512-px PNG for Linux and Electron notifications
    png512 = render(512)
    png_path = os.path.join(out_dir, "icon.png")
    png512.save(png_path, format="PNG")
    print(f"  OK  {png_path}")

    print("\nIcon generation complete.")
    print("Note: icon.icns (macOS) requires 'iconutil' — run on a Mac or use")
    print("      'png2icns' / 'makeicns' with the generated icon.png.")


if __name__ == "__main__":
    main()
