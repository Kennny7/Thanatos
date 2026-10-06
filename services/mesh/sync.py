# Thanatos/services/mesh/sync.py
"""
Manifest-Based Delta File Synchronization Service.
Allows primary coordinator to synchronize profile documents, LaTeX resumes,
and configuration files to remote mesh nodes without redundant transfers.
"""

import hashlib
import json
import logging
import os
from typing import Any, Dict, List
import httpx

from services.mesh.node_manager import mesh_manager
from services.mesh.remote_control import remote_controller

logger = logging.getLogger(__name__)


def compute_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class MeshSyncService:
    """
    Computes local manifests and synchronizes delta changes to mesh nodes.
    """

    def generate_manifest(self, folder_path: str) -> Dict[str, str]:
        """Compute relative path -> sha256 manifest."""
        manifest = {}
        if not os.path.exists(folder_path):
            return manifest

        for root, _, files in os.walk(folder_path):
            for fname in files:
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, folder_path).replace("\\", "/")
                try:
                    manifest[rel] = compute_file_hash(full)
                except Exception:
                    pass
        return manifest

    async def sync_folder_to_node(self, node_id: str, local_folder: str, remote_folder: str) -> Dict[str, Any]:
        """Transfer only modified or new files to the target node."""
        node = mesh_manager.nodes.get(node_id)
        if not node:
            return {"status": "error", "error": f"Node {node_id} not found."}

        manifest = self.generate_manifest(local_folder)
        synced_count = 0
        skipped_count = 0

        for rel_path, fhash in manifest.items():
            full_path = os.path.join(local_folder, rel_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                remote_path = f"{remote_folder}/{rel_path}".replace("\\", "/")
                res = await remote_controller.write_file_to_node(node_id, remote_path, content)
                if res.get("status") == "written":
                    synced_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                logger.warning("Could not sync file %s to %s: %s", rel_path, node_id, e)
                skipped_count += 1

        return {
            "status": "completed",
            "node_id": node_id,
            "synced_files": synced_count,
            "skipped": skipped_count,
            "total_files": len(manifest),
        }

    async def sync_profile_to_all_nodes(self) -> List[Dict[str, Any]]:
        """Sync candidate profile folder to all active mesh nodes."""
        results = []
        for nid in list(mesh_manager.nodes.keys()):
            res = await self.sync_folder_to_node(nid, "data/profile_dir", "data/profile_dir")
            results.append(res)
        return results


sync_service = MeshSyncService()
