import httpx

OLLAMA_URL = "http://ollama:11434"

async def chat(model: str, messages: list, temperature: float = 0.0):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "options": {
                    "temperature": temperature
                },
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()