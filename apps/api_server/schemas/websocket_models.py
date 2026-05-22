# Thanatos/apps/api_server/schemas/websocket_models.py

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class UserMessage(BaseModel):
    """Incoming message from the WebSocket client."""
    type: Literal["user_message"] = "user_message"
    content: str = Field(..., description="Text input from the user")


class AssistantChunk(BaseModel):
    """Streamed chunk of assistant response text."""
    type: Literal["assistant_chunk"] = "assistant_chunk"
    content: str = Field(..., description="Partial or complete assistant text")


class ToolCallRequest(BaseModel):
    """Request to execute a tool on the client side."""
    type: Literal["tool_call_request"] = "tool_call_request"
    tool_name: str = Field(..., description="Name of the tool to invoke")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class HeartbeatMessage(BaseModel):
    """Periodic heartbeat to keep the connection alive."""
    type: Literal["heartbeat"] = "heartbeat"


class ErrorMessage(BaseModel):
    """Error message sent to the client."""
    type: Literal["error"] = "error"
    detail: str = Field(..., description="Human-readable error description")