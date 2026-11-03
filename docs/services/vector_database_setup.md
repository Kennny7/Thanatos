# Vector Database Setup & Hybrid Memory Guide

This guide explains how to set up, configure, and connect a Vector Database to Thanatos for persistent, semantic memory recall.

---

## 1. Overview of Memory Architecture

Thanatos uses a **Hybrid Memory System** combining two tiers:
1. **Dynamic Fact Store**: Key-value JSON/SQLite store holding user preferences, personality traits, and profile entities dynamically extracted from conversations.
2. **Semantic Vector Store**: An embedded or remote vector database storing conversation history snippets, document embeddings, and project context with semantic similarity search.

```
       [User Message]
              │
      ┌───────▼───────┐
      │ Memory Service│
      └───┬───────┬───┘
          │       │
┌─────────▼─┐   ┌─▼──────────────────┐
│ Fact Store│   │ Vector DB          │
│ (Profile) │   │ (ChromaDB/LanceDB) │
└───────────┘   └────────────────────┘
```

---

## 2. Option A: ChromaDB (Default & Recommended)

Thanatos includes built-in support for ChromaDB in both **embedded (in-process)** and **client-server (Docker)** modes.

### A.1 Embedded Mode (Zero-Config, Runs Locally)
Embedded mode is enabled by default. Vectors and metadata are stored directly in your local directory without needing Docker or extra services.

1. Ensure the Python package is installed:
   ```bash
   pip install chromadb
   ```
2. In your `.env` file, configure the persist directory:
   ```env
   MEMORY_PERSIST_DIR=./memory_store
   MEMORY_COLLECTION=thanatos_memories
   ```
3. Thanatos will automatically create the `./memory_store` directory and initialize SQLite + Parquet vector indices on first run.

### A.2 Client-Server Mode (via Docker)
For multi-process scaling or sharing vectors across services:

1. Launch ChromaDB with Docker:
   ```bash
   docker run -d -p 8001:8000 --name thanatos-chroma -v thanatos_chroma_data:/chroma/chroma chromadb/chroma:latest
   ```
2. Configure Thanatos in `.env`:
   ```env
   CHROMA_SERVER_HOST=localhost
   CHROMA_SERVER_HTTP_PORT=8001
   MEMORY_COLLECTION=thanatos_memories
   ```

---

## 3. Option B: Qdrant (High-Performance Alternative)

If you prefer Qdrant for enterprise-grade vector search:

1. Launch Qdrant using Docker:
   ```bash
   docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant
   ```
2. Install the client:
   ```bash
   pip install qdrant-client
   ```
3. In `.env`:
   ```env
   VECTOR_STORE_BACKEND=qdrant
   QDRANT_URL=http://localhost:6333
   ```

---

## 4. Embedding Providers

Thanatos supports multiple embedding models:

### 4.1 Local Ollama Embeddings (Free, 100% Offline)
Pull an embedding model in Ollama:
```bash
ollama pull nomic-embed-text
# or
ollama pull bge-m3
```
In `.env`:
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_URL=http://localhost:11434
```

### 4.2 Fast In-Process HuggingFace Embeddings
```bash
pip install sentence-transformers
```
In `.env`:
```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 4.3 Deterministic Fallback
If neither ChromaDB nor an embedding model is installed, Thanatos automatically uses its built-in normalized feature hash vectorizer with cosine similarity, ensuring zero crashes even in minimal environments.

---

## 5. How Thanatos Uses Memory

1. **Auto-Extraction**: During dialogue, the memory service detects personal details (names, likes, tech stacks, ongoing goals) and updates `UserProfile`.
2. **Context Injection**: Before any LLM prompt is executed, `MemoryManager.get_relevant_context(user_prompt)` performs top-k semantic search to pull relevant memories into the prompt.
3. **Session Continuity**: Memories persist across restarts in `./memory_store`, allowing your assistant to remember your preferences indefinitely.
