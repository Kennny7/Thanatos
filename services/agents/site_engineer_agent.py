# Thanatos/services/agents/site_engineer_agent.py
"""
Knowledge Curator & Systems Specialist Persona: Velma Sinclair.
Combines:
- Bookworm & knowledge bank capabilities (primary persona)
- System diagnostics & telemetry (retained technical capabilities)
- Error triage, self-correction detection, and patch recommendation
- Private diagnostic notes and reading logs

System prompt is now generated dynamically via TraitEngine + DynamicPromptBuilder.
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


class SystemDiagnostics(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    platform: str
    cpu_percent: float
    cpu_count: int
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    battery_status: Optional[str] = None
    open_network_connections: int = 0
    top_processes: List[Dict[str, Any]] = Field(default_factory=list)


class SiteEngineerAgent:
    """
    Velma Sinclair — Knowledge Curator & Systems Specialist:
    - Primary: Shy, bookish knowledge bank. Voracious reader and researcher.
    - Secondary: Retains system diagnostics, telemetry, and Docker management.
    - Tracks private diagnostic notes and reading discoveries.
    - Runs deep system health checks and self-repair analyses.
    - System prompt generated dynamically via RL TraitEngine.
    """

    def __init__(self, agent_id: str = "site_engineer") -> None:
        self.agent_id = agent_id
        entry = roster.get_agent_index_entry(agent_id)
        self.storage_dir = entry.memory_partition if entry else os.path.join("data", "agent_memory", "site_engineer")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.notes_file = os.path.join(self.storage_dir, "engineer_notes.json")
        self.reading_log_file = os.path.join(self.storage_dir, "reading_log.json")
        self.notes: List[Dict[str, Any]] = self._load_notes()
        self.reading_log: List[Dict[str, Any]] = self._load_reading_log()

    def get_profile(self):
        """Loads only this agent's dedicated JSON profile on-demand."""
        return roster.load_agent_profile(self.agent_id)

    def build_system_prompt(self, extra_context: str = "", growth_summary: str = "", recent_dialogue: str = "") -> str:
        """
        Generate system prompt dynamically from live trait vector.
        Uses 'librarian' persona from the trait engine (legacy ID mapping).
        """
        from services.agents.dynamic_prompt_builder import prompt_builder
        return prompt_builder.build_system_prompt(
            agent_id=self.agent_id,
            extra_context=extra_context,
            growth_summary=growth_summary,
            recent_dialogue=recent_dialogue,
        )

    def _load_notes(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.notes_file):
            return []
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed loading engineer notes: %s", e)
            return []

    def _save_notes(self) -> None:
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, indent=2)
        except Exception as e:
            logger.error("Failed saving engineer notes: %s", e)

    def _load_reading_log(self) -> List[Dict[str, Any]]:
        """Load Velma's reading discoveries and book notes."""
        if not os.path.exists(self.reading_log_file):
            return []
        try:
            with open(self.reading_log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed loading reading log: %s", e)
            return []

    def _save_reading_log(self) -> None:
        try:
            with open(self.reading_log_file, "w", encoding="utf-8") as f:
                json.dump(self.reading_log, f, indent=2)
        except Exception as e:
            logger.error("Failed saving reading log: %s", e)

    def log_reading(self, title: str, author: str = "", category: str = "General",
                    notes: str = "", rating: Optional[float] = None) -> Dict[str, Any]:
        """Log a book, article, or research paper to Velma's reading collection."""
        entry = {
            "id": f"read_{int(time.time())}_{len(self.reading_log)}",
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "title": title,
            "author": author,
            "category": category,
            "notes": notes,
            "rating": rating,
        }
        self.reading_log.append(entry)
        self._save_reading_log()
        return entry

    def get_reading_log(self, limit: int = 20, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent readings, optionally filtered by category."""
        entries = self.reading_log
        if category:
            entries = [e for e in entries if e.get("category", "").lower() == category.lower()]
        return entries[-limit:]

    def collect_system_telemetry(self) -> Dict[str, Any]:
        """Collect real-time CPU, RAM, Disk, and Process Metrics."""
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        
        # Get top 5 CPU/memory processes
        procs = []
        try:
            for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                            key=lambda x: (x.info.get('cpu_percent') or 0) + (x.info.get('memory_percent') or 0),
                            reverse=True)[:5]:
                procs.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "cpu_pct": p.info['cpu_percent'],
                    "mem_pct": round(p.info['memory_percent'] or 0, 1),
                })
        except Exception:
            pass

        diag = SystemDiagnostics(
            platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
            cpu_percent=psutil.cpu_percent(interval=0.2),
            cpu_count=psutil.cpu_count(logical=True) or 1,
            memory_total_gb=round(vm.total / (1024**3), 2),
            memory_used_gb=round(vm.used / (1024**3), 2),
            memory_percent=vm.percent,
            disk_total_gb=round(disk.total / (1024**3), 2),
            disk_used_gb=round(disk.used / (1024**3), 2),
            disk_percent=disk.percent,
            top_processes=procs,
        )
        return diag.model_dump()

    def record_engineer_note(self, title: str, content: str, tag: str = "Optimization") -> Dict[str, Any]:
        """Log a private diagnostic observation, fix, or performance note."""
        entry = {
            "id": f"note_{int(time.time())}_{len(self.notes)}",
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": tag,
            "title": title,
            "content": content,
        }
        self.notes.append(entry)
        self._save_notes()
        return entry

    def get_engineer_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.notes[-limit:]

    def check_port_conflicts(self, target_ports: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Scans system to check if database or gateway ports are blocked by host processes."""
        ports = target_ports or [5432, 5436, 8000, 7474, 7687, 9092, 11434, 19530, 27017, 27018]
        conflicts = []
        try:
            for conn in psutil.net_connections(kind="inet"):
                if conn.status == "LISTEN" and conn.laddr and conn.laddr.port in ports:
                    pname = "unknown"
                    try:
                        p = psutil.Process(conn.pid)
                        pname = p.name()
                    except Exception:
                        pass
                    conflicts.append({
                        "port": conn.laddr.port,
                        "pid": conn.pid,
                        "process": pname,
                    })
        except Exception as e:
            logger.debug("Port scan check note: %s", e)
        return conflicts

    def launch_docker_desktop(self) -> Dict[str, Any]:
        """Launch the Docker Desktop application on the host machine."""
        from services.database.db_orchestrator import db_orchestrator
        return db_orchestrator.start_docker_desktop()

    def wait_for_docker_ready(self, timeout_sec: int = 90, status_callback=None) -> bool:
        """Poll until Docker Desktop engine finishes booting."""
        from services.database.db_orchestrator import db_orchestrator
        return db_orchestrator.wait_for_docker(timeout_sec=timeout_sec, status_callback=status_callback)

    def auto_manage_docker(self, action: str = "ensure", start_if_stopped: bool = False, status_callback=None) -> Dict[str, Any]:
        """
        Velma's automated Docker supervisor:
        Checks if Docker daemon is running, identifies port conflicts,
        starts Docker Desktop if requested, and deploys enterprise database containers.
        """
        from services.database.db_orchestrator import db_orchestrator
        is_avail = db_orchestrator.is_docker_available()

        if not is_avail and start_if_stopped:
            if status_callback:
                status_callback("Launching Docker Desktop engine in background...")
            launch_res = db_orchestrator.start_docker_desktop()
            if not launch_res.get("success"):
                return {
                    "running": False,
                    "error": launch_res.get("message") or launch_res.get("error"),
                    "message": "Couldn't locate or launch Docker Desktop automatically. Standing by on embedded local storage."
                }
            
            # Wait for docker engine to come alive
            ready = db_orchestrator.wait_for_docker(
                timeout_sec=90,
                poll_interval_sec=3.0,
                status_callback=lambda elapsed, total: status_callback(f"Docker Desktop initializing... ({elapsed}s/{total}s)") if status_callback else None
            )
            is_avail = ready

        if not is_avail:
            has_exe = bool(db_orchestrator.get_docker_desktop_executable())
            return {
                "running": False,
                "can_launch": has_exe,
                "message": "Docker Desktop is currently stopped. I can launch Docker Desktop and bring up your database cluster automatically, or stand by on local embedded storage."
            }

        conflicts = self.check_port_conflicts([5436, 27018, 19530, 7474, 9092])
        if action == "ensure":
            if status_callback:
                status_callback("Starting database containers (Postgres, Mongo, Milvus, Neo4j, Kafka)...")
            res = db_orchestrator.ensure_containers_running()
            statuses = db_orchestrator.get_container_status()
            return {
                "running": True,
                "orchestrator_result": res,
                "containers": statuses,
                "port_conflicts": conflicts,
                "message": "All enterprise database & streaming containers (Postgres, Mongo, Milvus, Neo4j, Kafka) are operational with storage mounted in data/docker_storage/."
            }
        elif action == "status":
            return {
                "running": True,
                "containers": db_orchestrator.get_container_status(),
                "port_conflicts": conflicts,
            }
        elif action == "stop":
            return db_orchestrator.stop_containers()

        return {"running": is_avail}

    def verify_llm_claim(self, claimed_action: str, tool_calls_made: list, tool_results: list) -> Dict[str, Any]:
        """
        Autonomous verification watchdog:
        Cross-checks what the LLM claims it did against actual tool calls and results.
        Returns a verification report that flags hallucinated or unsubstantiated claims.
        """
        verification = {
            "verified": True,
            "claimed_action": claimed_action,
            "actual_tools_called": [tc.get("name", "unknown") for tc in tool_calls_made] if tool_calls_made else [],
            "warnings": [],
            "diagnosis": "",
        }

        lower_claim = claimed_action.lower()

        # Patterns that indicate substantive system actions
        action_patterns = {
            "scan": ["run_malware_scan", "run_sfc_scan", "run_system_command"],
            "malware": ["run_malware_scan", "run_system_command"],
            "sfc": ["run_sfc_scan", "run_system_command"],
            "dism": ["run_dism_repair", "run_system_command"],
            "disk": ["check_disk_health", "run_system_command"],
            "update": ["check_windows_updates", "run_system_command"],
            "repair": ["run_sfc_scan", "run_dism_repair", "run_system_command"],
            "install": ["manage_system_package", "run_system_command"],
            "uninstall": ["manage_system_package", "run_system_command"],
            "creating tool": ["create_and_register_skill"],
            "building tool": ["create_and_register_skill"],
            "registering": ["create_and_register_skill"],
        }

        tools_called_names = verification["actual_tools_called"]

        for keyword, required_tools in action_patterns.items():
            if keyword in lower_claim:
                if not any(rt in tools_called_names for rt in required_tools):
                    verification["verified"] = False
                    verification["warnings"].append(
                        f"Claimed '{keyword}' action but none of the required tools "
                        f"({', '.join(required_tools)}) were actually invoked."
                    )

        # Check for fake progress indicators
        fake_progress_markers = [
            "in progress", "is running", "scanning now", "creating 8",
            "building 8", "step 1:", "step 2:", "tool creation in progress",
        ]
        if any(marker in lower_claim for marker in fake_progress_markers):
            if not tool_calls_made:
                verification["verified"] = False
                verification["warnings"].append(
                    "Response contains progress indicators but no tools were actually called. "
                    "This is likely hallucinated progress."
                )

        # Check for failed tools being reported as success
        if tool_results:
            for result in tool_results:
                if isinstance(result, dict) and not result.get("success", True):
                    if "success" in lower_claim or "completed" in lower_claim:
                        verification["verified"] = False
                        verification["warnings"].append(
                            f"Tool returned failure but response claims success: {result.get('error', 'unknown error')}"
                        )

        if verification["verified"]:
            verification["diagnosis"] = "All claimed actions are substantiated by actual tool executions."
        else:
            verification["diagnosis"] = (
                f"HALLUCINATION DETECTED: {len(verification['warnings'])} unsubstantiated claim(s). "
                "The LLM response should not be shown to the user as-is."
            )
            logger.warning(
                "Velma verification failed for claim '%s': %s",
                claimed_action[:80],
                "; ".join(verification["warnings"]),
            )

        return verification


site_engineer_agent = SiteEngineerAgent()
