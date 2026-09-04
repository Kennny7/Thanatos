# **Thanatos**

### *Autonomous Multi-Agent AI Assistant Engine with Tony Stark Holographic HUD, Voice Intelligence & Hybrid Memory*

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.44+-02569B.svg?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg?style=for-the-badge)](https://ollama.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](./docker-compose.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](./LICENSE)

<br/>

[![Quick Start](#quick-start-orderly-setup-guide)](#quick-start-orderly-setup-guide)
[![Production Deployment](./docs/production_deployment.md)](./docs/production_deployment.md)
[![Vector DB Guide](./docs/vector_database_setup.md)](./docs/vector_database_setup.md)
[![Security & Network](./docs/security_and_network.md)](./docs/security_and_network.md)
[![Future Vision: Vision & CCTV](./docs/future_vision_roadmap.md)](./docs/future_vision_roadmap.md)

</div>

---

## Overview

**Thanatos** is a local-first, autonomous multi-agent personal assistant engine. Inspired by the Tony Stark / Jarvis paradigm, it rejects bland chat bubbles in favor of a **holographic command terminal**, real-time telemetry HUD panels, continuous 3D mathematical data sphere visualization, and dynamic hybrid memory.

### Core Architecture Highlights

1. **Tony Stark / Jarvis Holographic HUD Client**:
   - Built in Flutter with 4 customizable futuristic palettes: **TRON Legacy** (pitch-black with neon cyan wireframes), **Cyberpunk Amber**, **Deep Matrix**, and **Obsidian Purple**.
   - Persistent 110-node 3D Fibonacci Holographic Data Sphere with continuous harmonic rotation and audio-reactivity.
   - Chamfered (45° cut corner) tactical panels and holographic data transmission readouts instead of standard chat bubbles.
   - Command Deck input terminal with mode selector (`AUTONOMOUS`, `DEEP REASONING`, `TERMINAL CODE`).
2. **Autonomous Multi-Agent Brain**:
   - General-purpose autonomous coordinator that plans, reasons, and invokes OS automation tools.
   - Proactive self-diagnosis: when model connectivity or resources fail, it identifies the problem and guides the operator.
3. **Dynamic Ollama Engine & In-UI Model Puller**:
   - Directly detects locally installed models via Ollama API (`GET /api/tags`).
   - In-app model puller with real-time percentage progress streaming.
   - Hardware detection (CPU cores, RAM capacity, GPU VRAM) with task-aware intelligent recommendation.
4. **Self-Learning Hybrid Memory**:
   - Combines structured dynamic fact extraction with semantic vector storage (`ChromaDB`).
   - Automatically remembers operator preferences, personal details, and ongoing workflows across restarts without hardcoded values.
5. **Security & Production Hardening**:
   - Optional Bearer token authentication and WSS WebSocket security gate.
   - Caddy auto-HTTPS reverse proxy integration.
   - Tamper-evident SHA-256 Merkle audit trail for every action.

---

## Quick Start: Orderly Setup Guide

Follow these steps in order to get Thanatos running smoothly on your machine.

### Method A: One-Command Docker Stack (Recommended)

1. Ensure [Docker Desktop](https://www.docker.com/) is installed and running.
2. Clone the repository:
   ```bash
   git clone https://github.com/Kennny7/Thanatos.git
   cd Thanatos
   ```
3. Copy environment file:
   ```bash
   cp .env.example .env
   ```
4. Start the complete system stack:
   ```bash
   docker compose up --build
   ```
   *This automatically starts the Ollama engine, pulls the default `qwen2.5:7b` model, boots the ChromaDB vector database, initializes the FastAPI application gateway on port 8000, and enables the Caddy auto-TLS proxy.*

5. Launch the Flutter Holographic Client:
   ```bash
   cd apps/client_flutter
   flutter pub get
   flutter run -d windows    # Or macos / linux / chrome / android
   ```

---

### Method B: Manual Local Setup (Developer Mode)

#### 1. Start Ollama Engine & Pull Default Model
Install [Ollama](https://ollama.com/), start the daemon, and pull your preferred model:
```bash
ollama serve
# In another terminal:
ollama pull qwen2.5:7b
```

#### 2. Configure Python Virtual Environment
```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Vector Database (ChromaDB)
Thanatos automatically initializes an embedded ChromaDB store inside `./memory_store`.
No manual database setup is required. If you wish to use a remote ChromaDB or Qdrant server, see the [Vector Database Setup Guide](./docs/vector_database_setup.md).

#### 4. Launch Backend API Gateway
```bash
uvicorn apps.api_server.main:app --host 127.0.0.1 --port 8000 --reload
```
Test health endpoint:
```bash
curl http://127.0.0.1:8000/health
```

#### 5. Launch Flutter Holographic HUD Client
```bash
cd apps/client_flutter
flutter pub get
flutter run -d windows
```

---

## Master Documentation Suite

| Document | Purpose |
| :--- | :--- |
| **[Production Deployment Guide](./docs/production_deployment.md)** | Step-by-step VPS server deployment, port mappings, Caddy auto-HTTPS, and systemd service templates. |
| **[Vector Database Setup Guide](./docs/vector_database_setup.md)** | Detailed setup for embedded ChromaDB, Docker ChromaDB, Qdrant, and Ollama embedding models. |
| **[Security & Network Intelligence](./docs/security_and_network.md)** | Authentication gates, network scanning capabilities, OSINT pipelines, and defense mechanisms. |
| **[Future Vision: CCTV & Biometrics](./docs/future_vision_roadmap.md)** | Architectural blueprint for RTSP video stream ingest, YOLO object tracking, and InsightFace recognition. |
| **[System Architecture & Workflows](./docs/system_architecture_and_workflow.md)** | Technical specification of modules, schemas, and multi-agent coordination contracts. |
| **[API Specification](./docs/api_spec.md)** | Complete REST endpoint contracts and bidirectional WebSocket protocol documentation. |

---

## License

Apache License 2.0. See [`LICENSE`](./LICENSE) for full details.
