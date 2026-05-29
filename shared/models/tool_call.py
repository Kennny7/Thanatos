# Thanatos/shared/models/tool_call.py
"""
Model representing a concrete request to execute a tool.

Used by the LLM Brain to request a tool execution and by the Dispatcher to route the call.
"""

import uuid
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class ToolCall(BaseModel):
    """A request to invoke a specific tool with given arguments."""

    call_id: str
    """Unique identifier for this call (UUID hex string)."""

    tool_name: str
    """Exact name of the tool to invoke."""

    arguments: Dict[str, Any]
    """Parameter dictionary to pass to the tool."""

    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def generate_call_id() -> str:
        """Return a new UUID4 hex string suitable as a call ID."""
        return uuid.uuid4().hex

    def __init__(self, **data: Any) -> None:
        if "call_id" not in data:
            data["call_id"] = self.generate_call_id()
        super().__init__(**data)