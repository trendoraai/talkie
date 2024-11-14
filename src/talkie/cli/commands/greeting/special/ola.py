import argparse
import sys


def run(caps):
    print("ola" + ("!" if caps else ""))


def run_all(caps):
    run(caps)


def main(*args):
    """Ola command

    This is a big comand


    """
    parser = argparse.ArgumentParser(description="Ola command")
    parser.add_argument("--caps", action="store_true", help="Add exclamation mark")

    # If args provided, use those. Otherwise use sys.argv[1:]
    args = parser.parse_args(args)

    run_all(args.caps)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
