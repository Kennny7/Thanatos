with open("apps/cli/terminal_client.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update imports
old_imports = """from .ui import (
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
)"""

new_imports = """from services.database.enterprise_database_service import enterprise_db
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
)"""

code = code.replace(old_imports, new_imports)

# 2. Update /docker handler
old_docker = """        elif cmd == "/docker":
            from services.agents.site_engineer_agent import site_engineer_agent
            sub = arg.lower().strip() if arg else "status"

            if sub in ("status", ""):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Inspecting Docker Daemon & Container Topology", 0.5)
                statuses = site_engineer_agent.auto_manage_docker(action="status")
                if not statuses.get("running"):
                    console.print(f"[bold yellow]• Docker Engine Status:[/bold yellow] [red]OFFLINE[/red]")
                    console.print(f"[dim]Message:[/dim] {statuses.get('message')}")
                    console.print("[dim]Tip: Run [bold white]/docker start[/bold white] to have Velma launch Docker Desktop and deploy containers.[/dim]\\n")
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
                console.print("[dim cyan]❯ Velma Sinclair:[/dim cyan] [white]Checking if Docker Desktop needs to be launched...[/white]")
                
                def live_progress(status_text: str):
                    console.print(f"  [dim]• {status_text}[/dim]")

                res = site_engineer_agent.auto_manage_docker(action="ensure", start_if_stopped=True, status_callback=live_progress)
                orch_res = res.get("orchestrator_result", {})
                statuses = res.get("containers", {})
                running_any = any(c.get("running") for c in statuses.values() if isinstance(c, dict))
                
                if res.get("running") and (orch_res.get("success") or running_any):
                    print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Database Containers Online & Verified", 1.0)
                    up_list = [name for name, c in statuses.items() if isinstance(c, dict) and c.get("running")]
                    if up_list:
                        console.print(f"[bold green][✓] Docker is online. Active containers: {', '.join(up_list)}[/bold green]")
                    else:
                        console.print(f"[bold green][✓] Docker Desktop is online. Container deployment initiated.[/bold green]")
                    console.print()
                else:
                    err_msg = orch_res.get("output") or res.get("message") or res.get("error") or "Error deploying containers."
                    console.print(f"[bold red][!] Docker error: {err_msg}[/bold red]\\n")

            elif sub in ("stop", "down"):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Stopping Database Containers", 0.8)
                res = site_engineer_agent.auto_manage_docker(action="stop")
                console.print(f"[bold yellow][✓] Database containers stopped.[/bold yellow]\\n")
            else:
                console.print("[dim]Usage: /docker status | /docker start | /docker stop[/dim]")"""

new_docker = """        elif cmd == "/docker":
            from services.agents.site_engineer_agent import site_engineer_agent
            sub = arg.lower().strip() if arg else "status"

            if sub in ("status", ""):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Inspecting Enterprise Multi-Database Cluster")
                cluster_health = enterprise_db.get_cluster_health()
                print_enterprise_cluster_table(cluster_health)

                statuses = site_engineer_agent.auto_manage_docker(action="status")
                if not statuses.get("running"):
                    console.print(f"[bold yellow]• Host Docker Daemon:[/bold yellow] [red]OFFLINE[/red] (Local embedded SQLite & JSON fallbacks active)")
                    console.print("[dim]Tip: Run [bold white]/docker start[/bold white] to have Velma launch Docker Desktop and deploy containers.[/dim]\\n")
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
                    console.print(f"[bold red][!] Docker error: {err_msg}[/bold red]\\n")

            elif sub in ("stop", "down"):
                print_agent_breadcrumb("Velma Sinclair [Site Reliability]", "Stopping Database Containers")
                res = site_engineer_agent.auto_manage_docker(action="stop")
                console.print(f"[bold yellow][✓] Database containers stopped.[/bold yellow]\\n")
            else:
                console.print("[dim]Usage: /docker status | /docker start | /docker stop[/dim]")"""

code = code.replace(old_docker, new_docker)

# 3. Update _handle_chat
old_chat = """        # Stream coordinator execution
        self.conversation_history.append({"role": "user", "content": user_text})
        full_response = ""
        current_agent = "Thanatos"

        async for chunk in self.coordinator.execute_task_stream(user_text, self.conversation_history):
            chunk_type = chunk.get("type")

            if chunk_type == "agent_status":
                current_agent = chunk.get("agent", current_agent)
                print_agent_breadcrumb(
                    current_agent,
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
            print_assistant_response(full_response, agent_name=current_agent)"""

new_chat = """        # Stream coordinator execution
        self.conversation_history.append({"role": "user", "content": user_text})
        full_response = ""
        current_agent = "Thanatos"
        has_started_reply = False

        async for chunk in self.coordinator.execute_task_stream(user_text, self.conversation_history):
            chunk_type = chunk.get("type")

            if chunk_type in ("dag_init", "dag_update", "dag_finish"):
                print_dag_box(chunk["box"])
            elif chunk_type == "agent_status":
                current_agent = chunk.get("agent", current_agent)
                print_agent_breadcrumb(
                    current_agent,
                    chunk.get("status", ""),
                )
            elif chunk_type == "thought":
                if self.show_thinking:
                    print_thought(chunk.get("thought", ""))
            elif chunk_type == "assistant_chunk":
                content = chunk.get("content", "")
                if content:
                    full_response += content
                    if not has_started_reply:
                        console.print(f"\\n[bold cyan]❯ [{current_agent}]:[/bold cyan] ", end="")
                        has_started_reply = True
                    console.print(content, end="")

        if has_started_reply:
            console.print("\\n")

        if full_response:
            self.conversation_history.append({"role": "assistant", "content": full_response})"""

code = code.replace(old_chat, new_chat)

with open("apps/cli/terminal_client.py", "w", encoding="utf-8") as f:
    f.write(code)

print("TERMINAL_CLIENT_UPDATED")
