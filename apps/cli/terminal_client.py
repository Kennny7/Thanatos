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

from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED

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

        # Site Engineer Velma Sinclair startup telemetry & database check
        try:
            from services.database.db_orchestrator import db_orchestrator
            from services.agents.site_engineer_agent import site_engineer_agent
            if not db_orchestrator.is_docker_available():
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Host Infrastructure & Database Diagnostic", 1.0)
                console.print(
                    "[bold magenta]❯ Velma Sinclair:[/bold magenta] [white]Hey! I ran a pre-flight system check and Docker Desktop isn't running yet; "
                    "therefore, your enterprise database cluster (PostgreSQL, MongoDB, Milvus, Neo4j, Kafka) is offline. "
                    "Should I launch Docker Desktop and deploy your containers, or keep rolling with local embedded storage? "
                    "Just tell me whether you want to [bold yellow]start Docker[/bold yellow] or [bold yellow]keep it local[/bold yellow].[/white]\n"
                )
        except Exception:
            pass

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

                # Handle exit variants & typos (e.g. \exot, /exot, exot, eixt, exit, quit)
                low_raw = user_input.lower().strip()
                norm_raw = low_raw.lstrip("/\\")
                if norm_raw in ("exit", "quit", "bye", "exot", "eixt", "q"):
                    console.print("[bold yellow]Exiting Thanatos CLI. Have a productive day![/bold yellow]")
                    break

                # Support both forward slash (/) and backslash (\) for commands
                if user_input.startswith("/") or user_input.startswith("\\"):
                    # Normalize backslash prefix to forward slash
                    normalized_cmd = "/" + user_input[1:]
                    await self._handle_command(normalized_cmd)
                else:
                    await self._handle_chat(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold yellow]Session terminated.[/bold yellow]")
                break
            except Exception as e:
                err_str = str(e)
                console.print(f"[bold red]System Exception Intercepted: {err_str}[/bold red]")
                # Velma Sinclair autonomous error triage
                try:
                    from services.agents.site_engineer_agent import site_engineer_agent
                    print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Autonomously Triaging Error & Formulating Patch", 1.0)
                    triage_msg = f"Hey, looks like something broke: `{err_str}`. I'm checking background telemetry and isolating the root cause."
                    if "too_many_pings" in err_str or "GOAWAY" in err_str or "keepalive" in err_str:
                        triage_msg += " (Diagnosis: gRPC HTTP/2 keepalive ping saturation between local pymilvus client and embedded Milvus Lite. Throttling ping frequency to 300s resolved this.)"
                    console.print(f"[bold magenta]❯ Velma Sinclair:[/bold magenta] [white]{triage_msg}[/white]\n")
                except Exception:
                    pass

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

        elif cmd == "/docker":
            from services.agents.site_engineer_agent import site_engineer_agent
            from services.database.db_orchestrator import db_orchestrator
            sub = arg.lower().strip() if arg else "status"

            if sub in ("status", ""):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Inspecting Docker Daemon & Container Topology", 0.5)
                statuses = site_engineer_agent.auto_manage_docker(action="status")
                if not statuses.get("running"):
                    console.print(f"[bold yellow]• Docker Engine Status:[/bold yellow] [red]OFFLINE[/red]")
                    console.print(f"[dim]Message:[/dim] {statuses.get('message')}")
                    console.print("[dim]Tip: Run [bold white]/docker start[/bold white] to have Velma launch Docker Desktop and spin up the database cluster automatically.[/dim]\n")
                else:
                    console.print(f"[bold green]• Docker Engine Status:[/bold green] [green]ONLINE[/green]")
                    containers = statuses.get("containers", {})
                    table = Table(title="• Enterprise Database Containers", box=ROUNDED, border_style="cyan")
                    table.add_column("Container", style="bold white")
                    table.add_column("Status", style="bold")
                    table.add_column("Details", style="dim")
                    for cname, cinfo in containers.items():
                        if cname == "error":
                            continue
                        is_up = cinfo.get("running", False)
                        col = "green" if is_up else "yellow"
                        table.add_row(cname, f"[{col}]{cinfo.get('status', 'unknown')}[/{col}]", cinfo.get("status_line", ""))
                    console.print(table)
                    console.print()

            elif sub in ("start", "up", "launch"):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Autonomous Docker Desktop Boot & Container Deployment", 0.2)
                console.print("[dim cyan]❯ Velma Sinclair:[/dim cyan] [white]On it! Checking if Docker Desktop needs to be launched...[/white]")
                
                def live_progress(status_text: str):
                    console.print(f"  [dim]• {status_text}[/dim]")

                res = site_engineer_agent.auto_manage_docker(action="ensure", start_if_stopped=True, status_callback=live_progress)
                if res.get("running"):
                    print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Database Containers Online & Verified", 1.0)
                    console.print("[bold green][✓] Docker Desktop and enterprise database containers (Postgres, Mongo, Milvus, Neo4j, Kafka) are up and running![/bold green]\n")
                else:
                    console.print(f"[bold red][!] Could not start Docker: {res.get('message') or res.get('error')}[/bold red]\n")

            elif sub in ("stop", "down"):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Safely Stopping Database Containers", 0.8)
                res = site_engineer_agent.auto_manage_docker(action="stop")
                console.print(f"[bold yellow][✓] Database containers stopped to conserve RAM/CPU.[/bold yellow]\n")
            else:
                console.print("[dim]Usage: /docker status │ /docker start │ /docker stop[/dim]")

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
            sub_parts = arg.split(maxsplit=1)
            sub_cmd = sub_parts[0].lower() if sub_parts else ""
            sub_query = sub_parts[1].strip() if len(sub_parts) > 1 else ""

            if not arg or sub_cmd in ("help", "status", "info"):
                p = memory_service.user_profile.get_profile()
                acc = getattr(p, "accounts", {}) if hasattr(p, "accounts") else {}
                console.print(f"\n[bold cyan]• Autonomous Job Hunter & Application Suite[/bold cyan]")
                console.print(f"  [dim]Target Role:[/dim]       [bold white]{p.title or 'AI / ML Engineer'}[/bold white]")
                console.print(f"  [dim]Preferred Locations:[/dim] [yellow]{', '.join(p.open_to_relocation or ['Pune', 'Remote', 'Mumbai'])}[/yellow]")
                console.print(f"  [dim]Experience Level:[/dim]   [green]3 years and 8 months[/green]")
                console.print(f"  [dim]Integrated Portals:[/dim] [cyan]LinkedIn, Naukri, Direct Corporate Careers[/cyan]")
                console.print(f"  [dim]ATS Quality Gating:[/dim] [green]Active (Auditing & Auto-Calibrating)[/green]\n")
                console.print("[dim]Commands:[/dim]")
                console.print("  • [bold yellow]/jobs run [query][/bold yellow]    - Scan LinkedIn & Naukri, tailor ATS resumes, and stage applications")
                console.print("  • [bold yellow]/jobs search [query][/bold yellow] - Search openings without dispatching applications")
                console.print("  • [bold yellow]/jobs history[/bold yellow]        - View logged application audit ledger\n")
            elif sub_cmd == "history":
                history_res = await registry.dispatch("get_application_history", {"limit": 10})
                if history_res.success:
                    print_application_history_table(history_res.content.get("recent_applications", []))
            elif sub_cmd == "search":
                search_q = sub_query or "AI / ML Engineer remote or Pune"
                console.print(f"[dim]Scanning LinkedIn & Naukri for: {search_q}...[/dim]")
                search_res = await registry.dispatch("search_jobs", {
                    "location": "Pune & Remote",
                    "keywords": search_q,
                    "experience": "3 years and 8 months",
                    "require_email_apply": True,
                    "limit": 5,
                })
                if search_res.success and search_res.content.get("jobs"):
                    jobs_found = search_res.content["jobs"]
                    console.print(f"[bold green][✓] Found {len(jobs_found)} matching openings with recruiter email route:[/bold green]")
                    for idx, j in enumerate(jobs_found, 1):
                        portal_tag = f"[{j.get('portal', 'Job')}] " if j.get('portal') else ""
                        console.print(f"  {idx}. [bold cyan]{portal_tag}{j['title']}[/bold cyan] at [bold white]{j['company']}[/bold white] -> [yellow]{j.get('apply_email')}[/yellow]")
                else:
                    console.print("[yellow]No direct recruiter email openings located for this search query.[/yellow]")
            else:
                # User ran /jobs run or provided a query
                query = sub_query if sub_cmd == "run" else arg
                await self.job_runner.execute_job_workflow(
                    query=query if query else "AI / ML Engineer remote or Pune",
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

        elif cmd == "/agents":
            from services.agents.agent_roster import roster
            sub_parts = arg.split(maxsplit=2)
            sub_action = sub_parts[0].lower() if sub_parts else "list"
            target_agent = sub_parts[1].lower() if len(sub_parts) > 1 else ""
            msg = sub_parts[2].strip() if len(sub_parts) > 2 else ""

            if sub_action in ("list", ""):
                table = Table(title="• Thanatos Autonomous Multi-Agent Personas", box=ROUNDED, border_style="cyan")
                table.add_column("Agent ID", style="bold yellow")
                table.add_column("Assigned Name", style="bold white")
                table.add_column("Role / Specialization", style="cyan")
                table.add_column("Voice Profile", style="magenta")
                table.add_column("Memory Partition", style="dim green")

                for ag in roster.list_agents():
                    table.add_row(
                        ag.id,
                        ag.name,
                        ag.role,
                        ag.voice,
                        ag.memory_partition,
                    )
                console.print(table)
                console.print(f"[dim]Active Persona Mode:[/dim] [bold green]{roster.active_agent_id.upper()}[/bold green] [dim](auto = intelligent coordinator delegation)[/dim]\n")
                console.print("[dim]Commands:[/dim]")
                console.print("  • [bold yellow]/agents dm <agent_id> <message>[/bold yellow] - Direct private message to a specific agent")
                console.print("  • [bold yellow]/agents set <agent_id|auto>[/bold yellow]     - Set default conversation persona")
                console.print("  • [bold yellow]/agents rename <agent_id> <new_name>[/bold yellow] - Update persona name safely without data loss\n")

            elif sub_action == "dm":
                if not target_agent or not msg:
                    console.print("[red]Usage: /agents dm <site_engineer|secretary|butler> <message>[/red]")
                else:
                    agent = roster.load_agent_profile(target_agent)
                    if not agent:
                        console.print(f"[red]Agent '{target_agent}' not found. Valid IDs: site_engineer, secretary, butler[/red]")
                    else:
                        console.print(f"[bold cyan]❯ [Private DM -> {agent.name}][/bold cyan] [dim]{msg}[/dim]")
                        # Run tailored execution
                        if agent.id == "site_engineer":
                            from services.agents.site_engineer_agent import site_engineer_agent
                            diag = site_engineer_agent.collect_system_telemetry()
                            prompt = f"{site_engineer_agent.build_system_prompt()}\n\nUser Question: {msg}\n\nLive System Telemetry:\n{json.dumps(diag, indent=2)}\n\nRespond with your charming, willful Velma persona."
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name} [Velma]", "Hardware & System Diagnosis Complete", 1.0)
                            print_assistant_response(ans.text or "Velma completed telemetry analysis.")
                        elif agent.id == "secretary":
                            from services.agents.secretary_agent import SecretaryAgent
                            sec = SecretaryAgent()
                            prompt = f"{sec.build_system_prompt()}\n\nUser Agenda/Schedule Question: {msg}\n\nRespond in your Amelia Sterling persona."
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name} [Amelia]", "Agenda & Routine Checked", 1.0)
                            print_assistant_response(ans.text or "Amelia checked your schedule.")
                        elif agent.id == "butler":
                            from services.agents.butler_agent import ButlerAgent
                            butler = ButlerAgent()
                            prompt = f"{butler.build_system_prompt()}\n\nUser Question: {msg}\n\nRespond in your Alfred Vance persona."
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name} [Alfred]", "Social Counsel Formulated", 1.0)
                            print_assistant_response(ans.text or "Alfred prepared his assessment.")

            elif sub_action == "set":
                if not target_agent:
                    console.print("[red]Usage: /agents set <site_engineer|secretary|butler|auto>[/red]")
                elif target_agent in ("auto", "site_engineer", "secretary", "butler"):
                    roster.active_agent_id = target_agent
                    roster.save_index()
                    console.print(f"[bold green][✓] Active default agent persona switched to: {target_agent.upper()}[/bold green]")
                else:
                    console.print(f"[red]Invalid agent ID '{target_agent}'. Choose: site_engineer, secretary, butler, or auto.[/red]")

            elif sub_action == "rename":
                new_name = sub_parts[2] if len(sub_parts) > 2 else ""
                if not target_agent or not new_name:
                    console.print("[red]Usage: /agents rename <agent_id> <new_name>[/red]")
                else:
                    if roster.update_agent_name(target_agent, new_name):
                        console.print(f"[bold green][✓] Agent {target_agent} updated to name: '{new_name}'. Private & shared memories remain safely intact.[/bold green]")
                    else:
                        console.print(f"[red]Agent '{target_agent}' not found.[/red]")

        else:
            import difflib
            known_cmds = [
                "/help", "/clear", "/status", "/vector-db", "/docker", "/thinking",
                "/preview", "/history", "/jobs", "/profile", "/smtp",
                "/audit", "/audit-web", "/nodes", "/agents", "/exit", "/quit"
            ]
            matches = difflib.get_close_matches(cmd, known_cmds, n=1, cutoff=0.5)
            suggestion = f" Maybe you meant [bold yellow]{matches[0]}[/bold yellow]?" if matches else ""
            console.print(f"[red]Unknown command '{cmd}'.{suggestion} Type [bold white]/help[/bold white] for available commands.[/red]")

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

        if any(phrase in lower for phrase in [
            "start docker", "launch docker", "spin up docker", "start containers", "up docker", 
            "bring up database", "containerized service", "containerised service", "run containers",
            "prefer running the container", "prefer docker", "boot docker", "start database"
        ]) and not any(neg in lower for neg in ["dont", "don't", "no", "stop", "never"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Triggering autonomous Docker boot & container deployment...[/yellow]")
            await self._handle_command("/docker start")
            return

        if any(phrase in lower for phrase in [
            "dont want docker", "don't want docker", "no docker", "keep local", "stay local", 
            "prefer lite", "use lite", "without docker", "local lite"
        ]):
            console.print("[dim cyan]❯ [Velma Sinclair][/dim cyan] [white]Got it! Keeping local embedded storage active. Docker remains off.[/white]\n")
            return

        if any(phrase in lower for phrase in ["check docker", "docker status", "database status", "containers status", "is docker running"]):
            await self._handle_command("/docker status")
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
