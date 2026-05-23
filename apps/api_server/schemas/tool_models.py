# Thanatos\apps\api_server\schemas\tool_models.py

"""Schemas for tool definitions, calls, and results."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Static definition of a tool the agent can use."""
    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Human-readable description")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for parameters",
    )


class ToolCall(BaseModel):
    """Concrete request to invoke a tool."""
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_id: str = Field(..., description="Unique ID for this call")


class ToolResult(BaseModel):
    """Result returned after a tool execution."""
    call_id: str
    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time_ms: float | None = None