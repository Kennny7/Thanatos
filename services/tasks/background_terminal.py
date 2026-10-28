# Thanatos/services/tasks/background_terminal.py
"""
Background Terminal Spawner for Windows:
Opens a dedicated real Command Prompt / Terminal window that live-tails
ongoing subagent tasks, compilers, code optimizations, and diagnostics.
"""

import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import Optional

logger = logging.getLogger(__name__)


class BackgroundTerminalSpawner:
    """Spawns and monitors detached background terminal consoles on Windows/Linux."""

    def __init__(self, logs_dir: str = "logs/background_tasks") -> None:
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    def create_log_file(self, task_name: str) -> str:
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in task_name)[:40]
        timestamp = int(time.time())
        log_path = os.path.abspath(os.path.join(self.logs_dir, f"{safe_name}_{timestamp}.log"))
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"=== THANATOS BACKGROUND WORKER LOG ===\nTask: {task_name}\nStarted: {time.ctime()}\n" + "=" * 50 + "\n\n")
        return log_path

    def append_log(self, log_path: str, message: str) -> None:
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")
        except Exception as e:
            logger.debug("Failed writing to background log %s: %s", log_path, e)

    def spawn_terminal_window(self, task_title: str, log_file: str) -> Optional[subprocess.Popen]:
        """
        Open a visible native Windows Command Prompt or Linux terminal window
        running a live real-time tail of the task's execution log.
        """
        if sys.platform == "win32":
            try:
                # PowerShell Get-Content -Wait provides a responsive native live log viewer
                ps_script = f"""
$host.UI.RawUI.WindowTitle = 'Thanatos Subagent Worker: {task_title}'
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ' THANATOS AUTONOMOUS BACKGROUND AGENT WORKSPACE' -ForegroundColor Green
Write-Host ' Task: {task_title}' -ForegroundColor Yellow
Write-Host ' Log:  {log_file}' -ForegroundColor DarkGray
Write-Host '============================================================' -ForegroundColor Cyan
Write-Host ''
Get-Content -Path '{log_file}' -Wait -Tail 20
"""
                temp_ps = os.path.join(tempfile.gettempdir(), f"thanatos_tail_{int(time.time())}.ps1")
                with open(temp_ps, "w", encoding="utf-8") as f:
                    f.write(ps_script)

                cmd = [
                    "powershell.exe",
                    "-NoExit",
                    "-ExecutionPolicy", "Bypass",
                    "-File", temp_ps,
                ]

                # CREATE_NEW_CONSOLE = 0x00000010 opens a separate visible window on Windows
                creation_flags = 0x00000010
                proc = subprocess.Popen(
                    cmd,
                    creationflags=creation_flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info("Spawned background console for task: %s (PID %d)", task_title, proc.pid)
                return proc
            except Exception as e:
                logger.warning("Could not launch Windows CMD console for background task: %s", e)
                return None
        else:
            # Linux / macOS fallback using xterm / gnome-terminal or background tail
            try:
                proc = subprocess.Popen(
                    ["xterm", "-title", f"Thanatos: {task_title}", "-e", "tail", "-f", log_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return proc
            except Exception:
                return None


background_terminal = BackgroundTerminalSpawner()
