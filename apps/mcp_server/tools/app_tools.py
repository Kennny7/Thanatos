# Thanatos\apps\mcp_server\tools\app_tools.py

"""
Application tools for the Thanatos MCP server.
Provides opening, closing, listing, and focusing applications.
"""

from __future__ import annotations

import asyncio
import logging
import platform
import subprocess
from typing import Dict, Any, List, Optional

# Optional integration with Thanatos os_automation services
try:
    from services.os_automation.process_manager import ProcessManager  # type: ignore[import-untyped]
    from services.os_automation.system_control import SystemControl  # type: ignore[import-untyped]
    _OS_AUTO = True
except ImportError:
    _OS_AUTO = False

logger = logging.getLogger(__name__)

_SYSTEM = platform.system()


async def _run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


# ---------------------------------------------------------------------------
# Application launching
# ---------------------------------------------------------------------------
async def open_application(app_name: str, app_path: str = "") -> str:
    """
    Launch an application by name or executable path.
    Uses the Thanatos process manager if available, otherwise falls back to OS commands.
    """
    target = app_path.strip() or app_name.strip()
    if not target:
        raise ValueError("Either app_name or app_path must be provided.")

    if _OS_AUTO:
        # Use Thanatos's robust process manager
        pm = ProcessManager()
        await _run_in_executor(pm.launch, target)
        return f"Application '{target}' launched via Thanatos ProcessManager."
    else:
        # Fallback OS-specific launching
        try:
            if _SYSTEM == "Windows":
                cmd = ["cmd", "/c", "start", "", target]
            elif _SYSTEM == "Darwin":
                cmd = ["open", "-a", target] if not app_path else ["open", target]
            else:  # Linux
                cmd = ["xdg-open", target]

            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.wait()
            return f"Application '{target}' launched successfully ({_SYSTEM})."
        except FileNotFoundError:
            # Fallback: try running the target directly
            try:
                proc = await asyncio.create_subprocess_exec(target)
                await proc.wait()
                return f"Application '{target}' executed directly (fallback)."
            except Exception as e2:
                raise RuntimeError(f"Failed to launch '{target}': {e2}") from e2

# ---------------------------------------------------------------------------
# Application closing / killing
# ---------------------------------------------------------------------------
async def close_application(app_name: str, force: bool = False) -> str:
    """
    Close an application by name. On macOS/Linux tries graceful close first.
    If force is True, kills the process unconditionally.
    """
    if _OS_AUTO:
        pm = ProcessManager()
        await _run_in_executor(pm.terminate_by_name, app_name, force)
        return f"Application '{app_name}' {'forcefully' if force else 'gracefully'} closed via ProcessManager."
    else:
        # OS-specific fallback
        if _SYSTEM == "Windows":
            kill_cmd = ["taskkill", "/IM", app_name]
            if force:
                kill_cmd.append("/F")
        elif _SYSTEM == "Darwin":
            kill_cmd = ["pkill", "-f", app_name] if force else ["osascript", "-e",
                         f'tell application "{app_name}" to quit']
        else:  # Linux
            kill_cmd = ["pkill", "-f", app_name] if force else ["pkill", "-SIGTERM", "-f", app_name]

        try:
            proc = await asyncio.create_subprocess_exec(*kill_cmd)
            await proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"Command returned code {proc.returncode}")
            return f"Application '{app_name}' closed."
        except Exception as e:
            raise RuntimeError(f"Failed to close '{app_name}': {e}") from e


# ---------------------------------------------------------------------------
# List running applications (GUI windows)
# ---------------------------------------------------------------------------
async def list_running_apps() -> List[Dict[str, Any]]:
    """
    Return a list of visible GUI applications with window titles.
    Requires psutil on Linux/macOS or tasklist on Windows.
    """
    apps = []
    if _SYSTEM == "Windows":
        try:
            output = subprocess.check_output(["tasklist", "/fo", "csv", "/nh"], text=True)
            for line in output.strip().splitlines():
                parts = line.split('","')
                if len(parts) >= 2:
                    apps.append({"name": parts[0].strip('"'), "pid": int(parts[1].strip('"'))})
        except Exception:
            pass
    else:
        # Try wmctrl for X11 or JXA for macOS
        if _SYSTEM == "Darwin":
            try:
                script = 'tell application "System Events" to get name of every process whose visible is true'
                proc = await asyncio.create_subprocess_exec("osascript", "-e", script,
                                                            stdout=asyncio.subprocess.PIPE)
                stdout, _ = await proc.communicate()
                names = stdout.decode().strip().split(", ")
                apps = [{"name": n} for n in names if n]
            except Exception:
                pass
        else:
            try:
                output = subprocess.check_output(["wmctrl", "-l"], text=True)
                for line in output.strip().splitlines():
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        apps.append({"window_id": parts[0], "title": parts[3]})
            except Exception:
                pass

    if not apps:
        apps.append({"warning": "Could not enumerate GUI apps. Install wmctrl (Linux) or tasklist (Windows)."})
    return apps


# ---------------------------------------------------------------------------
# Window focus / keyboard input
# ---------------------------------------------------------------------------
async def focus_window(window_title: str) -> str:
    """Bring a window to front by its title. Requires wmctrl (Linux) or AppleScript (macOS)."""
    if _SYSTEM == "Darwin":
        script = f'tell application "System Events" to set frontmost of process "{window_title}" to true'
        proc = await asyncio.create_subprocess_exec("osascript", "-e", script)
        await proc.wait()
    elif _SYSTEM == "Linux":
        try:
            subprocess.run(["wmctrl", "-a", window_title], check=True)
        except subprocess.CalledProcessError:
            # Try activating via xdotool
            try:
                subprocess.run(["xdotool", "search", "--name", window_title, "windowactivate"], check=True)
            except Exception:
                raise RuntimeError(f"Could not focus window '{window_title}'. Install wmctrl or xdotool.")
    else:
        raise NotImplementedError("Window focusing is only supported on macOS and Linux currently.")

    return f"Window '{window_title}' focused."


async def type_text(text: str, interval: float = 0.01) -> str:
    """
    Type a string via keyboard simulation. Requires pyautogui.
    Use with caution; always confirm before typing sensitive information.
    """
    try:
        import pyautogui
    except ImportError:
        raise RuntimeError("pyautogui is required. Install with: pip install pyautogui")

    await _run_in_executor(pyautogui.typewrite, text, interval=interval)
    return f"Typed: {text[:30]}{'...' if len(text) > 30 else ''}"