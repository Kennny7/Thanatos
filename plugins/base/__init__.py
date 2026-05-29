# Thanatos\plugins\base\__init__.py

"""Public API for the plugin base system."""

from plugins.base.skill_interface import BaseSkill
from plugins.base.registry import SkillRegistry, registry

__all__ = ["BaseSkill", "SkillRegistry", "registry"]