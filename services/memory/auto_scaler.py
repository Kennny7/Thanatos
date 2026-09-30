# Thanatos/services/memory/auto_scaler.py

import logging
import os
import shutil
import subprocess
from typing import Any, Dict

logger = logging.getLogger(__name__)

SCALING_COMPOSE_FILE = "docker-compose.scaling.yml"
THRESHOLD_DOC_COUNT = 1000  # Recommend scaling when docs exceed this


class StorageAutoScaler:
    """
    Monitors data volume in Thanatos (vector document count and database size).
    When scale exceeds local lightweight thresholds, it detects Docker availability,
    advises the user, and can orchestrate the enterprise scaling stack (Milvus + PostgreSQL).
    """

    def __init__(self, doc_threshold: int = THRESHOLD_DOC_COUNT) -> None:
        self.doc_threshold = doc_threshold

    def check_scale(self, current_doc_count: int) -> Dict[str, Any]:
        """Check if storage exceeds lightweight capacity threshold."""
        has_docker = shutil.which("docker") is not None
        needs_scale = current_doc_count >= self.doc_threshold

        return {
            "current_doc_count": current_doc_count,
            "threshold": self.doc_threshold,
            "needs_scale": needs_scale,
            "has_docker": has_docker,
            "recommended_backends": {
                "vector": "Milvus Standalone (Distributed Vector DB with GPU support)",
                "relational": "PostgreSQL 16 (Scalable fact storage)",
            },
            "scaling_compose_file": SCALING_COMPOSE_FILE,
        }

    def launch_scaling_stack(self) -> Dict[str, Any]:
        """Launch docker-compose.scaling.yml to spin up Milvus and PostgreSQL."""
        if not shutil.which("docker"):
            return {
                "success": False,
                "error": "Docker executable not detected on system PATH. Please install or start Docker Desktop.",
            }

        if not os.path.exists(SCALING_COMPOSE_FILE):
            return {
                "success": False,
                "error": f"Scaling compose file '{SCALING_COMPOSE_FILE}' not found.",
            }

        try:
            cmd = ["docker", "compose", "-f", SCALING_COMPOSE_FILE, "up", "-d"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                return {
                    "success": True,
                    "message": "Milvus Standalone and PostgreSQL 16 containers launched successfully.",
                    "details": res.stdout.strip(),
                }
            else:
                return {
                    "success": False,
                    "error": res.stderr.strip() or res.stdout.strip(),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton auto scaler
auto_scaler = StorageAutoScaler()
