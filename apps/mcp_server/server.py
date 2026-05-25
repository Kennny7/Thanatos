# Thanatos\apps\mcp_server\server.py
#!/usr/bin/env python3
"""
Thanatos Tools - Model Context Protocol Server
Exposes safe OS control operations to AI clients (Claude Desktop, Cursor, etc.)

Find claude_desktop_config.json at the provided location and edit it accordingly.
(just copy from Thanatos\apps\mcp_server\claude_desktop_config.json to the required location)
// Windows: %APPDATA%\Claude\claude_desktop_config.json
// macOS and Linux:  ~/.config/Claude/claude_desktop_config.json

"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import tool implementations
from tools.system_tools import (
    get_system_info,
    list_processes,
    kill_process,
    execute_command,
    list_directory,
    read_file,
    take_screenshot,
)
from tools.app_tools import (
    open_application,
    close_application,
    list_running_apps,
    focus_window,
    type_text,
)

# ---------------------------------------------------------------------------
# Logger (stderr to avoid interfering with stdio JSON-RPC)
# ---------------------------------------------------------------------------
logger = logging.getLogger("thanatos-mcp-server")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

server = Server("Thanatos Tools")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_system_info",
            description="Retrieve detailed system information (OS, CPU, memory, disks, network).",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="list_processes",
            description="List running processes, optionally filtered by name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name_filter": {
                        "type": "string",
                        "description": "Substring to filter process names (optional).",
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="kill_process",
            description="Terminate a process by PID. Use force=True to kill unconditionally.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process ID."},
                    "force": {
                        "type": "boolean",
                        "description": "If true, force-kill the process.",
                        "default": False,
                    },
                },
                "required": ["pid"],
            },
        ),
        Tool(
            name="execute_command",
            description="Execute a shell command and return stdout/stderr. Timeout in seconds (default 30).",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run."},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)."},
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="list_directory",
            description="List files and directories in a given path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: current directory)."},
                },
                "required": [],
            },
        ),
        Tool(
            name="read_file",
            description="Read the content of a text file (limited to 1 MB by default).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file."},
                    "max_size_kb": {
                        "type": "integer",
                        "description": "Maximum file size in KB (default 1024).",
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="take_screenshot",
            description="Capture the primary screen and return as base64 PNG or save to file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "save_path": {
                        "type": "string",
                        "description": "Optional path to save the screenshot. If omitted, returns base64 data URI.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="open_application",
            description="Launch an application by name or full path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name (e.g. 'Firefox')."},
                    "app_path": {"type": "string", "description": "Full path to executable (optional)."},
                },
                "required": ["app_name"],
            },
        ),
        Tool(
            name="close_application",
            description="Close an application by name. Force flag enables kill.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Application name."},
                    "force": {
                        "type": "boolean",
                        "description": "If true, forcefully kill the application.",
                        "default": False,
                    },
                },
                "required": ["app_name"],
            },
        ),
        Tool(
            name="list_running_apps",
            description="List visible GUI applications with window titles.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="focus_window",
            description="Bring a window to the foreground by its title.",
            inputSchema={
                "type": "object",
                "properties": {
                    "window_title": {"type": "string", "description": "Exact or partial window title."},
                },
                "required": ["window_title"],
            },
        ),
        Tool(
            name="type_text",
            description="Simulate keyboard typing. Use with extreme caution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type."},
                    "interval": {
                        "type": "number",
                        "description": "Delay between keystrokes in seconds (default 0.01).",
                    },
                },
                "required": ["text"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------
@server.call_tool()
async def call_tool(
    name: str, arguments: Dict[str, Any]
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    try:
        if name == "get_system_info":
            info = await get_system_info()
            return [TextContent(type="text", text=json.dumps(info, indent=2))]

        elif name == "list_processes":
            name_filter = arguments.get("name_filter")
            procs = await list_processes(name_filter)
            return [TextContent(type="text", text=json.dumps(procs, indent=2))]

        elif name == "kill_process":
            pid = arguments["pid"]
            force = arguments.get("force", False)
            msg = await kill_process(pid, force)
            return [TextContent(type="text", text=msg)]

        elif name == "execute_command":
            command = arguments["command"]
            timeout = arguments.get("timeout", 30)
            result = await execute_command(command, timeout)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_directory":
            path = arguments.get("path", ".")
            items = await list_directory(path)
            return [TextContent(type="text", text=json.dumps(items, indent=2))]

        elif name == "read_file":
            path = arguments["path"]
            max_kb = arguments.get("max_size_kb", 1024)
            content = await read_file(path, max_kb)
            return [TextContent(type="text", text=content)]

        elif name == "take_screenshot":
            save_path = arguments.get("save_path")
            result = await take_screenshot(save_path)
            # If result starts with 'data:', return it as an ImageContent? MCP spec allows TextContent with data URI.
            if result.startswith("data:image/png;base64,"):
                # For better client support, we could return ImageContent, but that requires a separate mime_type.
                # We'll return as text; AI clients usually handle base64 images in text.
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text=result)]

        elif name == "open_application":
            app_name = arguments.get("app_name", "")
            app_path = arguments.get("app_path", "")
            msg = await open_application(app_name, app_path)
            return [TextContent(type="text", text=msg)]

        elif name == "close_application":
            app_name = arguments["app_name"]
            force = arguments.get("force", False)
            msg = await close_application(app_name, force)
            return [TextContent(type="text", text=msg)]

        elif name == "list_running_apps":
            apps = await list_running_apps()
            return [TextContent(type="text", text=json.dumps(apps, indent=2))]

        elif name == "focus_window":
            title = arguments["window_title"]
            msg = await focus_window(title)
            return [TextContent(type="text", text=msg)]

        elif name == "type_text":
            text = arguments["text"]
            interval = arguments.get("interval", 0.01)
            msg = await type_text(text, interval)
            return [TextContent(type="text", text=msg)]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.exception("Tool '%s' failed", name)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
async def main():
    logger.info("Starting Thanatos MCP server with extended tools...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())