# Thanatos/services/memory/user_profile.py

import hashlib
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from config.settings import app_config

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    name: str = app_config.user_name
    email: str = app_config.user_email
    location: str = app_config.user_location
    title: str = app_config.user_title
    portfolio_url: Optional[str] = "https://khushal-portfolio.dev"
    github_url: Optional[str] = "https://github.com/Kennny7"
    linkedin_url: Optional[str] = "https://linkedin.com/in/khushal-pareta"
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
    custom_documents: Dict[str, str] = Field(default_factory=dict)


class UserProfileManager:
    """
    Manages the user's career & knowledge profile from a multi-file folder repository.
    Supports continuous ingestion of Markdown, JSON, LaTeX (.tex), and text files
    with SHA-256 deduplication to avoid redundant reads or vector duplicates.
    """

    def __init__(self, memory_manager: Optional[Any] = None, profile_dir: Optional[str] = None) -> None:
        self.profile = UserProfile()
        self.memory_manager = memory_manager
        self.profile_dir = profile_dir or app_config.profile_dir
        self._file_hashes: Dict[str, str] = {}
        self._loaded_files: Set[str] = set()

        self._ensure_and_ingest_directory()

    def set_profile_directory(self, folder_path: str) -> Dict[str, Any]:
        """Switch or point to a new profile directory and ingest files."""
        self.profile_dir = folder_path
        return self._ensure_and_ingest_directory()

    def _calculate_file_hash(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _ensure_and_ingest_directory(self) -> Dict[str, Any]:
        os.makedirs(self.profile_dir, exist_ok=True)
        stats = {"added": 0, "updated": 0, "skipped": 0, "files": []}

        # Seed initial sample files if directory is completely empty
        self._seed_default_files_if_empty()

        for root, _, filenames in os.walk(self.profile_dir):
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in (".md", ".json", ".tex", ".txt", ".yaml", ".yml"):
                    continue

                full_path = os.path.join(root, fname)
                try:
                    fhash = self._calculate_file_hash(full_path)
                    prev_hash = self._file_hashes.get(full_path)

                    if prev_hash == fhash:
                        stats["skipped"] += 1
                        stats["files"].append({"file": fname, "status": "unchanged"})
                        continue

                    # File is new or updated
                    is_new = full_path not in self._file_hashes
                    self._parse_and_ingest_file(full_path, ext)
                    self._file_hashes[full_path] = fhash
                    self._loaded_files.add(full_path)

                    if is_new:
                        stats["added"] += 1
                        stats["files"].append({"file": fname, "status": "added"})
                    else:
                        stats["updated"] += 1
                        stats["files"].append({"file": fname, "status": "updated"})

                except Exception as e:
                    logger.warning("Error ingesting profile file %s: %s", full_path, e)

        logger.info("Profile directory %s synchronized: %s", self.profile_dir, stats)
        return stats

    def _seed_default_files_if_empty(self) -> None:
        """Seed baseline profile.json and resume.tex if directory is empty."""
        files = os.listdir(self.profile_dir)
        if files:
            return

        # Seed profile.json
        profile_json_path = os.path.join(self.profile_dir, "profile.json")
        try:
            with open(profile_json_path, "w", encoding="utf-8") as f:
                json.dump(self.profile.model_dump(), f, indent=2)
        except Exception:
            pass

        # Seed portfolio_links.md
        links_md_path = os.path.join(self.profile_dir, "online_profiles.md")
        try:
            with open(links_md_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Online Profiles & Portfolio\n\n"
                    f"- **GitHub**: {self.profile.github_url}\n"
                    f"- **LinkedIn**: {self.profile.linkedin_url}\n"
                    f"- **Portfolio**: {self.profile.portfolio_url}\n"
                )
        except Exception:
            pass

    def _parse_and_ingest_file(self, filepath: str, ext: str) -> None:
        """Parse contents of individual file and merge into profile & vector memory."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        fname = os.path.basename(filepath)
        self.profile.custom_documents[fname] = content

        # Extract links (GitHub, LinkedIn, Portfolio)
        gh_match = re.search(r"https?://(?:www\.)?github\.com/[a-zA-Z0-9_\-]+", content, re.IGNORECASE)
        if gh_match:
            self.profile.github_url = gh_match.group(0)

        li_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_\-]+", content, re.IGNORECASE)
        if li_match:
            self.profile.linkedin_url = li_match.group(0)

        pf_match = re.search(r"https?://[a-zA-Z0-9_\-]+\.(?:dev|io|me|com|tech)", content, re.IGNORECASE)
        if pf_match and "github" not in pf_match.group(0) and "linkedin" not in pf_match.group(0):
            self.profile.portfolio_url = pf_match.group(0)

        # Ingest JSON fields if applicable
        if ext == ".json":
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    if "name" in data and data["name"]:
                        self.profile.name = data["name"]
                    if "email" in data and data["email"]:
                        self.profile.email = data["email"]
                    if "location" in data and data["location"]:
                        self.profile.location = data["location"]
                    if "skills" in data and isinstance(data["skills"], list):
                        for s in data["skills"]:
                            if s not in self.profile.skills:
                                self.profile.skills.append(s)
                    if "portfolio_url" in data:
                        self.profile.portfolio_url = data["portfolio_url"]
                    if "github_url" in data:
                        self.profile.github_url = data["github_url"]
                    if "linkedin_url" in data:
                        self.profile.linkedin_url = data["linkedin_url"]
            except Exception:
                pass

        # Index into vector database if memory manager is attached
        if self.memory_manager and hasattr(self.memory_manager, "add_memory"):
            try:
                self.memory_manager.add_memory(
                    f"Profile Knowledge Document ({fname}):\n{content[:600]}",
                    metadata={"source": filepath, "filename": fname, "type": "profile_folder"},
                )
            except Exception as e:
                logger.debug("Could not index profile file into vector DB: %s", e)

    def sync(self) -> Dict[str, Any]:
        """Rescan the folder and ingest any added or modified documents without duplication."""
        return self._ensure_and_ingest_directory()

    def get_profile(self) -> UserProfile:
        return self.profile

    def get_links(self) -> Dict[str, Optional[str]]:
        return {
            "portfolio": self.profile.portfolio_url,
            "github": self.profile.github_url,
            "linkedin": self.profile.linkedin_url,
        }

    def get_resume_context(self) -> str:
        """Returns structured markdown context of the user's resume and profile folder."""
        p = self.profile
        skills_str = ", ".join(p.skills)
        edu_str = "\n".join([f"- {e['degree']} from {e['institution']} ({e['year']})" for e in p.education])
        exp_str = "\n".join([f"- {x['role']} at {x['company']} ({x['duration']}): {x['summary']}" for x in p.experience])
        proj_str = "\n".join([f"- **{pr['name']}** ({pr['tech']}): {pr['summary']}" for pr in p.projects])
        docs_loaded = ", ".join(self.profile.custom_documents.keys()) if self.profile.custom_documents else "None"

        return f"""
# CANDIDATE PROFILE & KNOWLEDGE REPOSITORY
- **Name**: {p.name}
- **Contact**: {p.email} | Location: {p.location}
- **GitHub**: {p.github_url or 'N/A'}
- **LinkedIn**: {p.linkedin_url or 'N/A'}
- **Portfolio**: {p.portfolio_url or 'N/A'}
- **Profile Folder**: `{self.profile_dir}` (Loaded Files: {docs_loaded})
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
