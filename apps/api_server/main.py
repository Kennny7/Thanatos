# Thanatos\apps\api_server\main.py

from fastapi import FastAPI

from .routes.websocket import router as ws_router
from .routes.health import router as health_router
from .routes.speech import router as speech_router


app = FastAPI(
    title="Thanatos API Server",
    description="WebSocket orchestration layer",
    version="0.1.0",
)

# Register REST and WebSocket routes
app.include_router(health_router)
app.include_router(ws_router)
app.include_router(speech_router)