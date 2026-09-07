# Thanatos/apps/api_server/routes/system_metrics.py
import os
import psutil
from typing import Any, Dict
from fastapi import APIRouter
from config.settings import app_config
from plugins.base.registry import registry

router = APIRouter(prefix="/api/system", tags=["System Telemetry"])


@router.get("/live-metrics")
async def get_live_metrics() -> Dict[str, Any]:
    """
    Returns live physical telemetry of host machine:
    CPU percent, RAM breakdown, disk space, active registered tools,
    and user geocoordinates for the digital Earth sphere.
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True) or 4
    
    # Virtual Memory
    vmem = psutil.virtual_memory()
    total_ram_gb = round(vmem.total / (1024 ** 3), 2)
    used_ram_gb = round(vmem.used / (1024 ** 3), 2)
    available_ram_gb = round(vmem.available / (1024 ** 3), 2)
    ram_percent = vmem.percent
    
    # Disk
    disk = psutil.disk_usage(os.getcwd())
    total_disk_gb = round(disk.total / (1024 ** 3), 1)
    used_disk_gb = round(disk.used / (1024 ** 3), 1)
    disk_percent = disk.percent
    
    # Active tools & skills
    tools = registry.get_all_tools()
    tool_names = [t.name for t in tools]
    
    # Location coordinates from config or fallback (Mumbai, India)
    location_str = getattr(app_config, "user_location", "Mumbai-India")
    lat, lon = 19.0760, 72.8777
    if "pune" in location_str.lower():
        lat, lon = 18.5204, 73.8567
    elif "delhi" in location_str.lower():
        lat, lon = 28.6139, 77.2090
    elif "bangalore" in location_str.lower():
        lat, lon = 12.9716, 77.5946

    return {
        "status": "online",
        "cpu": {
            "percent": cpu_percent,
            "logical_cores": cpu_count,
        },
        "ram": {
            "total_gb": total_ram_gb,
            "used_gb": used_ram_gb,
            "available_gb": available_ram_gb,
            "percent": ram_percent,
        },
        "disk": {
            "total_gb": total_disk_gb,
            "used_gb": used_disk_gb,
            "percent": disk_percent,
        },
        "telemetry": {
            "active_skills_count": len(tool_names),
            "tools": tool_names,
            "user_location": location_str,
            "latitude": lat,
            "longitude": lon,
        }
    }
