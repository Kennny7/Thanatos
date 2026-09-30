# Thanatos/plugins/base/registry.py

"""Singleton skill registry for Thanatos with lazy skill resolution."""

import logging
from typing import Any, Callable, Dict, List, Optional

from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult
from plugins.base.skill_interface import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """
    Central registry that holds registered skills and lazy-loads skill instances on demand.
    """

    def __init__(self) -> None:
        self._skills: Dict[str, BaseSkill] = {}
        self._lazy_factories: Dict[str, Callable[[], BaseSkill]] = {}

    def register(self, skill: BaseSkill) -> None:
        """Add an instantiated skill to the registry."""
        self._skills[skill.skill_name] = skill
        logger.debug("Registered skill '%s'.", skill.skill_name)

    def register_lazy(self, skill_name: str, factory: Callable[[], BaseSkill]) -> None:
        """Register a lazy skill factory that initializes only when its tools are accessed."""
        self._lazy_factories[skill_name] = factory

    def _ensure_skill(self, skill_name: str) -> Optional[BaseSkill]:
        if skill_name in self._skills:
            return self._skills[skill_name]
        if skill_name in self._lazy_factories:
            try:
                skill = self._lazy_factories[skill_name]()
                self._skills[skill_name] = skill
                return skill
            except Exception as e:
                logger.warning("Failed lazy-loading skill '%s': %s", skill_name, e)
        return None

    def unregister(self, skill_name: str) -> None:
        self._skills.pop(skill_name, None)
        self._lazy_factories.pop(skill_name, None)

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        return self._ensure_skill(skill_name)

    def get_all_tools(self) -> List[ToolDefinition]:
        """Aggregate tool definitions from every registered and lazy skill."""
        # Ensure lazy skills are instantiated so their schemas are known
        for name in list(self._lazy_factories.keys()):
            self._ensure_skill(name)

        tools: List[ToolDefinition] = []
        for skill in self._skills.values():
            tools.extend(skill.get_tool_definitions())
        return tools

    async def dispatch(self, tool_name: str, params: dict) -> ToolResult:
        """Find the skill that owns the given tool and invoke its execution."""
        # Ensure lazy skills are instantiated so their tools can be dispatched
        for name in list(self._lazy_factories.keys()):
            self._ensure_skill(name)

        for skill in self._skills.values():
            for tool_def in skill.get_tool_definitions():
                if tool_def.name == tool_name:
                    try:
                        return await skill.execute(tool_name, params)
                    except Exception as e:
                        logger.exception("Error executing skill tool '%s': %s", tool_name, e)
                        return ToolResult.error_result(tool_name=tool_name, error=str(e))

        return ToolResult.error_result(tool_name=tool_name, error=f"Tool '{tool_name}' not found in any registered skill.")

    def identify_missing_capability(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Inspects existing tool capabilities against a task.
        If no existing tool matches the domain, formulates a proposed tool specification.
        """
        all_tools = self.get_all_tools()
        tool_names = [t.name for t in all_tools]
        lower_task = task_description.lower()

        # Check existing tool coverage
        for t in all_tools:
            if any(word in lower_task for word in t.name.split("_")):
                return None

        # Determine what capability is missing
        if any(w in lower_task for w in ["database backup", "export database", "dump db"]):
            return {
                "capability": "Database Export & Backup Skill",
                "suggested_skill_name": "db_backup_manager",
                "tool_name": "backup_vector_and_sqlite_stores",
                "reason": "Thanatos currently has memory search and profiling tools, but lacks automated database export/snapshot capabilities.",
            }
        elif any(w in lower_task for w in ["docker", "container", "containerize"]):
            return {
                "capability": "Docker Container Management Skill",
                "suggested_skill_name": "docker_manager",
                "tool_name": "manage_docker_containers",
                "reason": "Thanatos lacks direct Docker Engine socket orchestration tools.",
            }

        return {
            "capability": f"Specialized Tool for '{task_description[:40]}...'",
            "suggested_skill_name": "custom_extension",
            "tool_name": "execute_custom_task",
            "reason": f"No existing skill currently covers: {task_description}",
        }


# Module-level singleton
registry = SkillRegistry()


def init_default_skills() -> None:
    """Auto-register default domain skills using lazy factories for zero startup delay."""
    registry.register_lazy("job_hunter", lambda: __import__("plugins.system_skills.job_hunter.job_hunter_skill", fromlist=["JobHunterSkill"]).JobHunterSkill())
    registry.register_lazy("resume_tailor", lambda: __import__("plugins.system_skills.resume_tailor.resume_tailor_skill", fromlist=["ResumeTailorSkill"]).ResumeTailorSkill())
    registry.register_lazy("job_applicator", lambda: __import__("plugins.system_skills.job_applicator.job_applicator_skill", fromlist=["JobApplicatorSkill"]).JobApplicatorSkill())
    registry.register_lazy("security_auditor", lambda: __import__("plugins.system_skills.security_auditor.security_auditor_skill", fromlist=["SecurityAuditorSkill"]).SecurityAuditorSkill())
    registry.register_lazy("novel_agent", lambda: __import__("plugins.system_skills.novel_agent.novel_skill", fromlist=["NovelAgentSkill"]).NovelAgentSkill())
    registry.register_lazy("self_improvement", lambda: __import__("plugins.system_skills.self_improvement.self_improvement_skill", fromlist=["SelfImprovementSkill"]).SelfImprovementSkill())
    registry.register_lazy("web_search", lambda: __import__("plugins.system_skills.web_search.web_search_skill", fromlist=["WebSearchSkill"]).WebSearchSkill())


init_default_skills()
