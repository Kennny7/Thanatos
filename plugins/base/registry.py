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

    def get_skills_by_category(self, category: str) -> List[BaseSkill]:
        """Return all skills belonging to a given category."""
        for name in list(self._lazy_factories.keys()):
            self._ensure_skill(name)
        return [s for s in self._skills.values() if getattr(s, "category", "system") == category]

    def list_categories(self) -> Dict[str, List[str]]:
        """Return all categories and their registered skill names."""
        for name in list(self._lazy_factories.keys()):
            self._ensure_skill(name)
        cat_map: Dict[str, List[str]] = {}
        for skill in self._skills.values():
            cat = getattr(skill, "category", "system")
            cat_map.setdefault(cat, []).append(skill.skill_name)
        return cat_map

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
        If the task asks for an action/tool that does not exist in any registered skill,
        dynamically formulates a proposed capability and tool specification instead of hardcoding.
        """
        all_tools = self.get_all_tools()
        lower_task = task_description.lower().strip()

        # Conversational, knowledge, philosophical, or greetings NEVER need tool creation
        conversational_markers = [
            "quote", "saying", "proverb", "who is", "what is", "why", "how", "tell me",
            "explain", "translate", "write a", "poem", "story", "joke", "hello", "hi",
            "hey", "bye", "goodbye", "help", "thanks", "thank you", "meaning of"
        ]
        if any(lower_task.startswith(m) or f" {m} " in f" {lower_task} " for m in conversational_markers):
            return None

        # Slash commands or escape commands are shell actions, not missing plugin requests
        if task_description.startswith(("/", "\\")):
            return None

        # Check existing tool coverage
        for t in all_tools:
            # Check if key tokens in the tool name appear in the task
            tokens = [tok for tok in t.name.split("_") if len(tok) > 3]
            if tokens and any(tok in lower_task for tok in tokens):
                return None

        # Check for action words indicating an intent to execute or integrate something new
        action_triggers = ["create feature", "build tool", "add support for", "integrate", "automate", "missing feature", "new capability"]
        if any(trig in lower_task for trig in action_triggers):
            # Derive capability dynamically from the user's description
            import re
            clean_name = re.sub(r"[^a-zA-Z0-9\s]", "", lower_task)
            words = [w for w in clean_name.split() if w not in ["can", "you", "please", "i", "want", "to", "a", "the", "create", "build", "tool", "feature", "for", "in", "my", "me"]]
            suggested_tag = "_".join(words[:4]) if words else "custom_automation"
            return {
                "capability": f"Dynamic Capability ({' '.join(words[:4]).title() or 'Custom Action'})",
                "suggested_skill_name": f"{suggested_tag}_skill",
                "tool_name": f"execute_{suggested_tag}",
                "reason": f"User requested '{task_description[:80]}' which is not covered by existing registered skills.",
            }

        return None


# Module-level singleton
registry = SkillRegistry()


def init_default_skills() -> None:
    """Auto-register default domain skills using lazy factories for zero startup delay."""
    registry.register_lazy("system_execution", lambda: __import__("plugins.system_skills.system_execution.system_execution_skill", fromlist=["SystemExecutionSkill"]).SystemExecutionSkill())
    registry.register_lazy("site_operations", lambda: __import__("plugins.system_skills.site_operations.site_operations_skill", fromlist=["SiteOperationsSkill"]).SiteOperationsSkill())
    registry.register_lazy("web_search", lambda: __import__("plugins.system_skills.web_search.web_search_skill", fromlist=["WebSearchSkill"]).WebSearchSkill())
    registry.register_lazy("security_auditor", lambda: __import__("plugins.system_skills.security_auditor.security_auditor_skill", fromlist=["SecurityAuditorSkill"]).SecurityAuditorSkill())
    registry.register_lazy("self_improvement", lambda: __import__("plugins.system_skills.self_improvement.self_improvement_skill", fromlist=["SelfImprovementSkill"]).SelfImprovementSkill())
    registry.register_lazy("novel_agent", lambda: __import__("plugins.system_skills.novel_agent.novel_skill", fromlist=["NovelAgentSkill"]).NovelAgentSkill())
    registry.register_lazy("job_hunter", lambda: __import__("plugins.system_skills.job_hunter.job_hunter_skill", fromlist=["JobHunterSkill"]).JobHunterSkill())
    registry.register_lazy("resume_tailor", lambda: __import__("plugins.system_skills.resume_tailor.resume_tailor_skill", fromlist=["ResumeTailorSkill"]).ResumeTailorSkill())
    registry.register_lazy("job_applicator", lambda: __import__("plugins.system_skills.job_applicator.job_applicator_skill", fromlist=["JobApplicatorSkill"]).JobApplicatorSkill())
    registry.register_lazy("dynamic_skill_factory", lambda: __import__("plugins.system_skills.dynamic_skill_factory.dynamic_skill_factory", fromlist=["DynamicSkillFactorySkill"]).DynamicSkillFactorySkill())


init_default_skills()

