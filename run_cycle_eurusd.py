"""
Full trading cycle simulation for EURUSD using synthetic ICT bearish setup.
Pipeline: Trend-Master → Analyse-Master → Trader-Master
"""
import asyncio, os, sys, logging
os.environ.setdefault("ACCOUNT_BALANCE", "10000")
sys.path.insert(0, os.path.dirname(__file__))
logging.disable(logging.CRITICAL)

from datetime import datetime, timedelta
from market_data.data_provider import OHLCData
from agents.workflow import TradingWorkflow

BASE = datetime(2026, 4, 1, 0, 0)

def oc(idx, o, h, l, cl, v=500_000):
    return OHLCData(BASE + timedelta(hours=idx), round(o,5), round(h,5), round(l,5), round(cl,5), v)


def build_1h():
    """
    85 1H candles — BEARISH structure + ICT bearish setup.

    Swing detection window=5 → range(5, 80) for 85 candles → positions 5-79 only.
    ICT candles at positions 80-84 are OUTSIDE detection window.

    Verified swing highs (chronological): ~[1.0882, 1.0862, 1.0842] at pos ~8, 22, 36
    Verified swing lows  (chronological): ~[1.0822, 1.0802, 1.0782] at pos ~15, 29, 43
    Structure: LH + LL → BEARISH ✓
    max(swing_highs) ≈ 1.0882

    ICT elements:
    [80] Sweep + bearish OB: high=1.0888 > 1.0882+0.0002 ✓; close=1.0858 < 1.0882 ✓
         OB zone: [low=1.0838, high=1.0888]
    [81] Impulse 1 (bearish)
    [82] Impulse 2: creates FVG — candles[80].low=1.0838 > candles[82].high+0.0002
    [83] Impulse 3 (bearish) — BoS via pullback close
    [84] Pullback into OB: high ∈ [1.0835, 1.0891] ✓; close < sorted_lows[1] ✓
    """
    candles = []
    i = 0

    def up_leg(start, from_p, to_p, steps):
        """Monotonically rising candles; last candle has high = to_p."""
        nonlocal i
        for k in range(steps):
            t = k / max(steps - 1, 1)
            mid = from_p + (to_p - from_p) * t
            o_  = mid - 0.0002
            cl_ = mid + 0.0002
            # Intermediate candles: wicks stay below to_p
            h_  = mid + 0.0004 if k < steps - 1 else to_p
            l_  = mid - 0.0004
            candles.append(oc(start + k, o_, h_, l_, cl_))
        return start + steps

    def dn_leg(start, from_p, to_p, steps):
        """Monotonically falling candles; last candle has low = to_p."""
        nonlocal i
        for k in range(steps):
            t = k / max(steps - 1, 1)
            mid = from_p + (to_p - from_p) * t
            o_  = mid + 0.0002
            cl_ = mid - 0.0002
            l_  = mid - 0.0004 if k < steps - 1 else to_p
            h_  = mid + 0.0004
            candles.append(oc(start + k, o_, h_, l_, cl_))
        return start + steps

    SH1, SH2, SH3 = 1.0882, 1.0862, 1.0842   # swing highs — max is SH1
    SL1, SL2, SL3 = 1.0822, 1.0802, 1.0782   # swing lows

    # Structured zigzag: 9 candles per leg
    next_i = up_leg(0,  1.0820, SH1, 9)   # 0-8:   UP  → SH1 at pos 8
    next_i = dn_leg(next_i, SH1, SL1, 7)  # 9-15:  DN  → SL1 at pos 15
    next_i = up_leg(next_i, SL1, SH2, 7)  # 16-22: UP  → SH2 at pos 22
    next_i = dn_leg(next_i, SH2, SL2, 7)  # 23-29: DN  → SL2 at pos 29
    next_i = up_leg(next_i, SL2, SH3, 7)  # 30-36: UP  → SH3 at pos 36
    next_i = dn_leg(next_i, SH3, SL3, 7)  # 37-43: DN  → SL3 at pos 43

    # Drift sideways-up from SL3 toward ICT zone (positions 44-79)
    drift_target = 1.0842
    drift_steps  = 80 - next_i           # fill up to position 79
    next_i = up_leg(next_i, SL3, drift_target, drift_steps)

    # ── ICT SETUP: positions 80-84 ────────────────────────────────────────────
    # [80] Bullish sweep candle (also the bearish OB)
    #   high=1.0890 > SH1+0.0002=1.0888 ✓  |  close=1.0858 < SH1=1.0886 ✓
    #   OB zone: [low=1.0836, high=1.0890]
    candles.append(oc(80, 1.0838, 1.0890, 1.0836, 1.0858))

    # [81] Impulse 1 — bearish
    candles.append(oc(81, 1.0858, 1.0860, 1.0824, 1.0828))

    # [82] Impulse 2 — FVG: candles[80].low=1.0838 > candles[82].high+0.0002 → high ≤ 1.0836
    candles.append(oc(82, 1.0828, 1.0832, 1.0798, 1.0802))

    # [83] Impulse 3 — bearish (price now ~1.0802)
    candles.append(oc(83, 1.0802, 1.0804, 1.0768, 1.0772))

    # [84] Pullback into detected OB zone [1.08363, 1.08443]
    #   high=1.0843 ∈ [1.08333, 1.08473] ✓
    #   close=1.0772 < sorted_lows[1]=1.0798 ✓  (BoS)
    candles.append(oc(84, 1.0772, 1.0843, 1.0765, 1.0772))

    return candles


def build_tf(turns, total, base_offset_days=0, base_offset_hours=0, v_mult=1):
    """Generic timeframe builder from a list of (abs_pos, price) turning points."""
    result = []
    for seg in range(len(turns) - 1):
        s_idx, s_p = turns[seg]
        e_idx, e_p = turns[seg + 1]
        steps = e_idx - s_idx
        going_up = e_p > s_p
        for k in range(steps):
            t = k / max(steps - 1, 1)
            mid = s_p + (e_p - s_p) * t
            sp = 0.0025
            if going_up:
                o, h, l, cl = mid-sp*.3, mid+sp*.6, mid-sp*.5, mid+sp*.4
            else:
                o, h, l, cl = mid+sp*.3, mid+sp*.5, mid-sp*.6, mid-sp*.4
            ts = (BASE - timedelta(days=base_offset_days)
                  - timedelta(hours=base_offset_hours)
                  + timedelta(hours=(s_idx + k)))
            result.append(OHLCData(ts, round(o,5), round(h,5), round(l,5), round(cl,5), 500_000*v_mult))
    return result


def build_daily(n=80):
    turns = [
        (0,1.1500),(8,1.1350),(16,1.1450),(24,1.1300),
        (32,1.1380),(40,1.1220),(48,1.1300),(56,1.1150),
        (64,1.1220),(72,1.1080),(n,1.1050),
    ]
    return build_tf(turns, n, base_offset_days=n, v_mult=4)


def build_4h(n=80):
    turns = [
        (0,1.1100),(8,1.0960),(16,1.1020),(24,1.0880),
        (32,1.0940),(40,1.0800),(48,1.0860),(56,1.0720),
        (64,1.0780),(72,1.0650),(n,1.0620),
    ]
    return build_tf(turns, n, base_offset_hours=n*4, v_mult=2)


async def run():
    wf = TradingWorkflow(verbose=False)
    market_data = {
        "daily": build_daily(80),
        "4h":    build_4h(80),
        "1h":    build_1h(),
    }

    print("=" * 58)
    print("  TechnobizTrader  |  EURUSD  |  Full Cycle  |  BEARISH")
    print("=" * 58)

    # ── STEP 1: Trend-Master ──────────────────────────────────
    trend = await wf.trend_master.analyze(market_data)
    print("\n[STEP 1] TREND-MASTER")
    if not trend:
        print("  RESULT : NO REPORT — insufficient data"); return
    print(f"  Bias         : {trend.bias}")
    print(f"  Confidence   : {trend.confidence}%")
    print(f"  Risk Level   : {trend.risk_level}")
    print(f"  TF Structures: {trend.swing_structure['tf_structures']}")
    print(f"  Support      : {trend.support_resistance['support_levels']}")
    print(f"  Resistance   : {trend.support_resistance['resistance_levels']}")
    print(f"  Liquidity    : {trend.liquidity_levels}")

    if trend.bias == "NEUTRAL":
        print("  PIPELINE STOP: NEUTRAL bias"); return
    if trend.confidence < 65:
        print(f"  PIPELINE STOP: low confidence {trend.confidence}%"); return
    if trend.risk_level == "HIGH":
        print("  PIPELINE STOP: HIGH volatility"); return
    print("  DECISION : PASS → Analyse-Master")

    # ── STEP 2: Analyse-Master ────────────────────────────────
    signal = await wf.analyse_master.analyze(trend.to_dict(), candle_data=market_data)
    print("\n[STEP 2] ANALYSE-MASTER")
    if not signal:
        print("  RESULT : NO SIGNAL — ICT conditions not met"); return
    print(f"  ICT Elements : {signal.pattern_elements}")
    print(f"  Entry        : {signal.entry_level}")
    print(f"  Stop Loss    : {signal.stop_loss}")
    print(f"  TP1 (50%)    : {signal.take_profit_1}")
    print(f"  TP2 (30%)    : {signal.take_profit_2}")
    print(f"  TP3 (20%)    : {signal.take_profit_3}")
    print(f"  R:R Ratio    : {signal.risk_reward_ratio}")
    print(f"  Confidence   : {signal.confidence}%")
    print(f"  Kill Zone    : {signal.kill_zone_start.strftime('%H:%M')} → {signal.kill_zone_end.strftime('%H:%M')}")
    print("  DECISION : PASS → Trader-Master")

    # ── STEP 3: Trader-Master ─────────────────────────────────
    rec = await wf.trader_master.analyze(signal.to_dict())
    print("\n[STEP 3] TRADER-MASTER")
    if not rec:
        print("  RESULT : REJECTED — pre-execution check failed"); return
    pip_risk = abs(rec.entry_price - rec.stop_loss) / 0.0001
    risk_usd = rec.position_size * pip_risk * 10
    print(f"  Signal ID    : {rec.signal_id}")
    print(f"  Status       : {rec.status}")
    print(f"  Direction    : SELL (BEARISH)")
    print(f"  Entry Price  : {rec.entry_price}")
    print(f"  Stop Loss    : {rec.stop_loss}  ({pip_risk:.1f} pips)")
    print(f"  TP1/TP2/TP3  : {rec.take_profit_1} / {rec.take_profit_2} / {rec.take_profit_3}")
    print(f"  Position     : {rec.position_size} lots")
    print(f"  Risk (USD)   : ${risk_usd:.2f}  (~2% of $10,000 account)")
    print(f"  Entry Time   : {rec.entry_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"\n  LIMIT ORDER PLACED — awaiting fill at {rec.entry_price}")
    print("=" * 58)


if __name__ == "__main__":
    asyncio.run(run())
