import asyncio
import json
import pytest
from fastapi.testclient import TestClient

from apps.api_server.main import app
from apps.api_server.core.dispatcher import register_tool, dispatch_tool_call
from apps.api_server.schemas.websocket_models import (
    UserMessage,
    AssistantChunk,
    HeartbeatMessage,
)
from apps.api_server.schemas.tool_models import ToolCall


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_config_endpoint(client):
    """Test config endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "provider" in data


def test_speech_voice_status(client):
    """Test voice status endpoint."""
    response = client.get("/speech/voice-status")
    assert response.status_code == 200
    assert "is_enrolled" in response.json()


@pytest.mark.asyncio
async def test_websocket_agent_loop(client):
    """Connect to /ws, send a user message, and check the streaming response."""
    with client.websocket_connect("/ws") as ws:
        user_msg = UserMessage(content="Hello")
        ws.send_text(user_msg.model_dump_json())

        received = []
        for _ in range(10):
            try:
                raw_text = ws.receive_text()
                data = json.loads(raw_text)
                msg_type = data.get("type")
                if msg_type in ("assistant_chunk", "agent_status", "thought"):
                    received.append(data)
                if msg_type == "assistant_chunk":
                    break
            except Exception:
                break

        assert len(received) >= 1


def test_dispatcher_registered_tool():
    """Test the dispatcher with a registered handler."""
    def dummy_handler(args: dict):
        return {"output": f"processed {args.get('query')}"}

    register_tool("dummy_tool", dummy_handler)
    tool_call = ToolCall(tool_name="dummy_tool", arguments={"query": "test"}, call_id="123")
    result = asyncio.run(dispatch_tool_call(tool_call))
    assert result.success
    assert result.result["output"] == "processed test"


def test_dispatcher_skill_tool():
    """Test dispatcher executing an auto-registered skill tool."""
    tool_call = ToolCall(tool_name="search_jobs", arguments={"location": "Pune", "keywords": "engineer"}, call_id="789")
    result = asyncio.run(dispatch_tool_call(tool_call))
    assert result.success
    assert "jobs" in result.result