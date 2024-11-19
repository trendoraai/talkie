import logging
import os
from datetime import datetime
from typing import Optional
from pathlib import Path


def setup_global_logger(
    name: str = "talkie",
    log_file: Optional[str] = None,
    chat_file: Optional[str] = None,
) -> logging.Logger:
    """Configure global logger with environment-based log level control and enhanced formatting.

    Args:
        name: Logger name, defaults to "talkie"
        log_file: Optional log file path. If None, a timestamped file will be created in current directory
        chat_file: Optional chat file path. If provided, will create a log file based on the chat file name

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

    # If chat_file is provided, create a log file based on its name
    if chat_file:
        chat_path = Path(chat_file)
        log_dir = chat_path.parent / ".logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = log_dir / f"{chat_path.stem}.log"
    # If no log_file specified, create a timestamped one in current directory
    elif log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{timestamp}.talkie.log"

    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(str(log_file))
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create the global logger
talkie_logger = setup_global_logger()
