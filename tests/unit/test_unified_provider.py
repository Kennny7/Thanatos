# tests/unit/test_unified_provider.py

import pytest
from services.llm_brain.provider import UnifiedLLMProvider, LLMResponse
from shared.settings import Settings


@pytest.mark.asyncio
async def test_provider_list_models():
    settings = Settings(
        base_url="http://localhost:11434",
        api_key=None,
        model="qwen2.5:7b",
        provider="ollama",
        is_local=True,
    )
    provider = UnifiedLLMProvider(settings)
    models = await provider.list_available_models()
    assert len(models) > 0
    model_names = [m["name"] for m in models]
    assert any("7b" in name or "8b" in name or "deepseek" in name for name in model_names)


def test_thought_extraction():
    provider = UnifiedLLMProvider()
    raw = "<think>I should search for jobs in Pune first.</think>Here is the list of jobs found."
    thought, clean = provider._extract_thought(raw)
    assert thought == "I should search for jobs in Pune first."
    assert clean == "Here is the list of jobs found."


def test_embedded_tool_call_extraction():
    provider = UnifiedLLMProvider()
    raw = 'To perform this search, I will call the tool: <tool_call>{"name": "search_jobs", "arguments": {"location": "Pune", "keywords": "freshers"}}</tool_call>'
    parsed = provider._extract_embedded_tool_call(raw)
    assert parsed is not None
    assert parsed.action == "tool_call"
    assert parsed.tool_name == "search_jobs"
    assert parsed.args.get("location") == "Pune"
