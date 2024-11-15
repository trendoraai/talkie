import logging
import os
from typing import Optional


def setup_global_logger(
    name: str = "talkie", log_file: Optional[str] = None
) -> logging.Logger:
    """Configure global logger with environment-based log level control and enhanced formatting.

    Args:
        name: Logger name, defaults to "talkie"
        log_file: Optional log file path. If None, only console logging is enabled

    Returns:
        Configured logger instance
    """
    # Get log level from environment, default to INFO
    log_level = os.environ.get("LOG", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    # Enhanced formatter with thread name and module for better debugging
    formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s:%(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler - always enabled
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers = []

    # Add console handler
    logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Logging to file: {log_file}")

    logger.debug(f"Logger '{name}' initialized with level {log_level}")
    return logger


# Create the global logger
talkie_logger = setup_global_logger()
