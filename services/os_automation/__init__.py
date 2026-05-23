from .router import os_automation_router

__all__ = ["os_automation_router"]

# The os_automation_router can be mounted in the main FastAPI app:
# from services.os_automation import os_automation_router
# app.include_router(os_automation_router)