import os
from dotenv import load_dotenv
from pprint import pprint
from talkie.fsutils.directory import (
    walk_respecting_ignore,
    get_relative_path,
    get_absolute_path,
)
from talkie.fsutils.file import update_all_file_hashes
from talkie.rag.directory_rag import DirectoryRAG
from talkie.chat.create import create_chat
from talkie.chat.ask import ask
import asyncio


# Load environment variables (make sure you have .env file with OPENAI_API_KEY)
load_dotenv()


async def main():
    full_path = get_absolute_path("programming")
    # Example Usage

    print(full_path)

    # create_chat("third", full_path)

    ff = os.path.join(full_path, "third.md")
    await ask(ff)

    # # Replace with your directory path and OpenAI API key
    # directory_path = full_path
    # openai_api_key = os.getenv("OPENAI_API_KEY")

    # rag = DirectoryRAG(directory_path, openai_api_key)
    # rag.process_directory()

    # user_query = "What is the secret?"
    # relevant_chunks = rag.query(user_query)
    # context = []
    # for idx, chunk in enumerate(relevant_chunks):
    #     context.append(
    #         f"File {idx + 1} Name: {chunk[0]}\n File {idx + 1} Content: {chunk[1]}\n\n"
    #     )
    # answer = rag.generate_response(user_query, context)
    # print("Answer:", answer)

    # # List all embedded files
    # files = rag.list_embedded_files()
    # for file in files:
    #     print(f"File: {file['rel_path']}, Modified: {file['mod_time']}")

    # print("\nSearching for Python files:")
    # # Search for specific files using $in operator for pattern matching
    # python_files = rag.search_metadata(
    #     {
    #         "rel_path": {
    #             "$in": [
    #                 "*.md",
    #                 "*/*.md",
    #                 "*/*/*.py",
    #             ]  # Match Python files in any subdirectory
    #         }
    #     }
    # )
    # for file in python_files:
    #     print(f"Found Python file: {file['rel_path']}")

    # print("\nGetting specific file metadata:")
    # # Get metadata for a specific file
    # metadata = rag.get_file_metadata("src/main.py")
    # if metadata:
    #     print(f"File metadata: {metadata}")

    # # Find files modified after a certain time
    # recent_files = rag.search_metadata({"mod_time": {"$gt": 1234567890}})

    # # Find files with specific paths
    # specific_files = rag.search_metadata(
    #     {"rel_path": {"$in": ["src/main.py", "src/utils.py"]}}
    # )

    # # Find files modified before a certain time
    # old_files = rag.search_metadata({"mod_time": {"$lt": 1234567890}})

    # print("\nSearching for files modified after a certain time:")
    # for file in recent_files:
    #     print(f"Found file modified after 1234567890: {file['rel_path']}")

    # print("\nSearching for files with specific paths:")
    # for file in specific_files:
    #     print(f"Found file with specific path: {file['rel_path']}")

    # print("\nSearching for files modified before a certain time:")
    # for file in old_files:
    #     print(f"Found file modified before 1234567890: {file['rel_path']}")

    # relative_path = get_relative_path(full_path)

    # print(f"Full path: {full_path}")
    # print(f"Relative path: {relative_path}")

    # for file in walk_respecting_ignore(full_path, ".talkieignore"):
    #     print(f"File: {file}")

    # update_all_file_hashes(full_path)

    # Initialize the embedding manager with absolute path for ChromaDB persistence
    # persist_directory = os.path.abspath("chroma_db")
    # print(persist_directory)

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

    # manager = FileEmbeddingManager(
    #     directory="programming",
    #     openai_api_key=os.getenv("OPENAI_API_KEY"),
    #     persist_directory=persist_directory,
    # )

    # Create embeddings for all files
    # manager.create_embeddings()

    # # Update embeddings for changed files
    # manager.update_embeddings()

    # # Delete embeddings for removed files
    # manager.delete_embeddings()

    # manager.get_embeddings()

    # # Search through embeddings
    # results = manager.query("is ai awesome?", n_results=1)

    # print(results)


def quick():
    """Quick command entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    quick()
