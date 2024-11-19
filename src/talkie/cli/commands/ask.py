import argparse
import sys
import asyncio
from talkie.logger_setup import setup_global_logger
from talkie.chat.ask import ask


def main(*args):
    """Process a chat file and get a response from OpenAI.

    This command processes a markdown chat file and sends the conversation
    to OpenAI to get a response. The response is then appended to the file.

    Args:
        *args: Command line arguments. If not provided, sys.argv[1:] will be used.

    Usage:
        talkie ask <file>
        talkie ask <file> --api-key <key>

    Examples:
        # Process a chat file and get response
        talkie ask python-help.md

        # Process with a specific API key
        talkie ask code-review.md --api-key sk-xxx

    Returns:
        int: 0 for success, non-zero for failure
    """
    parser = argparse.ArgumentParser(
        description="Process a chat file and get OpenAI response"
    )
    parser.add_argument("file", help="Path to the chat file")
    parser.add_argument(
        "--api-key",
        help="OpenAI API key. If not provided, will look in environment or config",
        default=None,
    )

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args)

    # Setup logger specific to this chat file
    logger = setup_global_logger(chat_file=args.file)
    logger.info(f"Executing ask command for file: {args.file}")

    asyncio.run(ask(args.file, args.api_key))
    return 0
