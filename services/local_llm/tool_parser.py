import json

def parse_llm_output(content: str):
    try:
        data = json.loads(content)
        return data
    except Exception:
        return {
            "action": "respond",
            "text": content
        }