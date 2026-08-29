# Thanatos/plugins/base/registry.py

"""Singleton skill registry for Thanatos."""

import logging
from typing import Dict, List, Optional

from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult
from plugins.base.skill_interface import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Central registry that holds all installed skills and dispatches tool calls."""

    def __init__(self) -> None:
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """Add a skill to the registry."""
        if skill.skill_name in self._skills:
            logger.info("Skill '%s' updated in registry.", skill.skill_name)
        self._skills[skill.skill_name] = skill
        logger.debug("Registered skill '%s' with %d tools.", skill.skill_name, len(skill.get_tool_definitions()))

    def unregister(self, skill_name: str) -> None:
        self._skills.pop(skill_name, None)

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        return self._skills.get(skill_name)

    def get_all_tools(self) -> List[ToolDefinition]:
        """Aggregate tool definitions from every registered skill."""
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
    """Auto-register all default domain and system skills."""
    try:
        from plugins.system_skills.job_hunter.job_hunter_skill import JobHunterSkill
        from plugins.system_skills.resume_tailor.resume_tailor_skill import ResumeTailorSkill
        from plugins.system_skills.job_applicator.job_applicator_skill import JobApplicatorSkill
        from plugins.system_skills.novel_agent.novel_skill import NovelAgentSkill
        from plugins.system_skills.self_improvement.self_improvement_skill import SelfImprovementSkill

        registry.register(JobHunterSkill())
        registry.register(ResumeTailorSkill())
        registry.register(JobApplicatorSkill())
        registry.register(NovelAgentSkill())
        registry.register(SelfImprovementSkill())
        logger.info("Default Thanatos skills initialized successfully.")
    except Exception as e:
        logger.warning("Could not auto-initialize some default skills: %s", e)


# Initialize on import
init_default_skills()
