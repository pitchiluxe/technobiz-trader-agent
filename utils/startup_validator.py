"""
Production startup validator.

Ensures all required environment variables and configurations are set before trading.
Fails fast if running in production without proper setup.
"""

import os
import sys
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class StartupValidator:
    """Validates production readiness before trading."""

    # Required environment variables for production
    REQUIRED_ENV_VARS = {
        "MT5_ACCOUNT": "MetaTrader 5 account number",
        "MT5_PASSWORD": "MetaTrader 5 password",
        "MT5_SERVER": "MetaTrader 5 broker server",
        "ACCOUNT_BALANCE": "Trading account balance (USD)",
        "DATABASE_URL": "PostgreSQL connection string (required for production)",
        "FOUNDRY_PROJECT_ENDPOINT": "Azure AI Foundry endpoint URL",
        "FOUNDRY_MODEL_DEPLOYMENT_NAME": "Azure AI Foundry model deployment name",
        "FOUNDRY_API_KEY": "Azure AI Foundry API key",
    }

    # Optional but recommended
    OPTIONAL_ENV_VARS = {
        "ENABLE_EMAIL_NOTIFICATIONS": "Email notification support",
        "EMAIL_RECIPIENT": "Email address for alerts",
        "ENABLE_TELEGRAM_NOTIFICATIONS": "Telegram notification support",
        "TELEGRAM_BOT_TOKEN": "Telegram bot token",
    }

    @staticmethod
    def validate() -> bool:
        """
        Validate all required environment variables are set.

        Returns:
            True if all required vars are set, False otherwise.

        Raises:
            SystemExit if validation fails in strict mode.
        """
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        missing_vars = []
        invalid_vars = []

        # Check required variables
        for var_name, description in StartupValidator.REQUIRED_ENV_VARS.items():
            value = os.getenv(var_name, "").strip()
            if not value:
                missing_vars.append((var_name, description))
            elif var_name == "ACCOUNT_BALANCE":
                try:
                    float(value)
                except ValueError:
                    invalid_vars.append((var_name, f"Must be numeric (got '{value}')"))
            elif var_name == "DATABASE_URL":
                if "sqlite" in value.lower() and is_production:
                    invalid_vars.append(
                        (
                            var_name,
                            "SQLite not allowed in production. Use PostgreSQL.",
                        )
                    )

        # Report findings
        if missing_vars or invalid_vars:
            logger.error("=" * 70)
            logger.error("STARTUP VALIDATION FAILED")
            logger.error("=" * 70)

            if missing_vars:
                logger.error("\n❌ MISSING REQUIRED ENVIRONMENT VARIABLES:")
                for var_name, description in missing_vars:
                    logger.error(f"   - {var_name:30} ({description})")

            if invalid_vars:
                logger.error("\n❌ INVALID ENVIRONMENT VARIABLES:")
                for var_name, reason in invalid_vars:
                    logger.error(f"   - {var_name:30} {reason}")

            logger.error("\n" + "=" * 70)
            logger.error("ACTION REQUIRED:")
            logger.error("  1. Copy .env.template to .env")
            logger.error("  2. Fill in all required variables")
            logger.error("  3. Ensure MT5 terminal is running")
            logger.error("  4. Verify database connectivity")
            logger.error("=" * 70 + "\n")

            if is_production:
                logger.critical("EXITING: Production mode requires all variables to be set.")
                sys.exit(1)

            return False

        logger.info("✅ Startup validation PASSED - All required environment variables are set")
        return True

    @staticmethod
    def check_mt5_terminal() -> bool:
        """
        Check if MetaTrader 5 terminal is running and accessible.

        Returns:
            True if MT5 is available, False otherwise.
        """
        try:
            import MetaTrader5 as mt5

            if mt5.initialize():
                logger.info("✅ MetaTrader 5 terminal is accessible")
                mt5.shutdown()
                return True
            else:
                logger.warning(
                    "⚠️  MetaTrader 5 not initialized. Is the terminal running?"
                )
                return False
        except ImportError:
            logger.warning("⚠️  MetaTrader5 package not installed. Run: pip install MetaTrader5")
            return False
        except Exception as e:
            logger.warning(f"⚠️  Could not connect to MT5: {e}")
            return False

    @staticmethod
    def check_database() -> bool:
        """
        Check if database is accessible.

        Returns:
            True if database connection succeeds, False otherwise.
        """
        from config.settings import settings
        from database.db_manager import db_manager

        try:
            session = db_manager.get_session()
            session.close()
            logger.info(f"✅ Database connection successful: {settings.DATABASE_URL}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Database connection failed: {e}")
            return False

    @staticmethod
    def full_startup_check() -> bool:
        """
        Perform complete startup validation including env vars, MT5, and database.

        Returns:
            True if all checks pass, False if any check fails (non-blocking in dev).
        """
        logger.info("\n" + "=" * 70)
        logger.info("RUNNING PRODUCTION STARTUP VALIDATION")
        logger.info("=" * 70 + "\n")

        checks = [
            ("Environment Variables", StartupValidator.validate),
            ("MetaTrader 5 Terminal", StartupValidator.check_mt5_terminal),
            ("Database Connection", StartupValidator.check_database),
        ]

        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                logger.error(f"❌ {check_name} check failed: {e}")
                results.append((check_name, False))

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("VALIDATION SUMMARY:")
        for check_name, result in results:
            status = "✅ PASS" if result else "⚠️  FAIL"
            logger.info(f"  {check_name:.<40} {status}")
        logger.info("=" * 70 + "\n")

        all_passed = all(result for _, result in results)
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

        if is_production and not all_passed:
            logger.critical("EXITING: Production mode with failed checks.")
            sys.exit(1)

        return all_passed
