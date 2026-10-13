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
                        "portals": {"type": "array", "items": {"type": "string"}, "description": "Specific job portals e.g. ['linkedin', 'naukri']"},
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
            portals = params.get("portals", ["linkedin", "naukri"])
            require_email_apply = params.get("require_email_apply", True)
            limit = params.get("limit", 5)

            # 1. Fetch portal listings from LinkedIn and Naukri search service
            from services.web.portal_job_search import portal_job_search
            all_jobs = await portal_job_search.search_portals(
                keywords=keywords,
                location=location,
                experience=experience,
                portals=portals,
                limit=limit + 3,
            )

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
