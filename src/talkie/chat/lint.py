import re
from pathlib import Path
from typing import List, Optional
import logging


def validate_frontmatter(content: str) -> bool:
    """Validate the frontmatter section of the chat content."""
    required_fields = [
        "title",
        "system",
        "model",
        "api_endpoint",
        "created_at",
        "updated_at",
        "tags",
        "summary",
    ]

    for field in required_fields:
        if not re.search(f"{field}:\\s*.+", content):
            logging.error(
                f"Frontmatter error: '{field}' is missing or has incorrect format."
            )
            return False
    return True


def validate_chat_structure(content: str, file_path: Path) -> bool:
    """Validate the structure of the chat content."""
    try:
        frontmatter_end = content.rindex("---")
        chat_content = content[frontmatter_end + 3 :]

        if not chat_content.strip():
            logging.error("Chat structure error: No content after frontmatter.")
            return False

        lines = chat_content.split("\n")
        expect_user = True

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("user:"):
                if not expect_user:
                    logging.error("Chat structure error: Unexpected 'user:' entry.")
                    return False
                expect_user = False
            elif line.startswith("assistant:"):
                if expect_user:
                    logging.error(
                        "Chat structure error: Unexpected 'assistant:' entry."
                    )
                    return False
                expect_user = True

        if not expect_user:
            logging.error("Chat structure error: Chat must end with a user entry.")
            return False

        return True

    except ValueError:
        logging.error("Missing frontmatter end delimiter '---'.")
        return False


def lint_file(file_path: Path) -> bool:
    """Lint a single chat file."""
    try:
        content = file_path.read_text()
        return validate_frontmatter(content) and validate_chat_structure(
            content, file_path
        )
    except Exception as e:
        logging.error(f"Error processing {file_path}: {str(e)}")
        return False


def lint_directory(directory: Path) -> bool:
    """Lint all chat files in a directory."""
    success = True
    for file_path in directory.glob("*.md"):
        if not lint_file(file_path):
            success = False
    return success
