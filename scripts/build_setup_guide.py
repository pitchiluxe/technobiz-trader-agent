"""Generate the TechnobizTrader Setup & Connection Guide PDF.

Run:  python scripts/build_setup_guide.py
Output: docs/TechnobizTrader_Setup_Guide.pdf
"""

from pathlib import Path

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "TechnobizTrader_Setup_Guide.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Palette
GOLD       = HexColor("#FFD700")
DARK_BLUE  = HexColor("#1a1a2e")
MID_BLUE   = HexColor("#2a2a3e")
GREEN      = HexColor("#4CAF50")
RED        = HexColor("#f44336")
ORANGE     = HexColor("#ff9800")
GREY_TXT   = HexColor("#3a3a3a")
LIGHT_GREY = HexColor("#dddddd")
ROOM_KIT   = HexColor("#f3e5cd")
ROOM_HALL  = HexColor("#4a4a55")
ROOM_OFC   = HexColor("#7a8fa0")
ROOM_BR    = HexColor("#e0c9a8")
ROOM_MAIN  = HexColor("#b89466")
ROOM_REST  = HexColor("#d8e6ec")

PAGE_W, PAGE_H = letter
MARGIN = 0.6 * inch


def header(c, title, page_num):
    """Top banner + page footer."""
    c.setFillColor(DARK_BLUE)
    c.rect(0, PAGE_H - 0.55 * inch, PAGE_W, 0.55 * inch, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, PAGE_H - 0.36 * inch, "TechnobizTrader  —  Setup & Connection Guide")
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.36 * inch, title)

    c.setFillColor(GREY_TXT)
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, 0.35 * inch,
                        f"TechnobizTrader  ·  Setup Guide  ·  Page {page_num}")
    c.setStrokeColor(LIGHT_GREY)
    c.setLineWidth(0.5)
    c.line(MARGIN, 0.55 * inch, PAGE_W - MARGIN, 0.55 * inch)


def heading(c, y, text, size=15):
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", size)
    c.drawString(MARGIN, y, text)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.line(MARGIN, y - 4, MARGIN + 1.2 * inch, y - 4)
    return y - 0.32 * inch


def body(c, y, text, size=10.5, color=GREY_TXT, leading=14, indent=0):
    """Wrap text into lines that fit the page width."""
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    max_w = PAGE_W - 2 * MARGIN - indent
    words = text.split(" ")
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, "Helvetica", size) <= max_w:
            line = test
        else:
            c.drawString(MARGIN + indent, y, line)
            y -= leading
            line = w
    if line:
        c.drawString(MARGIN + indent, y, line)
        y -= leading
    return y


def code(c, y, text, color_bg=MID_BLUE, color_fg=GOLD):
    """Render a single-line code/command box."""
    c.setFillColor(color_bg)
    c.roundRect(MARGIN, y - 18, PAGE_W - 2 * MARGIN, 22, 3, stroke=0, fill=1)
    c.setFillColor(color_fg)
    c.setFont("Courier-Bold", 10)
    c.drawString(MARGIN + 8, y - 12, text)
    return y - 30


def bullet(c, y, text, size=10.5):
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN + 2, y, "•")
    return body(c, y, text, size=size, indent=14)


def step_callout(c, y, n, title, lines):
    """Draw a numbered-step block with a gold circle."""
    box_h = 18 + 14 * len(lines)
    c.setFillColor(MID_BLUE)
    c.roundRect(MARGIN, y - box_h, PAGE_W - 2 * MARGIN, box_h, 4, stroke=0, fill=1)
    # number circle
    c.setFillColor(GOLD)
    c.circle(MARGIN + 16, y - 14, 11, stroke=0, fill=1)
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(MARGIN + 16, y - 18, str(n))
    # title
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN + 36, y - 16, title)
    # body
    c.setFillColor(white)
    c.setFont("Helvetica", 10)
    yy = y - 30
    for ln in lines:
        c.drawString(MARGIN + 36, yy, ln)
        yy -= 13
    return y - box_h - 10


def arrow(c, x1, y1, x2, y2, color=DARK_BLUE):
    c.setStrokeColor(color)
    c.setLineWidth(1.4)
    c.line(x1, y1, x2, y2)
    # arrow head
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    s = 6
    c.line(x2, y2, x2 - s * math.cos(ang - math.pi / 8), y2 - s * math.sin(ang - math.pi / 8))
    c.line(x2, y2, x2 - s * math.cos(ang + math.pi / 8), y2 - s * math.sin(ang + math.pi / 8))


def labeled_box(c, x, y, w, h, label, fill=ROOM_OFC, fg=DARK_BLUE, font_size=10):
    c.setFillColor(fill)
    c.setStrokeColor(DARK_BLUE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 3, stroke=1, fill=1)
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", font_size)
    c.drawCentredString(x + w / 2, y + h / 2 - 4, label)


# ─────────────────────────────────────────────────────────────────────────────
# Page builders
# ─────────────────────────────────────────────────────────────────────────────

def page_title(c):
    # Background banner
    c.setFillColor(DARK_BLUE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    # Gold accent bar
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 1.4 * inch, PAGE_W, 0.08 * inch, stroke=0, fill=1)
    c.rect(0, 1.4 * inch, PAGE_W, 0.08 * inch, stroke=0, fill=1)

    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 0.6 * inch, "TechnobizTrader")
    c.setFont("Helvetica", 18)
    c.setFillColor(white)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 0.2 * inch, "Setup & Connection Guide")

    c.setFillColor(GOLD)
    c.setFont("Helvetica-Oblique", 12)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 0.2 * inch,
                        "Multi-Agent ICT Trading System with GUI")

    # Mini agency logo (3 silhouettes inside a building outline)
    cx, cy = PAGE_W / 2, PAGE_H / 2 - 1.2 * inch
    c.setStrokeColor(GOLD)
    c.setFillColor(MID_BLUE)
    c.setLineWidth(2)
    c.roundRect(cx - 90, cy - 50, 180, 80, 6, stroke=1, fill=1)
    for i, label in enumerate(("T", "A", "X")):
        x = cx - 60 + i * 60
        c.setFillColor(GOLD)
        c.circle(x, cy + 6, 11, stroke=0, fill=1)
        c.setFillColor(DARK_BLUE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x, cy + 2, label)
        c.setFillColor(GOLD)
        c.rect(x - 6, cy - 22, 12, 20, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica", 9)
    c.drawCentredString(cx, cy - 38, "Trend-Master  →  Analyse-Master  →  Trader-Master")

    c.setFillColor(white)
    c.setFont("Helvetica", 11)
    c.drawCentredString(PAGE_W / 2, 1.0 * inch, "Document version 1.0  ·  May 5, 2026")
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(GOLD)
    c.drawCentredString(PAGE_W / 2, 0.7 * inch,
                        "Liquidity Sweep · Break of Structure · Imbalance/Order Block · Pullback Entry")
    c.showPage()


def page_overview(c, page_num):
    header(c, "1. System Overview", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "1.  System Overview")
    y = body(c, y,
        "TechnobizTrader is a multi-agent trading system that pairs an interactive office "
        "GUI (rendered in your browser) with a real Python backend running the ICT "
        "(Inner Circle Trading) pipeline. Click START CYCLE in the GUI and three specialist "
        "agents — Trend-Master, Analyse-Master, Trader-Master — execute one full cycle "
        "against live MT5 market data. Optional Telegram broadcast lets you push every "
        "validated signal to a channel, group, or DM.")
    y -= 0.1 * inch

    # Architecture diagram
    diagram_top = y - 0.1 * inch
    diagram_h = 2.7 * inch
    c.setStrokeColor(LIGHT_GREY)
    c.setFillColor(HexColor("#fafafa"))
    c.roundRect(MARGIN, diagram_top - diagram_h, PAGE_W - 2 * MARGIN, diagram_h, 6, stroke=1, fill=1)

    cx = PAGE_W / 2
    # Browser
    labeled_box(c, MARGIN + 20, diagram_top - 0.7 * inch, 1.7 * inch, 0.5 * inch,
                "Browser", fill=GOLD, fg=DARK_BLUE)
    c.setFont("Helvetica", 8)
    c.setFillColor(GREY_TXT)
    c.drawString(MARGIN + 24, diagram_top - 0.95 * inch,
                 "minecraft_trading_office.html")

    # FastAPI
    labeled_box(c, cx - 0.85 * inch, diagram_top - 0.7 * inch, 1.7 * inch, 0.5 * inch,
                "FastAPI server", fill=MID_BLUE, fg=GOLD)
    c.setFont("Helvetica", 8); c.setFillColor(GREY_TXT)
    c.drawCentredString(cx, diagram_top - 0.95 * inch, "gui_server.py  +  SSE")

    # Agents box
    labeled_box(c, PAGE_W - MARGIN - 1.7 * inch - 20, diagram_top - 0.7 * inch,
                1.7 * inch, 0.5 * inch, "Trading Agents", fill=DARK_BLUE, fg=GOLD)
    c.setFont("Helvetica", 8); c.setFillColor(GREY_TXT)
    c.drawCentredString(PAGE_W - MARGIN - 1.7 * inch / 2 - 20, diagram_top - 0.95 * inch,
                        "Trend → Analyse → Trader")

    # Arrows browser <-> server <-> agents
    arrow(c, MARGIN + 20 + 1.7 * inch, diagram_top - 0.45 * inch,
          cx - 0.85 * inch, diagram_top - 0.45 * inch)
    arrow(c, cx - 0.85 * inch, diagram_top - 0.45 * inch + 6,
          MARGIN + 20 + 1.7 * inch, diagram_top - 0.45 * inch + 6, color=GREEN)
    arrow(c, cx + 0.85 * inch, diagram_top - 0.45 * inch,
          PAGE_W - MARGIN - 1.7 * inch - 20, diagram_top - 0.45 * inch)
    arrow(c, PAGE_W - MARGIN - 1.7 * inch - 20, diagram_top - 0.45 * inch + 6,
          cx + 0.85 * inch, diagram_top - 0.45 * inch + 6, color=GREEN)

    # External services row
    y2 = diagram_top - 1.7 * inch
    labeled_box(c, cx - 1.6 * inch, y2, 1.4 * inch, 0.45 * inch, "MT5 Terminal",
                fill=ROOM_OFC, fg=DARK_BLUE)
    labeled_box(c, cx + 0.2 * inch, y2, 1.4 * inch, 0.45 * inch, "Telegram",
                fill=HexColor("#5b9bd5"), fg=white)

    # Connectors agents -> services
    arrow(c, PAGE_W - MARGIN - 1.7 * inch / 2 - 20, diagram_top - 0.7 * inch,
          cx - 0.9 * inch, y2 + 0.45 * inch)
    arrow(c, PAGE_W - MARGIN - 1.7 * inch / 2 - 20, diagram_top - 0.7 * inch,
          cx + 0.9 * inch, y2 + 0.45 * inch)

    c.setFillColor(GREY_TXT)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(cx, y2 - 14,
                        "Browser ↔ Server messages stream over Server-Sent Events (SSE).")
    c.showPage()


def page_prereqs(c, page_num):
    header(c, "2. Prerequisites", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "2.  Prerequisites")
    y = body(c, y, "Before you start, make sure the following are in place:")
    y -= 6
    y = bullet(c, y, "Python 3.10 or newer (Windows recommended for MT5 support).")
    y = bullet(c, y, "MetaTrader 5 desktop terminal installed, with valid broker credentials and "
                     "the terminal logged in. Required only when you actually want to trade.")
    y = bullet(c, y, "(Optional) A Telegram bot — create one by chatting with @BotFather on "
                     "Telegram, then add the bot to your channel or group as an admin.")
    y = bullet(c, y, "(Optional) The numeric Chat ID of the destination channel, group, or DM. "
                     "For channels this is typically a negative number like  -1001234567890.")
    y -= 0.15 * inch

    # Quick-start callout
    c.setFillColor(MID_BLUE)
    c.roundRect(MARGIN, y - 1.0 * inch, PAGE_W - 2 * MARGIN, 1.0 * inch, 6, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(MARGIN + 14, y - 22, "What we'll build in 8 steps")
    c.setFillColor(white)
    c.setFont("Helvetica", 10)
    txt = ("Install dependencies → run the backend → open the browser → enter MT5 + Telegram "
           "credentials → spawn the 3 ICT agents → assign tasks → press START CYCLE → watch them "
           "walk through the office and log every trade in real time.")
    yy = y - 40
    for line in wrap_text(c, txt, "Helvetica", 10, PAGE_W - 2 * MARGIN - 28):
        c.drawString(MARGIN + 14, yy, line)
        yy -= 13
    c.showPage()


def wrap_text(c, text, font, size, max_w):
    out = []
    line = ""
    for w in text.split(" "):
        test = (line + " " + w).strip()
        if c.stringWidth(test, font, size) <= max_w:
            line = test
        else:
            out.append(line)
            line = w
    if line:
        out.append(line)
    return out


def page_steps_install(c, page_num):
    header(c, "3. Install & Run", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "3.  Install & Run")

    y = body(c, y, "Steps 1 and 2 set up the backend. Run them once per machine.")
    y -= 6

    y = step_callout(c, y, 1, "Install dependencies",
                     ["Open a terminal in the project folder, then run:"])
    y = code(c, y, "pip install -r requirements.txt")
    y = body(c, y, "If your requirements.txt does not yet include the GUI dependencies, also run:")
    y = code(c, y, "pip install fastapi uvicorn sse-starlette httpx python-dotenv reportlab")
    y -= 6

    y = step_callout(c, y, 2, "Start the backend server",
                     ["From the same folder, launch:"])
    y = code(c, y, "python gui_server.py")
    y = body(c, y, "On startup the server connects to MT5, builds the three trading agents, and "
                   "begins listening on:")
    y = code(c, y, "http://127.0.0.1:8765", color_bg=DARK_BLUE, color_fg=GREEN)
    y -= 4
    y = body(c, y, "If MT5 is not yet running, the server still starts — you'll be able to enter "
                   "credentials in the GUI, and the connection will be retried automatically.")

    y = step_callout(c, y, 3, "Open the GUI",
                     ["Open the URL above in any modern browser.",
                      "The office floor will be empty at first.",
                      "The status panel (bottom-right) will read \"Ready\"",
                      "or briefly \"Initializing services...\" while it connects."])
    c.showPage()


def page_step_mt5(c, page_num):
    header(c, "4. Connect MT5", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "4.  Connect MetaTrader 5")
    y = body(c, y,
             "Click the gold ⚙ Settings button in the right sidebar of the GUI to open the "
             "credentials modal. Choose MetaTrader 5 from the Provider dropdown and fill in:")
    y -= 4
    y = bullet(c, y, "Account Number — your MT5 login id, e.g.  12345678")
    y = bullet(c, y, "Password — your MT5 trading or investor password.")
    y = bullet(c, y, "Server — the broker server name shown in the MT5 terminal.")
    y -= 6
    y = body(c, y, "Click Save & Connect. The status panel will switch to Ready when the link "
                   "is established.")

    # Modal mockup
    mx, my, mw, mh = MARGIN + 0.6 * inch, y - 3.1 * inch, 4.6 * inch, 2.7 * inch
    c.setFillColor(MID_BLUE)
    c.setStrokeColor(GOLD)
    c.setLineWidth(2)
    c.roundRect(mx, my, mw, mh, 6, stroke=1, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(mx + 14, my + mh - 22, "⚙  Settings — Data Provider Credentials")
    c.setStrokeColor(GOLD)
    c.line(mx + 14, my + mh - 30, mx + mw - 14, my + mh - 30)

    def field(label, placeholder, yfield):
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(mx + 18, yfield, label)
        c.setFillColor(DARK_BLUE)
        c.setStrokeColor(GOLD)
        c.roundRect(mx + 18, yfield - 22, mw - 36, 18, 3, stroke=1, fill=1)
        c.setFillColor(HexColor("#888"))
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(mx + 24, yfield - 16, placeholder)

    field("Provider", "MetaTrader 5", my + mh - 60)
    field("Account Number", "12345678", my + mh - 110)
    field("Password", "••••••••", my + mh - 160)
    field("Server", "BrokerName-Server", my + mh - 210)

    # Save button
    bx, by = mx + 18, my + 22
    c.setFillColor(GREEN)
    c.roundRect(bx, by, 110, 24, 3, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(bx + 55, by + 8, "Save & Connect")

    c.showPage()


def page_step_telegram(c, page_num):
    header(c, "5. Connect Telegram", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "5.  (Optional) Connect Telegram for signal broadcast")
    y = body(c, y,
             "When Telegram is configured, every TradeSignal generated by the Analyse-Master "
             "is broadcast as a SIGNAL ALERT message — even if your Trader-Master later "
             "rejects the signal for risk-management reasons. Setup is the same modal, with "
             "Provider set to Telegram (signal broadcast).")
    y -= 6
    y = bullet(c, y, "Bot Token — issued by @BotFather when you run /newbot. Paste it whole, "
                     "e.g.  123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11.")
    y = bullet(c, y, "Chat ID — destination channel/group/DM id. Use a userinfo bot or call "
                     "the Telegram API getUpdates to find yours.")
    y -= 4

    # Telegram message preview
    px, py, pw, ph = MARGIN, y - 3.5 * inch, PAGE_W - 2 * MARGIN, 3.4 * inch
    c.setFillColor(HexColor("#fafafa"))
    c.setStrokeColor(LIGHT_GREY)
    c.roundRect(px, py, pw, ph, 6, stroke=1, fill=1)
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(px + 14, py + ph - 20, "Example broadcast — what subscribers receive:")
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#cfd8dc"))
    msg_x, msg_y, msg_w, msg_h = px + 22, py + 22, pw - 44, ph - 56
    c.roundRect(msg_x, msg_y, msg_w, msg_h, 8, stroke=1, fill=1)

    c.setFillColor(RED)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(msg_x + 14, msg_y + msg_h - 22, "🚨  SIGNAL ALERT  🚨")

    rows = [
        ("🌐  #XAUUSD",                                 black,  "Helvetica-Bold", 11),
        ("📊  Trade Details:  📉  #SELL",                black,  "Helvetica",      11),
        ("⚪  Entry Point:  4695",                       black,  "Helvetica",      10),
        ("🔴  Stop Loss (SL):  4703",                    RED,    "Helvetica",      10),
        ("⚪  Take Profit 1 (TP1):  4692",               black,  "Helvetica",      10),
        ("⚪  Take Profit 2 (TP2):  4687",               black,  "Helvetica",      10),
        ("⚪  Take Profit 3 (TP3):  4679",               black,  "Helvetica",      10),
        ("⚠  Risk no more than 1-2% of your balance.",  ORANGE, "Helvetica-Oblique", 9),
    ]
    yy = msg_y + msg_h - 46
    for text, col, font, size in rows:
        c.setFillColor(col)
        c.setFont(font, size)
        c.drawString(msg_x + 14, yy, text)
        yy -= 16
    c.showPage()


def page_step_agents(c, page_num):
    header(c, "6-7. Agents & Tasks", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "6.  Add the three core agents")
    y = body(c, y,
             "Click the +Agent toolbar button. In the modal, choose Role to spawn the matching "
             "core agent — each one walks into the Main Office (top-right) where they idle "
             "until tasked.")
    y -= 4
    y = bullet(c, y, "🧠 Trend-Master  → goes to the Trend room when the cycle starts.")
    y = bullet(c, y, "🔍 Analyse-Master → goes to the Analyse room.")
    y = bullet(c, y, "💰 Trader-Master → goes to the Trader room.")
    y -= 6
    y = body(c, y, "Pick any costume; the role is what assigns the office. While idle the "
                   "agents will wander the Main Office, sit at the conference table, take "
                   "coffee breaks in the kitchen, or use the restroom.")
    y -= 0.15 * inch

    y = heading(c, y, "7.  Assign tasks")
    y = body(c, y,
             "Click Assign on the right sidebar. For each agent pick the recommended task "
             "(Analyze Market Trend / Detect ICT Patterns / Execute Trade) and click Assign Task. "
             "Once all three agents are tasked you're ready to run a cycle.")
    y -= 6
    # Three role chips
    chip_w, chip_h = 1.6 * inch, 0.45 * inch
    chip_y = y - 0.7 * inch
    chip_xs = [MARGIN + 0.2 * inch,
               MARGIN + 0.2 * inch + chip_w + 0.2 * inch,
               MARGIN + 0.2 * inch + 2 * (chip_w + 0.2 * inch)]
    labels = [("🧠 Trend-Master", ROOM_KIT),
              ("🔍 Analyse-Master", ROOM_OFC),
              ("💰 Trader-Master", HexColor("#6a8aaa"))]
    for x, (lbl, col) in zip(chip_xs, labels):
        labeled_box(c, x, chip_y, chip_w, chip_h, lbl, fill=col, fg=DARK_BLUE)
    c.showPage()


def page_step_cycle(c, page_num):
    header(c, "8. Run a Cycle", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "8.  Run a cycle")
    y = body(c, y,
             "In the bottom toolbar, type the trading pair (e.g. EURUSD or XAUUSD) and click "
             "START CYCLE. The backend immediately runs the real ICT pipeline and the GUI "
             "mirrors each phase in real time:")
    y -= 4
    y = bullet(c, y, "Trend-Master walks out of the Main Office, through the hallway, and into "
                     "the Trend room. They sit, the door closes, and the arms-typing animation "
                     "kicks in while the agent's analyze() method runs server-side.")
    y = bullet(c, y, "When the trend phase is complete the agent stands up, exits, and the "
                     "baton passes to Analyse-Master, who repeats the routine.")
    y = bullet(c, y, "If the Analyse-Master generates a TradeSignal, the server immediately "
                     "broadcasts a SIGNAL ALERT to Telegram (if configured).")
    y = bullet(c, y, "Trader-Master walks in last, evaluates risk, and either executes the trade "
                     "via MT5 or rejects it. The status panel shows direction, RR, ticket id.")
    y -= 0.15 * inch

    # Cycle flow diagram
    diag_top = y
    diag_h = 2.6 * inch
    c.setFillColor(HexColor("#fafafa"))
    c.setStrokeColor(LIGHT_GREY)
    c.roundRect(MARGIN, diag_top - diag_h, PAGE_W - 2 * MARGIN, diag_h, 6, stroke=1, fill=1)

    box_w, box_h = 1.5 * inch, 0.7 * inch
    bx_y = diag_top - 1.0 * inch
    spacing = (PAGE_W - 2 * MARGIN - 3 * box_w) / 4
    boxes = [
        ("🧠 Trend-Master",    HexColor("#9d7e67"), white),
        ("🔍 Analyse-Master",  ROOM_OFC,            DARK_BLUE),
        ("💰 Trader-Master",   HexColor("#6a8aaa"), white),
    ]
    xs = []
    for i, (lbl, fill, fg) in enumerate(boxes):
        x = MARGIN + spacing + i * (box_w + spacing)
        xs.append(x)
        labeled_box(c, x, bx_y, box_w, box_h, lbl, fill=fill, fg=fg, font_size=11)

    # Arrows between agents
    for i in range(2):
        arrow(c, xs[i] + box_w, bx_y + box_h / 2, xs[i + 1], bx_y + box_h / 2)

    # Branches: Analyse → Telegram, Trader → MT5
    tb_x = xs[1] + box_w / 2
    labeled_box(c, tb_x - 0.7 * inch, bx_y - 1.0 * inch, 1.4 * inch, 0.45 * inch,
                "Telegram", fill=HexColor("#5b9bd5"), fg=white)
    arrow(c, tb_x, bx_y, tb_x, bx_y - 0.55 * inch, color=HexColor("#5b9bd5"))

    mt_x = xs[2] + box_w / 2
    labeled_box(c, mt_x - 0.7 * inch, bx_y - 1.0 * inch, 1.4 * inch, 0.45 * inch,
                "MT5 Order", fill=GREEN, fg=white)
    arrow(c, mt_x, bx_y, mt_x, bx_y - 0.55 * inch, color=GREEN)

    c.setFillColor(GREY_TXT)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(PAGE_W / 2, diag_top - diag_h + 14,
                        "Each box's Server-Sent Event drives the on-screen agent to walk, sit, work, and exit.")
    c.showPage()


def page_layout_map(c, page_num):
    header(c, "9. Office Layout Map", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "9.  Office layout map")
    y = body(c, y,
             "The diagram below mirrors the GUI floor plan. Two narrow vertical hallways "
             "and one wide main hallway connect every room — agents always travel through "
             "doors, never through walls.")
    y -= 0.1 * inch

    # Layout grid
    map_top = y - 0.1 * inch
    map_h = 4.4 * inch
    map_w = PAGE_W - 2 * MARGIN
    c.setFillColor(HexColor("#0f0f1e"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.roundRect(MARGIN, map_top - map_h, map_w, map_h, 6, stroke=1, fill=1)

    # 6 cols, 3 rows ratios
    col_ratios = [1.6, 0.3, 1.6, 0.32, 1.1, 1.0]
    total_c = sum(col_ratios)
    row_ratios = [1.0, 0.22, 1.0]
    total_r = sum(row_ratios)
    inner_pad = 6
    inner_w = map_w - 2 * inner_pad
    inner_h = map_h - 2 * inner_pad

    col_w = [r / total_c * inner_w for r in col_ratios]
    row_h = [r / total_r * inner_h for r in row_ratios]
    col_x = [MARGIN + inner_pad]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)
    row_y = [map_top - inner_pad - row_h[0]]
    for h in row_h[1:]:
        row_y.append(row_y[-1] - h)

    def cell(col, row, span_cols=1, span_rows=1, fill=ROOM_OFC, label="", fg=DARK_BLUE):
        x = col_x[col]
        y0 = row_y[row + span_rows - 1]
        w = sum(col_w[col:col + span_cols])
        h = sum(row_h[row:row + span_rows])
        c.setFillColor(fill); c.setStrokeColor(DARK_BLUE)
        c.setLineWidth(0.8)
        c.roundRect(x + 1, y0 + 1, w - 2, h - 2, 3, stroke=1, fill=1)
        c.setFillColor(fg)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + w / 2, y0 + h / 2 - 4, label)

    # Top row
    cell(0, 0, span_cols=3, fill=ROOM_KIT, label="🍳 KITCHEN")
    cell(3, 0, span_rows=3, fill=ROOM_HALL, label="HALL", fg=white)
    cell(4, 0, fill=ROOM_BR, label="🛋 BREAKROOM")
    cell(5, 0, fill=ROOM_MAIN, label="🏢 MAIN OFFICE", fg=white)
    # Middle row (main hallway spans all)
    cell(0, 1, span_cols=6, fill=ROOM_HALL, label="◀  MAIN HALLWAY  ▶", fg=white)
    # Bottom row
    cell(0, 2, fill=ROOM_OFC, label="🧠 TREND")
    cell(1, 2, fill=ROOM_HALL, label="HALL", fg=white)
    cell(2, 2, fill=ROOM_OFC, label="🔍 ANALYSE")
    cell(4, 2, fill=ROOM_OFC, label="💰 TRADER")
    cell(5, 2, fill=ROOM_REST, label="🚻 RESTROOM")

    # Pets
    cat_x = col_x[0] + col_w[0] * 0.5
    cat_y = row_y[0] + row_h[0] * 0.4
    c.setFillColor(HexColor("#f5a637"))
    c.circle(cat_x, cat_y, 5, stroke=0, fill=1)
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica", 7)
    c.drawString(cat_x + 7, cat_y - 2, "Whiskers")

    dog_x = col_x[1] + col_w[1] * 0.5 + col_w[2] * 0.6
    dog_y = row_y[0] + row_h[0] * 0.55
    c.setFillColor(HexColor("#8b5a2b"))
    c.circle(dog_x, dog_y, 5, stroke=0, fill=1)
    c.setFillColor(DARK_BLUE)
    c.setFont("Helvetica", 7)
    c.drawString(dog_x + 7, dog_y - 2, "Rex")

    # Legend
    legend_y = map_top - map_h - 14
    c.setFillColor(GREY_TXT)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(PAGE_W / 2, legend_y,
                        "Pets wander the kitchen avoiding furniture. Restroom is single-occupancy "
                        "(toilet lid opens & closes; agents wash hands at the sink).")
    c.showPage()


def page_troubleshoot(c, page_num):
    header(c, "10. Troubleshooting", page_num)
    y = PAGE_H - 1.0 * inch
    y = heading(c, y, "10.  Troubleshooting")
    y = body(c, y, "If something does not behave as expected, walk through this list before "
                   "anything else.")
    y -= 6

    issues = [
        ("Backend not running",
         "The browser shows \"Service temporarily unavailable\" or the status panel never "
         "leaves \"Initializing services...\". Restart the backend with:  python gui_server.py."),
        ("MT5 not connected",
         "The status panel says MT5 is not connected. Check that (a) the MT5 desktop terminal "
         "is open and logged in; (b) the credentials in Settings → MT5 match your broker; "
         "(c) Algo Trading is enabled in MT5 (the icon in the toolbar should be green)."),
        ("No signal generated",
         "Cycle finishes without a trade. This is normal — the Analyse-Master only emits a "
         "TradeSignal when ALL four ICT conditions (Sweep, BoS, Imbalance/OB, Pullback) are "
         "satisfied. Most cycles will not produce a signal."),
        ("Telegram not posting",
         "Check the bot token (re-issue with /token in @BotFather if needed). Make sure the "
         "bot is added to the destination channel as an admin and that the chat id is correct."),
        ("Cycle fails immediately",
         "Usually means one of the three core agents was not added before pressing START "
         "CYCLE. Use +Agent to spawn Trend-Master, Analyse-Master, and Trader-Master first."),
    ]
    for title, desc in issues:
        c.setFillColor(GOLD)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(MARGIN, y, "▸  " + title)
        y -= 14
        y = body(c, y, desc, indent=12, color=GREY_TXT, leading=13)
        y -= 6

    # Footer note
    y -= 0.1 * inch
    c.setFillColor(MID_BLUE)
    c.roundRect(MARGIN, y - 0.7 * inch, PAGE_W - 2 * MARGIN, 0.7 * inch, 6, stroke=0, fill=1)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN + 14, y - 22, "Need a fresh start?")
    c.setFillColor(white)
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN + 14, y - 38,
                 "Stop the server (Ctrl+C), refresh the browser, then re-run python gui_server.py.")
    c.drawString(MARGIN + 14, y - 52,
                 "All credentials persist in .env so you only need to enter them once.")
    c.showPage()


# ─────────────────────────────────────────────────────────────────────────────

def build():
    c = pdfcanvas.Canvas(str(OUT), pagesize=letter)
    c.setTitle("TechnobizTrader — Setup & Connection Guide")
    c.setAuthor("TechnobizTrader")

    page_title(c)                    # 1
    page_overview(c, 2)              # 2
    page_prereqs(c, 3)               # 3
    page_steps_install(c, 4)         # 4
    page_step_mt5(c, 5)              # 5
    page_step_telegram(c, 6)         # 6
    page_step_agents(c, 7)           # 7
    page_step_cycle(c, 8)            # 8
    page_layout_map(c, 9)            # 9
    page_troubleshoot(c, 10)         # 10

    c.save()
    print(f"Wrote: {OUT}")


if __name__ == "__main__":
    build()
