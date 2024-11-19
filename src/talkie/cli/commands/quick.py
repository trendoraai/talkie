import argparse
import sys
import asyncio
from talkie.logger_setup import setup_global_logger
from talkie.chat.quick import quick_chat
from talkie.config import load_config


def main(*args):
    """Process a quick chat request and get a response from OpenAI.

    This command sends a quick question to OpenAI and gets a response
    without creating a chat file. Optionally can save the conversation
    to a file and use RAG with a specified directory.

    Args:
        *args: Command line arguments. If not provided, sys.argv[1:] will be used.

    Usage:
        talkie quick "Your question here"
        talkie quick "Your question here" --output file.md
        talkie quick "Your question here" --rag-dir ./src
        talkie quick "Your question here" --system "You are a helpful assistant"

    Returns:
        int: 0 for success, non-zero for failure
    """
    parser = argparse.ArgumentParser(
        description="Send a quick question to OpenAI and get a response"
    )
    parser.add_argument("question", help="The question to ask")
    parser.add_argument(
        "--output",
        help="Optional file to save the conversation",
        default=None,
    )
    parser.add_argument(
        "--rag-dir",
        help="Optional directory to use for RAG context",
        default=None,
    )
    parser.add_argument(
        "--system",
        help="Optional system prompt",
        default=None,
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key. If not provided, will look in environment or config",
        default=None,
    )

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args if args else sys.argv[1:])

    # Setup logger
    logger = setup_global_logger()
    logger.info(f"Executing quick chat command")

    # Load config for model and endpoint
    config = load_config()

    # Use system prompt from config if none provided
    system_prompt = args.system if args.system is not None else config.system_prompt

    # Run the chat and get response
    response = asyncio.run(
        quick_chat(
            question=args.question,
            system_prompt=system_prompt,
            model=config.model,
            api_endpoint=config.api_endpoint,
            api_key=args.api_key,
            output_file=args.output,
            rag_directory=args.rag_dir,
        )
    )

    # Print the conversation
    print(f"\nQ: {args.question}")
    print(f"\nA: {response['answer']}\n")

    return 0
