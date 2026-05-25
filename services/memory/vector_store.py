# Thanatos\services\memory\vector_store.py
"""
ChromaDB vector store wrapper with persistent local storage.
"""

import uuid
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from .embeddings import MiniLMEmbeddingFunction


class VectorStore:
    """
    Manages a ChromaDB collection for storing and searching text embeddings.
    Uses a persistent client that writes to a local directory.
    """

    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "memory_store",
        embedding_function: Optional[MiniLMEmbeddingFunction] = None,
    ) -> None:
        """
        Args:
            persist_directory: Path to the directory where ChromaDB data will be stored.
            collection_name: Name of the ChromaDB collection.
            embedding_function: Optional custom embedding function. If None,
                a default CPU-bound MiniLMEmbeddingFunction is created.
        """
        # Create a persistent ChromaDB client (data survives restarts).
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        if embedding_function is None:
            self.embedding_function = MiniLMEmbeddingFunction()
        else:
            self.embedding_function = embedding_function

        # Get or create the collection with cosine distance (default for semantic search).
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add a batch of documents to the vector store.

        Args:
            texts: List of document texts.
            metadatas: List of metadata dictionaries (same length as texts).
                Defaults to empty metadata for each document.
            ids: Optional list of unique IDs. If not provided, UUIDs are generated.

        Returns:
            List of IDs of the inserted documents.

        Raises:
            ValueError: If texts is empty.
        """
        if not texts:
            raise ValueError("At least one document text must be provided.")

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        if metadatas is None:
            metadatas = [{}] * len(texts)

        if len(texts) != len(metadatas) or len(texts) != len(ids):
            raise ValueError("Lengths of texts, metadatas, and ids must match.")

        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
        return ids

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Query the vector store for documents semantically similar to the query.

        Args:
            query: The search query text.
            k: Number of top results to return.

        Returns:
            A list of dictionaries with keys:
                - text: The original document text.
                - metadata: The associated metadata dictionary.
                - score: A similarity score between 0 and 1 (1 = perfect match).
                  Computed as 1 - cosine_distance.

        Raises:
            ValueError: If query is empty or whitespace-only.
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        results = self.collection.query(query_texts=[query], n_results=k)

        # ChromaDB returns lists of lists; we queried a single text so take the first element.
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        formatted = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Convert cosine distance to similarity score.
            # Cosine distance = 1 - cosine_similarity, so similarity = 1 - distance.
            score = 1.0 - dist if dist is not None else None
            formatted.append({"text": doc, "metadata": meta, "score": score})

        return formatted

    def delete_collection(self) -> None:
        """Delete the underlying collection (use with caution)."""
        self.client.delete_collection(self.collection.name)