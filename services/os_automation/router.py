"""
FastAPI router exposing OS automation capabilities.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, conint

from .exceptions import SafetyCheckRequired
from .system_control import SystemController
from .input_controller import InputController

os_automation_router = APIRouter(prefix="/os", tags=["OS Automation"])


# ---------- Request models ----------
class OpenAppRequest(BaseModel):
    app_name: str = Field(..., min_length=1, description="Application name to open (e.g., 'Chrome')")

class SetVolumeRequest(BaseModel):
    level: conint(ge=0, le=100) = Field(..., description="Volume level 0-100")

class TypeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to type")
    force: bool = Field(False, description="Bypass safety confirmation if True")


# ---------- Endpoints ----------
@os_automation_router.post("/open-app")
async def open_app(payload: OpenAppRequest):
    """
    Launch an application by name.
    """
    try:
        result = SystemController.open_application(payload.app_name)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@os_automation_router.get("/system-stats")
async def system_stats():
    """
    Return real‑time CPU, memory, and disk usage statistics.
    """
    try:
        stats = SystemController.get_system_stats()
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@os_automation_router.post("/set-volume")
async def set_volume(payload: SetVolumeRequest):
    """
    Set system volume (0‑100%).
    """
    try:
        msg = SystemController.set_volume(payload.level)
        return {"status": "success", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@os_automation_router.post("/type-text")
async def type_text(payload: TypeTextRequest):
    """
    Simulate keyboard typing after optional safety check.
    """
    try:
        msg = InputController.type_text(payload.text, force=payload.force)
        return {"status": "success", "message": msg}
    except SafetyCheckRequired as e:
        # Return 409 Conflict so the client can ask the user to confirm.
        raise HTTPException(
            status_code=409,
            detail=f"Confirmation required. Active window: {e.window_title}. "
                   "Set 'force' to True to proceed."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))