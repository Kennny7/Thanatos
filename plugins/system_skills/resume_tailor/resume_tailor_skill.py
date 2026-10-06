# Thanatos/plugins/system_skills/resume_tailor/resume_tailor_skill.py

import logging
from typing import Any, Dict, List
from plugins.base.skill_interface import BaseSkill
from services.memory.memory_manager import memory_service
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class ResumeTailorSkill(BaseSkill):
    """
    Skill for tailoring user resume and generating custom cover letters for job descriptions using RAG.
    """

    @property
    def skill_name(self) -> str:
        return "resume_tailor"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="tailor_resume",
                description="Customizes the user resume and cover letter to match a specific job description.",
                parameters={
                    "type": "object",
                    "properties": {
                        "job_title": {"type": "string", "description": "Target job title"},
                        "company": {"type": "string", "description": "Hiring company name"},
                        "job_description": {"type": "string", "description": "Job requirements and description"},
                        "experience_level": {"type": "string", "description": "Experience duration to calibrate (e.g. 3 years 8 months)"},
                        "source_file_path": {"type": "string", "description": "Optional path to existing resume (.tex, .md, .txt) or profile JSON"},
                    },
                    "required": ["job_title", "company"],
                },
            )
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "tailor_resume":
            job_title = params.get("job_title", "AI / ML Engineer")
            company = params.get("company", "Target Company")
            jd = params.get("job_description", "")
            exp_duration = params.get("experience_level", "3 years 8 months")
            source_file = params.get("source_file_path")

            profile = memory_service.user_profile.get_profile()

            # 1. Resolve source LaTeX/Markdown document template
            import os
            import re
            template_content = ""
            selected_template_name = "default"

            # Check explicit source file first
            if source_file and os.path.exists(source_file):
                try:
                    with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
                        template_content = f.read()
                        selected_template_name = os.path.basename(source_file)
                except Exception as e:
                    logger.warning("Could not read explicit source resume %s: %s", source_file, e)

            # If no explicit template, check loaded custom documents in profile
            if not template_content and profile.custom_documents:
                # Prefer matching role keywords (Engineer vs Developer)
                lower_title = job_title.lower()
                if "develop" in lower_title and "AI_Developer.tex" in profile.custom_documents:
                    template_content = profile.custom_documents["AI_Developer.tex"]
                    selected_template_name = "AI_Developer.tex"
                elif "AI_Engineer.tex" in profile.custom_documents:
                    template_content = profile.custom_documents["AI_Engineer.tex"]
                    selected_template_name = "AI_Engineer.tex"
                elif "AI_Developer.tex" in profile.custom_documents:
                    template_content = profile.custom_documents["AI_Developer.tex"]
                    selected_template_name = "AI_Developer.tex"
                else:
                    # Pick first available .tex or .md document
                    for doc_name, content in profile.custom_documents.items():
                        if doc_name.endswith(".tex") or doc_name.endswith(".md"):
                            template_content = content
                            selected_template_name = doc_name
                            break

            # 2. Calibrate LaTeX Resume based on template
            if template_content and ("\\documentclass" in template_content or "\\begin{document}" in template_content):
                # We have an authentic LaTeX resume! Calibrate it for the company & role
                tailored_resume_latex = template_content
                # Update title line in header if present
                tailored_resume_latex = re.sub(
                    r"\{\\normalsize\\textbf\{[^}]+\}\}",
                    f"{{\\normalsize\\textbf{{{job_title} | Generative AI, LLM & RAG Systems}}}}",
                    tailored_resume_latex,
                    count=1
                )
                # Calibrate experience in profile section
                tailored_resume_latex = re.sub(
                    r"\\textbf\{3\+? years of experience\}",
                    f"\\textbf{{{exp_duration} of experience}}",
                    tailored_resume_latex
                )
                # Ensure candidate name and contact align
                if profile.name:
                    tailored_resume_latex = re.sub(r"\{\\LARGE\\textbf\{[^}]+\}\}", f"{{\\LARGE\\textbf{{{profile.name}}}}}", tailored_resume_latex, count=1)
                
                # Derive comprehensive markdown version from authentic LaTeX
                from services.document.pdf_generator import clean_latex_to_text
                tailored_resume_md = clean_latex_to_text(tailored_resume_latex)
            else:
                # Fallback to authentic rich profile details
                tailored_resume_md = f"""# {profile.name or 'Khushal Pareta'}
{job_title} | {profile.location or 'Mumbai, India'} | {profile.email or 'Khushalpareta9@gmail.com'}
Phone: +91 96604 64021 | LinkedIn: {profile.linkedin_url} | GitHub: {profile.github_url} | Portfolio: {profile.portfolio_url}

### Executive Profile
AI/ML Engineer with {exp_duration} of dedicated experience designing, developing, and deploying scalable Generative AI applications, RAG pipelines, and agentic workflows. Proven track record building enterprise AI assistants and microservices using LangChain, OpenAI, Azure OpenAI, Claude, Hugging Face, PyTorch, and FastAPI.

### Core Competencies
- Generative AI & LLMs: OpenAI, Claude, Gemini, LangChain, Hugging Face, RAG, Prompt Engineering, Fine-tuning, Vector DBs (Chroma/FAISS)
- Engineering & Backend: Python, FastAPI, PySpark, PostgreSQL, Docker, Microservices, CI/CD, Git, Linux
- Data & MLOps: MLflow, Airflow, ELK Stack, Data Validation, Automated Ingestion Pipelines

### Professional Experience
Project Engineer (AI/ML & Data Pipelines) | C-DAC, Mumbai
March 2025 – Present
- Architected and deployed an LLM-powered conversational assistant for the Maritime Knowledge Cluster using LangChain and RAG over regulatory circulars.
- Engineered PySpark ETL pipelines for the National Family Health Survey (NFHS), optimizing query latency by 40% with PostgreSQL connection pooling.
- Developed real-time error classification microservices and deployed ELK Stack for centralized telemetry and monitoring.

Data Operations Engineer | Laxmi Traders, Rajasthan
July 2022 – August 2024
- Engineered real-time data synchronization layers with Python and PostgreSQL, unifying procurement across multiple commodity hubs.
- Built automated commodity forecasting microservices using XGBoost, Scikit-learn, and FastAPI.
- Orchestrated end-to-end Airflow ETL pipelines and MLflow experiment tracking.

### Education & Honors
- Post Graduate Diploma in Big Data Analytics | C-DAC, Mumbai (Rank 1 for Academic Excellence)
- Bachelor of Technology in Computer Science | Poornima College of Engineering, Jaipur
"""
                tailored_resume_latex = rf"""\documentclass[10pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[a4paper,left=1.8cm,right=1.8cm,top=1.6cm,bottom=1.6cm]{{geometry}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\begin{{document}}
\begin{{center}}
  {{\LARGE\textbf{{{profile.name or 'Khushal Pareta'}}}}}\\[4pt]
  {{\normalsize\textbf{{{job_title}}}}}\\[4pt]
  \href{{mailto:{profile.email}}}{{{profile.email}}} $\cdot$ {profile.location} $\cdot$ \href{{{profile.portfolio_url}}}{{Portfolio}}
\end{{center}}
\section*{{Profile}}
AI/ML Engineer with \textbf{{{exp_duration} of experience}} developing Generative AI, RAG architectures, and agentic systems tailored for \textbf{{{company}}}.
\end{{document}}
"""

            # 3. Create professional, clean cover letter with ZERO asterisk artifacts
            portfolio_ref = profile.portfolio_url or "https://kennny7.github.io/"
            github_ref = profile.github_url or "https://github.com/Kennny7"
            linkedin_ref = profile.linkedin_url or "https://www.linkedin.com/in/khushal-pareta-704355338"

            cover_letter = f"""Subject: Application for {job_title} - {profile.name}

Dear Hiring Team at {company},

I am writing to express my strong interest in the {job_title} role at {company}. With over {exp_duration} of hands-on experience engineering production Generative AI applications, Retrieval-Augmented Generation (RAG) architectures, and high-performance Python microservices, I am excited about the opportunity to contribute to your engineering initiatives.

At C-DAC Mumbai, I architected and deployed an enterprise LLM conversational assistant for the Maritime Knowledge Cluster utilizing LangChain, Hugging Face, and state-of-the-art foundation models. Grounding responses in official regulatory documentation through vector search and structured prompt engineering delivered measurable accuracy gains for over 100 maritime stakeholders. Prior to this, I designed automated data synchronization pipelines and predictive machine learning microservices served via FastAPI and Docker, driving significant latency reductions and reporting accuracy.

My technical background directly aligns with your requirements:
- Large Language Models & RAG: LangChain, LlamaIndex, Vector Databases, Semantic Search, and Prompt Optimization.
- Backend & Microservices: Python, FastAPI, Docker, PostgreSQL, REST APIs, and Async Architecture.
- Robust Data Pipelines: PySpark, Apache Airflow, MLflow tracking, and ELK Stack observability.

You can inspect my technical portfolio and open-source contributions here:
- Portfolio: {portfolio_ref}
- GitHub: {github_ref}
- LinkedIn: {linkedin_ref}

I have attached my tailored resume for your review. I would welcome the opportunity to discuss how my experience in building intelligent AI systems can bring immediate value to {company}.

Sincerely,

{profile.name}
{profile.email} | {profile.location}
Phone: +91 96604 64021"""

            # Clean any stray markdown artifacts or symbols
            cover_letter = cover_letter.replace("**", "").replace("__", "")

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "job_title": job_title,
                    "company": company,
                    "experience_calibrated": exp_duration,
                    "template_source": selected_template_name,
                    "resume_markdown": tailored_resume_md.strip(),
                    "resume_latex": tailored_resume_latex.strip(),
                    "cover_letter": cover_letter.strip(),
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
