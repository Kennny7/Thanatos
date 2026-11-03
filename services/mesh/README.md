# Mesh Microservice

## Overview
The `mesh` microservice implements decentralized peer-to-peer compute, local area network (LAN) node discovery, and task delegation. It enables Thanatos to discover nearby worker machines, distribute subagent workloads, and manage remote execution nodes.

## Key Modules
- `node_manager.py`: Registry for local and remote compute nodes, hardware capabilities, and health status.
- `discovery.py`: Network discovery for LAN worker peers.
- `worker.py`: Worker node client for executing distributed subagent tasks.
- `remote_control.py`: Secure protocol for executing remote commands across nodes.
- `sync.py`: State synchronization between cluster master and edge workers.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run node manager unit tests:
```bash
uv run pytest tests/unit/test_enhancements.py -k "mesh_node_manager"
```
