import os

from ._common import (
    calculate_file_hash,
    create_embedding,
    store_embedding,
    save_hashes,
    ensure_clients,
)
from talkie.logger_setup import talkie_logger

def create(folder_path, hash_file=None):
    ensure_clients()  # Initialize clients before using them
    from ._common import index  # Import index AFTER ensure_clients() is called
    
    # Set hash_file path within the target directory
    if hash_file is None:
        hash_file = os.path.join(folder_path, ".file_hashes.json")

    # Delete all existing embeddings
    talkie_logger.info("Deleting all existing embeddings...")
    try:
        index.delete(delete_all=True)
        talkie_logger.info("Successfully deleted all existing embeddings")
    except Exception as e:
        talkie_logger.error(f"Failed to delete existing embeddings: {e}")
        raise

    talkie_logger.info(f"Starting fresh embedding creation for folder: {folder_path}")
    new_hashes = {}
    files_processed = 0
    embeddings_created = 0

    for root, _, files in os.walk(folder_path):
        for file in files:
            files_processed += 1
            file_path = os.path.join(root, file)
            
            # Skip .file_hashes.json
            if file == ".file_hashes.json":
                talkie_logger.info(f"Skipping hash file: {file_path}")
                continue
                
            talkie_logger.info(f"Processing file: {file_path}")
            file_hash = calculate_file_hash(file_path)
            embedding = create_embedding(file_path)
            if embedding is not None:
                store_embedding(file_hash, embedding)
                embeddings_created += 1
                new_hashes[file_hash] = file_path

            if files_processed % 10 == 0:  # Log progress every 10 files
                talkie_logger.info(
                    f"Progress: Processed {files_processed} files, Created {embeddings_created} embeddings"
                )

    save_hashes(hash_file, new_hashes)
    talkie_logger.info(
        f"Initial embedding creation complete. Total files processed: {files_processed}, Embeddings created: {embeddings_created}"
    )


def run(directory):
    # Remove the default hash_file parameter since it will be handled in create()
    talkie_logger.info(
        f"Starting embedding creation process for directory: {directory}"
    )
    create(directory)
    talkie_logger.info(
        f"Finished embedding creation process for directory: {directory}"
    )


def main(*args):
    """Embedding Creation Script

    This script processes files in a directory to create embeddings.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Creation Script")
    parser.add_argument("--dir", required=True, help="Directory to process")

    args = parser.parse_args(args)

    run(args.dir)
    return 0


if __name__ == "__main__":
    import sys

    talkie_logger.info("Script started")
    exit_code = main(*sys.argv[1:])
    talkie_logger.info(f"Script finished with exit code {exit_code}")
    sys.exit(exit_code)
