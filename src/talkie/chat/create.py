import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

from .constants import FRONTMATTER_TEMPLATE
from ..config import load_config


def create_chat(name: str, dir_path: str | None = None) -> None:
    """Create a new chat file with the given name in the specified directory."""
    now = datetime.utcnow().isoformat()
    created_at = now
    updated_at = now

    # Get configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Prepare frontmatter data
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

    try:
        with open(file_path, "w") as f:
            f.write(frontmatter)
    except IOError as e:
        print(f"Error creating chat file: {e}", file=sys.stderr)
        sys.exit(1)
