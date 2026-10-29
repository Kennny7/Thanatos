# Thanatos/services/agents/tech_prodigy_agent.py
"""
Technical Systems Architect Persona: Pip Ashworth.
An extraordinarily intelligent child in the realm of technology.
Innocent, curious, chubby, short — but with a mind that can dissect
system architectures, spot security loopholes, and understand
complex codebases with startling clarity.

Pip manages the technical subagents (Developer, Crawler, Doc Writer)
and coordinates code-related tasks across the agent team.
"""

import json
import logging
import os
import platform
import psutil
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from services.agents.agent_roster import roster

logger = logging.getLogger(__name__)


class CodeAgentTask(BaseModel):
    """Tracks a task delegated to a code-related subagent."""
    task_id: str
    subagent: str  # "developer", "crawler", "doc_writer"
    description: str
    status: str = "pending"  # pending, running, completed, failed
    result_summary: str = ""
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None


class TechProdigyAgent:
    """
    Pip Ashworth — Technical Systems Architect:
    - Extremely intelligent child persona with innocent curiosity.
    - Primary technical brain: system architecture, security, code review.
    - Manages code-related subagents (Developer, Crawler, Doc Writer).
    - Inherited system diagnostics and Docker management capabilities.
    - System prompt generated dynamically via RL TraitEngine.
    """

    def __init__(self, agent_id: str = "tech_prodigy") -> None:
        self.agent_id = agent_id
        entry = roster.get_agent_index_entry(agent_id)
        storage_dir = entry.memory_partition if entry else os.path.join("data", "agent_memory", "tech_prodigy")
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.notes_file = os.path.join(self.storage_dir, "tech_notes.json")
        self.discoveries_file = os.path.join(self.storage_dir, "discoveries.json")
        self.delegated_tasks_file = os.path.join(self.storage_dir, "delegated_tasks.json")
        self.notes: List[Dict[str, Any]] = self._load_json(self.notes_file)
        self.discoveries: List[Dict[str, Any]] = self._load_json(self.discoveries_file)
        self.delegated_tasks: List[CodeAgentTask] = self._load_delegated_tasks()

    def get_profile(self):
        """Loads only Pip's dedicated JSON profile on-demand."""
        return roster.load_agent_profile(self.agent_id)

    def build_system_prompt(self, extra_context: str = "", growth_summary: str = "", recent_dialogue: str = "") -> str:
        """Generate system prompt dynamically from live trait vector."""
        from services.agents.dynamic_prompt_builder import prompt_builder
        return prompt_builder.build_system_prompt(
            agent_id=self.agent_id,
            extra_context=extra_context,
            growth_summary=growth_summary,
            recent_dialogue=recent_dialogue,
        )

    def _load_json(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed loading %s: %s", path, e)
            return []

    def _save_json(self, path: str, data: List) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed saving %s: %s", path, e)

    # ------------------------------------------------------------------
    # Code Agent Management
    # ------------------------------------------------------------------

    def _load_delegated_tasks(self) -> List[CodeAgentTask]:
        if not os.path.exists(self.delegated_tasks_file):
            return []
        try:
            with open(self.delegated_tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [CodeAgentTask(**item) for item in data]
        except Exception as e:
            logger.error("Failed loading delegated tasks: %s", e)
            return []

    def _save_delegated_tasks(self) -> None:
        self._save_json(
            self.delegated_tasks_file,
            [t.model_dump() for t in self.delegated_tasks],
        )

    def delegate_to_subagent(
        self,
        subagent: str,
        description: str,
    ) -> CodeAgentTask:
        """
        Pip delegates a task to one of his code subagents.
        This records the delegation for tracking and potential follow-up.
        """
        task = CodeAgentTask(
            task_id=f"task_{int(time.time())}_{len(self.delegated_tasks)}",
            subagent=subagent,
            description=description,
        )
        self.delegated_tasks.append(task)
        self._save_delegated_tasks()

        from services.agents.agent_bus import agent_bus
        agent_bus.post_message(
            sender="Pip Ashworth",
            recipient=f"{subagent.title()} Subagent",
            content=f"Hey! I need you to do something for me: {description[:100]}",
            topic_tags=["delegation", subagent],
        )
        return task

    def complete_subagent_task(
        self,
        task_id: str,
        result_summary: str,
        success: bool = True,
    ) -> Optional[CodeAgentTask]:
        """Record a subagent task as completed with results."""
        for task in self.delegated_tasks:
            if task.task_id == task_id:
                task.status = "completed" if success else "failed"
                task.result_summary = result_summary[:500]
                task.completed_at = time.time()
                self._save_delegated_tasks()
                return task
        return None

    def get_active_delegations(self) -> List[Dict[str, Any]]:
        """Get all currently active (pending/running) delegated tasks."""
        return [
            t.model_dump() for t in self.delegated_tasks
            if t.status in ("pending", "running")
        ]

    def get_delegation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent delegation history."""
        return [t.model_dump() for t in self.delegated_tasks[-limit:]]

    # ------------------------------------------------------------------
    # Technical Knowledge & Discovery
    # ------------------------------------------------------------------

    def record_discovery(self, title: str, content: str, category: str = "Architecture") -> Dict[str, Any]:
        """Log a technical discovery, loophole, or architectural insight."""
        entry = {
            "id": f"discovery_{int(time.time())}_{len(self.discoveries)}",
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "title": title,
            "content": content,
        }
        self.discoveries.append(entry)
        self._save_json(self.discoveries_file, self.discoveries)
        return entry

    def get_discoveries(self, limit: int = 20, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent technical discoveries."""
        entries = self.discoveries
        if category:
            entries = [e for e in entries if e.get("category", "").lower() == category.lower()]
        return entries[-limit:]

    def record_tech_note(self, title: str, content: str, tag: str = "Security") -> Dict[str, Any]:
        """Log a technical observation or finding."""
        entry = {
            "id": f"note_{int(time.time())}_{len(self.notes)}",
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": tag,
            "title": title,
            "content": content,
        }
        self.notes.append(entry)
        self._save_json(self.notes_file, self.notes)
        return entry

    def get_tech_notes(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.notes[-limit:]

    # ------------------------------------------------------------------
    # System Diagnostics (inherited capabilities)
    # ------------------------------------------------------------------

    def collect_system_telemetry(self) -> Dict[str, Any]:
        """Collect real-time system metrics — inherited technical capability."""
        from services.agents.site_engineer_agent import site_engineer_agent
        return site_engineer_agent.collect_system_telemetry()

    def check_port_conflicts(self, target_ports: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Scan for port conflicts — inherited technical capability."""
        from services.agents.site_engineer_agent import site_engineer_agent
        return site_engineer_agent.check_port_conflicts(target_ports)

    def auto_manage_docker(self, action: str = "ensure", start_if_stopped: bool = False, status_callback=None) -> Dict[str, Any]:
        """Docker management — inherited technical capability."""
        from services.agents.site_engineer_agent import site_engineer_agent
        return site_engineer_agent.auto_manage_docker(action, start_if_stopped, status_callback)


tech_prodigy_agent = TechProdigyAgent()
