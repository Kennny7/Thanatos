"""Data models for the agent orchestration layer."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Possible states of the agent during a conversation turn."""
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    RESPONDING = "responding"
    ERROR = "error"


class AgentAction(BaseModel):
    """An action the agent decides to take."""
    action_type: str = Field(..., description="e.g., 'tool_call', 'final_answer'")
    tool_name: Optional[str] = Field(None, description="Name of the tool if action_type is 'tool_call'")
    arguments: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = Field(None, description="Brief reason for the action")


class AgentContext(BaseModel):
    """Full context passed to the agent for a single turn."""
    session_id: str
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    user_input: str
    available_tools: List[str] = Field(default_factory=list)
    state: AgentState = AgentState.IDLE