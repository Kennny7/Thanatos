# Thanatos\services\llm_brain\tool_router.py

from __future__ import annotations
import logging
from typing import Any, Dict, Optional

from plugins.base.registry import SkillRegistry
from sandbox.docker_manager import SandboxExecutor
from shared.models import ToolResult

logger = logging.getLogger(__name__)


class ToolRouter:
    """
    Merges built‑in tool handlers with plugin (skill) capabilities.

    Built‑in tools are handled internally by dedicated methods.
    Custom tools are discovered through the `SkillRegistry`, which dispatches
    to the appropriate registered skill.  The router first checks the
    built‑in map, then falls back to the registry’s `dispatch` method,
    raising a `ValueError` if the tool is completely unknown.
    """

    def __init__(
        self,
        registry: SkillRegistry,
        sandbox: Optional[SandboxExecutor] = None,
    ) -> None:
        """
        Args:
            registry: The central skill registry used to resolve plugin tools.
            sandbox: Optional sandbox executor for running commands in isolation.
        """
        self.registry = registry
        self.sandbox = sandbox
        # Map of built‑in tool names → handler methods
        self._builtin_handlers: Dict[str, Any] = {
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

        The routing order is:
        1. Check the built‑in handler map.
        2. Delegate to the `SkillRegistry.dispatch` for plugin tools.

        Args:
            tool_name: Unique identifier of the tool to execute.
            args: Dictionary of parameters for the tool.

        Returns:
            A `ToolResult` produced by the handler or skill.

        Raises:
            ValueError: If the tool is not found in either the built‑in map
                        or the registry.
        """
        # 1. Check built‑ins first
        handler = self._builtin_handlers.get(tool_name)
        if handler is not None:
            logger.debug("Routing built‑in tool: %s", tool_name)
            return await handler(tool_name, args)

        # 2. Delegate to the skill registry (handles all plugin tools)
        try:
            logger.debug("Dispatching to skill registry for tool: %s", tool_name)
            res = await self.registry.dispatch(tool_name, args)
            if not getattr(res, "success", True) and "not found" in str(getattr(res, "error", "")).lower():
                raise ValueError(f"Unknown tool: {tool_name}")
            return res
        except ValueError:
            raise ValueError(f"Unknown tool: {tool_name}")

    # ------------------------------------------------------------------ #
    # Built‑in tool handlers (stubs that log and return dummy results)
    # In production these would delegate to os_automation, web, etc.
    # ------------------------------------------------------------------ #
    async def _launch_app(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `launch_application` requests."""
        logger.info("launch_application called with %s", args)
        # e.g., os_automation.router.launch(args["app_name"], args.get("arguments"))
        return ToolResult.success_result(
            tool_name, content=f"Launched {args['app_name']}"
        )

    async def _search_web(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `search_web` requests."""
        logger.info("search_web called with %s", args)
        return ToolResult.success_result(
            tool_name, content="[dummy search results]"
        )

    async def _get_system_info(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `get_system_info` requests."""
        info_type = args["info_type"]
        logger.info("get_system_info for %s", info_type)
        return ToolResult.success_result(
            tool_name, content=f"System {info_type} info"
        )

    async def _execute_command(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `execute_command` requests (sandboxed)."""
        command = args["command"]
        logger.info("execute_command: %s", command)
        # Would pass to sandbox executor
        return ToolResult.success_result(
            tool_name, content="Command executed (sandboxed)"
        )

    async def _remember_fact(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `remember_fact` requests."""
        logger.info("remember_fact: %s", args["key"])
        # Would call memory.vector_store.store()
        return ToolResult.success_result(tool_name, content="Fact remembered")

    async def _recall_fact(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `recall_fact` requests."""
        key = args.get("key", args.get("semantic_query"))
        logger.info("recall_fact: %s", key)
        # Would call memory.vector_store.query()
        return ToolResult.success_result(tool_name, content="[recalled fact]")

    async def _open_url(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """Handle `open_url` requests."""
        logger.info("open_url: %s", args["url"])
        return ToolResult.success_result(tool_name, content="Opened URL")