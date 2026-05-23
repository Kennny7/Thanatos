# Thanatos/apps/api_server/core/dispatcher.py

"""
Placeholder dispatcher that routes tool calls to actual implementations.
In production this would invoke the MCP server, sandbox, or local tools.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from ..schemas.tool_models import ToolCall, ToolResult

logger = logging.getLogger(__name__)

# A fake registry of tool names -> async handler functions (replace with real plugin loading)
_TOOL_REGISTRY: Dict[str, Any] = {}


def register_tool(name: str, handler: Any) -> None:
    """Register a tool handler (for mocking in tests)."""
    _TOOL_REGISTRY[name] = handler


async def dispatch_tool_call(tool_call: ToolCall) -> ToolResult:
    """
    Look up the tool name and execute it, returning a ToolResult.
    In real code this would call the MCP server or sandbox.
    """
    handler = _TOOL_REGISTRY.get(tool_call.tool_name)
    if handler is None:
        logger.warning("Tool not found: %s", tool_call.tool_name)
        return ToolResult(
            call_id=tool_call.call_id,
            success=False,
            error=f"Tool '{tool_call.tool_name}' not registered.",
        )

    # Simulate async execution
    try:
        # Call the handler (could be an async function)
        result = handler(tool_call.arguments) if not asyncio.iscoroutinefunction(handler) else await handler(tool_call.arguments)
        return ToolResult(call_id=tool_call.call_id, success=True, result=result)
    except Exception as exc:
        logger.exception("Tool execution failed for %s", tool_call.tool_name)
        return ToolResult(call_id=tool_call.call_id, success=False, error=str(exc))