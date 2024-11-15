import asyncio
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import os
import json
from dotenv import load_dotenv

from .api import query_openai
from .response_metadata import handle_openai_response
from .constants import ADD_OPENAI_KEY_MESSAGE
from ..rag.directory_rag import DirectoryRAG
from ..logger_setup import talkie_logger as logging
from pprint import pprint


async def process_file_and_query_openai(
    file_path: str, api_key: str, include_rag_context_in_chat_history: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """Process the chat file and query OpenAI with the extracted information."""
    with open(file_path, "r") as f:
        content = f.read()

    # Extract system prompt, model, and messages from file content
    system_prompt, model, api_endpoint, messages, rag_directory = parse_file_content(
        content, file_path
    )

    print("===================")
    print(system_prompt)
    print(model)
    print(messages)
    print("===================")

    # If RAG directory is provided, augment the last user message with relevant context
    if rag_directory and messages:
        last_message = messages[-1]
        if last_message["role"] == "user":
            try:
                rag_path = discover_rag_path(rag_directory, file_path)
                logging.info(f"Discovered RAG directory: {rag_path}")
                rag = DirectoryRAG(rag_path, openai_api_key=api_key)
                question = "\n".join(last_message["content"])
                rag_context = []
                for filename, content in rag.query(question):
                    context = f"File Path: {filename}\nFile Content:\n{content}\n"
                    rag_context.append(context)

                if rag_context:
                    last_message["content"] = [
                        f"Context from codebase:\n{"\n".join(rag_context)}\n\nQuestion: {question}"
                    ]
            except FileNotFoundError as e:
                logging.error(f"RAG directory not found: {e}")
                raise

    api_messages = prepare_api_messages(system_prompt, messages)

    logging.debug(f"Prepared API messages:\n{json.dumps(api_messages, indent=2)}")

    answer, response_body = await query_openai(
        api_key, model, api_endpoint, api_messages
    )
    question = messages[-1]["content"] if include_rag_context_in_chat_history else ""
    return question, answer, response_body


def is_comment(line: str) -> bool:
    """Check if a line is an HTML comment."""
    line = line.strip()
    return line.startswith("<!--") and line.endswith("-->")


def parse_frontmatter_line(
    line: str, current_key: str, current_value: List[str], i: int
) -> Tuple[str, List[str]]:
    """Parse a single line of frontmatter."""
    if ":" in line and not line.strip().startswith(" "):
        parts = line.split(":", 1)
        key = parts[0].strip()

        if " " in key:
            logging.warning(f"Invalid frontmatter key format at line {i+1}: {line}")
            return current_key, current_value

        new_value = [parts[1].strip()] if len(parts) > 1 else []
        return key, new_value

    if current_key:
        current_value.append(line.strip())
    return current_key, current_value


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
    return (
        frontmatter.get("system", "You are a helpful assistant."),
        frontmatter.get("model", "gpt-4"),
        frontmatter.get("api_endpoint", "https://api.openai.com/v1/chat/completions"),
        frontmatter.get("rag_directory"),
    )


def parse_file_content(
    content: str,
    chat_file_path: str,
) -> Tuple[str, str, str, List[Dict[str, str]], Optional[str]]:
    """Parse the chat file content to extract necessary information."""
    lines = content.split("\n")
    frontmatter = {}
    messages = []

    # Parse frontmatter
    in_frontmatter = False
    current_key = None
    current_value = []
    current_message = {"role": None, "content": []}

    for i, line in enumerate(lines):
        line = line.strip()

        # Handle frontmatter delimiters
        if line == "---":
            if in_frontmatter and current_key:
                frontmatter[current_key] = "\n".join(current_value).strip()
            in_frontmatter = not in_frontmatter
            continue

        if in_frontmatter:
            # Process frontmatter
            current_key, current_value = parse_frontmatter_line(
                line, current_key, current_value, i
            )
            if current_key and current_key != current_value[0]:  # New key found
                frontmatter[current_key] = "\n".join(current_value).strip()
        else:
            # Process messages
            new_message = process_message_line(line, current_message, chat_file_path)
            if new_message != current_message:
                if current_message["role"]:
                    messages.append(current_message)
                current_message = new_message

    # Add the last message if it exists
    if current_message["role"]:
        messages.append(current_message)

    # Get values from frontmatter with defaults
    system_prompt, model, api_endpoint, rag_directory = get_frontmatter_defaults(
        frontmatter
    )

    pprint(messages)

    return system_prompt, model, api_endpoint, messages, rag_directory


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


def prepare_api_messages(
    system_prompt: str, messages: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """Prepare messages for the OpenAI API."""
    api_messages = []

    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})

    for msg in messages:
        api_messages.append({"role": msg["role"], "content": "\n".join(msg["content"])})

    return api_messages


def save_api_key(api_key: str) -> None:
    """Save API key to .env file in ~/.talkie directory."""
    talkie_dir = Path.home() / ".talkie"
    talkie_dir.mkdir(exist_ok=True)
    env_path = talkie_dir / ".env"
    with open(env_path, "a") as f:
        f.write(f"\nOPENAI_API_KEY={api_key}\n")


def get_openai_api_key(cli_key: Optional[str] = None) -> str:
    """Get OpenAI API key from various sources."""
    if cli_key:
        # Store CLI key for future use
        save_api_key(cli_key)
        logging.info("Stored OpenAI API key from CLI in ~/.talkie/.env for future use")
        return cli_key

    # Try to load from local .env file
    load_dotenv()

    # Check environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    # Try to load from ~/.talkie/.env file
    talkie_env = Path.home() / ".talkie" / ".env"
    if talkie_env.exists():
        load_dotenv(talkie_env)
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key

    print(ADD_OPENAI_KEY_MESSAGE)
    raise ValueError("OpenAI API key not found")


def discover_rag_path(rag_directory: str, file_path: str) -> str:
    """
    Discover the actual RAG directory path by checking multiple locations.
    """
    # Check if it's already an absolute path
    if os.path.isabs(rag_directory) and os.path.isdir(rag_directory):
        return rag_directory

    # Try relative to the chat file's directory
    chat_dir = os.path.dirname(os.path.abspath(file_path))
    relative_to_chat = os.path.join(chat_dir, rag_directory)
    if os.path.isdir(relative_to_chat):
        return os.path.abspath(relative_to_chat)

    # Try relative to current working directory
    relative_to_cwd = os.path.join(os.getcwd(), rag_directory)
    if os.path.isdir(relative_to_cwd):
        return os.path.abspath(relative_to_cwd)

    raise FileNotFoundError(
        f"RAG directory '{rag_directory}' not found. Tried:\n"
        f"1. As absolute path: {rag_directory}\n"
        f"2. Relative to chat file: {relative_to_chat}\n"
        f"3. Relative to current directory: {relative_to_cwd}"
    )


async def ask(file_path: str, api_key: Optional[str] = None) -> None:
    try:
        # Setup logging
        file_path = str(Path(file_path).resolve())
        logging.info(f"Starting processing for file: {file_path}")

        # Get API key
        api_key = get_openai_api_key(api_key)

        # Process file and query OpenAI
        question, answer, response_body = await process_file_and_query_openai(
            file_path, api_key
        )

        print(f"Answer: {answer}")
        logging.info("Successfully processed file and received answer")

        # Append answer to file
        handle_openai_response(file_path, question, answer, response_body)
        logging.info("Successfully appended answer to file")

    except Exception as e:
        logging.error(f"Error processing file and querying OpenAI: {str(e)}")
        raise
