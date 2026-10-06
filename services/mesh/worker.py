# Thanatos/services/mesh/worker.py
"""
Lightweight Standalone Mesh Worker Node.
Run this on secondary devices (such as a laptop, or Android running Termux):
    python -m services.mesh.worker --port 8002 --role worker
"""

import argparse
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.mesh.node_manager import mesh_manager

logger = logging.getLogger("MeshWorker")


class MeshWorkerHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass  # Suppress default server access logging

    def do_GET(self) -> None:
        if self.path in ("/api/mesh/health", "/health"):
            specs = mesh_manager.get_local_specs()
            payload = {
                "status": "healthy",
                "role": getattr(self.server, "role", "worker"),
                "specs": specs,
            }
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path in ("/api/mesh/exec", "/exec"):
            import subprocess
            cmd = payload.get("command", "")
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                res = {
                    "status": "success",
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "exit_code": proc.returncode,
                }
            except Exception as e:
                res = {"status": "error", "error": str(e)}

            data = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        elif self.path in ("/api/mesh/file/write", "/file/write"):
            rel_path = payload.get("path", "")
            content = payload.get("content", "")
            try:
                os.makedirs(os.path.dirname(os.path.abspath(rel_path)), exist_ok=True)
                with open(rel_path, "w", encoding="utf-8") as f:
                    f.write(content)
                res = {"status": "written", "path": rel_path}
            except Exception as e:
                res = {"status": "error", "error": str(e)}

            data = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        elif self.path in ("/api/mesh/task", "/task"):
            response_payload = {
                "status": "received",
                "message": "Task queued on worker node",
                "node_hostname": mesh_manager.get_local_specs().get("hostname"),
            }
            data = json.dumps(response_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()


def run_worker(host: str = "0.0.0.0", port: int = 8002, role: str = "worker") -> None:
    server = HTTPServer((host, port), MeshWorkerHandler)
    setattr(server, "role", role)
    print(f"[✓] Thanatos Mesh Worker listening on http://{host}:{port} (Role: {role})")
    print(f"    Press Ctrl+C to terminate.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mesh worker.")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Thanatos Mesh Worker")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8002, help="Port to listen on")
    parser.add_argument("--role", default="worker", help="Role (worker, inference, memory)")
    args = parser.parse_args()

    run_worker(host=args.host, port=args.port, role=args.role)
