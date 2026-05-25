# Thanatos\services\memory\memory_manager.py

"""
High-level memory manager for storing and recalling user memories.
"""

import logging
from typing import Any, Dict, List, Optional

from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Public interface for the memory sub-system.
    Supports adding text memories with metadata and semantic search.
    """

    def __init__(
        self,
        persist_directory: str = "./memory_store",
        collection_name: str = "user_memories",
    ) -> None:
        """
        Args:
            persist_directory: Local path for ChromaDB persistence.
            collection_name: Name of the collection to use.
        """
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )

    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a memory snippet with optional metadata.

        Args:
            text: The text content to remember.
            metadata: Optional dictionary with additional context
                      (e.g., {"timestamp": ..., "source": "user"}).

        Returns:
            The unique ID of the stored memory.

        Raises:
            ValueError: If text is empty or whitespace.
        """
        if not text or not text.strip():
            raise ValueError("Memory text cannot be empty.")

        metadata = metadata or {}
        ids = self.vector_store.add_documents(texts=[text], metadatas=[metadata])
        memory_id = ids[0]
        logger.debug("Memory added (ID: %s): %s...", memory_id, text[:50])
        return memory_id

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the top-k most semantically similar memories.

        Args:
            query: The search query.
            k: Number of results to return (default 3).

        Returns:
            A list of result dictionaries, each containing:
                - text: The stored memory text.
                - metadata: Its associated metadata.
                - score: Similarity score (0 to 1).

        Raises:
            ValueError: If query is empty or whitespace.
        """
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        return self.vector_store.search(query=query, k=k)