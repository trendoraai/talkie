import os

from ._common import (
    calculate_file_hash,
    create_embedding,
    store_embedding,
    load_existing_hashes,
    save_hashes,
    ensure_clients
)
from talkie.logger_setup import talkie_logger

def run(directory):
    """Refresh embeddings for files in the specified directory."""
    ensure_clients()  # Initialize clients before using them
    from ._common import index  # Import index AFTER ensure_clients() is called
    
    talkie_logger.info(f"Starting embedding refresh process for directory: {directory}")
    hash_file = os.path.join(directory, ".file_hashes.json")
    
    existing_hashes = load_existing_hashes(hash_file)
    current_hashes = {}
    
    # Statistics for logging
    files_processed = 0
    embeddings_created = 0
    embeddings_updated = 0
    embeddings_deleted = 0
    files_unchanged = 0

    # Process current files
    for root, _, files in os.walk(directory):
        for file in files:
            # Skip .file_hashes.json
            if file == ".file_hashes.json":
                continue
                
            files_processed += 1
            file_path = os.path.join(root, file)
            file_hash = calculate_file_hash(file_path)
            
            # Check if file exists in old hashes but with a different hash
            old_hash = next((h for h, p in existing_hashes.items() if p == file_path), None)
            
            current_hashes[file_hash] = file_path
            
            if old_hash and old_hash != file_hash:
                # File was modified
                talkie_logger.info(f"Modified file detected: {file_path}")
                embedding = create_embedding(file_path)
                if embedding is not None:
                    # Delete old embedding
                    try:
                        index.delete(ids=[old_hash])
                        # Store new embedding
                        store_embedding(file_hash, embedding)
                        embeddings_updated += 1
                        talkie_logger.info(f"Updated embedding for modified file: {file_path}")
                    except Exception as e:
                        talkie_logger.error(f"Failed to update embedding for {file_path}: {e}")
            elif file_hash not in existing_hashes:
                # New file
                talkie_logger.info(f"New file detected: {file_path}")
                embedding = create_embedding(file_path)
                if embedding is not None:
                    store_embedding(file_hash, embedding)
                    embeddings_created += 1
            else:
                # File exists and hasn't changed
                talkie_logger.debug(f"Unchanged file: {file_path}")
                files_unchanged += 1

    # Find and handle deleted files
    for old_hash, old_path in existing_hashes.items():
        if old_hash not in current_hashes:
            talkie_logger.info(f"File no longer exists: {old_path}")
            try:
                # Delete the old embedding
                index.delete(ids=[old_hash])
                embeddings_deleted += 1
                talkie_logger.info(f"Deleted embedding for removed file: {old_path}")
            except Exception as e:
                talkie_logger.error(f"Failed to delete embedding for {old_path}: {e}")

    # Save the updated hash mapping
    save_hashes(hash_file, current_hashes)
    
    # Log summary
    talkie_logger.info(
        f"Refresh complete:\n"
        f"- Files processed: {files_processed}\n"
        f"- New embeddings created: {embeddings_created}\n"
        f"- Embeddings updated: {embeddings_updated}\n"
        f"- Old embeddings deleted: {embeddings_deleted}\n"
        f"- Files unchanged: {files_unchanged}"
    )

def main(*args):
    """Embedding Refresh Script"""
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Refresh Script")
    parser.add_argument("--dir", required=True, help="Directory to process")

    args = parser.parse_args(args)
    run(args.dir)
    return 0

if __name__ == "__main__":
    import sys
    talkie_logger.info("Refresh script started")
    exit_code = main(*sys.argv[1:])
    talkie_logger.info(f"Refresh script finished with exit code {exit_code}")
    sys.exit(exit_code)