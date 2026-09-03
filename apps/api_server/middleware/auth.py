# Thanatos/apps/api_server/middleware/auth.py

import logging
import os
from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Configurable API Auth Token. If not set or empty, auth is disabled for local dev.
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "")

EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class ApiAuthMiddleware(BaseHTTPMiddleware):
    """
    Bearer Token security gate for REST and WebSocket endpoints.
    Protects assistant engine from unauthorized access or external interception.
    """

    async def dispatch(self, request: Request, call_next):
        # If no auth token is configured in environment, allow local development
        if not API_AUTH_TOKEN:
            return await call_next(request)

        # Allow exempt public health endpoints
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Handle WebSocket handshake authentication via query param or headers
        if request.url.path == "/ws":
            token = request.query_params.get("token") or request.headers.get("x-auth-token")
            if token != API_AUTH_TOKEN:
                logger.warning("Unauthorized WebSocket connection attempt to /ws from %s", request.client.host if request.client else "unknown")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Forbidden: Invalid or missing authentication token."},
                )
            return await call_next(request)

        # REST Bearer header verification
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Fallback to query param token
            param_token = request.query_params.get("token")
            if param_token != API_AUTH_TOKEN:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized: Missing Bearer token in Authorization header."},
                )
        else:
            token = auth_header.split(" ", 1)[1].strip()
            if token != API_AUTH_TOKEN:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Forbidden: Invalid authorization token."},
                )

        return await call_next(request)
