# Getting Started with Thanatos

Welcome to **Thanatos**. This guide walks you through setting up, configuring, and running the Thanatos AI Assistant Engine and its cross-platform Flutter client on your local machine.

---

## Table of Contents

- [1. System Requirements](#1-system-requirements)
- [2. Prerequisites](#2-prerequisites)
- [3. Backend Installation & Setup](#3-backend-installation--setup)
- [4. Local LLM Setup (Ollama)](#4-local-llm-setup-ollama)
- [5. Flutter Client Installation & Setup](#5-flutter-client-installation--setup)
- [6. Running the Entire Stack](#6-running-the-entire-stack)
- [7. Running the Test Suite](#7-running-the-test-suite)
- [8. Troubleshooting & FAQ](#8-troubleshooting--faq)

---

## 1. System Requirements

| Component | Minimum | Recommended |
| :--- | :--- | :--- |
| **OS** | Windows 10/11, macOS 12+, or Ubuntu 20.04+ | Windows 11 / Ubuntu 22.04 LTS |
| **Python** | Python 3.12+ | Python 3.12 or 3.13 |
| **RAM** | 16 GB (for 14B models) | 32 GB – 64 GB (for 32B–70B models) |
| **GPU** | Optional (CPU inference supported, slow) | NVIDIA GPU (16 GB+ VRAM) or Apple Silicon (M2 Pro/Max/Ultra) |
| **Flutter** | Flutter SDK 3.x | Latest Flutter Stable Channel |

---

## 2. Prerequisites

Ensure you have installed:
1. **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
2. **uv** (Python package manager): [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
3. **Git**: [Download Git](https://git-scm.com/)
4. **Ollama** (for local LLM inference): [Download Ollama](https://ollama.com)
5. **Flutter SDK** (for UI client): [Install Flutter](https://docs.flutter.dev/get-started/install)

---

## 3. Backend Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/Kennny7/Thanatos.git
cd Thanatos
```

### Step 2: Install `uv` (Python Package Manager)

Thanatos uses [`uv`](https://docs.astral.sh/uv/) for deterministic, lock-file-based dependency management.

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell after installation so `uv` is on your PATH.

### Step 3: Install Dependencies (reproducible via lock file)

```bash
# Install all runtime deps from the committed uv.lock (exact versions)
uv sync

# Include dev/test extras
uv sync --extra dev
```

> **Why `uv sync` instead of `pip install`?**  
> `uv sync` reads `uv.lock` — a committed, cross-platform lock file — and installs
> the **exact same versions** on every machine. This prevents the `>=` version drift
> problem where a new library release could silently break the project.

> **Fallback (if `uv` is unavailable)**  
> ```bash
> python -m venv venv && venv\Scripts\activate   # Windows
> pip install -r requirements.txt
> ```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory (or copy from sample):
```env
ENVIRONMENT=development
PORT=8000
HOST=0.0.0.0
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_BASE_URL=http://localhost:11434
```

---

## 4. Local LLM Setup (Ollama)

Thanatos runs completely offline using local models managed by Ollama.

> [!IMPORTANT]
> Thanatos orchestrates multiple agents with planning, RAG retrieval, tool execution, and multi-step reasoning chains. **7B–8B models will struggle** with this complexity. The practical minimum for coherent multi-agent behaviour is **14B**; **32B is the recommended sweet spot**.

### Model Tier Guide

| Tier | Model | RAM Required | Notes |
|:--|:--|:--|:--|
| 🟡 Minimum | `qwen2.5:14b` | ~12 GB | Works for simple tasks; struggles with deep reasoning |
| 🟢 Recommended | `qwen2.5:32b` | ~20 GB | Strong reasoning, excellent tool use |
| 🟢 Recommended | `deepseek-r1:32b` | ~20 GB | Best local choice for planning-heavy tasks |
| 🔵 Best | `qwen2.5:72b` | ~45 GB | Near-frontier quality locally |
| 🔵 Best | `deepseek-r1:70b` | ~45 GB | Top open-source reasoning model |
| ☁️ Cloud fallback | GPT-4o / Claude / Gemini | — | Set `LLM_PROVIDER=openai` or `deepseek`, add API key |

### Pull Models

```bash
# Recommended: strong reasoning & planning
ollama pull qwen2.5:32b
ollama pull deepseek-r1:32b

# Constrained hardware minimum (14B)
ollama pull qwen2.5:14b

# Optional: lightweight sub-agent models for delegated skills
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b
```

Ensure the Ollama daemon is running in the background (`ollama serve` or system service).

---

## 5. Flutter Client Installation & Setup

The Flutter application provides a desktop and mobile UI for chat, live sub-agent status tracking, and voice interaction.

```bash
cd apps/client_flutter

# Fetch Dart/Flutter dependencies
flutter pub get

# Check connected devices
flutter devices
```

---

## 6. Running the Entire Stack

### Step 1: Start the Backend API Server
In your root repository folder with virtual environment activated:
```bash
uvicorn apps.api_server.main:app --host 0.0.0.0 --port 8000 --reload
```
Once started, the API docs are accessible at `http://localhost:8000/docs`.

### Step 2: Launch the Flutter Client
In a second terminal:
```bash
cd apps/client_flutter
flutter run -d windows    # On Windows Desktop
# or
flutter run -d macos      # On macOS Desktop
# or
flutter run -d linux      # On Linux Desktop
# or
flutter run -d chrome     # In Web Browser
```

---

## 7. Running the Test Suite

Thanatos includes a comprehensive test suite covering unit tests, multi-agent integration workflows, security sandboxing, and audit trail verification.

```bash
# Run all 48 tests
pytest tests -v

# Run specific unit tests
pytest tests/unit -v

# Run multi-agent workflow tests
pytest tests/integration/test_workflow.py -v
```

---

## 8. Troubleshooting & FAQ

### Issue 1: `Ollama connection error`
- **Cause**: Ollama is not running on `http://localhost:11434`.
- **Fix**: Open a terminal and run `ollama serve`. Verify with `curl http://localhost:11434/api/tags`.

### Issue 2: `Audio / Microphone not detected in speech transcription`
- **Cause**: Missing audio driver or microphone permissions.
- **Fix**: Ensure your microphone permissions are granted to the application, or test using the REST endpoint `/speech/transcribe` with an audio file.

### Issue 3: `OS Automation 409 Conflict Error`
- **Cause**: `SafetyCheckRequired` exception triggered because typing into an active window requires confirmation.
- **Fix**: Send `"force": true` in the `/os/type-text` payload or confirm via the client UI.
