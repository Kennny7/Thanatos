# Thanatos/services/agents/site_engineer_agent.py
"""
Site Engineer & Systems Architect Persona: Velma Sinclair.
Specializes in:
- System diagnostics & telemetry (CPU, RAM, GPU, Disks, Networks, Processes)
- Error triage, self-correction detection, and patch recommendation
- Private hardware benchmarks and optimization notes
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
    Autonomous Site Reliability & Systems Engineer:
    - Personality: Charming, willful, brilliant young female engineer with glasses.
    - Tracks private diagnostic notes and optimization observations.
    - Runs deep system health checks and self-repair analyses.
    """

    def __init__(self, agent_id: str = "site_engineer") -> None:
        self.agent_id = agent_id
        entry = roster.get_agent_index_entry(agent_id)
        self.storage_dir = entry.memory_partition if entry else os.path.join("data", "agent_memory", "site_engineer")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.notes_file = os.path.join(self.storage_dir, "engineer_notes.json")
        self.notes: List[Dict[str, Any]] = self._load_notes()

    def get_profile(self):
        """Loads only this agent's dedicated JSON profile on-demand."""
        return roster.load_agent_profile(self.agent_id)

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

    def build_system_prompt(self) -> str:
        prof = self.get_profile()
        name = prof.name if prof else "Velma Sinclair"
        personality = prof.personality if prof else "Charming, willful young systems engineer with glasses."
        traits_list = f"\nKey Traits: {', '.join(prof.traits)}" if prof and prof.traits else ""
        return f"""You are {name}, the Site Reliability & Systems Engineer of Thanatos.
Personality: {personality}{traits_list}
Voice & Tone: Energetic, highly competent, playful banter, candid about errors, never sugarcoating bad code, loves clean architecture and high-FPS performance.
You excel at checking CPU, RAM, background threads, and automatically diagnosing syntax, regex, or runtime errors before they reach production.
Always provide crisp, technical diagnoses while maintaining your charming and assertive personality."""


site_engineer_agent = SiteEngineerAgent()
