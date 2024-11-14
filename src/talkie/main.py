import os
from dotenv import load_dotenv
from talkie.rag.embedding import EmbeddingManager
from pprint import pprint

# Load environment variables (make sure you have .env file with OPENAI_API_KEY)
load_dotenv()

def main():
    # Initialize the embedding manager
    manager = EmbeddingManager(
        collection_name="demo_collection",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        persist_directory="./chroma_db"  # This will store the database in your notebook directory
    )

    # Add some sample documents
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a subset of artificial intelligence",
        "Python is a versatile programming language"
    ]
    ids = ["doc1", "doc2", "doc3"]
    metadata = [
        {"source": "sample1"},
        {"source": "sample2"},
        {"source": "sample3"}
    ]

    # Add documents to the collection
    manager.add(texts=texts, ids=ids, metadata=metadata)

    # Query similar documents
    query = "Tell me about AI"
    results = manager.query(query_text=query, n_results=2)
    pprint(f"Query results: {results}")

    # Get specific documents
    docs = manager.get(ids=["doc1"])
    pprint(f"Retrieved document: {docs}")

    # Update a document
    manager.update(
        texts=["Updated: The quick brown fox is very quick"],
        ids=["doc1"]
    )

    # Delete a document
    manager.delete(ids=["doc3"])

if __name__ == "__main__":
    main()