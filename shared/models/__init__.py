# Thanatos/shared/models/__init__.py

"""
Core data models that serve as cross‑project contracts for the Thanatos ecosystem.
These classes define the immutable shapes of data passed between components,
ensuring consistency and decoupling across modules and services.
"""

from .agent_event import AgentEvent
from .tool_call import ToolCall
from .tool_definition import ToolDefinition
from .tool_result import ToolResult

__all__ = ["AgentEvent", "ToolCall", "ToolDefinition", "ToolResult"]