from dataclasses import dataclass
from pathlib import Path
import os
import yaml
from typing import Optional
from .logger_setup import talkie_logger as logger


@dataclass
class Config:
    system_prompt: str = (
        "You are a helpful AI assistant. Answer the user's questions clearly and concisely."
    )
    model: str = "gpt-4"
    api_endpoint: str = "https://api.openai.com/v1/chat/completions"
    rag_directory: str = ""


DEFAULT_CONFIG = {
    "system_prompt": Config.system_prompt,
    "model": Config.model,
    "api_endpoint": Config.api_endpoint,
    "rag_directory": Config.rag_directory,
}


def create_default_config() -> Path:
    """
    Create a default config file in ~/.talkie/config.talkie.yml
    Returns the path to the created config file.
    """
    logger.info("No config file found, creating default configuration")
    config_dir = Path.home() / ".talkie"

    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created or verified config directory at: {config_dir}")
    except Exception as e:
        logger.error(f"Failed to create config directory: {e}")
        raise

    config_path = config_dir / "config.talkie.yml"

    try:
        with open(config_path, "w") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Created default config file at: {config_path}")
        logger.debug(f"Default configuration: {DEFAULT_CONFIG}")
    except Exception as e:
        logger.error(f"Failed to write default config file: {e}")
        raise

    return config_path


def find_config_file() -> Optional[Path]:
    """
    Look for config.talkie.yml in the following order:
    1. Current directory
    2. ~/.talkie/
    """
    logger.debug("Searching for config file...")

    # Check current directory
    current_dir_config = Path.cwd() / "config.talkie.yml"
    if current_dir_config.exists():
        logger.info(f"Found config file in current directory: {current_dir_config}")
        return current_dir_config

    logger.debug("No config file in current directory")

    # Check ~/.talkie directory
    home_dir_config = Path.home() / ".talkie" / "config.talkie.yml"
    if home_dir_config.exists():
        logger.info(f"Found config file in home directory: {home_dir_config}")
        return home_dir_config

    logger.debug("No config file found in home directory")
    return None


def load_config() -> Config:
    """
    Load configuration from config.talkie.yml file.
    If no config file exists, creates one with default values in ~/.talkie/
    """
    logger.debug("Starting config loading process")

    try:
        config_path = find_config_file()
        if not config_path:
            config_path = create_default_config()

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
            logger.debug(f"Loaded configuration data: {config_data}")

        config = Config(**config_data)
        logger.info("Successfully loaded configuration")
        return config

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse config file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        raise
