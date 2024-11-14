from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from talkie.logger_setup import talkie_logger
import os


class EmbeddingManager:
    def __init__(
        self,
        collection_name: str,
        openai_api_key: str,
        persist_directory: Optional[str] = None,
        model: str = "text-embedding-ada-002",
    ):
        """Initialize the EmbeddingManager with ChromaDB and OpenAI settings.

        Args:
            collection_name: Name of the ChromaDB collection
            openai_api_key: OpenAI API key for generating embeddings
            persist_directory: Optional directory to persist ChromaDB data
            model: OpenAI model to use for embeddings
        """
        self.model = model
        self.client = OpenAI(api_key=openai_api_key)

        # Create persistence directory if it doesn't exist
        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)

        # Initialize ChromaDB client with persistence enabled
        settings = Settings(
            persist_directory=persist_directory if persist_directory else None,
            is_persistent=True,
        )

        self.chroma_client = chromadb.Client(settings)

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name
        )

    def create_embedding(self, text: str) -> List[float]:
        """Create an embedding for the given text using OpenAI."""
        try:
            response = self.client.embeddings.create(input=text, model=self.model)
            return response.data[0].embedding
        except Exception as e:
            talkie_logger.error(f"Failed to create embedding: {e}")
            raise

    def add(
        self,
        texts: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add documents and their embeddings to the collection.

        Args:
            texts: List of text documents
            ids: List of unique IDs for the documents
            metadata: Optional list of metadata dictionaries for each document
        """
        try:
            embeddings = [self.create_embedding(text) for text in texts]
            self.collection.add(
                embeddings=embeddings, documents=texts, ids=ids, metadatas=metadata
            )
            talkie_logger.info(
                f"Successfully added {len(texts)} documents to collection"
            )
        except Exception as e:
            talkie_logger.error(f"Failed to add documents: {e}")
            raise

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query the collection using a text query.

        Args:
            query_text: Text to search for
            n_results: Number of results to return
            metadata_filter: Optional filter for metadata fields
        """
        try:
            query_embedding = self.create_embedding(query_text)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=metadata_filter,
            )
            return results
        except Exception as e:
            talkie_logger.error(f"Failed to query collection: {e}")
            raise

    def update(
        self,
        texts: List[str],
        ids: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update existing documents in the collection.

        Args:
            texts: List of updated text documents
            ids: List of IDs for the documents to update
            metadata: Optional list of updated metadata dictionaries
        """
        try:
            embeddings = [self.create_embedding(text) for text in texts]
            self.collection.update(
                embeddings=embeddings, documents=texts, ids=ids, metadatas=metadata
            )
            talkie_logger.info(f"Successfully updated {len(texts)} documents")
        except Exception as e:
            talkie_logger.error(f"Failed to update documents: {e}")
            raise

    def delete(self, ids: Optional[List[str]] = None) -> None:
        """Delete documents from the collection.

        Args:
            ids: Optional list of IDs to delete. If None, deletes all documents.
        """
        try:
            if ids is None:
                self.collection.delete()
                talkie_logger.info("Successfully deleted all documents")
            else:
                self.collection.delete(ids=ids)
                talkie_logger.info(f"Successfully deleted {len(ids)} documents")
        except Exception as e:
            talkie_logger.error(f"Failed to delete documents: {e}")
            raise

    def get(self, ids: List[str]) -> Dict[str, Any]:
        """Retrieve specific documents by their IDs.

        Args:
            ids: List of document IDs to retrieve
        """
        try:
            return self.collection.get(ids=ids)
        except Exception as e:
            talkie_logger.error(f"Failed to get documents: {e}")
            raise

    def delete_collection(self):
        """Delete the current collection."""
        self.chroma_client.delete_collection(self.collection.name)
        # Recreate the collection after deletion
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection.name
        )
