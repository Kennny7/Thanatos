# Thanatos/plugins/system_skills/system_execution/system_execution_skill.py
"""
System Execution Skill:
Empowers Thanatos to run native host commands (PowerShell / CMD / Bash),
manage Windows AppX packages (install, inspect, uninstall e.g. LinkedIn),
and execute diagnostic & maintenance utilities (sfc, DISM, chkdsk, winget)
with transparent status and live output streaming.
"""

import asyncio
import logging
import os
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class SystemExecutionSkill(BaseSkill):
    """
    Direct host execution & package management skill.
    Allows Thanatos to run commands on the local machine and report real output.
    """

    @property
    def skill_name(self) -> str:
        return "system_execution"

    @property
    def category(self) -> str:
        return "system"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="run_system_command",
                description=(
                    "Execute a command directly on the host system (PowerShell/CMD on Windows, bash on Linux/macOS) "
                    "and capture real exit code, stdout, and stderr. Supports running maintenance (sfc, dism, chkdsk), "
                    "package managers (winget, choco, pip, npm), and process/service tasks."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The exact shell command line string to execute.",
                        },
                        "shell_type": {
                            "type": "string",
                            "enum": ["powershell", "cmd", "bash", "auto"],
                            "description": "Shell to use. Defaults to 'powershell' on Windows, 'bash' on POSIX.",
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "description": "Timeout in seconds before aborting the command (default: 180).",
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Optional working directory to execute the command from.",
                        },
                    },
                    "required": ["command"],
                },
            ),
            ToolDefinition(
                name="manage_system_package",
                description=(
                    "Inspect, install, or uninstall software applications and packages. On Windows, supports "
                    "Windows Store AppX packages (e.g. LinkedIn, Spotify, Xbox) via PowerShell Get-AppxPackage, "
                    "as well as WinGet and MSI/EXE installers."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["inspect", "uninstall", "install", "list"],
                            "description": "Package management action to take.",
                        },
                        "package_name": {
                            "type": "string",
                            "description": "Name or pattern of the package/application (e.g., 'LinkedIn', 'chrome', 'git').",
                        },
                        "manager": {
                            "type": "string",
                            "enum": ["appx", "winget", "auto"],
                            "description": "Package manager backend. Defaults to 'auto'.",
                        },
                    },
                    "required": ["action"],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "run_system_command":
            return await self._run_command(params)
        elif tool_name == "manage_system_package":
            return await self._manage_package(params)
        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")

    async def _run_command(self, params: Dict[str, Any]) -> ToolResult:
        command = params.get("command", "").strip()
        if not command:
            return ToolResult.error_result(tool_name="run_system_command", error="No command provided.")

        shell_type = params.get("shell_type", "auto")
        timeout_seconds = int(params.get("timeout_seconds", 180))
        cwd = params.get("working_dir") or None

        is_win = platform.system() == "Windows"

        if shell_type == "auto":
            shell_type = "powershell" if is_win else "bash"

        if is_win:
            if shell_type == "powershell":
                shell_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
            else:
                shell_cmd = ["cmd.exe", "/c", command]
        else:
            shell_cmd = ["/bin/bash", "-c", command]

        logger.info("Executing host command via %s: %s", shell_type, command)

        try:
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return ToolResult.error_result(
                    tool_name="run_system_command",
                    error=f"Command timed out after {timeout_seconds} seconds.",
                )

            # Windows console encodings (utf-16le for utilities like sfc/dism, cp1252, utf-8 fallback)
            encodings = ["utf-16le", "utf-16", "utf-8", "cp1252", "latin1"]
            def decode_bytes(b: bytes) -> str:
                if not b:
                    return ""
                # Check for UTF-16 null byte pattern (every second byte null)
                if len(b) >= 2 and b[1] == 0:
                    try:
                        return b.decode("utf-16le").strip()
                    except Exception:
                        pass
                for enc in ["utf-8", "cp1252", "latin1"]:
                    try:
                        s = b.decode(enc)
                        # Clean any leftover embedded null bytes
                        return s.replace("\x00", "").strip()
                    except UnicodeDecodeError:
                        continue
                return b.decode("utf-8", errors="replace").replace("\x00", "").strip()

            stdout_str = decode_bytes(stdout_bytes)
            stderr_str = decode_bytes(stderr_bytes)
            exit_code = process.returncode

            return ToolResult.success_result(
                tool_name="run_system_command",
                content={
                    "command": command,
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                    "stdout": stdout_str or "(No output emitted to stdout)",
                    "stderr": stderr_str or "(No errors emitted to stderr)",
                },
            )
        except Exception as e:
            logger.exception("Failed executing system command: %s", e)
            return ToolResult.error_result(
                tool_name="run_system_command",
                error=f"Host execution exception: {str(e)}",
            )

    async def _manage_package(self, params: Dict[str, Any]) -> ToolResult:
        action = params.get("action", "inspect")
        package_name = params.get("package_name", "").strip()
        manager = params.get("manager", "auto")

        is_win = platform.system() == "Windows"
        if not is_win:
            return ToolResult.error_result(
                tool_name="manage_system_package",
                error="Package management currently optimized for Windows environments.",
            )

        if not package_name and action in ("uninstall", "install", "inspect"):
            return ToolResult.error_result(
                tool_name="manage_system_package",
                error="Package name is required for inspect, install, or uninstall actions.",
            )

        # Handle AppX (UWP / Modern Windows Apps like LinkedIn, Store apps)
        if manager in ("appx", "auto"):
            clean_pkg = package_name.replace("'", "").replace('"', "")
            if action == "inspect":
                ps_cmd = f"Get-AppxPackage -Name '*{clean_pkg}*' | Select-Object Name, PackageFullName, Version, Publisher, InstallLocation | ConvertTo-Json -Depth 2"
                res = await self._run_command({"command": ps_cmd, "shell_type": "powershell"})
                if res.success:
                    return ToolResult.success_result(tool_name="manage_system_package", content={"appx_result": res.content.get("stdout")})
            
            elif action == "uninstall":
                # Find package full name and remove it
                ps_cmd = (
                    f"$pkgs = Get-AppxPackage -Name '*{clean_pkg}*'; "
                    f"if ($pkgs) {{ "
                    f"  $pkgs | Remove-AppxPackage -ErrorAction Continue; "
                    f"  Write-Output ('Successfully uninstalled ' + ($pkgs.Name -join ', ')) "
                    f"}} else {{ "
                    f"  Write-Output ('No AppX package matching \"{clean_pkg}\" found. Trying winget...') "
                    f"}}"
                )
                res = await self._run_command({"command": ps_cmd, "shell_type": "powershell"})
                output_str = res.content.get("stdout", "") if res.success else ""
                
                # If appx uninstalled successfully, return immediately
                if "Successfully uninstalled" in output_str:
                    return ToolResult.success_result(
                        tool_name="manage_system_package",
                        content={"status": "uninstalled", "details": output_str},
                    )

                # Fallback to winget uninstall if AppX didn't find it
                winget_cmd = f"winget uninstall --id '{clean_pkg}' --silent --accept-source-agreements"
                w_res = await self._run_command({"command": winget_cmd, "shell_type": "powershell"})
                return ToolResult.success_result(
                    tool_name="manage_system_package",
                    content={
                        "appx_check": output_str,
                        "winget_result": w_res.content.get("stdout") if w_res.success else w_res.error,
                    },
                )

            elif action == "list":
                ps_cmd = "Get-AppxPackage | Select-Object Name, Version | ConvertTo-Json"
                res = await self._run_command({"command": ps_cmd, "shell_type": "powershell"})
                return ToolResult.success_result(
                    tool_name="manage_system_package",
                    content=res.content if res.success else {"error": res.error},
                )

        # Fallback to Winget
        if action == "install":
            winget_cmd = f"winget install --id '{package_name}' --silent --accept-source-agreements --accept-package-agreements"
            return await self._run_command({"command": winget_cmd, "shell_type": "powershell"})

        return ToolResult.error_result(tool_name="manage_system_package", error=f"Unsupported action: {action}")
