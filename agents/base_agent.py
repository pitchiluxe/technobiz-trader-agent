"""Base Agent Class - Common functionality for all agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    Provides common initialization, logging, and communication patterns.
    """

    def __init__(self, name: str, instructions: str, verbose: bool = False):
        """
        Initialize the base agent.

        Args:
            name: Agent identifier
            instructions: System instructions for the agent
            verbose: Enable detailed logging
        """
        self.name = name
        self.instructions = instructions
        self.verbose = verbose
        self.logger = logging.getLogger(f"{__name__}.{name}")

        if verbose:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    @abstractmethod
    async def analyze(self, *args: Any, **kwargs: Any) -> Any:
        """
        Analyze data and produce output.

        Args:
            data: Input data for analysis

        Returns:
            Analysis results
        """
        pass

    def log_analysis(self, message: str, level: str = "info"):
        """Log analysis results."""
        if level == "debug":
            self.logger.debug(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)

    async def validate_input(self, data: Dict[str, Any], required_keys: list) -> bool:
        """
        Validate that all required keys are present in input data.

        Args:
            data: Input data dictionary
            required_keys: List of required keys

        Returns:
            True if all required keys present, False otherwise
        """
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            self.logger.error(f"Missing required keys: {missing_keys}")
            return False
        return True
