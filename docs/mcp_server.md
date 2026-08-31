# Thanatos Model Context Protocol (MCP) Server

This document explains how to use and configure the Thanatos Model Context Protocol (MCP) Server (`apps/mcp_server/server.py`) to expose system control, process management, and OS automation tools to external AI clients such as **Claude Desktop**, **Cursor IDE**, and other MCP-compatible hosts.

---

## 📑 Table of Contents

- [1. Overview](#1-overview)
- [2. Available MCP Tools](#2-available-mcp-tools)
- [3. Setup & Configuration with Claude Desktop](#3-setup--configuration-with-claude-desktop)
- [4. Setup & Configuration with Cursor IDE](#4-setup--configuration-with-cursor-ide)
- [5. Running the MCP Server Standalone](#5-running-the-mcp-server-standalone)
- [6. Safety and Permissions](#6-safety-and-permissions)

---

## 1. Overview

The Thanatos MCP Server implements the standard [Model Context Protocol](https://modelcontextprotocol.io/) specification over JSON-RPC stdio. It allows AI models running in external environments to securely inspect system state, capture screenshots, manage running processes, and launch applications.

---

## 2. Available MCP Tools

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `get_system_info` | None | Retrieves OS details, CPU utilization, RAM usage, disk stats, and network interfaces. |
| `list_processes` | `name_filter?: string` | Lists running processes with optional name filtering. |
| `kill_process` | `pid: int, force?: bool` | Terminates a process by its PID. |
| `execute_command` | `command: string, timeout?: int` | Executes a shell command and captures stdout/stderr with a timeout safeguard. |
| `list_directory` | `path?: string` | Lists files and subdirectories in the specified path. |
| `read_file` | `path: string, max_size_kb?: int` | Reads the content of a text file (default cap: 1MB). |
| `take_screenshot` | `save_path?: string` | Captures the primary screen as a base64 PNG or saves to disk. |
| `open_application` | `app_name: string, app_path?: string` | Launches a desktop application by name or executable path. |
| `close_application`| `app_name: string, force?: bool` | Closes or terminates an application by name. |
| `list_running_apps`| None | Lists all active GUI windows and visible applications. |
| `focus_window` | `window_title: string` | Brings a window to the foreground by matching title. |
| `type_text` | `text: string, interval?: float` | Simulates keyboard typing into the active window. |

---

## 3. Setup & Configuration with Claude Desktop

### Configuration File Locations
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Configuration Content
Add the `thanatos-tools` server entry to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "thanatos-tools": {
      "command": "python",
      "args": [
        "C:\\Users\\ACER\\Desktop\\Self-Projects\\Thanatos\\apps\\mcp_server\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\ACER\\Desktop\\Self-Projects\\Thanatos\\apps\\mcp_server"
      }
    }
  }
}
```
*(Replace paths with your actual project location).*

---

## 4. Setup & Configuration with Cursor IDE

In Cursor:
1. Open **Settings** > **Features** > **MCP Servers**.
2. Click **+ Add New MCP Server**.
3. Set Name: `Thanatos Tools`.
4. Set Type: `command`.
5. Command: `python apps/mcp_server/server.py`.

---

## 5. Running the MCP Server Standalone

You can test the MCP server directly via terminal:

```bash
cd apps/mcp_server
python server.py
```
The server listens on `stdio` for standard MCP JSON-RPC messages.

---

## 6. Safety and Permissions

All system-modifying operations (such as killing processes or executing arbitrary commands) are logged to stderr and subject to safety timeouts.
