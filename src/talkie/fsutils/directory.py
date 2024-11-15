from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
import os
from talkie.logger_setup import talkie_logger as logger


def walk_respecting_ignore(root: str, ignore_file: str):
    """Walk directory tree respecting gitignore patterns."""
    try:
        # Get the absolute path of the root
        root_path = get_absolute_path(root)
        # Look for ignore file within the root directory
        ignore_path = os.path.join(root_path, ignore_file)

        logger.debug(f"Walking directory: {root_path}")
        logger.debug(f"Using ignore file: {ignore_path}")

        # Check if ignore file exists
        if not os.path.exists(ignore_path):
            logger.warning(f"Ignore file not found: {ignore_path}")
            spec = PathSpec([])
        else:
            try:
                with open(ignore_path, "r") as gitignore:
                    spec = PathSpec.from_lines(GitWildMatchPattern, gitignore)
            except IOError as e:
                logger.error(f"Failed to read ignore file: {e}")
                spec = PathSpec([])

        # Check if root directory exists
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Root directory not found: {root_path}")

        for dirpath, dirnames, filenames in os.walk(root_path):
            logger.debug(f"Scanning directory: {dirpath}")
            logger.debug(f"Found files: {filenames}")

            try:
                dirnames[:] = [
                    d for d in dirnames if not spec.match_file(os.path.join(dirpath, d))
                ]
                for filename in filenames:
                    full_path = os.path.join(dirpath, filename)
                    is_ignored = spec.match_file(full_path)
                    status = "✅ INCLUDED" if not is_ignored else "❌ IGNORED"
                    logger.debug(f"[{status:^12}] {full_path}")
                    if not is_ignored:
                        yield full_path
            except Exception as e:
                logger.error(f"Error processing directory {dirpath}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in walk_respecting_ignore: {e}")
        raise


def get_relative_path(path, start=None):
    """Get relative path from start directory."""
    try:
        if start is None:
            start = os.getcwd()

        path = os.path.normpath(os.path.abspath(path))
        start = os.path.normpath(os.path.abspath(start))

        try:
            relative_path = os.path.relpath(path, start)
        except ValueError as e:
            logger.error(f"Path {path} is not under the start directory {start}")
            raise

        return relative_path
    except Exception as e:
        logger.error(f"Error in get_relative_path: {e}")
        raise


def get_absolute_path(path, base=None):
    """Get absolute path from base directory."""
    if os.path.isabs(path):
        return os.path.normpath(path)

    try:
        if base is None:
            base = os.getcwd()

        if not os.path.exists(base):
            logger.error(f"Base directory does not exist: {base}")
            raise FileNotFoundError(f"Base directory does not exist: {base}")

        if os.path.isabs(path):
            return os.path.normpath(path)

        full_path = os.path.join(base, path)
        return os.path.normpath(os.path.abspath(full_path))
    except Exception as e:
        logger.error(f"Error in get_absolute_path: {e}")
        raise
