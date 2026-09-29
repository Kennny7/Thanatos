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
    """Print Linux-style ASCII banner with active system specifications."""
    banner_text = Text()
    banner_text.append(" ████████╗██╗  ██╗ █████╗ ███╗   ██╗ █████╗ ████████╗ ██████╗ ███████╗\n", style="bold cyan")
    banner_text.append(" ╚══██╔══╝██║  ██║██╔══██╗████╗  ██║██╔══██╗╚══██╔══╝██╔═══██╗██╔════╝\n", style="bold cyan")
    banner_text.append("    ██║   ███████║███████║██╔██╗ ██║███████║   ██║   ██║   ██║███████╗\n", style="bold blue")
    banner_text.append("    ██║   ██╔══██║██╔══██║██║╚██╗██║██╔══██║   ██║   ██║   ██║╚════██║\n", style="bold blue")
    banner_text.append("    ██║   ██║  ██║██║  ██║██║ ╚████║██║  ██║   ██║   ╚██████╔╝███████║\n", style="bold magenta")
    banner_text.append("    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚══════╝\n", style="bold magenta")
    banner_text.append("  [ Autonomous Multi-Agent Terminal Client & AI Job Orchestrator ]", style="italic white")

    meta_info = f"[dim]Provider:[/dim] [bold green]{provider}[/bold green]  │  [dim]Model:[/dim] [bold cyan]{model_name}[/bold cyan]  │  [dim]Terminal:[/dim] [bold yellow]Interactive Shell[/bold yellow]"
    console.print(banner_text)
    console.print(Panel(meta_info, box=ROUNDED, border_style="dim blue", padding=(0, 1)))


def print_thought(thought_text: str) -> None:
    """Render LLM reasoning / thinking step in an isolated terminal panel."""
    if not thought_text or not thought_text.strip():
        return
    console.print()
    thought_panel = Panel(
        Markdown(thought_text.strip()),
        title="🧠 [bold magenta]Deep Reasoning & Planning[/bold magenta]",
        title_align="left",
        border_style="dim magenta",
        box=ROUNDED,
        padding=(0, 1),
    )
    console.print(thought_panel)


def print_agent_breadcrumb(agent: str, status: str, progress: Optional[float] = None) -> None:
    """Print live sub-agent status indicator."""
    pct_text = f" [{int(progress * 100)}%]" if progress is not None else ""
    console.print(f"[bold cyan]⚡ [{agent}][/bold cyan] [dim]{status}[/dim]{pct_text}")


def print_assistant_response(text: str) -> None:
    """Render finalized assistant markdown response."""
    console.print()
    console.print(Panel(Markdown(text.strip()), title="🤖 [bold cyan]Thanatos[/bold cyan]", title_align="left", border_style="cyan", box=ROUNDED, padding=(1, 2)))
    console.print()


def print_vector_status(diag: Dict[str, Any]) -> None:
    """Render diagnostic table of vector store health."""
    table = Table(title="📦 Vector Database Self-Diagnostics", box=ROUNDED, border_style="blue")
    table.add_column("Property", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("Backend", str(diag.get("backend", "Unknown")))
    table.add_row("Status", str(diag.get("status", "Unknown")).upper())
    table.add_row("Collection", str(diag.get("collection", "Unknown")))
    table.add_row("Total Indexed Documents", str(diag.get("doc_count", 0)))
    table.add_row("Storage Path", str(diag.get("persist_directory", "Unknown")))
    table.add_row("Collection Created Fresh?", "Yes (Newly Initialized)" if diag.get("is_new") else "No (Pre-existing Indexed)")

    console.print(table)


def print_application_history_table(applications: List[Dict[str, Any]]) -> None:
    """Render a table of past job applications."""
    if not applications:
        console.print("[dim yellow]No applications logged yet.[/dim yellow]")
        return

    table = Table(title="📄 Autonomous Job Applications & Email Outreach Log", box=ROUNDED, border_style="green")
    table.add_column("App ID", style="dim white")
    table.add_column("Company", style="bold white")
    table.add_column("Role", style="cyan")
    table.add_column("Recipient Email", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Date", style="dim white")

    for app in applications:
        table.add_row(
            app.get("application_id", "N/A"),
            app.get("company", "N/A"),
            app.get("job_title", "N/A"),
            app.get("recipient_email", "N/A"),
            app.get("status", "Staged"),
            app.get("timestamp", "N/A"),
        )

    console.print(table)


def print_help() -> None:
    """Display terminal CLI command help."""
    table = Table(title="💡 Thanatos Terminal Commands", box=ROUNDED, border_style="magenta")
    table.add_column("Command", style="bold yellow")
    table.add_column("Description", style="white")

    table.add_row("/help", "Show this command reference list")
    table.add_row("/clear", "Clear terminal screen")
    table.add_row("/status", "Display active LLM model, provider, and settings")
    table.add_row("/vector-db", "Verify and inspect vector database health & collections")
    table.add_row("/thinking on|off", "Toggle visibility of model reasoning / thought blocks")
    table.add_row("/history", "View recent autonomous job applications & email logs")
    table.add_row("/jobs [query]", "Run autonomous job hunter & verified email workflow")
    table.add_row("/profile [folder]", "Inspect or set path to profile directory & sync files")
    table.add_row("/smtp", "Test or configure SMTP email transmission credentials")
    table.add_row("/audit [target]", "Run defensive port and service audit on authorized target")
    table.add_row("/audit-web [url]", "Inspect defensive HTTP security headers and TLS status")
    table.add_row("/exit, /quit", "Exit the Thanatos terminal client")

    console.print(table)


def print_clarification_box(question: str) -> None:
    """Print an interactive inquiry box asking the user for clarification."""
    console.print()
    console.print(Panel(
        f"[bold yellow]❓ {question}[/bold yellow]\n\n[dim]Thanatos paused this action to ensure accuracy. Please provide your answer or instruction below:[/dim]",
        title="[bold yellow]Agent Clarification Needed[/bold yellow]",
        box=ROUNDED,
        border_style="yellow",
        padding=(0, 1),
    ))
