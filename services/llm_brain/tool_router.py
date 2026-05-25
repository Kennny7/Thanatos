from __future__ import annotations
import logging
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from pydantic import BaseModel
from plugins.base.registry import PluginRegistry  
from sandbox.docker_manager import SandboxExecutor

logger = logging.getLogger(__name__)

class ToolResult(BaseModel):
    """Standard result from any tool execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None

@runtime_checkable
class ToolHandler(Protocol):
    """Expected interface for a tool handler (plugin)."""
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        ...

class ToolRouter:
    """
    Dispatches tool calls to the appropriate handler.
    Built‑in tools are handled internally; custom tools are looked up
    via the PluginRegistry.
    """

    def __init__(self, registry: PluginRegistry, sandbox: Optional[SandboxExecutor] = None):
        self.registry = registry
        self.sandbox = sandbox
        # Map of built‑in tool names → handler methods
        self._builtin_handlers = {
            "launch_application": self._launch_app,
            "search_web": self._search_web,
            "get_system_info": self._get_system_info,
            "execute_command": self._execute_command,
            "remember_fact": self._remember_fact,
            "recall_fact": self._recall_fact,
            "open_url": self._open_url,
        }

    async def route(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """
        Execute the named tool with the given arguments.
        Raises ValueError if tool is unknown.
        """
        # 1. Check built‑ins first
        handler = self._builtin_handlers.get(tool_name)
        if handler:
            logger.debug("Routing built‑in tool: %s", tool_name)
            return await handler(args)

        # 2. Look up in plugin registry
        plugin = self.registry.get_tool(tool_name)
        if plugin and isinstance(plugin, ToolHandler):
            logger.debug("Routing plugin tool: %s", tool_name)
            return await plugin.execute(args)

        raise ValueError(f"Unknown tool: {tool_name}")

    # ------------------------------------------------------------------ #
    # Built‑in tool handlers (stubs that log and return dummy results)
    # In production these would delegate to os_automation, web, etc.
    # ------------------------------------------------------------------ #
    async def _launch_app(self, args: Dict[str, Any]) -> ToolResult:
        logger.info("launch_application called with %s", args)
        # e.g., os_automation.router.launch(args["app_name"], args.get("arguments"))
        return ToolResult(success=True, data=f"Launched {args['app_name']}")

    async def _search_web(self, args: Dict[str, Any]) -> ToolResult:
        logger.info("search_web called with %s", args)
        return ToolResult(success=True, data="[dummy search results]")

    async def _get_system_info(self, args: Dict[str, Any]) -> ToolResult:
        info_type = args["info_type"]
        logger.info("get_system_info for %s", info_type)
        return ToolResult(success=True, data=f"System {info_type} info")

    async def _execute_command(self, args: Dict[str, Any]) -> ToolResult:
        command = args["command"]
        logger.info("execute_command: %s", command)
        # Would pass to sandbox executor
        return ToolResult(success=True, data="Command executed (sandboxed)")

    async def _remember_fact(self, args: Dict[str, Any]) -> ToolResult:
        logger.info("remember_fact: %s", args["key"])
        # Would call memory.vector_store.store()
        return ToolResult(success=True, data="Fact remembered")

    async def _recall_fact(self, args: Dict[str, Any]) -> ToolResult:
        key = args.get("key", args.get("semantic_query"))
        logger.info("recall_fact: %s", key)
        # Would call memory.vector_store.query()
        return ToolResult(success=True, data="[recalled fact]")

    async def _open_url(self, args: Dict[str, Any]) -> ToolResult:
        logger.info("open_url: %s", args["url"])
        return ToolResult(success=True, data="Opened URL")