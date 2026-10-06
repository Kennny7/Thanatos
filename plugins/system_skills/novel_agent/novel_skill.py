# Thanatos/plugins/system_skills/novel_agent/novel_skill.py

import logging
import os
from typing import Any, Dict, List
from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult
from services.creative.novel_manager import novel_manager

logger = logging.getLogger(__name__)

# Wuxia / Xianxia Chinese Novelist Framework Conventions
XIANXIA_GLOSSARY = {
    "Dao": "The Heavenly Dao (Natural Order)",
    "Qi": "Spiritual Qi (Primordial Essence)",
    "Cultivator": "Immortal Cultivator",
    "Sect": "Ancient Sect / Order",
    "Dantian": "Lower Dantian (Sea of Qi)",
    "Tribulation": "Heavenly Lightning Tribulation",
    "Realm": "Cultivation Stage (Qi Condensation -> Foundation Establishment -> Golden Core -> Nascent Soul)",
}


class NovelAgentSkill(BaseSkill):
    """
    Skill for long-form novel architecture, Wuxia/Xianxia generation,
    chapter folder indexing (Zettlr/markdown), and character evolution analysis.
    """

    category: str = "creative"

    @property
    def skill_name(self) -> str:
        return "novel_agent"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="scan_novel_project",
                description="Indexes a folder containing novel chapters (e.g. Zettlr markdown files), detects chapter order, and discards unindexed spam.",
                parameters={
                    "type": "object",
                    "properties": {
                        "folder_path": {"type": "string", "description": "Local path to the folder containing chapter files"},
                        "novel_title": {"type": "string", "description": "Optional title of the novel"},
                    },
                    "required": ["folder_path"],
                },
            ),
            ToolDefinition(
                name="track_character_evolution",
                description="Records or updates a character's cultivation realm, sect allegiance, and progression over chapters.",
                parameters={
                    "type": "object",
                    "properties": {
                        "novel_id": {"type": "string", "description": "Novel identifier"},
                        "name": {"type": "string", "description": "Character name"},
                        "realm": {"type": "string", "description": "Cultivation Realm / Stage"},
                        "sect": {"type": "string", "description": "Sect / Clan"},
                        "notes": {"type": "string", "description": "Personality shift or plot developments"},
                        "chapter": {"type": "integer", "description": "Chapter number"},
                    },
                    "required": ["novel_id", "name"],
                },
            ),
            ToolDefinition(
                name="generate_wuxia_chapter",
                description="Generates or refines a Wuxia/Xianxia novel chapter following Chinese Novelist tropes, cultivating pacing, and poetic cadence.",
                parameters={
                    "type": "object",
                    "properties": {
                        "plot_outline": {"type": "string", "description": "Rough plot points or events for the chapter"},
                        "protagonist": {"type": "string", "description": "Main character name & current realm"},
                        "antagonist": {"type": "string", "description": "Opponent / rival sect name"},
                        "conflict": {"type": "string", "description": "Core conflict or treasure contention"},
                    },
                    "required": ["plot_outline"],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "scan_novel_project":
            folder = params.get("folder_path", "")
            title = params.get("novel_title")
            res = novel_manager.scan_novel_folder(folder, title)
            return ToolResult.success_result(tool_name=tool_name, content=res)

        elif tool_name == "track_character_evolution":
            nid = params.get("novel_id", "")
            name = params.get("name", "")
            realm = params.get("realm", "Qi Condensation")
            sect = params.get("sect", "Independent")
            notes = params.get("notes", "")
            ch = params.get("chapter", 1)
            novel_manager.record_character(nid, name, realm, sect, notes, ch)
            return ToolResult.success_result(tool_name=tool_name, content={"status": "recorded", "character": name})

        elif tool_name == "generate_wuxia_chapter":
            outline = params.get("plot_outline", "")
            mc = params.get("protagonist", "Lin Feng")
            antag = params.get("antagonist", "Young Master of the Iron Blood Clan")

            chapter_content = f"""# Chapter Draft: Unyielding Will

The autumn wind swept across the jagged peaks of the Azure Cloud Mountain, carrying the faint scent of blood and pine.

{mc} stood with his hands clasped behind his back, his coarse hemp robes fluttering in the chilling gale. Deep within his dantian, the nine spiritual meridians pulsed with golden luminescence—each breath synchronizing with the primordial rhythm of the Heavenly Dao.

"You have courted death, junior!" a cold sneer echoed through the mist. {antag} emerged, his silver-embroidered boots crushing the withered leaves beneath his feet. "Hand over the Spirit Dew, and I might leave your corpse intact."

{mc}'s expression remained undisturbed, akin to an ancient well without ripples. In the world of cultivation, the strong preyed upon the weak; reasoning was merely a luxury for those with equal power.

Slowly, {mc} lifted his right palm. The surrounding spiritual qi compressed into a razor-sharp vortex, whistling through the empty canyon.

---
*Draft generated following Xianxia Narrative Framework (pacing, face-slapping buildup, sensory martial descriptions).*
"""
            return ToolResult.success_result(tool_name=tool_name, content={"chapter_text": chapter_content})

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")

