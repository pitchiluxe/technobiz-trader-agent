"""
TechnobizTrader - Interactive Trading Mode

Allows users to:
- Analyze any trading pair
- Request trend analysis
- Generate trade signals with approval gateway
- Execute trades after user confirmation
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from agents.workflow import TradingWorkflow
from config.settings import settings
from database.db_manager import db_manager
from market_data.mt5_provider import MT5Provider
from utils.logger import setup_logging
from utils.startup_validator import StartupValidator
from utils.trade_approval import TradeApproval

setup_logging()
logger = logging.getLogger(__name__)


class InteractiveTradingMode:
    """Interactive mode for dynamic pair analysis and trading."""

    def __init__(self):
        """Initialize interactive trading mode."""
        self.workflow: Optional[TradingWorkflow] = None
        self.provider: Optional[MT5Provider] = None
        self.trading_history: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        """
        Initialize all components.

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 70)
        logger.info("TECHNOBIZTRADER - INTERACTIVE MODE")
        logger.info(f"Version: {settings.APP_VERSION}")
        logger.info("=" * 70)

        try:
            # Validate startup
            logger.info("\n[INIT] Running startup validation...")
            if not StartupValidator.validate():
                if settings.ENVIRONMENT == "production":
                    logger.error("Startup validation failed in production mode")
                    return False
                logger.warning("Non-critical validation warnings")

            # Initialize database
            logger.info("[INIT] Initializing database...")
            db_manager.create_tables()
            logger.info("✓ Database ready")

            # Initialize workflow
            logger.info("[INIT] Initializing trading agents...")
            verbose_mode = settings.DEBUG and settings.ENVIRONMENT != "production"
            self.workflow = TradingWorkflow(verbose=verbose_mode)
            logger.info("✓ Trend-Master, Analyse-Master, Trader-Master initialized")

            # Initialize MT5 provider
            logger.info("[INIT] Connecting to MetaTrader 5...")
            self.provider = MT5Provider(
                account=settings.MT5_ACCOUNT,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER,
            )

            connected = await self.provider.connect()
            if not connected:
                logger.error("Failed to connect to MetaTrader 5 terminal")
                logger.error("Ensure MT5 terminal is running and credentials are correct")
                return False

            logger.info("✓ MetaTrader 5 connected")
            logger.info("\n" + "=" * 70)
            logger.info("✅ INITIALIZATION COMPLETE - Ready for trading")
            logger.info("=" * 70)
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    async def fetch_pair_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch market data for a specific pair.

        Args:
            symbol: Trading pair symbol (e.g., "EURUSD")

        Returns:
            Market data dict with timeframes, or None if fetch fails
        """
        try:
            logger.info(f"\n[DATA] Fetching market data for {symbol}...")

            market_data = {}
            timeframes = {"daily": ("D", 100), "4h": ("4H", 100), "1h": ("1H", 100)}

            for key, (tf_symbol, limit) in timeframes.items():
                try:
                    candles = await self.provider.get_candles(symbol, tf_symbol, limit=limit)
                    if candles:
                        market_data[key] = candles
                        logger.info(f"  ✓ Fetched {len(candles)} {tf_symbol} candles")
                    else:
                        logger.warning(f"  ✗ No {tf_symbol} candles for {symbol}")
                except Exception as e:
                    logger.error(f"  ✗ Error fetching {tf_symbol}: {e}")

            if not all(market_data.values()):
                logger.error(f"Insufficient data for {symbol}")
                return None

            return market_data

        except Exception as e:
            logger.error(f"Data fetch failed: {e}")
            return None

    async def analyze_pair(
        self, symbol: str, analysis_only: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a specific trading pair.

        Args:
            symbol: Trading pair symbol
            analysis_only: If True, only show trend analysis; don't generate trades

        Returns:
            Analysis result or None
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"ANALYZING {symbol} - Starting complete analysis pipeline")
        logger.info("=" * 70)

        try:
            # Step 1: Fetch data
            market_data = await self.fetch_pair_data(symbol)
            if not market_data:
                logger.error(f"Cannot analyze {symbol} - no market data")
                return None

            # Step 2: Trend Analysis
            logger.info(f"\n[STEP 1] Trend-Master analyzing {symbol}...")
            trend_report = await self.workflow.trend_master.analyze(market_data)
            if not trend_report:
                logger.warning("No trend report generated")
                return None

            logger.info(f"✓ Trend: {trend_report.bias} (Confidence: {trend_report.confidence}%)")
            logger.info(f"  Support Levels: {trend_report.support_resistance.get('support_levels', [])}")
            logger.info(
                f"  Resistance Levels: {trend_report.support_resistance.get('resistance_levels', [])}"
            )

            # If analysis-only mode, stop here
            if analysis_only:
                logger.info(f"\n[INFO] Analysis complete for {symbol}")
                logger.info("No trade signals generated (analysis-only mode)")
                return {"trend_report": trend_report}

            # Step 3: Signal Generation
            logger.info(f"\n[STEP 2] Analyse-Master scanning for ICT patterns in {symbol}...")
            trade_signal = await self.workflow.analyse_master.analyze(
                trend_report.to_dict(), candle_data=market_data
            )

            if not trade_signal:
                logger.info("No ICT trade signals found - waiting for pattern alignment")
                return {"trend_report": trend_report}

            logger.info(
                f"✓ Trade Signal Generated! (Confidence: {trade_signal.confidence}%)"
            )
            logger.info(f"  Entry: {trade_signal.entry_level}")
            logger.info(f"  Stop Loss: {trade_signal.stop_loss}")
            logger.info(f"  R/R Ratio: {trade_signal.risk_reward_ratio}:1")

            return {"trend_report": trend_report, "trade_signal": trade_signal}

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return None

    async def execute_trade_with_approval(
        self, symbol: str, trade_signal: Dict[str, Any]
    ) -> bool:
        """
        Execute trade after user approval.

        Args:
            symbol: Trading pair
            trade_signal: TradeSignal dict from Analyse-Master

        Returns:
            True if trade executed, False if rejected
        """
        logger.info(f"\n[STEP 3] Trader-Master processing {symbol}...")

        # REQUEST APPROVAL
        approved = TradeApproval.request_approval(trade_signal)

        if not approved:
            logger.info("Trade rejected by user - signal discarded")
            TradeApproval.log_approval_decision(trade_signal, False, "User rejection")
            return False

        # Execute trade
        try:
            logger.info("Executing trade on MetaTrader 5...")
            execution_record = await self.workflow.trader_master.analyze(trade_signal)

            if execution_record:
                logger.info("=" * 70)
                logger.info("✅ TRADE EXECUTED SUCCESSFULLY")
                logger.info("=" * 70)
                logger.info(f"Signal ID: {execution_record.signal_id}")
                logger.info(f"Entry Price: {execution_record.entry_price}")
                logger.info(f"Position Size: {execution_record.position_size} lots")
                logger.info(f"Stop Loss: {execution_record.stop_loss}")
                logger.info(f"Status: {execution_record.status}")
                logger.info("=" * 70)

                # Store in history
                self.trading_history.append(execution_record.to_dict())
                TradeApproval.log_approval_decision(trade_signal, True, "Trade executed")
                return True
            else:
                logger.warning("Trade execution failed - validation error")
                TradeApproval.log_approval_decision(
                    trade_signal, False, "Trader validation failed"
                )
                return False

        except Exception as e:
            logger.error(f"Trade execution error: {e}", exc_info=True)
            return False

    def display_menu(self) -> str:
        """Display main menu and get user choice."""
        print("\n" + "=" * 70)
        print("MAIN MENU".center(70))
        print("=" * 70)
        print()
        print("  [1] Analyze trading pair (trend only)")
        print("  [2] Analyze and generate trade signal")
        print("  [3] Execute trade with approval")
        print("  [4] View trading history")
        print("  [5] Analyze multiple pairs")
        print("  [6] Settings")
        print("  [7] Exit")
        print()
        print("=" * 70)

        choice = input("Enter your choice (1-7): ").strip()
        return choice

    async def interactive_session(self) -> None:
        """Run interactive trading session."""
        print("\n" + "=" * 70)
        print("Welcome to TechnobizTrader Interactive Mode".center(70))
        print("=" * 70)
        print()
        print("You can analyze any trading pair and approve/reject trades manually.")
        print("The system requires your approval before executing any trades on MT5.")
        print()

        while True:
            try:
                choice = self.display_menu()

                if choice == "1":
                    # Trend analysis only
                    symbol = input("\nEnter trading pair (e.g., EURUSD): ").strip().upper()
                    if symbol:
                        result = await self.analyze_pair(symbol, analysis_only=True)
                        if result:
                            print("\n✓ Trend analysis complete")

                elif choice == "2":
                    # Analyze and generate signal
                    symbol = input("\nEnter trading pair (e.g., EURUSD): ").strip().upper()
                    if symbol:
                        result = await self.analyze_pair(symbol, analysis_only=False)
                        if result and "trade_signal" in result:
                            # Signal generated, ask about execution
                            exec_choice = input(
                                "\nTrade signal generated. Execute now? (Y/N): "
                            ).strip().upper()
                            if exec_choice == "Y":
                                await self.execute_trade_with_approval(
                                    symbol, result["trade_signal"].to_dict()
                                )

                elif choice == "3":
                    # Manual pair selection and execution
                    symbol = input("\nEnter trading pair for manual analysis: ").strip().upper()
                    if symbol:
                        result = await self.analyze_pair(symbol)
                        if result and "trade_signal" in result:
                            await self.execute_trade_with_approval(
                                symbol, result["trade_signal"].to_dict()
                            )

                elif choice == "4":
                    # View history
                    self.display_trading_history()

                elif choice == "5":
                    # Analyze multiple pairs
                    pairs_input = input(
                        "\nEnter trading pairs (comma-separated, e.g., EURUSD,GBPUSD,XAUUSD): "
                    ).strip()
                    pairs = [p.strip().upper() for p in pairs_input.split(",")]
                    for pair in pairs:
                        if pair:
                            result = await self.analyze_pair(pair, analysis_only=True)
                            if result:
                                await asyncio.sleep(1)  # Brief pause between pairs

                elif choice == "6":
                    # Settings
                    self.display_settings()

                elif choice == "7":
                    # Exit
                    print("\n✓ Shutting down...")
                    break

                else:
                    print("❌ Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print("\n\n✓ Session interrupted by user")
                break
            except Exception as e:
                logger.error(f"Session error: {e}")
                print(f"❌ Error: {e}")

    def display_trading_history(self) -> None:
        """Display trading history."""
        print("\n" + "=" * 70)
        print("TRADING HISTORY".center(70))
        print("=" * 70)

        if not self.trading_history:
            print("No trades executed in this session")
        else:
            for i, trade in enumerate(self.trading_history, 1):
                print(f"\nTrade #{i}:")
                print(f"  Signal ID: {trade.get('signal_id')}")
                print(f"  Entry: {trade.get('entry_price')}")
                print(f"  Size: {trade.get('position_size')} lots")
                print(f"  Status: {trade.get('status')}")

        print("\n" + "=" * 70)

    def display_settings(self) -> None:
        """Display settings."""
        print("\n" + "=" * 70)
        print("SETTINGS".center(70))
        print("=" * 70)
        print(f"\nAccount Balance: ${settings.ACCOUNT_BALANCE:,.2f}")
        print(f"Max Risk Per Trade: {settings.MAX_RISK_PER_TRADE * 100}%")
        print(f"Max Concurrent Trades: {settings.MAX_CONCURRENT_TRADES}")
        print(f"Min Confidence Threshold: {settings.MIN_CONFIDENCE_THRESHOLD}%")
        print(f"Database: {settings.DATABASE_URL}")
        print("\n" + "=" * 70)

    async def shutdown(self) -> None:
        """Clean shutdown."""
        logger.info("\nShutting down...")
        if self.provider:
            await self.provider.disconnect()
        db_manager.close()
        logger.info("✓ Shutdown complete")


async def main():
    """Main entry point for interactive mode."""
    trader = InteractiveTradingMode()

    try:
        # Initialize
        if not await trader.initialize():
            logger.error("Initialization failed")
            return

        # Run interactive session
        await trader.interactive_session()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await trader.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
