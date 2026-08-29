# Thanatos/apps/api_server/core/session_manager.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationMemory:
    """Session-based memory storing conversation turns."""
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        self.messages.append({
            "role": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
        })

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages.copy()

    def clear(self) -> None:
        self.messages.clear()


class SessionManager:
    """
    State manager for a single client session.
    """

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.memory = ConversationMemory()
        self.current_generator: Optional[Any] = None

    def remember_user_input(self, content: str) -> None:
        self.memory.add_user_message(content)

    def remember_assistant_output(self, content: str) -> None:
        self.memory.add_assistant_message(content)

    def remember_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        self.memory.add_tool_call(tool_name, arguments)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        return self.memory.get_messages()

    def clear_history(self) -> None:
        self.memory.clear()
