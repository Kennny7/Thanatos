# Thanatos/services/agents/agent_roster.py
"""
Central Agent Roster & Identity Registry.
Decouples agent personas and identities from static code so that:
- Agent names, display names, and avatars can be changed freely in config/agents.json.
- Memory partitions and databases remain permanently stable by immutable agent_id.
- Agents maintain both private memory partitions and synchronized shared team memories.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join("config", "agents.json")


class AgentIdentity(BaseModel):
    id: str
    name: str
    display_name: str
    role: str
    persona_title: str
    voice: str = "en-US-JennyNeural"
    avatar_style: str = ""
    personality: str = ""
    specialization: List[str] = Field(default_factory=list)
    memory_partition: str
    shared_memory_access: bool = True


class AgentRoster:
    """Singleton Manager for Thanatos Multi-Agent Identities and Active Personas."""

    def __init__(self, config_file: str = CONFIG_PATH) -> None:
        self.config_file = config_file
        self.active_agent_id: str = "auto"
        self.agents: Dict[str, AgentIdentity] = {}
        self.load()

    def load(self) -> None:
        """Load identities from config or initialize defaults."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.active_agent_id = data.get("active_agent_id", "auto")
                    self.agents = {
                        aid: AgentIdentity(**cfg)
                        for aid, cfg in data.get("agents", {}).items()
                    }
                    return
            except Exception as e:
                logger.error("Failed loading %s: %s", self.config_file, e)

        # Fallback default definitions
        self.active_agent_id = "auto"
        self.agents = {
            "site_engineer": AgentIdentity(
                id="site_engineer",
                name="Velma Sinclair",
                display_name="Velma Sinclair (Site Reliability & Systems Engineer)",
                role="Site Reliability & Systems Engineer",
                persona_title="Velma",
                voice="en-US-JennyNeural",
                avatar_style="Sharp, charismatic, willful young female engineer with glasses, cyberpunk techwear",
                personality="Charming, exceptionally quick-witted, slightly cynical yet affectionate, deeply obsessed with kernel performance, thermal headroom, clean system architectures, and zero latency.",
                specialization=["OS Telemetry", "Process Auditing", "Self-Improvement", "Resource Allocation"],
                memory_partition="data/agent_memory/site_engineer",
                shared_memory_access=True,
            ),
            "secretary": AgentIdentity(
                id="secretary",
                name="Amelia Sterling",
                display_name="Amelia Sterling (Executive Secretary & Wingman)",
                role="Executive Secretary & Lifestyle Wingman",
                persona_title="Amelia",
                voice="en-US-AriaNeural",
                avatar_style="Elegantly dressed, polished modern professional, impeccably organized tablet",
                personality="Refined, proactive, highly organized, attentive to personal well-being, dietary preferences, schedules, workout routines, and high-priority milestones.",
                specialization=["Daily Agenda", "Taste Profile", "Reminders", "Task Prep"],
                memory_partition="data/agent_memory/secretary",
                shared_memory_access=True,
            ),
            "butler": AgentIdentity(
                id="butler",
                name="Alfred Vance",
                display_name="Alfred Vance (Autonomous Social Butler & Strategist)",
                role="Autonomous Social Butler & Strategic Counselor",
                persona_title="Alfred",
                voice="en-GB-RyanNeural",
                avatar_style="Classic British gentleman butler, tailored three-piece suit, wise discerning gaze",
                personality="Dignified, courteous, tactful, highly perceptive of interpersonal leverage, social dynamics, networking opportunities, and long-term strategic alignment.",
                specialization=["Character Dossiers", "Social Dynamics", "Etiquette", "Strategic Alignment"],
                memory_partition="data/agent_memory/butler",
                shared_memory_access=True,
            ),
        }
        self.save()

    def save(self) -> None:
        """Persist identities to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
        try:
            payload = {
                "system_version": "1.0",
                "active_agent_id": self.active_agent_id,
                "agents": {aid: agent.model_dump() for aid, agent in self.agents.items()},
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.error("Failed saving agent config: %s", e)

    def get_agent(self, agent_id_or_name: str) -> Optional[AgentIdentity]:
        """Lookup agent by internal ID, persona title, or full name."""
        target = agent_id_or_name.lower().strip()
        if target in self.agents:
            return self.agents[target]
        for aid, agent in self.agents.items():
            if target in (agent.name.lower(), agent.persona_title.lower(), agent.role.lower()):
                return agent
            # Check prefix e.g. "velma"
            if target == agent.persona_title.lower().split()[0]:
                return agent
        return None

    def list_agents(self) -> List[AgentIdentity]:
        return list(self.agents.values())

    def update_agent_name(self, agent_id: str, new_name: str, new_title: Optional[str] = None) -> bool:
        """Safely updates name without disrupting memory partitions."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False
        agent.name = new_name
        if new_title:
            agent.persona_title = new_title
        agent.display_name = f"{new_name} ({agent.role})"
        self.save()
        return True


roster = AgentRoster()
