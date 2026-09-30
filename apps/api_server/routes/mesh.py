# Thanatos/apps/api_server/routes/mesh.py

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.mesh.node_manager import mesh_manager

router = APIRouter(prefix="/api/mesh", tags=["mesh"])


class RegisterNodeRequest(BaseModel):
    node_id: str
    host: str
    port: int
    role: str = "worker"
    specs: Optional[Dict[str, Any]] = None


@router.get("/health")
async def mesh_health() -> Dict[str, Any]:
    """Node health and spec endpoint."""
    return {
        "status": "online",
        "specs": mesh_manager.get_local_specs(),
        "total_nodes": len(mesh_manager.nodes),
    }


@router.get("/nodes")
async def list_nodes() -> List[Dict[str, Any]]:
    """List all registered LAN mesh nodes."""
    return mesh_manager.list_nodes()


@router.post("/register")
async def register_node(req: RegisterNodeRequest) -> Dict[str, Any]:
    """Register a new mesh node or worker."""
    entry = mesh_manager.register_node(
        node_id=req.node_id,
        host=req.host,
        port=req.port,
        role=req.role,
        specs=req.specs,
    )
    return {"status": "registered", "node": entry}


@router.delete("/nodes/{node_id}")
async def unregister_node(node_id: str) -> Dict[str, Any]:
    """Unregister a mesh node."""
    success = mesh_manager.unregister_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "unregistered", "node_id": node_id}


@router.post("/ping/{node_id}")
async def ping_node(node_id: str) -> Dict[str, Any]:
    """Ping a specific mesh node."""
    return await mesh_manager.ping_node(node_id)


@router.post("/ping-all")
async def ping_all() -> List[Dict[str, Any]]:
    """Ping all registered mesh nodes."""
    return await mesh_manager.ping_all()
