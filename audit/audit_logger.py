# Thanatos/audit/audit_logger.py

import logging
from typing import Any, Dict
from .chain_manager import ChainManager

logger = logging.getLogger(__name__)


class AuditLogger:
    """High-level audit logger recording agent actions and cryptographic hashes."""

    def __init__(self, chain_manager: Optional[ChainManager] = None) -> None:
        self.chain = chain_manager or ChainManager()

    def log_agent_action(self, agent_name: str, action: str, details: Dict[str, Any]) -> str:
        payload = {
            "agent": agent_name,
            "action": action,
            "details": details,
        }
        event_hash = self.chain.append_event("AGENT_ACTION", payload)
        logger.debug("Logged audit event: agent=%s action=%s hash=%s", agent_name, action, event_hash[:12])
        return event_hash


# Global instance
audit_service = AuditLogger()
