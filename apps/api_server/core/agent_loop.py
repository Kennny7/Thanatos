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
from ..schemas.tool_models import ToolCall, ToolResult   # kept for completeness

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Placeholder async generator that simulates the orchestration pipeline.
# This is the stub that MUST be replaced by the real LLM logic later.
# ---------------------------------------------------------------------------
async def orchestrate_response(
    user_input: str, session_id: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stub that mimics an async orchestrator yielding JSON-serializable chunks.
    Yields 'Thinking...', a dummy tool call, then 'Done.'.
    """
    # Simulate some async work (e.g., LLM call)
    yield AssistantChunk(content="Thinking...").model_dump()

    # Simulate a tool call (dispatcher can be used later for server‑side execution)
    tool_call_request = ToolCallRequest(
        tool_name="dummy_tool",
        arguments={"query": user_input},
    )
    yield tool_call_request.model_dump()

    # In a real loop, you'd wait for client or process server-side.
    # Here we just yield a final Done.
    yield AssistantChunk(content="Done.").model_dump()


async def run_agent_loop(websocket: WebSocket, session_manager: SessionManager) -> None:
    """
    Main loop that reads user text messages from the WebSocket,
    passes them to the orchestrator, and streams back the generated chunks.
    Includes error handling for each message.
    """
    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected during receive.")
            break
        except Exception as exc:
            logger.exception("Error receiving text: %s", exc)
            break

        # Validate incoming message
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
            # Stream orchestrator chunks back to the client
            async for chunk in orchestrate_response(user_text, session_manager.session_id):
                # Optionally update session memory depending on chunk type
                if chunk.get("type") == "assistant_chunk":
                    session_manager.remember_assistant_output(chunk["content"])
                elif chunk.get("type") == "tool_call_request":
                    session_manager.remember_tool_call(
                        chunk["tool_name"], chunk.get("arguments", {})
                    )
                await websocket.send_json(chunk)

        except Exception as exc:
            logger.exception("Error during orchestration for session %s", session_manager.session_id)
            await websocket.send_json(
                ErrorMessage(detail=f"Internal error: {exc}").model_dump()
            )
            # Continue the loop, allowing the client to try again