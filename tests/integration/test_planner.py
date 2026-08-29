# Thanatos/tests/integration/test_planner.py

import pytest
from services.llm_brain.provider import UnifiedLLMProvider
from shared.settings import Settings


@pytest.mark.asyncio
async def test_planner_basic():
    """
    Test the unified planner using environment-based configuration.
    """
    settings = Settings.load()
    provider = UnifiedLLMProvider(settings=settings)

    history = [
        {"role": "user", "content": "Hello, Thanatos!"}
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
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    response = await provider.generate_response(history, tools_schema)
    assert response is not None
    assert response.action in ("respond", "tool_call")

