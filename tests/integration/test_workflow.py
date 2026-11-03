# Thanatos/tests/integration/test_workflow.py

"""
End-to-end multi-agent workflow integration tests.
Tests the autonomous agent coordination and self-improvement loops.
"""

import pytest
from services.llm_brain.coordinator import AgentCoordinator
from plugins.base.registry import registry, init_default_skills


@pytest.fixture(autouse=True)
def setup_skills():
    init_default_skills()


@pytest.mark.asyncio
async def test_self_improvement_workflow():
    """Verify self improvement code reflection workflow."""
    coord = AgentCoordinator()
    prompt = "Analyze the codebase, run tests, and propose code improvements"

    events = []
    async for chunk in coord.execute_task_stream(prompt, []):
        events.append(chunk)

    final_chunks = [e["content"] for e in events if e.get("type") == "assistant_chunk"]
    combined_text = "".join(final_chunks)
    assert len(combined_text) > 0
