# Thanatos/services/background/task_manager.py
"""
Background Task Manager:
Runs long-running tool executions as asyncio background tasks so the main
terminal prompt remains responsive. Provides task tracking, progress
notifications, and a /tasks command interface.

Architecture:
- Tasks run as fire-and-forget asyncio.Tasks
- A notification callback (set by the terminal client) prints updates above the prompt
- Tasks store their results for later retrieval via /tasks view <id>
- The coordinator offloads LONG_RUNNING_TOOLS here instead of blocking
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    """A single tracked background task."""
    id: str
    name: str
    tool_name: str
    args: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    progress_message: str = ""
    result_text: str = ""
    error: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    _asyncio_task: Optional[asyncio.Task] = field(default=None, repr=False)

    @property
    def elapsed_seconds(self) -> float:
        end = self.completed_at or time.time()
        return round(end - self.started_at, 1) if self.started_at else 0.0

    @property
    def elapsed_display(self) -> str:
        secs = self.elapsed_seconds
        if secs < 60:
            return f"{secs:.0f}s"
        mins = int(secs // 60)
        remaining = int(secs % 60)
        return f"{mins}m {remaining}s"


# Tools that are known to take a long time and should be backgrounded automatically
LONG_RUNNING_TOOLS = frozenset({
    "run_malware_scan",
    "run_sfc_scan",
    "run_dism_repair",
})


class BackgroundTaskManager:
    """
    Singleton manager for background tool execution tasks.
    Keeps the main terminal prompt responsive by running long operations
    as asyncio background tasks with notification callbacks.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, BackgroundTask] = {}
        self._counter: int = 0
        self._notification_callback: Optional[Callable[[BackgroundTask, str], None]] = None

    def set_notification_callback(self, callback: Callable[[BackgroundTask, str], None]) -> None:
        """
        Register a callback that the terminal client uses to print notifications.
        callback(task, event_type) where event_type is 'started', 'progress', 'completed', 'failed'
        """
        self._notification_callback = callback

    def _next_id(self) -> str:
        self._counter += 1
        return f"bg-{self._counter}"

    def _notify(self, task: BackgroundTask, event_type: str) -> None:
        if self._notification_callback:
            try:
                self._notification_callback(task, event_type)
            except Exception as e:
                logger.debug("Notification callback error: %s", e)

    def submit(
        self,
        name: str,
        tool_name: str,
        args: Dict[str, Any],
        coroutine: Coroutine,
    ) -> BackgroundTask:
        """
        Submit a coroutine to run as a background task.
        Returns the BackgroundTask immediately (non-blocking).
        The coroutine should return a dict with 'result_text' key.
        """
        task_id = self._next_id()
        task = BackgroundTask(
            id=task_id,
            name=name,
            tool_name=tool_name,
            args=args,
            status=TaskStatus.PENDING,
            started_at=time.time(),
        )
        self._tasks[task_id] = task

        # Schedule as an asyncio task
        asyncio_task = asyncio.create_task(self._run_task(task, coroutine))
        task._asyncio_task = asyncio_task

        task.status = TaskStatus.RUNNING
        task.progress_message = f"Executing {tool_name}..."
        self._notify(task, "started")
        logger.info("Background task %s started: %s (%s)", task_id, name, tool_name)

        return task

    async def _run_task(self, task: BackgroundTask, coroutine: Coroutine) -> None:
        """Execute the task coroutine and handle results/errors."""
        try:
            result = await coroutine

            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

            if isinstance(result, dict):
                task.result_text = result.get("result_text", str(result))
            else:
                task.result_text = str(result)

            self._notify(task, "completed")
            logger.info(
                "Background task %s completed in %s: %s",
                task.id, task.elapsed_display, task.name,
            )

        except asyncio.CancelledError:
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.error = "Task was cancelled."
            self._notify(task, "failed")
            logger.warning("Background task %s cancelled: %s", task.id, task.name)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = time.time()
            task.error = str(e)
            self._notify(task, "failed")
            logger.exception("Background task %s failed: %s", task.id, e)

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[BackgroundTask]:
        """List all tasks, optionally filtered by status. Most recent first."""
        tasks = list(self._tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        return sorted(tasks, key=lambda t: t.started_at, reverse=True)

    def running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running background task."""
        task = self._tasks.get(task_id)
        if task and task._asyncio_task and not task._asyncio_task.done():
            task._asyncio_task.cancel()
            return True
        return False

    def clear_completed(self) -> int:
        """Remove completed/failed tasks from the list. Returns count removed."""
        to_remove = [
            tid for tid, t in self._tasks.items()
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        ]
        for tid in to_remove:
            del self._tasks[tid]
        return len(to_remove)

    def is_tool_long_running(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a tool should be automatically backgrounded."""
        if tool_name in LONG_RUNNING_TOOLS:
            return True

        # run_system_command is long-running if admin_required or timeout > 120s
        if tool_name == "run_system_command" and args:
            if args.get("admin_required", False):
                return True
            if int(args.get("timeout_seconds", 180)) > 300:
                return True

        return False


# Module-level singleton
task_manager = BackgroundTaskManager()
