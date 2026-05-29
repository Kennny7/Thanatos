# Thanatos\plugins\base\registry.py

"""Singleton skill registry for Thanatos."""

from typing import Dict

from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult
from plugins.base.skill_interface import BaseSkill


class SkillRegistry:
    """Central registry that holds all installed skills and dispatches tool calls."""

    def __init__(self) -> None:
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        """Add a skill to the registry.

        Args:
            skill: An instance of a class derived from BaseSkill.

        Raises:
            ValueError: If a skill with the same ``skill_name`` is already registered.
        """
        if skill.skill_name in self._skills:
            raise ValueError(
                f"Skill '{skill.skill_name}' is already registered."
            )
        self._skills[skill.skill_name] = skill

    def unregister(self, skill_name: str) -> None:
        """Remove a skill from the registry.

        Args:
            skill_name: The unique name of the skill to remove.
        """
        self._skills.pop(skill_name, None)

    def get_all_tools(self) -> list[ToolDefinition]:
        """Aggregate tool definitions from every registered skill.

        Returns:
            A flat list of ToolDefinition objects for all available tools.
        """
        tools: list[ToolDefinition] = []
        for skill in self._skills.values():
            tools.extend(skill.get_tool_definitions())
        return tools

    async def dispatch(self, tool_name: str, params: dict) -> ToolResult:
        """Find the skill that owns the given tool and invoke its execution.

        Args:
            tool_name: The name of the tool to execute.
            params: A dictionary of parameters for the tool.

        Returns:
            The ToolResult produced by the skill's ``execute`` method.

        Raises:
            ValueError: If no registered skill provides a tool with the given name.
        """
        for skill in self._skills.values():
            for tool_def in skill.get_tool_definitions():
                if tool_def.name == tool_name:
                    return await skill.execute(tool_name, params)
        raise ValueError(
            f"Tool '{tool_name}' not found in any registered skill."
        )


# Module-level singleton – import this instance elsewhere.
registry = SkillRegistry()