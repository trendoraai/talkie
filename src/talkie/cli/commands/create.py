import argparse
import sys
from talkie.logger_setup import talkie_logger
from talkie.chat.create import create_chat


def main(*args):
    """Create a new chat file with the specified name and optional directory.

    This command creates a new markdown file for chat interactions. The file will be
    initialized with frontmatter containing configuration settings from your talkie config.

    Args:
        *args: Command line arguments. If not provided, sys.argv[1:] will be used.

    Usage:
        talkie create <name>
        talkie create <name> --dir <directory>

    Examples:
        # Create a chat file named 'python-help' in current directory
        talkie create python-help

        # Create a chat file named 'code-review' in a specific directory
        talkie create code-review --dir ~/chats/work

    Returns:
        int: 0 for success, non-zero for failure

    The created file will be named '<name>.md' and will contain frontmatter with:
        - title: The provided name
        - system prompt: From config
        - model: From config
        - API endpoint: From config
        - RAG directory: From config
        - creation timestamp
        - update timestamp
        - empty tags and summary
    """
    parser = argparse.ArgumentParser(description="Create a new chat file")
    parser.add_argument("name", help="Name of the chat file")
    parser.add_argument(
        "--dir", help="Directory to create the chat file in", default=None
    )

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args)

    talkie_logger.info(f"Executing create command for chat: {args.name}")
    create_chat(args.name, args.dir)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
