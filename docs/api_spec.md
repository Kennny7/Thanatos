# Thanatos API Specification

This document provides the definitive specification for all REST endpoints, WebSocket streaming protocols, and shared data schemas in the Thanatos AI Assistant Engine.

---

## Table of Contents

- [Overview & Base URL](#overview--base-url)
- [Authentication & Headers](#authentication--headers)
- [REST Endpoints](#rest-endpoints)
  - [1. Health Check](#1-health-check)
  - [2. Model & Runtime Configuration](#2-model--runtime-configuration)
  - [3. Speech & Voice Intelligence](#3-speech--voice-intelligence)
  - [4. OS Automation & System Control](#4-os-automation--system-control)
- [WebSocket Protocol (`/ws`)](#websocket-protocol-ws)
  - [Connection Lifecycle](#connection-lifecycle)
  - [Message Types & Envelopes](#message-types--envelopes)
  - [Streaming Flow Diagram](#streaming-flow-diagram)
  - [WebSocket Error Handling](#websocket-error-handling)
- [Error Codes & Responses](#error-codes--responses)

---

## Overview & Base URL

The Thanatos API Server is built with FastAPI and runs asynchronously on port 8000 by default.

- **HTTP Base URL**: `http://localhost:8000`
- **WebSocket URL**: `ws://localhost:8000/ws`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **ReDoc UI**: `http://localhost:8000/redoc`

---

## Authentication & Headers

Currently, Thanatos operates in local-first development mode. All endpoints accept standard JSON payloads.

| Header | Value | Description |
| :--- | :--- | :--- |
| `Content-Type` | `application/json` | Required for JSON request bodies |
| `Accept` | `application/json`, `audio/mpeg` | Expected response MIME type |

CORS is enabled by default to allow connections from local Flutter Desktop, Web, and mobile debug builds (`*`).

---

## REST Endpoints

### 1. Health Check

#### `GET /health`
Verifies that the FastAPI server and core services are active and reachable.

**Response (`200 OK`)**:
```json
{
  "status": "ok"
}
```

---

### 2. Model & Runtime Configuration

#### `GET /api/config`
Retrieves the active LLM provider, current model, endpoint URL, temperature, and local execution flags.

**Response (`200 OK`)**:
```json
{
  "provider": "ollama",
  "model": "qwen2.5:7b",
  "base_url": "http://localhost:11434",
  "temperature": 0.7,
  "is_local": true,
  "supports_tools": true
}
```

#### `POST /api/config/llm`
Dynamically changes the active LLM model, provider, or temperature without restarting the server.

**Request Body (`application/json`)**:
```json
{
  "provider": "ollama",
  "model": "deepseek-r1:14b",
  "base_url": "http://localhost:11434",
  "temperature": 0.6,
  "api_key": null
}
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Active model updated to deepseek-r1:14b",
  "config": {
    "provider": "ollama",
    "model": "deepseek-r1:14b",
    "base_url": "http://localhost:11434",
    "temperature": 0.6,
    "is_local": true
  }
}
```

#### `GET /api/config/models`
Enumerates installed local Ollama models along with available cloud models.

**Response (`200 OK`)**:
```json
{
  "active_model": "qwen2.5:7b",
  "active_provider": "ollama",
  "models": [
    "qwen2.5:7b",
    "deepseek-r1:7b",
    "deepseek-r1:14b",
    "llama3.1:8b",
    "phi3:mini",
    "deepseek-chat",
    "gpt-4o-mini"
  ]
}
```

---

### 3. Speech & Voice Intelligence

#### `POST /speech/transcribe`
Processes audio files with Acoustic Echo Cancellation (AEC), Voice Activity Detection (VAD), Faster-Whisper ASR, and optional multi-speaker diarization.

**Request (`multipart/form-data`)**:
- `file`: Audio file (`.wav`, `.mp3`, `.ogg`, `.m4a`)
- `diarize`: `bool` (default: `true`)

**Response (`200 OK`)**:
```json
{
  "transcript": "Search for software engineer jobs in Pune and customize my resume.",
  "primary_speaker": "Owner (You)",
  "confidence": 0.96,
  "segments": [
    {
      "start": 0.0,
      "end": 3.42,
      "speaker": "Owner (You)",
      "text": "Search for software engineer jobs in Pune and customize my resume."
    }
  ]
}
```

#### `POST /speech/synthesize`
Synthesizes text into high-fidelity neural speech (Edge-TTS) and returns a streaming MP3 audio byte buffer.

**Request Body (`application/json`)**:
```json
{
  "text": "I found 3 matching fresher roles in Pune and prepared your tailored resume.",
  "voice": "en-US-ChristopherNeural"
}
```

**Response (`200 OK`)**:
- `Content-Type`: `audio/mpeg`
- Body: Binary MP3 stream

#### `POST /speech/enroll-voice`
Enrolls the user's primary voice profile by extracting pitch, MFCCs, and spectral signatures from a clear speech sample.

**Request (`multipart/form-data`)**:
- `file`: Audio sample (`.wav`)

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Voice profile enrolled successfully",
  "features": {
    "pitch_mean": 124.5,
    "spectral_centroid": 1820.3
  }
}
```

#### `GET /speech/voice-status`
Checks if an enrolled owner voice profile exists on disk.

**Response (`200 OK`)**:
```json
{
  "is_enrolled": true,
  "profile_path": "services/speech/profiles/owner_voice.json"
}
```

---

### 4. OS Automation & System Control

#### `POST /os/open-app`
Launches an installed desktop application by name.

**Request Body (`application/json`)**:
```json
{
  "app_name": "Chrome"
}
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Application 'Chrome' launched successfully."
}
```

#### `GET /os/system-stats`
Returns live system metrics including CPU utilization, RAM usage, and primary disk statistics.

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "data": {
    "cpu_percent": 18.4,
    "memory_percent": 62.1,
    "memory_used_gb": 9.94,
    "memory_total_gb": 16.0,
    "disk_percent": 45.2
  }
}
```

#### `POST /os/set-volume`
Sets the system master audio volume between 0 and 100%.

**Request Body (`application/json`)**:
```json
{
  "level": 65
}
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "System volume set to 65%."
}
```

#### `POST /os/type-text`
Simulates keyboard typing after safety confirmation against the active foreground window.

**Request Body (`application/json`)**:
```json
{
  "text": "print('Hello from Thanatos')",
  "force": false
}
```

**Response (`200 OK`)**:
```json
{
  "status": "success",
  "message": "Typed 28 characters."
}
```

**Safety Confirmation Error (`409 Conflict`)**:
```json
{
  "detail": "Confirmation required. Active window: Visual Studio Code. Set 'force' to True to proceed."
}
```

---

## WebSocket Protocol (`/ws`)

The WebSocket endpoint provides full-duplex, low-latency streaming between client UIs (such as the Flutter client) and the Thanatos multi-agent orchestration engine.

### Connection Lifecycle

1. **Handshake**: Client initiates WebSocket connection to `ws://localhost:8000/ws`.
2. **Session Initialization**: A unique `SessionManager` is allocated for the connection.
3. **Heartbeat**: The server emits a `heartbeat` frame every 15 seconds.
4. **Message Exchange**: Client sends user prompts; server streams thoughts, sub-agent statuses, tool execution events, and token chunks.
5. **Clean Disconnect**: Handles client unmounts and cancels active generator tasks gracefully.

---

### Message Types & Envelopes

All WebSocket messages are serialized as JSON objects with a discriminating `"type"` field.

#### 1. Incoming: User Message (`user_message`)
Sent by the client when the user inputs a prompt or voice transcription.
```json
{
  "type": "user_message",
  "content": "Find software engineer openings in Pune and tailor my resume."
}
```

#### 2. Outgoing: Thought Stream (`thought`)
Streams internal reasoning traces (e.g. DeepSeek-R1 `<think>` tags or multi-step agent planning).
```json
{
  "type": "thought",
  "content": "Analyzing user intent: user wants to search Pune jobs and tailor resume using profile RAG."
}
```

#### 3. Outgoing: Agent Status Update (`agent_status`)
Live breadcrumb informing the client UI which sub-agent is active and current progress.
```json
{
  "type": "agent_status",
  "agent": "job_hunter",
  "status": "Searching tech openings in Pune...",
  "progress": 0.35
}
```

#### 4. Outgoing: Tool Call Request (`tool_call_request`)
Emitted when an agent invokes a tool (either server-side skill or client-side action).
```json
{
  "type": "tool_call_request",
  "call_id": "call_9a8b7c6d",
  "tool_name": "search_jobs",
  "arguments": {
    "location": "Pune",
    "keywords": "freshers software engineer",
    "limit": 3
  }
}
```

#### 5. Outgoing / Incoming: Tool Result (`tool_result`)
Represents the output of a tool execution.
```json
{
  "type": "tool_result",
  "call_id": "call_9a8b7c6d",
  "success": true,
  "content": {
    "total": 3,
    "jobs": [
      {
        "id": "job-102",
        "title": "Associate Software Engineer",
        "company": "Persistent Systems",
        "location": "Pune, India"
      }
    ]
  },
  "error": null
}
```

#### 6. Outgoing: Assistant Chunk (`assistant_chunk`)
Streamed token chunks of the final synthesized assistant response.
```json
{
  "type": "assistant_chunk",
  "content": "I found 3 relevant software engineering roles in Pune and tailored your resume."
}
```

#### 7. Outgoing: Heartbeat (`heartbeat`)
```json
{
  "type": "heartbeat"
}
```

#### 8. Outgoing: Error Message (`error`)
```json
{
  "type": "error",
  "content": "Ollama connection timeout. Please ensure Ollama is running."
}
```

---

### Streaming Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client as Flutter Client UI
    participant WS as WebSocket Handler (/ws)
    participant Loop as Agent ReAct Loop
    participant Coord as Multi-Agent Coordinator
    participant Skill as Skill / Tool Registry

    Client->>WS: UserMessage("Search Pune jobs & tailor resume")
    WS->>Loop: Initialize Step Execution
    Loop->>WS: ThoughtMessage("Decomposing goal into subtasks...")
    WS->>Client: Thought Streamed

    Loop->>Coord: Plan Task Pipeline
    Coord->>WS: AgentStatusMessage("job_hunter", "Searching...", 0.25)
    WS->>Client: Render Status Breadcrumb

    Coord->>Skill: dispatch("search_jobs", {location: "Pune"})
    Skill-->>Coord: ToolResult(jobs: [...])

    Coord->>WS: AgentStatusMessage("resume_tailor", "Tailoring resume...", 0.70)
    WS->>Client: Render Status Breadcrumb

    Coord->>Skill: dispatch("tailor_resume", {...})
    Skill-->>Coord: ToolResult(resume_markdown: "...")

    Coord-->>Loop: Aggregated Pipeline Output
    loop For each token chunk
        Loop->>WS: AssistantChunk("...")
        WS->>Client: Live Text Streaming
    end
```

---

## Error Codes & Responses

Thanatos uses standard HTTP status codes:

| Status Code | Reason | Description |
| :--- | :--- | :--- |
| `200 OK` | Success | Request succeeded normally. |
| `400 Bad Request` | Invalid Input | Invalid parameters (e.g. volume out of 0-100 range). |
| `404 Not Found` | Resource Missing | Skill, tool, or requested endpoint not found. |
| `409 Conflict` | Safety Check Required | OS automation requested a sensitive action; user confirmation needed. |
| `500 Internal Error` | Server Error | Unhandled exception in provider, speech, or sandbox runner. |
