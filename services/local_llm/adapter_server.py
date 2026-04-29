# Thanatos/services/local_llm/adapter_server.py

import json
import logging
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from shared.logging_setup import ensure_logging
from .ollama_client import chat
from .tool_parser import parse_llm_output
from .prompt_builder import build_system_prompt

# Ensure logging works even if this file is run standalone
ensure_logging()

logger = logging.getLogger(__name__)

app = FastAPI()

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    tools: List[Dict[str, Any]] = []
    temperature: float = 0.0

from fastapi import Request

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    print("\n========== INCOMING REQUEST ==========", flush=True)
    print("URL:", request.url, flush=True)
    print("Headers:", dict(request.headers), flush=True)

    try:
        body = await request.body()
        print("Body:", body.decode(), flush=True)
    except Exception as e:
        print("Failed to read body:", e, flush=True)

    print("=====================================\n", flush=True)

    response = await call_next(request)

    print("\n========== RESPONSE ==========", flush=True)
    print("Status code:", response.status_code, flush=True)
    print("=====================================\n", flush=True)

    return response

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    logger.info("Received chat completion request | model=%s", req.model)
    logger.debug(
        "Request details | messages=%d | tools=%d | temperature=%s",
        len(req.messages),
        len(req.tools),
        req.temperature
    )

    # Use centralized prompt builder (instead of inline string)
    system_prompt = {
        "role": "system",
        "content": build_system_prompt(req.tools)
    }

    logger.debug("System prompt built successfully")

    messages = [system_prompt] + req.messages

    # Call Ollama backend
    try:
        logger.info("Calling local LLM backend")
        raw = await chat(req.model, messages, req.temperature)
        logger.debug("Raw response received from LLM")
        logger.debug("RAW OLLAMA RESPONSE: %s", str(raw)[:1000])
    except Exception:
        logger.exception("LLM backend call failed")
        raise

    content = raw.get("message", {}).get("content", "")
    logger.debug("LLM content preview: %s", content[:200])

    try:
        parsed = parse_llm_output(content)
        logger.debug("Parsed LLM output successfully")
    except Exception:
        logger.warning("Parser failed, falling back to plain text response")
        parsed = {
            "action": "respond",
            "text": content
        }

    # --- NORMALIZATION LAYER (critical for small models) ---
    if not isinstance(parsed, dict):
        logger.warning("Parsed output is not a dict, forcing text response")
        parsed = {
            "action": "respond",
            "text": str(parsed)
        }

    # Handle common non-compliant outputs from small models
    if "action" not in parsed:
        logger.warning("Missing 'action' field, attempting recovery")

        # Case: {"response": "..."}
        if "response" in parsed and isinstance(parsed["response"], str):
            parsed = {
                "action": "respond",
                "text": parsed["response"]
            }

        # Case: {"text": "..."} (no action)
        elif "text" in parsed and isinstance(parsed["text"], str):
            parsed["action"] = "respond"

        # Case: fallback → treat whole content as text
        else:
            logger.warning("Unknown structure, falling back to raw content")
            parsed = {
                "action": "respond",
                "text": content
            }

    action = parsed.get("action")
    logger.info("Parsed action from LLM: %s", action)

    # Case 1: Explicit tool_call format (ideal case)
    if action == "tool_call":
        tool_name = parsed.get("tool_name")
        logger.info("Returning tool_call response | tool=%s", tool_name)
        logger.debug("Tool arguments: %s", parsed.get("args", {}))

        return {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(parsed.get("args", {}))
                        }
                    }]
                }
            }]
        }

    # Case 2: Model returned tool name directly (common with small models)
    if action not in (None, "respond", "tool_call"):
        logger.warning("Non-standard action detected, treating as tool call | action=%s", action)
        logger.debug("Tool arguments: %s", parsed.get("args", {}))

        return {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": action,
                            "arguments": json.dumps(parsed.get("args", {}))
                        }
                    }]
                }
            }]
        }

    # Case 3: Normal text response
    logger.info("Returning standard text response")
    logger.debug("Response preview: %s", parsed.get("text", "")[:200])

    return {
        "choices": [{
            "message": {
                "content": parsed.get("text", "")
            }
        }]
    }
