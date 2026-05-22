# Agent Office Animation Demo

An interactive HTML visualization showing the three TechnobizTrader agents walking around an office environment.

## Features

✅ **Animated Agents**
- Trend-Master (🧠 Brain) - Green
- Analyse-Master (🔍 Search) - Blue  
- Trader-Master (💰 Money) - Orange

✅ **Office Environment**
- 3 agent desks
- Grid background
- Agents walking in infinite loops

✅ **Real-time Dashboard**
- Phase progress bars (0-100%)
- Agent status indicators
- Trading metrics (cycles, signals, trades, win rate)
- Status indicators (Idle, Working, Complete)

✅ **Interactive Controls**
- START TRADING CYCLE: Simulate full workflow
- Trend Analysis: Assign Phase 1 task
- Signal Generation: Assign Phase 2 task
- Execute Trade: Assign Phase 3 task
- RESET: Clear all metrics

✅ **Visual Indicators**
- Idle status: Gray dot
- Working status: Yellow pulsing dot
- Complete status: Green dot
- Walking animation: Continuous movement
- Thinking animation: Opacity pulse

## How to Use

### Method 1: Open Directly
```bash
# Windows
start agent_office_animation.html

# macOS
open agent_office_animation.html

# Linux
xdg-open agent_office_animation.html
```

### Method 2: Use Python HTTP Server
```bash
cd c:\Users\erick\Downloads\Trading_Agent
python -m http.server 8000
```
Then open: `http://localhost:8000/agent_office_animation.html`

### Method 3: Drag & Drop
Drag the HTML file directly into your web browser

## Demo Workflow

1. **Open the file** in any modern web browser
2. **Click "START TRADING CYCLE"** to see:
   - Trend-Master activates (Phase 1)
   - After 3 seconds → Analyse-Master activates (Phase 2)
   - After 3 seconds → Trader-Master activates (Phase 3)
   - Each phase shows progress bar 0-100%
   - Metrics update after each phase
3. **Individual Tasks** - Click individual buttons to test each agent
4. **Watch the animation** - Agents walk in office, status changes in real-time
5. **Monitor metrics** - Track cycles, signals, trades, and win rate

## Screen Layout

```
┌─────────────────────────────────────────┬──────────────────────────────┐
│                                         │    Agent Status Dashboard    │
│      Office Animation                   │                              │
│  (Agents walking around desks)          │  [Status Indicators]        │
│                                         │  [Progress Bars]            │
│  🧠 Trend-Master                        │  [Metrics]                  │
│  🔍 Analyse-Master                      │                              │
│  💰 Trader-Master                       │  [Control Buttons]          │
│                                         │                              │
└─────────────────────────────────────────┴──────────────────────────────┘
```

## Agent Movements

### Trend-Master 🧠
- Walks left-to-right continuously
- Green status indicator
- Phase 1: Market structure analysis

### Analyse-Master 🔍
- Walks right-to-left (mirrored) 
- Blue status indicator
- Phase 2: ICT signal generation

### Trader-Master 💰
- Walks left-to-right (offset timing)
- Orange status indicator
- Phase 3: Trade execution

## Status Colors

| Color | Meaning |
|-------|---------|
| Gray | IDLE - Waiting for task |
| Yellow (Pulsing) | WORKING - Currently processing |
| Green | COMPLETE - Task finished |

## Trading Cycle Flow

```
START TRADING CYCLE
       ↓
PHASE 1 (3 seconds)
├─ Trend-Master analyzes market
├─ Progress: 0% → 100%
└─ Status: WORKING → COMPLETE
       ↓
PHASE 2 (3 seconds)
├─ Analyse-Master generates signal
├─ Progress: 0% → 100%
└─ Status: WORKING → COMPLETE
       ↓
PHASE 3 (3 seconds)
├─ Trader-Master executes trade
├─ Progress: 0% → 100%
└─ Status: WORKING → COMPLETE
       ↓
CYCLE COMPLETE
├─ All agents return to IDLE
├─ Metrics updated
└─ Ready for next cycle
```

## Metrics Tracking

**Cycles Completed**
- Total number of full trading cycles executed
- Increments each time "START TRADING CYCLE" is clicked

**Signals Generated**
- Count of valid trade signals from Analyse-Master
- Updates when Phase 2 completes successfully

**Trades Executed**
- Count of trades executed by Trader-Master
- Updates when Phase 3 completes successfully

**Win Rate**
- Calculated as: (Trades Executed / Expected Trades) × 100%
- Shows overall trading success percentage

## Browser Support

✅ Chrome 60+  
✅ Firefox 55+  
✅ Safari 12+  
✅ Edge 79+  
✅ Mobile browsers (responsive design)

## Customization

To modify agent movements, colors, or animations, edit the CSS:

```css
/* Change walking speed */
animation: walk 2s infinite;  /* 2s = speed */

/* Change colors */
.trend-master .agent-head { background: #4CAF50; }  /* Green */
.analyse-master .agent-head { background: #2196F3; }  /* Blue */
.trader-master .agent-head { background: #FF9800; }  /* Orange */
```

## Technical Details

- **Framework:** Pure HTML5 + CSS3 + JavaScript (no dependencies)
- **Animation:** CSS3 Keyframes + JavaScript timers
- **Responsive:** Works on desktop, tablet, mobile
- **Performance:** Optimized for smooth 60fps animations
- **File Size:** ~15KB (single HTML file)

## Troubleshooting

**Agents not moving?**
- Ensure JavaScript is enabled in your browser
- Try refreshing the page (F5)
- Use a modern browser (Chrome, Firefox, Safari, Edge)

**Animations stuttering?**
- Close other browser tabs to free memory
- Disable browser extensions
- Try a different browser

**Dashboard not updating?**
- Click a button to trigger updates
- Check browser console for errors (F12)
- Ensure JavaScript is not blocked

## Future Enhancements

- [ ] Real-time data connection to actual trading engine
- [ ] Live candle chart display
- [ ] Order book visualization
- [ ] Trade execution animation
- [ ] Real-time P&L tracking
- [ ] Multi-pair pair rotation visualization
- [ ] Sound effects for phase transitions
- [ ] Export cycle history

## Files

```
agent_office_animation.html    - Main animation file (this file)
```

## Notes

- This is a **demonstration** of the GUI concept
- Actual trading data comes from the Python trading engine
- Metrics shown are for **demonstration purposes**
- Real-time data requires integration with `main.py`

---

**Version:** 1.0  
**Status:** Production Ready  
**Date:** May 4, 2026
