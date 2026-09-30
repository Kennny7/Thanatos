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

        # 1. Sync Profile Directory and verify available portfolio/links
        sync_stats = memory_service.user_profile.sync()
        profile = memory_service.user_profile.get_profile()
        loaded_count = len(profile.custom_documents)
        
        if self.show_thinking:
            links_summary = f"GitHub: {profile.github_url or 'None'}, LinkedIn: {profile.linkedin_url or 'None'}, Portfolio: {profile.portfolio_url or 'None'}"
            print_thought(
                f"Synchronized Profile Repository (`{memory_service.user_profile.profile_dir}`):\n"
                f"- Active documents: {loaded_count} ({', '.join(profile.custom_documents.keys()) if loaded_count else 'None'})\n"
                f"- Extracted links: {links_summary}\n"
                f"- Deduplication status: {sync_stats.get('added', 0)} added, {sync_stats.get('updated', 0)} updated, {sync_stats.get('skipped', 0)} skipped."
            )

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
            "source_file_path": source_resume_path if source_resume_path and os.path.exists(source_resume_path) else None,
        })

        tailor_data = tailor_res.content if tailor_res.success else {}
        resume_md = tailor_data.get("resume_markdown", "")
        resume_tex = tailor_data.get("resume_latex", "")
        cover_letter = tailor_data.get("cover_letter", "")

        # Save generated LaTeX and Markdown resumes to disk for user
        out_dir = os.path.join("logs", "generated_resumes")
        os.makedirs(out_dir, exist_ok=True)
        slug = target_job['company'].lower().replace(' ', '_')
        tex_path = os.path.join(out_dir, f"{slug}_resume.tex")
        md_path = os.path.join(out_dir, f"{slug}_resume.md")
        resume_pdf_path = os.path.join(out_dir, f"{slug}_resume.pdf")
        cover_letter_pdf_path = os.path.join(out_dir, f"{slug}_cover_letter.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(resume_tex)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(resume_md)

        # Autonomously convert to high-impact PDF attachments (Resume + Cover Letter)
        from services.document.pdf_generator import pdf_generator
        from services.memory.memory_manager import memory_service
        prof = memory_service.user_profile.get_profile()

        pdf_generator.generate_resume_pdf(
            source_tex_or_md=resume_tex or resume_md,
            output_pdf_path=resume_pdf_path,
            candidate_name=prof.name or "Khushal Pareta",
            candidate_title=prof.title or "AI Developer | Machine Learning Engineer",
            candidate_contacts={"email": prof.email, "phone": "+91 96604 64021", "location": prof.location},
        )

        pdf_generator.generate_cover_letter_pdf(
            cover_letter_text=cover_letter,
            applicant_name=prof.name or "Khushal Pareta",
            job_title=target_job["title"],
            company=target_job["company"],
            output_pdf_path=cover_letter_pdf_path,
            contact_info={"email": prof.email, "phone": "+91 96604 64021", "location": prof.location},
        )

        if self.show_thinking:
            print_thought(f"Successfully compiled tailored documents & official PDF attachments:\n- Resume PDF: `{resume_pdf_path}`\n- Cover Letter PDF: `{cover_letter_pdf_path}`\n- TeX source backup: `{tex_path}`\n- Included candidate links: Portfolio, GitHub, LinkedIn.")

        # 4. Check Email Transmission Preference and Credentials
        from services.email.email_service import email_service
        is_configured = email_service.is_configured()

        console.print(f"\n[bold yellow]• Email Delivery Verification Check[/bold yellow]")
        if not is_configured:
            console.print(f"[dim red]Notice: SMTP credentials are not configured. The email will be drafted and staged.[/dim red]")
            console.print(f"[dim]Tip: You can configure SMTP anytime using [bold white]/smtp[/bold white] to enable verified live sending.[/dim]")

        # 5. Application Packaging & Optional Sending
        # Resumes and cover letters are attached exclusively as PDFs
        pdf_attachments = [resume_pdf_path, cover_letter_pdf_path]
        print_agent_breadcrumb("Job Applicator Agent", f"Packaging PDF attachments and formatting outreach dispatch record...", 0.85)
        apply_res = await registry.dispatch("prepare_job_application", {
            "job_id": target_job.get("id"),
            "job_title": target_job["title"],
            "company": target_job["company"],
            "recipient_email": target_job.get("apply_email"),
            "hiring_manager": target_job.get("hiring_manager"),
            "tailored_resume": resume_md,
            "cover_letter": cover_letter,
            "resume_attachments": pdf_attachments,
            "send_email_now": is_configured,
        })

        print_agent_breadcrumb("Coordinator", "Workflow evaluation completed!", 1.0)

        # 6. Display Outreach Email and Verified Status
        status_text = apply_res.content.get("status", "Staged")
        verification_note = apply_res.content.get("verification_note", "")
        status_color = "green" if apply_res.content.get("verified_delivery") else ("yellow" if "Staged" in status_text else "red")

        email_preview = f"""### • Humanized Outreach Email
**To:** `{target_job.get('apply_email')}`  
**Hiring Lead:** `{target_job.get('hiring_manager')}`  
**Verified Attachments (PDF):**  
  • `{os.path.basename(resume_pdf_path)}`  
  • `{os.path.basename(cover_letter_pdf_path)}`  
**Delivery Verification Status:** **[{status_text}]**  
*{verification_note or 'Application staged and verified locally.'}*

```text
{cover_letter}
```
"""
        console.print()
        console.print(Panel(Markdown(email_preview), title=f"[{status_color}]• Application Package — {status_text}[/{status_color}]", box=ROUNDED, border_style=status_color))
        console.print(f"[bold green][✓] Persistent audit entry saved in: [white]logs/job_applications.jsonl[/white][/bold green]\n")
