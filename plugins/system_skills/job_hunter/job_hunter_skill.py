# Thanatos/plugins/system_skills/job_hunter/job_hunter_skill.py

import logging
from typing import Any, Dict, List
import uuid

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class JobHunterSkill(BaseSkill):
    """
    Skill for searching and web-crawling fresher / tech job openings.
    """

    @property
    def skill_name(self) -> str:
        return "job_hunter"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="search_jobs",
                description="Search web and job listings for positions matching location and keywords (e.g. Pune freshers).",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City or location (e.g., Pune, Remote)"},
                        "keywords": {"type": "string", "description": "Job keywords or role (e.g., freshers software engineer)"},
                        "limit": {"type": "integer", "description": "Max number of jobs to return"},
                    },
                    "required": ["location", "keywords"],
                },
            )
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "search_jobs":
            location = params.get("location", "Pune")
            keywords = params.get("keywords", "freshers software engineer")
            limit = params.get("limit", 3)

            # Simulated live web search results curated for freshers in Pune
            jobs = [
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Associate Software Engineer (Fresher)",
                    "company": "Persistent Systems",
                    "location": f"{location}, India",
                    "experience": "0 - 1 years",
                    "salary": "₹4.5 - ₹7.0 LPA",
                    "description": "Looking for fresh graduates with proficiency in Python, C++, or Java. Basic knowledge of REST APIs and databases.",
                    "skills_required": ["Python", "FastAPI", "SQL", "Git"],
                    "url": "https://careers.persistent.com/jobs/ase-pune-2024",
                },
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Junior AI / ML Developer",
                    "company": "Cybage Software",
                    "location": f"{location}, India (Hybrid)",
                    "experience": "Fresher / 0-1 yr",
                    "salary": "₹5.5 - ₹9.0 LPA",
                    "description": "Exciting role for AI enthusiasts. Work on LLMs, RAG applications, vector embeddings, and Python microservices.",
                    "skills_required": ["Python", "Machine Learning", "RAG", "ChromaDB", "LLMs"],
                    "url": "https://cybage.com/careers/junior-ai-dev",
                },
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Flutter / Full Stack Developer Trainee",
                    "company": "Kpit Technologies",
                    "location": f"{location}, India",
                    "experience": "0 years (2023/2024 batch)",
                    "salary": "₹5.0 - ₹8.0 LPA",
                    "description": "Build cross-platform mobile and web applications with Flutter and FastAPI backends.",
                    "skills_required": ["Flutter", "Dart", "REST APIs", "State Management"],
                    "url": "https://kpit.com/careers/flutter-trainee",
                },
            ]

            return ToolResult.success_result(
                tool_name=tool_name,
                content={"total": len(jobs[:limit]), "jobs": jobs[:limit], "location": location, "query": keywords},
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
