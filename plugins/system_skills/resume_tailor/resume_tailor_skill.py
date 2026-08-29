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
                    },
                    "required": ["job_title", "company"],
                },
            )
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "tailor_resume":
            job_title = params.get("job_title", "Software Engineer")
            company = params.get("company", "Target Company")
            jd = params.get("job_description", "")

            profile = memory_service.user_profile.get_profile()

            tailored_resume_md = f"""# {profile.name}
**{job_title} | {profile.location} | {profile.email}**

### Professional Summary
Motivated and adaptive Software Engineer with hands-on expertise in Python, Flutter, RAG systems, and AI agent architectures. Eager to contribute to {company} as a {job_title}, leveraging strong problem-solving skills and passion for building high-impact software.

### Key Technical Competencies
- **Languages & Frameworks**: {", ".join(profile.skills)}
- **AI & Data**: Retrieval-Augmented Generation (RAG), Vector Embeddings, Ollama Local LLMs, Agentic Workflows
- **Tools & Methodologies**: Git, Docker, Agile Development, Async APIs, Microservices

### Featured Projects & Experience
- **Thanatos Autonomous AI Assistant**: Engineered modular multi-agent platform combining Flutter cross-platform UI, FastAPI backend, local Ollama LLM integration, and speaker diarization.
- **RAG & Knowledge Automation System**: Developed high-performance semantic retrieval pipelines using vector stores and transformer embeddings.

### Education
- {profile.education[0]['degree']} — {profile.education[0]['institution']} ({profile.education[0]['year']})
"""

            cover_letter = f"""Dear Hiring Team at {company},

I am writing to express my strong enthusiasm for the {job_title} position at {company}. With a solid foundation in computer science and extensive practical experience building scalable AI-driven applications, I am eager to bring my skills in Python, AI orchestration, and full-stack development to your team.

I look forward to discussing how my skills align with {company}'s vision.

Sincerely,
{profile.name}"""

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "job_title": job_title,
                    "company": company,
                    "resume_markdown": tailored_resume_md.strip(),
                    "cover_letter": cover_letter.strip(),
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
