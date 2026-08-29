# Thanatos/apps/api_server/core/agent_loop.py

import json
import logging
from typing import Any, Dict

from fastapi import WebSocket, WebSocketDisconnect

from .session_manager import SessionManager
from .dispatcher import dispatch_tool_call
from ..schemas.websocket_models import (
    UserMessage,
    AssistantChunk,
    ToolCallRequest,
    ToolResultMessage,
    ErrorMessage,
)
from ..schemas.tool_models import ToolCall, ToolResult
from services.llm_brain.coordinator import AgentCoordinator
from services.llm_brain.provider import UnifiedLLMProvider

logger = logging.getLogger(__name__)


async def run_agent_loop(websocket: WebSocket, session_manager: SessionManager) -> None:
    """
    Main WebSocket Agent Loop:
    Receives incoming user messages, executes the multi-agent coordinator,
    streams agent statuses, thoughts, and responses in real-time.
    """
    coordinator = AgentCoordinator()

    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for session %s", session_manager.session_id)
            break
        except Exception as exc:
            logger.exception("Error receiving text: %s", exc)
            break

        try:
            msg_data = json.loads(raw)
            msg_type = msg_data.get("type", "user_message")

            if msg_type == "tool_result":
                # Handle client-side tool completion
                tool_result_msg = ToolResultMessage.model_validate(msg_data)
                tool_result = ToolResult(
                    call_id=tool_result_msg.call_id,
                    success=tool_result_msg.success,
                    result=tool_result_msg.result,
                    error=tool_result_msg.error,
                )
                if session_manager.current_generator:
                    try:
                        await session_manager.current_generator.asend(tool_result)
                    except StopAsyncIteration:
                        pass
                continue

            user_msg = UserMessage.model_validate(msg_data)
            user_text = user_msg.content

        except Exception as exc:
            await websocket.send_json(ErrorMessage(detail=f"Invalid message format: {exc}").model_dump())
            continue

        session_manager.remember_user_input(user_text)
        history = session_manager.get_conversation_history()

        full_assistant_response = ""

        try:
            # Stream coordinator response & agent status updates
            async for chunk in coordinator.execute_task_stream(user_text, history):
                chunk_type = chunk.get("type")
                if chunk_type == "assistant_chunk":
                    content = chunk.get("content", "")
                    full_assistant_response += content
                    await websocket.send_json(AssistantChunk(content=content).model_dump())
                elif chunk_type == "agent_status":
                    # Send live breadcrumb update
                    await websocket.send_json(chunk)
                elif chunk_type == "thought":
                    await websocket.send_json(chunk)
                else:
                    await websocket.send_json(chunk)

            if full_assistant_response:
                session_manager.remember_assistant_output(full_assistant_response)

        except Exception as exc:
            logger.exception("Error in agent execution stream: %s", exc)
            await websocket.send_json(ErrorMessage(detail=f"Execution error: {str(exc)}").model_dump())
