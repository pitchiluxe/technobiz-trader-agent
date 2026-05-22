"""
Interactive Trading Manager with Multi-Pair Support

Allows users to:
- Select trading pairs dynamically
- Run trading cycles for multiple pairs
- Monitor each pair through the strict workflow
- Switch pairs without restarting the system
"""

import logging
from typing import List, Optional, Dict, Any
from config.trading_pairs_config import pairs_registry, TradingPair, AssetClass

logger = logging.getLogger(__name__)


class InteractiveTradingManager:
    """Manages interactive user input for pair selection and trading."""

    def __init__(self):
        """Initialize the trading manager."""
        self.selected_pairs: List[TradingPair] = []
        self.current_pair_index = 0

        logger.info("[TRADING-MANAGER] Interactive Trading Manager initialized")

    def display_welcome(self) -> None:
        """Display welcome banner."""
        print("\n" + "═" * 70)
        print("  TechnobizTrader — Multi-Pair Trading Agent")
        print("═" * 70)
        print("  ICT-Based Methodology: Trend → Analysis → Execution")
        print("  Strict workflow enforcement with real-time validation")
        print("═" * 70 + "\n")

    def display_pair_categories(self) -> None:
        """Display available pair categories."""
        print("\n[PAIRS] Available Asset Classes:")
        for i, asset_class in enumerate(AssetClass, 1):
            count = len(pairs_registry.get_pairs_by_asset_class(asset_class))
            print(f"  {i}. {asset_class.value:<15} ({count} pairs)")

    def display_pairs_by_category(self, asset_class: AssetClass) -> None:
        """Display all pairs in a category."""
        pairs = pairs_registry.get_pairs_by_asset_class(asset_class)

        print(f"\n[PAIRS] {asset_class.value} Pairs:")
        print("-" * 70)

        for i, pair in enumerate(pairs, 1):
            print(f"  {i:2d}. {pair.symbol:<10} | {pair.description}")

        print("-" * 70)

    def enter_custom_pair(self) -> Optional[TradingPair]:
        """Allow user to enter any custom trading pair."""
        print("\n[CUSTOM] Enter Trading Pair Details")
        print("-" * 70)

        try:
            symbol = input("Enter pair symbol (e.g., EURUSD, BTCUSD, CUSTOMUSD): ").strip().upper()

            if not symbol:
                print("[ERROR] Symbol cannot be empty")
                return None

            if not symbol.isalpha():
                print("[ERROR] Symbol must contain only letters")
                return None

            if len(symbol) < 3 or len(symbol) > 10:
                print("[ERROR] Symbol must be 3-10 characters")
                return None

            print("\n[ASSET] Select Asset Class for this pair:")
            for i, asset_class in enumerate(AssetClass, 1):
                print(f"  {i}. {asset_class.value}")

            asset_choice = int(input("Enter asset class number (1-5): "))
            asset_classes = list(AssetClass)

            if not (1 <= asset_choice <= len(asset_classes)):
                print("[ERROR] Invalid asset class")
                return None

            selected_class = asset_classes[asset_choice - 1]

            pip_value = float(input("Enter pip value (default 0.0001): ") or "0.0001")
            min_lot = float(input("Enter minimum lot size (default 0.01): ") or "0.01")
            max_lot = float(input("Enter maximum lot size (default 100.0): ") or "100.0")

            description = f"Custom {selected_class.value} pair"

            pair = pairs_registry.register_custom_pair(
                symbol=symbol,
                asset_class=selected_class,
                pip_value=pip_value,
                min_lot_size=min_lot,
                max_lot_size=max_lot,
                description=description,
            )

            print(f"\n[OK] Registered custom pair: {pair.symbol}")
            return pair

        except ValueError as e:
            print(f"[ERROR] Invalid input: {e}")
            return None

    def select_from_category(self) -> Optional[TradingPair]:
        """Allow user to select a single pair from a category."""
        print("\n[SELECT] Choose Asset Class:")
        self.display_pair_categories()

        try:
            category_choice = int(input("\nEnter category number (1-5): "))
            asset_classes = list(AssetClass)

            if 1 <= category_choice <= len(asset_classes):
                selected_class = asset_classes[category_choice - 1]
                self.display_pairs_by_category(selected_class)

                pairs = pairs_registry.get_pairs_by_asset_class(selected_class)
                pair_choice = int(input(f"Enter pair number (1-{len(pairs)}): "))

                if 1 <= pair_choice <= len(pairs):
                    return pairs[pair_choice - 1]

            print("[ERROR] Invalid selection")
            return None

        except ValueError:
            print("[ERROR] Please enter a valid number")
            return None

    def select_multiple_pairs(self) -> bool:
        """Allow user to select multiple pairs for trading."""
        print("\n[SELECT] Multi-Pair Trading Setup")
        print("-" * 70)
        print("Add pairs one at a time. Type 'done' to start trading.\n")

        added_pairs = []

        while True:
            print(f"[PAIRS] Currently selected: {[p.symbol for p in added_pairs]}")
            print("\n[OPTIONS] How to add pair:")
            print("  1. Select from registry")
            print("  2. Enter custom pair symbol")

            option = input("Choose (1-2): ").strip()

            pair = None
            if option == '1':
                pair = self.select_from_category()
            elif option == '2':
                pair = self.enter_custom_pair()
            else:
                print("[ERROR] Invalid option")
                continue

            if pair:
                if pair.symbol in [p.symbol for p in added_pairs]:
                    print(f"[INFO] {pair.symbol} already selected")
                    continue

                added_pairs.append(pair)
                print(f"[OK] Added {pair.symbol}")
                print(f"[COUNT] Total pairs: {len(added_pairs)}\n")

            user_input = input("Add another pair? (yes/no/done): ").strip().lower()
            if user_input in ['no', 'done', 'q']:
                break

        if added_pairs:
            self.selected_pairs = added_pairs
            symbols = [p.symbol for p in self.selected_pairs]
            logger.info(f"[TRADING-MANAGER] Pairs selected: {symbols}")
            return True
        else:
            print("[WARNING] No pairs selected")
            return False

    def select_single_pair(self) -> bool:
        """Allow user to select a single pair."""
        pair = self.select_from_category()

        if pair:
            self.selected_pairs = [pair]
            logger.info(f"[TRADING-MANAGER] Pair selected: {pair.symbol}")
            return True
        else:
            print("[ERROR] Failed to select pair")
            return False

    def display_selection_menu(self) -> bool:
        """Display main selection menu."""
        print("\n[MENU] Trading Setup")
        print("-" * 70)
        print("  1. Trade Single Pair (from registry)")
        print("  2. Trade Multiple Pairs")
        print("  3. Enter Custom Pair Symbol")
        print("  4. View All Available Pairs")
        print("  5. Exit")
        print("-" * 70)

        try:
            choice = input("\nSelect option (1-5): ").strip()

            if choice == '1':
                return self.select_single_pair()
            elif choice == '2':
                return self.select_multiple_pairs()
            elif choice == '3':
                pair = self.enter_custom_pair()
                if pair:
                    self.selected_pairs = [pair]
                    return True
                return self.display_selection_menu()
            elif choice == '4':
                self.display_all_pairs()
                return self.display_selection_menu()
            elif choice == '5':
                print("[EXIT] User cancelled")
                return False
            else:
                print("[ERROR] Invalid option")
                return self.display_selection_menu()

        except KeyboardInterrupt:
            print("\n[EXIT] User cancelled")
            return False

    def display_all_pairs(self) -> None:
        """Display all available pairs organized by category."""
        print("\n[PAIRS] Complete Registry")
        print("=" * 70)

        for asset_class in AssetClass:
            pairs = pairs_registry.get_pairs_by_asset_class(asset_class)
            print(f"\n{asset_class.value}:")
            print("-" * 70)

            for pair in pairs:
                print(
                    f"  {pair.symbol:<10} | Min: {pair.min_lot_size}L | "
                    f"Max: {pair.max_lot_size}L | {pair.description}"
                )

    def get_selected_pairs(self) -> List[TradingPair]:
        """Get list of selected pairs."""
        return self.selected_pairs

    def get_current_pair(self) -> Optional[TradingPair]:
        """Get currently trading pair."""
        if 0 <= self.current_pair_index < len(self.selected_pairs):
            return self.selected_pairs[self.current_pair_index]
        return None

    def switch_to_next_pair(self) -> Optional[TradingPair]:
        """Switch to next pair in the list."""
        if len(self.selected_pairs) > 1:
            self.current_pair_index = (self.current_pair_index + 1) % len(
                self.selected_pairs
            )
            pair = self.get_current_pair()
            logger.info(
                f"[TRADING-MANAGER] Switched to pair: {pair.symbol}"
            )
            return pair

        return self.get_current_pair()

    def display_selection_summary(self) -> None:
        """Display summary of selected pairs."""
        print("\n" + "=" * 70)
        print("  TRADING SETUP SUMMARY")
        print("=" * 70)
        print(f"  Pairs: {len(self.selected_pairs)}")

        for i, pair in enumerate(self.selected_pairs, 1):
            print(
                f"  {i}. {pair.symbol:<10} | {pair.asset_class.value:<12} | "
                f"{pair.description}"
            )

        print("=" * 70 + "\n")

    def validate_pairs(self) -> bool:
        """Validate selected pairs for trading."""
        if not self.selected_pairs:
            logger.error("[TRADING-MANAGER] No pairs selected")
            return False

        logger.info(
            f"[TRADING-MANAGER] Validating {len(self.selected_pairs)} pair(s)"
        )

        for pair in self.selected_pairs:
            logger.info(
                f"[TRADING-MANAGER] ✓ {pair.symbol} | {pair.asset_class.value}"
            )

        return True

    @staticmethod
    def display_quick_start() -> None:
        """Display quick start guide."""
        print("\n" + "=" * 70)
        print("  QUICK START GUIDE")
        print("=" * 70)
        print("\n[WORKFLOW] Strict Three-Phase Execution:")
        print("  PHASE 1: Trend-Master analyzes market structure")
        print("           → Identifies bias (BULLISH/BEARISH/NEUTRAL)")
        print("           → Returns support/resistance with confidence score")
        print()
        print("  PHASE 2: Analyse-Master detects ICT patterns")
        print("           → Confirms Liquidity Sweep")
        print("           → Confirms Break of Structure")
        print("           → Identifies Order Block & Imbalance")
        print("           → Validates Pullback Entry (kill zone: 15-30 min)")
        print()
        print("  PHASE 3: Trader-Master executes trade")
        print("           → Validates risk/reward ≥ 1:2")
        print("           → Validates confidence ≥ 75%")
        print("           → Places order with hard stop loss")
        print("           → Monitors position with tiered exits (50/30/20%)")
        print()
        print("[GUARDRAILS] Risk Management:")
        print("  • Max 2% risk per trade")
        print("  • Max 3 concurrent open trades")
        print("  • Max 5% daily drawdown (auto-pause)")
        print("  • Minimum 40% win rate threshold")
        print()
        print("=" * 70 + "\n")
