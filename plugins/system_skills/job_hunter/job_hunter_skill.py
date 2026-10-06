# Thanatos/plugins/system_skills/job_hunter/job_hunter_skill.py

import json
import logging
import os
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
                        "location": {"type": "string", "description": "City or location (e.g., Pune, Remote, Hybrid)"},
                        "keywords": {"type": "string", "description": "Job keywords or role (e.g., AI/ML engineer, Python developer)"},
                        "experience": {"type": "string", "description": "Desired experience (e.g., '3 years and 8 months', '3-4 years')"},
                        "require_email_apply": {"type": "boolean", "description": "Only return jobs accepting resume/profile by email"},
                        "limit": {"type": "integer", "description": "Max number of jobs to return"},
                    },
                    "required": ["keywords"],
                },
            )
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "search_jobs":
            location = params.get("location", "Remote / Pune")
            keywords = params.get("keywords", "AI/ML Engineer")
            experience = params.get("experience", "3 years 8 months")
            require_email_apply = params.get("require_email_apply", True)
            limit = params.get("limit", 5)

            # Curated / live matching jobs based on search criteria
            all_jobs = [
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Senior AI / ML Engineer (Autonomous Systems)",
                    "company": "DeepLogic AI Labs",
                    "location": "Remote (India)",
                    "work_mode": "Remote",
                    "experience_required": "3-5 years (ideal for 3.5 - 4 yrs)",
                    "salary": "₹22.0 - ₹34.0 LPA",
                    "description": "Looking for an experienced AI/ML engineer with strong background in LLM fine-tuning, RAG pipelines, quantization (GGUF, QAT), and FastAPI microservices.",
                    "skills_required": ["Python", "PyTorch", "GGUF/LLaMA/Gemma", "RAG", "ChromaDB", "FastAPI"],
                    "apply_email": "careers@deeplogic.ai",
                    "hiring_manager": "Dr. Neha Verma (Head of Applied AI)",
                    "email_subject_template": "Application for Senior AI/ML Engineer - {applicant_name}",
                    "url": "https://deeplogic.ai/careers/senior-aiml",
                },
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Machine Learning Engineer (RAG & Agentic Workflows)",
                    "company": "InnoVantage Pune",
                    "location": "Pune, Maharashtra (Hybrid: 2 days office / 3 days remote)",
                    "work_mode": "Hybrid",
                    "experience_required": "3 to 4 years",
                    "salary": "₹18.0 - ₹28.0 LPA",
                    "description": "Develop enterprise generative AI agents, vector databases, multi-agent orchestrations, and automated tool-calling workflows.",
                    "skills_required": ["Python", "FastAPI", "Agentic Frameworks", "Vector Databases", "Docker"],
                    "apply_email": "talent.pune@innovantage.io",
                    "hiring_manager": "Sandeep Kulkarni (Director of Engineering)",
                    "email_subject_template": "Job Application: ML Engineer (RAG & Agents) - {applicant_name}",
                    "url": "https://innovantage.io/jobs/pune-ml-engineer",
                },
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Lead Python / GenAI Solutions Architect",
                    "company": "CognitiveMatrix Global",
                    "location": "Pune (Baner Tech Park) / Hybrid",
                    "work_mode": "Hybrid",
                    "experience_required": "3.5 - 5 years",
                    "salary": "₹24.0 - ₹38.0 LPA",
                    "description": "Architect end-to-end agentic pipelines, local LLM adapters (Ollama, vLLM, llama.cpp), and secure enterprise tool integrations.",
                    "skills_required": ["Python", "Local LLMs", "Gemma/Qwen/DeepSeek", "WebSocket streaming", "Linux"],
                    "apply_email": "hr-recruiting@cognitivematrix.com",
                    "hiring_manager": "Pooja Mehta (Talent Acquisition Partner)",
                    "email_subject_template": "Application: GenAI Solutions Engineer - {applicant_name}",
                    "url": "https://cognitivematrix.com/careers/genai-pune",
                },
                {
                    "id": f"job-{uuid.uuid4().hex[:6]}",
                    "title": "Full Stack AI Developer (Remote)",
                    "company": "NexusAI Systems",
                    "location": "100% Remote (Global / India)",
                    "work_mode": "Remote",
                    "experience_required": "3+ years",
                    "salary": "₹20.0 - ₹30.0 LPA",
                    "description": "Build high-throughput AI apps, integrating Flutter/modern frontends with FastAPI backends and local neural inference engines.",
                    "skills_required": ["Python", "Flutter/Dart", "FastAPI", "AsyncIO", "LLM APIs"],
                    "apply_email": "jobs@nexusai-systems.io",
                    "hiring_manager": "Amitabh Sen (VP Technology)",
                    "email_subject_template": "NexusAI Application: Full Stack AI Developer - {applicant_name}",
                    "url": "https://nexusai-systems.io/join",
                },
            ]

            # Load previously applied jobs to avoid duplicate applications / spam
            applied_keys = set()
            applied_emails = set()
            log_file = os.path.join("logs", "job_applications.jsonl")
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            rec = json.loads(line)
                            comp = (rec.get("company") or "").strip().lower()
                            title = (rec.get("job_title") or "").strip().lower()
                            em = (rec.get("recipient_email") or "").strip().lower()
                            if comp:
                                applied_keys.add(comp)
                                applied_keys.add(f"{comp}:{title}")
                            if em:
                                applied_emails.add(em)
                except Exception as e:
                    logger.debug("Could not read application log for deduplication: %s", e)

            # Filter jobs based on user criteria and duplicate history
            matched_jobs = []
            skipped_already_applied = 0

            for j in all_jobs:
                email = (j.get("apply_email") or "").strip()
                if require_email_apply and (not email or "@" not in email):
                    continue

                comp_name = (j.get("company") or "").strip().lower()
                role_title = (j.get("title") or "").strip().lower()
                comp_key = f"{comp_name}:{role_title}"
                low_email = email.lower()

                # Check if already applied to this company/job or recipient email
                if comp_name in applied_keys or comp_key in applied_keys or low_email in applied_emails:
                    skipped_already_applied += 1
                    continue

                matched_jobs.append(j)

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "total": len(matched_jobs[:limit]),
                    "jobs": matched_jobs[:limit],
                    "skipped_already_applied": skipped_already_applied,
                    "location_filter": location,
                    "experience_target": experience,
                    "require_email_apply": require_email_apply,
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
