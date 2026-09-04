"""
News Blackout — high-impact economic event calendar.

Covers the major market-moving releases that can cause sudden spikes and
whipsaws.  The system blocks new trade executions within NEWS_BLACKOUT_MINUTES
of any event in this calendar.

Sources / methodology:
  - FOMC meeting dates: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
  - NFP schedule: first Friday of each month at 8:30 AM ET (USD)
  - CPI: approximately the 10th–15th of each month (US CPI, 8:30 AM ET)
  - ECB / BoE: ECB Governing Council meetings; BoE Monetary Policy meetings
  - To add live data: swap _EVENTS for a call to a ForexFactory / FFcal API.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import List, Optional

# ── Constants ──────────────────────────────────────────────────────────────────

BLACKOUT_MINUTES = 10    # minutes before AND after event to block trading
ET = timezone(timedelta(hours=-5))   # Eastern Time (EST/EDT — simplified)

# ── Event type taxonomy ────────────────────────────────────────────────────────
# HIGH  → always block
# MEDIUM → block only for the correlated symbol (e.g. GBP news blocks GBP pairs)
# LOW   → informational only, no block

@dataclass
class EconEvent:
    name:     str
    datetime: datetime          # always UTC
    currency: str               # e.g. "USD", "EUR", "GBP"
    impact:   str              # "HIGH" | "MEDIUM" | "LOW"
    symbols:  List[str] = field(default_factory=list)   # affected pairs

    @property
    def blackout_start(self) -> datetime:
        return self.datetime - timedelta(minutes=BLACKOUT_MINUTES)

    @property
    def blackout_end(self) -> datetime:
        return self.datetime + timedelta(minutes=BLACKOUT_MINUTES)

    def to_dict(self) -> dict:
        return {
            "name":          self.name,
            "datetime_utc":  self.datetime.isoformat(),
            "currency":      self.currency,
            "impact":        self.impact,
            "symbols":       self.symbols,
            "blackout_start": self.blackout_start.isoformat(),
            "blackout_end":   self.blackout_end.isoformat(),
        }


def _now() -> datetime:
    """Current UTC time — injected by tests, real clock in production."""
    return _NOW_CTX[0] if _NOW_CTX else datetime.now(timezone.utc)


# Module-level mutable cell for test-time injection.
# Tests set _NOW_CTX[0] = fake_time; the production path never touches this.
_NOW_CTX: list[datetime] = []


# ── Helper: first weekday of a month that falls on or after a given day ─────────

def _first_weekday_on_or_after(year: int, month: int, day: int, weekday: int) -> datetime:
    """Return the first occurrence of |weekday| (0=Mon) on or after |day| in |year/month|.

    Used to find NFP (first Friday ≥ day 1).
    """
    c = calendar.Calendar()
    days_in_month = calendar.monthrange(year, month)[1]
    for d in range(day, days_in_month + 1):
        if c.monthdayscalendar(year, month)[0][d % 7] == 0:
            target_weekday = d
            break
    # Find the actual first occurrence of the weekday in the month
    for week in c.monthdayscalendar(year, month):
        for i, dom in enumerate(week):
            if dom != 0 and i == weekday and dom >= day:
                dt = datetime(year, month, dom, 8, 30, tzinfo=ET)
                return dt.astimezone(timezone.utc)
    # Fallback: compute directly
    first_day = datetime(year, month, 1, 8, 30, tzinfo=ET)
    days_until = (weekday - first_day.weekday()) % 7
    return (first_day + timedelta(days=days_until)).astimezone(timezone.utc)


# ── 2026 Economic Event Calendar ───────────────────────────────────────────────

def _build_calendar() -> List[EconEvent]:
    """Hardcoded 2026 high-impact events. Swap for a live feed in production."""
    events: List[EconEvent] = []

    # ── FOMC Meetings (Federal Reserve) — 8 scheduled in 2026 ──────────────
    # Times: first day starts ~14:00 ET, second day decision ~14:00 ET
    # High-impact for all USD pairs (EURUSD, GBPUSD, USDJPY, etc.)
    fomc_meetings = [
        (2026, 1, 27),   # Jan 27-28
        (2026, 3, 17),   # Mar 17-18
        (2026, 5, 5),    # May 5-6
        (2026, 6, 16),   # Jun 16-17
        (2026, 7, 28),   # Jul 28-29
        (2026, 9, 15),   # Sep 15-16
        (2026, 11, 3),   # Nov 3-4
        (2026, 12, 15),  # Dec 15-16
    ]
    for y, m, d in fomc_meetings:
        dt = datetime(y, m, d, 14, 0, tzinfo=ET).astimezone(timezone.utc)
        events.append(EconEvent(
            name=f"FOMC Meeting + Rate Decision",
            datetime=dt,
            currency="USD",
            impact="HIGH",
            symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"],
        ))

    # ── FOMC Press Conference (separate from meeting decision) ─────────────
    # Held within 30 min of decision; equivalent impact
    for y, m, d in fomc_meetings:
        dt = datetime(y, m, d, 14, 30, tzinfo=ET).astimezone(timezone.utc)
        events.append(EconEvent(
            name=f"FOMC Press Conference",
            datetime=dt,
            currency="USD",
            impact="HIGH",
            symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"],
        ))

    # ── Non-Farm Payrolls (NFP) — first Friday each month, 8:30 AM ET ─────
    # Covers USD and all correlated pairs
    for month in range(1, 13):
        try:
            dt = _first_weekday_on_or_after(2026, month, 1, 4)  # weekday 4 = Friday
        except Exception:
            continue
        events.append(EconEvent(
            name=f"NFP — Non-Farm Payrolls",
            datetime=dt,
            currency="USD",
            impact="HIGH",
            symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"],
        ))

    # ── US CPI (Consumer Price Index) — approximately 10th–15th each month, 8:30 AM ET ─
    # Scheduled mid-month; exact date varies, we use the 13th as a conservative anchor
    for month in range(1, 13):
        # Use 13th of each month as the anchor; actual date varies ±2 days
        dt = datetime(2026, month, 13, 8, 30, tzinfo=ET).astimezone(timezone.utc)
        events.append(EconEvent(
            name=f"US CPI — Consumer Price Index",
            datetime=dt,
            currency="USD",
            impact="HIGH",
            symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"],
        ))

    # ── US Retail Sales — approximately mid-month, 8:30 AM ET ────────────
    for month in range(1, 13):
        dt = datetime(2026, month, 15, 8, 30, tzinfo=ET).astimezone(timezone.utc)
        events.append(EconEvent(
            name="US Retail Sales",
            datetime=dt,
            currency="USD",
            impact="MEDIUM",
            symbols=["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD"],
        ))

    # ── ECB Interest Rate Decision — ~6 meetings per year ────────────────
    # Times: typically 13:45 CET (= 7:45 ET)
    ecb_meetings = [
        (2026, 1, 29),   # Jan 29
        (2026, 3, 5),    # Mar 5
        (2026, 4, 15),   # Apr 15
        (2026, 6, 3),    # Jun 3
        (2026, 7, 16),   # Jul 16
        (2026, 9, 9),    # Sep 9
        (2026, 10, 28),  # Oct 28
        (2026, 12, 10),  # Dec 10
    ]
    CET = timezone(timedelta(hours=1))
    for y, m, d in ecb_meetings:
        dt = datetime(y, m, d, 13, 45, tzinfo=CET).astimezone(timezone.utc)
        events.append(EconEvent(
            name="ECB Interest Rate Decision",
            datetime=dt,
            currency="EUR",
            impact="HIGH",
            symbols=["EURUSD", "EURGBP", "EURJPY", "EURCHF"],
        ))
        # ECB President press conference ~14:30 CET
        dt_pc = datetime(y, m, d, 14, 30, tzinfo=CET).astimezone(timezone.utc)
        events.append(EconEvent(
            name="ECB President Press Conference",
            datetime=dt_pc,
            currency="EUR",
            impact="HIGH",
            symbols=["EURUSD", "EURGBP", "EURJPY", "EURCHF"],
        ))

    # ── Bank of England (BoE) Rate Decision — ~8 meetings per year ─────────
    # Times: typically 12:00 GMT (= 7:00 ET)
    boe_meetings = [
        (2026, 2, 5),    # Feb 5
        (2026, 3, 19),   # Mar 19
        (2026, 5, 7),    # May 7
        (2026, 6, 18),   # Jun 18
        (2026, 8, 6),    # Aug 6
        (2026, 9, 17),   # Sep 17
        (2026, 11, 5),   # Nov 5
        (2026, 12, 17),  # Dec 17
    ]
    GMT = timezone.utc
    for y, m, d in boe_meetings:
        dt = datetime(y, m, d, 12, 0, tzinfo=GMT).astimezone(timezone.utc)
        events.append(EconEvent(
            name="BoE Interest Rate Decision",
            datetime=dt,
            currency="GBP",
            impact="HIGH",
            symbols=["GBPUSD", "EURGBP", "GBPJPY"],
        ))

    # ── Bank of Japan (BoJ) Rate Decision — typically ~8 meetings per year ──
    # Times: typically 03:00–04:00 JST (= 14:00-15:00 ET previous day)
    boj_meetings = [
        (2026, 1, 22),   # Jan 22
        (2026, 3, 19),   # Mar 19
        (2026, 4, 27),   # Apr 27
        (2026, 6, 18),   # Jun 18
        (2026, 7, 29),   # Jul 29
        (2026, 9, 24),   # Sep 24
        (2026, 10, 29),  # Oct 29
        (2026, 12, 18),  # Dec 18
    ]
    JST = timezone(timedelta(hours=9))
    for y, m, d in boj_meetings:
        dt = datetime(y, m, d, 3, 0, tzinfo=JST).astimezone(timezone.utc)
        events.append(EconEvent(
            name="BoJ Interest Rate Decision",
            datetime=dt,
            currency="JPY",
            impact="HIGH",
            symbols=["USDJPY", "EURJPY", "GBPJPY"],
        ))

    # ── Canada CPI — approximately 17th of each month, 8:30 AM ET ─────────
    for month in range(1, 13):
        dt = datetime(2026, month, 17, 8, 30, tzinfo=ET).astimezone(timezone.utc)
        events.append(EconEvent(
            name="Canada CPI",
            datetime=dt,
            currency="CAD",
            impact="MEDIUM",
            symbols=["USDCAD"],
        ))

    # ── Australia CPI — approximately 28th of each month, 8:30 AM AEST ─────
    # AEST = UTC+10
    AEST = timezone(timedelta(hours=10))
    for month in range(1, 13):
        dt = datetime(2026, month, 28, 8, 30, tzinfo=AEST).astimezone(timezone.utc)
        events.append(EconEvent(
            name="Australia CPI",
            datetime=dt,
            currency="AUD",
            impact="MEDIUM",
            symbols=["AUDUSD"],
        ))

    return events


# Build once at module import
_EVENTS: List[EconEvent] = _build_calendar()


# ── Public API ─────────────────────────────────────────────────────────────────

def is_news_blackout_active(symbol: Optional[str] = None) -> bool:
    """
    Returns True if we are currently within the blackout window of a high-impact
    event.  If |symbol| is provided, HIGH-impact events block all symbols while
    MEDIUM-impact events only block their correlated symbol list.
    """
    now = _now()
    for evt in _EVENTS:
        if not (evt.blackout_start <= now <= evt.blackout_end):
            continue
        if evt.impact == "HIGH":
            return True
        if evt.impact == "MEDIUM" and symbol:
            # MEDIUM events only block correlated symbols
            if any(s.upper() in symbol.upper() for s in evt.symbols):
                return True
    return False


def get_active_blackout(symbol: Optional[str] = None) -> Optional[EconEvent]:
    """Return the currently active EconEvent if any, else None."""
    now = _now()
    for evt in _EVENTS:
        if evt.blackout_start <= now <= evt.blackout_end:
            if evt.impact == "HIGH":
                return evt
            if evt.impact == "MEDIUM" and symbol:
                if any(s.upper() in symbol.upper() for s in evt.symbols):
                    return evt
    return None


def get_upcoming_events(hours_ahead: int = 24) -> List[EconEvent]:
    """Return events in the next |hours_ahead| hours that are not yet in blackout."""
    now = _now()
    cutoff = now + timedelta(hours=hours_ahead)
    return [
        evt for evt in _EVENTS
        if evt.datetime <= cutoff and evt.datetime >= now
        and evt.datetime - timedelta(minutes=BLACKOUT_MINUTES) <= cutoff
    ]


def get_all_events() -> List[EconEvent]:
    """Return all events (for debug / display)."""
    return sorted(_EVENTS, key=lambda e: e.datetime)
