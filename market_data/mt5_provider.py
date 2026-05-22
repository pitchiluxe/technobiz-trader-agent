"""MetaTrader 5 integration for market data and trade execution."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .data_provider import DataProvider, OHLCData

from config.constants import (
    CANDLE_MAX_AGE_FACTOR,
    TIMEFRAME_MINUTES,
    RECONNECT_DELAYS,
)

logger = logging.getLogger(__name__)

try:
    import MetaTrader5 as mt5
    _MT5_AVAILABLE = True
except ImportError:
    _MT5_AVAILABLE = False
    logger.warning("[MT5] MetaTrader5 package not installed. Run: pip install MetaTrader5")

# Map timeframe string keys to MT5 constants
_TIMEFRAME_MAP: Dict[str, int] = {
    "D":   16408,
    "4H":  16388,
    "1H":  16385,
    "15M": 15,
    "5M":  5,
    "1M":  1,
}

if _MT5_AVAILABLE:
    _TIMEFRAME_MAP = {
        "D":   mt5.TIMEFRAME_D1,
        "4H":  mt5.TIMEFRAME_H4,
        "1H":  mt5.TIMEFRAME_H1,
        "15M": mt5.TIMEFRAME_M15,
        "5M":  mt5.TIMEFRAME_M5,
        "1M":  mt5.TIMEFRAME_M1,
    }


class MT5Provider(DataProvider):
    """
    MetaTrader 5 data provider for real-time market data and execution.

    Thread-safety: MT5's Python library is NOT thread-safe.  All calls are
    serialised through self._lock so that concurrent async tasks cannot make
    simultaneous MT5 API calls that corrupt internal state.

    Order retry: place_order() retries up to MAX_ORDER_RETRIES times on
    non-fatal retrodes before giving up, preventing silent missed fills.
    """

    MAX_ORDER_RETRIES = 3
    RETRY_DELAY_S     = 1.0

    def __init__(self, account: str, password: str, server: str) -> None:
        if not _MT5_AVAILABLE:
            raise RuntimeError(
                "MetaTrader5 package is not installed. Run: pip install MetaTrader5"
            )
        self.account  = int(account)
        self.password = password
        self.server   = server
        self._connected = False
        # Serialises all MT5 API calls — the library is not thread-safe.
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        async with self._lock:
            if not await asyncio.to_thread(mt5.initialize):
                logger.error("[MT5] initialize() failed: %s", mt5.last_error())
                return False

            authorized = await asyncio.to_thread(
                mt5.login, self.account, self.password, self.server
            )
            if not authorized:
                logger.error(
                    "[MT5] login() failed — account=%s server=%s err=%s",
                    self.account, self.server, mt5.last_error(),
                )
                await asyncio.to_thread(mt5.shutdown)
                return False

            self._connected = True
            info = await asyncio.to_thread(mt5.account_info)
            logger.info(
                "[MT5] Connected — account=%s server=%s balance=%.2f %s",
                self.account, self.server, info.balance, info.currency,
            )
            return True

    async def disconnect(self) -> bool:
        async with self._lock:
            await asyncio.to_thread(mt5.shutdown)
            self._connected = False
        logger.info("[MT5] Disconnected")
        return True

    async def is_connected(self) -> bool:
        if not self._connected:
            return False
        async with self._lock:
            info = await asyncio.to_thread(mt5.account_info)
        return info is not None

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 200,
    ) -> List[OHLCData]:
        """
        Retrieve OHLCV candles from MT5 with a staleness check.

        Returns empty list if:
        - not connected
        - unknown timeframe
        - MT5 returns no data
        - the most-recent candle is older than CANDLE_MAX_AGE_FACTOR × TF_interval
        """
        if not self._connected:
            logger.warning("[MT5] get_candles called while not connected")
            return []

        tf = _TIMEFRAME_MAP.get(timeframe.upper())
        if tf is None:
            logger.error("[MT5] Unknown timeframe '%s'. Valid: %s", timeframe, list(_TIMEFRAME_MAP))
            return []

        async with self._lock:
            rates = await asyncio.to_thread(mt5.copy_rates_from_pos, symbol, tf, 0, limit)

        if rates is None or len(rates) == 0:
            logger.warning("[MT5] No data for %s %s: %s", symbol, timeframe, mt5.last_error())
            return []

        candles = [
            OHLCData(
                timestamp   = datetime.fromtimestamp(int(r["time"])),
                open_price  = float(r["open"]),
                high_price  = float(r["high"]),
                low_price   = float(r["low"]),
                close_price = float(r["close"]),
                volume      = float(r["tick_volume"]),
            )
            for r in rates
        ]

        # ── Staleness check ────────────────────────────────────────────
        if candles:
            tf_key = timeframe.upper()
            tf_minutes = TIMEFRAME_MINUTES.get(tf_key, 60)
            max_age_seconds = tf_minutes * 60 * CANDLE_MAX_AGE_FACTOR
            newest_ts = candles[-1].timestamp
            # Make timezone-aware for comparison
            if newest_ts.tzinfo is None:
                newest_ts = newest_ts.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - newest_ts).total_seconds()
            if age > max_age_seconds:
                logger.warning(
                    "[MT5] STALE DATA — %s %s newest candle is %.0f min old "
                    "(max allowed: %.0f min). Rejecting.",
                    symbol, timeframe, age / 60, max_age_seconds / 60,
                )
                return []

        logger.debug("[MT5] %s %s: %d candles retrieved", symbol, timeframe, len(candles))
        return candles

    async def get_current_price(self, symbol: str) -> float:
        if not self._connected:
            return 0.0
        async with self._lock:
            tick = await asyncio.to_thread(mt5.symbol_info_tick, symbol)
        if tick is None:
            logger.error("[MT5] No tick for %s: %s", symbol, mt5.last_error())
            return 0.0
        return (tick.bid + tick.ask) / 2.0

    # ------------------------------------------------------------------
    # Account info
    # ------------------------------------------------------------------

    async def get_account_balance(self) -> float:
        if not self._connected:
            return 0.0
        async with self._lock:
            info = await asyncio.to_thread(mt5.account_info)
        return float(info.balance) if info else 0.0

    async def get_account_equity(self) -> float:
        if not self._connected:
            return 0.0
        async with self._lock:
            info = await asyncio.to_thread(mt5.account_info)
        return float(info.equity) if info else 0.0

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        if not self._connected:
            return []
        async with self._lock:
            positions = await asyncio.to_thread(mt5.positions_get)
        if positions is None:
            return []
        return [
            {
                "ticket":      p.ticket,
                "symbol":      p.symbol,
                "type":        "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume":      p.volume,
                "price_open":  p.price_open,
                "price_current": p.price_current,
                "sl":          p.sl,
                "tp":          p.tp,
                "profit":      p.profit,
            }
            for p in positions
        ]

    async def get_position_by_ticket(self, ticket: int) -> Optional[Dict[str, Any]]:
        """Return a single position dict by MT5 ticket, or None."""
        positions = await self.get_open_positions()
        for p in positions:
            if p["ticket"] == ticket:
                return p
        return None

    # ------------------------------------------------------------------
    # Symbol helpers
    # ------------------------------------------------------------------

    async def validate_symbol(self, symbol: str) -> bool:
        if not self._connected:
            return False
        async with self._lock:
            info = await asyncio.to_thread(mt5.symbol_info, symbol)
            if info is None:
                logger.error("[MT5] Symbol '%s' not found: %s", symbol, mt5.last_error())
                return False
            if not info.visible:
                ok = await asyncio.to_thread(mt5.symbol_select, symbol, True)
                if not ok:
                    logger.error("[MT5] Cannot enable '%s' in Market Watch", symbol)
                    return False
        return True

    async def _get_filling_mode(self, symbol: str) -> int:
        async with self._lock:
            info = await asyncio.to_thread(mt5.symbol_info, symbol)
        if info is None:
            return mt5.ORDER_FILLING_IOC
        if info.filling_mode & 4:
            return mt5.ORDER_FILLING_RETURN
        if info.filling_mode & 2:
            return mt5.ORDER_FILLING_IOC
        return mt5.ORDER_FILLING_FOK

    # ------------------------------------------------------------------
    # Order execution (with retry on soft failures)
    # ------------------------------------------------------------------

    async def place_order(
        self,
        symbol:      str,
        order_type:  str,
        volume:      float,
        price:       float,
        stop_loss:   float,
        take_profit: float,
        comment:     str = "TechnobizTrader",
        deviation:   int = 20,
    ) -> Optional[int]:
        """
        Place a limit order via MT5.  Retries up to MAX_ORDER_RETRIES times
        on requote / price-moved retrodes before returning None.

        Returns:
            MT5 order ticket on success, None on failure.
        """
        if not self._connected:
            logger.error("[MT5] Cannot place order: not connected")
            return None

        if not await self.validate_symbol(symbol):
            return None

        filling_mode = await self._get_filling_mode(symbol)
        mt5_type = mt5.ORDER_TYPE_BUY_LIMIT if order_type == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT

        request = {
            "action":       mt5.TRADE_ACTION_PENDING,
            "symbol":       symbol,
            "volume":       volume,
            "type":         mt5_type,
            "price":        price,
            "sl":           stop_loss,
            "tp":           take_profit,
            "deviation":    deviation,
            "magic":        202600,
            "comment":      comment,
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        # ── Retry loop ─────────────────────────────────────────────────
        for attempt in range(1, self.MAX_ORDER_RETRIES + 1):
            async with self._lock:
                result = await asyncio.to_thread(mt5.order_send, request)

            if result is not None and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(
                    "[MT5] Order placed: ticket=%d %s %s %.2f lots @ %.5f (attempt %d)",
                    result.order, order_type, symbol, volume, price, attempt,
                )
                return result.order

            retcode = result.retcode if result else "None"
            logger.warning(
                "[MT5] order_send attempt %d/%d failed: retcode=%s err=%s",
                attempt, self.MAX_ORDER_RETRIES, retcode, mt5.last_error(),
            )

            # On last attempt escalate to market order if signal is urgent
            if attempt == self.MAX_ORDER_RETRIES:
                logger.error("[MT5] All retries exhausted — order not placed")
                return None

            await asyncio.sleep(self.RETRY_DELAY_S)

        return None  # unreachable, satisfies type checker

    # ------------------------------------------------------------------
    # Position management
    # ------------------------------------------------------------------

    async def close_position(
        self,
        ticket:     int,
        symbol:     str,
        volume:     float,
        order_type: str,
    ) -> bool:
        """Close (or partially close) an open position."""
        if not self._connected:
            logger.error("[MT5] Cannot close position: not connected")
            return False

        close_type = mt5.ORDER_TYPE_SELL if order_type == "BUY" else mt5.ORDER_TYPE_BUY
        async with self._lock:
            tick = await asyncio.to_thread(mt5.symbol_info_tick, symbol)
        if tick is None:
            logger.error("[MT5] No tick for %s while closing position", symbol)
            return False

        close_price  = tick.bid if order_type == "BUY" else tick.ask
        filling_mode = await self._get_filling_mode(symbol)

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       volume,
            "type":         close_type,
            "position":     ticket,
            "price":        close_price,
            "deviation":    20,
            "magic":        202600,
            "comment":      "TechnobizTrader-Close",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        async with self._lock:
            result = await asyncio.to_thread(mt5.order_send, request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            retcode = result.retcode if result else "None"
            logger.error("[MT5] close_position failed: retcode=%s err=%s", retcode, mt5.last_error())
            return False

        logger.info("[MT5] Position closed: ticket=%d %s vol=%.2f", ticket, symbol, volume)
        return True

    async def modify_sl(
        self,
        ticket: int,
        symbol: str,
        new_sl: float,
        new_tp: Optional[float] = None,
    ) -> bool:
        """
        Modify the stop loss (and optionally take profit) of an open position.
        Used to move SL to break-even after TP1 is hit.
        """
        if not self._connected:
            return False

        async with self._lock:
            positions = await asyncio.to_thread(mt5.positions_get, ticket=ticket)

        if not positions:
            logger.warning("[MT5] modify_sl: ticket %d not found", ticket)
            return False

        pos = positions[0]
        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol":   symbol,
            "sl":       new_sl,
            "tp":       new_tp if new_tp is not None else pos.tp,
        }
        async with self._lock:
            result = await asyncio.to_thread(mt5.order_send, request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            retcode = result.retcode if result else "None"
            logger.error("[MT5] modify_sl failed: retcode=%s err=%s", retcode, mt5.last_error())
            return False

        logger.info("[MT5] SL moved → %.5f for ticket %d", new_sl, ticket)
        return True
