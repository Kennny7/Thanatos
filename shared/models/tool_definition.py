# Thanatos/shared/models/tool_definition.py

from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ToolDefinition:
    """Schema for a tool (function) that the agent can call."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema for the function parameters
    required: Optional[list] = None