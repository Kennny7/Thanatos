"""
Specialized Growth Subagents for Thanatos AI:
- Developer Subagent: Code implementation, refactoring, bug fixes, testing.
- Web Crawler Subagent: Live internet browsing, article scraping, documentation research.
- Doc Writer Subagent: Documentation, README generation, user manuals, markdown architecture reports.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
from services.llm_brain.provider import UnifiedLLMProvider
from services.agents.project_manager import project_manager

logger = logging.getLogger(__name__)


class BaseGrowthSubagent:
    """Base class for growth subagents that learn and refine work continuously."""

    def __init__(self, name: str, role: str, system_prompt: str, provider: Optional[UnifiedLLMProvider] = None) -> None:
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.provider = provider or UnifiedLLMProvider()
        self.task_history: List[Dict[str, Any]] = []

    def record_experience(self, task: str, result_summary: str) -> None:
        """Store growth experience to calibrate future executions."""
        self.task_history.append({"task": task, "summary": result_summary[:200]})


class DeveloperSubagent(BaseGrowthSubagent):
    """Developer Subagent for coding, modifying project code, debugging, and testing."""

    def __init__(self, provider: Optional[UnifiedLLMProvider] = None) -> None:
        super().__init__(
            name="Developer Subagent",
            role="Autonomous Software Engineer",
            system_prompt=(
                "You are the Developer Subagent for Thanatos. "
                "You write concise, clean, production-grade code. "
                "When addressing code changes, provide direct modifications and verify syntax. "
                "Keep responses compact, conversational, and direct."
            ),
            provider=provider,
        )

    async def execute_task(self, prompt: str, target_project: Optional[str] = None) -> Dict[str, Any]:
        context = ""
        if target_project:
            file_meta = project_manager.list_files(target_project)
            context = f"\nTarget Project: {target_project}\nDiscovered Files: {file_meta.get('files', [])[:20]}"

        full_prompt = f"{self.system_prompt}\n{context}\n\nTask: {prompt}\nBe concise and practical."
        resp = await self.provider.generate(full_prompt)
        text = resp.text.strip()
        self.record_experience(prompt, text)
        return {"agent": self.name, "result": text}


class CrawlerSubagent(BaseGrowthSubagent):
    """Crawler Subagent for live internet browsing, document scraping, and research."""

    def __init__(self, provider: Optional[UnifiedLLMProvider] = None) -> None:
        super().__init__(
            name="Web Crawler Subagent",
            role="Autonomous Internet Researcher & Web Crawler",
            system_prompt=(
                "You are the Web Crawler Subagent for Thanatos. "
                "You query live web information, summarize key findings, and extract direct answers. "
                "Keep answers brief, conversational, and omit filler text."
            ),
            provider=provider,
        )

    async def execute_task(self, query: str) -> Dict[str, Any]:
        from plugins.system_skills.web_search.web_search_skill import WebSearchSkill
        search_skill = WebSearchSkill()
        search_res = await search_skill.execute("search_web", {"query": query, "limit": 4})
        web_data = search_res.content if search_res.success else "Could not reach web search."

        prompt = f"{self.system_prompt}\n\nLive Search Data:\n{web_data}\n\nQuery: {query}\nSummarize concisely:"
        resp = await self.provider.generate(prompt)
        text = resp.text.strip()
        self.record_experience(query, text)
        return {"agent": self.name, "result": text, "sources": web_data}


class DocWriterSubagent(BaseGrowthSubagent):
    """Doc Writer Subagent for writing docs, guides, and structured markdown summaries."""

    def __init__(self, provider: Optional[UnifiedLLMProvider] = None) -> None:
        super().__init__(
            name="Doc Writer Subagent",
            role="Technical Documentation & Systems Writer",
            system_prompt=(
                "You are the Doc Writer Subagent for Thanatos. "
                "You write clean, structured technical documentation, markdown READMEs, and quick guides. "
                "Keep the tone clean, professional, concise, and avoid repetitive boilerplate."
            ),
            provider=provider,
        )

    async def execute_task(self, prompt: str) -> Dict[str, Any]:
        full_prompt = f"{self.system_prompt}\n\nDocumentation Task: {prompt}\nWrite clear and concise markdown:"
        resp = await self.provider.generate(full_prompt)
        text = resp.text.strip()
        self.record_experience(prompt, text)
        return {"agent": self.name, "result": text}
