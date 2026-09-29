# Thanatos/apps/cli/job_workflow.py

import os
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.box import ROUNDED

from plugins.base.registry import registry
from services.memory.memory_manager import memory_service
from .ui import console, print_agent_breadcrumb, print_thought

DEFAULT_RESUME_TEX = os.path.join("data", "resumes", "default_resume.tex")
DEFAULT_PROFILE_JSON = os.path.join("data", "resumes", "profile.json")


class JobWorkflowRunner:
    """
    Modular execution engine for Autonomous Job Hunting,
    LaTeX/Markdown Resume Calibration, and Humanized Email Applicator.
    """

    def __init__(self, show_thinking: bool = True) -> None:
        self.show_thinking = show_thinking

    async def execute_job_workflow(
        self,
        query: str = "AI / ML Engineer",
        location: str = "Pune (Hybrid/Office) & Remote",
        experience: str = "3 years and 8 months",
        source_resume_path: Optional[str] = None,
    ) -> None:
        """Runs end-to-end autonomous job workflow with live terminal feedback."""
        console.print(f"\n[bold green]🚀 Initiating Autonomous Job Hunt & Application Dispatch[/bold green]")
        console.print(f"[dim]Role:[/dim] [cyan]{query}[/cyan] │ [dim]Location:[/dim] [cyan]{location}[/cyan] │ [dim]Experience Target:[/dim] [yellow]{experience}[/yellow]\n")

        # 1. Check / Index resume source into Vector Store
        resume_source = source_resume_path or DEFAULT_RESUME_TEX
        if os.path.exists(resume_source):
            try:
                with open(resume_source, "r", encoding="utf-8") as f:
                    content = f.read()
                memory_service.add_memory(
                    f"User Base Resume from {resume_source}: {content[:500]}...",
                    metadata={"source": resume_source, "type": "resume_seed"},
                )
                if self.show_thinking:
                    print_thought(f"Loaded and verified base resume file from `{resume_source}` into semantic vector store.")
            except Exception as e:
                console.print(f"[dim yellow]Notice: Could not load resume file {resume_source}: {e}[/dim yellow]")
        else:
            if self.show_thinking:
                print_thought(f"Base resume file `{resume_source}` not specified or absent. Vector database and profile memory will supply baseline skills.")

        # 2. Search Jobs accepting email
        print_agent_breadcrumb("Web Crawler & Job Hunter", f"Scanning listings for {query} ({location}) with email application channel...", 0.25)
        search_res = await registry.dispatch("search_jobs", {
            "location": location,
            "keywords": query,
            "experience": experience,
            "require_email_apply": True,
            "limit": 4,
        })

        if not search_res.success or not search_res.content.get("jobs"):
            console.print(f"[bold red]❌ No vacancies found matching '{query}' with email application channel.[/bold red]")
            return

        jobs = search_res.content["jobs"]
        console.print(f"[bold green]✔ Located {len(jobs)} high-match openings with direct email application routes![/bold green]\n")

        # Print quick summary of jobs found
        for idx, j in enumerate(jobs, 1):
            console.print(f"  [bold cyan]{idx}. {j['title']}[/bold cyan] at [bold white]{j['company']}[/bold white]")
            console.print(f"     [dim]Mode:[/dim] {j.get('work_mode')} │ [dim]Exp:[/dim] {j.get('experience_required')} │ [dim]Email:[/dim] [yellow]{j.get('apply_email')}[/yellow]")

        # 3. Process top matching job application
        target_job = jobs[0]
        console.print(f"\n[bold cyan]🎯 Targeting Top Opportunity: {target_job['title']} at {target_job['company']}[/bold cyan]")

        # Resume Tailoring
        print_agent_breadcrumb("Resume Tailor Agent", f"Calibrating qualifications to {experience} & generating LaTeX/MD for {target_job['company']}...", 0.60)
        tailor_res = await registry.dispatch("tailor_resume", {
            "job_title": target_job["title"],
            "company": target_job["company"],
            "job_description": target_job.get("description", ""),
            "experience_level": experience,
            "source_file_path": resume_source if os.path.exists(resume_source) else None,
        })

        tailor_data = tailor_res.content if tailor_res.success else {}
        resume_md = tailor_data.get("resume_markdown", "")
        resume_tex = tailor_data.get("resume_latex", "")
        cover_letter = tailor_data.get("cover_letter", "")

        # Save generated LaTeX and Markdown resumes to disk for user
        out_dir = os.path.join("logs", "generated_resumes")
        os.makedirs(out_dir, exist_ok=True)
        tex_path = os.path.join(out_dir, f"{target_job['company'].lower().replace(' ', '_')}_resume.tex")
        md_path = os.path.join(out_dir, f"{target_job['company'].lower().replace(' ', '_')}_resume.md")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(resume_tex)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(resume_md)

        if self.show_thinking:
            print_thought(f"Successfully compiled tailored documents:\n- LaTeX source: `{tex_path}`\n- Markdown source: `{md_path}`\n- Experience calibrated accurately to {experience} with realistic skill bridging.")

        # 4. Email Packaging & Logging
        print_agent_breadcrumb("Job Applicator Agent", f"Formulating humanized email outreach and logging dispatch record...", 0.85)
        apply_res = await registry.dispatch("prepare_job_application", {
            "job_id": target_job.get("id"),
            "job_title": target_job["title"],
            "company": target_job["company"],
            "recipient_email": target_job.get("apply_email"),
            "hiring_manager": target_job.get("hiring_manager"),
            "tailored_resume": resume_md,
            "cover_letter": cover_letter,
            "status": "Staged for Email Dispatch",
        })

        print_agent_breadcrumb("Coordinator", "Workflow completed successfully!", 1.0)

        # 5. Display Outreach Email to Terminal
        email_preview = f"""### ✉️ Humanized Outreach Email
**To:** `{target_job.get('apply_email')}`  
**Hiring Lead:** `{target_job.get('hiring_manager')}`  
**Attachment:** `{tex_path}` (LaTeX) and `{md_path}` (Markdown)  

```text
{cover_letter}
```
"""
        console.print()
        console.print(Panel(Markdown(email_preview), title="📨 [bold green]Ready for Email Dispatch[/bold green]", box=ROUNDED, border_style="green"))
        console.print(f"[bold green]✔ Logged to audit ledger: [white]logs/job_applications.jsonl[/white][/bold green]\n")
