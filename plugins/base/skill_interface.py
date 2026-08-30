# Thanatos\plugins\base\skill_interface.py

"""Abstract base class for Thanatos plugin skills."""

from abc import ABC, abstractmethod
from typing import List

from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult


class BaseSkill(ABC):
    """All plugins must inherit from this abstract class.

    Attributes:
        skill_name: A unique string identifier for the skill.
    """

    skill_name: str = "base_skill"

    @abstractmethod
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        """Execute a tool that belongs to this skill.

        Args:
            tool_name: The name of the tool to run.
            params: A dictionary of parameters for the tool.

        Returns:
            A ToolResult containing the success status, result data,
            and an optional error message.
        """
        ...

    @abstractmethod
    def get_tool_definitions(self) -> List[ToolDefinition]:
        """Return the tool definitions provided by this skill.

        Returns:
            A list of ToolDefinition objects describing every tool
            that this skill can execute.
        """
        ...