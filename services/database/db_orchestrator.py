# Thanatos/services/database/db_orchestrator.py

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

COMPOSE_FILE = "docker-compose.enterprise.yml"
REGISTRY_FILE = os.path.join("data", "database_registry.json")


class DatabaseOrchestrator:
    """
    Autonomous Supervisor for Enterprise Multi-Database Infrastructure.
    Manages lifecycle, container auto-start, healthchecks, RAM guardrails,
    and schema deduplication across:
      1. PostgreSQL 16 (Relational tables, operational logs, jobs)
      2. MongoDB 7.0 (Document transcripts, unformatted dossiers)
      3. Milvus 2.4.13 Standalone (Vector embeddings)
      4. Neo4j 5.20 Community (Knowledge graph & entity relationships)
    """

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = project_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.compose_path = os.path.join(self.project_root, COMPOSE_FILE)
        self.registry_path = os.path.join(self.project_root, REGISTRY_FILE)
        self._ensure_registry()

    def _ensure_registry(self) -> None:
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        if not os.path.exists(self.registry_path):
            initial_catalog = {
                "version": "1.0.0",
                "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "engines": {
                    "postgresql": {
                        "container": "thanatos-postgres",
                        "port": 5432,
                        "database": "thanatos_memory",
                        "user": "thanatos",
                        "role": "Relational Data, Structured Profiles, Jobs & Deduplication Audit",
                        "volume": "thanatos_postgres_data",
                        "health_cmd": "pg_isready -U thanatos"
                    },
                    "mongodb": {
                        "container": "thanatos-mongodb",
                        "port": 27017,
                        "database": "thanatos_docs",
                        "user": "thanatos_admin",
                        "role": "Agent Transcripts, Dynamic Raw Dossiers, Unstructured Memory",
                        "volume": "thanatos_mongo_data",
                        "health_cmd": "mongosh --eval \"db.adminCommand('ping')\""
                    },
                    "milvus": {
                        "container": "milvus-standalone",
                        "port": 19530,
                        "health_port": 9091,
                        "role": "High-Dimensional Vector Memory, Semantic Similarity, RAG",
                        "dependencies": ["milvus-etcd", "milvus-minio"],
                        "volume": "thanatos_milvus_data"
                    },
                    "neo4j": {
                        "container": "thanatos-neo4j",
                        "http_port": 7474,
                        "bolt_port": 7687,
                        "user": "neo4j",
                        "role": "Social Graph, Interpersonal Dossiers, Multi-Agent Knowledge Topology",
                        "volume": "thanatos_neo4j_data"
                    }
                },
                "status_history": []
            }
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(initial_catalog, f, indent=2)

    def is_docker_available(self) -> bool:
        """Check if Docker CLI daemon is accessible on the host machine."""
        docker_cmd = shutil.which("docker")
        if not docker_cmd:
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_docker_desktop_executable(self) -> Optional[str]:
        """Locate Docker Desktop executable on the host system."""
        candidates = [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
            r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Docker\Docker Desktop.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\Docker\Docker\Docker Desktop.exe"),
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        # Try finding in PATH
        which_desktop = shutil.which("Docker Desktop.exe") or shutil.which("docker-desktop")
        return which_desktop

    def start_docker_desktop(self) -> Dict[str, Any]:
        """Launch the Docker Desktop GUI/daemon process in the background."""
        if self.is_docker_available():
            return {"success": True, "already_running": True, "message": "Docker daemon is already online and operational."}

        exe_path = self.get_docker_desktop_executable()
        if not exe_path:
            return {"success": False, "message": "Docker Desktop executable could not be found in standard installation directories."}

        try:
            subprocess.Popen([exe_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Launched Docker Desktop process from: %s", exe_path)
            return {
                "success": True,
                "already_running": False,
                "executable": exe_path,
                "message": f"Successfully launched Docker Desktop ({os.path.basename(exe_path)}). Initializing daemon..."
            }
        except Exception as e:
            logger.error("Failed to launch Docker Desktop: %s", e)
            return {"success": False, "error": str(e)}

    def wait_for_docker(self, timeout_sec: int = 90, poll_interval_sec: float = 3.0, status_callback=None) -> bool:
        """Poll until Docker daemon reports healthy or timeout is reached."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            if self.is_docker_available():
                return True
            elapsed = int(time.time() - start_time)
            if status_callback:
                status_callback(elapsed, timeout_sec)
            time.sleep(poll_interval_sec)
        return self.is_docker_available()

    def get_container_status(self) -> Dict[str, Dict[str, Any]]:
        """Inspect current running state and resource usage for all database containers."""
        if not self.is_docker_available():
            return {"error": {"message": "Docker CLI or daemon is not reachable on host."}}

        expected_containers = [
            "thanatos-postgres",
            "thanatos-mongodb",
            "milvus-etcd",
            "milvus-minio",
            "milvus-standalone",
            "thanatos-neo4j",
            "thanatos-zookeeper",
            "thanatos-kafka",
        ]

        status_map: Dict[str, Dict[str, Any]] = {}
        try:
            # Query docker inspect for JSON status
            cmd = ["docker", "ps", "-a", "--format", "{{json .}}"]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            
            running_lookup = {}
            for line in res.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    cdata = json.loads(line)
                    c_name = cdata.get("Names", "")
                    running_lookup[c_name] = cdata
                except Exception:
                    continue

            for name in expected_containers:
                if name in running_lookup:
                    entry = running_lookup[name]
                    status_map[name] = {
                        "status": entry.get("State", "unknown"),
                        "running": entry.get("State") == "running",
                        "status_line": entry.get("Status", ""),
                        "ports": entry.get("Ports", "")
                    }
                else:
                    status_map[name] = {
                        "status": "not_created",
                        "running": False,
                        "status_line": "Container not created",
                        "ports": ""
                    }
        except Exception as e:
            logger.error("Failed to query Docker containers: %s", e)
            status_map["error"] = {"message": str(e)}

        return status_map

    def ensure_containers_running(self, target_engines: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Check container states and start missing or stopped containers using Docker Compose.
        """
        if not self.is_docker_available():
            return {
                "success": False,
                "message": "Docker is not currently running. Local embedded fallback storage remains active."
            }

        service_map = {
            "postgres": ["thanatos-postgres"],
            "mongodb": ["thanatos-mongodb"],
            "milvus": ["milvus-etcd", "milvus-minio", "milvus-standalone"],
            "neo4j": ["thanatos-neo4j"],
            "kafka": ["thanatos-zookeeper", "thanatos-kafka"],
        }

        services_to_start: List[str] = []
        if target_engines:
            for eng in target_engines:
                if eng in service_map:
                    services_to_start.extend(service_map[eng])
        else:
            # All enterprise services
            services_to_start = [
                "thanatos-postgres",
                "thanatos-mongodb",
                "milvus-etcd",
                "milvus-minio",
                "milvus-standalone",
                "thanatos-neo4j",
                "thanatos-zookeeper",
                "thanatos-kafka",
            ]

        try:
            compose_cmd = ["docker", "compose", "-f", self.compose_path, "up", "-d"] + services_to_start
            logger.info("Deploying database containers: %s", " ".join(compose_cmd))
            proc = subprocess.run(
                compose_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False
            )

            success = proc.returncode == 0
            msg = proc.stdout if success else proc.stderr
            return {
                "success": success,
                "command": " ".join(compose_cmd),
                "output": msg.strip(),
                "containers": services_to_start
            }
        except Exception as e:
            logger.error("Failed executing Docker compose: %s", e)
            return {"success": False, "error": str(e)}

    def stop_containers(self, target_engines: Optional[List[str]] = None) -> Dict[str, Any]:
        """Safely halt database containers to conserve RAM/CPU."""
        if not self.is_docker_available():
            return {"success": False, "message": "Docker not available."}

        try:
            cmd = ["docker", "compose", "-f", self.compose_path, "stop"]
            if target_engines:
                cmd.extend(target_engines)
            proc = subprocess.run(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
                check=False
            )
            return {"success": proc.returncode == 0, "output": proc.stdout.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def export_backup_catalog(self) -> Dict[str, Any]:
        """Provides operational details on volumes, backup directories, and restore commands."""
        return {
            "engines": [
                {
                    "name": "PostgreSQL",
                    "backup_command": "docker exec -t thanatos-postgres pg_dumpall -c -U thanatos > backups/postgres_dump.sql",
                    "restore_command": "cat backups/postgres_dump.sql | docker exec -i thanatos-postgres psql -U thanatos -d thanatos_memory",
                    "volume": "thanatos_postgres_data"
                },
                {
                    "name": "MongoDB",
                    "backup_command": "docker exec thanatos-mongodb mongodump --out /data/db/backup",
                    "restore_command": "docker exec thanatos-mongodb mongorestore /data/db/backup",
                    "volume": "thanatos_mongo_data"
                },
                {
                    "name": "Milvus",
                    "backup_command": "Milvus Backup CLI tool or volume snapshot of thanatos_milvus_data and thanatos_etcd_data",
                    "volumes": ["thanatos_milvus_data", "thanatos_etcd_data", "thanatos_minio_data"]
                },
                {
                    "name": "Neo4j",
                    "backup_command": "docker exec -it thanatos-neo4j neo4j-admin database dump neo4j --to-path=/data/backup",
                    "restore_command": "docker exec -it thanatos-neo4j neo4j-admin database load neo4j --from-path=/data/backup --overwrite-destination=true",
                    "volume": "thanatos_neo4j_data"
                }
            ]
        }


# Global singleton instance
db_orchestrator = DatabaseOrchestrator()
