import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import WebSocket, WebSocketDisconnect

from .session_manager import SessionManager
from .dispatcher import dispatch_tool_call
from ..schemas.websocket_models import (
    UserMessage,
    AssistantChunk,
    ToolCallRequest,
    ErrorMessage,
)
from ..schemas.tool_models import ToolCall, ToolResult

logger = logging.getLogger(__name__)


async def orchestrate_response(
    user_input: str, session_id: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stub orchestrator that yields 'Thinking...' and a dummy tool call.
    Replace with real LLM integration.
    """
    # Assistant thinks
    yield AssistantChunk(content="Thinking...").model_dump()

    # Simulate a tool call
    tool_call_request = ToolCallRequest(
        tool_name="dummy_tool",
        arguments={"query": user_input},
    )
    yield tool_call_request.model_dump()

    # In a real loop, you'd wait for client or process server-side.
    # Here we simulate executing it directly via dispatcher (server-side tools).
    # But for client-side tools, you'd wait for a tool_result message.
    # For demonstration, we just yield a final Done.
    yield AssistantChunk(content="Done.").model_dump()


async def run_agent_loop(websocket: WebSocket, session_manager: SessionManager) -> None:
    """Main loop: receive user text, run orchestrator, stream back chunks."""
    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("Client disconnected")
            break
        except Exception as exc:
            logger.exception("Receive error")
            break

        # Validate
        try:
            user_msg = UserMessage.model_validate_json(raw)
        except Exception as exc:
            await websocket.send_json(
                ErrorMessage(detail=f"Invalid message format: {exc}").model_dump()
            )
            continue

        user_text = user_msg.content
        session_manager.remember_user_input(user_text)

        try:
            async for chunk in orchestrate_response(user_text, session_manager.session_id):
                # Optionally store in memory
                if chunk.get("type") == "assistant_chunk":
                    session_manager.remember_assistant_output(chunk["content"])
                elif chunk.get("type") == "tool_call_request":
                    session_manager.remember_tool_call(
                        chunk["tool_name"], chunk.get("arguments", {})
                    )

                await websocket.send_json(chunk)

        except Exception as exc:
            logger.exception("Orchestration failed")
            await websocket.send_json(
                ErrorMessage(detail=f"Internal error: {exc}").model_dump()
            )