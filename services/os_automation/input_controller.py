# Thanatos\services\os_automation\input_controller.py
"""
Keyboard input control with safety checks.
"""

import logging
import platform
import subprocess
from typing import Optional

import pyautogui

from .exceptions import SafetyCheckRequired

logger = logging.getLogger(__name__)

# Try to import pygetwindow for active window title detection.
try:
    import pygetwindow as gw
    HAS_GETWINDOW = True
except ImportError:
    HAS_GETWINDOW = False
    logger.warning("pygetwindow not installed; active window detection will be limited.")


class InputController:
    """Handles typing text with safeguards against dangerous contexts."""

    DANGEROUS_TITLE_KEYWORDS = ["terminal", "code"]

    @staticmethod
    def _get_active_window_title() -> Optional[str]:
        """Return the title of the currently focused window, or None if undetectable."""
        if HAS_GETWINDOW:
            try:
                win = gw.getActiveWindow()
                return win.title if win else None
            except Exception:
                pass

        # Fallback platform-specific methods
        system = platform.system()
        try:
            if system == "Darwin":
                script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                title = proc.stdout.strip()
                return title if title else None
            elif system == "Windows":
                # PowerShell: requires Add-Type and pinvoke, same as volume; simplified via tasklist
                # Not reliable, skip
                pass
            elif system == "Linux":
                # xdotool or wmctrl could be used
                proc = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                                      capture_output=True, text=True)
                if proc.returncode == 0:
                    return proc.stdout.strip()
        except Exception:
            pass
        return None

    @classmethod
    def type_text(cls, text: str, force: bool = False) -> str:
        """
        Type the given text as keyboard input.

        If the active window title contains 'Terminal' or 'Code' (case‑insensitive),
        a SafetyCheckRequired exception is raised unless `force=True`.
        """
        if not text:
            return "No text to type."

        if not force:
            title = cls._get_active_window_title()
            if title:
                lowered = title.lower()
                if any(kw in lowered for kw in cls.DANGEROUS_TITLE_KEYWORDS):
                    raise SafetyCheckRequired(window_title=title)

        # All checks passed, simulate typing
        try:
            pyautogui.write(text, interval=0.05)   # small delay to avoid flooding
            return f"Typed {len(text)} characters successfully."
        except Exception as e:
            raise RuntimeError(f"Failed to type text: {e}")