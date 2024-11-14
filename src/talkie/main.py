import os
from dotenv import load_dotenv
from talkie.rag.embedding import EmbeddingManager
from talkie.rag.create import FileEmbeddingManager
from pprint import pprint

# Load environment variables (make sure you have .env file with OPENAI_API_KEY)
load_dotenv()


def main():
    # Initialize the embedding manager with absolute path for ChromaDB persistence
    persist_directory = os.path.abspath("chroma_db")
    print(persist_directory)

    # First clean up any existing ChromaDB data
    # if os.path.exists(persist_directory):
    #     import shutil
    #     shutil.rmtree(persist_directory)

    # manager = EmbeddingManager(
    #     collection_name="demo_collection",
    #     openai_api_key=os.getenv("OPENAI_API_KEY"),
    #     persist_directory=persist_directory,
    # )

    # # Add some sample documents
    # texts = [
    #     "The quick brown fox jumps over the lazy dog",
    #     "Machine learning is a subset of artificial intelligence",
    #     "Python is a versatile programming language",
    # ]
    # ids = ["doc1", "doc2", "doc3"]
    # metadata = [{"source": "sample1"}, {"source": "sample2"}, {"source": "sample3"}]

    # # Add documents to the collection
    # manager.add(texts=texts, ids=ids, metadata=metadata)

    # # Query similar documents
    # query = "Tell me about AI"
    # results = manager.query(query_text=query, n_results=2)
    # pprint(f"Query results: {results}")

    # # Get specific documents
    # docs = manager.get(ids=["doc1"])
    # pprint(f"Retrieved document: {docs}")

    # # Update a document
    # manager.update(texts=["Updated: The quick brown fox is very quick"], ids=["doc1"])

    # # Delete a document
    # manager.delete(ids=["doc3"])

    # # Clean up ChromaDB client before creating a new one
    # manager.chroma_client.reset()

    manager = FileEmbeddingManager(
        directory="programming",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        persist_directory=persist_directory,
    )

    # Create embeddings for all files
    # manager.create_embeddings()

    # # Update embeddings for changed files
    # manager.update_embeddings()

    # # Delete embeddings for removed files
    # manager.delete_embeddings()

    manager.get_embeddings()

    # Search through embeddings
    results = manager.query("is ai awesome?", n_results=1)

    print(results)


if __name__ == "__main__":
    main()
