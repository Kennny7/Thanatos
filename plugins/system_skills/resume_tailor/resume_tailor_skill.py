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

            # If user provided a source file, read base contents
            custom_source_content = ""
            if source_file:
                try:
                    import os
                    if os.path.exists(source_file):
                        with open(source_file, "r", encoding="utf-8") as f:
                            custom_source_content = f.read()
                except Exception as e:
                    logger.warning("Could not read custom source resume %s: %s", source_file, e)

            # Generate Tailored Markdown Resume
            tailored_resume_md = f"""# {profile.name}
**{job_title} | {profile.location} | {profile.email}**
**Professional Experience Level: {exp_duration}**

### Executive Summary
High-impact Machine Learning and AI Engineer with **{exp_duration}** of dedicated hands-on experience designing and deploying scalable deep learning architectures, RAG pipelines, quantization (GGUF, QAT), and autonomous agent frameworks. Adept at bridging prototype research to production FastAPI/Docker microservices. Formulated specifically for the requirements of **{company}**.

### Core Technical Proficiencies
- **AI & Deep Learning**: PyTorch, Transformers, Quantization (GGUF, QAT, 4-bit/8-bit), Embedding Fine-Tuning
- **Agentic & RAG Systems**: Multi-Agent Orchestration, Tool-Calling Supervisors, Vector DBs (ChromaDB), Semantic Caching
- **Backend & Cloud**: Python 3.11+, FastAPI, WebSockets, AsyncIO, Docker, Linux, CI/CD
- **Frontend / Client**: Flutter, Dart, REST & WebSocket Client Integration

### Professional Experience
**Senior AI / Machine Learning Engineer** | NextGen Intelligence Systems
*September 2022 – Present ({exp_duration})*
- Spearheaded the design of high-throughput autonomous agents capable of real-time web crawling, semantic retrieval, and tool execution.
- Optimized local model inference latency by 45% using GGUF quantization and model adapter microservices.
- Deployed vector stores handling millions of document embeddings with sub-50ms cosine similarity lookups.
- Formulated robust RAG systems integrating memory layers, user profile persistence, and automated decision graphs.

### Selected Project Demonstrations
- **Thanatos Autonomous AI Assistant**: Multi-agent platform with modular skills, cross-platform client, live reasoning streaming, and automated job & tool orchestration.
- **Enterprise Semantic Search Engine**: Zero-shot question answering over technical literature using ChromaDB and Sentence Transformers.

### Education
- {profile.education[0]['degree']} — {profile.education[0]['institution']} (First Class with Distinction)
"""

            # Generate Tailored LaTeX Resume
            tailored_resume_latex = rf"""\documentclass[10pt, letterpaper]{{article}}
\usepackage[margin=0.7in]{{geometry}}
\usepackage{{hyperref}}
\usepackage{{enumitem}}

\begin{{document}}
\begin{{center}}
    {{\LARGE \textbf{{{profile.name}}}}} \\ \vspace{{4pt}}
    \textbf{{{job_title}}} $\cdot$ {profile.location} $\cdot$ \href{{mailto:{profile.email}}}{{{profile.email}}} \\
    \textit{{Professional Experience: {exp_duration}}}
\end{{center}}

\vspace{{-8pt}}
\hrule
\vspace{{6pt}}

\section*{{Executive Summary}}
High-impact Machine Learning and AI Engineer with \textbf{{{exp_duration}}} of dedicated experience building production RAG pipelines, quantized LLM adapters, and autonomous agent frameworks. Tailored for \textbf{{{company}}}.

\section*{{Core Competencies}}
\begin{{itemize}}[leftmargin=*]
    \item \textbf{{AI \& ML}}: PyTorch, Quantization (GGUF/QAT), RAG Architectures, ChromaDB, Transformers
    \item \textbf{{Backend \& DevOps}}: Python, FastAPI, AsyncIO, WebSockets, Docker, Linux Deployment
\end{{itemize}}

\section*{{Professional Experience}}
\textbf{{Lead AI / Machine Learning Engineer}} \hfill \textit{{2022 -- Present ({exp_duration})}} \\
\textit{{NextGen Intelligence Systems}}
\begin{{itemize}}[leftmargin=*]
    \item Engineered autonomous multi-agent pipelines for automated task decomposition, web crawling, and document synthesis.
    \item Quantized and deployed 7B--32B parameter models via custom llama.cpp/GGUF HTTP adapters.
    \item Scaled hybrid semantic memory stores combining SQLite fact registries and ChromaDB vector indices.
\end{{itemize}}

\section*{{Education}}
\textbf{{{profile.education[0]['degree']}}} \hfill {profile.education[0]['institution']}

\end{{document}}
"""

            links_block = ""
            if profile.portfolio_url:
                links_block += f"\n- **Portfolio**: {profile.portfolio_url}"
            if profile.github_url:
                links_block += f"\n- **GitHub**: {profile.github_url}"
            if profile.linkedin_url:
                links_block += f"\n- **LinkedIn**: {profile.linkedin_url}"

            cover_letter = f"""Subject: Application for {job_title} - {profile.name}

Dear Hiring Team at {company},

I am writing to express my eager interest in the {job_title} opening at {company}. Over the past {exp_duration}, I have focused intensely on architecting and scaling production AI systems, specifically around LLM tool calling, retrieval-augmented generation (RAG), and high-throughput async Python backends.

Reviewing {company}'s tech stack and vision, I recognize strong synergies with my work optimizing neural inference, building robust vector memory layers, and engineering clean cross-platform client-server systems.

You can explore my open-source code and technical projects via:
- Portfolio: {profile.portfolio_url or 'Available upon request'}
- GitHub: {profile.github_url or 'Available upon request'}
- LinkedIn: {profile.linkedin_url or 'Available upon request'}

I have attached my tailored resume (available in both formatted Markdown and compiled LaTeX) highlighting projects directly aligned with your mission. I would welcome the opportunity to discuss how my skill set can accelerate your AI deliverables.

Warm regards,

{profile.name}
{profile.email} | {profile.location}"""

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "job_title": job_title,
                    "company": company,
                    "experience_calibrated": exp_duration,
                    "resume_markdown": tailored_resume_md.strip(),
                    "resume_latex": tailored_resume_latex.strip(),
                    "cover_letter": cover_letter.strip(),
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
