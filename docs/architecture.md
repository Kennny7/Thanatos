# Thanatos Architecture Specification

> **Canonical Document Notice**:
> The complete, authoritative, and in-depth architecture and workflow documentation for Thanatos is located at:
> 📄 **[`docs/system_architecture_and_workflow.md`](./system_architecture_and_workflow.md)**

---

## Quick Reference Architecture

```mermaid
flowchart TB
    subgraph ClientLayer ["Client Layer (Cross-Platform Flutter)"]
        FlutterApp["Flutter App (Android, iOS, Web, Windows, macOS, Linux)"]
        ChatUI["Chat UI & Deep Thinking Trace"]
        VoiceUI["Voice Visualizer (AEC & Speaker Diarization)"]
        SettingsUI["Model Configuration (Ollama 7B/14B/30B & Cloud)"]
    end

    subgraph APILayer ["API Orchestration Gateway (FastAPI)"]
        MainApp["FastAPI Main Server (:8000)"]
        WSRoute["WebSocket Handler (/ws)"]
        ConfigRoute["Model Config API (/api/config)"]
        SpeechRoute["Speech Intelligence API (/speech)"]
    end

    subgraph CoreEngine ["Agent & Orchestration Core"]
        Coordinator["Agent Coordinator / Supervisor"]
        UnifiedProvider["Unified LLM Brain Adapter"]
        SkillRegistry["Skill & Tool Registry"]
    end

    subgraph SubAgents ["Autonomous Sub-Agents"]
        JobHunter["Job Hunter (Pune & Remote)"]
        ResumeTailor["Resume Tailor & RAG Matcher"]
        JobApplicator["Application Packager & Auto-Apply"]
        NovelAgent["Novel Translator & Glossary Editor"]
        SelfImprovement["Self-Improvement & Sandbox Verifier"]
    end

    subgraph MemoryVoice ["Memory & Voice Intelligence"]
        RAGMemory["Hybrid Vector Store & User Profile"]
        SpeechService["AEC, ASR, TTS & Speaker Diarization"]
    end

    FlutterApp <-->|WebSocket / REST| MainApp
    MainApp --> WSRoute & ConfigRoute & SpeechRoute
    WSRoute --> Coordinator --> UnifiedProvider
    Coordinator --> SkillRegistry --> SubAgents
    Coordinator --> RAGMemory
    SpeechRoute --> SpeechService
```

For full details regarding multi-agent pipelines, data flows, cryptographic audit logs, and directory layout, please refer to the **[Master Architecture & Workflow Specification](./system_architecture_and_workflow.md)**.
