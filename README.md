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

1. **Unified LLM Brain & Deep Thinking**: Local Ollama execution (`qwen2.5:7b`, `deepseek-r1:7b/14b`, `llama3.1:8b`, `phi3`) with real-time `<think>` reasoning streaming and robust tool parsing.
2. **Multi-Agent Supervisor / Coordinator**: Decomposes high-level natural language goals into sub-agent Directed Acyclic Graphs (DAGs).
3. **Speech Intelligence & Speaker Diarization**:
   - **ASR & TTS**: Powered by `faster-whisper` and neural `edge-tts`.
   - **Acoustic Echo Cancellation (AEC)**: Real-time spectral subtraction and noise suppression.
   - **Speaker Diarization**: Distinguishes between "Owner (You)" and "Guest Speaker" using pitch and spectral embeddings.
4. **Hybrid Memory & Career RAG**: ChromaDB vector search integrated with a structured candidate profile manager for context-aware workflows.
5. **Cross-Platform Flutter Client**: Responsive desktop (Windows, macOS, Linux) and mobile (Android, iOS) UI with deep thinking traces, animated voice visualizer, and live agent status tracking.
6. **Zero-Trust Sandbox & Merkle Audit Trail**: Subprocess timeouts, isolated test runners, and SHA-256 tamper-evident cryptographic event logging.

---

## Documentation Hub

Explore the comprehensive technical documentation suite in the [`docs/`](./docs) directory:

| Document | Description | Action |
| :--- | :--- | :---: |
| **Getting Started Guide** | Step-by-step setup guide for Python backend, Ollama models, and Flutter client. | [![Read Guide](https://img.shields.io/badge/Open-Guide-2EA44F?style=flat-square)](./docs/getting_started.md) |
| **System Architecture** | Component breakdown, supervisor-worker topology, and layer interactions. | [![Read Spec](https://img.shields.io/badge/Open-Spec-6F42C1?style=flat-square)](./docs/architecture.md) |
| **Master Architecture & Workflows** | Authoritative 7-module blueprint with sequence diagrams and execution contracts. | [![Read Blueprint](https://img.shields.io/badge/Open-Blueprint-007ACC?style=flat-square)](./docs/system_architecture_and_workflow.md) |
| **API Specification** | Full REST endpoints and WebSocket streaming protocol (`/ws`) reference. | [![Read API Spec](https://img.shields.io/badge/Open-API%20Spec-009688?style=flat-square)](./docs/api_spec.md) |
| **Plugin Development Guide** | Tutorial on creating, registering, and testing custom sub-agent skills. | [![Read Guide](https://img.shields.io/badge/Open-Dev%20Guide-F39C12?style=flat-square)](./docs/plugin_dev_guide.md) |
| **Speech Intelligence & AEC** | Voice pipeline, acoustic echo cancellation, and speaker diarization details. | [![Read Voice Spec](https://img.shields.io/badge/Open-Voice%20Spec-3776AB?style=flat-square)](./docs/speech_intelligence.md) |
| **Memory & RAG Subsystem** | ChromaDB vector store, semantic embeddings, and career profile matching. | [![Read RAG Guide](https://img.shields.io/badge/Open-RAG%20Guide-4B8BBE?style=flat-square)](./docs/memory_and_rag.md) |
| **Security & Isolation Model** | Sandbox boundaries, OS safety confirmation gates, and Merkle audit logs. | [![Read Model](https://img.shields.io/badge/Open-Security%20Model-E74C3C?style=flat-square)](./docs/security_model.md) |
| **Model Context Protocol (MCP)** | Exposing Thanatos OS tools to Claude Desktop, Cursor IDE, and MCP hosts. | [![Read MCP Guide](https://img.shields.io/badge/Open-MCP%20Guide-555555?style=flat-square)](./docs/mcp_server.md) |
| **Contributor Guide** | Coding conventions, PR guidelines, and running the test suite. | [![Read Guide](https://img.shields.io/badge/Open-Contributing-24292E?style=flat-square)](./docs/contributing.md) |

---

## System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Client Layer (Cross-Platform Flutter)"]
        FlutterApp["Flutter App (Desktop / Mobile / Web)"]
        ChatUI["Chat UI & Deep Thinking Trace"]
        VoiceUI["Voice Visualizer (AEC & Speaker Diarization)"]
        SettingsUI["Model Configuration (Ollama & Cloud)"]
    end

    subgraph APILayer ["2. API Orchestration Gateway (FastAPI)"]
        MainApp["FastAPI Server (:8000)"]
        WSRoute["WebSocket Handler (/ws)"]
        ConfigRoute["Config API (/api/config)"]
        SpeechRoute["Speech API (/speech)"]
        OSRoute["OS Automation API (/os)"]
    end

    subgraph CoreEngine ["3. Agent & Orchestration Core"]
        Coordinator["Agent Coordinator / Supervisor"]
        UnifiedProvider["Unified LLM Brain Adapter"]
        SkillRegistry["Singleton Skill Registry"]
    end

    subgraph SubAgents ["4. Domain Agent Skills"]
        JobHunter["Job Hunter Agent"]
        ResumeTailor["Resume Tailor Agent (RAG)"]
        JobApplicator["Job Applicator Agent"]
        NovelAgent["Novel Translation Agent"]
        SelfImprovement["Self-Improvement & Sandbox Verifier"]
    end

    subgraph MemoryVoice ["5. Memory, Audio & Governance"]
        RAGMemory["ChromaDB Vector Store & User Profile"]
        SpeechService["AEC, ASR, TTS & Speaker Diarization"]
        SandboxAudit["Sandbox Runner & Merkle Audit Trail"]
    end

    FlutterApp <-->|WebSocket / REST| MainApp
    MainApp --> WSRoute & ConfigRoute & SpeechRoute & OSRoute
    WSRoute --> Coordinator --> UnifiedProvider
    Coordinator --> SkillRegistry --> SubAgents
    Coordinator --> RAGMemory
    SpeechRoute --> SpeechService
    SubAgents --> SandboxAudit
```

---

## Key Workflows

### 1. Autonomous Job Hunting & Resume Tailoring Pipeline
```text
User Prompt ──► Agent Coordinator ──► JobHunter (finds matching tech openings)
                                  ──► ResumeTailor (queries UserProfile RAG & generates custom resume)
                                  ──► JobApplicator (packages application & logs entry)
                                  ──► Streams live progress to Flutter UI
```

### 2. Web Novel Translation & Glossary Polish Pipeline
```text
Chapter Raw Text ──► NovelAgent ──► Translates with glossary term enforcement
                                ──► Polishes prose style & tone
                                ──► Returns structured bilingual chapter output
```

### 3. Self-Improvement Code Reflection Pipeline
```text
Codebase Inspection ──► SelfImprovement Agent ──► Analyzes target file
                                              ──► Proposes fix / refactor
                                              ──► Runs tests inside Sandbox
                                              ──► Commits verified patch
```

### 4. Multi-Speaker Voice Intelligence & Diarization
```text
Microphone Audio ──► AEC Processor (removes acoustic echo & noise)
                 ──► Speaker Identifier (extracts pitch/spectral features vs Owner profile)
                 ──► Faster-Whisper ASR (transcribes multi-speaker audio with timestamps)
                 ──► Agent Loop (handles directives like "summarize what others said")
```

---

## Sub-Agent Skills & Plugin Ecosystem

Thanatos features a pluggable skill architecture where every domain agent implements `BaseSkill` and registers with `SkillRegistry`:

| Skill Identifier | Tools Provided | Functional Scope |
| :--- | :--- | :--- |
| `job_hunter` | `search_jobs` | Scrapes tech openings by role and location (e.g. Pune freshers). |
| `resume_tailor` | `tailor_resume` | Queries RAG career memory and generates tailored resumes and cover letters. |
| `job_applicator` | `prepare_job_application` | Formulates application submission packages and logs history. |
| `novel_agent` | `translate_and_edit_novel` | Translates raw novel chapters with glossary consistency. |
| `self_improvement` | `self_improve_code` | Inspects architecture, runs sandbox tests, and validates code improvements. |

*To build a custom skill, refer to the [Plugin Development Guide](./docs/plugin_dev_guide.md).*

---

## Quick Start

### 1. Prerequisites
- **Python 3.12+**
- **Flutter SDK 3.x** (for desktop/mobile client)
- **Ollama** (for local LLM execution: `ollama run qwen2.5:7b` or `deepseek-r1:7b`)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Kennny7/Thanatos.git
cd Thanatos

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # On Windows
source venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn apps.api_server.main:app --host 0.0.0.0 --port 8000 --reload
```
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

### 5. Flutter Client Setup
```bash
cd apps/client_flutter

# Install Flutter dependencies
flutter pub get

# Run on your desktop platform
flutter run -d windows    # Windows Desktop
# or
flutter run -d macos      # macOS Desktop
# or
flutter run -d chrome     # Web Browser
```

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
