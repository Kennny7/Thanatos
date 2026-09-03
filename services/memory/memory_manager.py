# Thanatos/services/memory/memory_manager.py

import logging
from typing import Any, Dict, List, Optional

from .vector_store import VectorStore
from .user_profile import UserProfileManager, UserProfile
from config.settings import app_config

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    High-level memory and RAG manager for user preferences, facts, and profile retrieval.
    """

    def __init__(
        self,
        persist_directory: str = app_config.memory_persist_dir,
        collection_name: str = app_config.memory_collection,
    ) -> None:
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
        self.user_profile = UserProfileManager(self)

    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a text snippet in vector memory."""
        if not text or not text.strip():
            raise ValueError("Memory text cannot be empty.")
        metadata = metadata or {}
        ids = self.vector_store.add_documents(texts=[text], metadatas=[metadata])
        logger.debug("Added memory ID %s", ids[0])
        return ids[0]

    def search(self, query: str, k: int = 3, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Semantic RAG search over stored memories."""
        return self.vector_store.search(query=query, k=k, filter_metadata=filter_metadata)

    def get_relevant_context(self, user_query: str) -> str:
        """Fetch both user profile and top semantic memories for agent prompt injection."""
        results = self.search(user_query, k=2)
        profile_ctx = self.user_profile.get_resume_context()
        
        mem_snippets = []
        for r in results:
            if r.get("score", 0) > 0.2:
                mem_snippets.append(f"- {r['text']}")

        mem_block = "\n".join(mem_snippets) if mem_snippets else "No previous specific memory found."

        return f"""
{profile_ctx}

## Relevant Recalled Memories
{mem_block}
""".strip()


# Global shared instance
memory_service = MemoryManager()
