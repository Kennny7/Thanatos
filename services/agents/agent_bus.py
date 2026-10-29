"""
Inter-Agent Communication Bus & Shared Growth Memory.
Supports topic-based message exchanges, agent debates, collaborative decisions,
trait-aware intercommunication, and growth records.

Agents can now auto-subscribe to conversations based on topic affinity scores
from the TopicRouter, enabling organic inter-agent collaboration without
hardcoded routing rules.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    sender: str
    recipient: str  # specific agent name, 'all', or 'user'
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    topic_tags: List[str] = Field(default_factory=list)


class InterAgentBus:
    """
    Real-time communication and knowledge sharing channel between all agents.
    Now supports topic-based auto-routing and trait-aware messaging.

    Agents:
    - Alfred Vance (Head Butler & Household Manager)
    - The Prodigy (Technical Systems Architect)
    - Amelia Sterling (Private Secretary & Mentalist)
    - Velma Sinclair (Knowledge Curator & Bookworm)
    - Subagents (Developer, Crawler, Doc Writer)
    """

    def __init__(self) -> None:
        self.channel_history: List[AgentMessage] = []
        self._subscribers: Dict[str, Any] = {}
        self.growth_learnings: List[Dict[str, str]] = []
        self._pending_cc: List[Dict[str, Any]] = []

    def post_message(
        self,
        sender: str,
        recipient: str,
        content: str,
        topic_tags: Optional[List[str]] = None,
        **kwargs,
    ) -> AgentMessage:
        """Post a message to the agent channel with optional topic tags."""
        clean_content = content.strip()
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            content=clean_content,
            topic_tags=topic_tags or [],
            metadata=kwargs,
        )
        self.channel_history.append(msg)
        if len(self.channel_history) > 200:
            self.channel_history = self.channel_history[-100:]
        return msg

    def post_with_auto_cc(
        self,
        sender: str,
        primary_recipient: str,
        content: str,
        secondary_agents: Optional[List[str]] = None,
        topic_tags: Optional[List[str]] = None,
        **kwargs,
    ) -> AgentMessage:
        """
        Post a message and auto-CC secondary agents based on topic routing.
        Secondary agents are notified but the primary agent handles the response.
        """
        msg = self.post_message(
            sender=sender,
            recipient=primary_recipient,
            content=content,
            topic_tags=topic_tags,
            **kwargs,
        )

        # Record CC'd agents for potential follow-up commentary
        if secondary_agents:
            for agent_id in secondary_agents:
                self._pending_cc.append({
                    "agent_id": agent_id,
                    "message_content": content[:200],
                    "primary_agent": primary_recipient,
                    "timestamp": msg.timestamp,
                })
            # Cap pending CC queue
            if len(self._pending_cc) > 50:
                self._pending_cc = self._pending_cc[-30:]

        return msg

    def get_pending_cc(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get and clear any pending CC notifications for a specific agent."""
        pending = [cc for cc in self._pending_cc if cc["agent_id"] == agent_id]
        self._pending_cc = [cc for cc in self._pending_cc if cc["agent_id"] != agent_id]
        return pending

    def get_recent_dialogue(self, limit: int = 6) -> List[AgentMessage]:
        """Fetch latest conversational exchanges."""
        return self.channel_history[-limit:]

    def get_agent_dialogue(self, agent_name: str, limit: int = 10) -> List[AgentMessage]:
        """Fetch recent messages involving a specific agent."""
        return [
            msg for msg in self.channel_history[-50:]
            if msg.sender == agent_name or msg.recipient in (agent_name, "all")
        ][-limit:]

    def record_agent_growth(self, agent_name: str, learning: str) -> None:
        """Register persistent growth memory for an agent."""
        self.growth_learnings.append({
            "agent": agent_name,
            "learning": learning,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def get_growth_summary(self) -> str:
        """Format growth summary for prompt injection."""
        if not self.growth_learnings:
            return "No previous learned corrections."
        recent = self.growth_learnings[-5:]
        return "\n".join([f"- [{g['agent']}]: {g['learning']}" for g in recent])


agent_bus = InterAgentBus()
