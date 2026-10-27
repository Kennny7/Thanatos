"""
Inter-Agent Communication Bus & Shared Growth Memory for Alfred, Amelia, Velma, and Subagents.
Supports WhatsApp-style message exchanges, agent debates, collaborative decisions, and growth records.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    sender: str
    recipient: str  # specific agent name or 'all' / 'user'
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InterAgentBus:
    """
    Real-time communication and knowledge sharing channel between:
    - Alfred Vance (Butler & Social Strategist)
    - Amelia Sterling (Executive Secretary & Routine Wingman)
    - Velma Sinclair (Site Reliability & Systems Engineer)
    - Subagents (Developer, Crawler, Doc Writer)
    """

    def __init__(self) -> None:
        self.channel_history: List[AgentMessage] = []
        self._subscribers: Dict[str, Any] = {}
        self.growth_learnings: List[Dict[str, str]] = []

    def post_message(self, sender: str, recipient: str, content: str, **kwargs) -> AgentMessage:
        """Post a short, conversational message to the agent channel."""
        clean_content = content.strip()
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            content=clean_content,
            metadata=kwargs,
        )
        self.channel_history.append(msg)
        if len(self.channel_history) > 200:
            self.channel_history = self.channel_history[-100:]
        return msg

    def get_recent_dialogue(self, limit: int = 6) -> List[AgentMessage]:
        """Fetch latest conversational exchanges."""
        return self.channel_history[-limit:]

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
