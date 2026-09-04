"""
TechnobizTrader Icon Generator — Neon Cartography
Creates a masterpiece icon representing the 7-agent ICT trading system.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
import math
import os

# ─── Palette ────────────────────────────────────────────────────────────────────
BG_DEEP      = (10,  14,  26)   # #0A0E1A — deep night background
BG_MID       = (15,  20,  40)   # #0F1428 — subtle gradient layer
INDIGO       = (26,  35, 126)   # #1A237E — deep indigo
CYAN_BRIGHT  = (0,   229, 255)  # #00E5FF — electric cyan (primary)
CYAN_DIM     = (0,   150, 200)  # dimmer cyan for secondary
GOLD         = (255, 215, 0)    # #FFD700 — authority gold
GOLD_DIM     = (200, 160, 0)    # dimmer gold
WHITE        = (255, 255, 255)  # pure white accents
SILVER       = (180, 200, 220)  # silver for subtle elements
GLOW_CYAN    = (0,   229, 255, 80)
GLOW_GOLD    = (255, 215, 0,   80)

SIZES = [
    (16,   "icon-16.png"),
    (24,   "icon-24.png"),
    (32,   "icon-32.png"),
    (48,   "icon-48.png"),
    (64,   "icon-64.png"),
    (128,  "icon-128.png"),
    (256,  "icon-256.png"),
    (512,  "icon-512.png"),
]


def hex_to_cart(hex_angle, cx, cy, radius):
    """Convert hex grid angle to cartesian coordinates (0° = top, clockwise)."""
    angle = math.radians(hex_angle - 90)
    return (
        cx + radius * math.cos(angle),
        cy + radius * math.sin(angle),
    )


def draw_glow_ring(draw, cx, cy, radius, color, glow_radius=3):
    """Draw a glowing ring."""
    for r in range(glow_radius, 0, -1):
        alpha = int(255 * (r / glow_radius) * 0.3)
        col = (*color[:3], alpha)
        draw.ellipse(
            [cx - radius - r, cy - radius - r,
             cx + radius + r, cy + radius + r],
            outline=col, width=1
        )


def draw_luminous_node(draw, cx, cy, size, color, glow_color=None, filled=True):
    """Draw a node with a multi-layer glow effect."""
    glow_r = size + 4
    if glow_color:
        for i in range(4, 0, -1):
            alpha = int(60 * (i / 4))
            col = (*glow_color[:3], alpha)
            draw.ellipse(
                [cx - glow_r - i, cy - glow_r - i,
                 cx + glow_r + i, cy + glow_r + i],
                fill=col
            )
    if filled:
        draw.ellipse(
            [cx - size, cy - size, cx + size, cy + size],
            fill=color
        )
        # Inner highlight
        hi_size = size * 0.4
        hi_col = tuple(min(255, c + 60) for c in color[:3])
        draw.ellipse(
            [cx - hi_size, cy - hi_size - 1, cx + hi_size, cy + hi_size - 1],
            fill=hi_col
        )
    else:
        draw.ellipse(
            [cx - size, cy - size, cx + size, cy + size],
            outline=color, width=2
        )


def draw_hex_grid(draw, cx, cy, outer_r, num_rings=2):
    """Draw subtle hexagonal grid lines in the background."""
    for ring in range(1, num_rings + 1):
        r = outer_r * (ring / num_rings)
        points = [hex_to_cart(a, cx, cy, r) for a in range(0, 360, 60)]
        flat = [p for pt in points for p in pt]
        alpha = int(25 * (1 - ring / (num_rings + 1)))
        col = (*CYAN_DIM[:3], alpha)
        draw.polygon(flat, outline=col, width=1)


def draw_network_lines(draw, cx, cy, center_r, outer_r, theta_offset=0):
    """Draw luminous connection threads from center to 6 outer nodes."""
    # Six directions for the agent nodes
    for i in range(6):
        angle = theta_offset + i * 60
        ox, oy = hex_to_cart(angle, cx, cy, outer_r)
        # Main line
        draw.line([cx, cy, ox, oy], fill=(*CYAN_BRIGHT[:3], 180), width=1)
        # Glow layer
        draw.line([cx, cy, ox, oy], fill=(*CYAN_BRIGHT[:3], 60), width=3)

    # Outer hexagon connections (agents connected to each other)
    outer_pts = [hex_to_cart(i * 60 + theta_offset, cx, cy, outer_r) for i in range(6)]
    for i in range(6):
        x1, y1 = outer_pts[i]
        x2, y2 = outer_pts[(i + 1) % 6]
        draw.line([x1, y1, x2, y2], fill=(*CYAN_DIM[:3], 80), width=1)


def draw_candlestick_pattern(draw, cx, cy, size, direction="up"):
    """Draw a tiny candlestick chart element in the center."""
    bar_w = size * 0.25
    body_h = size * 0.5
    wick_h = size * 0.8
    # Center node is the main candlestick
    draw.rectangle(
        [cx - bar_w, cy - body_h / 2, cx + bar_w, cy + body_h / 2],
        fill=GOLD
    )
    draw.line([cx, cy - wick_h, cx, cy - body_h / 2], fill=GOLD, width=1)
    draw.line([cx, cy + body_h / 2, cx, cy + wick_h], fill=GOLD, width=1)


def draw_outer_ring(draw, cx, cy, r, thickness=2):
    """Draw the outer containment ring with gradient glow."""
    # Dark ring
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 outline=(*INDIGO[:3], 200), width=thickness)
    # Glow
    draw.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1],
                 outline=(*CYAN_DIM[:3], 60), width=1)


def draw_tick_marks(draw, cx, cy, r, count=24):
    """Draw subtle tick marks around the outer ring (like a clock or compass)."""
    for i in range(count):
        angle = math.radians(i * (360 / count) - 90)
        inner = r - 4
        outer = r
        x1 = cx + inner * math.cos(angle)
        y1 = cy + inner * math.sin(angle)
        x2 = cx + outer * math.cos(angle)
        y2 = cy + outer * math.sin(angle)
        alpha = 80 if i % 6 == 0 else 40
        draw.line([x1, y1, x2, y2],
                  fill=(*CYAN_DIM[:3], alpha), width=1)


def create_icon(size):
    """Create a single icon at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size / 2, size / 2
    outer_radius = size * 0.45   # outermost boundary
    center_r    = size * 0.08   # center node radius
    outer_node_r = size * 0.05  # outer node radius

    # ── Background ──────────────────────────────────────────────────────────────
    # Filled dark circle
    bg_r = int(outer_radius * 1.02)
    draw.ellipse(
        [cx - bg_r, cy - bg_r, cx + bg_r, cy + bg_r],
        fill=BG_DEEP
    )

    # ── Subtle hexagonal grid ───────────────────────────────────────────────────
    draw_hex_grid(draw, cx, cy, outer_radius, num_rings=3)

    # ── Network lines ──────────────────────────────────────────────────────────
    outer_node_distance = outer_radius * 0.62
    draw_network_lines(draw, cx, cy, center_r, outer_node_distance, theta_offset=0)

    # ── Outer ring & tick marks ────────────────────────────────────────────────
    draw_outer_ring(draw, cx, cy, int(outer_radius * 0.98), thickness=max(1, size // 64))
    if size >= 64:
        draw_tick_marks(draw, cx, cy, int(outer_radius * 0.98), count=36)

    # ── Central node (gold candlestick — the "T" in Technobiz) ─────────────────
    draw_luminous_node(draw, cx, cy, int(center_r), GOLD, GOLD, filled=True)
    # Inner "T" mark — simplified candlestick
    bar_w = max(1, int(center_r * 0.25))
    bar_h = center_r * 0.5
    draw.rectangle(
        [cx - bar_w, cy - bar_h, cx + bar_w, cy + bar_h],
        fill=(255, 255, 255, 230)
    )
    draw.line([cx, cy - bar_h * 1.6, cx, cy - bar_h],
              fill=(255, 255, 255, 230), width=max(1, bar_w))
    draw.line([cx, cy + bar_h, cx, cy + bar_h * 1.6],
              fill=(255, 255, 255, 230), width=max(1, bar_w))

    # ── Outer nodes (6 agents in hexagonal constellation) ───────────────────────
    for i in range(6):
        angle = i * 60 - 90
        ox, oy = hex_to_cart(angle, cx, cy, outer_node_distance)

        # Alternate between filled cyan and outlined cyan
        filled = (i % 2 == 0)
        draw_luminous_node(draw, ox, oy, int(outer_node_r),
                          CYAN_BRIGHT, CYAN_BRIGHT, filled=filled)

        # Tiny inner dot
        dot_r = max(1, int(outer_node_r * 0.3))
        draw.ellipse([ox - dot_r, oy - dot_r, ox + dot_r, oy + dot_r],
                     fill=WHITE)

    # ── Accent: subtle radial gradient overlay ──────────────────────────────────
    # Add a very subtle vignette by drawing a dark ellipse at corners
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for i in range(3, 0, -1):
        inset = size * 0.03 * i
        alpha = int(15 * i / 3)
        overlay_draw.ellipse(
            [inset, inset, size - inset, size - inset],
            fill=(10, 14, 26, alpha)
        )
    img = Image.alpha_composite(img, overlay)

    # ── Micro detail: 7 tiny dots around the center ring ───────────────────────
    if size >= 128:
        for i in range(7):
            angle = math.radians(i * (360 / 7) - 90)
            dist = outer_radius * 0.82
            px = cx + dist * math.cos(angle)
            py = cy + dist * math.sin(angle)
            pr = max(1, size // 256)
            draw.ellipse([px - pr, py - pr, px + pr, py + pr],
                         fill=(*GOLD[:3], 180))

    return img


def create_ico():
    """Create the final icon.ico with all required sizes."""
    sizes_for_ico = [16, 24, 32, 48, 64, 128, 256]
    images = []
    for s in sizes_for_ico:
        img = create_icon(s)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        # Resize to exact size (for crispness)
        img = img.resize((s, s), Image.LANCZOS)
        images.append(img)

    output_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes_for_ico],
        append_images=images[1:],
    )
    print(f"✅ Created: {output_path}")
    return output_path


def create_png_set():
    """Export all sizes as PNG files."""
    for size, name in SIZES:
        img = create_icon(size)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        output_path = os.path.join(os.path.dirname(__file__), name)
        img.save(output_path, "PNG")
        print(f"✅ Created: {output_path}")


def create_showcase():
    """Create a large showcase PNG showing the icon at multiple sizes."""
    sizes_preview = [512, 256, 128, 64]
    padding = 32
    gap = 24
    icon_size = 256
    cols = 2
    rows = 2

    canvas_w = cols * icon_size + (cols + 1) * padding + cols * gap
    canvas_h = rows * icon_size + (rows + 1) * padding + rows * gap
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (10, 14, 26, 255))
    draw = ImageDraw.Draw(canvas)

    # Subtle background grid
    grid_spacing = 32
    for x in range(0, canvas_w, grid_spacing):
        draw.line([(x, 0), (x, canvas_h)], fill=(26, 35, 126, 30), width=1)
    for y in range(0, canvas_h, grid_spacing):
        draw.line([(0, y), (canvas_w, y)], fill=(26, 35, 126, 30), width=1)

    for idx, size in enumerate(sizes_preview):
        img = create_icon(icon_size)
        row = idx // cols
        col = idx % cols
        x = padding + col * (icon_size + gap)
        y = padding + row * (icon_size + gap)
        canvas.paste(img, (x, y), img)

    # Label
    try:
        label_font = ImageFont.truetype(
            os.path.join(os.path.dirname(__file__), "..", "..", "..",
                         ".claude", "skills", "canvas-design", "canvas-fonts",
                         "JetBrainsMono-Bold.ttf"),
            14
        )
    except Exception:
        label_font = ImageFont.load_default()

    label = "TechnobizTrader  •  Neon Cartography  •  7-Agent ICT System"
    lw, lh = draw.textbbox((0, 0), label, font=label_font)[2:]
    draw.text(
        ((canvas_w - lw) // 2, canvas_h - padding - lh),
        label, font=label_font, fill=(0, 229, 255, 150)
    )

    output_path = os.path.join(os.path.dirname(__file__), "icon_showcase.png")
    canvas.save(output_path, "PNG")
    print(f"✅ Created showcase: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Generating TechnobizTrader icon (Neon Cartography)...")
    create_ico()
    create_png_set()
    create_showcase()
    print("\n🎉 All icons generated successfully!")
