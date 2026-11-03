# Thanatos/tests/integration/test_planner.py

from unittest.mock import AsyncMock, patch
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

    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I assist you today?"
                }
            }
        ]
    }

    with patch.object(provider, "_call_openai_compatible", new=AsyncMock(return_value=mock_response)):
        response = await provider.generate_response(history, tools_schema)
        assert response is not None
        assert "choices" in response or getattr(response, "action", None) in ("respond", "tool_call")
