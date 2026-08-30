import inspect
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
            result = handler(tool_call.arguments) if not inspect.iscoroutinefunction(handler) else await handler(tool_call.arguments)
            return ToolResult.success_result(tool_name=tool_call.tool_name, content=result)
        except Exception as exc:
            return ToolResult.error_result(tool_name=tool_call.tool_name, error=str(exc))

    # 2. Check SkillRegistry
    try:
        result = await registry.dispatch(tool_call.tool_name, tool_call.arguments)
        return result
    except Exception as exc:
        logger.exception("Error executing tool '%s': %s", tool_call.tool_name, exc)
        return ToolResult.error_result(tool_name=tool_call.tool_name, error=str(exc))


