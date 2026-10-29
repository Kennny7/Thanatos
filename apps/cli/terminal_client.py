# Thanatos/apps/cli/terminal_client.py

import asyncio
import os
import sys
import json
from typing import Any, Dict, List, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from shared.settings import Settings, runtime_settings
from services.llm_brain.provider import UnifiedLLMProvider
from services.llm_brain.coordinator import AgentCoordinator
from services.memory.memory_manager import memory_service
from services.agents.agent_roster import roster
from services.agents.agent_bus import agent_bus
from services.agents.project_manager import project_manager
from plugins.base.registry import init_default_skills, registry

from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED

from services.database.enterprise_database_service import enterprise_db
from .ui import (
    console,
    print_banner,
    print_thought,
    print_agent_breadcrumb,
    print_assistant_response,
    print_vector_status,
    print_help,
    print_task_notification,
    print_task_table,
    print_task_detail,
    print_dag_box,
    print_enterprise_cluster_table,
)

prompt_style = Style.from_dict({
    "prompt": "#00d7ff bold",
})


class ThanatosCLI:
    """
    Interactive Linux-style terminal client for Thanatos AI.
    Provides direct command and conversational access with streaming thoughts,
    system diagnostics, multi-agent growth collaboration, project workspace management,
    mesh networking, and Docker control.
    """

    def __init__(self) -> None:
        init_default_skills()
        self.settings = Settings.load()
        self.provider = UnifiedLLMProvider(self.settings)
        self.coordinator = AgentCoordinator(self.provider)
        self.show_thinking = True
        self.collapse_thinking = True
        self.last_thought = ""
        self.last_thought_agent = ""
        self.conversation_history: List[Dict[str, Any]] = []

        # Register background task notification callback
        from services.background.task_manager import task_manager
        self._task_manager = task_manager
        task_manager.set_notification_callback(print_task_notification)

    async def execute_single_command(self, cmd_input: str) -> None:
        """Execute a single non-interactive command or query and exit cleanly."""
        cmd_input = cmd_input.strip()
        if not cmd_input:
            return
        if cmd_input.startswith("/") or cmd_input.startswith("\\"):
            await self._handle_command("/" + cmd_input.lstrip("/\\"))
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
                    "[bold magenta]❯ Velma Sinclair:[/bold magenta] [white]Docker Desktop isn't running yet; "
                    "enterprise database cluster (PostgreSQL, MongoDB, Milvus, Neo4j, Kafka) is offline. "
                    "Type [bold yellow]/docker start[/bold yellow] or tell me to launch Docker anytime, or keep rolling with local embedded storage.[/white]\n"
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

                low_raw = user_input.lower().strip()
                norm_raw = low_raw.lstrip("/\\")
                if norm_raw in ("exit", "quit", "bye", "exot", "eixt", "q"):
                    console.print("[bold yellow]Exiting Thanatos CLI. Have a productive day![/bold yellow]")
                    break

                if user_input.startswith("/") or user_input.startswith("\\"):
                    normalized_cmd = "/" + user_input.lstrip("/\\")
                    await self._handle_command(normalized_cmd)
                else:
                    try:
                        await self._handle_chat(user_input)
                    except (asyncio.CancelledError, KeyboardInterrupt):
                        console.print("\n[bold yellow]Generation interrupted by user.[/bold yellow]\n")

            except (KeyboardInterrupt, EOFError):
                console.print("\n[bold yellow]Session terminated.[/bold yellow]")
                break
            except Exception as e:
                err_str = str(e)
                console.print(f"[bold red]System Exception Intercepted: {err_str}[/bold red]")
                try:
                    from services.agents.site_engineer_agent import site_engineer_agent
                    print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Autonomously Triaging Error", 1.0)
                    triage_msg = f"Error intercepted: `{err_str}`."
                    if "too_many_pings" in err_str or "GOAWAY" in err_str or "keepalive" in err_str:
                        triage_msg += " (Diagnosis: gRPC keepalive saturation. Throttled ping frequency.)"
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
            active_entry = roster.get_agent_index_entry(roster.active_agent_id)
            active_name = active_entry.name if active_entry else "Alfred Vance"
            console.print(f"  [dim]Active Persona:[/dim] [cyan]{active_name} ({roster.active_agent_id})[/cyan]\n")

        elif cmd == "/undo":
            res = project_manager.undo_last_change(arg if arg else None)
            level = "bold green" if res.get("success") else "bold yellow"
            console.print(f"[{level}]{res.get('message')}[/{level}]\n")

        elif cmd == "/bus":
            dialogue = agent_bus.get_recent_dialogue(limit=8)
            table = Table(title="• Inter-Agent Communication Bus", box=ROUNDED, border_style="cyan")
            table.add_column("Time", style="dim")
            table.add_column("Sender", style="bold yellow")
            table.add_column("Recipient", style="dim cyan")
            table.add_column("Message", style="white")

            for m in dialogue:
                table.add_row(m.timestamp, m.sender, m.recipient, m.content)
            console.print(table)
            console.print()

        elif cmd == "/vector-db":
            diag = memory_service.vector_store.verify_and_diagnose()
            print_vector_status(diag)

        elif cmd == "/docker":
            from services.agents.site_engineer_agent import site_engineer_agent
            sub = arg.lower().strip() if arg else "status"

            if sub in ("status", ""):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Inspecting Enterprise Multi-Database Cluster")
                cluster_health = enterprise_db.get_cluster_health()
                print_enterprise_cluster_table(cluster_health)

                statuses = site_engineer_agent.auto_manage_docker(action="status")
                if not statuses.get("running"):
                    console.print(f"[bold yellow]• Host Docker Daemon:[/bold yellow] [red]OFFLINE[/red] (Local embedded SQLite & JSON fallbacks active)")
                    console.print("[dim]Tip: Run [bold white]/docker start[/bold white] to have Velma launch Docker Desktop and deploy containers.[/dim]\n")
                else:
                    containers = statuses.get("containers", {})
                    table = Table(title="• Container Topology", box=ROUNDED, border_style="cyan")
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
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Autonomous Docker Boot & Enterprise Cluster Deployment")
                console.print("[dim cyan]❯ Velma Sinclair:[/dim cyan] [white]Launching Docker Desktop and provisioning database containers...[/white]")
                
                def live_progress(status_text: str):
                    console.print(f"  [dim]• {status_text}[/dim]")

                res = site_engineer_agent.auto_manage_docker(action="ensure", start_if_stopped=True, status_callback=live_progress)
                orch_res = res.get("orchestrator_result", {})
                statuses = res.get("containers", {})
                running_any = any(c.get("running") for c in statuses.values() if isinstance(c, dict))
                
                if res.get("running") and (orch_res.get("success") or running_any):
                    print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Enterprise Database Cluster Online")
                    cluster_health = enterprise_db.get_cluster_health()
                    print_enterprise_cluster_table(cluster_health)
                else:
                    err_msg = orch_res.get("output") or res.get("message") or res.get("error") or "Error deploying containers."
                    console.print(f"[bold red][!] Docker error: {err_msg}[/bold red]\n")

            elif sub in ("stop", "down"):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Stopping Database Containers")
                res = site_engineer_agent.auto_manage_docker(action="stop")
                console.print(f"[bold yellow][✓] Database containers stopped.[/bold yellow]\n")
            else:
                console.print("[dim]Usage: /docker status | /docker start | /docker stop[/dim]")

        elif cmd == "/thinking":
            sub = arg.lower().strip()
            if sub in ("on", "true", "1"):
                self.show_thinking = True
                console.print("[bold green][✓] Model reasoning / thinking display enabled.[/bold green]")
            elif sub in ("off", "false", "0"):
                self.show_thinking = False
                console.print("[bold yellow][✓] Model thinking display hidden.[/bold yellow]")
            elif sub in ("collapse", "collapsed"):
                self.collapse_thinking = True
                self.show_thinking = True
                console.print("[bold green][✓] Thinking panel is now COLLAPSED by default (compact view).[/bold green]")
            elif sub in ("expand", "expanded", "full"):
                self.collapse_thinking = False
                self.show_thinking = True
                console.print("[bold green][✓] Thinking panel is now EXPANDED by default (full view).[/bold green]")
            elif sub in ("last", "view"):
                if self.last_thought:
                    print_thought(self.last_thought, agent_name=self.last_thought_agent, collapsed=False)
                else:
                    console.print("[dim]No previous thinking block recorded in this session.[/dim]")
            else:
                status = "ON" if self.show_thinking else "OFF"
                mode = "COLLAPSED" if self.collapse_thinking else "EXPANDED"
                console.print(f"[dim]Thinking display: [bold]{status}[/bold] (Default view: [bold]{mode}[/bold]). Usage: /thinking [collapse | expand | on | off | last][/dim]")

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
                console.print("[bold cyan]• Synchronizing Config & Documents across all mesh nodes...[/bold cyan]")
                results = await sync_service.sync_profile_to_all_nodes()
                for r in results:
                    nid = r.get("node_id")
                    console.print(f"  [✓] Node {nid}: {r.get('synced_files')} files updated, {r.get('skipped')} unchanged.")
                console.print("[bold green][✓] Mesh synchronization complete![/bold green]\n")

        elif cmd == "/agents":
            sub_parts = arg.split(maxsplit=2)
            sub_action = sub_parts[0].lower() if sub_parts else "list"
            target_agent = sub_parts[1].lower() if len(sub_parts) > 1 else ""
            msg = sub_parts[2].strip() if len(sub_parts) > 2 else ""

            if sub_action in ("list", ""):
                table = Table(title="• Thanatos Autonomous Multi-Agent Personas", box=ROUNDED, border_style="cyan")
                table.add_column("Agent ID", style="bold yellow")
                table.add_column("Assigned Name", style="bold white")
                table.add_column("Role / Specialization", style="cyan")
                table.add_column("Active", justify="center")

                for ag in roster.list_agents():
                    is_act = "[bold green]YES[/bold green]" if ag.id == roster.active_agent_id else "[dim]No[/dim]"
                    table.add_row(
                        ag.id,
                        ag.name,
                        ag.role,
                        is_act,
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
                        if agent.id == "site_engineer":
                            from services.agents.site_engineer_agent import site_engineer_agent
                            diag = site_engineer_agent.collect_system_telemetry()
                            prompt = (
                                f"{site_engineer_agent.build_system_prompt()}\n\n"
                                f"User Direct Message: {msg}\n"
                                f"System Status: CPU {diag.get('cpu_percent')}% | RAM {diag.get('virtual_memory', {}).get('percent')}%\n\n"
                                "Reply naturally and concisely like in a chat without essays:"
                            )
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name}", "System Inspected", 1.0)
                            print_assistant_response(ans.text or "Diagnostics complete.", agent_name=agent.name)
                            agent_bus.post_message(agent.name, "User (DM)", ans.text or "")

                        elif agent.id == "secretary":
                            from services.agents.secretary_agent import SecretaryAgent
                            sec = SecretaryAgent()
                            prompt = (
                                f"{sec.build_system_prompt()}\n\n"
                                f"User Direct Message: {msg}\n\n"
                                "Reply naturally and concisely like in a chat without essays:"
                            )
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name}", "Agenda Evaluated", 1.0)
                            print_assistant_response(ans.text or "Agenda checked.", agent_name=agent.name)
                            agent_bus.post_message(agent.name, "User (DM)", ans.text or "")

                        elif agent.id == "butler":
                            from services.agents.butler_agent import ButlerAgent
                            butler = ButlerAgent()
                            prompt = (
                                f"{butler.build_system_prompt()}\n\n"
                                f"User Direct Message: {msg}\n\n"
                                "Reply with discreet gentlemanly counsel, natural and concise without essays:"
                            )
                            ans = await self.provider.generate(prompt=prompt, stream=False)
                            print_agent_breadcrumb(f"{agent.name}", "Counsel Prepared", 1.0)
                            print_assistant_response(ans.text or "Counsel prepared.", agent_name=agent.name)
                            agent_bus.post_message(agent.name, "User (DM)", ans.text or "")

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
                        console.print(f"[bold green][✓] Agent {target_agent} updated to name: '{new_name}'. Memories remain safely intact.[/bold green]")
                    else:
                        console.print(f"[red]Agent '{target_agent}' not found.[/red]")

        elif cmd == "/tasks":
            sub_parts = arg.split(maxsplit=1) if arg else []
            sub_cmd = sub_parts[0].lower() if sub_parts else "list"

            if sub_cmd == "list":
                print_task_table(self._task_manager.list_tasks())
            elif sub_cmd == "view":
                tid = sub_parts[1].strip() if len(sub_parts) > 1 else ""
                if not tid:
                    console.print("[red]Usage: /tasks view <task-id>[/red]")
                else:
                    task = self._task_manager.get_task(tid)
                    if task:
                        print_task_detail(task)
                    else:
                        console.print(f"[red]No task found with ID '{tid}'.[/red]")
            elif sub_cmd == "cancel":
                tid = sub_parts[1].strip() if len(sub_parts) > 1 else ""
                if not tid:
                    console.print("[red]Usage: /tasks cancel <task-id>[/red]")
                elif self._task_manager.cancel_task(tid):
                    console.print(f"[bold yellow]⏹ Task '{tid}' cancellation requested.[/bold yellow]")
                else:
                    console.print(f"[red]Cannot cancel task '{tid}' (not found or already finished).[/red]")
            elif sub_cmd == "clear":
                removed = self._task_manager.clear_completed()
                console.print(f"[bold green][✓] Cleared {removed} completed/failed task(s).[/bold green]")
            else:
                console.print("[red]Usage: /tasks [list|view <id>|cancel <id>|clear][/red]")

        else:
            import difflib
            known_cmds = [
                "/help", "/clear", "/status", "/vector-db", "/docker", "/thinking",
                "/preview", "/nodes", "/agents", "/bus", "/undo", "/tasks", "/exit", "/quit"
            ]
            matches = difflib.get_close_matches(cmd, known_cmds, n=1, cutoff=0.5)
            suggestion = f" Maybe you meant [bold yellow]{matches[0]}[/bold yellow]?" if matches else ""
            console.print(f"[red]Unknown command '{cmd}'.{suggestion} Type [bold white]/help[/bold white] for available commands.[/red]")

    async def _handle_chat(self, user_text: str) -> None:
        """Handle conversational interactions and natural language task executions."""
        lower = user_text.lower()

        # Autonomous natural language command triggers
        if any(phrase in lower for phrase in ["scan network", "scan wifi", "find devices", "search devices", "discover nodes", "scan nodes"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Triggering subnet UDP node discovery...[/yellow]")
            await self._handle_command("/nodes scan")
            return

        if any(phrase in lower for phrase in ["sync mesh", "sync nodes", "sync files across devices", "sync config to laptop"]):
            console.print("[dim cyan]❯ [Autonomous Action Gate][/dim cyan] [yellow]Triggering delta file synchronization across LAN mesh...[/yellow]")
            await self._handle_command("/nodes sync")
            return

        if any(phrase in lower for phrase in ["turn on preview", "enable preview", "turn on draft preview"]):
            await self._handle_command("/preview on")
            return

        if any(phrase in lower for phrase in ["turn off preview", "disable preview", "autopilot", "auto pilot"]):
            await self._handle_command("/preview off")
            return

        if any(phrase in lower for phrase in ["turn on thinking", "show thinking", "enable thinking", "display reasoning"]):
            await self._handle_command("/thinking on")
            return

        if any(phrase in lower for phrase in ["turn off thinking", "hide thinking", "disable thinking", "hide reasoning"]):
            await self._handle_command("/thinking off")
            return

        if any(phrase in lower for phrase in [
            "start docker", "launch docker", "spin up docker", "start containers", "up docker", 
            "bring up database", "boot docker", "start database"
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

        # Stream coordinator execution
        self.conversation_history.append({"role": "user", "content": user_text})
        full_response = ""
        current_agent = "Thanatos"
        has_started_reply = False
        accumulated_thought = ""
        live_thinking_active = False

        def flush_thought():
            nonlocal accumulated_thought, live_thinking_active
            if live_thinking_active:
                console.print("\r" + " " * 80 + "\r", end="")
                live_thinking_active = False
            if accumulated_thought.strip() and self.show_thinking:
                self.last_thought = accumulated_thought.strip()
                self.last_thought_agent = current_agent
                print_thought(
                    accumulated_thought.strip(),
                    agent_name=current_agent,
                    collapsed=self.collapse_thinking,
                )
                accumulated_thought = ""

        # Display immediate status indicator while waiting for first tokens
        console.print("[dim cyan]Reasoning and preparing response...[/dim cyan]", end="\r")
        live_thinking_active = True

        async for chunk in self.coordinator.execute_task_stream(user_text, self.conversation_history):
            chunk_type = chunk.get("type")
            chunk_agent = chunk.get("agent")

            if chunk_type in ("dag_init", "dag_update", "dag_finish"):
                flush_thought()
                print_dag_box(chunk["box"])
            elif chunk_type == "agent_status":
                flush_thought()
                if chunk_agent:
                    current_agent = chunk_agent
                print_agent_breadcrumb(
                    current_agent,
                    chunk.get("status", ""),
                )
            elif chunk_type == "thought":
                if chunk_agent:
                    current_agent = chunk_agent
                thought_piece = chunk.get("thought", "")
                if thought_piece:
                    accumulated_thought += thought_piece
            elif chunk_type == "assistant_chunk":
                flush_thought()
                # If a different agent speaks, close current message block cleanly and start a new message line
                if chunk_agent and chunk_agent != current_agent:
                    if has_started_reply:
                        console.print("\n")
                        has_started_reply = False
                    current_agent = chunk_agent

                content = chunk.get("content", "")
                if content:
                    full_response += content
                    if not has_started_reply:
                        console.print(f"\n[bold cyan]❯ [{current_agent}]:[/bold cyan] ", end="")
                        has_started_reply = True
                    console.print(content, end="")

        flush_thought()

        if has_started_reply:
            console.print("\n")

        if full_response:
            self.conversation_history.append({"role": "assistant", "content": full_response})


def main() -> None:
    cli = ThanatosCLI()
    asyncio.run(cli.start())


if __name__ == "__main__":
    main()
