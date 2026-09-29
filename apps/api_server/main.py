from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from .routes.websocket import router as ws_router
from .routes.health import router as health_router
from .routes.speech import router as speech_router
from .routes.config import router as config_router
from .routes.system_metrics import router as system_metrics_router
from .middleware.auth import ApiAuthMiddleware
from services.os_automation.router import os_automation_router
from plugins.base.registry import init_default_skills


from services.memory.memory_manager import memory_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize default system skills on startup
    init_default_skills()
    diag = memory_service.vector_store.verify_and_diagnose()
    print(f"\n========================================================")
    print(f"🚀 Thanatos AI Server Engine Starting Up")
    print(f"📦 Vector Store Backend : {diag.get('backend')}")
    print(f"📂 Persistence Path     : {diag.get('persist_directory')}")
    print(f"🗂️  Collection Name      : {diag.get('collection')}")
    print(f"📄 Indexed Documents    : {diag.get('doc_count')}")
    print(f"✨ New DB Created?      : {'Yes (Empty initialized)' if diag.get('is_new') else 'No (Existing store loaded)'}")
    print(f"========================================================\n")
    yield


app = FastAPI(
    title="Thanatos AI Assistant Engine",
    description="Autonomous Multi-Agent Orchestration, Voice & RAG System",
    version="1.0.0",
    lifespan=lifespan,
)

# Optional Bearer Token Authentication
app.add_middleware(ApiAuthMiddleware)

# Configurable CORS origins for production security
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router)
app.include_router(ws_router)
app.include_router(speech_router)
app.include_router(config_router)
app.include_router(system_metrics_router)
app.include_router(os_automation_router)

