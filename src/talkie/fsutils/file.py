import os
import json
import xxhash
import time
from typing import Dict, Optional, Tuple
from talkie.logger_setup import talkie_logger as logger
from talkie.fsutils.directory import get_relative_path, walk_respecting_ignore
from pathlib import Path

HASH_FILE = ".file_hashes.json"


def get_file_metadata(file_path: str) -> Tuple[float, int]:
    """Get file modification time and size."""
    stat = os.stat(file_path)
    return (stat.st_mtime, stat.st_size)


def calculate_file_hash(file_path: str) -> str:
    """Calculate xxHash of a file (faster than MD5)."""
    logger.debug(f"Calculating hash for file: {file_path}")
    try:
        hasher = xxhash.xxh64()
        with open(file_path, "rb") as f:
            chunk = f.read(65536)  # Increased chunk size for better performance
            while chunk:
                hasher.update(chunk)
                chunk = f.read(65536)
        hash_value = hasher.hexdigest()
        logger.debug(f"Hash calculated successfully: {hash_value}")
        return hash_value
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise


def load_file_hashes(root_dir: str, hash_file: str = HASH_FILE) -> Dict:
    """Load file hashes from .file_hashes.json."""
    hash_file_path = os.path.join(root_dir, hash_file)
    logger.debug(f"Loading file hashes from: {hash_file_path}")
    try:
        if os.path.exists(hash_file_path):
            try:
                with open(hash_file_path, "r") as f:
                    hashes = json.load(f)
                    logger.debug(
                        f"Successfully loaded {len(hashes.get('files', {}))} file hashes"
                    )
                    return hashes
            except json.JSONDecodeError:
                logger.warning(
                    f"Invalid or empty hash file, creating new hash dictionary"
                )
                return create_new_hash_dict(root_dir)
        else:
            logger.info(
                f"Hash file not found, creating new hash dictionary for {root_dir}"
            )
            return create_new_hash_dict(root_dir)
    except Exception as e:
        logger.error(f"Error loading file hashes: {e}")
        raise


def create_new_hash_dict(root_dir: str) -> Dict:
    """Create a new hash dictionary with default values."""
    return {
        "files": {},
        "collection_name": os.path.basename(root_dir),
        "last_check": None,
    }


def save_file_hashes(root_dir: str, hashes: Dict) -> None:
    """Save file hashes to .file_hashes.json."""
    hash_file_path = os.path.join(root_dir, HASH_FILE)
    logger.debug(
        f"Saving {len(hashes.get('files', {}))} file hashes to: {hash_file_path}"
    )
    try:
        with open(hash_file_path, "w") as f:
            json.dump(hashes, f, indent=2)
        logger.debug("File hashes saved successfully")
    except Exception as e:
        logger.error(f"Error saving file hashes: {e}")
        raise


def update_file_hash(
    root_dir: str, file_path: str, file_hash: Optional[str] = None
) -> None:
    """Update hash for a single file in .file_hashes.json."""
    logger.debug(f"Updating hash for file: {file_path}")
    hashes = load_file_hashes(root_dir)
    relative_path = get_relative_path(file_path, root_dir)

    if os.path.exists(file_path):
        if file_hash is None:
            file_hash = calculate_file_hash(file_path)
        timestamp, size = get_file_metadata(file_path)
        hashes["files"][relative_path] = {
            "metadata": {"timestamp": timestamp, "size": size},
            "hash": file_hash,
        }
        logger.info(f"Updated hash for {relative_path}: {file_hash}")
    else:
        logger.info(f"Removing hash for non-existent file: {relative_path}")
        hashes["files"].pop(relative_path, None)

    save_file_hashes(root_dir, hashes)


def get_file_hash(root_dir: str, file_path: str) -> Optional[str]:
    """Get hash for a single file from .file_hashes.json."""
    hashes = load_file_hashes(root_dir)
    relative_path = get_relative_path(file_path, root_dir)
    file_data = hashes["files"].get(relative_path)
    return file_data["hash"] if file_data else None


def update_all_file_hashes(full_path: str, ignore_file: str = ".talkieignore") -> None:
    """Update hashes for all files in the directory."""
    logger.info(f"Starting full hash update in directory: {full_path}")
    hashes = load_file_hashes(full_path)
    current_files = {}

    file_count = 0
    for file_path in walk_respecting_ignore(full_path, ignore_file):
        relative_path = get_relative_path(file_path, full_path)
        timestamp, size = get_file_metadata(file_path)

        # Only calculate hash if metadata changed or file is new
        stored_file = hashes["files"].get(relative_path, {})
        stored_metadata = stored_file.get("metadata", {})
        if (
            not stored_metadata
            or stored_metadata.get("timestamp") != timestamp
            or stored_metadata.get("size") != size
        ):
            file_hash = calculate_file_hash(file_path)
        else:
            # Reuse existing hash if metadata unchanged
            logger.debug(f"♻️  Reusing existing hash for file: {file_path}")
            file_hash = stored_file["hash"]

        current_files[relative_path] = {
            "metadata": {"timestamp": timestamp, "size": size},
            "hash": file_hash,
        }
        file_count += 1
        logger.debug(f"Processed file {file_count}: {relative_path}")

    logger.info(f"Completed processing {file_count} files")
    hashes["files"] = current_files
    hashes["last_check"] = time.time()
    save_file_hashes(full_path, hashes)


def has_file_changed(root_dir: str, file_path: str) -> bool:
    """Check if a file has changed by comparing metadata first, then hash if needed."""
    logger.debug(f"Checking for changes in file: {file_path}")
    hashes = load_file_hashes(root_dir)
    relative_path = get_relative_path(file_path, root_dir)

    stored_file = hashes["files"].get(relative_path)
    if not stored_file:
        return True

    # Check metadata first
    timestamp, size = get_file_metadata(file_path)
    stored_metadata = stored_file["metadata"]

    if stored_metadata["timestamp"] != timestamp or stored_metadata["size"] != size:
        # Metadata changed, check hash
        current_hash = calculate_file_hash(file_path)
        has_changed = stored_file["hash"] != current_hash
        logger.info(
            f"File {file_path} {'has changed' if has_changed else 'remains unchanged'}"
        )
        logger.debug(
            f"Stored hash: {stored_file['hash']}, Current hash: {current_hash}"
        )
        return has_changed

    # Metadata unchanged, file is the same
    logger.debug("File unchanged (metadata match)")
    return False


def read_file_content(file_path: Path) -> str:
    """Read the content of a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
