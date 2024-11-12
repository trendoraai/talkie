import sys
import argparse
import importlib
import os


def load_command_module(command_path):
    """Dynamically load a command module based on the given path."""
    module_name = command_path.replace("/", ".")
    return importlib.import_module(module_name)


def get_available_commands(base_path="talkie", filter_prefix=""):
    """Retrieve a sorted list of available command modules that contain a main function."""
    commands = []
    base_dir = base_path.replace(".", "/")

    for root, _, files in os.walk(base_dir):
        for file in files:
            if (
                file.endswith(".py")
                and not file.startswith("_")
                and file != "__init__.py"
            ):
                module_path = os.path.join(root, file[:-3]).replace("/", ".")
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, "main") and not module_path.endswith("__main__"):
                        command = module_path.replace(f"{base_path}.", "").replace(
                            ".", " "
                        )
                        if filter_prefix and not command.startswith(filter_prefix):
                            continue
                        docstring = module.main.__doc__ or ""
                        first_line = docstring.strip().split("\n")[0]
                        if len(docstring.strip()) > len(first_line):
                            first_line += "..."
                        commands.append((command, first_line))
                except (ImportError, ModuleNotFoundError) as e:
                    print(f"Debug: Failed to import {module_path}: {str(e)}")
                    continue

    def sort_key(cmd_tuple):
        command, _ = cmd_tuple
        depth = command.count(" ")
        return depth, command

    return sorted(commands, key=sort_key)


def display_available_commands(commands, prefix=""):
    """Print the list of available commands to the console."""
    if prefix:
        print(f"Available commands in 'talkie {prefix}':")
    else:
        print("Available commands:")

    for cmd, description in commands:
        print(f"  talkie {cmd:<30} {description}")


def display_command_help(command_parts):
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


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("command", nargs="+", help="Command to execute")
    return parser.parse_known_args()


def execute_command(command_path, remaining_args):
    """Load and execute the specified command module's main function."""
    command_module = load_command_module(command_path)
    if not hasattr(command_module, "main"):
        raise ModuleNotFoundError()

    original_argv = sys.argv
    sys.argv = [sys.argv[0]] + remaining_args

    try:
        return command_module.main(*remaining_args)
    finally:
        sys.argv = original_argv


def handle_help_request(args):
    """Handle help requests based on the provided arguments."""
    if not args:
        display_available_commands(get_available_commands())
    else:
        display_command_help(args)

    print(
        "\nUse `talkie command --help` (e.g., `talkie hey --help`) to see detailed help for specific commands"
    )


def handle_command_execution(command_parts, remaining_args):
    """Handle the execution of a specified command."""
    command_path = "talkie" + "".join(f"/{part}" for part in command_parts)

    try:
        return execute_command(command_path, remaining_args)
    except ModuleNotFoundError:
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


def main():
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
