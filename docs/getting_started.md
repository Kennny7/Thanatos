# Getting Started with Thanatos

Welcome to **Thanatos**! This guide walks you through setting up, configuring, and running the Thanatos AI Assistant Engine and its cross-platform Flutter client on your local machine.

---

## 📑 Table of Contents

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
| **RAM** | 8 GB (for 7B models) | 16 GB - 32 GB (for 14B/32B models) |
| **GPU** | Optional (CPU inference supported) | NVIDIA GPU (6GB+ VRAM) or Apple Silicon (M1/M2/M3) |
| **Flutter** | Flutter SDK 3.x | Latest Flutter Stable Channel |

---

## 2. Prerequisites

Ensure you have installed:
1. **Python 3.12+**: [Download Python](https://www.python.org/downloads/)
2. **Git**: [Download Git](https://git-scm.com/)
3. **Ollama** (for local LLM inference): [Download Ollama](https://ollama.com)
4. **Flutter SDK** (for UI client): [Install Flutter](https://docs.flutter.dev/get-started/install)

---

## 3. Backend Installation & Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/Kennny7/Thanatos.git
cd Thanatos
```

### Step 2: Create a Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the root directory (or copy from sample):
```env
APP_ENV=development
API_PORT=8000
API_HOST=0.0.0.0
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 4. Local LLM Setup (Ollama)

Thanatos runs completely offline using local models managed by Ollama.

### Pull Recommended Models
```bash
# Lightweight & fast (Recommended for 8GB RAM laptops)
ollama pull qwen2.5:7b

# Deep reasoning model (Recommended for 16GB RAM / GPU)
ollama pull deepseek-r1:7b
# or
ollama pull deepseek-r1:14b

# General purpose assistant
ollama pull llama3.1:8b
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
