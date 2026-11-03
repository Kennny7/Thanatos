# Database Microservice

## Overview
The `database` microservice manages multi-engine data storage across relational and document backends, supporting enterprise clusters and state synchronization.

## Backends Supported
- PostgreSQL (relational state, metrics, audit references)
- MongoDB (document store, JSON-based agent memory schemas)
- SQLite / local state fallback when remote containers are offline

## Key Modules
- `db_orchestrator.py`: Multi-database connection pool manager and health checker.
- `enterprise_database_service.py`: High-level data operations, transactions, and event logging.

## Installation & Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run unit tests for database health and fallback operations:
```bash
uv run pytest tests/unit/test_enterprise_and_dag.py -k "enterprise"
```
