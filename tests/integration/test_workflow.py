# Thanatos/tests/integration/test_workflow.py

"""
End-to-end multi-agent workflow integration tests.
Tests the autonomous job hunting pipeline, novel agent translation, and self-improvement loops.
"""

import pytest
from services.llm_brain.coordinator import AgentCoordinator
from plugins.base.registry import registry, init_default_skills


@pytest.fixture(autouse=True)
def setup_skills():
    init_default_skills()


@pytest.mark.asyncio
async def test_job_hunting_pipeline_workflow():
    """Verify autonomous job hunter -> resume tailor -> applicator multi-agent workflow."""
    coord = AgentCoordinator()
    prompt = "Find fresher software engineer jobs in Pune and prepare tailored applications"

    events = []
    async for chunk in coord.execute_task_stream(prompt, []):
        events.append(chunk)

    # Validate agent status events were emitted
    status_types = [e.get("type") for e in events]
    assert "agent_status" in status_types
    assert "assistant_chunk" in status_types

    # Validate final completion
    final_chunks = [e["content"] for e in events if e.get("type") == "assistant_chunk"]
    combined_text = "".join(final_chunks)
    assert len(combined_text) > 0


@pytest.mark.asyncio
async def test_novel_translation_workflow():
    """Verify novel agent translation and styling workflow."""
    coord = AgentCoordinator()
    prompt = "Translate chapter 1 of web novel: The cultivator stepped onto the flying sword."

    events = []
    async for chunk in coord.execute_task_stream(prompt, []):
        events.append(chunk)

    final_chunks = [e["content"] for e in events if e.get("type") == "assistant_chunk"]
    combined_text = "".join(final_chunks)
    assert len(combined_text) > 0


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
