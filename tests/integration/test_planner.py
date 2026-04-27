import pytest
from shared.deepseek_planner import DeepSeekPlanner

@pytest.mark.asyncio
async def test_planner_basic():
    planner = DeepSeekPlanner()

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

    result = await planner.plan(history, tools_schema)

    assert result is not None
    assert isinstance(result, (dict, list, str))  # adjust based on actual output