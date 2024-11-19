import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

from talkie.chat.constants import FRONTMATTER_TEMPLATE
from talkie.config import load_config
from talkie.logger_setup import talkie_logger


def create_chat(name: str, dir_path: str | None = None) -> None:
    """Create a new chat file with the given name in the specified directory."""
    talkie_logger.info(f"Creating new chat file with name: {name}")
    now = datetime.utcnow().isoformat()
    created_at = now
    updated_at = now

    # Get configuration
    try:
        config = load_config()
        talkie_logger.debug(f"Loaded configuration: {config}")
    except Exception as e:
        talkie_logger.error(f"Failed to load config: {e}")
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Prepare frontmatter data
    talkie_logger.debug("Preparing frontmatter data")
    frontmatter = FRONTMATTER_TEMPLATE.format(
        title=name,
        system=config.system_prompt,
        model=config.model,
        api_endpoint=config.api_endpoint,
        rag_directory=config.rag_directory,
        created_at=created_at,
        updated_at=updated_at,
        tags="[]",
        summary="",
    )

    # Create file path
    file_path = Path(dir_path or ".") / f"{name}.md"
    talkie_logger.debug(f"Creating chat file at: {file_path}")

    try:
        with open(file_path, "w") as f:
            f.write(frontmatter)
        talkie_logger.info(f"Successfully created chat file: {file_path}")
    except IOError as e:
        talkie_logger.error(f"Failed to create chat file: {e}")
        print(f"Error creating chat file: {e}", file=sys.stderr)
        sys.exit(1)
