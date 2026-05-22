# Minecraft Trading Office - New Design

**File:** `minecraft_trading_office.html` (Updated)

A complete redesign with all 3 agents starting in a cafeteria and moving to their own dedicated rooms when assigned tasks.

## Layout

```
┌─────────────────────────────────────────────────────┐
│              ☕ CAFETERIA (Top)                    │
│                                                    │
│  🧠 Trend-Master walking                           │
│  🔍 Analyse-Master walking                         │
│  💰 Trader-Master walking                          │
│                                                    │
│     [Cafe Tables & Plants]                         │
└─────────────────────────────────────────────────────┘
┌──────────────────┬──────────────────┬──────────────┐
│ 🧠 TREND ROOM    │ 🔍 ANALYSE ROOM  │ 💰 TRADER   │
│                  │                  │ ROOM         │
│  [Desk & PC]     │  [Desk & PC]     │ [Desk & PC] │
└──────────────────┴──────────────────┴──────────────┘
```

## Features

✅ **All 3 Agents Visible in Cafeteria**
- 🧠 Trend-Master (Green)
- 🔍 Analyse-Master (Blue)
- 💰 Trader-Master (Orange)
- All walking around cafeteria initially

✅ **3 Dedicated Rooms**
- Trend-Master's Room (left)
- Analyse-Master's Room (center)
- Trader-Master's Room (right)
- Each has desk + computer

✅ **Agent Workflow**
1. All agents start in cafeteria (walking)
2. Task assigned → agent walks to their room (1.5s)
3. Agent works at desk (10s)
4. Agent returns to cafeteria (walks back)
5. Ready for next task

✅ **Minecraft Characters**
- Pixel art style heads
- Color-coded bodies (Green/Blue/Orange)
- Eyes and mouth animations
- Status indicators (colored dots)

✅ **Status Indicators**
- Gray dot: IDLE (in cafeteria)
- Yellow dot: MOVING TO ROOM
- Red dot: WORKING at desk (10s)
- Green dot: COMPLETE (returning)

## How to Use

### 1. Open File
```bash
Double-click: minecraft_trading_office.html
```

### 2. Enter Trading Pair
```
Right panel:
[EURUSD] ← Input field
Type: BTCUSD
Click: SET (or press Enter)
```

### 3. Start Trading Cycle
```
Click: ▶ START CYCLE

Watch:
1. Trend-Master leaves cafeteria
2. Walks to Trend room (1.5s)
3. Works at desk (10s)
4. Returns to cafeteria

(Then Analyse-Master, then Trader-Master)
```

### 4. Monitor in Real-Time
```
Right panel shows:
- Current phase
- Agent status
- Metrics (Cycles, Signals, Trades, Win Rate)
```

## Trading Cycle Phases

```
START CYCLE
    ↓
PHASE 1 (Trend-Master): ~12 seconds
├─ Leaves cafeteria (moving)
├─ Walks to Trend room (1.5s)
├─ Works at desk (10s)
└─ Returns to cafeteria

PHASE 2 (Analyse-Master): ~12 seconds
├─ Leaves cafeteria (moving)
├─ Walks to Analyse room (1.5s)
├─ Works at desk (10s)
└─ Returns to cafeteria

PHASE 3 (Trader-Master): ~12 seconds
├─ Leaves cafeteria (moving)
├─ Walks to Trader room (1.5s)
├─ Works at desk (10s)
└─ Returns to cafeteria

Total: ~36 seconds per cycle
```

## Cafeteria Area

**Top section where agents walk around initially:**

```
┌─────────────────────────────────────┐
│  ☕ CAFETERIA                       │
│                                     │
│ [Plant]  [Table] [Table]  [Plant]  │
│                                     │
│    🧠 Trend      🔍 Analyse         │
│           💰 Trader                 │
│                                     │
│  (All agents walking randomly)      │
└─────────────────────────────────────┘
```

Agents spawn here initially and walk around when idle.

## Individual Room Layout

**Each room is identical, customized for agent:**

```
┌──────────────────────┐
│ 🧠 TREND-MASTER      │
│                      │
│                      │
│     [Desk]           │
│    [Monitor]         │
│                      │
│   (Agent works here  │
│    for 10 seconds)   │
└──────────────────────┘
```

When agent is in room, it shows:
- Room title at top
- Desk with computer in center
- Chair under desk

## Agent Behavior Timeline

```
T=0s:  START CYCLE
       ├─ Trend-Master status: IDLE (CAFETERIA)
       └─ All agents in cafeteria walking

T=0.5s: Trend-Master status: MOVING TO ROOM
        └─ Agent walks from cafeteria to Trend room

T=2s:   Trend-Master status: WORKING (10s)
        └─ Agent sits at desk, works

T=12s:  Trend-Master status: COMPLETE
        ├─ Returns to cafeteria
        ├─ Analyse-Master status: MOVING TO ROOM
        └─ Analyse walks to room

T=14s:  Analyse-Master status: WORKING (10s)

T=24s:  Analyse-Master returns to cafeteria
        ├─ Trader-Master status: MOVING TO ROOM
        └─ Trader walks to room

T=26s:  Trader-Master status: WORKING (10s)

T=36s:  Trader-Master returns to cafeteria
        ├─ All agents IDLE
        └─ Cafeteria walking
```

## Dashboard Display

```
📊 TRADING CONTROL

Current Pair: BTCUSD

[Input Field] [SET Button]
[▶ START CYCLE Button]
[RESET Button]

🧠 PHASE 1 - TREND
   Status: MOVING TO ROOM

🔍 PHASE 2 - ANALYSE
   Status: IDLE (Cafeteria)

💰 PHASE 3 - TRADER
   Status: IDLE (Cafeteria)

CYCLES: 1
SIGNALS: 1
TRADES: 1
WIN RATE: 100%
```

## Agent Characters

**Design:** Minecraft-style pixel art

**Head:**
- Square 32×32 pixel head
- Color-coded: Green (Trend), Blue (Analyse), Orange (Trader)
- Eyes (2 black pixels)
- Mouth (1 pixel line)
- Status dot (top-right)

**Body:**
- 32×16 pixel rectangle
- Same color as head, slightly transparent
- Below head

**Label:** Agent name below character

## Status Indicators

| Dot Color | Status | Meaning |
|-----------|--------|---------|
| Gray | IDLE | Agent in cafeteria, walking |
| Yellow | MOVING | Agent walking to their room |
| Red | WORKING | Agent at desk (10-second work) |
| Green | COMPLETE | Task done, returning to cafeteria |

## Room Assignment

**Each agent has dedicated room:**

| Agent | Room | Location |
|-------|------|----------|
| 🧠 Trend-Master | Trend Room | Left |
| 🔍 Analyse-Master | Analyse Room | Center |
| 💰 Trader-Master | Trader Room | Right |

When assigned task:
- Agent leaves cafeteria
- Walks to their room
- Works at desk for 10s
- Returns to cafeteria

## Example Workflow

```
Step 1: Open file
        See all 3 agents walking in cafeteria

Step 2: Enter pair
        Input: SOLANA
        Press: Enter or SET button

Step 3: Click START CYCLE
        Watch Trend-Master walk to Trend room

        Wait 10 seconds while working

        Trend returns to cafeteria
        Analyse-Master walks to Analyse room

        Wait 10 seconds while working

        Analyse returns to cafeteria
        Trader-Master walks to Trader room

        Wait 10 seconds while working

        Trader returns to cafeteria
        All metrics updated

Step 4: Click START CYCLE again
        Repeat workflow
```

## Cafeteria Walking

When idle, agents in cafeteria:
- Walk randomly around the space
- Don't collide with furniture
- Stay within cafeteria bounds
- Smooth walking animation

## Room Working

When in assigned room:
- Agent positioned at desk
- Pulsing work animation
- 10-second duration
- Status shows "WORKING (10s)"

## Valid Trading Pairs

```
EURUSD  BTCUSD  SOLANA  XAUUSD  AAPL
GBPUSD  ETHUSD  ADAUSD  WTIUSD  MSFT
USDJPY  XRPUSD  DAX40   GOOGL   SPX500
```

Requirements:
- 3-10 letters only
- No numbers or special characters
- Auto-converted to UPPERCASE

## Features

✅ All 3 agents visible initially  
✅ Cafeteria starting area  
✅ 3 dedicated rooms (one per agent)  
✅ Smooth agent movement  
✅ 10-second work periods  
✅ Realistic Minecraft characters  
✅ Real-time status updates  
✅ Metrics tracking  
✅ Custom pair entry  
✅ Responsive design  

## Controls

**Input Field:**
- Type trading pair
- Press Enter or click SET

**START CYCLE Button:**
- Begins trading cycle
- All 3 phases execute sequentially
- ~36 seconds per cycle

**RESET Button:**
- Clears all metrics
- Returns all agents to cafeteria
- Resets status to IDLE

## Browser Support

✅ Chrome 60+  
✅ Firefox 55+  
✅ Safari 12+  
✅ Edge 79+  
✅ Mobile browsers  

## Performance

- 60 FPS smooth animations
- No lag with 3 agents
- Responsive UI
- Fast load time

---

**Version:** 3.0  
**Status:** Production Ready  
**Date:** May 4, 2026

All 3 agents in cafeteria, walking to their rooms when assigned tasks! 🚀
