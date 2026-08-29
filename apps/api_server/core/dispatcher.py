import asyncio
import logging
from typing import Any, Callable, Dict

from plugins.base.registry import registry
from ..schemas.tool_models import ToolCall, ToolResult

logger = logging.getLogger(__name__)

# Test mock registry
_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str, handler: Any) -> None:
    """Register a custom tool handler function (for testing/mocking)."""
    _TOOL_REGISTRY[name] = handler


async def dispatch_tool_call(tool_call: ToolCall) -> ToolResult:
    """
    Unified Tool Dispatcher:
    Routes tool calls to mock handlers or registered skills in SkillRegistry.
    """
    logger.info("Dispatching tool call: %s (call_id=%s)", tool_call.tool_name, tool_call.call_id)

    # 1. Check direct test registry first
    if tool_call.tool_name in _TOOL_REGISTRY:
        try:
            handler = _TOOL_REGISTRY[tool_call.tool_name]
            result = handler(tool_call.arguments) if not asyncio.iscoroutinefunction(handler) else await handler(tool_call.arguments)
            return ToolResult(call_id=tool_call.call_id, success=True, result=result)
        except Exception as exc:
            return ToolResult(call_id=tool_call.call_id, success=False, error=str(exc))

    # 2. Check SkillRegistry
    try:
        result = await registry.dispatch(tool_call.tool_name, tool_call.arguments)
        return ToolResult(
            call_id=tool_call.call_id,
            success=result.success,
            result=result.content,
            error=result.error,
        )
    except Exception as exc:
        logger.exception("Error executing tool '%s': %s", tool_call.tool_name, exc)
        return ToolResult(
            call_id=tool_call.call_id,
            success=False,
            error=str(exc),
        )

