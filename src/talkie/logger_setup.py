import logging
import os


def setup_global_logger(name="talkie", log_file="talkie.log"):
    """Configure global logger with environment-based log level control."""
    # Get log level from environment, default to INFO
    log_level = os.environ.get("LOG", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add handlers if they haven't been added already
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


# Create the global logger
talkie_logger = setup_global_logger()
