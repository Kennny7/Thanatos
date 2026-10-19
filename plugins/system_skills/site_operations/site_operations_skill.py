# Thanatos/plugins/system_skills/site_operations/site_operations_skill.py
"""
Site Operations Skill:
Equips Thanatos with direct autonomous tool execution for:
- Managing Docker Desktop lifecycle (launch, start, status, stop)
- Deploying enterprise database and streaming containers (PostgreSQL, MongoDB, Milvus, Neo4j, Kafka)
- Querying host system telemetry (CPU, RAM, Disks, Processes, Ports)
"""

import json
import logging
from typing import Any, Dict, List

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class SiteOperationsSkill(BaseSkill):
    """
    Direct system operations skill for Velma Sinclair and the Agent Coordinator.
    Enables autonomous execution of Docker Desktop, container clusters, and host telemetry.
    """

    @property
    def skill_name(self) -> str:
        return "site_operations"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="manage_docker_infrastructure",
                description="Autonomously launch Docker Desktop, deploy or halt enterprise database containers (Postgres, Mongo, Milvus, Neo4j, Kafka), or inspect live container states.",
                parameters={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start", "status", "stop", "ensure"],
                            "description": "Action to perform: 'start' launches Docker Desktop if down and brings up all database containers; 'status' inspects live container health; 'stop' safely stops containers; 'ensure' verifies running state."
                        },
                        "target_engines": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of engines to target e.g. ['postgres', 'mongodb', 'milvus', 'neo4j', 'kafka']. Default: all."
                        }
                    },
                    "required": ["action"],
                },
            ),
            ToolDefinition(
                name="get_system_telemetry",
                description="Query host machine CPU, RAM, disk, network connections, and top active processes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "include_top_processes": {
                            "type": "boolean",
                            "description": "Include top 5 CPU/RAM consuming processes (default: true)."
                        }
                    },
                },
            ),
            ToolDefinition(
                name="check_port_conflicts",
                description="Scan system network sockets to see which processes are binding critical database or gateway ports.",
                parameters={
                    "type": "object",
                    "properties": {
                        "ports": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "List of ports to verify (default: standard Thanatos ports 5436, 27018, 19530, 7474, 9092)."
                        }
                    },
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "manage_docker_infrastructure":
            action = params.get("action", "status")
            target_engines = params.get("target_engines")
            from services.agents.site_engineer_agent import site_engineer_agent

            if action in ("start", "ensure"):
                res = site_engineer_agent.auto_manage_docker(action="ensure", start_if_stopped=True)
                return ToolResult.success_result(tool_name=tool_name, content=res)
            elif action == "status":
                res = site_engineer_agent.auto_manage_docker(action="status")
                return ToolResult.success_result(tool_name=tool_name, content=res)
            elif action == "stop":
                from services.database.db_orchestrator import db_orchestrator
                res = db_orchestrator.stop_containers(target_engines=target_engines)
                return ToolResult.success_result(tool_name=tool_name, content=res)
            else:
                return ToolResult.error_result(tool_name=tool_name, error=f"Unknown action: {action}")

        elif tool_name == "get_system_telemetry":
            from services.agents.site_engineer_agent import site_engineer_agent
            telemetry = site_engineer_agent.collect_system_telemetry()
            return ToolResult.success_result(tool_name=tool_name, content=telemetry)

        elif tool_name == "check_port_conflicts":
            ports = params.get("ports")
            from services.agents.site_engineer_agent import site_engineer_agent
            conflicts = site_engineer_agent.check_port_conflicts(target_ports=ports)
            return ToolResult.success_result(tool_name=tool_name, content={"conflicts": conflicts})

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool: {tool_name}")
