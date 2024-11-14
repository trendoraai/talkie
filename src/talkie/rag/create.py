from typing import Optional, Dict, List, Any
from pathlib import Path

from talkie.rag.embedding import EmbeddingManager
from talkie.logger_setup import talkie_logger
from talkie.rag.utils import (
    load_hashes,
    save_hashes,
    calculate_file_hash,
    read_file_content,
    get_file_metadata,
    process_embedding_results,
    log_embedding_details,
)


class FileEmbeddingManager:
    def __init__(
        self,
        directory: str,
        openai_api_key: str,
        persist_directory: Optional[str] = None,
        model: str = "text-embedding-ada-002",
        hash_file: str = ".file_hashes.json",
    ):
        """Initialize the FileEmbeddingManager.

        Args:
            directory: Directory to manage embeddings for
            openai_api_key: OpenAI API key
            persist_directory: Optional directory to persist ChromaDB data
            model: OpenAI model to use for embeddings
            hash_file: Name of the file to store file hashes
        """
        self.directory = Path(directory).resolve()
        if not self.directory.is_dir():
            raise ValueError(f"{directory} is not a directory")

        self.hash_file = self.directory / hash_file
        self.file_hashes = load_hashes(self.hash_file)

        # Create a valid collection name from the full directory path
        collection_name = str(self.directory).replace("/", "-").replace("\\", "-")
        # Remove any leading/trailing non-alphanumeric characters
        collection_name = collection_name.strip("-_")
        # Ensure it starts with an alphanumeric
        if not collection_name[0].isalnum():
            collection_name = "dir" + collection_name
        # Truncate if too long
        collection_name = collection_name[:63]
        # Ensure it ends with an alphanumeric
        if not collection_name[-1].isalnum():
            collection_name = collection_name[:-1] + "dir"

        self.file_hashes["collection_name"] = collection_name

        self.embedding_manager = EmbeddingManager(
            collection_name=collection_name,
            openai_api_key=openai_api_key,
            persist_directory=persist_directory,
            model=model,
        )
        print(self.directory)

    def create_embeddings(self) -> None:
        """Create embeddings for all files in the directory.
        First deletes all existing embeddings in the collection."""
        talkie_logger.info(
            "Starting creation of embeddings for directory: %s", self.directory
        )

        self._clear_existing_embeddings()
        eligible_files = self._find_eligible_files()
        batch = self._process_eligible_files(eligible_files)
        self._add_embeddings_batch(batch)

    def _clear_existing_embeddings(self) -> None:
        """Delete all existing embeddings and reset file hashes."""
        self.embedding_manager.delete_collection()
        talkie_logger.debug("Deleted existing collection")
        self.file_hashes["files"] = {}

    def _find_eligible_files(self) -> List[Path]:
        """Find all eligible files for embedding creation."""
        eligible_files = [
            file_path
            for file_path in self.directory.rglob("*")
            if file_path.is_file() and file_path.name != self.hash_file.name
        ]
        talkie_logger.debug("Found %d eligible files", len(eligible_files))
        return eligible_files

    def _process_eligible_files(self, eligible_files: List[Path]) -> Dict[str, List]:
        """Process eligible files and prepare them for embedding creation."""
        batch = {"texts": [], "ids": [], "metadata": []}

        for file_path in eligible_files:
            try:
                talkie_logger.debug("Processing file: %s", file_path)
                self._process_single_file(file_path, batch)
                talkie_logger.debug(
                    "Successfully processed %s", file_path.relative_to(self.directory)
                )
            except Exception as e:
                talkie_logger.error("Error processing file %s: %s", file_path, e)
                continue

        return batch

    def _process_single_file(self, file_path: Path, batch: Dict[str, List]) -> None:
        """Process a single file and add its information to the batch."""
        file_hash = calculate_file_hash(file_path)
        rel_path = str(file_path.relative_to(self.directory))

        content = read_file_content(file_path)
        batch["texts"].append(content)
        batch["ids"].append(rel_path)
        batch["metadata"].append(get_file_metadata(file_path))
        self.file_hashes["files"][rel_path] = file_hash

    def _add_embeddings_batch(self, batch: Dict[str, List]) -> None:
        """Add the processed batch to the embedding collection."""
        if batch["texts"]:
            talkie_logger.debug(
                "Adding %d files to embedding collection", len(batch["texts"])
            )
            try:
                self.embedding_manager.add(
                    texts=batch["texts"], ids=batch["ids"], metadata=batch["metadata"]
                )
                save_hashes(self.hash_file, self.file_hashes)
                talkie_logger.info(
                    "Successfully created embeddings for %d files", len(batch["texts"])
                )
            except Exception as e:
                talkie_logger.error("Error adding embeddings: %s", e)
        else:
            talkie_logger.info("No files found to create embeddings for")

    def update_embeddings(self, file_path: Optional[str] = None) -> None:
        """Update embeddings for changed files."""
        talkie_logger.info(
            "Starting embedding updates for %s", file_path if file_path else "all files"
        )

        paths_to_check = self._get_paths_to_check(file_path)
        updates, additions = self._process_file_changes(paths_to_check)

        self._apply_embedding_changes(updates, additions)

    def _get_paths_to_check(self, file_path: Optional[str] = None) -> List[Path]:
        """Get list of paths to check for updates."""
        if file_path:
            return [Path(self.directory) / file_path]
        return list(self.directory.rglob("*"))

    def _process_file_changes(self, paths_to_check: List[Path]) -> tuple[dict, dict]:
        """Process files and separate them into updates and additions."""
        updates = {"texts": [], "ids": [], "metadata": []}
        additions = {"texts": [], "ids": [], "metadata": []}

        for path in paths_to_check:
            if not (path.is_file() and path.name != self.hash_file.name):
                continue

            file_hash = calculate_file_hash(path)
            rel_path = str(path.relative_to(self.directory))

            if self._is_file_changed(rel_path, file_hash):
                self._add_file_to_batch(path, rel_path, file_hash, updates)
            elif self._is_file_new(rel_path):
                self._add_file_to_batch(path, rel_path, file_hash, additions)

        return updates, additions

    def _is_file_changed(self, rel_path: str, file_hash: str) -> bool:
        """Check if file has changed."""
        return (
            rel_path in self.file_hashes["files"]
            and self.file_hashes["files"][rel_path] != file_hash
        )

    def _is_file_new(self, rel_path: str) -> bool:
        """Check if file is new."""
        return rel_path not in self.file_hashes["files"]

    def _add_file_to_batch(
        self, path: Path, rel_path: str, file_hash: str, batch: dict
    ) -> None:
        """Add file information to the specified batch."""
        action = "updating" if self._is_file_changed(rel_path, file_hash) else "adding"
        talkie_logger.debug("File %s: %s", action, rel_path)

        batch["texts"].append(read_file_content(path))
        batch["ids"].append(rel_path)
        batch["metadata"].append(get_file_metadata(path))
        self.file_hashes["files"][rel_path] = file_hash

    def _apply_embedding_changes(self, updates: dict, additions: dict) -> None:
        """Apply the embedding updates and additions."""
        if updates["texts"]:
            talkie_logger.debug(
                "Updating embeddings for %d changed files", len(updates["texts"])
            )
            self.embedding_manager.update(
                texts=updates["texts"], ids=updates["ids"], metadata=updates["metadata"]
            )

        if additions["texts"]:
            talkie_logger.debug(
                "Adding embeddings for %d new files", len(additions["texts"])
            )
            self.embedding_manager.add(
                texts=additions["texts"],
                ids=additions["ids"],
                metadata=additions["metadata"],
            )

        if updates["texts"] or additions["texts"]:
            save_hashes(self.hash_file, self.file_hashes)
            talkie_logger.info(
                "Successfully processed embeddings for %d files",
                len(updates["texts"]) + len(additions["texts"]),
            )
        else:
            talkie_logger.info("No files needed updating")

    def delete_embeddings(self, path: Optional[str] = None) -> None:
        """Delete embeddings for specified path or removed files."""
        talkie_logger.info(
            "Starting deletion of embeddings for %s", path if path else "removed files"
        )

        if path:
            self._delete_single_embedding(path)
        else:
            self._delete_removed_embeddings()

    def _delete_single_embedding(self, path: str) -> None:
        """Delete embedding for a specific path."""
        if str(path) in self.file_hashes["files"]:
            talkie_logger.debug("Deleting embedding for: %s", path)
            self.embedding_manager.delete([path])
            del self.file_hashes["files"][str(path)]
            save_hashes(self.hash_file, self.file_hashes)
            talkie_logger.info("Successfully deleted embedding for: %s", path)
        else:
            talkie_logger.warning("No embedding found for path: %s", path)

    def _delete_removed_embeddings(self) -> None:
        """Delete embeddings for all removed files."""
        deleted_paths = self._find_removed_files()

        if deleted_paths:
            talkie_logger.debug(
                "Deleting embeddings for %d removed files", len(deleted_paths)
            )
            self.embedding_manager.delete(deleted_paths)
            save_hashes(self.hash_file, self.file_hashes)
            talkie_logger.info(
                "Successfully deleted embeddings for %d removed files",
                len(deleted_paths),
            )
        else:
            talkie_logger.info("No files needed deletion")

    def _find_removed_files(self) -> List[str]:
        """Find files that no longer exist in the filesystem."""
        deleted_paths = []
        for stored_path in list(self.file_hashes["files"].keys()):
            if not (self.directory / stored_path).exists():
                talkie_logger.debug("File no longer exists: %s", stored_path)
                deleted_paths.append(stored_path)
                del self.file_hashes["files"][stored_path]
        return deleted_paths

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the embeddings.

        Args:
            query_text: Text to search for
            n_results: Number of results to return
        """
        return self.embedding_manager.query(query_text, n_results=n_results)

    def get_embeddings(self, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get embeddings for specific files or all files in the directory."""
        file_paths = self._get_file_paths(file_paths)
        if not file_paths:
            talkie_logger.info("No files found to get embeddings for")
            return {}

        try:
            results = self._fetch_embeddings(file_paths)
            if not results:
                return {}

            processed_results = process_embedding_results(results)
            log_embedding_details(processed_results)
            return results

        except Exception as e:
            talkie_logger.error(f"Error getting embeddings: {e}")
            return {}

    def _get_file_paths(self, file_paths: Optional[List[str]] = None) -> List[str]:
        """Get list of file paths to process."""
        if file_paths is not None:
            return file_paths

        return [
            str(path.relative_to(self.directory))
            for path in self.directory.rglob("*")
            if path.is_file() and path.name != self.hash_file.name
        ]

    def _fetch_embeddings(self, file_paths: List[str]) -> Dict[str, Any]:
        """Fetch embeddings from embedding manager."""
        results = self.embedding_manager.get(file_paths)
        if not results or not results.get("ids"):
            talkie_logger.info("No embeddings found for the specified files")
            return {}
        return results
