# Thanatos/apps/cli/ui.py

import os
import sys
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.box import ROUNDED, DOUBLE_EDGE

# Ensure stdout/stderr use UTF-8 encoding across Windows/Linux terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True, highlight=False)


def print_banner(app_name: str = "Thanatos AI", model_name: str = "Unknown", provider: str = "Unknown") -> None:
    """Print large original ASCII banner with active system specifications."""
    banner_text = Text()
    banner_text.append(" ████████╗██╗  ██╗ █████╗ ███╗   ██╗ █████╗ ████████╗ ██████╗ ███████╗\n", style="bold cyan")
    banner_text.append(" ╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝\n", style="bold cyan")
    banner_text.append("    ██║   ███████║███████║██╔██╗ ██║███████║   ██║   ██║   ██║███████╗\n", style="bold blue")
    banner_text.append("    ██║   ██╔══██║██╔══██║██║╚██╗██║██╔══██║   ██║   ██║   ██║╚════██║\n", style="bold blue")
    banner_text.append("    ██║   ██║  ██║██║  ██║██║ ╚████║██║  ██║   ██║   ╚██████╔╝███████║\n", style="bold magenta")
    banner_text.append("    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝\n", style="bold magenta")
    banner_text.append("  [ Autonomous Multi-Agent Terminal Client & AI Developer Operating System ]", style="italic white")

    meta_info = f"[dim]Provider:[/dim] [bold green]{provider}[/bold green]  │  [dim]Model:[/dim] [bold cyan]{model_name}[/bold cyan]  │  [dim]Terminal:[/dim] [bold yellow]Interactive Shell[/bold yellow]"
    console.print(banner_text)
    console.print(Panel(meta_info, box=ROUNDED, border_style="dim blue", padding=(0, 1)))


def clean_markdown_thought(text: str) -> str:
    """Clean up common LLM thought markdown formatting quirks like malformed bold bullets and personality preambles."""
    if not text:
        return ""
    import re

    # Strip out any lingering persona recitations at the start of thought blocks:
    # e.g., "Felix Ashworth (Technical Systems Architect). Extraordinarily intelligent child..."
    # or "Alfred Vance (Head Butler & Household Manager)..."
    cleaned = re.sub(
        r"^(?:[A-Z][a-z]+ [A-Z][a-z]+|[A-Za-z]+)\s*\([^\)]+\)\.?\s*(?:[A-Z][^\.\n]+\.?)*\n*",
        "",
        text.strip(),
        flags=re.MULTILINE,
    )

    # Fix nested asterisk patterns like `*   *Title:*` -> `- **Title:**`
    cleaned = re.sub(r'^\s*\*\s+\*([^*]+?)\*(\:?)', r'- **\1**\2', cleaned, flags=re.MULTILINE)
    # Fix triple asterisks or broken bold markers like `***`
    cleaned = re.sub(r'\*\*\*+', '**', cleaned)
    return cleaned.strip()


def print_thought(thought_text: str, agent_name: Optional[str] = None, collapsed: bool = True) -> None:
    """Render LLM reasoning / thinking step in an isolated terminal panel with expand/collapse control."""
    if not thought_text or not thought_text.strip():
        return
    cleaned = clean_markdown_thought(thought_text)
    if not cleaned:
        return

    agent_tag = f" [{agent_name}]" if agent_name else ""
    title = f"[bold magenta]• REASONING & PLANNING{agent_tag}[/bold magenta]"

    console.print()
    if collapsed:
        # Show first 2 preview lines and summary indicator
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        preview_text = " ".join(lines[:2])
        if len(preview_text) > 160:
            preview_text = preview_text[:157] + "..."
        line_count = len(lines)
        summary = (
            f"[dim italic]{preview_text}[/dim italic]\n"
            f"[dim cyan](Collapsed: {line_count} lines. Use [/dim cyan][bold yellow]/thinking expand[/bold yellow][dim cyan] to show full or [/dim cyan][bold yellow]/thinking last[/bold yellow][dim cyan] to inspect)[/dim cyan]"
        )
        thought_panel = Panel(
            summary,
            title=title,
            title_align="left",
            border_style="dim magenta",
            box=ROUNDED,
            padding=(0, 1),
        )
        console.print(thought_panel)
    else:
        thought_panel = Panel(
            Markdown(cleaned),
            title=title,
            title_align="left",
            border_style="dim magenta",
            box=ROUNDED,
            padding=(0, 1),
        )
        console.print(thought_panel)


def print_agent_breadcrumb(agent: str, status: str, state_tag: Optional[str] = None) -> None:
    """Print live sub-agent status indicator with real state tags (no fake percentages)."""
    tag_str = f" [bold yellow][{state_tag}][/bold yellow]" if state_tag else ""
    console.print(f"[bold cyan]❯ [{agent}][/bold cyan] [dim]{status}[/dim]{tag_str}")


def print_dag_box(box_panel: Any) -> None:
    """Render Antigravity-style Task Box."""
    console.print()
    console.print(box_panel)
    console.print()


def print_assistant_response(text: str, agent_name: str = "Thanatos") -> None:
    """Render finalized assistant markdown response."""
    console.print()
    console.print(Panel(
        Markdown(text.strip()),
        title=f"[bold cyan]• {agent_name.upper()}[/bold cyan]",
        title_align="left",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2)
    ))
    console.print()


def print_help() -> None:
    """Render comprehensive Linux-style help manual with all available commands."""
    table = Table(
        title="• Thanatos Multi-Agent Terminal Client - Command Deck",
        box=ROUNDED,
        border_style="cyan",
        header_style="bold cyan",
    )
    table.add_column("Command", style="bold yellow", no_wrap=True)
    table.add_column("Arguments", style="dim", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("/status", "", "Display current LLM provider, active model, and system parameters")
    table.add_row("/agents", "[dm | set | rename]", "Manage multi-agent personas, private DMs, and active default agent")
    table.add_row("/bus", "", "View recent inter-agent communication messages and growth learnings")
    table.add_row("/docker", "[status | start | stop]", "Inspect or control enterprise database cluster (PostgreSQL, MongoDB, Milvus, Neo4j, Kafka)")
    table.add_row("/nodes", "[list | scan | add | exec | pull | sync]", "Manage distributed LAN compute mesh, UDP discovery, and remote inference offloading")
    table.add_row("/undo", "[file_path]", "Revert the last project file modification made by the agent")
    table.add_row("/tasks", "[list | view | cancel | clear]", "Inspect or cancel asynchronous background agent tasks")
    table.add_row("/thinking", "[collapse | expand | on | off | last]", "Toggle thinking stream, collapse/expand mode, or view last reasoning")
    table.add_row("/preview", "[on | off]", "Toggle interactive human review gate before action execution")
    table.add_row("/vector-db", "", "Run diagnostics and verify vector database integrity")
    table.add_row("/clear", "", "Clear terminal screen and redraw system banner")
    table.add_row("/exit", "", "Terminate session cleanly")

    console.print(table)
    console.print("[dim]Type natural language requests directly, or use slash commands above.[/dim]\n")


def print_vector_status(diag: Dict[str, Any]) -> None:
    """Render diagnostic table of vector store health."""
    table = Table(title="• Vector Store Health & Diagnostics", box=ROUNDED, border_style="cyan")
    table.add_column("Component", style="bold white")
    table.add_column("Status / Value", style="bold green")
    table.add_column("Notes", style="dim")

    table.add_row("Vector Backend", diag.get("backend", "Unknown"), "Target database runtime")
    table.add_row("Document Count", str(diag.get("doc_count", 0)), "Total memories / documents indexed")
    table.add_row("Collection Name", diag.get("collection_name", "N/A"), "Active vector collection")
    table.add_row("Persistence Path", diag.get("persist_dir", "N/A"), "Host filesystem mapping")
    table.add_row("Self-Diagnosis", diag.get("status", "Unknown"), "Integrity verification result")

    console.print(table)
    console.print()


def print_enterprise_cluster_table(cluster_data: Dict[str, Any]) -> None:
    """Render diagnostic table of all 5 enterprise database engines."""
    table = Table(title="• Enterprise Multi-Engine Database Cluster", box=ROUNDED, border_style="cyan")
    table.add_column("Engine", style="bold white")
    table.add_column("Role / Responsibility", style="dim")
    table.add_column("Port", style="cyan", justify="center")
    table.add_column("Cluster Health", style="bold")

    for eng_key, info in cluster_data.items():
        is_on = info.get("online", False)
        status_col = "green" if is_on else "yellow"
        table.add_row(
            info.get("engine", eng_key),
            info.get("role", ""),
            str(info.get("target_port", "")),
            f"[{status_col}]{info.get('status', 'Unknown')}[/{status_col}]",
        )
    console.print(table)
    console.print()


def print_task_notification(title: str, message: str) -> None:
    """Render background task alerts."""
    console.print(f"[dim yellow][Task Alert][/dim yellow] [bold white]{title}:[/bold white] [dim]{message}[/dim]")


def print_task_table(tasks: list) -> None:
    """Render running background tasks table."""
    table = Table(title="• Background Tasks", box=ROUNDED, border_style="blue")
    table.add_column("ID", style="cyan")
    table.add_column("Task", style="white")
    table.add_column("Status", style="green")
    for t in tasks:
        table.add_row(str(t.get("id")), str(t.get("description")), str(t.get("status")))
    console.print(table)


def print_task_detail(task_data: dict) -> None:
    """Render single task detail panel."""
    console.print(Panel(str(task_data), title="Task Detail", box=ROUNDED, border_style="dim blue"))
