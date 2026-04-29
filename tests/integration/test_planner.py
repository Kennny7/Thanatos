# Thanatos\tests\integration\test_planner.py

import time
import pytest
import asyncio
from shared.settings import Settings
from shared.deepseek_planner import DeepSeekPlanner

@pytest.mark.asyncio
async def test_planner_basic():
    """
    Test the planner using environment‑based configuration.
    For Docker Ollama, no extra env needed (automatic detection).
    For DeepSeek, set DEEPSEEK_API_KEY (LLM_BASE_URL is optional).
    """
    start_time = time.time()
    print("[TEST] Starting test_planner_basic", flush=True)

    settings = Settings.load()
    print("[TEST] Settings loaded", flush=True)

    planner = DeepSeekPlanner(settings=settings)
    print("[TEST] Planner initialized", flush=True)

    history = [
        {"role": "user", "content": "What's the weather in Paris?"}
    ]

    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ]



    async def heartbeat():
        while True:
            print("[TEST] Still running...", flush=True)
            await asyncio.sleep(5)

    print("[TEST] Calling planner.plan()", flush=True)

    hb_task = asyncio.create_task(heartbeat())

    try:
        result = await asyncio.wait_for(
            planner.plan(history, tools_schema),
            timeout=300
        )
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass

    print(f"[TEST] planner.plan() returned in {time.time() - start_time:.2f}s", flush=True)
    print(f"[TEST] Result: {result}", flush=True)

    assert result is not None
    assert isinstance(result, dict)
    assert "action" in result
