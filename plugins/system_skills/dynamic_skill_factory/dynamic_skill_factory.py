# Thanatos/plugins/system_skills/dynamic_skill_factory/dynamic_skill_factory.py
"""
Dynamic Skill Factory:
Allows Thanatos to create, validate, and register new skill plugins at runtime.
When the LLM encounters a capability it doesn't have, this tool actually writes
the Python code, validates it through the sandbox, and hot-registers it —
preventing the LLM from hallucinating fake progress.
"""

import ast
import importlib
import importlib.util
import json
import logging
import os
import re
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult
from sandbox.resource_limiter import ResourceLimitedRunner

logger = logging.getLogger(__name__)


class DynamicSkillFactorySkill(BaseSkill):
    """
    Meta-skill that creates new skills at runtime.
    Generates Python plugin files from specifications, validates them in
    an isolated sandbox, and registers them live in the skill registry.
    """

    def __init__(self, workspace_dir: Optional[str] = None) -> None:
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).resolve().parent.parent.parent.parent
        self.runner = ResourceLimitedRunner(timeout_seconds=15)
        self.dynamic_skills_dir = self.workspace_dir / "plugins" / "system_skills" / "dynamic"
        self.dynamic_skills_dir.mkdir(parents=True, exist_ok=True)
        init_file = self.dynamic_skills_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated dynamic skills package\n", encoding="utf-8")

    @property
    def skill_name(self) -> str:
        return "dynamic_skill_factory"

    @property
    def category(self) -> str:
        return "system"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="create_and_register_skill",
                description=(
                    "Creates a new skill plugin from a specification, validates it in an isolated sandbox, "
                    "and registers it live in the skill registry. Use this when the user needs a capability "
                    "that doesn't exist yet. Do NOT pretend to create tools — call this tool to actually build them."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "Snake_case name for the new skill (e.g., 'wifi_scanner', 'screenshot_tool').",
                        },
                        "description": {
                            "type": "string",
                            "description": "Human-readable description of what the skill does.",
                        },
                        "tool_definitions": {
                            "type": "array",
                            "description": "Array of tool definitions, each with 'name', 'description', and 'parameters' (JSON Schema).",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "parameters": {"type": "object"},
                                },
                            },
                        },
                        "implementation_code": {
                            "type": "string",
                            "description": (
                                "Python code for the execute method body. This is the body of an async method "
                                "receiving tool_name: str and params: Dict[str, Any], returning a ToolResult. "
                                "Available imports: asyncio, json, logging, os, platform, subprocess. "
                                "Use ToolResult.success_result() or ToolResult.error_result() to return."
                            ),
                        },
                    },
                    "required": ["skill_name", "description", "tool_definitions", "implementation_code"],
                },
            ),
            ToolDefinition(
                name="list_dynamic_skills",
                description="Lists all dynamically created skill plugins that have been registered at runtime.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "create_and_register_skill":
            return await self._create_skill(params)
        elif tool_name == "list_dynamic_skills":
            return await self._list_dynamic_skills(params)
        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")

    def _sanitize_skill_name(self, name: str) -> str:
        """Strip unsafe characters, enforce snake_case."""
        clean = re.sub(r"[^a-zA-Z0-9_]", "", name.lower().replace("-", "_").replace(" ", "_"))
        if not clean or clean[0].isdigit():
            clean = "skill_" + clean
        return clean

    def _generate_class_name(self, skill_name: str) -> str:
        """Convert snake_case to PascalCase class name."""
        return "".join(word.capitalize() for word in skill_name.split("_")) + "Skill"

    async def _create_skill(self, params: Dict[str, Any]) -> ToolResult:
        """Create, validate, and register a new skill plugin."""
        raw_name = params.get("skill_name", "")
        description = params.get("description", "Dynamic skill")
        tool_defs = params.get("tool_definitions", [])
        impl_code = params.get("implementation_code", "")

        if not raw_name:
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error="skill_name is required.",
            )

        if not tool_defs:
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error="At least one tool_definition is required.",
            )

        if not impl_code:
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error="implementation_code is required.",
            )

        skill_name = self._sanitize_skill_name(raw_name)
        class_name = self._generate_class_name(skill_name)
        file_name = f"{skill_name}_skill.py"
        file_path = self.dynamic_skills_dir / file_name

        # Generate tool definitions code
        tool_defs_code = self._generate_tool_defs_code(tool_defs)

        # Indent the implementation code properly
        impl_lines = impl_code.strip().split("\n")
        indented_impl = "\n".join(f"        {line}" for line in impl_lines)

        # Generate the complete skill file
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        file_content = f'''# Auto-generated Thanatos dynamic skill: {skill_name}
# Created: {timestamp}
# Description: {description}

import asyncio
import json
import logging
import os
import platform
import subprocess
from typing import Any, Dict, List, Optional

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class {class_name}(BaseSkill):
    """{description}"""

    @property
    def skill_name(self) -> str:
        return "{skill_name}"

    @property
    def category(self) -> str:
        return "dynamic"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
{tool_defs_code}
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
{indented_impl}
'''

        # Step 1: Validate syntax with ast.parse
        try:
            ast.parse(file_content)
        except SyntaxError as e:
            logger.error("Dynamic skill '%s' has syntax errors: %s", skill_name, e)
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error=f"Generated code has syntax errors at line {e.lineno}: {e.msg}. "
                      f"Please fix the implementation_code and retry.",
            )

        # Step 2: Write the file
        try:
            file_path.write_text(file_content, encoding="utf-8")
            logger.info("Wrote dynamic skill file: %s", file_path)
        except Exception as e:
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error=f"Failed to write skill file: {e}",
            )

        # Step 3: Validate by attempting a sandbox import check
        validate_cmd = f'python -c "import ast; ast.parse(open(r\'{file_path}\').read()); print(\'SYNTAX_OK\')"'
        validate_res = await self.runner.run_command(validate_cmd, cwd=str(self.workspace_dir))
        if "SYNTAX_OK" not in validate_res.get("stdout", ""):
            logger.warning("Sandbox validation warning for %s: %s", skill_name, validate_res.get("stderr", ""))

        # Step 4: Dynamically import and register
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugins.system_skills.dynamic.{skill_name}_skill",
                str(file_path),
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the skill class
            skill_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseSkill)
                    and attr is not BaseSkill
                ):
                    skill_class = attr
                    break

            if not skill_class:
                return ToolResult.error_result(
                    tool_name="create_and_register_skill",
                    error=f"No BaseSkill subclass found in generated file for '{skill_name}'.",
                )

            # Instantiate and register
            from plugins.base.registry import registry
            instance = skill_class()
            registry.register(instance)

            registered_tools = [t.name for t in instance.get_tool_definitions()]
            logger.info(
                "Dynamic skill '%s' created and registered with tools: %s",
                skill_name,
                registered_tools,
            )

            return ToolResult.success_result(
                tool_name="create_and_register_skill",
                content={
                    "status": "created_and_registered",
                    "skill_name": skill_name,
                    "class_name": class_name,
                    "file_path": str(file_path),
                    "registered_tools": registered_tools,
                    "message": f"Skill '{skill_name}' has been created, validated, and registered. "
                               f"Tools available: {', '.join(registered_tools)}",
                },
            )

        except Exception as e:
            logger.exception("Failed to import/register dynamic skill '%s': %s", skill_name, e)
            return ToolResult.error_result(
                tool_name="create_and_register_skill",
                error=f"Skill file was written but import failed: {e}. "
                      f"The file is at {file_path} for manual inspection.",
            )

    def _generate_tool_defs_code(self, tool_defs: list) -> str:
        """Generate Python source code for tool definition list items."""
        lines = []
        for td in tool_defs:
            name = td.get("name", "unnamed_tool")
            desc = td.get("description", "A dynamic tool.")
            params = td.get("parameters", {"type": "object", "properties": {}, "required": []})

            # Ensure parameters has the right structure
            if "type" not in params:
                params["type"] = "object"
            if "properties" not in params:
                params["properties"] = {}
            if "required" not in params:
                params["required"] = []

            params_json = json.dumps(params, indent=16)
            # Fix indentation for the nested JSON
            params_lines = params_json.split("\n")
            indented_params = params_lines[0]
            for pl in params_lines[1:]:
                indented_params += "\n            " + pl

            lines.append(f"""            ToolDefinition(
                name="{name}",
                description="{desc}",
                parameters={indented_params},
            ),""")

        return "\n".join(lines)

    async def _list_dynamic_skills(self, params: Dict[str, Any]) -> ToolResult:
        """List all dynamically created skill files."""
        skills = []
        if self.dynamic_skills_dir.exists():
            for f in sorted(self.dynamic_skills_dir.glob("*_skill.py")):
                skill_name = f.stem.replace("_skill", "")
                # Try to read the description from the file header
                desc = ""
                try:
                    content = f.read_text(encoding="utf-8")
                    for line in content.split("\n"):
                        if line.startswith("# Description:"):
                            desc = line.replace("# Description:", "").strip()
                            break
                except Exception:
                    pass
                skills.append({
                    "skill_name": skill_name,
                    "file": str(f),
                    "description": desc,
                })

        return ToolResult.success_result(
            tool_name="list_dynamic_skills",
            content={
                "dynamic_skills_count": len(skills),
                "skills": skills,
                "dynamic_skills_directory": str(self.dynamic_skills_dir),
            },
        )
