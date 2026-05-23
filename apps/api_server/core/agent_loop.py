# apps/api_server/core/agent_loop.py

import json
import logging
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from .session_manager import SessionManager
from .dispatcher import dispatch_tool_call, _TOOL_REGISTRY   # server-side dispatch + registry
from ..schemas.websocket_models import (
    UserMessage,
    AssistantChunk,
    ToolCallRequest,
    ToolResultMessage,
    ErrorMessage,
)
from ..schemas.tool_models import ToolCall, ToolResult

# Import our planner and the tool schema loader
from services.llm_brain.deepseek_planner import DeepSeekPlanner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load tool schema once at module level (or inject via dependency)
# ---------------------------------------------------------------------------
def load_tool_schema() -> list[dict]:
    schema_path = (
        Path(__file__).resolve().parents[3]
        / "services"
        / "llm_brain"
        / "prompt_templates"
        / "tool_schema.json"
    )
    with open(schema_path, "r") as f:
        return json.load(f)


TOOLS_SCHEMA = load_tool_schema()


# ---------------------------------------------------------------------------
# Helper: decide whether a tool should be executed server‑side
# ---------------------------------------------------------------------------
def is_server_side_tool(tool_name: str) -> bool:
    """Return True if the tool is registered in the dispatcher's registry."""
    return tool_name in _TOOL_REGISTRY


# ---------------------------------------------------------------------------
# Async generator that uses the planner to decide next step
# ---------------------------------------------------------------------------
async def orchestrate_with_planner(
    history: list[dict],
    session_id: str,
    planner: DeepSeekPlanner,
    tools_schema: list[dict],
) -> AsyncGenerator[Dict[str, Any], Optional[ToolResult]]:
    """
    Core orchestration that talks to the LLM, yields chunks, and
    optionally accepts a ToolResult to continue the conversation.

    Yields:
        AssistantChunk, ToolCallRequest, or ErrorMessage dicts.

    The generator can receive a ToolResult via ``.asend(result)`` to
    continue the conversation after a tool call that was sent to the client.
    """
    while True:
        # Plan the next action given the conversation history
        try:
            decision = await planner.plan(history, tools_schema)
        except Exception as exc:
            logger.error("Planner failed: %s", exc)
            yield ErrorMessage(detail="Planner error, please try again.").model_dump()
            return

        if decision["action"] == "respond":
            # Send the final text response
            yield AssistantChunk(content=decision["text"]).model_dump()
            # After a plain response, the conversation is done (for this turn)
            return

        # Otherwise it's a tool call – create the canonical ToolCall object
        tool_name = decision["tool_name"]
        tool_args = decision["args"]
        call_id = str(uuid.uuid4())

        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=tool_args,
            call_id=call_id,
        )

        if is_server_side_tool(tool_name):
            # Execute server‑side and immediately feed the result back to the LLM
            logger.info("Dispatching server‑side tool %s (call_id=%s)", tool_name, call_id)
            tool_result = await dispatch_tool_call(tool_call)

            # Append the assistant's tool_call message to history
            history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(tool_args),
                        },
                    }
                ],
            })
            # Append the tool result to history
            history.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": json.dumps(tool_result.model_dump()),
            })

            # Yield a chunk indicating the tool was executed (optional UI feedback)
            yield AssistantChunk(
                content=f"Executed tool '{tool_name}'."
            ).model_dump()

            # Loop back to let the planner process the result
            continue

        # Client‑side path: send a ToolCallRequest and wait for the result
        tool_call_req = ToolCallRequest(
            tool_name=tool_name,
            arguments=tool_args,
            call_id=call_id,
        )
        yield tool_call_req.model_dump()

        # Wait for the tool result from the client
        tool_result: Optional[ToolResult] = yield  # receive via .asend()
        if tool_result is None:
            # Client may have closed or timed out – abort
            logger.warning("Tool result not received for call_id %s, aborting.", call_id)
            yield ErrorMessage(
                detail="Tool execution timed out or client disconnected."
            ).model_dump()
            return

        # Append the assistant tool_call and the client's ToolResult to history
        history.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_args),
                    },
                }
            ],
        })
        history.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps(tool_result.model_dump()),
        })
        # Loop back to let the planner process the result


# ---------------------------------------------------------------------------
# Main agent loop
# ---------------------------------------------------------------------------
async def run_agent_loop(
    websocket: WebSocket, session_manager: SessionManager
) -> None:
    planner = DeepSeekPlanner()  # will read DEEPSEEK_API_KEY from env

    while True:
        try:
            raw = await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected.")
            break
        except Exception as exc:
            logger.exception("Error receiving text: %s", exc)
            break

        # Try to parse as different message types
        try:
            msg_data = json.loads(raw)
            msg_type = msg_data.get("type")

            # Check if it's a ToolResult first (client sends after executing a tool)
            if msg_type == "tool_result":
                tool_result_msg = ToolResultMessage.model_validate(msg_data)
                # Convert the wire model to the internal ToolResult
                tool_result = ToolResult(
                    call_id=tool_result_msg.call_id,
                    success=tool_result_msg.success,
                    result=tool_result_msg.result,
                    error=tool_result_msg.error,
                )
                # Resume the current orchestration generator
                if hasattr(session_manager, "current_generator"):
                    try:
                        await session_manager.current_generator.asend(tool_result)
                    except StopAsyncIteration:
                        pass
                else:
                    await websocket.send_json(
                        ErrorMessage(
                            detail="No active orchestration to receive tool result."
                        ).model_dump()
                    )
                continue

            # Otherwise treat as a new UserMessage
            user_msg = UserMessage.model_validate(msg_data)
        except Exception as exc:
            await websocket.send_json(
                ErrorMessage(detail=f"Invalid message format: {exc}").model_dump()
            )
            continue

        user_text = user_msg.content
        session_manager.remember_user_input(user_text)

        # Build initial history from session
        history = session_manager.get_conversation_history()  # TODO: implement
        # Add the new user message
        history.append({"role": "user", "content": user_text})

        # Create an orchestration generator for this turn
        gen = orchestrate_with_planner(
            history, session_manager.session_id, planner, TOOLS_SCHEMA
        )
        session_manager.current_generator = gen  # store for tool result

        try:
            # Prime the generator to get the first yield
            first_chunk = await gen.__anext__()
            # Loop through all yields (including tool calls that may require async send)
            while True:
                # Update memory based on chunk type
                if first_chunk.get("type") == "assistant_chunk":
                    session_manager.remember_assistant_output(
                        first_chunk["content"]
                    )
                elif first_chunk.get("type") == "tool_call_request":
                    session_manager.remember_tool_call(
                        first_chunk["tool_name"],
                        first_chunk.get("arguments", {}),
                    )
                await websocket.send_json(first_chunk)

                # If the chunk is a tool call, we must stop and wait for ToolResult from client
                if first_chunk.get("type") == "tool_call_request":
                    # Yield control back to the event loop; next chunk will come via .asend()
                    break

                # Otherwise get next chunk (plain text continues)
                first_chunk = await gen.__anext__()

        except StopAsyncIteration:
            # Orchestration finished normally
            pass
        except Exception as exc:
            logger.exception(
                "Error during orchestration for session %s",
                session_manager.session_id,
            )
            await websocket.send_json(
                ErrorMessage(detail=f"Internal error: {exc}").model_dump()
            )
        finally:
            session_manager.current_generator = None