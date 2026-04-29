# Thanatos\tests\debug\debug_planner.py
import asyncio
import time
import traceback
import json

from shared.settings import Settings
from shared.deepseek_planner import DeepSeekPlanner


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"[DEBUG] {title}")
    print("=" * 60)


async def heartbeat():
    while True:
        print("[DEBUG] Heartbeat... still waiting", flush=True)
        await asyncio.sleep(5)


async def main():
    start_time = time.time()

    print_section("STARTING DEBUG RUN")

    # --- Load settings ---
    try:
        settings = Settings.load()
    except Exception:
        print("[ERROR] Failed to load settings")
        traceback.print_exc()
        return

    print_section("SETTINGS LOADED")

    # 🔴 CRITICAL — verify routing
    print(f"[DEBUG] base_url: {settings.base_url}")
    print(f"[DEBUG] model: {settings.model}")
    print(f"[DEBUG] is_local: {getattr(settings, 'is_local', 'N/A')}")
    print(f"[DEBUG] api_key present: {bool(settings.api_key)}")

    # --- Init planner ---
    try:
        planner = DeepSeekPlanner(settings=settings)
    except Exception:
        print("[ERROR] Planner initialization failed")
        traceback.print_exc()
        return

    print_section("PLANNER INITIALIZED")

    # --- Input ---
    history = [
        {"role": "user", "content": "What's the weather in Paris?"}
    ]

    tools_schema = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ]

    print_section("INPUT SUMMARY")
    print(f"[DEBUG] messages: {len(history)}")
    print(f"[DEBUG] tools: {len(tools_schema)}")

    # --- Run planner ---
    print_section("CALLING planner.plan()")

    hb_task = asyncio.create_task(heartbeat())

    try:
        result = await asyncio.wait_for(
            planner.plan(history, tools_schema),
            timeout=120
        )
    except asyncio.TimeoutError:
        print("[ERROR] planner.plan() TIMED OUT")
        traceback.print_exc()
        return
    except Exception:
        print("[ERROR] planner.plan() FAILED")
        traceback.print_exc()
        return
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass

    # --- Output ---
    print_section("RESULT RECEIVED")

    print(f"[DEBUG] Total time: {time.time() - start_time:.2f}s")

    try:
        print("[DEBUG] Result JSON:")
        print(json.dumps(result, indent=2))
    except Exception:
        print("[DEBUG] Raw result:", result)

    print_section("VALIDATION")

    if not result:
        print("[ERROR] Result is None or empty")
    elif not isinstance(result, dict):
        print("[ERROR] Result is not a dict")
    elif "action" not in result:
        print("[ERROR] Missing 'action' key")
    else:
        print("[SUCCESS] Planner returned valid structure")

    print_section("DONE")


if __name__ == "__main__":
    asyncio.run(main())