from typing import Optional, Tuple, Dict, Any, List
import os
from pprint import pprint
from ..logger_setup import talkie_logger as logging


def is_comment(line: str) -> bool:
    """Check if a line is an HTML comment."""
    line = line.strip()
    return line.startswith("<!--") and line.endswith("-->")


def is_file_reference(line: str) -> bool:
    """Check if a line contains a file reference in the format [[filename]]."""
    line = line.strip()
    return line.startswith("[[") and line.endswith("]]") and not "\n" in line


def expand_file_reference(line: str, chat_file_path: str) -> str:
    """Expand a file reference by reading the referenced file's content."""
    file_path = line.strip()[2:-2]  # Remove [[ and ]]

    # Make the path relative to the chat file's directory
    chat_dir = os.path.dirname(chat_file_path)
    absolute_path = os.path.join(chat_dir, file_path)

    try:
        with open(absolute_path, "r") as f:
            file_content = f.read()
        return f"\n\nFile Path:\n[[{file_path}]]\nFile Content:\n{file_content}\n\n"
    except Exception as e:
        logging.error(f"Failed to read file {absolute_path}: {e}")
        raise


def process_message_line(
    line: str, current_message: Dict[str, Any], chat_file_path: str
) -> Dict[str, Any]:
    """Process a single line in the message section."""
    if line.startswith("user:") or line.startswith("assistant:"):
        role = "user" if line.startswith("user:") else "assistant"
        content_start = line.find(":") + 1
        return {"role": role, "content": [line[content_start:].strip()]}

    if current_message["role"] and not is_comment(line):
        if is_file_reference(line):
            current_message["content"].append(
                expand_file_reference(line, chat_file_path)
            )
        else:
            current_message["content"].append(line.strip())

    return current_message


def get_frontmatter_defaults(
    frontmatter: Dict[str, str]
) -> Tuple[str, str, str, Optional[str]]:
    """Get frontmatter values with defaults."""
    system_default = "You are a helpful assistant."
    api_endpoint_default = "https://api.openai.com/v1/chat/completions"
    return (
        frontmatter.get("system", system_default) or system_default,
        frontmatter.get("model", "gpt-4") or "gpt-4",
        frontmatter.get("api_endpoint", api_endpoint_default) or api_endpoint_default,
        frontmatter.get("rag_directory", ""),
    )


def parse_frontmatter_section(frontmatter_lines: List[str]) -> Dict[str, str]:
    """Parse frontmatter lines into a dictionary."""
    frontmatter = {}
    current_key = None
    current_value = []

    for line in frontmatter_lines:
        line = line.strip()
        if not line:
            continue

        if ":" in line:
            if current_key:
                frontmatter[current_key] = "\n".join(current_value).strip()
            key, value = line.split(":", 1)
            current_key = key.strip()
            current_value = [value.strip()]
        elif current_key:
            current_value.append(line)

    if current_key:
        frontmatter[current_key] = "\n".join(current_value).strip()

    return frontmatter


def parse_messages_section(
    message_lines: List[str], chat_file_path: str
) -> List[Dict[str, Any]]:
    """Parse message lines into a list of messages."""
    messages = []
    current_message = {"role": None, "content": []}

    for line in message_lines:
        line = line.strip()
        if (
            not line or line == "---"
        ):  # Skip empty lines and any additional frontmatter markers
            continue

        new_message = process_message_line(line, current_message, chat_file_path)
        if new_message != current_message:
            if current_message["role"]:
                messages.append(current_message)
            current_message = new_message

    if current_message["role"]:
        messages.append(current_message)

    return messages


def parse_file_content(
    content: str,
    chat_file_path: str,
) -> Tuple[str, str, str, List[Dict[str, str]], Optional[str]]:
    """Parse the chat file content to extract necessary information."""
    lines = content.split("\n")

    # Find the frontmatter section boundaries
    frontmatter_start = -1
    frontmatter_end = -1

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if frontmatter_start == -1:
                frontmatter_start = i
            elif frontmatter_end == -1:
                frontmatter_end = i
                break

    if frontmatter_start == -1 or frontmatter_end == -1:
        raise ValueError(
            "Invalid file format: Missing frontmatter section (must be enclosed by ---)"
        )

    # Split and parse sections
    frontmatter = parse_frontmatter_section(
        lines[frontmatter_start + 1 : frontmatter_end]
    )
    messages = parse_messages_section(lines[frontmatter_end + 1 :], chat_file_path)

    # Get values from frontmatter with defaults
    system_prompt, model, api_endpoint, rag_directory = get_frontmatter_defaults(
        frontmatter
    )

    return system_prompt, model, api_endpoint, messages, rag_directory
