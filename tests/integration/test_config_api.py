# tests/integration/test_config_api.py

import pytest
from httpx import AsyncClient, ASGITransport
from apps.api_server.main import app


@pytest.mark.asyncio
async def test_config_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Get config
        resp = await ac.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "model" in data
        assert "provider" in data

        # 2. Update model
        update_payload = {"model": "llama3.1:8b", "provider": "ollama", "temperature": 0.2}
        resp = await ac.post("/api/config/llm", json=update_payload)
        assert resp.status_code == 200
        res_data = resp.json()
        assert res_data["status"] == "success"
        assert res_data["config"]["model"] == "llama3.1:8b"

        # 3. List models
        resp = await ac.get("/api/config/models")
        assert resp.status_code == 200
        models_data = resp.json()
        assert len(models_data["models"]) > 0
