# Thanatos/sandbox/resource_limiter.py

import asyncio
import logging
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ResourceLimitedRunner:
    """
    Subprocess execution manager with timeouts and output bounds
    to safely execute test suites and verify self-improvement code patches.
    """

    def __init__(self, timeout_seconds: int = 15, max_output_chars: int = 4000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

    async def run_command(self, cmd: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Execute a shell command with strict timeout and capture output."""
        logger.info("Executing sandbox command: %s (cwd=%s)", cmd, cwd)
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds,
                )
                stdout_str = stdout.decode("utf-8", errors="replace")[:self.max_output_chars]
                stderr_str = stderr.decode("utf-8", errors="replace")[:self.max_output_chars]
                exit_code = process.returncode or 0

                return {
                    "success": exit_code == 0,
                    "exit_code": exit_code,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                }
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Execution timed out after {self.timeout_seconds}s",
                }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
            }
