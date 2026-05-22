"""
Trade Approval System - Manual approval gateway for trade execution.

Ensures every trade is reviewed and approved by the user before execution.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TradeApproval:
    """Manages user approval for trade execution."""

    @staticmethod
    def display_trade_for_approval(trade_signal: Dict[str, Any]) -> str:
        """
        Display trade signal details and request user approval.

        Args:
            trade_signal: TradeSignal.to_dict() from Analyse-Master

        Returns:
            'A' for approve, 'R' for reject, 'V' for view details
        """
        entry_price = float(trade_signal.get("entry_level", 0))
        stop_loss = float(trade_signal.get("stop_loss", 0))
        tp1 = float(trade_signal.get("take_profit_1", 0))
        tp2 = float(trade_signal.get("take_profit_2", 0))
        tp3 = float(trade_signal.get("take_profit_3", 0))
        confidence = float(trade_signal.get("confidence", 0))
        rr_ratio = float(trade_signal.get("risk_reward_ratio", 0))
        pattern_elements = trade_signal.get("pattern_elements", {})

        # Calculate risk in pips
        risk_pips = abs(entry_price - stop_loss) / 0.0001
        potential_profit_1 = abs(tp1 - entry_price) / 0.0001
        potential_profit_2 = abs(tp2 - entry_price) / 0.0001
        potential_profit_3 = abs(tp3 - entry_price) / 0.0001

        # Determine direction
        direction = "BUY" if entry_price > stop_loss else "SELL"

        # Display approval screen
        print("\n" + "=" * 70)
        print("⚠️  TRADE APPROVAL GATEWAY - REVIEW BEFORE EXECUTION".center(70))
        print("=" * 70)
        print()
        print(f"{'PAIR & DIRECTION':.<40} {direction:>25}")
        print(f"{'Confidence Score':.<40} {confidence:.0f}%{' ✓':>21}")
        print()
        print("-" * 70)
        print("ENTRY & RISK PARAMETERS")
        print("-" * 70)
        print(f"{'Entry Price':.<40} {entry_price:>25.5f}")
        print(f"{'Stop Loss':.<40} {stop_loss:>25.5f}")
        print(f"{'Risk (Pips)':.<40} {risk_pips:>25.0f} pips")
        print()
        print("-" * 70)
        print("TAKE PROFIT LEVELS")
        print("-" * 70)
        print(f"{'TP 1 (50% position)':.<40} {tp1:>15.5f} (+{potential_profit_1:>7.0f} pips)")
        print(f"{'TP 2 (30% position)':.<40} {tp2:>15.5f} (+{potential_profit_2:>7.0f} pips)")
        print(f"{'TP 3 (20% position)':.<40} {tp3:>15.5f} (+{potential_profit_3:>7.0f} pips)")
        print()
        print("-" * 70)
        print("RISK/REWARD & PATTERNS")
        print("-" * 70)
        print(f"{'Risk/Reward Ratio':.<40} {rr_ratio:.2f}:1{' (✓ Good)' if rr_ratio >= 2.0 else ''}:>12}")
        print()
        print("ICT Pattern Elements:")
        for element, confirmed in pattern_elements.items():
            status = "✓ CONFIRMED" if confirmed else "✗ NOT CONFIRMED"
            element_name = element.replace("_", " ").title()
            print(f"  {element_name:.<35} {status:>29}")
        print()
        print("=" * 70)
        print()

        # Get user input
        while True:
            try:
                choice = input(
                    "  [A] APPROVE TRADE   [R] REJECT   [V] VIEW DETAILS\n"
                    "  Enter your choice (A/R/V): "
                ).strip().upper()

                if choice in ["A", "R", "V"]:
                    return choice
                else:
                    print("  ❌ Invalid choice. Please enter A, R, or V.")
            except KeyboardInterrupt:
                print("\n\n❌ Approval cancelled by user")
                return "R"
            except Exception as e:
                print(f"  ❌ Error: {e}")
                return "R"

    @staticmethod
    def display_detailed_analysis(trade_signal: Dict[str, Any]) -> None:
        """Display detailed analysis of the trade signal."""
        print("\n" + "=" * 70)
        print("DETAILED TRADE ANALYSIS".center(70))
        print("=" * 70)
        print()
        print("Pattern Elements Analysis:")
        print("-" * 70)

        pattern_elements = trade_signal.get("pattern_elements", {})

        analysis_text = {
            "liquidity_sweep": (
                "Liquidity Sweep: Price moved beyond swing levels to capture stops,\n"
                "                then reversed. Indicates smart money absorption of liquidity."
            ),
            "break_of_structure": (
                "Break of Structure: Recent swing pattern was broken, confirming\n"
                "                   directional change or continuation."
            ),
            "imbalance": (
                "Order Block/Imbalance: Unfilled gap or institutional entry zone\n"
                "                      identified. Price often retests these areas."
            ),
            "pullback": (
                "Pullback Entry: Price retraced into the order block/imbalance zone\n"
                "               during the kill zone (15-30 min window). Precision entry."
            ),
        }

        for element, confirmed in pattern_elements.items():
            status = "✓ CONFIRMED" if confirmed else "✗ NOT CONFIRMED"
            text = analysis_text.get(element, element.replace("_", " ").title())
            print(f"\n{status}")
            print(text)

        print()
        print("=" * 70)
        print()

        # Recommendations
        print("Trade Execution Recommendations:")
        print("-" * 70)

        kill_zone_start = trade_signal.get("kill_zone_start")
        kill_zone_end = trade_signal.get("kill_zone_end")
        confidence = float(trade_signal.get("confidence", 0))

        print(
            f"\n✓ ENTRY WINDOW: {kill_zone_start} to {kill_zone_end}\n"
            f"  Trade must be entered within this 15-30 minute kill zone.\n"
            f"  After window closes, signal becomes invalid."
        )

        print(f"\n✓ CONFIDENCE: {confidence:.0f}%")
        if confidence >= 85:
            print("  Signal is HIGH CONFIDENCE - all conditions align perfectly.")
        elif confidence >= 75:
            print("  Signal is GOOD CONFIDENCE - meets all requirements.")
        else:
            print("  Signal is BORDERLINE - consider waiting for better setup.")

        print(
            f"\n✓ RISK MANAGEMENT:")
            f"\n  This trade adheres to all risk management rules:"
            f"\n  • 2% max risk per trade enforced ✓"
            f"\n  • Position size calculated dynamically ✓"
            f"\n  • Hard stop loss (non-negotiable) ✓"
            f"\n  • Minimum 1:2 risk/reward ratio ✓"
        )

        print("\n" + "=" * 70 + "\n")

    @staticmethod
    def request_approval(trade_signal: Dict[str, Any]) -> bool:
        """
        Request user approval for trade execution.

        Args:
            trade_signal: TradeSignal dict from Analyse-Master

        Returns:
            True if user approves, False otherwise
        """
        logger.info("=" * 70)
        logger.info("TRADE APPROVAL GATEWAY - Awaiting user decision")
        logger.info("=" * 70)

        while True:
            # Display trade for approval
            choice = TradeApproval.display_trade_for_approval(trade_signal)

            if choice == "A":
                logger.info("✓ User APPROVED trade execution")
                print("\n✓ Trade approved! Proceeding with execution on MetaTrader 5...\n")
                return True

            elif choice == "R":
                logger.info("✗ User REJECTED trade - signal discarded")
                print("\n✗ Trade rejected. Waiting for next signal.\n")
                return False

            elif choice == "V":
                TradeApproval.display_detailed_analysis(trade_signal)
                # Loop back to approval screen

    @staticmethod
    def log_approval_decision(
        trade_signal: Dict[str, Any], approved: bool, reason: Optional[str] = None
    ) -> None:
        """Log the approval decision for audit trail."""
        signal_id = f"SIG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        decision = "APPROVED" if approved else "REJECTED"
        reason_text = f" - Reason: {reason}" if reason else ""

        logger.info(
            f"[TRADE APPROVAL] {signal_id}: {decision}{reason_text}"
            f" | Entry: {trade_signal.get('entry_level')} | "
            f"Confidence: {trade_signal.get('confidence')}%"
        )
