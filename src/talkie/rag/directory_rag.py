import os
import openai
from openai import OpenAI
import chromadb
from chromadb import Client as ChromaClient, PersistentClient
from chromadb.config import Settings
from typing import List, Dict, Set
import pathspec
from pprint import pprint
from ..logger_setup import talkie_logger
from ..fsutils.directory import walk_respecting_ignore

# Utility Functions


def get_relative_path(base_path: str, full_path: str) -> str:
    """Return the relative path from base_path to full_path."""
    return os.path.relpath(full_path, start=base_path)


def is_file_ignored(file_path: str, ignore_patterns: pathspec.PathSpec) -> bool:
    """Check if the file matches any of the ignore patterns."""
    return ignore_patterns.match_file(file_path)


def get_file_modification_time(file_path: str) -> float:
    """Get the last modification time of the file."""
    return os.path.getmtime(file_path)


def get_or_create_collection_name(directory: str) -> str:
    """Get or create a valid collection name from the full directory path."""
    collection_name = str(directory).replace("/", "-").replace("\\", "-")
    # Remove any leading/trailing non-alphanumeric characters
    collection_name = collection_name.strip("-_")
    # Ensure it starts with an alphanumeric
    if not collection_name[0].isalnum():
        collection_name = "dir-" + collection_name
    # Truncate if too long
    collection_name = collection_name[:63]
    # Ensure it ends with an alphanumeric
    collection_name = collection_name.strip("-_")
    if not collection_name[-1].isalnum():
        collection_name = collection_name[:-1] + "-dir"
    return collection_name


# DirectoryRAG Class


class DirectoryRAG:
    def __init__(self, directory_path: str, openai_api_key: str):
        """
        Initialize the DirectoryRAG object with directory path and OpenAI API key.

        Args:
            directory_path: Path to the directory to process
            openai_api_key: OpenAI API key for embeddings
        """
        talkie_logger.info(
            f"Initializing DirectoryRAG with directory: {directory_path}"
        )
        self.directory_path = directory_path
        self.openai_api_key = openai_api_key
        # Set up ChromaDB persistence directory within the target directory
        self.persist_directory = os.path.join(directory_path, ".chromadb")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.chroma_client = self.initialize_chroma_client()
        collection_name = get_or_create_collection_name(directory_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )

    def initialize_chroma_client(self) -> PersistentClient:
        """Set up the persistent Chroma DB client."""
        # Create persistence directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        talkie_logger.info(f"Using persistent ChromaDB at: {self.persist_directory}")
        return chromadb.PersistentClient(path=self.persist_directory)

    def process_directory(self) -> None:
        """Process or update the entire directory."""
        talkie_logger.info("Starting directory processing")
        current_files = set(self.walk_directory())
        stored_files = set(self.get_stored_file_metadata().keys())

        # Identify deleted files
        deleted_files = stored_files - current_files
        if deleted_files:
            talkie_logger.info(f"Found {len(deleted_files)} files to delete")
            talkie_logger.debug(f"Files to delete: {deleted_files}")
            self.remove_deleted_files(deleted_files)

        # Process existing and new files
        files_to_process = len(current_files)
        talkie_logger.info(f"Processing {files_to_process} files")
        for rel_path in current_files:
            full_path = os.path.join(self.directory_path, rel_path)
            stored_metadata = self.get_stored_file_metadata().get(rel_path, {})
            if not self.file_has_changed(full_path, stored_metadata):
                talkie_logger.debug(f"Skipping unchanged file: {rel_path}")
                continue
            talkie_logger.info(f"Processing file: {rel_path}")
            self.process_file(rel_path, full_path)

    def walk_directory(self) -> List[str]:
        """Traverse the directory and return a list of file relative paths, respecting ignore patterns."""

        file_list = []
        for full_path in walk_respecting_ignore(self.directory_path, ".talkieignore"):
            rel_path = get_relative_path(self.directory_path, full_path)
            print("---")
            print(rel_path)
            file_list.append(rel_path)
        return file_list

    def get_stored_file_metadata(self) -> Dict[str, Dict]:
        """Retrieve metadata of stored files from Chroma DB."""
        metadata = {}
        if self.collection.count() == 0:  # Check if collection is empty
            return metadata
        results = self.collection.get(include=["metadatas"])
        for item in results["metadatas"]:
            if item and "rel_path" in item:  # Add null check
                metadata[item["rel_path"]] = item
        return metadata

    def file_has_changed(self, full_path: str, stored_metadata: Dict) -> bool:
        """Check if a file has been modified since last processing."""
        current_mod_time = get_file_modification_time(full_path)
        stored_mod_time = stored_metadata.get("mod_time", 0)
        return current_mod_time > stored_mod_time

    def process_file(self, rel_path: str, full_path: str) -> None:
        """Handle text extraction and embedding generation for a single file."""
        try:
            text = self.extract_text(full_path)
            talkie_logger.debug(f"Extracted text from {rel_path}")
            embedding = self.generate_embedding(text)
            talkie_logger.debug(f"Generated embedding for {rel_path}")
            metadata = {
                "rel_path": rel_path,
                "mod_time": get_file_modification_time(full_path),
            }
            self.store_in_chroma(rel_path, embedding, text, metadata)
            talkie_logger.debug(f"Successfully stored {rel_path} in Chroma")
        except Exception as e:
            talkie_logger.error(f"Error processing file {full_path}: {e}")
            raise

    def extract_text(self, file_path: str) -> str:
        """Extract text content from a file."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_embedding(self, text: str) -> List[float]:
        """Create an embedding for given text using OpenAI Embedding API."""
        response = self.client.embeddings.create(
            input=text, model="text-embedding-ada-002"
        )
        embedding = response.data[0].embedding
        # Log preview of the embedding (first 2 values)
        talkie_logger.debug(
            f"Generated embedding preview (first 2 values): [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]"
        )
        return embedding

    def store_in_chroma(
        self, id: str, embedding: List[float], content: str, metadata: Dict
    ) -> None:
        """Store or update a file's data in Chroma DB."""
        self.collection.upsert(
            ids=[id], embeddings=[embedding], documents=[content], metadatas=[metadata]
        )

    def remove_deleted_files(self, deleted_rel_paths: Set[str]) -> None:
        """Remove data for files that no longer exist."""
        if not deleted_rel_paths:
            talkie_logger.debug("No files to delete")
            return
        try:
            self.collection.delete(where={"rel_path": {"$in": list(deleted_rel_paths)}})
            talkie_logger.info(
                f"Successfully deleted {len(deleted_rel_paths)} files from collection"
            )
        except Exception as e:
            talkie_logger.error(f"Error deleting files from collection: {e}")
            raise

    def query(self, user_query: str) -> List[Dict]:
        """Perform a similarity search based on a user query."""
        embedding = self.generate_embedding(user_query)
        results = self.collection.query(query_embeddings=[embedding], n_results=5)
        return zip(results["ids"][0], results["documents"][0])

    def generate_response(self, query: str, relevant_chunks: List[str]) -> str:
        """Create a response based on the query and relevant chunks using OpenAI's GPT."""
        prompt = f"Question: {query}\n\nRelevant Information (you may ignore information that does not seem relevant):\n"
        for chunk in relevant_chunks:
            prompt += f"- {chunk}\n"
        prompt += "\nAnswer:"

        print(prompt)
        response = self.client.completions.create(
            model="gpt-3.5-turbo-instruct", prompt=prompt, max_tokens=150
        )
        return response.choices[0].text.strip()

    def list_embedded_files(self) -> List[Dict]:
        """
        Returns a list of all currently embedded files with their metadata.

        Returns:
            List[Dict]: List of dictionaries containing file metadata
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.get(include=["metadatas"])
        return [metadata for metadata in results["metadatas"] if metadata]

    def search_metadata(self, query: Dict) -> List[Dict]:
        """
        Search for files using a JSON-like query on metadata.

        Args:
            query: Dict containing the search criteria in ChromaDB where filter format.
                  Supported operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin

                  Examples:
                  # Find Python files in any directory
                  {"rel_path": {"$in": ["*.py", "*/*.py"]}}

                  # Find files modified after a certain time
                  {"mod_time": {"$gt": 1234567890}}

                  # Find files with exact path
                  {"rel_path": {"$eq": "src/main.py"}}

        Returns:
            List[Dict]: List of matching file metadata
        """
        results = self.collection.get(where=query, include=["metadatas"])
        return [metadata for metadata in results["metadatas"] if metadata]

    def get_file_metadata(self, rel_path: str) -> Dict:
        """
        Get metadata for a specific file.

        Args:
            rel_path: Relative path of the file

        Returns:
            Dict: File metadata or empty dict if file not found
        """
        results = self.collection.get(
            where={"rel_path": rel_path}, include=["metadatas"]
        )
        if results["metadatas"] and len(results["metadatas"]) > 0:
            return results["metadatas"][0]
        return {}
