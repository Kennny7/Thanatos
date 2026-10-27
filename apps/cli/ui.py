# Thanatos/apps/cli/ui.py
"""
Rich Terminal Interface for Thanatos Personal Agent Manager.
Clean formatting, natural chat feel, and no emojis.
"""

import os
import sys
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.box import ROUNDED

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, highlight=False)


def print_banner(app_name: str = "Thanatos AI", model_name: str = "Unknown", provider: str = "Unknown") -> None:
    """Print clean terminal banner without emojis."""
    banner_text = (
        "============================================================\n"
        f"   {app_name.upper()} - AUTONOMOUS AGENT ENGINE\n"
        "   Distributed LAN Mesh | Multi-Agent Growth | Docker Supervisor\n"
        "============================================================"
    )
    meta_info = f"Provider: [bold green]{provider}[/bold green] | Model: [bold cyan]{model_name}[/bold cyan] | Mode: [bold yellow]Interactive Agent Terminal[/bold yellow]"
    console.print(Panel(banner_text, box=ROUNDED, border_style="cyan"))
    console.print(Panel(meta_info, box=ROUNDED, border_style="dim blue", padding=(0, 1)))


def print_thought(thought_text: str) -> None:
    """Render LLM reasoning dynamically if non-empty."""
    if not thought_text or not thought_text.strip():
        return
    console.print(Panel(
        thought_text.strip(),
        title="[bold magenta]REASONING[/bold magenta]",
        title_align="left",
        border_style="dim magenta",
        box=ROUNDED,
        padding=(0, 1),
    ))


def print_agent_breadcrumb(agent: str, status: str, progress: Optional[float] = None) -> None:
    """Print clean agent status indicator without emojis."""
    pct = f" [{int(progress * 100)}%]" if progress is not None else ""
    console.print(f"[bold cyan][{agent}][/bold cyan] [dim]{status}[/dim]{pct}")


def print_assistant_response(text: str, agent_name: str = "Thanatos") -> None:
    """Render concise chat-style response."""
    console.print()
    console.print(Panel(
        text.strip(),
        title=f"[bold cyan]{agent_name.upper()}[/bold cyan]",
        title_align="left",
        border_style="cyan",
        box=ROUNDED,
        padding=(0, 1),
    ))
    console.print()


def print_help() -> None:
    """Print available commands."""
    table = Table(title="Thanatos Command Deck", box=ROUNDED, border_style="cyan")
    table.add_column("Command", style="bold yellow")
    table.add_column("Description", style="white")

    table.add_row("/status", "Display LLM provider, active model, and system status")
    table.add_row("/agents", "List agent personas, private DMs (/agents dm), and switch persona")
    table.add_row("/bus", "View inter-agent communication messages and growth logs")
    table.add_row("/docker", "Manage enterprise database containers (/docker start|status|stop)")
    table.add_row("/nodes", "Distributed LAN mesh networking (/nodes list|scan|ping|add|exec|pull|sync)")
    table.add_row("/undo", "Revert last project file change made by Developer Subagent")
    table.add_row("/tasks", "View background running tasks (/tasks list|view|cancel|clear)")
    table.add_row("/thinking", "Toggle reasoning thinking output on/off (/thinking on|off)")
    table.add_row("/preview", "Toggle interactive draft review gate on/off (/preview on|off)")
    table.add_row("/vector-db", "Run vector database diagnostics")
    table.add_row("/clear", "Clear terminal screen")
    table.add_row("/exit", "Exit Thanatos CLI")
    console.print(table)


def print_vector_status(diag: Dict[str, Any]) -> None:
    """Render vector store status."""
    backend = diag.get("backend", "Unknown")
    docs = diag.get("doc_count", 0)
    console.print(f"[dim blue]• Vector Store: {backend} ({docs} memories indexed)[/dim blue]")


def print_task_notification(title: str, message: str) -> None:
    console.print(f"[dim yellow][Task Alert][/dim yellow] [bold white]{title}:[/bold white] [dim]{message}[/dim]")


def print_task_table(tasks: list) -> None:
    table = Table(title="• Background Tasks", box=ROUNDED, border_style="blue")
    table.add_column("ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Status", style="green")
    for t in tasks:
        table.add_row(str(t.get("id")), str(t.get("description")), str(t.get("status")))
    console.print(table)


def print_task_detail(task_data: dict) -> None:
    console.print(Panel(str(task_data), title="Task Detail", box=ROUNDED, border_style="dim blue"))
