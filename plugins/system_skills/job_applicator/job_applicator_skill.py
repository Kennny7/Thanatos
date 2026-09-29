import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional
import uuid

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

APPLICATIONS_LOG_FILE = os.path.join("logs", "job_applications.jsonl")


class JobApplicatorSkill(BaseSkill):
    """
    Skill for packaging, generating humanized email outreach, and tracking automated job applications.
    """

    def __init__(self) -> None:
        self.application_history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self) -> None:
        if os.path.exists(APPLICATIONS_LOG_FILE):
            try:
                with open(APPLICATIONS_LOG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            self.application_history.append(json.loads(line))
            except Exception as e:
                logger.warning("Could not load application history: %s", e)

    def _persist_entry(self, entry: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(APPLICATIONS_LOG_FILE), exist_ok=True)
        try:
            with open(APPLICATIONS_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error("Could not append to applications log: %s", e)

    @property
    def skill_name(self) -> str:
        return "job_applicator"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="prepare_job_application",
                description="Prepares the submission payload, application tracker entry, and humanized email outreach for a target job.",
                parameters={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "ID of the target job"},
                        "job_title": {"type": "string", "description": "Title of the job"},
                        "company": {"type": "string", "description": "Company name"},
                        "recipient_email": {"type": "string", "description": "Hiring manager or talent email address"},
                        "hiring_manager": {"type": "string", "description": "Name/title of recipient"},
                        "tailored_resume": {"type": "string", "description": "Tailored resume markdown or latex"},
                        "cover_letter": {"type": "string", "description": "Personalized cover letter or email body"},
                        "status": {"type": "string", "description": "Status (e.g., Staged for Dispatch, Email Dispatched)"},
                    },
                    "required": ["job_title", "company"],
                },
            ),
            ToolDefinition(
                name="get_application_history",
                description="Fetches recent applied jobs and application logs.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max entries to return"},
                    },
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "prepare_job_application":
            app_id = f"app-{uuid.uuid4().hex[:8]}"
            now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            recipient_email = params.get("recipient_email") or f"talent@{params.get('company', 'company').lower().replace(' ', '')}.com"
            status = params.get("status", "Staged for Email Dispatch")

            entry = {
                "application_id": app_id,
                "job_id": params.get("job_id", ""),
                "job_title": params.get("job_title"),
                "company": params.get("company"),
                "recipient_email": recipient_email,
                "hiring_manager": params.get("hiring_manager", "Hiring Team"),
                "resume_preview": (params.get("tailored_resume") or "")[:200] + "...",
                "cover_letter": params.get("cover_letter", ""),
                "status": status,
                "timestamp": now_iso,
            }
            self.application_history.append(entry)
            self._persist_entry(entry)
            logger.info("Saved job application %s for %s (%s)", app_id, entry["company"], recipient_email)

            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "application_id": app_id,
                    "company": entry["company"],
                    "job_title": entry["job_title"],
                    "recipient_email": recipient_email,
                    "status": status,
                    "timestamp": now_iso,
                    "log_file": APPLICATIONS_LOG_FILE,
                    "message": f"Application for '{entry['job_title']}' at '{entry['company']}' successfully prepared and logged to {APPLICATIONS_LOG_FILE}.",
                },
            )

        elif tool_name == "get_application_history":
            limit = params.get("limit", 10)
            recent = self.application_history[-limit:][::-1]
            return ToolResult.success_result(
                tool_name=tool_name,
                content={
                    "total_logged": len(self.application_history),
                    "recent_applications": recent,
                    "log_path": os.path.abspath(APPLICATIONS_LOG_FILE),
                },
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
