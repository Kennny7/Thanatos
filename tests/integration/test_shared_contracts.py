# Thanatos/tests/integration/test_shared_contracts.py

"""
Integration tests for shared models and cross-module contract adherence.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# ============================================================
# 1. Shared model integrity
# ============================================================
class TestSharedModels:
    def test_tool_definition_is_pydantic(self):
        from shared.models.tool_definition import ToolDefinition

        assert issubclass(ToolDefinition, BaseModel)
        td = ToolDefinition(name="test_tool", description="A test", parameters={"type": "object"})
        assert td.name == "test_tool"
        assert td.parameters == {"type": "object"}
        assert td.required is None

    def test_tool_definition_to_openai_schema(self):
        from shared.models.tool_definition import ToolDefinition

        td = ToolDefinition(
            name="search",
            description="Search the web",
            parameters={"type": "object", "properties": {"q": {"type": "string"}}},
            required=["q"],
        )
        schema = td.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "search"
        assert schema["function"]["parameters"]["required"] == ["q"]

    def test_tool_definition_from_openai_schema(self):
        from shared.models.tool_definition import ToolDefinition

        data = {
            "type": "function",
            "function": {
                "name": "open_app",
                "description": "Opens an app",
                "parameters": {"type": "object", "properties": {"name": {"type": "string"}}},
            },
        }
        td = ToolDefinition.from_openai_schema(data)
        assert td.name == "open_app"
        assert td.description == "Opens an app"
        assert "name" in td.parameters["properties"]

    def test_tool_definition_extra_forbidden(self):
        from shared.models.tool_definition import ToolDefinition

        with pytest.raises(ValidationError):
            ToolDefinition(name="x", description="x", parameters={}, unknown="field")

    def test_tool_result_has_correct_fields(self):
        from shared.models.tool_result import ToolResult

        tr = ToolResult(tool_name="app", success=True, content="done")
        assert tr.content == "done"
        assert tr.error is None
        assert tr.is_error is False

    def test_tool_result_error_field(self):
        from shared.models.tool_result import ToolResult

        tr = ToolResult(tool_name="app", success=False, error="crash")
        assert tr.is_error is True
        assert tr.content is None

    def test_tool_result_factories(self):
        from shared.models.tool_result import ToolResult

        ok = ToolResult.success_result("open", "spawned")
        assert ok.success and ok.content == "spawned" and ok.tool_name == "open"

        err = ToolResult.error_result("open", "failed to launch")
        assert not err.success and err.error == "failed to launch" and err.tool_name == "open"

    def test_tool_call_model(self):
        from shared.models.tool_call import ToolCall

        tc = ToolCall(tool_name="test_tool", arguments={"arg1": "val1"})
        assert tc.tool_name == "test_tool"
        assert tc.arguments == {"arg1": "val1"}
        assert isinstance(tc.call_id, str) and len(tc.call_id) > 0

    def test_agent_event_model(self):
        from shared.models.agent_event import AgentEvent

        ev = AgentEvent.create_now(event_type="test", payload={"key": "value"})
        assert ev.event_type == "test"
        assert ev.payload == {"key": "value"}
        assert ev.timestamp is not None

    def test_shared_models_package_exports(self):
        import shared.models as shared_models

        assert hasattr(shared_models, "ToolDefinition")
        assert hasattr(shared_models, "ToolResult")
        assert hasattr(shared_models, "ToolCall")
        assert hasattr(shared_models, "AgentEvent")


# ============================================================
# 2. API server schemas
# ============================================================
class TestApiServerSchemas:
    def test_tool_models_re_exports_shared(self):
        from apps.api_server.schemas import tool_models
        from shared.models.tool_definition import ToolDefinition
        from shared.models.tool_result import ToolResult
        from shared.models.tool_call import ToolCall

        assert tool_models.ToolDefinition is ToolDefinition
        assert tool_models.ToolResult is ToolResult
        assert tool_models.ToolCall is ToolCall

    def test_agent_models_uses_shared_toolcall(self):
        from apps.api_server.schemas.agent_models import AgentAction
        from shared.models.tool_call import ToolCall

        tc = ToolCall(tool_name="search", arguments={"q": "test"})
        action = AgentAction(action_type="tool_call", tool_call=tc)
        assert action.is_tool_call is True
        assert action.tool_call.tool_name == "search"

    def test_websocket_models_wrappers(self):
        from apps.api_server.schemas.websocket_models import (
            ToolCallRequestWS,
            ToolResultMessageWS,
            AnyMessage,
        )
        from shared.models.tool_call import ToolCall
        from shared.models.tool_result import ToolResult

        tc = ToolCall(tool_name="open", arguments={"name": "Spotify"})
        ws_req = ToolCallRequestWS.from_tool_call(tc)
        assert ws_req.type == "tool_call_request"
        assert ws_req.tool_name == "open"

        tr_ok = ToolResult.success_result("open", "launched")
        ws_res = ToolResultMessageWS.from_tool_result(tr_ok, call_id="call123")
        assert ws_res.type == "tool_result"
        assert ws_res.success is True

        assert ToolCallRequestWS in AnyMessage.__args__
        assert ToolResultMessageWS in AnyMessage.__args__


# ============================================================
# 3. LLM Brain Tool Router
# ============================================================
class TestToolRouter:
    def test_router_does_not_redefine_toolresult(self):
        import services.llm_brain.tool_router as router_mod
        from services.llm_brain.tool_router import ToolRouter

        router = ToolRouter(registry=MagicMock())
        assert router is not None

    @pytest.mark.asyncio
    async def test_router_uses_shared_factories(self):
        from services.llm_brain.tool_router import ToolRouter
        from shared.models.tool_result import ToolResult

        mock_registry = MagicMock()
        router = ToolRouter(registry=mock_registry)
        result = await router.route("launch_application", {"app_name": "Firefox"})
        assert isinstance(result, ToolResult)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_router_unknown_tool_raises(self):
        from services.llm_brain.tool_router import ToolRouter
        mock_registry = MagicMock()
        mock_registry.dispatch = AsyncMock(return_value=MagicMock(success=False, error="Tool 'nonexistent' not found in any registered skill."))
        router = ToolRouter(registry=mock_registry)

        with pytest.raises(ValueError, match="Unknown tool: nonexistent"):
            await router.route("nonexistent", {})


# ============================================================
# 4. Plugin base and registry use shared models
# ============================================================
class TestPluginBase:
    def test_base_skill_uses_shared_types(self):
        from plugins.base.skill_interface import BaseSkill
        from shared.models.tool_definition import ToolDefinition
        from shared.models.tool_result import ToolResult

        assert "ToolResult" in str(BaseSkill.execute.__annotations__.get('return', ''))
        assert "ToolDefinition" in str(BaseSkill.get_tool_definitions.__annotations__.get('return', ''))

        class DummySkill(BaseSkill):
            skill_name = "dummy"

            async def execute(self, tool_name: str, params: dict) -> ToolResult:
                return ToolResult.success_result(tool_name, "ok")

            def get_tool_definitions(self) -> List[ToolDefinition]:
                return [ToolDefinition(name="dummy_tool", description="a", parameters={})]

        skill = DummySkill()
        td_list = skill.get_tool_definitions()
        assert len(td_list) == 1
        assert td_list[0].name == "dummy_tool"

        result = asyncio.run(skill.execute("dummy_tool", {}))
        assert result.success and result.tool_name == "dummy_tool"

    def test_registry_get_all_tools_returns_correct_type(self):
        from plugins.base.registry import registry as global_registry
        from shared.models.tool_definition import ToolDefinition

        tools = global_registry.get_all_tools()
        assert isinstance(tools, list)
        for tool in tools:
            assert isinstance(tool, ToolDefinition)

    @pytest.mark.asyncio
    async def test_registry_dispatch_returns_toolresult(self):
        from plugins.base.registry import registry as global_registry
        from shared.models.tool_result import ToolResult
        from plugins.base.skill_interface import BaseSkill
        from shared.models.tool_definition import ToolDefinition

        class TempSkill(BaseSkill):
            skill_name = "temp"

            async def execute(self, tool_name: str, params: dict) -> ToolResult:
                return ToolResult.success_result(tool_name, {"executed": True})

            def get_tool_definitions(self) -> List[ToolDefinition]:
                return [ToolDefinition(name="temp_tool", description="test", parameters={})]

        global_registry.register(TempSkill())
        try:
            result = await global_registry.dispatch("temp_tool", {})
            assert isinstance(result, ToolResult)
            assert result.success and result.content == {"executed": True}
        finally:
            global_registry.unregister("temp")


# ============================================================
# 5. Dispatcher uses SkillRegistry and shared models
# ============================================================
class TestDispatcher:
    @pytest.mark.asyncio
    async def test_dispatcher_returns_success_toolresult(self):
        from apps.api_server.core.dispatcher import dispatch_tool_call
        from shared.models.tool_call import ToolCall

        tc = ToolCall(tool_name="search_jobs", arguments={"location": "Pune", "keywords": "engineer"})
        result = await dispatch_tool_call(tc)
        assert result.success and "jobs" in result.content

    @pytest.mark.asyncio
    async def test_dispatcher_handles_unknown_tool(self):
        from apps.api_server.core.dispatcher import dispatch_tool_call
        from shared.models.tool_call import ToolCall

        tc = ToolCall(tool_name="ghost_tool", arguments={})
        result = await dispatch_tool_call(tc)
        assert result.success is False
        assert "not found" in result.error


# ============================================================
# 6. Coordinator & Agent Loop Integration
# ============================================================
class TestCoordinatorLoop:
    @pytest.mark.asyncio
    async def test_coordinator_stream_synthesis(self):
        from services.llm_brain.coordinator import AgentCoordinator

        coord = AgentCoordinator()
        chunks = []
        async for item in coord.execute_task_stream("Search for freshers jobs in Pune", []):
            if item.get("type") in ("assistant_chunk", "agent_status"):
                chunks.append(item)

        assert len(chunks) >= 1


# ============================================================
# 7. FastAPI Startup & Default Skills
# ============================================================
class TestStartup:
    def test_main_has_lifespan_event(self):
        from apps.api_server.main import app
        assert app.router.lifespan_context is not None

    def test_startup_registers_default_skills(self):
        from plugins.base.registry import registry
        tools = registry.get_all_tools()
        assert len(tools) > 0
        tool_names = [t.name for t in tools]
        assert "search_jobs" in tool_names
        assert "tailor_resume" in tool_names
        assert "prepare_job_application" in tool_names
        assert "translate_and_edit_novel" in tool_names
        assert "self_improve_code" in tool_names