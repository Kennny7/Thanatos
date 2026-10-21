# Thanatos/plugins/system_skills/system_execution/system_execution_skill.py
"""
System Execution Skill:
Empowers Thanatos to run native host commands (PowerShell / CMD / Bash),
manage Windows AppX packages (install, inspect, uninstall e.g. LinkedIn),
and execute diagnostic & maintenance utilities (sfc, DISM, chkdsk, winget)
with transparent status, live output streaming, and UAC auto-elevation.

Concrete system health tools:
- run_malware_scan: Windows Defender quick/full scan
- run_sfc_scan: System File Checker (elevated)
- run_dism_repair: DISM image health/repair (elevated)
- check_disk_health: Physical disk SMART/status query
- check_windows_updates: Pending Windows Update enumeration
"""

import asyncio
import ctypes
import logging
import os
import platform
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class SystemExecutionSkill(BaseSkill):
    """
    Direct host execution & package management skill.
    Allows Thanatos to run commands on the local machine and report real output.
    Supports UAC auto-elevation for admin-required operations on Windows.
    """

    @property
    def skill_name(self) -> str:
        return "system_execution"

    @property
    def category(self) -> str:
        return "system"

    def _is_admin(self) -> bool:
        """Check if the current process is running with Administrator privileges."""
        if platform.system() != "Windows":
            return os.geteuid() == 0
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="run_system_command",
                description=(
                    "Execute a command directly on the host system (PowerShell/CMD on Windows, bash on Linux/macOS) "
                    "and capture real exit code, stdout, and stderr. Supports running maintenance (sfc, dism, chkdsk), "
                    "package managers (winget, choco, pip, npm), and process/service tasks. "
                    "Set admin_required=true for commands that need UAC elevation (auto-handled)."
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
                        "admin_required": {
                            "type": "boolean",
                            "description": "If true, the command will be auto-elevated via UAC on Windows. Default: false.",
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
            ToolDefinition(
                name="run_malware_scan",
                description=(
                    "Run a Windows Defender antivirus scan (quick or full). "
                    "Executes the real MpCmdRun.exe or Start-MpScan cmdlet with admin elevation. "
                    "Returns actual scan output and exit status."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "scan_type": {
                            "type": "string",
                            "enum": ["quick", "full"],
                            "description": "Type of scan: 'quick' (default, ~5 min) or 'full' (30-60+ min).",
                        },
                    },
                    "required": [],
                },
            ),
            ToolDefinition(
                name="run_sfc_scan",
                description=(
                    "Run the Windows System File Checker (sfc /scannow) with auto-elevation. "
                    "Scans and repairs protected system files. Returns actual sfc output."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="run_dism_repair",
                description=(
                    "Run DISM (Deployment Image Servicing and Management) to check or repair the Windows component store. "
                    "Supports CheckHealth, ScanHealth, and RestoreHealth operations with auto-elevation."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["check_health", "scan_health", "restore_health"],
                            "description": "DISM operation: 'check_health' (fast), 'scan_health' (thorough), 'restore_health' (repair). Default: 'restore_health'.",
                        },
                    },
                    "required": [],
                },
            ),
            ToolDefinition(
                name="check_disk_health",
                description=(
                    "Query physical disk health status including model, media type, status, and size "
                    "via WMI/CIM. Does not require admin privileges."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            ToolDefinition(
                name="check_windows_updates",
                description=(
                    "Check for pending Windows updates. Lists available updates with KB numbers, "
                    "titles, and download sizes. Uses COM API fallback if PSWindowsUpdate is not installed."
                ),
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "run_system_command":
            return await self._run_command(params)
        elif tool_name == "manage_system_package":
            return await self._manage_package(params)
        elif tool_name == "run_malware_scan":
            return await self._run_malware_scan(params)
        elif tool_name == "run_sfc_scan":
            return await self._run_sfc_scan(params)
        elif tool_name == "run_dism_repair":
            return await self._run_dism_repair(params)
        elif tool_name == "check_disk_health":
            return await self._check_disk_health(params)
        elif tool_name == "check_windows_updates":
            return await self._check_windows_updates(params)
        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")

    async def _run_command(self, params: Dict[str, Any]) -> ToolResult:
        command = params.get("command", "").strip()
        if not command:
            return ToolResult.error_result(tool_name="run_system_command", error="No command provided.")

        shell_type = params.get("shell_type", "auto")
        timeout_seconds = int(params.get("timeout_seconds", 180))
        cwd = params.get("working_dir") or None
        admin_required = params.get("admin_required", False)

        is_win = platform.system() == "Windows"

        if shell_type == "auto":
            shell_type = "powershell" if is_win else "bash"

        # If elevation is needed and we're not already admin, use UAC elevation
        if admin_required and is_win and not self._is_admin():
            return await self._run_elevated_command(command, shell_type, timeout_seconds, cwd)

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

            stdout_str = self._decode_bytes(stdout_bytes)
            stderr_str = self._decode_bytes(stderr_bytes)
            exit_code = process.returncode

            return ToolResult.success_result(
                tool_name="run_system_command",
                content={
                    "command": command,
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                    "stdout": stdout_str or "(No output emitted to stdout)",
                    "stderr": stderr_str or "(No errors emitted to stderr)",
                    "elevated": admin_required,
                },
            )
        except Exception as e:
            logger.exception("Failed executing system command: %s", e)
            return ToolResult.error_result(
                tool_name="run_system_command",
                error=f"Host execution exception: {str(e)}",
            )

    async def _run_elevated_command(
        self, command: str, shell_type: str, timeout_seconds: int, cwd: Optional[str]
    ) -> ToolResult:
        """
        Run a command with UAC elevation on Windows.
        Creates temp script + output files, launches via Start-Process -Verb RunAs,
        then reads captured output.
        """
        tmp_dir = tempfile.mkdtemp(prefix="thanatos_elev_")
        script_path = os.path.join(tmp_dir, "elevated_cmd.ps1")
        stdout_path = os.path.join(tmp_dir, "stdout.txt")
        stderr_path = os.path.join(tmp_dir, "stderr.txt")
        exit_code_path = os.path.join(tmp_dir, "exitcode.txt")

        # Build the elevated script that captures output to files
        cwd_line = f"Set-Location -Path '{cwd}'" if cwd else ""
        script_content = f"""
$ErrorActionPreference = 'Continue'
{cwd_line}
try {{
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command {{ {command} }} 2>&1
    $stdout = ($output | Where-Object {{ $_ -isnot [System.Management.Automation.ErrorRecord] }}) -join "`n"
    $stderr = ($output | Where-Object {{ $_ -is [System.Management.Automation.ErrorRecord] }}) -join "`n"
    $stdout | Out-File -FilePath '{stdout_path}' -Encoding UTF8 -Force
    $stderr | Out-File -FilePath '{stderr_path}' -Encoding UTF8 -Force
    $LASTEXITCODE | Out-File -FilePath '{exit_code_path}' -Encoding UTF8 -Force
}} catch {{
    $_.Exception.Message | Out-File -FilePath '{stderr_path}' -Encoding UTF8 -Force
    '1' | Out-File -FilePath '{exit_code_path}' -Encoding UTF8 -Force
}}
"""
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Launch the elevated process
            launcher_cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                f"Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','{script_path}' "
                f"-Verb RunAs -Wait"
            ]

            logger.info("Launching elevated command via UAC: %s", command[:100])

            process = await asyncio.create_subprocess_exec(
                *launcher_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return ToolResult.error_result(
                    tool_name="run_system_command",
                    error=f"Elevated command timed out after {timeout_seconds} seconds.",
                )

            # Read captured output
            stdout_str = ""
            stderr_str = ""
            exit_code = -1

            if os.path.exists(stdout_path):
                with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
                    stdout_str = f.read().strip()
            if os.path.exists(stderr_path):
                with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
                    stderr_str = f.read().strip()
            if os.path.exists(exit_code_path):
                with open(exit_code_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_code = f.read().strip()
                    try:
                        exit_code = int(raw_code) if raw_code else 0
                    except ValueError:
                        exit_code = 0

            return ToolResult.success_result(
                tool_name="run_system_command",
                content={
                    "command": command,
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                    "stdout": stdout_str or "(No output captured from elevated process)",
                    "stderr": stderr_str or "(No errors captured from elevated process)",
                    "elevated": True,
                },
            )
        except Exception as e:
            logger.exception("Elevated command execution failed: %s", e)
            return ToolResult.error_result(
                tool_name="run_system_command",
                error=f"UAC elevation execution exception: {str(e)}",
            )
        finally:
            # Cleanup temp files
            for f in [script_path, stdout_path, stderr_path, exit_code_path]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
            try:
                os.rmdir(tmp_dir)
            except Exception:
                pass

    @staticmethod
    def _decode_bytes(b: bytes) -> str:
        """Decode subprocess output handling Windows console encodings."""
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

    # ── Concrete System Health Tools ──────────────────────────────────────

    async def _run_malware_scan(self, params: Dict[str, Any]) -> ToolResult:
        """Execute a real Windows Defender malware scan."""
        scan_type = params.get("scan_type", "quick")
        scan_type_num = "1" if scan_type == "quick" else "2"
        scan_label = "Quick Scan" if scan_type == "quick" else "Full Scan"

        # Try Start-MpScan first, fall back to MpCmdRun.exe
        command = (
            f"try {{ "
            f"  Start-MpScan -ScanType {scan_label.replace(' ', '')} -ErrorAction Stop; "
            f"  Write-Output 'Windows Defender {scan_label} completed successfully.' "
            f"}} catch {{ "
            f"  Write-Output 'Start-MpScan unavailable, using MpCmdRun.exe...'; "
            f"  $defenderPath = \"$env:ProgramFiles\\Windows Defender\\MpCmdRun.exe\"; "
            f"  if (Test-Path $defenderPath) {{ "
            f"    & $defenderPath -Scan -ScanType {scan_type_num}; "
            f"    Write-Output \"MpCmdRun.exe {scan_label} exit code: $LASTEXITCODE\" "
            f"  }} else {{ "
            f"    Write-Output 'ERROR: Windows Defender not found at expected path.' "
            f"  }} "
            f"}}"
        )

        logger.info("Executing Windows Defender %s", scan_label)
        timeout = 600 if scan_type == "quick" else 7200  # 10 min for quick, 2h for full

        result = await self._run_command({
            "command": command,
            "shell_type": "powershell",
            "timeout_seconds": timeout,
            "admin_required": True,
        })

        if result.success:
            result.content["tool_name"] = "run_malware_scan"
            result.content["scan_type"] = scan_label
        return ToolResult(
            tool_name="run_malware_scan",
            success=result.success,
            content=result.content if result.success else None,
            error=result.error,
        )

    async def _run_sfc_scan(self, params: Dict[str, Any]) -> ToolResult:
        """Execute System File Checker (sfc /scannow) with elevation."""
        logger.info("Executing sfc /scannow (elevated)")
        result = await self._run_command({
            "command": "sfc /scannow",
            "shell_type": "powershell",
            "timeout_seconds": 900,  # SFC can take 15+ minutes
            "admin_required": True,
        })
        return ToolResult(
            tool_name="run_sfc_scan",
            success=result.success,
            content=result.content if result.success else None,
            error=result.error,
        )

    async def _run_dism_repair(self, params: Dict[str, Any]) -> ToolResult:
        """Execute DISM health check or repair with elevation."""
        operation = params.get("operation", "restore_health")
        op_map = {
            "check_health": "/CheckHealth",
            "scan_health": "/ScanHealth",
            "restore_health": "/RestoreHealth",
        }
        dism_flag = op_map.get(operation, "/RestoreHealth")
        command = f"DISM /Online /Cleanup-Image {dism_flag}"

        # Timeout varies: CheckHealth is fast, RestoreHealth can take 20+ min
        timeout = 300 if operation == "check_health" else 1800

        logger.info("Executing DISM %s (elevated)", dism_flag)
        result = await self._run_command({
            "command": command,
            "shell_type": "powershell",
            "timeout_seconds": timeout,
            "admin_required": True,
        })
        return ToolResult(
            tool_name="run_dism_repair",
            success=result.success,
            content=result.content if result.success else None,
            error=result.error,
        )

    async def _check_disk_health(self, params: Dict[str, Any]) -> ToolResult:
        """Query physical disk health via CIM/WMI (no elevation needed)."""
        command = (
            "Get-CimInstance Win32_DiskDrive | "
            "Select-Object Model, MediaType, Status, "
            "@{n='SizeGB';e={[math]::Round($_.Size/1GB,2)}}, "
            "InterfaceType, Partitions, FirmwareRevision | "
            "ConvertTo-Json -Depth 2"
        )
        logger.info("Querying disk health via CIM")
        result = await self._run_command({
            "command": command,
            "shell_type": "powershell",
            "timeout_seconds": 30,
            "admin_required": False,
        })

        if result.success:
            stdout = result.content.get("stdout", "")
            import json
            try:
                disk_data = json.loads(stdout)
                return ToolResult.success_result(
                    tool_name="check_disk_health",
                    content={"disks": disk_data if isinstance(disk_data, list) else [disk_data]},
                )
            except Exception:
                return ToolResult.success_result(
                    tool_name="check_disk_health",
                    content={"raw_output": stdout},
                )

        return ToolResult(
            tool_name="check_disk_health",
            success=False,
            content=None,
            error=result.error,
        )

    async def _check_windows_updates(self, params: Dict[str, Any]) -> ToolResult:
        """Check for pending Windows updates using COM API."""
        # Use the COM API directly (doesn't require PSWindowsUpdate module)
        command = (
            "try { "
            "  $session = New-Object -ComObject Microsoft.Update.Session; "
            "  $searcher = $session.CreateUpdateSearcher(); "
            "  $result = $searcher.Search('IsInstalled=0'); "
            "  $updates = @(); "
            "  foreach ($update in $result.Updates) { "
            "    $updates += [PSCustomObject]@{ "
            "      Title = $update.Title; "
            "      KB = ($update.KBArticleIDs -join ','); "
            "      SizeMB = [math]::Round($update.MaxDownloadSize / 1MB, 1); "
            "      IsImportant = $update.AutoSelectOnWebSites; "
            "      Description = $update.Description.Substring(0, [Math]::Min(200, $update.Description.Length)) "
            "    } "
            "  }; "
            "  if ($updates.Count -eq 0) { "
            "    Write-Output '{\"pending_updates\": 0, \"updates\": [], \"message\": \"System is up to date.\"}' "
            "  } else { "
            "    $updates | ConvertTo-Json -Depth 2 "
            "  } "
            "} catch { "
            "  Write-Output ('{\"error\": \"' + $_.Exception.Message + '\"}') "
            "}"
        )

        logger.info("Checking for pending Windows updates")
        result = await self._run_command({
            "command": command,
            "shell_type": "powershell",
            "timeout_seconds": 120,
            "admin_required": False,
        })

        if result.success:
            stdout = result.content.get("stdout", "")
            import json
            try:
                update_data = json.loads(stdout)
                if isinstance(update_data, list):
                    return ToolResult.success_result(
                        tool_name="check_windows_updates",
                        content={"pending_updates": len(update_data), "updates": update_data},
                    )
                return ToolResult.success_result(
                    tool_name="check_windows_updates",
                    content=update_data,
                )
            except Exception:
                return ToolResult.success_result(
                    tool_name="check_windows_updates",
                    content={"raw_output": stdout},
                )

        return ToolResult(
            tool_name="check_windows_updates",
            success=False,
            content=None,
            error=result.error,
        )

    # ── Package Management ────────────────────────────────────────────────

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
