# Thanatos\apps\api_server\schemas\agent_models.py

"""Defines core models for the agent decision‑making layer.

The agent evaluates user input and conversation history, decides on an action
(tool call or final answer), and maintains its own state across conversation
turns.  These models encapsulate the agent’s internal representation and the
structure of the actions it produces.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from shared.models import ToolCall


class AgentState(str, Enum):
    """Possible states of the agent during a conversation turn."""
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    RESPONDING = "responding"
    ERROR = "error"


class AgentAction(BaseModel):
    """An action the agent decides to take.

    The action is either a request to call an external tool (``tool_call``)
    or a direct response to the user (``final_answer``).
    """
    action_type: Literal["tool_call", "final_answer"] = Field(
        ...,
        description="The kind of action: 'tool_call' or 'final_answer'",
    )
    tool_call: Optional[ToolCall] = Field(
        None,
        description="Details of the tool invocation; required when action_type is 'tool_call'",
    )
    reason: Optional[str] = Field(
        None,
        description="Brief explanation why the agent chose this action",
    )

    @property
    def is_tool_call(self) -> bool:
        """Return True if the action is a tool call."""
        return self.action_type == "tool_call"

    @property
    def is_final_answer(self) -> bool:
        """Return True if the action is a final answer."""
        return self.action_type == "final_answer"


class AgentContext(BaseModel):
    """Full context passed to the agent for a single turn."""
    session_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_input: str
    available_tools: List[str] = Field(default_factory=list)
    state: AgentState = AgentState.IDLE
