# Memory Microservice

## Overview
The `memory` microservice provides multi-tier memory storage, vector embeddings, similarity search, and automated scaling for Retrieval-Augmented Generation (RAG).

## Architecture & Backends
- Milvus Lite / Standalone: High-speed distributed vector database.
- ChromaDB: Persistent vector store for local and medium-scale indexing.
- Auto-Scaler: Automatically monitors document counts and triggers containerized scaling when thresholds are crossed.
- User Profile: Long-term personalized context, preferences, and entity tracking.

## Key Modules
- `vector_store.py`: Unified interface switching between Milvus and ChromaDB.
- `milvus_store.py`: Direct Milvus client with automatic connection fallback.
- `auto_scaler.py`: Automated scaling threshold manager.
- `memory_manager.py` & `hybrid_memory_service.py`: Hybrid lexical and vector memory retrieval.
- `user_profile.py`: Persistent user context extraction and storage.
- `embeddings.py`: Vector embeddings generation.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run memory and vector store tests:
```bash
uv run pytest tests/unit/test_enhancements.py -k "vector or auto_scaler"
uv run pytest tests/unit/test_memory_rag.py
```
