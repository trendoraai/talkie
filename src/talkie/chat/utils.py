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
    logging.debug(f"Expanding file reference: {file_path}")

    # Make the path relative to the chat file's directory
    chat_dir = os.path.dirname(chat_file_path)
    absolute_path = os.path.join(chat_dir, file_path)
    logging.debug(f"Resolved absolute path: {absolute_path}")

    try:
        with open(absolute_path, "r") as f:
            file_content = f.read()
        logging.debug(
            f"Successfully read referenced file, content length: {len(file_content)} characters"
        )
        return f"\n\nFile Path:\n[[{file_path}]]\nFile Content:\n{file_content}\n\n"
    except Exception as e:
        logging.error(
            f"Failed to read referenced file {absolute_path}: {str(e)}", exc_info=True
        )
        raise


def process_message_line(
    line: str, current_message: Dict[str, Any], chat_file_path: str
) -> Dict[str, Any]:
    """Process a single line in the message section."""
    logging.debug(f"Processing message line: {line[:50]}...")

    if line.startswith("user:") or line.startswith("assistant:"):
        role = "user" if line.startswith("user:") else "assistant"
        content_start = line.find(":") + 1
        logging.debug(f"Found new {role} message")
        return {"role": role, "content": [line[content_start:].strip()]}

    if current_message["role"] and not is_comment(line):
        if is_file_reference(line):
            logging.debug(f"Processing file reference in message: {line}")
            current_message["content"].append(
                expand_file_reference(line, chat_file_path)
            )
        else:
            logging.debug("Adding line to current message content")
            current_message["content"].append(line.strip())

    return current_message


def get_frontmatter_defaults(
    frontmatter: Dict[str, str]
) -> Tuple[str, str, str, Optional[str]]:
    """Get frontmatter values with defaults."""
    logging.debug("Getting frontmatter values with defaults")
    system_default = "You are a helpful assistant."
    api_endpoint_default = "https://api.openai.com/v1/chat/completions"

    system = frontmatter.get("system", system_default) or system_default
    model = frontmatter.get("model", "gpt-4") or "gpt-4"
    api_endpoint = (
        frontmatter.get("api_endpoint", api_endpoint_default) or api_endpoint_default
    )
    rag_directory = frontmatter.get("rag_directory", "")

    logging.debug(f"Using model: {model}, API endpoint: {api_endpoint}")
    logging.debug(f"RAG directory: {rag_directory or 'Not specified'}")

    return (system, model, api_endpoint, rag_directory)


def parse_frontmatter_section(frontmatter_lines: List[str]) -> Dict[str, str]:
    """Parse frontmatter lines into a dictionary."""
    logging.debug(f"Parsing frontmatter section with {len(frontmatter_lines)} lines")
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
                logging.debug(f"Parsed frontmatter key: {current_key}")
            key, value = line.split(":", 1)
            current_key = key.strip()
            current_value = [value.strip()]
            logging.debug(f"Found new frontmatter key: {current_key}")
        elif current_key:
            current_value.append(line)

    if current_key:
        frontmatter[current_key] = "\n".join(current_value).strip()
        logging.debug(f"Parsed final frontmatter key: {current_key}")

    logging.debug(f"Completed frontmatter parsing, found {len(frontmatter)} keys")
    return frontmatter


def parse_messages_section(
    message_lines: List[str], chat_file_path: str
) -> List[Dict[str, Any]]:
    """Parse message lines into a list of messages."""
    logging.debug(f"Parsing messages section with {len(message_lines)} lines")
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
                logging.debug(
                    f"Added {current_message['role']} message with {len(current_message['content'])} content items"
                )
            current_message = new_message

    if current_message["role"]:
        messages.append(current_message)
        logging.debug(
            f"Added final {current_message['role']} message with {len(current_message['content'])} content items"
        )

    logging.debug(f"Completed message parsing, found {len(messages)} messages")
    return messages


def parse_file_content(
    content: str,
    chat_file_path: str,
) -> Tuple[str, str, str, List[Dict[str, str]], Optional[str]]:
    """Parse the chat file content to extract necessary information."""
    logging.info(f"Starting to parse chat file: {chat_file_path}")
    logging.debug(f"File content length: {len(content)} characters")

    lines = content.split("\n")
    logging.debug(f"Split content into {len(lines)} lines")

    # Find the frontmatter section boundaries
    frontmatter_start = -1
    frontmatter_end = -1

    for i, line in enumerate(lines):
        if line.strip() == "---":
            if frontmatter_start == -1:
                frontmatter_start = i
                logging.debug(f"Found frontmatter start at line {i}")
            elif frontmatter_end == -1:
                frontmatter_end = i
                logging.debug(f"Found frontmatter end at line {i}")
                break

    if frontmatter_start == -1 or frontmatter_end == -1:
        logging.error("Invalid file format: Missing frontmatter section markers")
        raise ValueError(
            "Invalid file format: Missing frontmatter section (must be enclosed by ---)"
        )

    # Split and parse sections
    logging.debug("Parsing frontmatter section")
    frontmatter = parse_frontmatter_section(
        lines[frontmatter_start + 1 : frontmatter_end]
    )

    logging.debug("Parsing messages section")
    messages = parse_messages_section(lines[frontmatter_end + 1 :], chat_file_path)

    # Get values with defaults
    system_prompt, model, api_endpoint, rag_directory = get_frontmatter_defaults(
        frontmatter
    )

    logging.info(f"Successfully parsed chat file with {len(messages)} messages")
    return system_prompt, model, api_endpoint, messages, rag_directory
