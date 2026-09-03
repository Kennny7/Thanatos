# Thanatos/plugins/base/registry.py

"""Singleton skill registry for Thanatos with lazy skill resolution."""

import logging
from typing import Callable, Dict, List, Optional

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
        for skill in self._skills.values():
            for tool_def in skill.get_tool_definitions():
                if tool_def.name == tool_name:
                    try:
                        return await skill.execute(tool_name, params)
                    except Exception as e:
                        logger.exception("Error executing skill tool '%s': %s", tool_name, e)
                        return ToolResult.error_result(tool_name=tool_name, error=str(e))

        return ToolResult.error_result(tool_name=tool_name, error=f"Tool '{tool_name}' not found in any registered skill.")


# Module-level singleton
registry = SkillRegistry()


def init_default_skills() -> None:
    """Auto-register default domain skills using lazy factories for zero startup delay."""
    registry.register_lazy("job_hunter", lambda: __import__("plugins.system_skills.job_hunter.job_hunter_skill", fromlist=["JobHunterSkill"]).JobHunterSkill())
    registry.register_lazy("resume_tailor", lambda: __import__("plugins.system_skills.resume_tailor.resume_tailor_skill", fromlist=["ResumeTailorSkill"]).ResumeTailorSkill())
    registry.register_lazy("job_applicator", lambda: __import__("plugins.system_skills.job_applicator.job_applicator_skill", fromlist=["JobApplicatorSkill"]).JobApplicatorSkill())
    registry.register_lazy("novel_agent", lambda: __import__("plugins.system_skills.novel_agent.novel_skill", fromlist=["NovelAgentSkill"]).NovelAgentSkill())
    registry.register_lazy("self_improvement", lambda: __import__("plugins.system_skills.self_improvement.self_improvement_skill", fromlist=["SelfImprovementSkill"]).SelfImprovementSkill())


init_default_skills()
