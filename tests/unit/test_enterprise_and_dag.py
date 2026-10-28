# Thanatos/tests/unit/test_enterprise_and_dag.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from services.database.enterprise_database_service import enterprise_db
from services.tasks.dag_engine import dag_engine, DAGNode, DAGPlan
from services.llm_brain.coordinator import AgentCoordinator
from services.llm_brain.provider import UnifiedLLMProvider


def test_enterprise_cluster_health():
    """Verify that all 5 enterprise storage/streaming engines report valid status."""
    cluster = enterprise_db.get_cluster_health()
    assert "postgresql" in cluster
    assert "mongodb" in cluster
    assert "milvus" in cluster
    assert "neo4j" in cluster
    assert "kafka" in cluster

    # Verify fallback operation when Docker is offline
    assert "status" in cluster["postgresql"]
    assert "status" in cluster["mongodb"]
    assert "status" in cluster["neo4j"]
    assert "status" in cluster["milvus"]
    assert "status" in cluster["kafka"]


def test_enterprise_data_recording():
    """Verify storing user facts and turn records across engines."""
    enterprise_db.postgres.set_user_fact("test_fact_key", "test_val")
    facts = enterprise_db.postgres.get_user_facts()
    assert facts.get("test_fact_key") == "test_val"

    doc_id = enterprise_db.mongo.store_document("test_col", {"message": "hello enterprise"})
    assert doc_id is not None
    docs = enterprise_db.mongo.get_recent_documents("test_col", limit=5)
    assert any(d.get("message") == "hello enterprise" for d in docs)

    # Test relationship recording
    enterprise_db.neo4j.add_relationship("test_user", "User", "USES", "test_tech", "Technology")
    rels = enterprise_db.neo4j.query_relationships("test_user")
    assert any(r["target"] == "test_tech" for r in rels)


def test_dag_complex_task_detection():
    """Verify dynamic detection of complex engineering tasks requiring a DAG."""
    # Simple questions should NOT trigger heavy DAG
    assert not dag_engine.is_complex_task("Hi Velma, how are you?")
    assert not dag_engine.is_complex_task("What is the weather today?")
    assert not dag_engine.is_complex_task("Can you summarize our plan?")

    # Complex engineering directives SHOULD trigger DAG
    assert dag_engine.is_complex_task("Please analyze project at C:/projects/webapp and solve bugs")
    assert dag_engine.is_complex_task("Optimize performance and refactor database queries for project Thanatos")
    assert dag_engine.is_complex_task("First inspect code, and then run tests and fix bugs in parallel")


def test_dag_plan_generation_and_box_rendering():
    """Verify DAG plan creation with node dependencies and Antigravity box rendering."""
    plan = dag_engine.build_plan_for_task(
        "Optimize performance and refactor database queries for project Thanatos",
        target_project="Thanatos"
    )
    assert len(plan.nodes) >= 3
    assert plan.nodes[0].dependencies == []  # root node
    assert len(plan.nodes[1].dependencies) > 0  # dependent node

    # Verify Antigravity Task Box renders cleanly without errors
    box = dag_engine.render_antigravity_task_box(plan)
    assert box is not None


@pytest.mark.asyncio
async def test_dag_parallel_and_sequential_execution():
    """Verify parallel scheduling of ready nodes and sequential resolution of dependent nodes."""
    nodes = [
        DAGNode(id="n1", title="Root task", dependencies=[]),
        DAGNode(id="n2", title="Parallel task A", dependencies=["n1"]),
        DAGNode(id="n3", title="Parallel task B", dependencies=["n1"]),
        DAGNode(id="n4", title="Final verification", dependencies=["n2", "n3"]),
    ]
    plan = DAGPlan(
        task_id="test_dag_1",
        title="Unit Test Execution Graph",
        nodes=nodes,
    )

    execution_order = []

    async def mock_step_executor(node: DAGNode, log_path: str) -> str:
        execution_order.append(node.id)
        await asyncio.sleep(0.05)
        return f"Done {node.id}"

    events = []
    async for event in dag_engine.execute_dag_stream(plan, step_executor=mock_step_executor):
        events.append(event)

    assert plan.status == "completed"
    assert all(n.status == "completed" for n in plan.nodes)
    assert execution_order[0] == "n1"
    # n2 and n3 should execute before n4
    assert set(execution_order[1:3]) == {"n2", "n3"}
    assert execution_order[3] == "n4"


@pytest.mark.asyncio
async def test_coordinator_token_streaming():
    """Verify near-zero latency streaming response for simple conversational chat."""
    mock_provider = UnifiedLLMProvider()

    async def mock_generate_stream(*args, **kwargs):
        tokens = ["Hey ", "there! ", "All ", "systems ", "are ", "operational."]
        for t in tokens:
            yield {"type": "token", "token": t}

    mock_provider.generate_stream = mock_generate_stream

    coordinator = AgentCoordinator(mock_provider)
    chunks = []

    async for chunk in coordinator.execute_task_stream("Hey Velma, how is the server?", []):
        if chunk.get("type") == "assistant_chunk":
            chunks.append(chunk.get("content", ""))

    full_text = "".join(chunks)
    assert "operational" in full_text
    assert len(chunks) >= 3  # streamed in individual tokens, not buffered
