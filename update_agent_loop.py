with open("apps/api_server/core/agent_loop.py", "r", encoding="utf-8") as f:
    code = f.read()

target = """                else:
                    await websocket.send_json(chunk)"""

replacement = """                else:
                    payload = dict(chunk)
                    if "box" in payload:
                        payload["box"] = str(payload["box"])
                    if hasattr(payload.get("plan"), "model_dump"):
                        payload["plan"] = payload["plan"].model_dump()
                    await websocket.send_json(payload)"""

target_crlf = target.replace("\n", "\r\n")
replacement_crlf = replacement.replace("\n", "\r\n")

if target_crlf in code:
    code = code.replace(target_crlf, replacement_crlf)
elif target in code:
    code = code.replace(target, replacement)

with open("apps/api_server/core/agent_loop.py", "w", encoding="utf-8") as f:
    f.write(code)

print("AGENT_LOOP_UPDATED")
