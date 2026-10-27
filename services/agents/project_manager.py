"""
Autonomous Project Workspace Manager for Thanatos.
Allows Alfred, Amelia, Velma and subagents to inspect codebases, read/write/edit files,
and revert/undo modifications safely without needing external MCP configurations.
"""

import os
import shutil
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join("data", "project_backups")


class ProjectWorkspaceManager:
    """
    Manages direct, safe access to external project paths with automated snapshot backups
    so any modifications made by the agents can be cleanly undone if needed.
    """

    def __init__(self, backup_dir: str = BACKUP_DIR) -> None:
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)
        self.history: List[Dict[str, Any]] = []

    def _resolve_path(self, target_path: str) -> str:
        """Resolve relative or absolute path against common workspaces."""
        if os.path.isabs(target_path) and os.path.exists(target_path):
            return target_path

        # Check in parent Self-Projects directory
        base_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        candidate = os.path.join(base_parent, target_path)
        if os.path.exists(candidate):
            return candidate

        return os.path.abspath(target_path)

    def backup_file(self, file_path: str) -> Optional[str]:
        """Create a timestamped backup before modifying a file to allow rollback."""
        abs_path = self._resolve_path(file_path)
        if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
            return None

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = os.path.basename(abs_path)
        backup_filename = f"{filename}_{ts}.bak"
        dest_path = os.path.join(self.backup_dir, backup_filename)

        shutil.copy2(abs_path, dest_path)
        record = {
            "original_path": abs_path,
            "backup_path": dest_path,
            "timestamp": ts,
        }
        self.history.append(record)
        logger.info("Created rollback snapshot for %s at %s", abs_path, dest_path)
        return dest_path

    def undo_last_change(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Revert the most recent change for a file (or the latest global change)."""
        if not self.history:
            return {"success": False, "message": "No modification history available to undo."}

        target_record = None
        if file_path:
            abs_target = self._resolve_path(file_path)
            for rec in reversed(self.history):
                if rec["original_path"] == abs_target:
                    target_record = rec
                    break
        else:
            target_record = self.history.pop()

        if not target_record:
            return {"success": False, "message": f"No backup found for {file_path}."}

        orig = target_record["original_path"]
        bak = target_record["backup_path"]

        if os.path.exists(bak):
            shutil.copy2(bak, orig)
            if target_record in self.history:
                self.history.remove(target_record)
            return {
                "success": True,
                "message": f"Successfully reverted {orig} to backup {bak}.",
                "restored_path": orig,
            }

        return {"success": False, "message": f"Backup file {bak} missing."}

    def list_files(self, project_path: str, max_depth: int = 2) -> Dict[str, Any]:
        """Inspect the directory tree of a specified project directory."""
        resolved = self._resolve_path(project_path)
        if not os.path.exists(resolved):
            return {"success": False, "error": f"Path '{project_path}' does not exist."}

        file_list = []
        for root, dirs, files in os.walk(resolved):
            # Skip hidden / heavy directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "node_modules", "__pycache__", "target")]
            rel_dir = os.path.relpath(root, resolved)
            depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
            if depth > max_depth:
                continue

            for f in files:
                file_list.append(os.path.normpath(os.path.join(rel_dir, f)))

        return {
            "success": True,
            "project_path": resolved,
            "total_files": len(file_list),
            "files": file_list[:100],
        }

    def read_file(self, file_path: str, max_lines: int = 500) -> Dict[str, Any]:
        """Read file contents safely."""
        resolved = self._resolve_path(file_path)
        if not os.path.exists(resolved):
            return {"success": False, "error": f"File '{file_path}' does not exist."}

        try:
            with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            content = "".join(lines[:max_lines])
            return {
                "success": True,
                "file_path": resolved,
                "lines_read": len(lines[:max_lines]),
                "total_lines": len(lines),
                "content": content,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, file_path: str, content: str, create_backup: bool = True) -> Dict[str, Any]:
        """Write or overwrite file with automated rollback backup."""
        resolved = self._resolve_path(file_path)
        os.makedirs(os.path.dirname(os.path.abspath(resolved)), exist_ok=True)

        backup_file = None
        if create_backup and os.path.exists(resolved):
            backup_file = self.backup_file(resolved)

        try:
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "file_path": resolved,
                "backup_created": backup_file,
                "message": f"Successfully written to {resolved}.",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


project_manager = ProjectWorkspaceManager()
