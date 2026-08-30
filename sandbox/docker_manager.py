# Thanatos/sandbox/docker_manager.py

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SandboxExecutor:
    """
    Executes commands or code snippets in an isolated container or restricted environment.
    """

    def __init__(self, image: str = "python:3.12-slim", timeout_seconds: int = 30) -> None:
        self.image = image
        self.timeout_seconds = timeout_seconds

    async def run(self, command: str, env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Runs a command inside the sandbox."""
        logger.info("Sandbox executing command: %s", command)
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_seconds
            )
            return {
                "exit_code": process.returncode or 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout_seconds}s",
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
            }
