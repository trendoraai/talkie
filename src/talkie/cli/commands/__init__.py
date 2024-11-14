"""CLI commands package for talkie."""

from pathlib import Path

# Ensure all command modules are importable
__all__ = []
commands_dir = Path(__file__).parent

# Add all Python files (except __init__.py) to __all__
for file in commands_dir.glob("*.py"):
    if file.stem != "__init__":
        __all__.append(file.stem)

# Add all packages (directories with __init__.py) to __all__
for dir_path in commands_dir.glob("*/"):
    if dir_path.is_dir() and (dir_path / "__init__.py").exists():
        __all__.append(dir_path.name)