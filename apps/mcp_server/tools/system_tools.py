# Thanatos\apps\mcp_server\tools\system_tools.py

"""
System tools for the Thanatos MCP server.
Provides system information, process management, and safe shell execution.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Optional dependency for richer process & system data
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# Optional integration with Thanatos audit system
try:
    from audit.audit_logger import AuditLogger  # type: ignore[import-untyped]
    _AUDIT = True
except ImportError:
    _AUDIT = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _run_in_executor(func, *args, **kwargs):
    """Run a synchronous function in a thread pool to keep the event loop free."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


def _audit(action: str, details: Dict[str, Any]) -> None:
    """Send an audit entry if the audit module is available."""
    if _AUDIT:
        try:
            AuditLogger.log(action, details)
        except Exception:
            logger.exception("Audit logging failed")


# ---------------------------------------------------------------------------
# System information
# ---------------------------------------------------------------------------
async def get_system_info() -> Dict[str, Any]:
    """Collect detailed system information (OS, CPU, memory, disk, network)."""
    info: Dict[str, Any] = {
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
    }

    if _PSUTIL:
        try:
            info["cpu_count"] = {
                "physical": psutil.cpu_count(logical=False),
                "logical": psutil.cpu_count(logical=True),
            }
            info["cpu_usage_percent"] = psutil.cpu_percent(interval=0.1)

            mem = psutil.virtual_memory()
            info["memory"] = {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_percent": mem.percent,
            }

            swap = psutil.swap_memory()
            info["swap"] = {
                "total_gb": round(swap.total / (1024**3), 2),
                "used_gb": round(swap.used / (1024**3), 2),
                "percent": swap.percent,
            }

            # Disk usage for all mounted partitions
            disk_info = {}
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_info[part.mountpoint] = {
                        "device": part.device,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent,
                    }
                except PermissionError:
                    disk_info[part.mountpoint] = {"error": "permission denied"}
            info["disks"] = disk_info

            info["boot_time"] = psutil.boot_time()
            info["uptime_seconds"] = int(asyncio.get_event_loop().time() - psutil.boot_time())

            # Network I/O counters
            net_io = psutil.net_io_counters()
            info["network_io"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }

            # Active network connections summary
            connections = psutil.net_connections(kind='inet')
            info["active_connections"] = len(connections)

        except Exception as exc:
            logger.warning("psutil failed for system info: %s", exc)
    else:
        # Fallback without psutil
        try:
            disk_usage = shutil.disk_usage("/")
            info["disks"] = {"/": {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
            }}
        except Exception:
            info["disks"] = {"error": "unavailable"}

    _audit("get_system_info", {"success": True})
    return info


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------
async def list_processes(name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return a list of running processes, optionally filtered by name.
    Requires psutil.
    """
    if not _PSUTIL:
        raise RuntimeError("psutil is required for process listing")

    def _list() -> List[Dict[str, Any]]:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if name_filter and name_filter.lower() not in pinfo['name'].lower():
                    continue
                pinfo['cpu_percent'] = proc.cpu_percent(interval=0.0)  # non-blocking
                pinfo['memory_percent'] = proc.memory_percent()
                procs.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

    result = await _run_in_executor(_list)
    _audit("list_processes", {"filter": name_filter})
    return result


async def kill_process(pid: int, force: bool = False) -> str:
    """
    Terminate a process by PID. If force is True, use SIGKILL (non-Windows)
    or TerminateProcess on Windows.
    """
    if not _PSUTIL:
        raise RuntimeError("psutil is required for process management")

    def _kill():
        proc = psutil.Process(pid)
        if force:
            proc.kill()
        else:
            proc.terminate()
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait()

    await _run_in_executor(_kill)
    _audit("kill_process", {"pid": pid, "force": force})
    return f"Process {pid} terminated successfully."


# ---------------------------------------------------------------------------
# Shell command execution (sandboxed)
# ---------------------------------------------------------------------------
async def execute_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a shell command in a subprocess and capture stdout/stderr.
    For security, the command is run via `shlex.split` and never with shell=True.
    """
    args = shlex.split(command)
    logger.info("Executing command: %s", args)

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out and was killed.",
            }

        result = {
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except FileNotFoundError as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command not found: {e}",
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }

    _audit("execute_command", {"command": command, "returncode": result["returncode"]})
    return result


# ---------------------------------------------------------------------------
# File system operations (safe wrappers)
# ---------------------------------------------------------------------------
async def list_directory(path: str = ".") -> List[Dict[str, Any]]:
    """List files and directories in a given path."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    if not p.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    items = []
    for entry in p.iterdir():
        try:
            stat = entry.stat()
            items.append({
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
                "size_bytes": stat.st_size if entry.is_file() else 0,
                "modified": stat.st_mtime,
            })
        except PermissionError:
            items.append({"name": entry.name, "type": "unknown", "error": "permission denied"})
    return items


async def read_file(path: str, max_size_kb: int = 1024) -> str:
    """Read the content of a text file, limited to max_size_kb KB."""
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    size_limit = max_size_kb * 1024
    file_size = p.stat().st_size
    if file_size > size_limit:
        raise ValueError(f"File too large ({file_size} bytes). Max allowed: {size_limit} bytes.")

    content = await _run_in_executor(p.read_text, encoding="utf-8", errors="replace")
    return content


# ---------------------------------------------------------------------------
# Screenshot capture (optional)
# ---------------------------------------------------------------------------
async def take_screenshot(save_path: Optional[str] = None) -> str:
    """
    Capture the primary screen and save as PNG. Requires pyautogui.
    Returns the file path or base64-encoded image data.
    """
    try:
        import pyautogui
        import base64
        from io import BytesIO
    except ImportError:
        raise RuntimeError("pyautogui is required for screenshot capture. Install with: pip install pyautogui pillow")

    img = await _run_in_executor(pyautogui.screenshot)
    if save_path:
        path = Path(save_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        await _run_in_executor(img.save, str(path))
        return f"Screenshot saved to {path}"
    else:
        # Return as base64 data URI
        buffer = BytesIO()
        await _run_in_executor(img.save, buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{b64}"