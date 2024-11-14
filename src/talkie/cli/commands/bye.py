import argparse
import sys


def main(*args):
    parser = argparse.ArgumentParser(description="Hey command")
    parser.add_argument("--caps", action="store_true", help="Add exclamation mark")

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args)

    print("bye" + ("!" if args.caps else ""))
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
