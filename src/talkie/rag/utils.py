import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

from talkie.logger_setup import talkie_logger


def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_hashes(file_path, file_hashes) -> None:
    """Save file hashes to the hash file."""
    with open(file_path, "w") as f:
        json.dump(file_hashes, f, indent=2)


def log_embedding_details(processed_results: Dict[str, List]) -> None:
    """Log embedding details for each document."""
    for i, (doc_id, metadata, embedding) in enumerate(
        zip(
            processed_results["ids"],
            processed_results["metadatas"],
            processed_results["embeddings"],
        )
    ):
        talkie_logger.debug(f"\n=== Document {i+1} ===")
        talkie_logger.debug(f"Path: {doc_id}")
        if metadata:
            talkie_logger.debug("Metadata:")
            for key, value in metadata.items():
                talkie_logger.debug(f"  {key}: {value}")
        if embedding:
            talkie_logger.debug("Embedding: [...]")


def process_embedding_results(results: Dict[str, Any]) -> Dict[str, List]:
    """Process and normalize embedding results."""
    ids = [id[0] if isinstance(id, list) else id for id in results["ids"]]
    metadatas = [
        meta[0] if isinstance(meta, list) else meta
        for meta in results.get("metadatas", [{}] * len(ids))
    ]

    embeddings = []
    if results.get("embeddings"):
        embeddings = [
            emb[0] if isinstance(emb, list) else emb for emb in results["embeddings"]
        ]
    else:
        embeddings = [None] * len(ids)

    return {"ids": ids, "metadatas": metadatas, "embeddings": embeddings}
