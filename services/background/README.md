# Background Microservice

## Overview
The `background` microservice manages asynchronous background jobs, scheduled tasks, and long-running daemon operations outside the main conversational loop.

## Key Modules
- `task_manager.py`: Autonomous task supervisor responsible for scheduling, priority management, state persistence, and error recovery.

## Installation & Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To test the background task manager in isolation:
```bash
uv run python -c "from services.background.task_manager import BackgroundTaskManager; tm = BackgroundTaskManager(); print('Task manager operational')"
```
