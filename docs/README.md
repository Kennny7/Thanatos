# Documentation Overview and Sitemap

Welcome to the Thanatos System Documentation. Thanatos is an autonomous, self-optimizing multi-agent reinforcement learning intelligence platform organized as a modular microservice architecture.

This documentation suite is organized into role-tailored subcategories so that both technical contributors and non-technical stakeholders can navigate and learn how each capability operates.

## Subdirectory Structure

### 1. [Architecture](./architecture/)
System-wide architectural principles, multi-agent coordination loops, actor-critic feedback, and interaction topologies.
- [High-Level Architecture](./architecture/architecture.md): Overview of components, security boundaries, and modular microservices.
- [Agents Architecture](./architecture/agents_architecture.md): Specialization, personas (Butler, Tech Prodigy, Project Manager, Secretary, Site Engineer), and dynamic prompt building.
- [System Architecture and Workflow](./architecture/system_architecture_and_workflow.md): Complete end-to-end execution flow, WebSocket contracts, and task dispatching.

### 2. [Getting Started](./getting_started/)
Step-by-step guides for installing, configuring, running, and testing Thanatos on Windows and Linux.
- [Getting Started Guide](./getting_started/getting_started.md): Installation prerequisites, UV virtual environment setup, configuration options, and running local models.
- [Beginner Setup Guide](./getting_started/setup_guide_for_beginners.md): Detailed walkthrough for newcomers, step-by-step terminal instructions, and troubleshooting.

### 3. [Services & Storage](./services/)
Core data persistence, hybrid memory hierarchies, and vector storage microservices.
- [Memory and RAG System](./services/memory_and_rag.md): Multi-tier episodic and semantic memory architectures, retrieval augmented generation, and context injection.
- [Vector Database Setup](./services/vector_database_setup.md): Milvus Lite and ChromaDB vector indexing, failover mechanisms, and automated scaling thresholds.
- [Database Infrastructure](./services/database_infrastructure.md): PostgreSQL relational persistence and MongoDB document store cluster orchestration.

### 4. [Voice & Multimodal](./voice_and_multimodal/)
Low-latency real-time voice, vision verification, and audio processing subsystems.
- [Speech Intelligence](./voice_and_multimodal/speech_intelligence.md): Local Text-to-Speech (TTS), Speech-to-Text (STT), Acoustic Echo Cancellation (AEC), and barge-in handling.
- [Voice Mode and Speaker Verification](./voice_and_multimodal/voice_mode_speaker_verification.md): Acoustic biometric enrollment, speaker identification, and multimodal facial verification.

### 5. [Mesh & Deployment](./mesh_and_deployment/)
Distributed edge compute, mesh networking, container sandboxing, and security policies.
- [Production Deployment](./mesh_and_deployment/production_deployment.md): Docker Compose, enterprise scaling clusters, and background daemons.
- [Security and Network Policies](./mesh_and_deployment/security_and_network.md): Zero-trust boundaries, local network communication, and permission rings.
- [Security Model](./mesh_and_deployment/security_model.md): Cryptographic audit chains, process confinement, and input sanitization.

### 6. [Developer Guides & Tooling](./developers/)
Comprehensive technical specifications for developers extending the system.
- [API Specification](./developers/api_spec.md): REST endpoints, WebSocket streaming event schemas, and payload specifications.
- [MCP Server Integration](./developers/mcp_server.md): Model Context Protocol bridge enabling external tool access and cross-system interop.
- [Plugin Development Guide](./developers/plugin_dev_guide.md): How to create custom skills, dynamic skill generation, and tool registration.
- [Dependency Management](./developers/dependency_management.md): Deterministic package management with `uv` and pyproject configuration.
- [Contributing Guidelines](./developers/contributing.md): Contribution guidelines, testing standards, and pull request verification.
- [Future Vision & Roadmap](./developers/future_vision_roadmap.md): Strategic roadmap for autonomous self-optimization and distributed agent swarms.
