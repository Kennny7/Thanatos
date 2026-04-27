from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from .ollama_client import chat
from .tool_parser import parse_llm_output

app = FastAPI()

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    tools: List[Dict[str, Any]] = []
    temperature: float = 0.0


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    # Inject tool instructions into system prompt
    system_prompt = {
        "role": "system",
        "content": f"""
You are an AI planner.

You MUST respond in JSON format:

If calling tool:
{{"action":"tool_call","tool_name":"<name>","args":{{...}}}}

If responding:
{{"action":"respond","text":"..."}}

Available tools:
{req.tools}
"""
    }

    messages = [system_prompt] + req.messages

    raw = await chat(req.model, messages, req.temperature)

    content = raw["message"]["content"]

    parsed = parse_llm_output(content)

    # Convert to OpenAI format
    if parsed["action"] == "tool_call":
        return {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": parsed["tool_name"],
                            "arguments": json.dumps(parsed["args"])
                        }
                    }]
                }
            }]
        }

    return {
        "choices": [{
            "message": {
                "content": parsed.get("text", "")
            }
        }]
    }