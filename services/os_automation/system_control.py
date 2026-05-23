# Thanatos\services\os_automation\system_control.py

"""
System control utilities: open applications, set volume, get system stats.
"""

import platform
import subprocess
from typing import Dict, Union

import psutil


class SystemController:
    """Handles OS-level actions like launching apps, adjusting volume, and reading system stats."""

    @staticmethod
    def open_application(app_name: str) -> str:
        """
        Launch an application by name using platform‑specific commands.
        On macOS the `open` command is used, Windows uses `start`, Linux uses `xdg-open`.
        """
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.Popen(["open", "-a", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Windows":
                subprocess.Popen(["start", "", app_name], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Linux":
                subprocess.Popen(["xdg-open", app_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                raise NotImplementedError(f"Unsupported platform: {system}")
            return f"Application '{app_name}' launched successfully."
        except FileNotFoundError:
            raise RuntimeError(f"Could not find a way to launch '{app_name}'. Ensure the app is installed.")
        except Exception as e:
            raise RuntimeError(f"Failed to open '{app_name}': {e}")

    @staticmethod
    def get_system_stats() -> Dict[str, Union[float, Dict[str, float]]]:
        """
        Retrieve current system resource usage.

        Returns a dictionary containing:
        - cpu_percent: overall CPU utilisation (%)
        - memory: dict with total, available, used, percent
        - disk: dict with total, used, free, percent for root partition
        """
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu,
            "memory": {
                "total_gb": round(mem.total / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "percent": mem.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
        }

    @staticmethod
    def set_volume(level: int) -> str:
        """
        Set system volume to a percentage level (0-100).

        Uses platform‑specific commands:
        - macOS: osascript
        - Windows: PowerShell + Win32 API
        - Linux: pactl (PulseAudio)
        """
        if not 0 <= level <= 100:
            raise ValueError("Volume level must be between 0 and 100.")

        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {level}"],
                    check=True, capture_output=True
                )
            elif system == "Windows":
                # Requires PowerShell + Win32 wrapper
                ps_script = f"""
                Add-Type -TypeDefinition @'
                using System;
                using System.Runtime.InteropServices;
                public class Audio {{
                    [DllImport("user32.dll")] public static extern IntPtr SendMessageW(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);
                }}
'@
                $vol = [math]::Round({level} / 100 * 65535)
                [Audio]::SendMessageW(0xFFFF, 0x319, 0, $vol)
                """
                subprocess.run(
                    ["powershell", "-Command", ps_script],
                    check=True, capture_output=True
                )
            elif system == "Linux":
                # Assumes PulseAudio; adjust if using PipeWire/ALSA
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    check=True, capture_output=True
                )
            else:
                raise NotImplementedError(f"Unsupported platform: {system}")
            return f"Volume set to {level}%."
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to set volume: {e.stderr.decode().strip() if e.stderr else str(e)}")
        except FileNotFoundError:
            raise RuntimeError("Required system command not found. Ensure required tools are installed.")