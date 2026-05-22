# TechnobizTrader — User Manual
**Version 1.0  |  7-Agent ICT Trading System  |  © 2026 My Digital Solutions**

---

## Table of Contents

1. [What Is TechnobizTrader?](#1-what-is-technobiztrader)
2. [First Launch & Setup](#2-first-launch--setup)
3. [The Trading Office — Layout Overview](#3-the-trading-office--layout-overview)
4. [Adding Your 7 Agents](#4-adding-your-7-agents)
5. [Entering Credentials (Settings)](#5-entering-credentials-settings)
6. [Risk & Rewards Configuration](#6-risk--rewards-configuration)
7. [Running a Trading Cycle](#7-running-a-trading-cycle)
8. [Understanding Cycle Results](#8-understanding-cycle-results)
9. [Agent Costumes & Customisation](#9-agent-costumes--customisation)
10. [Zoom, Layout & Seats](#10-zoom-layout--seats)
11. [What Each Agent Does](#11-what-each-agent-does)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. What Is TechnobizTrader?

TechnobizTrader is a **7-agent AI trading system** built on the ICT (Inner Circle Trading)
methodology. Seven specialised AI agents work in sequence every time you start a cycle:

```
  PRE-CYCLE INTELLIGENCE          CORE ICT PIPELINE
  ┌──────────────────┐            ┌────────────────────────────────────────┐
  │ Market-Regime    │            │ Trend-Master → Analyse-Master → Trader │
  │ Backtester       │──────────► │                    ▲                   │
  │ News-Sentinel    │            │            Risk-Sentinel (gate)         │
  └──────────────────┘            └────────────────────────────────────────┘
```

The app runs as a desktop application (Electron). A Python backend (FastAPI) handles all AI
agent logic and MetaTrader 5 / TradingView connectivity. You never need to touch the terminal.

---

## 2. First Launch & Setup

### What Happens When You Open the App

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│          ◉  TechnobizTrader                         │
│          7-Agent ICT Trading System                 │
│                                                     │
│  ████████████████████░░░░░░░░░░░░  Checking Python… │
│                                                     │
└─────────────────────────────────────────────────────┘
```

On **first launch** the app automatically:
1. Locates your Python installation
2. Installs required packages (`pip install -r requirements-app.txt`) — takes ~60 s
3. Starts the backend server on port 8765
4. Opens the trading office

**Requirements before first use:**
- Python 3.11+ installed and on your PATH
- MetaTrader 5 terminal installed (for live trading)
- An Anthropic Claude API key (`sk-ant-…`)

---

## 3. The Trading Office — Layout Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🏢 TECHNOBIZTRADER AGENCY — 7-AGENT ICT TRADING SYSTEM                 🕐   │
├──────────────────────────────────────────────────────────────────────────────┤
│ [-][+] │                                                          │  Usage   │
│        │  ┌──────────────────┐  ┌──────────────────┐  ┌────────┐ │  Tasks   │
│        │  │  🍽 CAFETERIA    │  │  🛋 BREAKROOM    │  │ 🏢MAIN│ │  Assign  │
│        │  │  (agents idle)   │  │  (agents idle)   │  │ OFFICE│ │  ⚙Settings│
│        │  │                  │  │                  │  │       │ │          │
│        │  └──────────────────┘  └──────────────────┘  └────────┘ │          │
│        │  ══════════════════════ HALLWAY ═══════════════════════   │          │
│        │  ┌───────┐  ┌───────┐ ║ ┌───────┐  ║  ┌───────────────┐ │          │
│        │  │🧠TREND│  │🔍ANALY│ ║ │💰TRADE│  ║  │  ⚠️  RISK    │ │          │
│        │  │       │  │       │ ║ │       │  ║  │               │ │          │
│        │  └───────┘  └───────┘ ║ └───────┘  ║  └───────────────┘ │          │
│        │  ══════════════════════ HALLWAY 2 ═════════════════════   │          │
│        │  ┌───────┐  ┌───────┐ ║ ┌───────┐  ║  ┌───────────────┐ │          │
│        │  │📊DATA │  │📰NEWS │ ║ │💼PORT │  ║  │  🚻 RESTROOM  │ │          │
│        │  │       │  │       │ ║ │ FOLIO │  ║  │               │ │          │
│        │  └───────┘  └───────┘ ║ └───────┘  ║  └───────────────┘ │          │
│        │                                                          │          │
├────────┴──────────────────────────────────────────────────────────┴──────────┤
│  + Agent │ Layout │ Seats │ Costume │ ⚖ Risk & Rewards │ Settings │          │
│                        [ EURUSD ]  [ START CYCLE ]    Cycles:0  Trades:0    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Rooms at a Glance

| Room | Purpose |
|---|---|
| **Cafeteria** | Agents idle here between cycles; pets (Whiskers & Rex) live here |
| **Breakroom** | Additional idle area (couch, TV) |
| **Main Office** | Agents spawn here when first added; conference table |
| **Restroom** | Agents wander here when idle |
| **Trend Room** | Trend-Master works here during a cycle |
| **Analyse Room** | Analyse-Master works here during a cycle |
| **Trader Room** | Trader-Master executes here during a cycle |
| **Risk Room** | Risk-Sentinel evaluates portfolio risk here |
| **Data Room** | Market-Regime agent classifies market environment here |
| **News Room** | News-Sentinel checks economic calendar here |
| **Portfolio Room** | Backtester analyses historical performance here |

---

## 4. Adding Your 7 Agents

Before running any cycle you must add agents via the **+ Agent** button in the bottom toolbar.

### Step 1 — Click "+ Agent"

```
┌─────────────────────────────────────────────────────────────┐
│  [ + Agent ]  Layout  Seats  Costume  ⚖ Risk & Rewards  ... │
└─────────────────────────────────────────────────────────────┘
        ↑ click here
```

### Step 2 — The Add Agent Modal

```
┌──────────────────────────────────────┐
│  Add New Agent                    ×  │
│                                      │
│  Agent Type:  [▼ Trend-Master    ]   │
│                                      │
│  Name:        [Trend-Master         ]│
│                                      │
│  Costume:     [▼ Default            ]│
│                                      │
│           [ Add Agent ]              │
└──────────────────────────────────────┘
```

Select the agent type from the dropdown, optionally change the name and costume, then click
**Add Agent**. The agent spawns in the Main Office and starts wandering the common areas.

### The 7 Agent Types You Need to Add

| # | Agent Type | Room | Required for Cycle? |
|---|---|---|---|
| 1 | **Trend-Master** | Trend Room | ✅ Yes |
| 2 | **Analyse-Master** | Analyse Room | ✅ Yes |
| 3 | **Trader-Master** | Trader Room | ✅ Yes |
| 4 | **Risk-Sentinel** | Risk Room | Recommended |
| 5 | **News-Sentinel** | News Room | Recommended |
| 6 | **Market-Regime** | Data Room | Recommended |
| 7 | **Backtester** | Portfolio Room | Recommended |

> **Tip:** Add all 7 for maximum protection. The minimum to start a cycle is agents 1, 2, and 3.
> Support agents (4–7) run in the backend regardless; their room animations appear only when you
> have added them.

### Removing an Agent

Click on any agent in the office to see their details popup. Use the **Remove** button.
Agents cannot be removed while a cycle is actively running.

---

## 5. Entering Credentials (Settings)

Click **⚙ Settings** in the right sidebar.

```
┌─────────────────────────────────────────────────┐
│  ⚙ Settings — Data Provider Credentials      ×  │
│                                                 │
│  ┌─────────────────────────────────────────┐    │
│  │ ✓ Backend online — credentials will be  │    │  ← green banner
│  │   saved immediately                     │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  Provider:  [▼ Claude AI (Anthropic)       ]    │
│                                                 │
│  Anthropic API Key                              │
│  [sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx    ]    │
│  Get your key at console.anthropic.com          │
│                                                 │
│  [ Save & Connect ]                             │
│                                                 │
│  ✓ Claude API key saved — agents will use it    │
└─────────────────────────────────────────────────┘
```

### Provider Options

#### Claude AI (Anthropic) — required for all AI analysis
```
  API Key:   sk-ant-api03-xxxxxxxxxxxx
  Get key:   https://console.anthropic.com/keys
```

#### MetaTrader 5 — required for live market data and trade execution
```
  Account:   12345678           ← your MT5 login number
  Password:  ••••••••••         ← your MT5 password
  Server:    ICMarkets-Live01   ← your broker's MT5 server name
```
> Find your server name in MT5 under: File → Open Account → your broker

#### TradingView — alternative data source (no execution)
```
  Username:  your_username
  Password:  ••••••••••
```

#### Telegram — optional signal broadcast to your phone
```
  Bot Token:  123456789:AABBcc...    ← from @BotFather
  Chat ID:    -100123456789          ← your group or channel ID
```
After saving Telegram, click **📡 Send Test** to verify the connection.

### Banner Colours

| Banner Colour | Meaning |
|---|---|
| 🟢 Green | Backend running, credentials will save immediately |
| 🟡 Orange | Backend running but data provider not connected yet |
| 🔴 Red | Backend not reachable — restart the application |

---

## 6. Risk & Rewards Configuration

Click **⚖ Risk & Rewards** in the bottom toolbar.

```
┌────────────────────────────────────────────────────────┐
│  ⚖ Risk & Rewards                                   ×  │
│                                                        │
│  Risk Per Trade         [●────────────]   2.0 %        │
│  Min Risk : Reward      [●────────────]   1 : 2.0      │
│  Daily Max Loss         [●────────────]   5.0 %        │
│  Signal Confidence      [●────────────]   75 %         │
│  Max Open Trades        [●────────────]   3             │
│                                                        │
│  Take Profit Split                                     │
│  TP1 [●──] 50%    TP2 [●──] 30%    TP3 (auto): 20%    │
│                                                        │
│  [ Apply Settings ]        [ Reset to Defaults ]       │
└────────────────────────────────────────────────────────┘
```

| Setting | Default | What It Controls |
|---|---|---|
| **Risk Per Trade** | 2.0% | Maximum % of account risked per trade |
| **Min Risk:Reward** | 1:2.0 | Minimum R:R ratio; signals below this are rejected |
| **Daily Max Loss** | 5.0% | Drawdown threshold — trading pauses for the day if hit |
| **Signal Confidence** | 75% | Minimum AI confidence score required to execute |
| **Max Open Trades** | 3 | Maximum simultaneous live positions |
| **TP1 Split** | 50% | Percentage of position closed at first target |
| **TP2 Split** | 30% | Percentage closed at second target |
| **TP3 (auto)** | 20% | Remaining position; trailed with a stop |

When you modify any slider click **Apply Settings**. A small green dot appears on the
**⚖ Risk & Rewards** toolbar button as a reminder that custom settings are active.
Click **Reset to Defaults** to revert all sliders to the defaults above.

---

## 7. Running a Trading Cycle

### Pre-Cycle Checklist

```
  ☐  1. Add all 7 agents (+ Agent button)
  ☐  2. Save Claude API key (⚙ Settings → Claude AI)
  ☐  3. Save MT5 credentials (⚙ Settings → MetaTrader 5)
  ☐  4. Status bar shows: ✅ Ready — select pair and click START CYCLE
  ☐  5. Enter a trading pair below (EURUSD, XAUUSD, GBPUSD …)
```

### Starting the Cycle

1. **Type your trading pair** in the input box (bottom centre):

```
  ┌──────────────────────────────────────────────────────────────┐
  │                    [ XAUUSD ]  [ START CYCLE ]               │
  └──────────────────────────────────────────────────────────────┘
```

2. Click **START CYCLE**.

3. Watch the status bar update and each agent walk to their office:

```
  🚀 Cycle started for XAUUSD
```

### Live Cycle Progress (Status Panel)

```
  ┌─────────────────────────────────────────────────────────────┐
  │  📡 Cycle Status                                            │
  │  🚀 Cycle started for XAUUSD                               │
  │  ✓ data done  regime=TRENDING  risk_mult=1.0               │
  │  ✓ portfolio done  WR=62%  PF=1.8  conf×1.05               │
  │  ✓ news done  CLEAR — next: US CPI in 4.2h                 │
  │  ✓ trend done  BULLISH  conf=81%                           │
  │  ✓ analyse done  BUY @ 2341.50  conf=82%                   │
  │  ✓ risk done  approved  adj_risk=1.8%                      │
  │  ✓ trader done  0.10 lots placed                           │
  │  🏁 Cycle complete — TRADE EXECUTED                         │
  └─────────────────────────────────────────────────────────────┘
```

### Agent Animations During the Cycle

Each agent walks from the common area to their office room, sits at their desk (working
animation), then returns to idle after their phase completes.

```
OFFICE VIEW DURING CYCLE:

  [DATA ROOM]       ← Market-Regime agent sits here first
  [PORTFOLIO ROOM]  ← Backtester agent works here second
  [NEWS ROOM]       ← News-Sentinel checks calendar third
  [TREND ROOM]      ← Trend-Master analyses macro bias fourth
  [ANALYSE ROOM]    ← Analyse-Master hunts ICT patterns fifth
  [RISK ROOM]       ← Risk-Sentinel evaluates exposure sixth
  [TRADER ROOM]     ← Trader-Master places order last
```

---

## 8. Understanding Cycle Results

### Possible Outcomes

| Outcome | Status Bar Message | Meaning |
|---|---|---|
| Trade placed | `🏁 Cycle complete — TRADE EXECUTED` | Order sent to MT5 |
| No ICT signal | `🏁 Cycle complete — no trade` | Conditions not met (normal) |
| VOLATILE block | `✗ Market-Regime VOLATILE — trading blocked` | Too risky today |
| News block | `✗ News-Sentinel blocked — NFP in 12 min` | Event too close |
| Risk block | `✗ Risk-Sentinel blocked — daily loss limit` | Portfolio protection |

### "No Signal" Is Normal

Most cycles produce **no signal**. The system requires all 4 ICT elements to align:

```
  Required simultaneously:
  ✓ Liquidity Sweep   — price takes out a recent swing high/low
  ✓ Break of Structure — market structure shifts direction
  ✓ Order Block        — institutional entry zone identified
  ✓ Pullback Entry     — price retraces into the zone

  Must also be inside a Kill Zone:
  ✓ London:   08:00 – 11:00 UTC
  ✓ New York: 13:00 – 16:00 UTC
```

Expect signals on 20–40% of cycles. Accuracy is prioritised over frequency.

### Trade Monitoring (Automatic)

After execution the Trader-Master monitors the trade in the background without any action
needed from you:

```
  Entry price         → limit order placed, waits up to 5 min for fill
  Stop Loss (hard)    → never moved against you
  TP1 (50% position)  → first target hit → close half, move SL to break-even
  TP2 (30% position)  → second target hit → close another third
  TP3 (20% remaining) → trailing stop follows price to maximise final profit
```

---

## 9. Agent Costumes & Customisation

Click **Costume** in the bottom toolbar.

```
┌──────────────────────────────────────────────────┐
│  Agent Costumes                               ×  │
│                                                  │
│  Agent:  [▼ Trader-Master              ]         │
│                                                  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │  🧍  │ │  🧍  │ │  🧍  │ │  🧍  │            │
│  │ Def  │ │ Teal │ │Orange│ │Purple│            │
│  └──────┘ └──────┘ └──────┘ └──────┘            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │  🧍  │ │  🧍  │ │  🧍  │ │  🧍  │            │
│  │Coral │ │Black │ │White │ │ ... │             │
│  │Dress │ │Tuxedo│ │ Suit │ │     │             │
│  └──────┘ └──────┘ └──────┘ └──────┘            │
│                                                  │
│  [ Apply Costume ]                               │
└──────────────────────────────────────────────────┘
```

Select the agent from the dropdown, click a costume tile to preview it, then click
**Apply Costume** to confirm. Each agent can have a different outfit.

**Available costumes:** Default (blue), Teal Hoodie, Orange Polo, Purple Blazer,
Coral Dress, Black Tuxedo, White Suit, and more.

---

## 10. Zoom, Layout & Seats

### Zoom Controls

Use the **[ − ]** and **[ + ]** buttons on the left sidebar to zoom the office in or out.
Range: 50% (zoomed out) to 200% (zoomed in).

```
  ┌────┐
  │ +  │  ← zoom in
  ├────┤
  │ −  │  ← zoom out
  └────┘
```

### Layout

The **Layout** button is reserved for future furniture customisation.

### Seats

The **Seats** button lets you review and adjust which desk position each agent uses in
their office room.

### Assign (Right Sidebar)

Click **Assign** in the right sidebar to give an agent a task label. This label
appears as a speech bubble over their head when idle.

```
┌──────────────────────────────────────────────────┐
│  Assign Task                                  ×  │
│                                                  │
│  Select Agent:  [▼ Trend-Master             ]    │
│  Task:          [▼ Analyze Market Trend     ]    │
│                                                  │
│  [ Assign ]                                      │
└──────────────────────────────────────────────────┘
```

---

## 11. What Each Agent Does

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                      COMPLETE 7-AGENT PIPELINE                          │
 │                                                                         │
 │  [DATA ROOM]        Market-Regime Agent                                 │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Reads Weekly, Daily, 4H, 1H candles                                 │
 │  • Classifies: TRENDING / RANGING / VOLATILE / TRANSITION              │
 │  • TRENDING  → full risk, proceed normally                             │
 │  • RANGING   → reduce position size (risk multiplier 0.6×)             │
 │  • VOLATILE  → HARD BLOCK — cycle stops here                           │
 │  • TRANSITION → higher confidence required                             │
 │                                                                         │
 │  [PORTFOLIO ROOM]   Backtester Agent                                    │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Reads all closed trades from the database                           │
 │  • Computes win rate by setup type, session, symbol                    │
 │  • Produces a confidence_multiplier applied to the next signal         │
 │  • Good track record → confidence boosted; poor → reduced              │
 │                                                                         │
 │  [NEWS ROOM]        News-Sentinel Agent                                 │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Checks economic calendar: NFP, FOMC, CPI, BOE, ECB, GDP            │
 │  • DANGER (event within buffer window) → HARD BLOCK                   │
 │  • CAUTION (event nearby) → warning logged, cycle continues            │
 │  • CLEAR → safe to proceed                                             │
 │                                                                         │
 │  [TREND ROOM]       Trend-Master Agent                                  │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Analyses price structure top-down: Weekly → Daily → 4H              │
 │  • Identifies swing highs/lows and key support/resistance zones        │
 │  • Output: BULLISH / BEARISH / NEUTRAL + confidence score (0–100%)     │
 │  • Passes TrendReport to Analyse-Master                                │
 │                                                                         │
 │  [ANALYSE ROOM]     Analyse-Master Agent                                │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Only activates during London (08:00–11:00 UTC) / NY (13:00–16:00)  │
 │  • Requires ALL 4 ICT elements to confirm a signal:                    │
 │      1. Liquidity Sweep — price clears recent swing high/low           │
 │      2. Break of Structure — confirms directional intent               │
 │      3. Order Block / FVG — institutional entry zone identified        │
 │      4. Pullback Entry — price returns to the zone for entry           │
 │  • Minimum 1:2 Risk:Reward required; signal valid 30 min              │
 │  • Backtester confidence_multiplier applied here                       │
 │  • No signal = cycle ends normally (not an error)                     │
 │                                                                         │
 │  [RISK ROOM]        Risk-Sentinel Agent                                 │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Checks daily drawdown < configured limit (default 5%)              │
 │  • Checks concurrent positions < max (default 3)                      │
 │  • Checks correlated pair exposure (1 position per cluster max)       │
 │  • Reduces position size after consecutive losses                     │
 │  • Applies equity-curve protection when equity dips from peak         │
 │  • Block → cycle ends without placing a trade                         │
 │                                                                         │
 │  [TRADER ROOM]      Trader-Master Agent                                 │
 │  ───────────────────────────────────────────────────────────────────    │
 │  • Zooms to 15m / 5m for LTF confirmation candle                      │
 │  • Calculates lot size dynamically:                                    │
 │      lots = (account × risk%) / (SL pips × pip_value)                 │
 │      × regime_multiplier × streak_adjustment                           │
 │  • Places MT5 limit order (retries up to 3× on failure)               │
 │  • Background monitor (every 60s):                                     │
 │      TP1 hit → close 50%, move SL to break-even                       │
 │      TP2 hit → close 30%                                              │
 │      TP3     → trail remaining 20% until stopped out                  │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Troubleshooting

### "Backend not reachable" in Settings

The Python backend server is not running. The Electron app starts it automatically on launch.
Try these steps:

1. Close and reopen the TechnobizTrader application
2. Wait up to 90 seconds for the backend to start
3. If the problem persists, open a terminal and run:
   ```
   python gui_server.py
   ```
   then open `http://127.0.0.1:8765` in your browser

### "Missing agents: Trend-Master, Analyse-Master, Trader-Master"

You must add the three core agents before a cycle can run. Click **+ Agent** and add each one.

### Cycle always produces "No signal" (no trade)

This is expected behaviour outside Kill Zone hours. Run cycles between:
- **08:00 – 11:00 UTC** (London session)
- **13:00 – 16:00 UTC** (New York session)

Also confirm your Claude API key is saved — without it, agent analysis cannot run.

### "MT5 reconnect failed"

1. Ensure MetaTrader 5 is **installed and running** on your computer
2. Re-enter your credentials in **⚙ Settings → MetaTrader 5**
3. Verify the Server name exactly matches what MT5 shows (e.g. `ICMarkets-Live01`)

### "Market-Regime VOLATILE — trading blocked"

The market's volatility (ATR) is more than 2× its long-term average. This block protects you
from erratic conditions. Wait for the session to calm and try again.

### Agents not moving / stuck

Click on any agent to open their info popup. If their status shows `working` outside a cycle,
click the **X** on the popup to dismiss and wait — they will return to idle automatically.

---

## Appendix A — Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Reload page | Ctrl + R |
| Full screen | F11 |
| Zoom in | Ctrl + = |
| Zoom out | Ctrl + − |
| Developer tools (dev build only) | Ctrl + Shift + I |

---

## Appendix B — Menu Bar

```
File                     View                  Help
──────────────────────   ──────────────────    ─────────────────────────
Open User Data Folder    Reload                User Manual
──────────────────────   Force Reload          Support (email)
Exit                     ────────────────      ─────────────────────────
                         Reset Zoom            About TechnobizTrader
                         Zoom In
                         Zoom Out
                         ────────────────
                         Toggle Full Screen
```

**File → Open User Data Folder** opens the folder where your `.env` credentials and logs live.
On Windows this is: `C:\Users\<you>\AppData\Roaming\TechnobizTrader\`

---

## Appendix C — Log Files

| File | Location | Contents |
|---|---|---|
| `backend.log` | User Data Folder | All Python backend output (agents, MT5, errors) |
| `pip-install.log` | User Data Folder | Package installation log (first launch only) |

To view logs: **File → Open User Data Folder**, then open `backend.log` in any text editor.

---

*TechnobizTrader v1.0.0 — © 2026 My Digital Solutions — erickomari243@gmail.com*

*Trading financial instruments involves substantial risk of loss. Past performance does not
guarantee future results. Always trade with capital you can afford to lose.*
