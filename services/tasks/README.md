# Tasks Microservice

## Overview
The `tasks` microservice executes complex multi-step workflows using Directed Acyclic Graph (DAG) engines and supervises background terminal sessions.

## Key Modules
- `dag_engine.py`: Topological DAG executor supporting sequential, parallel, and conditional execution of tasks.
- `background_terminal.py`: Manages non-blocking terminal execution pipelines and captures stdout/stderr streams.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run DAG execution tests:
```bash
uv run pytest tests/unit/test_enterprise_and_dag.py -k "dag"
```
