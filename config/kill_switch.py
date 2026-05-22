"""
Trading Kill Switch — instant halt without a process restart.

Create the sentinel file to pause, remove it to resume.

Usage:
    from config.kill_switch import KillSwitch
    KillSwitch.check("EURUSD-cycle-42")   # raises if paused
    KillSwitch.pause("Daily drawdown 5% hit")
    KillSwitch.resume()
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SENTINEL = Path(__file__).parent.parent / "TRADING_PAUSED"


class KillSwitch:
    """Namespace for kill-switch helpers. All methods are static."""

    @staticmethod
    def is_paused() -> bool:
        """Return True if the TRADING_PAUSED sentinel file exists."""
        if _SENTINEL.exists():
            try:
                reason = _SENTINEL.read_text().strip()
            except OSError:
                reason = "unknown"
            logger.warning("[KILL-SWITCH] Trading PAUSED — reason: %s", reason or "file present")
            return True
        return False

    @staticmethod
    def check(cycle_label: str = "") -> None:
        """
        Raise RuntimeError immediately if the kill switch is active.
        Call at the top of every trading cycle.
        """
        if KillSwitch.is_paused():
            raise RuntimeError(f"Trading paused by kill switch (cycle={cycle_label})")

    @staticmethod
    def pause(reason: str = "manual") -> None:
        """Activate the kill switch — halts all new trade execution."""
        try:
            _SENTINEL.write_text(reason)
        except OSError as exc:
            logger.error("[KILL-SWITCH] Could not write sentinel: %s", exc)
        logger.critical("[KILL-SWITCH] Trading PAUSED — %s", reason)

    @staticmethod
    def resume() -> None:
        """Deactivate the kill switch — re-enables trade execution."""
        _SENTINEL.unlink(missing_ok=True)
        logger.info("[KILL-SWITCH] Trading RESUMED")
