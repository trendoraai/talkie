import os
from typing import Optional, Dict, Tuple
import argparse

from ._common import (
    calculate_file_hash,
    create_embedding,
    store_embedding,
    save_hashes,
    ensure_clients,
)
from talkie.logger_setup import talkie_logger


def delete_all_embeddings(index_module: object) -> None:
    """Delete all existing embeddings using the provided index module."""
    talkie_logger.info("Deleting all existing embeddings...")
    try:
        index_module.delete(delete_all=True)
        talkie_logger.info("Successfully deleted all existing embeddings.")
    except Exception as e:
        talkie_logger.error(f"Failed to delete existing embeddings: {e}")
        raise


def get_hash_file_path(folder_path: str, hash_file: Optional[str] = None) -> str:
    """Determine the path for the hash file."""
    return (
        os.path.join(folder_path, ".file_hashes.json")
        if hash_file is None
        else hash_file
    )


def process_files(folder_path: str) -> Tuple[Dict[str, str], int, int]:
    """Process all files in the directory to create embeddings."""
    new_hashes: Dict[str, str] = {}
    files_processed: int = 0
    embeddings_created: int = 0

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            files_processed += 1
            file_path = os.path.join(root, file_name)

            if file_name == ".file_hashes.json":
                talkie_logger.debug(f"Skipping hash file: {file_path}")
                continue

            if process_single_file(file_path, new_hashes):
                embeddings_created += 1

            # Log progress every 10 files
            if files_processed % 10 == 0:
                talkie_logger.info(
                    f"Progress: {files_processed} files processed, "
                    f"{embeddings_created} embeddings created."
                )

    return new_hashes, files_processed, embeddings_created


def process_single_file(file_path: str, new_hashes: Dict[str, str]) -> bool:
    """Process a single file and update hashes if embedding is created."""
    talkie_logger.debug(f"Processing file: {file_path}")
    file_hash = calculate_file_hash(file_path)
    embedding = create_embedding(file_path)

    if embedding:
        store_embedding(file_hash, embedding)
        new_hashes[file_hash] = file_path
        return True
    return False


def log_final_status(files_processed: int, embeddings_created: int) -> None:
    """Log the final processing status."""
    talkie_logger.info(
        f"Embedding creation complete. "
        f"Total files processed: {files_processed}, "
        f"Embeddings created: {embeddings_created}."
    )


def create(folder_path: str, hash_file: Optional[str] = None) -> None:
    """Create embeddings for all files in the specified folder."""
    ensure_clients()  # Initialize necessary clients

    # Dynamic import of index after initializing clients
    from ._common import index  # noqa: E402

    hash_file_path = get_hash_file_path(folder_path, hash_file)

    # Delete all existing embeddings
    delete_all_embeddings(index)

    talkie_logger.info(f"Starting embedding creation for folder: {folder_path}")

    # Process files and gather hashes
    new_hashes, files_processed, embeddings_created = process_files(folder_path)

    # Save the new hashes to the hash file
    save_hashes(hash_file_path, new_hashes)

    # Log the final status
    log_final_status(files_processed, embeddings_created)


def run(directory: str) -> None:
    """Execute the embedding creation process for a given directory."""
    talkie_logger.info(f"Starting embedding creation for directory: {directory}")
    create(directory)
    talkie_logger.info(f"Finished embedding creation for directory: {directory}")


def parse_arguments(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Embedding Creation Script")
    parser.add_argument("--dir", required=True, help="Directory to process")

    return parser.parse_args(args)


def main(*args: str) -> int:
    """Entry point for the Embedding Creation Script."""
    try:
        parsed_args = parse_arguments(args)
        run(parsed_args.dir)
        return 0
    except Exception as e:
        talkie_logger.error(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    import sys

    talkie_logger.info("Script started.")
    exit_code = main(*sys.argv[1:])
    talkie_logger.info(f"Script finished with exit code {exit_code}.")
    sys.exit(exit_code)
