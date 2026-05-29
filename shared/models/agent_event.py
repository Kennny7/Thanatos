# Thanatos/shared/models/agent_event.py

"""
Represents an event in the agent's execution.

Used to log agent decisions and can be consumed by the audit trail or real‑time monitoring.
"""

import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    """A structured log entry capturing an agent action or decision."""

    event_type: str
    """Category of the event (e.g. 'plan', 'tool_call', 'respond', 'error')."""

    payload: Dict[str, Any]
    """Event‑specific data."""

    timestamp: Optional[float] = Field(
        default_factory=time.time,
        description="POSIX timestamp; automatically set to the current time if omitted.",
    )

    model_config = {"extra": "forbid"}

    @classmethod
    def create_now(
        cls, event_type: str, payload: Dict[str, Any]
    ) -> "AgentEvent":
        """Create an event with the current timestamp."""
        return cls(event_type=event_type, payload=payload)