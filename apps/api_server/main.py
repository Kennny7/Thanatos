from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.websocket import router as ws_router
from .routes.health import router as health_router
from .routes.speech import router as speech_router
from .routes.config import router as config_router
from services.os_automation.router import os_automation_router
from plugins.base.registry import init_default_skills


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize default system skills on startup
    init_default_skills()
    yield


app = FastAPI(
    title="Thanatos AI Assistant Engine",
    description="Autonomous Multi-Agent Orchestration, Voice & RAG System",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-platform Flutter client and web browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(ws_router)
app.include_router(speech_router)
app.include_router(config_router)
app.include_router(os_automation_router)

