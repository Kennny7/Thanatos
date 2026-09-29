# Thanatos/apps/cli/terminal_client.py

import asyncio
import os
import sys
from typing import Any, Dict, List, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from shared.settings import Settings, runtime_settings
from services.llm_brain.provider import UnifiedLLMProvider
from services.llm_brain.coordinator import AgentCoordinator
from services.memory.memory_manager import memory_service
from plugins.base.registry import init_default_skills, registry

from .ui import (
    console,
    print_banner,
    print_thought,
    print_agent_breadcrumb,
    print_assistant_response,
    print_vector_status,
    print_application_history_table,
    print_help,
)
from .job_workflow import JobWorkflowRunner

prompt_style = Style.from_dict({
    "prompt": "#00d7ff bold",
})


class ThanatosCLI:
    """
    Interactive Linux-style terminal client for Thanatos AI.
    Provides direct command and conversational access with streaming thoughts,
    system diagnostics, and autonomous job hunting & application workflows.
    """

    def __init__(self) -> None:
        init_default_skills()
        self.settings = Settings.load()
        self.provider = UnifiedLLMProvider(self.settings)
        self.coordinator = AgentCoordinator(self.provider)
        self.job_runner = JobWorkflowRunner(show_thinking=True)
        self.show_thinking = True
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_resume_path: Optional[str] = None

    async def start(self) -> None:
        """Run terminal REPL loop."""
        os.system("cls" if os.name == "nt" else "clear")
        print_banner(
            app_name="Thanatos AI",
            model_name=self.settings.model,
            provider=self.settings.provider,
        )

        # Autonomously self-verify vector database on client boot
        diag = memory_service.vector_store.verify_and_diagnose()
        console.print(f"[dim blue]⚙ Vector DB Auto-Verified: {diag.get('backend')} ({diag.get('doc_count')} indexed memories)[/dim blue]")
        console.print("[dim]Type [bold white]/help[/bold white] for command list or start typing instructions/queries.[/dim]\n")

        session: PromptSession = PromptSession()

        while True:
            try:
                user_input = await session.prompt_async(
                    [("class:prompt", "thanatos> ")],
                    style=prompt_style,
                )
                user_input = user_input.strip()

                if not user_input:
                    continue

                if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                    console.print("[bold yellow]Exiting Thanatos CLI. Have a productive day![/bold yellow]")
                    break

                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                else:
                    await self._handle_chat(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold yellow]Session terminated.[/bold yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]CLI Error: {e}[/bold red]")

    async def _handle_command(self, cmd_line: str) -> None:
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/help":
            print_help()

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            print_banner(
                app_name="Thanatos AI",
                model_name=self.settings.model,
                provider=self.settings.provider,
            )

        elif cmd == "/status":
            console.print(f"\n[bold cyan]System Status:[/bold cyan]")
            console.print(f"  [dim]LLM Provider:[/dim] [green]{self.settings.provider}[/green]")
            console.print(f"  [dim]Active Model:[/dim] [yellow]{self.settings.model}[/yellow]")
            console.print(f"  [dim]Base URL:[/dim]     [white]{self.settings.base_url}[/white]")
            console.print(f"  [dim]Thinking Mode:[/dim] [{'green' if self.show_thinking else 'red'}]{'ON' if self.show_thinking else 'OFF'}[/]")
            if self.user_resume_path:
                console.print(f"  [dim]Loaded Resume:[/dim] [white]{self.user_resume_path}[/white]")
            console.print()

        elif cmd == "/vector-db":
            diag = memory_service.vector_store.verify_and_diagnose()
            print_vector_status(diag)

        elif cmd == "/thinking":
            if arg.lower() in ("on", "true", "1"):
                self.show_thinking = True
                self.job_runner.show_thinking = True
                console.print("[bold green]✔ Model deep reasoning / thinking display enabled.[/bold green]")
            elif arg.lower() in ("off", "false", "0"):
                self.show_thinking = False
                self.job_runner.show_thinking = False
                console.print("[bold yellow]✔ Model thinking display hidden.[/bold yellow]")
            else:
                status = "ON" if self.show_thinking else "OFF"
                console.print(f"[dim]Thinking display is currently [bold]{status}[/bold]. Usage: /thinking on|off[/dim]")

        elif cmd == "/history":
            history_res = await registry.dispatch("get_application_history", {"limit": 10})
            if history_res.success:
                print_application_history_table(history_res.content.get("recent_applications", []))
            else:
                console.print(f"[bold red]Could not fetch history: {history_res.error}[/bold red]")

        elif cmd == "/jobs":
            # Default or customized query
            query = arg if arg else "AI / ML Engineer remote or Pune"
            await self.job_runner.execute_job_workflow(
                query=query,
                location="Pune (Hybrid/Office) & Remote",
                experience="3 years and 8 months",
                source_resume_path=self.user_resume_path,
            )

        elif cmd == "/profile":
            if arg:
                if os.path.exists(arg):
                    self.user_resume_path = os.path.abspath(arg)
                    console.print(f"[bold green]✔ Configured custom resume source: {self.user_resume_path}[/bold green]")
                else:
                    console.print(f"[bold red]File not found: {arg}[/bold red]")
            else:
                p = memory_service.user_profile.get_profile()
                console.print(f"[bold cyan]User Profile:[/bold cyan] {p.name} ({p.title})")
                console.print(f"[dim]Email:[/dim] {p.email} │ [dim]Location:[/dim] {p.location}")
                console.print(f"[dim]Skills:[/dim] {', '.join(p.skills[:8])}...")
                if self.user_resume_path:
                    console.print(f"[dim]Active Resume Path:[/dim] [yellow]{self.user_resume_path}[/yellow]")
                else:
                    console.print("[dim]No custom resume path set. Using default embedded profile. (Set with /profile <path>)[/dim]")

        else:
            console.print(f"[red]Unknown command '{cmd}'. Type [bold white]/help[/bold white] for assistance.[/red]")

    async def _handle_chat(self, user_text: str) -> None:
        """Handle standard user conversational and natural language task prompts."""
        lower = user_text.lower()

        # Check if the user is naturally instructing a job workflow
        is_job_request = any(k in lower for k in ["job", "apply", "resume"]) and any(k in lower for k in ["search", "find", "hunt", "mail", "email", "pune", "remote"])

        if is_job_request:
            exp = "3 years and 8 months" if "3" in lower else "3+ years"
            loc = "Pune (Hybrid/Office) & Remote" if "pune" in lower or "remote" in lower else "Remote"
            await self.job_runner.execute_job_workflow(
                query=user_text,
                location=loc,
                experience=exp,
                source_resume_path=self.user_resume_path,
            )
            return

        # Stream coordinator execution
        self.conversation_history.append({"role": "user", "content": user_text})
        full_response = ""

        with console.status("[bold cyan]Thanatos thinking...[/bold cyan]", spinner="dots"):
            pass

        async for chunk in self.coordinator.execute_task_stream(user_text, self.conversation_history):
            chunk_type = chunk.get("type")

            if chunk_type == "agent_status":
                print_agent_breadcrumb(
                    chunk.get("agent", "Agent"),
                    chunk.get("status", ""),
                    chunk.get("progress"),
                )
            elif chunk_type == "thought":
                if self.show_thinking:
                    print_thought(chunk.get("thought", ""))
            elif chunk_type == "assistant_chunk":
                full_response += chunk.get("content", "")

        if full_response:
            self.conversation_history.append({"role": "assistant", "content": full_response})
            print_assistant_response(full_response)
