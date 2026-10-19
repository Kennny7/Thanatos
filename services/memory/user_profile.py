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
    name: str = "Khushal Pareta"
    email: str = "khushalpareta9@gmail.com"
    location: str = "Navi Mumbai, Maharashtra, India"
    title: str = "AI / ML Engineer"
    portfolio_url: Optional[str] = "https://kennny7.github.io"
    github_url: Optional[str] = "https://github.com/Kennny7"
    linkedin_url: Optional[str] = "https://www.linkedin.com/in/khushal-pareta-704355338"
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
        """Seed baseline profile.json, online_profiles.md, and resume_template.tex if directory is empty on fresh clones."""
        files = os.listdir(self.profile_dir)
        if files:
            return

        # 1. Seed clean starter profile.json
        profile_json_path = os.path.join(self.profile_dir, "profile.json")
        try:
            with open(profile_json_path, "w", encoding="utf-8") as f:
                starter_profile = {
                    "schema_version": "2.0",
                    "personal": {
                        "full_name": self.profile.name or "Your Name",
                        "email": self.profile.email or "your.email@example.com",
                        "phone": "+91 00000 00000",
                        "location": self.profile.location or "City, Country",
                        "primary_title": self.profile.title or "Software Engineer",
                        "github_url": self.profile.github_url or "https://github.com/your-username",
                        "linkedin_url": self.profile.linkedin_url or "https://www.linkedin.com/in/your-profile",
                        "portfolio_url": self.profile.portfolio_url or "https://your-portfolio.dev",
                    },
                    "skills": self.profile.skills or ["Python", "Docker", "REST APIs", "SQL", "Git"],
                    "experience": [],
                    "education": [],
                    "projects": []
                }
                json.dump(starter_profile, f, indent=2)
        except Exception as e:
            logger.warning("Could not auto-seed profile.json: %s", e)

        # 2. Seed online_profiles.md
        links_md_path = os.path.join(self.profile_dir, "online_profiles.md")
        try:
            with open(links_md_path, "w", encoding="utf-8") as f:
                f.write(
                    f"# Online Profiles & Portfolio\n\n"
                    f"- **GitHub**: {self.profile.github_url or 'https://github.com/your-username'}\n"
                    f"- **LinkedIn**: {self.profile.linkedin_url or 'https://www.linkedin.com/in/your-profile'}\n"
                    f"- **Portfolio**: {self.profile.portfolio_url or 'https://your-portfolio.dev'}\n"
                )
        except Exception as e:
            logger.warning("Could not auto-seed online_profiles.md: %s", e)

        # 3. Seed universal starter resume_template.tex
        tex_path = os.path.join(self.profile_dir, "resume_template.tex")
        try:
            with open(tex_path, "w", encoding="utf-8") as f:
                f.write(r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[a4paper,left=1.8cm,right=1.8cm,top=1.6cm,bottom=1.6cm]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}

\titleformat{\section}{\large\bfseries}{}{0em}{}
\titlespacing*{\section}{0pt}{1em}{0.3em}
\newcommand{\sectionline}{\vspace{2pt}\noindent\rule{\textwidth}{0.5pt}\vspace{4pt}}

\begin{document}

\begin{center}
  {\LARGE\textbf{Your Name}}\\[4pt]
  {\normalsize\textbf{Software Engineer | Systems & AI}}\\[4pt]
  your.email@example.com $\bullet$ +91 00000 00000 $\bullet$ City, Country\\
  \href{https://linkedin.com}{LinkedIn} $\bullet$ \href{https://github.com}{GitHub} $\bullet$ \href{https://portfolio.dev}{Portfolio}
\end{center}

\section*{Profile}
\sectionline
Experienced engineer skilled in architecting scalable applications, high-performance backends, and cloud microservices.

\section*{Technical Skills}
\sectionline
\begin{itemize}[leftmargin=*, label=--]
  \item \textbf{Languages \& Frameworks:} Python, SQL, REST APIs, FastAPI, Docker
  \item \textbf{Systems \& Cloud:} Linux, Git, CI/CD, Containerization, Distributed Storage
\end{itemize}

\section*{Professional Experience}
\sectionline
\textbf{Software Engineer} \hfill Company Name \\
\textit{2023 -- Present}
\begin{itemize}[leftmargin=*, label=--]
  \item Designed and deployed resilient microservices, improving throughput and reliability.
\end{itemize}

\section*{Education}
\sectionline
\textbf{Bachelor of Technology / Science} \hfill 2019--2023\\
University / Institute Name

\end{document}
""")
        except Exception as e:
            logger.warning("Could not auto-seed resume_template.tex: %s", e)

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
                    # Check nested personal block if present (e.g. Master Profile schema 2.0)
                    personal = data.get("personal", {}) if isinstance(data.get("personal"), dict) else {}
                    
                    name_val = personal.get("full_name") or data.get("name")
                    if name_val:
                        self.profile.name = name_val

                    email_val = personal.get("email") or data.get("email")
                    if email_val:
                        self.profile.email = email_val

                    loc_val = personal.get("location") or data.get("location")
                    if loc_val:
                        self.profile.location = loc_val

                    title_val = personal.get("primary_title") or data.get("title")
                    if title_val:
                        self.profile.title = title_val

                    pf_val = personal.get("portfolio_url") or data.get("portfolio_url")
                    if pf_val:
                        self.profile.portfolio_url = pf_val

                    gh_val = personal.get("github_url") or data.get("github_url")
                    if gh_val:
                        self.profile.github_url = gh_val

                    li_val = personal.get("linkedin_url") or data.get("linkedin_url")
                    if li_val:
                        self.profile.linkedin_url = li_val

                    if "skills" in data and isinstance(data["skills"], list):
                        for s in data["skills"]:
                            if s not in self.profile.skills:
                                self.profile.skills.append(s)
            except Exception as e:
                logger.debug("Error parsing JSON profile in %s: %s", fname, e)

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
