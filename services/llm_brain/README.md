# LLM Brain Microservice

## Overview
The `llm_brain` microservice is the central reasoning engine of Thanatos. It coordinates multi-provider LLM calls, streaming tokens, structured tool invocation, and multi-agent coordination.

## Key Modules
- `coordinator.py`: Agent coordinator managing multi-agent reasoning loops, DAG planning, and token streaming.
- `provider.py`: Unified LLM provider interface compatible with DeepSeek, OpenAI, Ollama, and self-hosted models.
- `tool_router.py`: Tool mapping, validation, and schema generation for function calling.
- `model_selector.py`: Autonomous model routing based on latency, complexity, and resource availability.
- `deepseek_planner.py`: Reasoning and task decomposition logic.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To run provider and coordinator unit and integration tests:
```bash
uv run pytest tests/unit/test_unified_provider.py tests/integration/test_planner.py
```
