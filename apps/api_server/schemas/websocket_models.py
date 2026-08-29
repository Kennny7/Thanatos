# Thanatos/apps/api_server/schemas/websocket_models.py

from typing import Any, Dict, Literal, Optional, Union

from pydantic import BaseModel, Field

from shared.models import ToolCall, ToolResult


class UserMessage(BaseModel):
    """Incoming message from the WebSocket client."""
    type: Literal["user_message"] = "user_message"
    content: str = Field(..., description="Text input from the user")


class AssistantChunk(BaseModel):
    """Streamed chunk of assistant response text."""
    type: Literal["assistant_chunk"] = "assistant_chunk"
    content: str = Field(..., description="Partial or complete assistant text")


class ToolCallRequestWS(BaseModel):
    """
    WebSocket envelope for a tool call request.

    This flat structure is used for serialization over the WebSocket.
    Core logic operates on the shared `ToolCall` model; use `from_tool_call()`
    to create instances from the shared representation.
    """
    type: Literal["tool_call_request"] = "tool_call_request"
    call_id: str
    tool_name: str
    arguments: Dict[str, Any] = {}

    @classmethod
    def from_tool_call(cls, tool_call: ToolCall) -> "ToolCallRequestWS":
        """Create a WS envelope from the shared ToolCall model."""
        return cls(
            call_id=tool_call.call_id,
            tool_name=tool_call.tool_name,
            arguments=tool_call.arguments,
        )


class ToolResultMessageWS(BaseModel):
    """
    WebSocket envelope for a tool execution result.

    Serialized over the WebSocket; core logic uses the shared `ToolResult` model.
    Use `from_tool_result()` to convert from the shared representation, providing
    the associated `call_id` explicitly.
    """
    type: Literal["tool_result"] = "tool_result"
    call_id: str
    success: bool
    content: Any = None
    error: Optional[str] = None

    @classmethod
    def from_tool_result(
        cls, tool_result: ToolResult, call_id: str
    ) -> "ToolResultMessageWS":
        """Create a WS envelope from a ToolResult and its call identifier."""
        return cls(
            call_id=call_id,
            success=tool_result.success,
            content=tool_result.content,
            error=tool_result.error,
        )


class HeartbeatMessage(BaseModel):
    """Periodic heartbeat to keep the connection alive."""
    type: Literal["heartbeat"] = "heartbeat"


class ErrorMessage(BaseModel):
    """Error message sent to the client."""
    type: Literal["error"] = "error"
class AgentStatusMessage(BaseModel):
    """Live status update from coordinator or active sub-agent."""
    type: Literal["agent_status"] = "agent_status"
    agent: str
    status: str
    progress: float = 0.0


class ThoughtMessage(BaseModel):
    """Deep reasoning thought chunk."""
    type: Literal["thought"] = "thought"
    content: str


# Aliases for backward compatibility
ToolCallRequest = ToolCallRequestWS
ToolResultMessage = ToolResultMessageWS


# Union of all possible WebSocket messages (outgoing and incoming)
AnyMessage = Union[
    UserMessage,
    AssistantChunk,
    ToolCallRequestWS,
    ToolResultMessageWS,
    AgentStatusMessage,
    ThoughtMessage,
    HeartbeatMessage,
    ErrorMessage,
]