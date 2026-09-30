# Thanatos/services/mesh/node_manager.py

import asyncio
import json
import logging
import os
import platform
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

MESH_STATE_FILE = os.path.join("data", "mesh_nodes.json")


class MeshNodeManager:
    """
    Manages distributed LAN mesh nodes and worker nodes (e.g. secondary laptops,
    Termux on Android phones) for collaborative compute, inference offloading,
    and agent task delegation.
    """

    def __init__(self, state_file: str = MESH_STATE_FILE) -> None:
        self.state_file = state_file
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self._load_state()

    def _load_state(self) -> None:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    self.nodes = json.load(f)
            except Exception as e:
                logger.warning("Could not read mesh state: %s", e)
                self.nodes = {}

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.nodes, f, indent=2)
        except Exception as e:
            logger.warning("Could not save mesh state: %s", e)

    def register_node(
        self,
        node_id: str,
        host: str,
        port: int,
        role: str = "worker",
        specs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register or update a peer mesh node."""
        endpoint = f"http://{host}:{port}"
        node_entry = {
            "node_id": node_id,
            "host": host,
            "port": port,
            "endpoint": endpoint,
            "role": role,
            "specs": specs or {
                "os": platform.system(),
                "machine": platform.machine(),
                "node": platform.node(),
            },
            "status": "online",
            "last_seen": time.time(),
        }
        self.nodes[node_id] = node_entry
        self._save_state()
        return node_entry

    def unregister_node(self, node_id: str) -> bool:
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._save_state()
            return True
        return False

    def list_nodes(self) -> List[Dict[str, Any]]:
        return list(self.nodes.values())

    async def ping_node(self, node_id: str, timeout: float = 3.0) -> Dict[str, Any]:
        """Ping a node via HTTP health endpoint."""
        node = self.nodes.get(node_id)
        if not node:
            return {"node_id": node_id, "status": "unknown", "error": "Node not registered"}

        endpoint = node.get("endpoint", "")
        url = f"{endpoint}/api/mesh/health"

        def _do_ping() -> Dict[str, Any]:
            req = urllib.request.Request(url, headers={"User-Agent": "Thanatos-Mesh/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    body = response.read().decode("utf-8")
                    return {"status": "online", "details": json.loads(body) if body else {}}
            except Exception as e:
                return {"status": "offline", "error": str(e)}

        res = await asyncio.to_thread(_do_ping)
        if res.get("status") == "online":
            node["status"] = "online"
            node["last_seen"] = time.time()
        else:
            node["status"] = "offline"
        self._save_state()
        return {"node_id": node_id, "endpoint": endpoint, **res}

    async def ping_all(self) -> List[Dict[str, Any]]:
        tasks = [self.ping_node(nid) for nid in list(self.nodes.keys())]
        if not tasks:
            return []
        return await asyncio.gather(*tasks)

    def get_local_specs(self) -> Dict[str, Any]:
        """Return local hardware specs and device context."""
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
        }


# Singleton mesh manager
mesh_manager = MeshNodeManager()
