"""Logging configuration."""

import logging
import logging.handlers
import os
from config.settings import settings


def setup_logging():
    """Configure logging for the application."""
    
    # Create log directory if needed (skip if LOG_FILE is in writable userData)
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except PermissionError:
            # Fallback: write log beside backend.log in userData
            userdata = os.getenv("TECHNOBIZ_USERDATA", "")
            if userdata:
                settings.LOG_FILE = os.path.join(userdata, "technobiz_trader.log")
            else:
                settings.LOG_FILE = os.devnull

    # Create logger
    logger = logging.getLogger()
    if logger.handlers:
        return logger  # already configured — don't add duplicate handlers
    logger.setLevel(settings.LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)

    # File handler (with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
