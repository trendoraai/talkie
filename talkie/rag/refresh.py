import os
from typing import Optional, Dict, Tuple, List, Any

from ._common import (
    calculate_file_hash,
    create_embedding,
    store_embedding,
    load_existing_hashes,
    save_hashes,
    ensure_clients,
)
from talkie.logger_setup import talkie_logger


def delete_embedding(index_module: Any, hash_id: str) -> bool:
    """Delete an embedding by its hash ID."""
    try:
        index_module.delete(ids=[hash_id])
        talkie_logger.info(f"Deleted embedding with hash ID: {hash_id}")
        return True
    except Exception as e:
        talkie_logger.error(f"Failed to delete embedding {hash_id}: {e}")
        return False


def get_hash_file_path(directory: str) -> str:
    """Get the path to the hash file within the directory."""
    return os.path.join(directory, ".file_hashes.json")


def load_hashes(hash_file: str) -> Dict[str, str]:
    """Load existing hashes from the hash file."""
    return load_existing_hashes(hash_file)


def find_old_hash(existing_hashes: Dict[str, str], file_path: str) -> Optional[str]:
    """Find the old hash for a given file path."""
    return next((h for h, p in existing_hashes.items() if p == file_path), None)


def process_file(
    file_path: str,
    existing_hashes: Dict[str, str],
    current_hashes: Dict[str, str],
    index_module: Any,
) -> Tuple[int, int]:
    """
    Process a single file to determine if it's new, modified, or unchanged.

    Returns:
        A tuple containing (embeddings_created, embeddings_updated)
    """
    embeddings_created = 0
    embeddings_updated = 0

    file_hash = calculate_file_hash(file_path)
    old_hash = find_old_hash(existing_hashes, file_path)
    current_hashes[file_hash] = file_path

    if old_hash and old_hash != file_hash:
        # File was modified
        talkie_logger.info(f"Modified file detected: {file_path}")
        embedding = create_embedding(file_path)
        if embedding:
            if delete_embedding(index_module, old_hash):
                store_embedding(file_hash, embedding)
                embeddings_updated += 1
                talkie_logger.info(f"Updated embedding for modified file: {file_path}")
    elif file_hash not in existing_hashes:
        # New file
        talkie_logger.info(f"New file detected: {file_path}")
        embedding = create_embedding(file_path)
        if embedding:
            store_embedding(file_hash, embedding)
            embeddings_created += 1
    else:
        # Unchanged file
        talkie_logger.debug(f"Unchanged file: {file_path}")

    return embeddings_created, embeddings_updated


def handle_deleted_files(
    existing_hashes: Dict[str, str], current_hashes: Dict[str, str], index_module: Any
) -> int:
    """Handle deletions by removing embeddings of files no longer present."""
    embeddings_deleted = 0
    for old_hash, old_path in existing_hashes.items():
        if old_hash not in current_hashes:
            talkie_logger.info(f"File no longer exists: {old_path}")
            if delete_embedding(index_module, old_hash):
                embeddings_deleted += 1
                talkie_logger.info(f"Deleted embedding for removed file: {old_path}")
    return embeddings_deleted


def log_summary(
    files_processed: int,
    embeddings_created: int,
    embeddings_updated: int,
    embeddings_deleted: int,
    files_unchanged: int,
) -> None:
    """Log the summary of the embedding refresh process."""
    talkie_logger.info(
        f"Refresh complete:\n"
        f"- Files processed: {files_processed}\n"
        f"- New embeddings created: {embeddings_created}\n"
        f"- Embeddings updated: {embeddings_updated}\n"
        f"- Old embeddings deleted: {embeddings_deleted}\n"
        f"- Files unchanged: {files_unchanged}"
    )


def refresh_embeddings(directory: str) -> None:
    """Refresh embeddings for files in the specified directory."""
    ensure_clients()  # Initialize clients before using them

    # Dynamic import of index after initializing clients
    from ._common import index  # noqa: E402

    talkie_logger.info(f"Starting embedding refresh process for directory: {directory}")
    hash_file = get_hash_file_path(directory)

    existing_hashes = load_hashes(hash_file)
    current_hashes: Dict[str, str] = {}

    # Statistics for logging
    files_processed = 0
    embeddings_created = 0
    embeddings_updated = 0
    embeddings_deleted = 0
    files_unchanged = 0

    # Traverse the directory and process files
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name == ".file_hashes.json":
                continue  # Skip the hash file

            files_processed += 1
            file_path = os.path.join(root, file_name)

            created, updated = process_file(
                file_path, existing_hashes, current_hashes, index
            )
            embeddings_created += created
            embeddings_updated += updated

    # Handle deletions
    embeddings_deleted = handle_deleted_files(existing_hashes, current_hashes, index)

    # Count unchanged files
    files_unchanged = files_processed - embeddings_created - embeddings_updated

    # Save the updated hashes
    save_hashes(hash_file, current_hashes)

    # Log the summary
    log_summary(
        files_processed,
        embeddings_created,
        embeddings_updated,
        embeddings_deleted,
        files_unchanged,
    )


def parse_arguments(args: Optional[List[str]] = None) -> Any:
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Refresh Script")
    parser.add_argument("--dir", required=True, help="Directory to process")

    return parser.parse_args(args)


def main(*args: str) -> int:
    """Entry point for the Embedding Refresh Script."""
    try:
        parsed_args = parse_arguments(args)
        refresh_embeddings(parsed_args.dir)
        return 0
    except Exception as e:
        talkie_logger.error(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    import sys

    talkie_logger.info("Refresh script started")
    exit_code = main(*sys.argv[1:])
    talkie_logger.info(f"Refresh script finished with exit code {exit_code}")
    sys.exit(exit_code)
