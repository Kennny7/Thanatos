# Thanatos/services/mesh/discovery.py
"""
UDP Broadcast Discovery Service for Thanatos LAN Mesh.
Allows Thanatos coordinator and worker nodes on the same Wi-Fi subnet
to automatically discover, authenticate, and register each other without manual IP entry.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import socket
import time
from typing import Any, Dict, Optional

from services.mesh.node_manager import mesh_manager

logger = logging.getLogger(__name__)

DEFAULT_DISCOVERY_PORT = 47470
DEFAULT_MESH_SECRET = "thanatos-default-key"


def compute_node_token(secret: str, node_id: str, timestamp: int) -> str:
    """Generate HMAC-SHA256 signature for beacon authenticity."""
    msg = f"{node_id}:{timestamp}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


class DiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, discovery_service: "MeshDiscoveryService") -> None:
        self.discovery_service = discovery_service

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        try:
            message = json.loads(data.decode("utf-8"))
            self.discovery_service.handle_beacon(message, addr)
        except Exception as e:
            logger.debug("Discarding malformed discovery packet from %s: %s", addr, e)


class MeshDiscoveryService:
    """
    Manages background beacon broadcasting and incoming node registration.
    """

    def __init__(
        self,
        port: int = DEFAULT_DISCOVERY_PORT,
        secret: str = DEFAULT_MESH_SECRET,
        announce_interval: float = 8.0,
    ) -> None:
        self.port = port
        self.secret = secret
        self.announce_interval = announce_interval
        self._running = False
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._broadcast_task: Optional[asyncio.Task] = None

    def handle_beacon(self, beacon: Dict[str, Any], addr: tuple) -> None:
        """Process incoming broadcast beacon from peer."""
        if beacon.get("service") != "thanatos-mesh":
            return

        node_id = beacon.get("node_id")
        peer_port = beacon.get("port", 8002)
        role = beacon.get("role", "worker")
        token = beacon.get("token", "")
        ts = beacon.get("timestamp", 0)

        # Discard self announcements
        local_host = socket.gethostname()
        if node_id == local_host:
            return

        # Validate timestamp freshness (prevent replay > 60 seconds)
        if abs(time.time() - ts) > 60:
            return

        # Validate HMAC signature
        expected = compute_node_token(self.secret, node_id, ts)
        if not hmac.compare_digest(expected, token):
            logger.warning("Rejected unauthenticated beacon from %s (%s)", node_id, addr[0])
            return

        # Register or update in Mesh Node Manager
        mesh_manager.register_node(
            node_id=node_id,
            host=addr[0],
            port=peer_port,
            role=role,
            specs=beacon.get("specs"),
        )
        logger.debug("Auto-discovered LAN mesh node: %s at %s:%s (Role: %s)", node_id, addr[0], peer_port, role)

    async def start(self, role: str = "coordinator", http_port: int = 8002) -> None:
        """Start UDP broadcast listener and announcer tasks."""
        if self._running:
            return

        self._running = True
        loop = asyncio.get_running_loop()

        # Bind UDP listening socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", self.port))
        sock.setblocking(False)

        transport, _ = await loop.create_datagram_endpoint(
            lambda: DiscoveryProtocol(self),
            sock=sock,
        )
        self._transport = transport

        # Start periodic announcement loop
        self._broadcast_task = asyncio.create_task(self._announce_loop(role, http_port))
        logger.info("Mesh Auto-Discovery active on UDP port %s.", self.port)

    async def _announce_loop(self, role: str, http_port: int) -> None:
        """Periodically broadcast local node identity to the subnet."""
        node_id = socket.gethostname()
        specs = mesh_manager.get_local_specs()

        while self._running:
            try:
                now = int(time.time())
                beacon = {
                    "service": "thanatos-mesh",
                    "node_id": node_id,
                    "port": http_port,
                    "role": role,
                    "specs": specs,
                    "timestamp": now,
                    "token": compute_node_token(self.secret, node_id, now),
                }
                payload = json.dumps(beacon).encode("utf-8")
                if self._transport:
                    self._transport.sendto(payload, ("<broadcast>", self.port))
            except Exception as e:
                logger.debug("Error sending broadcast beacon: %s", e)

            await asyncio.sleep(self.announce_interval)

    async def stop(self) -> None:
        """Stop discovery service."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
        if self._transport:
            self._transport.close()


discovery_service = MeshDiscoveryService()
