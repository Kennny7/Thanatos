# **Thanatos**

### *Autonomous Multi-Agent AI Assistant Engine with Voice Intelligence & RAG*

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B.svg?style=for-the-badge&logo=flutter&logoColor=white)](https://flutter.dev)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black.svg?style=for-the-badge)](https://ollama.com)
[![Tests](https://img.shields.io/badge/Tests-48%20Passed-brightgreen.svg?style=for-the-badge)](./tests)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg?style=for-the-badge)](./LICENSE)

<br/>

[![Documentation Hub](https://img.shields.io/badge/Docs-Documentation%20Hub-007ACC?style=for-the-badge)](#documentation-hub)
[![Quick Start](https://img.shields.io/badge/Guide-Quick%20Start-2EA44F?style=for-the-badge)](#quick-start)
[![Architecture](https://img.shields.io/badge/Spec-Architecture-6F42C1?style=for-the-badge)](#system-architecture)
[![Plugins & Skills](https://img.shields.io/badge/Ecosystem-Plugins%20%26%20Skills-F39C12?style=for-the-badge)](#sub-agent-skills--plugin-ecosystem)
[![Contributing](https://img.shields.io/badge/Community-Contributing-E74C3C?style=for-the-badge)](#contributing)

</div>

---

## Overview

**Thanatos** is an autonomous, local-first multi-agent AI assistant engine designed for cross-platform automation and intelligent personal assistance. Combining local LLM execution via Ollama with multi-agent orchestration, Retrieval-Augmented Generation (RAG), and advanced speech intelligence, Thanatos runs with high privacy, low latency, and zero cloud dependency.

### Core Capabilities

1. **Distributed LAN Mesh & Multi-Device Compute Clustering**:
   - Turn secondary laptops and Android devices (via Termux or directly through the Thanatos Flutter client) into compute and inference worker nodes over Wi-Fi.
   - **Zero-Config UDP Discovery**: Automatic subnet beacon scanning on UDP port 47470 with persistent node caching and dynamic Wi-Fi gateway auto-detection.
   - **Remote Node Control & Model Offloading**: Remotely dispatch shell commands, pull models on remote Ollama instances, and trigger manifest-based delta file sync across the LAN.
2. **Enterprise Multi-Engine Database Architecture**:
   - Production-grade hybrid persistence stack: **PostgreSQL 16** (relational & career deduplication), **MongoDB 7.0** (unstructured transcripts & dossiers), **Milvus 2.4.13 Standalone** (high-dimensional vector search), and **Neo4j 5.20** (knowledge graph & social relationships).
   - Automated Docker supervisor ([`services/database/db_orchestrator.py`](./services/database/db_orchestrator.py)) provides on-demand container startup, health checks, RAM guardrails, and backup recovery.
3. **Specialized Multi-Agent Personas & Isolated Memory**:
   - Distinct agent personas with segregated memory partitions:
     - **Butler Agent**: Tracks character dossiers, evaluates interpersonal social dynamics, and evaluates long-term strategic alignment.
     - **Secretary & Wingman Agent**: Daily agenda management, active workout/jogging routines, and personalized taste preference tracking.
4. **Hands-Free Call Mode & Cross-Platform Tactical UI**:
   - High-contrast minimal black terminal mode and hands-free **Call Mode** across Windows and Android.
   - Real-time acoustic frequency spectrum visualizer reacting directly to microphone input decibels rather than synthetic waveforms.
5. **Targeted SLM & Model Selection Agent**:
   - Assign specialized, lightweight Small Language Models ($\le 8\text{--}9\text{B}$) like `qwen2.5:3b/7b`, `phi3:mini`, `deepseek-r1:7b`, or `llama3.2:3b` tailored to specific agent tasks.
   - Automatically detects missing models and triggers automated Ollama pulls on local or secondary mesh nodes.
6. **External Action Execution & Autonomous Tool Creation**:
   - Real-time command-line dispatch, desktop automation, port/service auditing, and live web scraping with safety gates and SHA-256 Merkle audit logs.
   - Dynamic tool synthesis allowing agents to generate and execute custom tools on the fly.

---

## Documentation Hub

Explore the comprehensive technical documentation suite in the [`docs/`](./docs) directory:

| Document | Description | Action |
| :--- | :--- | :---: |
| **Getting Started Guide** | Step-by-step setup guide for Python backend, Ollama models, and Flutter client. | [![Read Guide](https://img.shields.io/badge/Open-Guide-2EA44F?style=flat-square)](./docs/getting_started.md) |
| **Dependency Management** | How `uv` lock files, `~=` pins, and `pubspec.lock` guarantee reproducible installs across Python and Flutter. | [![Read Guide](https://img.shields.io/badge/Open-Guide-F39C12?style=flat-square)](./docs/dependency_management.md) |
| **Production Deployment Guide** | Step-by-step VPS server deployment, port mappings, Caddy auto-HTTPS, and systemd service templates. | [![Read Deployment Guide](https://img.shields.io/badge/Open-Deployment%20Guide-2EA44F?style=flat-square)](./docs/production_deployment.md) |
| **System Architecture** | Component breakdown, supervisor-worker topology, and layer interactions. | [![Read Spec](https://img.shields.io/badge/Open-Spec-6F42C1?style=flat-square)](./docs/architecture.md) |
| **Master Architecture & Workflows** | Authoritative 7-module blueprint with sequence diagrams and execution contracts. | [![Read Blueprint](https://img.shields.io/badge/Open-Blueprint-007ACC?style=flat-square)](./docs/system_architecture_and_workflow.md) |
| **API Specification** | Full REST endpoints and WebSocket streaming protocol (`/ws`) reference. | [![Read API Spec](https://img.shields.io/badge/Open-API%20Spec-009688?style=flat-square)](./docs/api_spec.md) |
| **Plugin Development Guide** | Tutorial on creating, registering, and testing custom sub-agent skills. | [![Read Guide](https://img.shields.io/badge/Open-Dev%20Guide-F39C12?style=flat-square)](./docs/plugin_dev_guide.md) |
| **Database Infrastructure** | Enterprise 4-engine database stack (PostgreSQL, MongoDB, Milvus, Neo4j) with Docker supervisor & recovery. | [![Read DB Spec](https://img.shields.io/badge/Open-DB%20Spec-009688?style=flat-square)](./docs/database_infrastructure.md) |
| **Speech Intelligence & AEC** | Voice pipeline, acoustic echo cancellation, and speaker diarization details. | [![Read Voice Spec](https://img.shields.io/badge/Open-Voice%20Spec-3776AB?style=flat-square)](./docs/speech_intelligence.md) |
| **Voice Mode & Speaker Verification** | Separate Voice Mode, ECG frequency line, VAD, multi-speaker authorization, and optional camera lip-sync. | [![Read Voice Mode Guide](https://img.shields.io/badge/Open-Voice%20Mode-00E5FF?style=flat-square)](./docs/voice_mode_speaker_verification.md) |
| **Memory & RAG Subsystem** | ChromaDB & Milvus vector store, semantic embeddings, and career profile matching. | [![Read RAG Guide](https://img.shields.io/badge/Open-RAG%20Guide-4B8BBE?style=flat-square)](./docs/memory_and_rag.md) |
| **Vector Database Setup Guide** | Detailed setup for embedded ChromaDB, Docker ChromaDB, Qdrant, and Ollama embedding models. | [![Read Setup Guide](https://img.shields.io/badge/Open-Vector%20DB%20Guide-4B8BBE?style=flat-square)](./docs/vector_database_setup.md) |
| **Security & Isolation Model** | Sandbox boundaries, OS safety confirmation gates, and Merkle audit logs. | [![Read Model](https://img.shields.io/badge/Open-Security%20Model-E74C3C?style=flat-square)](./docs/security_model.md) |
| **Security & Network Intelligence** | Authentication gates, network scanning capabilities, OSINT pipelines, and defence mechanisms. | [![Read Security Guide](https://img.shields.io/badge/Open-Network%20Security-E74C3C?style=flat-square)](./docs/security_and_network.md) |
| **Model Context Protocol (MCP)** | Exposing Thanatos OS tools to Claude Desktop, Cursor IDE, and MCP hosts. | [![Read MCP Guide](https://img.shields.io/badge/Open-MCP%20Guide-555555?style=flat-square)](./docs/mcp_server.md) |
| **Future Vision: CCTV & Biometrics** | Architectural blueprint for RTSP video stream ingest, YOLO object tracking, and InsightFace recognition. | [![Read Roadmap](https://img.shields.io/badge/Open-Future%20Roadmap-007ACC?style=flat-square)](./docs/future_vision_roadmap.md) |
| **Contributor Guide** | Coding conventions, PR guidelines, and running the test suite. | [![Read Guide](https://img.shields.io/badge/Open-Contributing-24292E?style=flat-square)](./docs/contributing.md) |

---

## System Architecture

```mermaid
flowchart TB

    subgraph ClientLayer ["1. Holographic HUD Client (Cross-Platform Flutter)"]
        FlutterApp["Flutter App (Desktop / Mobile / Web)"]
        ChatUI["Tactical Chat UI & Deep Thinking Trace"]
        HUDSphere["110-Node 3D Holographic Data Sphere<br/>Audio-Reactive & Harmonic Rotation"]
        CommandDeck["Command Deck Input Terminal"]
        ModeSelector["Operation Modes<br/>AUTONOMOUS | DEEP REASONING | TERMINAL CODE"]
        VoiceUI["Voice Visualizer<br/>AEC & Speaker Diarization"]
        ThemeEngine["Futuristic Theme Engine<br/>TRON | Cyberpunk Amber | Deep Matrix | Obsidian Purple"]
        SettingsUI["Dynamic Model & System Configuration"]
    end

    subgraph APILayer ["2. API Orchestration Gateway (FastAPI)"]
        MainApp["FastAPI Server (:8000)"]
        AuthGate["Bearer Token & WSS Security Gate"]
        WSRoute["WebSocket Handler (/ws)"]
        ConfigRoute["Configuration API (/api/config)"]
        SpeechRoute["Speech API (/speech)"]
        OSRoute["OS Automation API (/os)"]
        OllamaRoute["Ollama Model Management API"]
    end

    subgraph CoreEngine ["3. Autonomous Agent & Orchestration Core"]
        Coordinator["Autonomous Agent Coordinator / Supervisor"]
        ReasoningEngine["Planning & Deep Reasoning Engine"]
        UnifiedProvider["Unified LLM Brain Adapter<br/>Ollama & Cloud Models"]
        SelfDiagnosis["Proactive Self-Diagnosis<br/>Connectivity & Resource Monitoring"]
        SkillRegistry["Singleton Skill Registry"]
    end

    subgraph ModelEngine ["4. Dynamic Model & Hardware Intelligence"]
        OllamaManager["Dynamic Ollama Engine"]
        ModelDetection["Local Model Detection<br/>GET /api/tags"]
        ModelPuller["In-UI Model Puller<br/>Real-Time Progress Streaming"]
        HardwareDetector["Hardware Detection<br/>CPU | RAM | GPU VRAM"]
        ModelRecommendation["Task-Aware Model Recommendation"]
    end

    subgraph SubAgents ["5. Domain Agent Skills"]
        JobHunter["Job Hunter Agent"]
        ResumeTailor["Resume Tailor Agent (RAG)"]
        JobApplicator["Job Applicator Agent"]
        NovelAgent["Novel Translation Agent"]
        SelfImprovement["Self-Improvement Agent"]
        SandboxVerifier["Sandbox & Execution Verifier"]
    end

    subgraph IntelligenceMemory ["6. Hybrid Memory & Intelligence"]
        FactExtractor["Dynamic Fact & Preference Extraction"]
        RAGMemory["Semantic Vector Memory<br/>ChromaDB"]
        WorkflowMemory["Persistent Workflow & Context Memory"]
        UserProfile["Dynamic User Profile"]
    end

    subgraph VoiceGovernance ["7. Voice, Security & Governance"]
        SpeechService["AEC | ASR | TTS | Speaker Diarization"]
        SandboxAudit["Sandbox Runner"]
        MerkleAudit["SHA-256 Merkle Audit Trail"]
        SecurityMonitor["Action & Security Monitoring"]
        CaddyProxy["Caddy Reverse Proxy<br/>Auto-HTTPS"]
    end


    %% Client Interactions
    FlutterApp --> ChatUI
    FlutterApp --> HUDSphere
    FlutterApp --> CommandDeck
    CommandDeck --> ModeSelector
    FlutterApp --> VoiceUI
    FlutterApp --> ThemeEngine
    FlutterApp --> SettingsUI

    %% API Communication
    FlutterApp <-->|REST / WebSocket / WSS| AuthGate
    AuthGate --> MainApp
    MainApp --> WSRoute
    MainApp --> ConfigRoute
    MainApp --> SpeechRoute
    MainApp --> OSRoute
    MainApp --> OllamaRoute

    %% Agent Orchestration
    WSRoute --> Coordinator
    ModeSelector --> ReasoningEngine
    ReasoningEngine --> Coordinator
    Coordinator --> UnifiedProvider
    Coordinator --> SkillRegistry
    Coordinator --> SelfDiagnosis

    %% Model Intelligence
    ConfigRoute --> OllamaManager
    OllamaRoute --> OllamaManager
    OllamaManager --> ModelDetection
    OllamaManager --> ModelPuller
    OllamaManager --> HardwareDetector
    HardwareDetector --> ModelRecommendation
    ModelRecommendation --> UnifiedProvider
    ModelDetection --> UnifiedProvider

    %% Agent Skills
    SkillRegistry --> JobHunter
    SkillRegistry --> ResumeTailor
    SkillRegistry --> JobApplicator
    SkillRegistry --> NovelAgent
    SkillRegistry --> SelfImprovement
    SelfImprovement --> SandboxVerifier

    %% Hybrid Memory
    Coordinator --> FactExtractor
    FactExtractor --> UserProfile
    FactExtractor --> WorkflowMemory
    UserProfile --> RAGMemory
    WorkflowMemory --> RAGMemory
    Coordinator <--> RAGMemory
    ResumeTailor <--> RAGMemory

    %% Voice
    SpeechRoute --> SpeechService
    VoiceUI <--> SpeechService

    %% OS Automation & Governance
    OSRoute --> SandboxAudit
    Coordinator --> SandboxAudit
    SandboxVerifier --> SandboxAudit
    SandboxAudit --> MerkleAudit
    MerkleAudit --> SecurityMonitor

    %% Production Deployment
    CaddyProxy --> AuthGate

    %% Self-Diagnosis Feedback
    SelfDiagnosis --> OllamaManager
    SelfDiagnosis --> HardwareDetector
    SelfDiagnosis --> SecurityMonitor
    SelfDiagnosis --> ChatUI
```

---

## Key Workflows

### 1. Distributed Multi-Device LAN Mesh & Compute Offloading
```text
Primary Coordinator ──► UDP Broadcast (:47470) ──► Auto-discovers Worker Nodes on Wi-Fi
                    ──► Dispatches `/nodes pull` ──► Triggers SLM downloads on Secondary Laptop
                    ──► Distributes Inference ──► Offloads embeddings & sub-agent execution
                    ──► Manifest Sync ──► Pushes profile & documents across LAN
```

### 2. Targeted SLM & Automated Model Selection
```text
Agent Directives ──► ModelSelectorAgent (evaluates role, RAM/GPU specs)
                 ──► Inspects Ollama (:11434) on Local & Remote Nodes
                 ──► Autonomous `ollama pull` (pulls <= 9B models e.g. Qwen, Phi-3)
                 ──► Deploys model into active agent execution loop
```

### 3. External Action & OS Automation Pipeline
```text
Natural Language Goal ──► Coordinator / Tool Executor ──► Audits targets & validates safety gate
                      ──► Subprocess & CLI Dispatch ──► Executes command in isolated environment
                      ──► Merkle Audit Trail ──► Records tamper-evident SHA-256 event leaf
```

### 4. Enterprise Multi-Engine Database & Autonomous Orchestration
```text
State / Data Ingestion ──► DatabaseOrchestrator (checks container health, RAM guardrails)
                       ──► PostgreSQL 16 (relational schema, transactional history, dedup audit)
                       ──► MongoDB 7.0 (unstructured agent transcripts & dynamic raw dossiers)
                       ──► Milvus 2.4.13 (high-dimensional semantic vectors via MinIO/etcd)
                       ──► Neo4j 5.20 (interpersonal entity graphs & multi-agent topologies)
```

---

## Sub-Agent Skills & Plugin Ecosystem

Thanatos features an extensible, modular architecture organized into clean categories (`system`, `memory`, `mesh`, `automation`, `creative`, `career`). Any agent tool or skill can be synthesized dynamically or plugged in by implementing `BaseSkill` and registering with `SkillRegistry`:

| Category | Primary Skills | Capabilities & Functional Scope |
| :--- | :--- | :--- |
| **System & Security** | `security_auditor`, `self_improvement` | Port auditing, process sandboxing, code self-inspection, automated test runs. |
| **Network & Mesh** | `mesh_worker`, `network_discovery` | Subnet node broadcasting, remote command dispatch, distributed inference pooling. |
| **Web & Intelligence**| `web_search`, `os_automation` | Live DuckDuckGo queries, Google News RSS, shell dispatch, desktop automation. |
| **Specialized Personas**| `butler_persona`, `secretary_persona` | Contact dossiers, interpersonal social dynamics, daily agendas, taste preference learning. |
| **Modular Domain Tasks**| `novel_agent`, `job_hunter`, `resume_tailor` | *Sample domain skills*: Chapter outline polishing, automated role discovery, and resume tailoring. Countless similar domain skills can be registered seamlessly. |

*To build a custom skill or domain agent, refer to the [Plugin Development Guide](./docs/plugin_dev_guide.md).*

---

## Tactical Voice Mode & Speaker Biometrics

Thanatos features a dedicated **Voice Mode** alongside standard Text Mode, designed for hands-free operations:

- **ECG / Cardiogram Frequency Waveform**: Live animated pulse wave visualizer that sweeps and modulates in real-time based on audio frequency (idle rhythm, user speaking bursts, AI neural speech harmonics).
- **Voice Activity Detection (VAD)**: Continuously evaluates energy thresholds and human vocal spectral boundaries (75 Hz to 3800 Hz) to detect speech without clipping.
- **Multi-Speaker Diarization & Authorization**:
  - **Owner (Boss)**: Primary enrolled voice profile with full administrative directive privileges.
  - **Authorized Delegates**: Approved team members or operators enrolled to issue permitted tasks.
  - **Unauthorized Guests**: Third-party speech is detected, flagged, and rejected by the agent authorization guard to prevent accidental or malicious execution.
- **Optional Camera Module (Face Recognition & Lip Tracking)**:
  - Real-time webcam viewfinder tracking the user's face.
  - Measures Mouth Aspect Ratio (MAR) and optical pixel variance to verify if the Boss is physically speaking on camera, preventing voice-spoofing or off-camera background audio execution.
  - Uses standard OpenCV Haar Cascades with zero mandatory cloud dependencies.

*For complete technical details and architecture, see [Voice Mode & Speaker Verification Specification](./docs/voice_mode_speaker_verification.md).*

---

## Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast, lock-file-based Python package manager
- **Flutter SDK 3.x** (for desktop/mobile/web client)
- **Ollama** (for local LLM execution: `ollama run qwen2.5:7b` or `deepseek-r1:7b`)
- *(Optional)* **OpenCV** for camera facial tracking

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Kennny7/Thanatos.git
cd Thanatos

# Install uv (if not already installed)
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux:
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Install exact, locked dependencies (reads uv.lock — no version drift)
uv sync --extra dev

# Start the FastAPI server
uv run uvicorn apps.api_server.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Why `uv sync` instead of `pip install`?**  
> `uv.lock` is committed to the repo and pins **exact versions** for all 100+ packages including transitive deps, so every developer and CI run gets an identical environment. See [Dependency Management](./docs/dependency_management.md) for details.
### 3. Environment & Variable Configuration

Copy `.env.example` to `.env` in the root directory to customize configuration settings:

```bash
cp .env.example .env
```

Key configuration parameters handled via `.env` file or environment variables:

- LLM Settings:
  - `LLM_PROVIDER`: LLM provider identifier (default: `ollama`).
  - `LLM_MODEL`: Active model name (default: `qwen2.5:7b`).
  - `LLM_BASE_URL`: Connection URL for local LLM service (default: `http://localhost:11434`).
  - `DEEPSEEK_API_KEY`: API key for DeepSeek cloud service.
  - `OPENAI_API_KEY`: API key for OpenAI API endpoint.
- Memory & Vector Database (ChromaDB):
  - `MEMORY_PERSIST_DIR`: Persistence storage path for ChromaDB vector database (default: `./memory_store`).
  - `MEMORY_COLLECTION`: Vector database collection name (default: `thanatos_memories`).
  - `EMBEDDING_MODEL`: Embedding model name for local RAG (default: `all-MiniLM-L6-v2`).
  - `EMBEDDING_DEVICE`: Computing device for embedding generation (default: `cpu`).
- User Profile & Personal Data Defaults:
  - `USER_NAME`: User display name in system context (default: `User`).
  - `USER_EMAIL`: User contact email address (default: `user@example.com`).
  - `USER_LOCATION`: Location context for localized skills.
  - `USER_TITLE`: Professional title context.
- Speech & Voice Settings:
  - `TTS_VOICE`: Voice identifier for Text-to-Speech (default: `en-US-AriaNeural`).
  - `STT_MODEL`: Faster-Whisper model size for Speech-to-Text (default: `base`).
  - `SPEAKER_ENROLLMENT_DIR`: Storage path for speaker enrollment profiles (default: `./voice_profiles`).

### 4. Local Model Setup (Ollama)
```bash
# Pull recommended models
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b
```

### 5. Flutter Client Setup & Cross-Platform Run

```bash
cd apps/client_flutter

# Install Flutter dependencies
flutter pub get

# Run directly on your desktop / browser platform
flutter run -d windows    # Windows Desktop
# or
flutter run -d macos      # macOS Desktop
# or
flutter run -d chrome     # Web Browser
```

#### Building & Deploying the Android App

Thanatos runs on Android devices both as a portable mobile UI and as a wireless mesh compute node.

**Option A: Direct Run & Debug on Connected Android Device**
1. Enable **Developer Options** and **USB Debugging** on your Android device (or connect via Wireless ADB on the same Wi-Fi: `adb connect <android-ip>:5555`).
2. Verify device connection:
   ```bash
   flutter devices
   ```
3. Run directly on Android:
   ```bash
   flutter run -d android
   ```

**Option B: Build Standalone Release APK & Transfer to Phone**
1. Build the optimized release APK:
   ```bash
   # Build universal release APK
   flutter build apk --release

   # Or build split per-ABI APKs (smaller file size for arm64-v8a devices)
   flutter build apk --split-per-abi --release
   ```
2. Locate the generated APK at:
   - Universal: `apps/client_flutter/build/app/outputs/flutter-apk/app-release.apk`
   - Split ABI: `apps/client_flutter/build/app/outputs/flutter-apk/app-arm64-v8a-release.apk`

3. Transfer and install onto your Android device:
   - **Via ADB (Instant Cable / Wireless Command)**:
     ```bash
     adb install -r build/app/outputs/flutter-apk/app-release.apk
     ```
   - **Manual Transfer (Without ADB)**:
     - Connect your Android phone to your PC via USB cable in **File Transfer (MTP)** mode.
     - Copy `app-release.apk` to your phone's `Download/` or internal storage folder.
     - Open the Files / File Manager app on your Android phone, tap `app-release.apk`, and tap **Install** (allow installation from unknown sources if prompted).
     - Alternatively, send the `.apk` file to your phone via local Wi-Fi sharing (e.g. LocalSend, KDE Connect, or Python HTTP server: `python -m http.server 8080` in the APK directory).

4. **Connecting Android to Thanatos Backend**:
   - Ensure your phone is connected to the same Wi-Fi network as the Thanatos host machine.
   - In the Thanatos Android app, open Settings and point the Gateway URL to your host's local IP (e.g. `http://192.168.1.X:8000`), or let the built-in UDP beacon discovery auto-link to the primary machine.

### 6. Running the Test Suite
```bash
# Run all 48 unit and integration tests
pytest tests -v
```

---

## Project Structure

```text
Thanatos
|-- apps/
|   |-- api_server/               # FastAPI backend with WebSockets & REST routers
|   |   |-- core/                 # Agent loop, dispatcher, session manager
|   |   |-- routes/               # WebSocket, config, speech, health, OS routes
|   |   `-- schemas/              # Pydantic v2 communication models
|   |-- client_flutter/           # Cross-platform Flutter application
|   |   |-- lib/models/           # Message, thought, and agent models
|   |   |-- lib/state/            # Riverpod state management & WebSocket provider
|   |   `-- lib/ui/               # Chat screen, voice visualizer, settings & tracker
|   `-- mcp_server/               # Model Context Protocol (MCP) server for Claude / Cursor
|-- services/
|   |-- llm_brain/                # Unified LLM provider & multi-agent coordinator
|   |-- local_llm/                # Ollama client with dynamic model discovery
|   |-- memory/                   # VectorStore (ChromaDB), MemoryManager & UserProfile
|   |-- speech/                   # STT, TTS, AEC processor & Speaker Diarization
|   `-- os_automation/            # System control & OS interaction
|-- plugins/
|   |-- base/                     # BaseSkill interface & SkillRegistry
|   `-- system_skills/            # Domain skills (Job hunter, resume tailor, applicator, novel, self-improvement)
|-- sandbox/                      # Subprocess limiter & Docker container isolation
|-- audit/                        # Tamper-evident Merkle hash audit logger
|-- docs/                         # Comprehensive technical documentation suite
`-- tests/                        # Full test suite (48 tests passing)
```

---

## Contributing

We welcome contributions from the community. Please read our [Contributor Guide](./docs/contributing.md) to learn about our development process, coding standards, and how to submit pull requests.

---

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](./LICENSE) file for details.
