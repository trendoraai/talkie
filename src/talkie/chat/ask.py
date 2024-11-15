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
from .utils import parse_file_content
from pprint import pprint

from ..logger_setup import talkie_logger as logging


async def process_file_and_query_openai(
    file_path: str, api_key: str, include_rag_context_in_chat_history: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """Process the chat file and query OpenAI with the extracted information."""
    logging.debug(f"Starting to process file: {file_path}")
    with open(file_path, "r") as f:
        content = f.read()
    logging.debug(f"Successfully read file content, length: {len(content)} characters")

    # Extract system prompt, model, and messages from file content
    system_prompt, model, api_endpoint, messages, rag_directory = parse_file_content(
        content, file_path
    )
    logging.debug(f"Parsed file content - Model: {model}, API Endpoint: {api_endpoint}")
    logging.debug(
        f"System prompt length: {len(system_prompt)}, Number of messages: {len(messages)}"
    )

    # If RAG directory is provided, augment the last user message with relevant context
    if rag_directory and messages:
        last_message = messages[-1]
        if last_message["role"] == "user":
            try:
                rag_path = discover_rag_path(rag_directory, file_path)
                logging.info(f"Using RAG directory: {rag_path}")
                logging.debug("Initializing DirectoryRAG instance")
                rag = DirectoryRAG(rag_path, openai_api_key=api_key)

                logging.debug("Processing RAG directory")
                rag.process_directory()

                question = "\n".join(last_message["content"])
                logging.debug(f"Extracted question for RAG: {question[:100]}...")

                rag_context = []
                logging.debug("Querying RAG for relevant context")
                for filename, content in rag.query(question):
                    logging.debug(f"Found relevant content in file: {filename}")
                    context = f"File Path: {filename}\nFile Content:\n{content}\n"
                    rag_context.append(context)

                if rag_context:
                    text_rag_context = "\n".join(rag_context)
                    logging.debug(
                        f"Added {len(rag_context)} context items to the message"
                    )
                    last_message["content"] = [
                        f"Context from codebase:\n{text_rag_context}\n\n"
                        f"Question: {question}"
                    ]
                else:
                    logging.debug("No relevant RAG context found for the question")
            except Exception as e:
                logging.error(f"Error processing RAG context: {str(e)}", exc_info=True)
                raise

    # Prepare messages for API call
    logging.debug("Preparing messages for OpenAI API call")
    api_messages = prepare_api_messages(system_prompt, messages)

    # Query OpenAI API
    logging.info(f"Querying OpenAI API with model: {model}")
    answer, response_body = await query_openai(
        api_key, model, api_endpoint, api_messages
    )
    logging.debug(
        f"Received response from OpenAI API, status: {response_body.get('status', 'unknown')}"
    )

    return question, answer, response_body


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
        logging.info(f"Processing chat file: {file_path}")
        logging.debug("Starting chat processing workflow")

        # Get API key
        logging.debug("Retrieving OpenAI API key")
        api_key = get_openai_api_key(api_key)
        logging.debug("Successfully retrieved API key")

        # Process file and query OpenAI
        logging.debug("Initiating file processing and OpenAI query")
        question, answer, response_body = await process_file_and_query_openai(
            file_path, api_key
        )

        logging.debug(f"Generated answer length: {len(answer)} characters")
        print(f"Answer: {answer}")

        # Append answer to file
        logging.debug("Handling OpenAI response and updating file")
        handle_openai_response(file_path, question, answer, response_body)
        logging.info("Successfully processed chat and updated file")

    except Exception as e:
        logging.error(f"Error in chat processing: {str(e)}", exc_info=True)
        raise
