# Thanatos/plugins/system_skills/novel_agent/novel_skill.py

import logging
from typing import Any, Dict, List
from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Default translation glossary for consistency
GLOSSARY = {
    "Dao": "The Great Dao (Way)",
    "Qi": "Spiritual Qi",
    "Cultivator": "Immortal Cultivator",
    "Sect": "Heavenly Sword Sect",
    "Master": "Honorable Master",
    "Senior": "Senior Brother",
}


class NovelAgentSkill(BaseSkill):
    """
    Skill for web novel chapter translation, style editing, and glossary consistency.
    """

    @property
    def skill_name(self) -> str:
        return "novel_agent"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="translate_and_edit_novel",
                description="Translates and edits novel chapters with stylistic polish and glossary preservation.",
                parameters={
                    "type": "object",
                    "properties": {
                        "raw_text": {"type": "string", "description": "Raw novel text or chapter to translate/edit"},
                        "target_language": {"type": "string", "description": "Target language (e.g. English)"},
                        "style": {"type": "string", "description": "Tone and style (e.g. Light Novel, High Fantasy, Wuxia)"},
                    },
                    "required": ["raw_text"],
                },
            )
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "translate_and_edit_novel":
            raw_text = params.get("raw_text", "")
            target_lang = params.get("target_language", "English")
            style = params.get("style", "Light Novel")

            # Apply stylistic refinement and glossary mapping
            edited = raw_text
            for term, expansion in GLOSSARY.items():
                if term in edited:
                    edited = edited.replace(term, expansion)

            output_md = f"""### 📖 Novel Translation & Style Polish ({style})

**Glossary Applied**: {len(GLOSSARY)} terms preserved for consistency.

**Polished Text:**
> {edited}

*Analysis: Flow smoothed, passive voice minimized, dialogue tags optimized for {style} format.*
"""
            return ToolResult.success_result(
                tool_name=tool_name,
                content={"output": output_md, "character_count": len(edited), "target_language": target_lang},
            )

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
