import argparse
import sys
from talkie.logger_setup import talkie_logger

def main(*args):
    parser = argparse.ArgumentParser(description="Hey command")
    parser.add_argument("--caps", action="store_true", help="Add exclamation mark")

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args)

    message = "hey" + ("!" if args.caps else "")
    talkie_logger.info(f"Executing hey command with message: {message}")
    print(message)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
