# Thanatos/services/mesh/remote_control.py
"""
Mesh Remote Control & Delegation Client.
Provides high-level coordination tools to remotely execute commands,
pull Ollama models, and read/write files across worker nodes on the LAN mesh.
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from services.mesh.node_manager import mesh_manager

logger = logging.getLogger(__name__)

DEFAULT_MESH_SECRET = "thanatos-default-key"


class MeshRemoteControl:
    """
    Client for controlling remote worker nodes from the coordinator.
    """

    def __init__(self, secret: str = DEFAULT_MESH_SECRET) -> None:
        self.secret = secret

    def _get_auth_token(self, node_id: str) -> str:
        now = int(time.time())
        msg = f"{node_id}:{now}".encode("utf-8")
        sig = hmac.new(self.secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        return f"{now}:{sig}"

    async def exec_on_node(self, node_id: str, command: str, timeout: float = 60.0) -> Dict[str, Any]:
        """Execute a shell command remotely on a worker node."""
        node = mesh_manager.nodes.get(node_id)
        if not node:
            return {"status": "error", "error": f"Node '{node_id}' not found in mesh."}

        endpoint = node.get("endpoint", "")
        token = self._get_auth_token(node_id)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    f"{endpoint}/api/mesh/exec",
                    json={"command": command, "auth_token": token},
                )
                if res.status_code == 200:
                    return res.json()
                return {"status": "error", "error": f"HTTP {res.status_code}: {res.text}"}
        except Exception as e:
            logger.exception("Error executing remote command on %s: %s", node_id, e)
            return {"status": "error", "error": str(e)}

    async def pull_model_on_node(self, node_id: str, model_name: str) -> Dict[str, Any]:
        """Instruct a remote node to pull an Ollama model."""
        cmd = f"ollama pull {model_name}"
        return await self.exec_on_node(node_id, cmd, timeout=600.0)

    async def list_models_on_node(self, node_id: str) -> Dict[str, Any]:
        """Query installed models on a remote node."""
        cmd = "ollama list"
        return await self.exec_on_node(node_id, cmd, timeout=15.0)

    async def write_file_to_node(self, node_id: str, rel_path: str, content: str) -> Dict[str, Any]:
        """Push a file to a remote worker node."""
        node = mesh_manager.nodes.get(node_id)
        if not node:
            return {"status": "error", "error": f"Node '{node_id}' not found."}

        endpoint = node.get("endpoint", "")
        token = self._get_auth_token(node_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{endpoint}/api/mesh/file/write",
                    json={"path": rel_path, "content": content, "auth_token": token},
                )
                return res.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}


remote_controller = MeshRemoteControl()
