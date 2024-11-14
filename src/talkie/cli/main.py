"""Command-line interface for the talkie package."""

import sys
import argparse
import importlib
import os
from typing import List, Tuple, Optional


def load_command_module(command_path: str) -> object:
    """Dynamically load a command module based on the given path."""
    module_name = command_path.replace("/", ".")
    return importlib.import_module(module_name)


def get_available_commands(
    base_path: str = "talkie.cli.commands", filter_prefix: str = ""
) -> List[Tuple[str, str]]:
    """Retrieve a sorted list of available command modules that contain a main function.

    Only searches within the talkie.cli.commands package for command modules.
    Each command module should have a main() function that implements the command.
    """
    commands = []
    # Convert module path to directory path for os.walk
    base_dir = os.path.join(*base_path.split("."))
    base_dir = os.path.join(os.path.dirname(__file__), "commands")

    # Ensure the commands directory exists
    if not os.path.exists(base_dir):
        return []

    for root, _, files in os.walk(base_dir):
        for file in files:
            if (
                file.endswith(".py")
                and not file.startswith("_")
                and file != "__init__.py"
            ):
                # Get relative path from commands directory
                rel_path = os.path.relpath(root, base_dir)
                if rel_path == ".":
                    module_name = file[:-3]  # Remove .py
                else:
                    module_name = f"{rel_path.replace(os.path.sep, '.')}.{file[:-3]}"

                # Construct full module path
                module_path = f"talkie.cli.commands.{module_name}"

                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, "main"):
                        command = module_name.replace(".", " ")
                        if filter_prefix and not command.startswith(filter_prefix):
                            continue
                        docstring = module.main.__doc__ or ""
                        first_line = docstring.strip().split("\n")[0]
                        if len(docstring.strip()) > len(first_line):
                            first_line += "..."
                        commands.append((command, first_line))
                except ImportError as e:
                    print(f"Debug: Failed to import {module_path}: {str(e)}")
                    continue

    def sort_key(cmd_tuple):
        command, _ = cmd_tuple
        depth = command.count(" ")
        return depth, command

    return sorted(commands, key=sort_key)


def display_available_commands(
    commands: List[Tuple[str, str]], prefix: str = ""
) -> None:
    """Print the list of available commands to the console."""
    if prefix:
        print(f"Available commands in 'talkie {prefix}':")
    else:
        print("Available commands:")

    for cmd, description in commands:
        print(f"  talkie {cmd:<30} {description}")


def display_command_help(command_parts: List[str]) -> None:
    """Display help information for a specific command path."""
    command_path = "talkie" + "".join(f"/{part}" for part in command_parts)

    try:
        command_module = load_command_module(command_path)
        if hasattr(command_module, "main"):
            docstring = command_module.main.__doc__ or "No documentation available."
            print(f"Help for 'talkie {' '.join(command_parts)}':\n")
            print(docstring.strip())
        else:
            filtered_commands = get_available_commands(
                filter_prefix=" ".join(command_parts)
            )
            if filtered_commands:
                display_available_commands(filtered_commands, " ".join(command_parts))
            else:
                print(f"No commands found under 'talkie {' '.join(command_parts)}'")
    except ModuleNotFoundError:
        filtered_commands = get_available_commands(
            filter_prefix=" ".join(command_parts)
        )
        if filtered_commands:
            display_available_commands(filtered_commands, " ".join(command_parts))
        else:
            print(f"Command '{' '.join(command_parts)}' not found.")
            display_available_commands(get_available_commands())


def parse_arguments() -> Tuple[argparse.Namespace, List[str]]:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Talkie CLI")
    parser.add_argument("command", nargs="+", help="Command to execute")
    return parser.parse_known_args()


def execute_command(
    command_parts: List[str], remaining_args: List[str]
) -> Optional[int]:
    """Load and execute the specified command module's main function."""
    # Join command parts with dots to form module path
    module_name = ".".join(command_parts)
    module_path = f"talkie.cli.commands.{module_name}"

    try:
        command_module = importlib.import_module(module_path)
        if not hasattr(command_module, "main"):
            raise ModuleNotFoundError()

        original_argv = sys.argv
        sys.argv = [sys.argv[0]] + remaining_args

        try:
            return command_module.main(*remaining_args)
        finally:
            sys.argv = original_argv
    except (ImportError, ModuleNotFoundError):
        return None


def handle_command_execution(
    command_parts: List[str], remaining_args: List[str]
) -> int:
    """Handle the execution of a specified command."""
    result = execute_command(command_parts, remaining_args)

    if result is not None:
        return result or 0

    # Command not found, show available commands
    filter_prefix = " ".join(command_parts)
    available_commands = get_available_commands(filter_prefix=filter_prefix)

    if available_commands:
        print(f"Available commands in 'talkie {filter_prefix}':")
        display_available_commands(available_commands)
    else:
        print(f"Command '{filter_prefix}' not found.")
        print("\nAvailable commands:")
        display_available_commands(get_available_commands())

    print(
        "\nUse `talkie command --help` (e.g., `talkie hey --help`) to inspect further into the commands"
    )
    return 1


def handle_help_request(args: List[str]) -> None:
    """Handle help requests based on the provided arguments."""
    if not args:
        display_available_commands(get_available_commands())
    else:
        display_command_help(args)

    print(
        "\nUse `talkie command --help` (e.g., `talkie hey --help`) to see detailed help for specific commands"
    )


def main() -> int:
    """Main entry point for the CLI tool."""
    args = sys.argv[1:]

    if not args:
        display_available_commands(get_available_commands())
        print(
            "\nUse `talkie command --help` to see detailed help for specific commands"
        )
        return 0

    if args[-1] in {"--help", "-h"}:
        command_parts = args[:-1]
        handle_help_request(command_parts)
        return 0

    initial_args, remaining_args = parse_arguments()
    command_parts = initial_args.command

    if any(flag in remaining_args for flag in {"--help", "-h"}):
        display_available_commands(get_available_commands())
        print(
            "\nUse `talkie command --help` (e.g., `talkie hey --help`) to inspect further into the commands"
        )
        return 0

    return handle_command_execution(command_parts, remaining_args)


if __name__ == "__main__":
    sys.exit(main())
