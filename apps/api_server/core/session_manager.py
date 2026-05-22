# Thanatos/apps/api_server/core/session_manager.py
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationMemory:
    """Simple list-based memory for a conversation session."""
    messages: list[dict[str, Any]] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def add_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        self.messages.append({
            "role": "tool_call",
            "tool_name": tool_name,
            "arguments": arguments,
        })

    def get_messages(self) -> list[dict[str, Any]]:
        return self.messages.copy()


class SessionManager:
    """
    Holds the full state for a single WebSocket session.
    """
    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.memory = ConversationMemory()

    def remember_user_input(self, content: str) -> None:
        self.memory.add_user_message(content)

    def remember_assistant_output(self, content: str) -> None:
        self.memory.add_assistant_message(content)

    def remember_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> None:
        self.memory.add_tool_call(tool_name, arguments)