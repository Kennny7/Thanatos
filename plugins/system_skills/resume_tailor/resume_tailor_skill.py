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
                # Prefer standard resume_template.tex, or any available single document
                if "resume_template.tex" in profile.custom_documents:
                    template_content = profile.custom_documents["resume_template.tex"]
                    selected_template_name = "resume_template.tex"
                else:
                    for doc_name, content in profile.custom_documents.items():
                        if doc_name.endswith(".tex") or doc_name.endswith(".md"):
                            template_content = content
                            selected_template_name = doc_name
                            break

            # 2. Calibrate LaTeX Resume based on template
            skills_required = params.get("skills_required", [])
            if not skills_required and jd:
                common_tech = ["Python", "FastAPI", "Docker", "PyTorch", "TensorFlow", "LangChain", "LlamaIndex", 
                               "ChromaDB", "Milvus", "RAG", "PostgreSQL", "Kafka", "Airflow", "PySpark", 
                               "Kubernetes", "AWS", "Azure", "GCP", "MLflow", "Ollama", "vLLM", "NLP", "LLM"]
                for tech in common_tech:
                    if re.search(r"\b" + re.escape(tech) + r"\b", jd, re.IGNORECASE):
                        skills_required.append(tech)

            if template_content and ("\\documentclass" in template_content or "\\begin{document}" in template_content):
                # We have an authentic LaTeX resume! Calibrate it for the company & role
                tailored_resume_latex = template_content

                # A. Calibrate Candidate Title Header
                safe_title_header = f"{{\\normalsize\\textbf{{{job_title} | Generative AI, LLM & RAG Systems}}}}"
                tailored_resume_latex = re.sub(
                    r"\{\\normalsize\\textbf\{[^}]+\}\}",
                    lambda m: safe_title_header,
                    tailored_resume_latex,
                    count=1
                )

                # B. Calibrate Candidate Name
                if profile.name:
                    safe_name_header = f"{{\\LARGE\\textbf{{{profile.name}}}}}"
                    tailored_resume_latex = re.sub(
                        r"\{\\LARGE\\textbf\{[^}]+\}\}",
                        lambda m: safe_name_header,
                        tailored_resume_latex,
                        count=1
                    )

                # C. Dynamically Tailor the Profile / Summary Paragraph
                # Craft a focused executive summary specifically targeted at this job & company
                target_focus = ", ".join(skills_required[:4]) if skills_required else "Generative AI, RAG architectures, and scalable microservices"
                tailored_profile_paragraph = (
                    f"AI/ML Engineer with \\textbf{{{exp_duration} of experience}} designing, deploying, and optimizing production "
                    f"\\textbf{{Generative AI systems, RAG pipelines, and high-performance ML architectures}} targeted for \\textbf{{{company}}}. "
                    f"Demonstrated track record engineering scalable backend services and automated workflows with \\textbf{{{target_focus}}}, "
                    f"PostgreSQL, and Docker. Proven capability in owning ML systems from data ingestion and model evaluation to production deployment, "
                    f"delivering measurable improvements in latency, accuracy, and operational efficiency."
                )

                # Replace the template's profile paragraph
                profile_match = re.search(r"(\\section\*\{Profile\}\s*\\vspace\{[^}]+\}\s*\\sectionline\s*(?:\\\\)?\s*)(.*?)(?=\s*\\section\*\{)", tailored_resume_latex, flags=re.DOTALL)
                if profile_match:
                    prefix = profile_match.group(1)
                    tailored_resume_latex = (
                        tailored_resume_latex[:profile_match.start()] +
                        f"{prefix}\n{tailored_profile_paragraph}\n\n" +
                        tailored_resume_latex[profile_match.end():]
                    )

                # D. Dynamically Prioritize Core Competencies
                # Parse existing competencies and re-order / highlight categories relevant to this job
                comp_match = re.search(r"(\\section\*\{Core Competencies\}\s*\\vspace\{[^}]+\}\s*\\sectionline\s*\\begin\{description\})(.*?)(\\end\{description\})", tailored_resume_latex, flags=re.DOTALL)
                if comp_match:
                    comp_header = comp_match.group(1)
                    comp_body = comp_match.group(2)
                    comp_footer = comp_match.group(3)

                    # Split into individual \item[Category:] blocks
                    items = re.findall(r"(\\item\[[^\]]+\]\s*[\s\S]*?)(?=(?:\\item\[|\\end\{description\}))", comp_body + "\\end{description}")
                    if items:
                        def score_item(item_text: str) -> int:
                            score = 0
                            for sk in skills_required:
                                if re.search(r"\b" + re.escape(sk) + r"\b", item_text, re.IGNORECASE):
                                    score += 2
                            if jd:
                                words = [w for w in re.split(r"\W+", jd.lower()) if len(w) > 3]
                                for w in set(words[:25]):
                                    if w in item_text.lower():
                                        score += 1
                            return score

                        # Sort items by relevance to the target job
                        sorted_items = sorted(items, key=score_item, reverse=True)
                        tailored_resume_latex = (
                            tailored_resume_latex[:comp_match.start()] +
                            f"{comp_header}\n" + "\n\n".join(it.strip() for it in sorted_items) + f"\n{comp_footer}" +
                            tailored_resume_latex[comp_match.end():]
                        )

                # E. Dynamically Select and Reorder Key Projects
                # The master resume contains 7 key projects. Select the top 3-4 most relevant to this opening
                proj_match = re.search(r"(\\section\*\{Key Projects\}\s*\\vspace\{[^}]+\}\s*\\sectionline\s*\\begin\{description\}[^\n]*\n)(.*?)(\\end\{description\})", tailored_resume_latex, flags=re.DOTALL)
                if proj_match:
                    proj_header = proj_match.group(1)
                    proj_body = proj_match.group(2)
                    proj_footer = proj_match.group(3)

                    # Extract each project item block
                    proj_items = re.findall(r"(\\item\[\\textbf\{[^\]]+\}\][\s\S]*?)(?=(?:\\item\[\\textbf\{|\\end\{description\}))", proj_body + "\\end{description}")
                    if proj_items:
                        def score_project(proj_text: str) -> int:
                            score = 0
                            for sk in skills_required:
                                if re.search(r"\b" + re.escape(sk) + r"\b", proj_text, re.IGNORECASE):
                                    score += 3
                            if jd:
                                words = [w for w in re.split(r"\W+", jd.lower()) if len(w) > 3]
                                for w in set(words[:30]):
                                    if w in proj_text.lower():
                                        score += 1
                            # Always ensure MKC and LRIT have high baseline relevance for AI/ML roles
                            if "Maritime Knowledge Cluster" in proj_text:
                                score += 2
                            return score

                        sorted_projs = sorted(proj_items, key=score_project, reverse=True)
                        # Keep top 3 most relevant projects to avoid clutter and ensure tight fit
                        selected_projs = sorted_projs[:3]
                        tailored_resume_latex = (
                            tailored_resume_latex[:proj_match.start()] +
                            f"{proj_header}\n" + "\n\n".join(p.strip() for p in selected_projs) + f"\n\n{proj_footer}" +
                            tailored_resume_latex[proj_match.end():]
                        )

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
\usepackage{{titlesec}}
\setlist[itemize]{{noitemsep, topsep=2pt, leftmargin=*, parsep=0pt, partopsep=0pt}}
\setlength{{\parskip}}{{3pt}}
\setlength{{\parindent}}{{0pt}}
\titleformat{{\section}}{{\large\bfseries}}{{}}{{0em}}{{}}
\titlespacing*{{\section}}{{0pt}}{{1em}}{{0.3em}}
\newcommand{{\sectionline}}{{\vspace{{2pt}}\noindent\rule{{\textwidth}}{{0.5pt}}\vspace{{4pt}}}}

\begin{{document}}
\begin{{center}}
  {{\LARGE\textbf{{{profile.name or 'Khushal Pareta'}}}}}\\[4pt]
  {{\normalsize\textbf{{{job_title} | Generative AI, LLM & RAG Systems}}}}\\[4pt]
  \href{{mailto:{profile.email}}}{{{profile.email}}} $\cdot$ {profile.location} $\cdot$ \href{{{profile.portfolio_url}}}{{Portfolio}} $\cdot$ \href{{{profile.linkedin_url}}}{{LinkedIn}} $\cdot$ \href{{{profile.github_url}}}{{GitHub}}
\end{{center}}

\section*{{Profile}}
\vspace{{-0.4em}}
\sectionline
AI/ML Engineer with \textbf{{{exp_duration} of experience}} developing Generative AI, RAG architectures, and agentic systems tailored for \textbf{{{company}}}. Proven track record designing enterprise AI assistants and microservices using LangChain, Hugging Face, PyTorch, and FastAPI.

\section*{{Core Competencies}}
\vspace{{-0.4em}}
\sectionline
\begin{{itemize}}
  \item \textbf{{Generative AI \& LLMs:}} OpenAI, Claude, Gemini, LangChain, Hugging Face, RAG, Prompt Engineering, Vector DBs (Chroma/FAISS)
  \item \textbf{{Engineering \& Backend:}} Python, FastAPI, PySpark, PostgreSQL, Docker, Microservices, CI/CD, Git, Linux
  \item \textbf{{Data \& MLOps:}} MLflow, Airflow, ELK Stack, Data Validation, Automated Ingestion Pipelines
\end{{itemize}}

\section*{{Professional Experience}}
\vspace{{-0.4em}}
\sectionline
\textbf{{Project Engineer (AI/ML \& Data Pipelines)}} \hfill C-DAC, Mumbai \\
\textit{{March 2025 -- Present}}
\begin{{itemize}}
  \item Architected and deployed an LLM-powered conversational assistant for the Maritime Knowledge Cluster using LangChain and RAG over regulatory circulars.
  \item Engineered PySpark ETL pipelines for the National Family Health Survey (NFHS), optimizing query latency by 40\% with PostgreSQL connection pooling.
  \item Developed real-time error classification microservices and deployed ELK Stack for centralized telemetry and monitoring.
\end{{itemize}}

\vspace{{4pt}}
\textbf{{Data Operations Engineer}} \hfill Laxmi Traders, Rajasthan \\
\textit{{July 2022 -- August 2024}}
\begin{{itemize}}
  \item Engineered real-time data synchronization layers with Python and PostgreSQL, unifying procurement across multiple commodity hubs.
  \item Built automated commodity forecasting microservices using XGBoost, Scikit-learn, and FastAPI.
  \item Orchestrated end-to-end Airflow ETL pipelines and MLflow experiment tracking.
\end{{itemize}}

\section*{{Education}}
\vspace{{-0.4em}}
\sectionline
\textbf{{Post Graduate Diploma in Big Data Analytics}} \hfill C-DAC, Mumbai (Rank 1 for Academic Excellence) \\
\textbf{{Bachelor of Technology in Computer Science}} \hfill Poornima College of Engineering, Jaipur

\end{{document}}
"""

            # 3. Create professional, clean cover letter with ZERO asterisk artifacts
            portfolio_ref = profile.portfolio_url or "https://kennny7.github.io/"
            github_ref = profile.github_url or "https://github.com/Kennny7"
            linkedin_ref = profile.linkedin_url or "https://www.linkedin.com/in/khushal-pareta-704355338"

            # Align cover letter core strengths to target job requirements
            primary_strengths = []
            if any(s.lower() in ["rag", "langchain", "llamaindex", "vector databases", "embeddings"] for s in skills_required):
                primary_strengths.append("Large Language Models & RAG: LangChain, LlamaIndex, Vector Databases, Semantic Search, and Prompt Optimization.")
            if any(s.lower() in ["fastapi", "python", "docker", "microservices", "postgresql", "rest apis"] for s in skills_required):
                primary_strengths.append("Backend & Microservices: Python, FastAPI, Docker, PostgreSQL, REST APIs, and Async Architecture.")
            if any(s.lower() in ["pyspark", "airflow", "kafka", "etl", "data pipeline"] for s in skills_required):
                primary_strengths.append("Robust Data & Streaming: PySpark, Apache Airflow, Kafka, and Data Validation Pipelines.")
            if any(s.lower() in ["pytorch", "tensorflow", "xgboost", "scikit-learn", "deep learning"] for s in skills_required):
                primary_strengths.append("Machine Learning & Deep Learning: PyTorch, Sequence Models, XGBoost, and Model Optimization.")
            if any(s.lower() in ["ollama", "vllm", "gguf", "local llm", "qwen", "deepseek"] for s in skills_required):
                primary_strengths.append("Local LLMs & Inference: Ollama, vLLM, GGUF Quantization, and High-Throughput Serving.")

            # Default to top 3 if fewer matches
            if len(primary_strengths) < 3:
                defaults = [
                    "Large Language Models & RAG: LangChain, LlamaIndex, Vector Databases, Semantic Search, and Prompt Optimization.",
                    "Backend & Microservices: Python, FastAPI, Docker, PostgreSQL, REST APIs, and Async Architecture.",
                    "Robust Data Pipelines: PySpark, Apache Airflow, MLflow tracking, and ELK Stack observability.",
                ]
                for d in defaults:
                    if d not in primary_strengths:
                        primary_strengths.append(d)
                    if len(primary_strengths) >= 3:
                        break

            bullet_alignment = "\n".join(f"- {b}" for b in primary_strengths[:3])

            cover_letter = f"""Subject: Application for {job_title} - {profile.name}

Dear Hiring Team at {company},

I am writing to express my strong interest in the {job_title} role at {company}. With over {exp_duration} of hands-on experience engineering production Generative AI applications, Retrieval-Augmented Generation (RAG) architectures, and high-performance Python microservices, I am excited about the opportunity to contribute to your engineering initiatives.

At C-DAC Mumbai, I architected and deployed an enterprise LLM conversational assistant for the Maritime Knowledge Cluster utilizing LangChain, Hugging Face, and state-of-the-art foundation models. Grounding responses in official regulatory documentation through vector search and structured prompt engineering delivered measurable accuracy gains for over 100 maritime stakeholders. Prior to this, I designed automated data synchronization pipelines and predictive machine learning microservices served via FastAPI and Docker, driving significant latency reductions and reporting accuracy.

My technical background directly aligns with your requirements:
{bullet_alignment}

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
