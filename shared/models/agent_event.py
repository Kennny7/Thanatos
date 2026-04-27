# Thanatos/shared/models/agent_event.py

from dataclasses import dataclass
from typing import Optional, Any, Dict

@dataclass
class AgentEvent:
    """Represents an event in the agent's execution."""
    event_type: str  # e.g., "plan", "tool_call", "respond"
    data: Dict[str, Any]
    timestamp: Optional[float] = None