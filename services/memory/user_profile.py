# Thanatos/services/memory/user_profile.py

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    name: str = "User"
    email: str = "user@example.com"
    location: str = "Pune, India"
    title: str = "Software Engineer / AI Enthusiast"
    education: List[Dict[str, str]] = Field(default_factory=lambda: [
        {"degree": "Bachelor of Technology in Computer Science", "institution": "University of Pune", "year": "2024"}
    ])
    skills: List[str] = Field(default_factory=lambda: [
        "Python", "Flutter", "FastAPI", "Machine Learning", "LLMs", "RAG", "SQL", "Git", "Docker"
    ])
    experience: List[Dict[str, str]] = Field(default_factory=lambda: [
        {"role": "AI / ML Developer Intern", "company": "Tech Solutions", "duration": "2023 - 2024", "summary": "Built RAG systems and autonomous agent workflows."}
    ])
    projects: List[Dict[str, str]] = Field(default_factory=lambda: [
        {"name": "Thanatos Assistant", "tech": "Python, Flutter, LLMs, Vector DB", "summary": "Autonomous AI assistant capable of web scraping, RAG, and multi-agent coordination."}
    ])
    preferences: Dict[str, Any] = Field(default_factory=lambda: {
        "preferred_locations": ["Pune", "Remote", "Bangalore"],
        "target_roles": ["Software Engineer", "AI Engineer", "Fresher Developer", "Full Stack Developer"],
        "min_expected_salary": "6-12 LPA",
    })


class UserProfileManager:
    """Manages the user's career & knowledge profile for RAG and resume generation."""

    def __init__(self, memory_manager: Optional[Any] = None) -> None:
        self.profile = UserProfile()
        self.memory_manager = memory_manager

    def get_profile(self) -> UserProfile:
        return self.profile

    def update_profile(self, updates: Dict[str, Any]) -> UserProfile:
        current_data = self.profile.model_dump()
        current_data.update(updates)
        self.profile = UserProfile.model_validate(current_data)
        logger.info("User profile updated for %s", self.profile.name)
        return self.profile

    def get_resume_context(self) -> str:
        """Returns structured markdown context of the user's resume data."""
        p = self.profile
        skills_str = ", ".join(p.skills)
        edu_str = "\n".join([f"- {e['degree']} from {e['institution']} ({e['year']})" for e in p.education])
        exp_str = "\n".join([f"- {x['role']} at {x['company']} ({x['duration']}): {x['summary']}" for x in p.experience])
        proj_str = "\n".join([f"- **{pr['name']}** ({pr['tech']}): {pr['summary']}" for pr in p.projects])

        return f"""
# CANDIDATE PROFILE
- **Name**: {p.name}
- **Contact**: {p.email} | Location: {p.location}
- **Target Roles**: {", ".join(p.preferences.get("target_roles", []))}

## Technical Skills
{skills_str}

## Experience
{exp_str}

## Education
{edu_str}

## Key Projects
{proj_str}
""".strip()
