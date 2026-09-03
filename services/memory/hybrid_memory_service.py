# Thanatos/services/memory/hybrid_memory_service.py

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .vector_store import VectorStore
from config.settings import app_config

logger = logging.getLogger(__name__)

USER_DATA_FILE = os.path.join(app_config.memory_persist_dir, "user_facts.json")


class DynamicUserProfile(BaseModel):
    name: Optional[str] = None
    assistant_name: str = "Aegis"
    traits: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class HybridMemoryService:
    """
    Hybrid memory service that automatically updates user facts and performs
    vector search without hardcoding profile values.
    """

    def __init__(
        self,
        persist_directory: str = app_config.memory_persist_dir,
        collection_name: str = app_config.memory_collection,
    ) -> None:
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
        self.profile = self._load_profile()

    def _load_profile(self) -> DynamicUserProfile:
        os.makedirs(self.persist_directory, exist_ok=True)
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return DynamicUserProfile.model_validate(data)
            except Exception as e:
                logger.warning("Could not read user facts file, starting fresh: %s", e)
        # Fallback to configured name if available
        default_name = app_config.user_name if hasattr(app_config, "user_name") and app_config.user_name != "John Doe" else None
        return DynamicUserProfile(name=default_name)

    def save_profile(self) -> None:
        os.makedirs(self.persist_directory, exist_ok=True)
        try:
            with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profile.model_dump(), f, indent=2)
        except Exception as e:
            logger.error("Failed to save user facts: %s", e)

    def extract_and_remember(self, user_text: str) -> None:
        """
        Lightweight heuristic rule/entity extractor for real-time memory capture.
        Learns name, preferences, skills, and important facts automatically.
        """
        lower = user_text.strip().lower()

        # Name extraction: "my name is X" or "call me X" or "i am X"
        name_match = re.search(r"(?:my name is|call me|i am)\s+([A-Za-z0-9_-]+)", user_text, re.IGNORECASE)
        if name_match and not any(w in name_match.group(1).lower() for w in ["looking", "trying", "here", "ready", "happy", "working"]):
            extracted_name = name_match.group(1).strip()
            if extracted_name.lower() not in ["a", "an", "the"]:
                self.profile.name = extracted_name
                self.save_profile()
                logger.info("Learned user name: %s", extracted_name)

        # Assistant name extraction: "call yourself X" or "your name is X"
        asst_match = re.search(r"(?:call yourself|your name is|you are named)\s+([A-Za-z0-9_-]+)", user_text, re.IGNORECASE)
        if asst_match:
            new_asst_name = asst_match.group(1).strip()
            self.profile.assistant_name = new_asst_name
            self.save_profile()
            logger.info("Updated assistant name: %s", new_asst_name)

        # Skill / interest extraction: "i like X", "i work with X", "i know X"
        skill_match = re.search(r"(?:i work with|i use|i code in|proficient in)\s+([A-Za-z0-9#+.\s]{2,30})", user_text, re.IGNORECASE)
        if skill_match:
            skill = skill_match.group(1).strip().strip(".,")
            if skill and skill not in self.profile.skills:
                self.profile.skills.append(skill)
                self.save_profile()

        # Add conversation turn to semantic vector memory if meaningful
        if len(user_text.split()) >= 4:
            try:
                self.vector_store.add_documents(
                    texts=[user_text],
                    metadatas=[{"source": "user_dialogue", "type": "observation"}],
                )
            except Exception as e:
                logger.debug("Failed indexing conversation snippet: %s", e)

    def get_context(self, query: str) -> str:
        """
        Assemble unified background context for LLM prompt.
        """
        parts = []
        if self.profile.name:
            parts.append(f"- User Name: {self.profile.name}")
        if self.profile.assistant_name:
            parts.append(f"- Assistant Preferred Name: {self.profile.assistant_name}")
        if self.profile.skills:
            parts.append(f"- User Known Skills / Tech: {', '.join(self.profile.skills)}")
        if self.profile.traits:
            parts.append(f"- User Traits: {', '.join(self.profile.traits)}")

        # Retrieve semantic memories
        try:
            semantic_hits = self.vector_store.search(query, k=3)
            memories = [h["text"] for h in semantic_hits if h.get("score", 0) > 0.15]
        except Exception:
            memories = []

        memory_text = "\n".join([f"- {m}" for m in memories]) if memories else "No relevant prior context."
        user_facts_text = "\n".join(parts) if parts else "No established user profile yet. Learn dynamically through dialogue."

        return f"""### Active User Knowledge & Preferences
{user_facts_text}

### Recalled Prior Dialogue & Notes
{memory_text}"""


hybrid_memory = HybridMemoryService()
