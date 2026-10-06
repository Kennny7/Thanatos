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

    async def execute_single_command(self, cmd_input: str) -> None:
        """Execute a single non-interactive command or query and exit cleanly."""
        cmd_input = cmd_input.strip()
        if not cmd_input:
            return
        if cmd_input.startswith("/"):
            await self._handle_command(cmd_input)
        else:
            await self._handle_chat(cmd_input)

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
        console.print(f"[dim blue]• Vector DB Auto-Verified: {diag.get('backend')} ({diag.get('doc_count')} indexed memories)[/dim blue]")
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
                console.print("[bold green][✓] Model deep reasoning / thinking display enabled.[/bold green]")
            elif arg.lower() in ("off", "false", "0"):
                self.show_thinking = False
                self.job_runner.show_thinking = False
                console.print("[bold yellow][✓] Model thinking display hidden.[/bold yellow]")
            else:
                status = "ON" if self.show_thinking else "OFF"
                console.print(f"[dim]Thinking display is currently [bold]{status}[/bold]. Usage: /thinking on|off[/dim]")

        elif cmd == "/preview":
            if arg.lower() in ("on", "true", "1"):
                os.environ["THANATOS_DRAFT_PREVIEW"] = "true"
                console.print("[bold green][✓] Interactive draft review & preview gate enabled.[/bold green]")
            elif arg.lower() in ("off", "false", "0"):
                os.environ["THANATOS_DRAFT_PREVIEW"] = "false"
                console.print("[bold yellow][✓] Draft preview gate disabled (Autonomous Auto-Pilot mode active).[/bold yellow]")
            else:
                curr = os.getenv("THANATOS_DRAFT_PREVIEW", "true")
                console.print(f"[dim]Draft preview gate is currently [bold]{'ON' if curr == 'true' else 'OFF'}[/bold]. Usage: /preview on|off[/dim]")

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
                if os.path.isdir(arg):
                    stats = memory_service.user_profile.set_profile_directory(arg)
                    console.print(f"[bold green][✓] Configured profile repository folder: {os.path.abspath(arg)}[/bold green]")
                    console.print(f"[dim]Sync Results: {stats.get('added', 0)} added, {stats.get('updated', 0)} updated, {stats.get('skipped', 0)} unchanged.[/dim]")
                elif os.path.isfile(arg):
                    self.user_resume_path = os.path.abspath(arg)
                    console.print(f"[bold green][✓] Configured custom resume file: {self.user_resume_path}[/bold green]")
                else:
                    console.print(f"[bold red]Path not found: {arg}[/bold red]")
            else:
                stats = memory_service.user_profile.sync()
                p = memory_service.user_profile.get_profile()
                console.print(f"\n[bold cyan]• Candidate Profile & Knowledge Directory:[/bold cyan]")
                console.print(f"  [dim]Name:[/dim]      [bold white]{p.name}[/bold white] ({p.title})")
                console.print(f"  [dim]Contact:[/dim]   {p.email} │ {p.location}")
                console.print(f"  [dim]Links:[/dim]     GitHub: [cyan]{p.github_url or 'N/A'}[/cyan] │ LinkedIn: [cyan]{p.linkedin_url or 'N/A'}[/cyan]")
                console.print(f"  [dim]Portfolio:[/dim] [cyan]{p.portfolio_url or 'N/A'}[/cyan]")
                console.print(f"  [dim]Directory:[/dim] [yellow]{os.path.abspath(memory_service.user_profile.profile_dir)}[/yellow]")
                console.print(f"  [dim]Files Ingested:[/dim] [green]{', '.join(p.custom_documents.keys()) if p.custom_documents else 'None'}[/green]")
                console.print(f"  [dim]Skills ({len(p.skills)}):[/dim] {', '.join(p.skills[:8])}...\n")

        elif cmd == "/smtp":
            from services.email.email_service import email_service
            if not arg:
                conf = email_service.is_configured()
                console.print(f"\n[bold cyan]• SMTP Email Configuration Status:[/bold cyan]")
                console.print(f"  [dim]Configured:[/dim] [{'green' if conf else 'red'}]{'YES' if conf else 'NO'}[/]")
                console.print(f"  [dim]Host:[/dim]       {email_service.host or 'Not set'}")
                console.print(f"  [dim]Port:[/dim]       {email_service.port}")
                console.print(f"  [dim]User:[/dim]       {email_service.user or 'Not set'}")
                console.print(f"  [dim]From:[/dim]       {email_service.from_email or 'Not set'}")
                if conf:
                    console.print("[dim]Testing connection...[/dim]")
                    res = email_service.verify_connection()
                    status_col = "green" if res.success else "red"
                    console.print(f"  [dim]Test Result:[/dim] [{status_col}]{res.message}[/{status_col}]\n")
                else:
                    console.print("[dim yellow]Setup Instructions for Gmail / Custom SMTP:[/dim yellow]")
                    console.print("[dim white]1. Go to: [underline cyan]https://myaccount.google.com/apppasswords?st_source=ai_mode[/underline cyan][/dim white]")
                    console.print("[dim white]2. Generate your 16-character App Password.[/dim white]")
                    console.print("[dim white]3. Run in Thanatos: [bold yellow]/smtp set smtp.gmail.com 587 your_email@gmail.com YOUR_16_CHAR_CODE[/bold yellow]\n[/dim white]")
            elif arg.startswith("set "):
                parts = arg.split(maxsplit=4)
                if len(parts) >= 5:
                    _, h, po, u, pw = parts
                    email_service.update_credentials(host=h, port=int(po), user=u, password=pw)
                    console.print(f"[bold green][✓] SMTP credentials updated for {u}@{h}:{po}[/bold green]")
                    res = email_service.verify_connection()
                    status_col = "green" if res.success else "red"
                    console.print(f"[{status_col}]{res.message}[/{status_col}]")
                else:
                    console.print("[red]Usage: /smtp set <host> <port> <username> <password>[/red]")

        elif cmd == "/audit":
            target = arg or "127.0.0.1"
            console.print(f"\n[bold cyan]• Running Defensive Port & Service Audit on: {target}[/bold cyan]")
            audit_res = await registry.dispatch("audit_authorized_services", {"host": target})
            if audit_res.success:
                data = audit_res.content
                open_svcs = data.get("open_services", [])
                console.print(f"[dim]Audited {data.get('audited_ports')} ports: [green]{len(open_svcs)} open[/green], {data.get('closed_filtered_count')} closed/filtered.[/dim]")
                for s in open_svcs:
                    console.print(f"  • [bold green]Port {s['port']}[/bold green] ({s['service']}): {s['status']} [dim]({s['risk_assessment']})[/dim]")
                console.print(f"[bold yellow]Posture:[/bold yellow] {data.get('assessment')}\n")
            else:
                console.print(f"[red]Audit error: {audit_res.error}[/red]")

        elif cmd == "/audit-web":
            url = arg or "http://localhost:8000"
            console.print(f"\n[bold cyan]• Auditing Web Security Headers: {url}[/bold cyan]")
            res = await registry.dispatch("audit_web_security_headers", {"url": url})
            if res.success:
                data = res.content
                console.print(f"[bold white]Status:[/bold white] {data.get('status_code')} │ [bold white]Rating:[/bold white] [green]{data.get('defensive_rating')}[/green]")
                present = data.get("present_security_headers", [])
                missing = data.get("missing_security_headers", [])
                if present:
                    console.print("[bold green]Present Security Headers:[/bold green]")
                    for p in present:
                        console.print(f"  [✓] [green]{p['header']}[/green]: {p['purpose']}")
                if missing:
                    console.print("[bold yellow]Missing Hardening Headers:[/bold yellow]")
                    for m in missing:
                        console.print(f"  [!] [yellow]{m['header']}[/yellow]: {m['purpose']}")
                console.print()
            else:
                console.print(f"[red]Error: {res.error}[/red]")

        elif cmd == "/nodes":
            from services.mesh.node_manager import mesh_manager
            sub = arg.split(maxsplit=1)
            action = sub[0].lower() if sub else "list"
            extra = sub[1].strip() if len(sub) > 1 else ""

            if action in ("list", ""):
                nodes = mesh_manager.list_nodes()
                console.print(f"\n[bold cyan]• Distributed LAN Mesh Nodes ({len(nodes)} Registered):[/bold cyan]")
                if not nodes:
                    console.print("  [dim yellow]No external nodes registered. Add peers with: /nodes add <ip>:<port> [node_id][/dim yellow]")
                for n in nodes:
                    status_col = "green" if n.get("status") == "online" else "red"
                    console.print(f"  • [bold white]{n.get('node_id')}[/bold white] ({n.get('endpoint')}): [{status_col}]{n.get('status').upper()}[/{status_col}] [dim]Role: {n.get('role')}[/dim]")
                specs = mesh_manager.get_local_specs()
                console.print(f"\n  [dim]Local Coordinator Host:[/dim] [green]{specs.get('hostname')}[/green] ({specs.get('os')} {specs.get('machine')})\n")

            elif action == "add":
                parts = extra.split()
                if not parts:
                    console.print("[red]Usage: /nodes add <host:port> [node_id] [role][/red]")
                else:
                    target = parts[0]
                    nid = parts[1] if len(parts) > 1 else target.replace(":", "_")
                    role = parts[2] if len(parts) > 2 else "worker"
                    if ":" in target:
                        h, p = target.split(":", 1)
                        port_num = int(p)
                    else:
                        h = target
                        port_num = 8002
                    entry = mesh_manager.register_node(node_id=nid, host=h, port=port_num, role=role)
                    console.print(f"[bold green][✓] Registered node {nid} ({entry['endpoint']})[/bold green]")
                    # Immediate ping check
                    ping_res = await mesh_manager.ping_node(nid)
                    status_col = "green" if ping_res.get("status") == "online" else "yellow"
                    console.print(f"  Status: [{status_col}]{ping_res.get('status').upper()}[/{status_col}]")

            elif action == "remove":
                if not extra:
                    console.print("[red]Usage: /nodes remove <node_id>[/red]")
                else:
                    if mesh_manager.unregister_node(extra):
                        console.print(f"[bold green][✓] Removed node: {extra}[/bold green]")
                    else:
                        console.print(f"[yellow]Node not found: {extra}[/yellow]")

            elif action == "ping":
                console.print("[dim]Pinging registered mesh nodes...[/dim]")
                results = await mesh_manager.ping_all()
                for r in results:
                    col = "green" if r.get("status") == "online" else "red"
                    console.print(f"  • {r.get('node_id')} ({r.get('endpoint')}): [{col}]{r.get('status').upper()}[/{col}]")

            elif action == "scan":
                from services.mesh.discovery import discovery_service
                console.print("[dim]Broadcasting UDP discovery beacon across local subnet...[/dim]")
                await discovery_service.start(role="coordinator", http_port=8000)
                await asyncio.sleep(2.0)
                nodes = mesh_manager.list_nodes()
                console.print(f"[bold green][✓] Discovery scan complete. {len(nodes)} node(s) discovered on LAN.[/bold green]")

            elif action == "exec":
                from services.mesh.remote_control import remote_controller
                parts = extra.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[red]Usage: /nodes exec <node_id> <command>[/red]")
                else:
                    nid, remote_cmd = parts
                    console.print(f"[dim]Dispatching command to {nid}: {remote_cmd}[/dim]")
                    res = await remote_controller.exec_on_node(nid, remote_cmd)
                    if res.get("status") == "success":
                        console.print(f"[bold green]Output from {nid}:[/bold green]\n{res.get('stdout', '')}")
                    else:
                        console.print(f"[bold red]Remote execution failed:[/bold red] {res.get('error', '')}")

            elif action == "pull":
                from services.mesh.remote_control import remote_controller
                parts = extra.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[red]Usage: /nodes pull <node_id> <model_name>[/red]")
                else:
                    nid, model_name = parts
                    console.print(f"[bold cyan]Instructing node {nid} to pull Ollama model {model_name}...[/bold cyan]")
                    res = await remote_controller.pull_model_on_node(nid, model_name)
                    if res.get("status") == "success":
                        console.print(f"[bold green][✓] Model {model_name} successfully downloaded on {nid}.[/bold green]")
                    else:
                        console.print(f"[bold red]Pull failed:[/bold red] {res.get('error', '')}")

            elif action == "sync":
                from services.mesh.sync import sync_service
                console.print("[bold cyan]• Synchronizing Profile, Resumes & Config across all mesh nodes...[/bold cyan]")
                results = await sync_service.sync_profile_to_all_nodes()
                for r in results:
                    nid = r.get("node_id")
                    console.print(f"  [✓] Node {nid}: {r.get('synced_files')} files updated, {r.get('skipped')} unchanged.")
                console.print("[bold green][✓] Mesh synchronization complete![/bold green]\n")

        else:
            console.print(f"[red]Unknown command '{cmd}'. Type [bold white]/help[/bold white] for assistance.[/red]")

    async def _handle_chat(self, user_text: str) -> None:
        """Handle standard user conversational and natural language task prompts."""
        lower = user_text.lower()

        # 1. Autonomous Natural Language Setting & Slash Command Translation
        # Allows user to speak naturally without typing slash commands manually
        if any(phrase in lower for phrase in ["scan network", "scan wifi", "find devices", "search devices", "discover nodes", "scan nodes"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Triggering subnet UDP node discovery...[/yellow]")
            await self._handle_command("/nodes scan")
            return

        if any(phrase in lower for phrase in ["sync mesh", "sync nodes", "sync files across devices", "sync profile to laptop"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Triggering manifest-based delta file synchronization across LAN mesh...[/yellow]")
            await self._handle_command("/nodes sync")
            return

        if any(phrase in lower for phrase in ["turn on preview", "enable preview", "turn on draft preview", "enable draft check"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Enabling interactive draft review gate...[/yellow]")
            await self._handle_command("/preview on")
            return

        if any(phrase in lower for phrase in ["turn off preview", "disable preview", "autopilot", "auto pilot", "disable draft check"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Disabling draft preview (Auto-Pilot active)...[/yellow]")
            await self._handle_command("/preview off")
            return

        if any(phrase in lower for phrase in ["turn on thinking", "show thinking", "enable thinking", "display reasoning"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Enabling model reasoning / think traces...[/yellow]")
            await self._handle_command("/thinking on")
            return

        if any(phrase in lower for phrase in ["turn off thinking", "hide thinking", "disable thinking", "hide reasoning"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Hiding model reasoning blocks...[/yellow]")
            await self._handle_command("/thinking off")
            return

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
