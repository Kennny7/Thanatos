import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from apps.api_server.main import app
from apps.api_server.core.dispatcher import register_tool
from apps.api_server.schemas.websocket_models import (
    UserMessage,
    AssistantChunk,
    ToolCallRequest,
    HeartbeatMessage,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_websocket_agent_loop(client):
    """Connect to /ws, send a user message, and check the streaming response."""
    with client.websocket_connect("/ws") as ws:
        # ---------------------------------------------------------------
        # Send a valid user message FIRST
        # ---------------------------------------------------------------
        user_msg = UserMessage(content="Hello world")
        ws.send_text(user_msg.model_dump_json())

        chunks = []

        # ---------------------------------------------------------------
        # Receive streamed responses with safeguards
        # ---------------------------------------------------------------
        max_messages = 20

        for index in range(max_messages):
            try:
                raw_text = ws.receive_text()
                data = json.loads(raw_text)

            except Exception as exc:
                pytest.fail(f"WebSocket receive failed at iteration {index}: {exc}")

            # -----------------------------------------------------------
            # Skip heartbeat messages
            # -----------------------------------------------------------
            try:
                HeartbeatMessage.model_validate(data)
                continue
            except Exception:
                pass

            # -----------------------------------------------------------
            # Validate message structure
            # -----------------------------------------------------------
            try:
                msg_type = data.get("type")

                if msg_type == "assistant_chunk":
                    validated = AssistantChunk.model_validate(data)
                    chunks.append(validated.model_dump())

                elif msg_type == "tool_call_request":
                    validated = ToolCallRequest.model_validate(data)
                    chunks.append(validated.model_dump())

                else:
                    chunks.append(data)

            except Exception as exc:
                pytest.fail(
                    f"Message validation failed.\n"
                    f"Payload: {data}\n"
                    f"Error: {exc}"
                )

            # -----------------------------------------------------------
            # Stop condition
            # -----------------------------------------------------------
            if (
                isinstance(data, dict)
                and data.get("type") == "assistant_chunk"
                and data.get("content") == "Done."
            ):
                break

        else:
            pytest.fail(
                "WebSocket stream exceeded max_messages without receiving completion.\n"
                f"Received chunks: {chunks}"
            )

        # ---------------------------------------------------------------
        # Assertions
        # ---------------------------------------------------------------
        assert len(chunks) >= 2
        assert chunks[0]["type"] == "assistant_chunk"
        assert chunks[0]["content"] == "Thinking..."

        assert any(
            c["type"] == "tool_call_request"
            for c in chunks
        )

        assert any(
            c["type"] == "assistant_chunk"
            and c["content"] == "Done."
            for c in chunks
        )


def test_speech_stt(client):
    """Test the speech-to-text mock endpoint."""
    response = client.post("/speech/stt", json={"audio_data": "test"})
    assert response.status_code == 200
    assert response.json()["text"] == "[mock transcript]"


def test_speech_tts(client):
    """Test the text-to-speech mock endpoint."""
    response = client.post("/speech/tts", json={"text": "Hello"})
    assert response.status_code == 200
    assert "audio_data" in response.json()


def test_dispatcher_registered_tool():
    """Test the dispatcher with a registered handler."""
    def dummy_handler(args: dict):
        return {"output": f"processed {args.get('query')}"}

    from apps.api_server.schemas.tool_models import ToolCall
    from apps.api_server.core.dispatcher import dispatch_tool_call, register_tool

    register_tool("dummy_tool", dummy_handler)
    tool_call = ToolCall(tool_name="dummy_tool", arguments={"query": "test"}, call_id="123")
    result = asyncio.run(dispatch_tool_call(tool_call))
    assert result.success
    assert result.result["output"] == "processed test"


def test_dispatcher_missing_tool():
    """Dispatcher returns error for unknown tool."""
    from apps.api_server.schemas.tool_models import ToolCall
    from apps.api_server.core.dispatcher import dispatch_tool_call

    tool_call = ToolCall(tool_name="nonexistent", arguments={}, call_id="456")
    result = asyncio.run(dispatch_tool_call(tool_call))
    assert not result.success
    assert "not registered" in result.error