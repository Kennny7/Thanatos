# Thanatos/shared/models/tool_result.py

from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class ToolResult:
    """Result of executing a tool call."""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None