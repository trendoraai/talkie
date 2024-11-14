import os
import hashlib
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from talkie.logger_setup import talkie_logger
except ImportError:
    import logging

    talkie_logger = logging.getLogger("talkie")
    talkie_logger.addHandler(logging.NullHandler())

# Initialize these as None
client = None
index = None


def ensure_clients():
    global client, index
    if client is None or index is None:
        from openai import OpenAI
        from pinecone import Pinecone

        # Check for required environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")

        missing_vars = []
        if not openai_api_key:
            missing_vars.append("OPENAI_API_KEY")
        if not pinecone_api_key:
            missing_vars.append("PINECONE_API_KEY")
        if not pinecone_environment:
            missing_vars.append("PINECONE_ENVIRONMENT")
        if not pinecone_index_name:
            missing_vars.append("PINECONE_INDEX_NAME")

        if missing_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please set these variables before running the command."
            )

        try:
            client = OpenAI(api_key=openai_api_key)
            pc = Pinecone(api_key=pinecone_api_key)
            index = pc.Index(pinecone_index_name)
            talkie_logger.info("Successfully initialized OpenAI and Pinecone clients")
        except Exception as e:
            talkie_logger.error(f"Failed to initialize clients: {e}")
            raise


def _check_clients():
    """Helper function to verify clients are initialized"""
    if client is None or index is None:
        talkie_logger.error("Clients not initialized. Current state:")
        talkie_logger.error(f"OpenAI client: {'Initialized' if client else 'None'}")
        talkie_logger.error(f"Pinecone index: {'Initialized' if index else 'None'}")
        raise RuntimeError("Clients not initialized. Call ensure_clients() first.")


def calculate_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def create_embedding(file_path):
    _check_clients()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        talkie_logger.info(f"Creating embedding for file: {file_path}")
        response = client.embeddings.create(
            input=content, model="text-embedding-3-large"
        )
        talkie_logger.info(f"Successfully created embedding for {file_path}")
        return response.data[0].embedding
    except Exception as e:
        talkie_logger.error(f"Failed to create embedding for {file_path}: {e}")
        return None


def store_embedding(file_hash, embedding):
    _check_clients()
    try:
        index.upsert(vectors=[(file_hash, embedding)])
        talkie_logger.info(f"Successfully stored embedding for hash {file_hash}")
    except Exception as e:
        talkie_logger.error(f"Failed to store embedding for hash {file_hash}: {e}")


def load_existing_hashes(hash_file):
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            hashes = json.load(f)
        talkie_logger.info(f"Loaded {len(hashes)} existing hashes from {hash_file}")
        return hashes
    talkie_logger.info(f"No existing hash file found at {hash_file}")
    return {}


def save_hashes(hash_file, hashes):
    with open(hash_file, "w") as f:
        json.dump(hashes, f, indent=4)
    talkie_logger.info(f"Saved {len(hashes)} hashes to {hash_file}")
