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
from .utils import parse_file_content


async def process_file_and_query_openai(
    file_path: str, api_key: str, include_rag_context_in_chat_history: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """Process the chat file and query OpenAI with the extracted information."""
    logging.info(f"Processing file: {file_path}")
    with open(file_path, "r") as f:
        content = f.read()
    logging.debug(f"File content length: {len(content)} characters")

    # Extract system prompt, model, and messages from file content
    logging.info("Parsing file content...")
    system_prompt, model, api_endpoint, messages, rag_directory = parse_file_content(
        content, file_path
    )
    logging.debug(
        f"Parsed configuration - Model: {model}, API Endpoint: {api_endpoint}, RAG Directory: {rag_directory}"
    )

    # If RAG directory is provided, augment the last user message with relevant context
    if rag_directory and messages:
        logging.info("RAG directory found, attempting to augment message with context")
        last_message = messages[-1]
        if last_message["role"] == "user":
            augment_message_with_rag_context(
                last_message, rag_directory, file_path, api_key
            )

    api_messages = prepare_api_messages(system_prompt, messages)
    logging.info(f"Prepared {len(api_messages)} messages for API request")
    logging.debug(f"Prepared API messages:\n{json.dumps(api_messages, indent=2)}")

    logging.info(f"Querying OpenAI API with model {model}")
    answer, response_body = await query_openai(
        api_key, model, api_endpoint, api_messages
    )
    logging.debug(f"Received response with {len(response_body)} characters")

    question = messages[-1]["content"] if include_rag_context_in_chat_history else ""
    return question, answer, response_body


def prepare_api_messages(
    system_prompt: str, messages: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """Prepare messages for the OpenAI API."""
    logging.debug(f"Preparing API messages with system prompt: {bool(system_prompt)}")
    api_messages = []

    if system_prompt:
        api_messages.append({"role": "system", "content": system_prompt})

    for msg in messages:
        api_messages.append({"role": msg["role"], "content": "\n".join(msg["content"])})

    logging.debug(f"Prepared {len(api_messages)} messages")
    return api_messages


def save_api_key(api_key: str) -> None:
    """Save API key to .env file in ~/.talkie directory."""
    logging.info("Saving API key to ~/.talkie/.env")
    talkie_dir = Path.home() / ".talkie"
    talkie_dir.mkdir(exist_ok=True)
    env_path = talkie_dir / ".env"
    with open(env_path, "a") as f:
        f.write(f"\nOPENAI_API_KEY={api_key}\n")
    logging.debug(f"API key saved to {env_path}")


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
    logging.info(f"Discovering RAG path for directory: {rag_directory}")

    # Check if it's already an absolute path
    if os.path.isabs(rag_directory) and os.path.isdir(rag_directory):
        logging.debug(f"Using absolute RAG path: {rag_directory}")
        return rag_directory

    # Try relative to the chat file's directory
    chat_dir = os.path.dirname(os.path.abspath(file_path))
    relative_to_chat = os.path.join(chat_dir, rag_directory)
    if os.path.isdir(relative_to_chat):
        logging.debug(f"Using RAG path relative to chat file: {relative_to_chat}")
        return os.path.abspath(relative_to_chat)

    # Try relative to current working directory
    relative_to_cwd = os.path.join(os.getcwd(), rag_directory)
    if os.path.isdir(relative_to_cwd):
        logging.debug(
            f"Using RAG path relative to current directory: {relative_to_cwd}"
        )
        return os.path.abspath(relative_to_cwd)

    logging.error(
        f"RAG directory '{rag_directory}' not found after trying multiple locations"
    )
    raise FileNotFoundError(
        f"RAG directory '{rag_directory}' not found. Tried:\n"
        f"1. As absolute path: {rag_directory}\n"
        f"2. Relative to chat file: {relative_to_chat}\n"
        f"3. Relative to current directory: {relative_to_cwd}"
    )


def augment_message_with_rag_context(
    message: Dict[str, Any], rag_directory: str, file_path: str, api_key: str
) -> None:
    """
    Augment a message with relevant context from the RAG directory.

    Args:
        message: The message to augment
        rag_directory: Path to the RAG directory
        file_path: Path to the current file
        api_key: OpenAI API key
    """
    try:
        rag_path = discover_rag_path(rag_directory, file_path)
        logging.info(f"Discovered RAG directory: {rag_path}")
        rag = DirectoryRAG(rag_path, openai_api_key=api_key)
        rag.process_directory()
        question = "\n".join(message["content"])
        rag_context = []
        for filename, content in rag.query(question):
            context = f"File Path: {filename}\nFile Content:\n{content}\n"
            rag_context.append(context)

        if rag_context:
            text_rag_context = "\n".join(rag_context)
            message["content"] = [
                f"Context from codebase:\n{text_rag_context}\n\n"
                f"Question: {question}"
            ]
    except FileNotFoundError as e:
        logging.error(f"RAG directory not found: {e}")
        raise


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
