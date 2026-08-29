# tests/integration/test_multi_agent_coordinator.py

import pytest
from services.llm_brain.coordinator import AgentCoordinator


@pytest.mark.asyncio
async def test_coordinator_job_hunt_pipeline():
    coordinator = AgentCoordinator()
    prompt = "Search for freshers jobs in Pune and apply with tailor made resume"
    
    chunks = []
    statuses = []
    async for item in coordinator.execute_task_stream(prompt, []):
        if item.get("type") == "assistant_chunk":
            chunks.append(item.get("content", ""))
        elif item.get("type") == "agent_status":
            statuses.append(item)

    # Verify multi-agent statuses were broadcast
    agent_names = [s.get("agent") for s in statuses]
    assert "Coordinator" in agent_names
    assert "Web Crawler & Job Hunter" in agent_names
    assert "Resume Tailor Agent" in agent_names

    # Verify synthesized response content
    full_text = "".join(chunks)
    assert "Job Search Agent Found" in full_text
    assert "Tailored Resume Prepared" in full_text
    assert "Application Status" in full_text
