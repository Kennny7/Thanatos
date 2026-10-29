# Thanatos/services/agents/agent_roster.py
"""
Scalable Multi-Agent Registry & Lazy-Loading Persona Service.
Architecture:
- Index registry in config/agents/index.json provides lightweight routing metadata.
- Detailed agent profiles live in dedicated files: config/agents/<agent_id>.json.
- Lazy-loads full personality & prompt context ONLY when that specific agent is invoked,
  preventing context bloat, token wastage, and unnecessary memory consumption.
- Immutable agent_id decouples persistent memory stores from cosmetic name changes.
- Integrates with TraitEngine for dynamic personality evolution (RL-driven).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

AGENTS_DIR = os.path.join("config", "agents")
INDEX_PATH = os.path.join(AGENTS_DIR, "index.json")

# Legacy ID mappings for backward compatibility
LEGACY_AGENT_IDS = {
    "site_engineer": "librarian",
}


class AgentIndexEntry(BaseModel):
    id: str
    name: str
    display_name: str
    role: str
    persona_title: str
    voice: str = "en-US-JennyNeural"
    profile_path: str
    memory_partition: str


class FullAgentProfile(BaseModel):
    schema_version: str = "2.0"
    id: str
    name: str
    full_name: Optional[str] = None
    display_name: str
    role: str
    persona_title: str
    voice: str = "en-US-JennyNeural"
    avatar_style: str = ""
    personality: str = ""
    appearance: Dict[str, Any] = Field(default_factory=dict)
    specialization: List[str] = Field(default_factory=list)
    traits: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    memory_partition: str
    shared_memory_access: bool = True
    trait_engine_enabled: bool = True


class AgentRoster:
    """
    Scalable Agent Registry that maintains a lightweight directory index
    and loads full individual agent profiles on-demand.
    Now integrates with the RL TraitEngine for dynamic personality.
    """

    def __init__(self, index_file: str = INDEX_PATH, agents_dir: str = AGENTS_DIR) -> None:
        self.index_file = index_file
        self.agents_dir = agents_dir
        self.active_agent_id: str = "auto"
        self.index: Dict[str, AgentIndexEntry] = {}
        self._loaded_profiles: Dict[str, FullAgentProfile] = {}
        self.load_index()

    def load_index(self) -> None:
        """Load the lightweight agent directory index without parsing all full profiles."""
        os.makedirs(self.agents_dir, exist_ok=True)
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_agent_id = data.get("active_agent_id", "auto")
                    self.index = {
                        entry["id"]: AgentIndexEntry(**entry)
                        for entry in data.get("index", [])
                    }
                    return
            except Exception as e:
                logger.error("Failed loading %s: %s", self.index_file, e)

        # Fallback index initialization if index.json is absent
        self.active_agent_id = "auto"
        self.index = {
            "butler": AgentIndexEntry(
                id="butler",
                name="Alfred Vance",
                display_name="Alfred Vance (Head Butler & Household Manager)",
                role="Head Butler & Household Manager",
                persona_title="Alfred",
                voice="en-GB-RyanNeural",
                profile_path=os.path.join(self.agents_dir, "butler.json"),
                memory_partition="data/agent_memory/butler",
            ),
            "tech_prodigy": AgentIndexEntry(
                id="tech_prodigy",
                name="Felix Ashworth",
                display_name="Felix Ashworth (Technical Systems Architect)",
                role="Technical Systems Architect",
                persona_title="Felix",
                voice="en-US-GuyNeural",
                profile_path=os.path.join(self.agents_dir, "tech_prodigy.json"),
                memory_partition="data/agent_memory/tech_prodigy",
            ),
            "secretary": AgentIndexEntry(
                id="secretary",
                name="Amelia Sterling",
                display_name="Amelia Sterling (Private Secretary & Mentalist)",
                role="Private Secretary & Psychological Counselor",
                persona_title="Amelia",
                voice="en-US-AriaNeural",
                profile_path=os.path.join(self.agents_dir, "secretary.json"),
                memory_partition="data/agent_memory/secretary",
            ),
            "librarian": AgentIndexEntry(
                id="librarian",
                name="Velma Sinclair",
                display_name="Velma Sinclair (Knowledge Curator & Bookworm)",
                role="Knowledge Curator & Research Librarian",
                persona_title="Velma",
                voice="en-US-JennyNeural",
                profile_path=os.path.join(self.agents_dir, "site_engineer.json"),
                memory_partition="data/agent_memory/site_engineer",
            ),
        }
        self.save_index()

    def save_index(self) -> None:
        """Persist directory index."""
        os.makedirs(os.path.dirname(os.path.abspath(self.index_file)), exist_ok=True)
        try:
            payload = {
                "system_version": "3.0",
                "active_agent_id": self.active_agent_id,
                "trait_engine_enabled": True,
                "index": [entry.model_dump() for entry in self.index.values()],
            }
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error("Failed saving index to %s: %s", self.index_file, e)

    def list_agents(self) -> List[AgentIndexEntry]:
        """Returns lightweight directory index entries for fast listing with zero profile overhead."""
        return list(self.index.values())

    def get_agent_index_entry(self, agent_id_or_name: str) -> Optional[AgentIndexEntry]:
        """Quick lookup in lightweight index. Supports legacy ID resolution."""
        target = agent_id_or_name.lower().strip()

        # Check legacy mapping
        resolved = LEGACY_AGENT_IDS.get(target, target)

        if resolved in self.index:
            return self.index[resolved]
        if target in self.index:
            return self.index[target]

        for aid, entry in self.index.items():
            if target in (entry.name.lower(), entry.persona_title.lower(), entry.role.lower()):
                return entry
            if target == entry.persona_title.lower().split()[0]:
                return entry
        return None

    def load_agent_profile(self, agent_id_or_name: str) -> Optional[FullAgentProfile]:
        """
        Targeted on-demand loader:
        Picks up ONLY the requested agent's individual JSON file.
        Caches in-memory to prevent repeated disk I/O.
        """
        entry = self.get_agent_index_entry(agent_id_or_name)
        if not entry:
            return None

        # Return cached profile if already loaded
        if entry.id in self._loaded_profiles:
            return self._loaded_profiles[entry.id]

        profile_file = entry.profile_path
        if not os.path.exists(profile_file):
            # Try path relative to workspace
            profile_file = os.path.join(self.agents_dir, f"{entry.id}.json")

        if os.path.exists(profile_file):
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profile = FullAgentProfile(**data)
                    self._loaded_profiles[entry.id] = profile
                    return profile
            except Exception as e:
                logger.error("Failed loading agent profile %s: %s", profile_file, e)

        # Fallback minimal profile if file missing
        fallback = FullAgentProfile(
            id=entry.id,
            name=entry.name,
            display_name=entry.display_name,
            role=entry.role,
            persona_title=entry.persona_title,
            voice=entry.voice,
            memory_partition=entry.memory_partition,
        )
        self._loaded_profiles[entry.id] = fallback
        return fallback

    def update_agent_name(self, agent_id: str, new_name: str, new_title: Optional[str] = None) -> bool:
        """
        Safely update agent name across index and individual profile.
        Preserves memory partition and historical records without data loss.
        """
        entry = self.get_agent_index_entry(agent_id)
        if not entry:
            return False

        entry.name = new_name
        if new_title:
            entry.persona_title = new_title
        entry.display_name = f"{new_name} ({entry.role})"
        self.save_index()

        # Update specific profile JSON file if present
        profile = self.load_agent_profile(entry.id)
        if profile:
            profile.name = new_name
            profile.full_name = new_name
            if new_title:
                profile.persona_title = new_title
            profile.display_name = entry.display_name
            self._loaded_profiles[entry.id] = profile

            target_path = entry.profile_path if os.path.exists(entry.profile_path) else os.path.join(self.agents_dir, f"{entry.id}.json")
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(profile.model_dump(), f, indent=2)
            except Exception as e:
                logger.error("Could not write updated profile to %s: %s", target_path, e)

        return True

    def resolve_agent_id(self, agent_id: str) -> str:
        """Resolve legacy agent IDs to current IDs."""
        return LEGACY_AGENT_IDS.get(agent_id, agent_id)


roster = AgentRoster()
