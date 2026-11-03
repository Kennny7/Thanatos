# Agents Microservice

## Overview
The `agents` microservice provides autonomous persona-driven AI agent orchestration, real-time reinforcement learning feedback, and topic routing. It coordinates multiple specialized agent personas who collaborate, critique, and accomplish complex objectives.

## Personas & Responsibilities
- Butler Agent: Executive orchestration, high-level user interaction, and intent summarization.
- Tech Prodigy Agent: Technical problem solving, system programming, and low-level execution logic.
- Project Manager Agent: Task planning, dependency tracking, and execution order management.
- Secretary Agent: Note-taking, contextual memory persistence, and record-keeping.
- Site Engineer Agent: DevOps, hardware/network operations, and service monitoring.

## Key Modules
- `agent_bus.py`: Event bus distributing signals, tool outputs, and status events across agents.
- `agent_personas.py` & `agent_roster.py`: Definition and active roster of agents.
- `topic_router.py`: Classifies input and directs requests to the best-suited agent or team of agents.
- `dynamic_prompt_builder.py`: Context-aware dynamic system prompt construction.
- `feedback_engine.py` & `trait_engine.py`: Dynamic reinforcement learning trait adjustment based on user and task outcomes.

## Installation & Standalone Testing
Ensure dependencies are installed using `uv`:
```bash
uv sync
```

To run unit tests for the agent microservice:
```bash
uv run pytest tests/unit/test_enterprise_and_dag.py
```

To test prompt building or persona initialization interactively:
```bash
uv run python -c "from services.agents.agent_roster import AgentRoster; r = AgentRoster(); print(r.list_agent_names())"
```
