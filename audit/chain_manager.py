# Thanatos/audit/chain_manager.py

import json
import logging
import os
from typing import Any, Dict, List, Optional

from .crypto_utils import calculate_hash

logger = logging.getLogger(__name__)


class AuditBlock:
    def __init__(self, index: int, event_type: str, data: Dict[str, Any], previous_hash: str) -> None:
        self.index = index
        self.event_type = event_type
        self.data = data
        self.previous_hash = previous_hash
        self.hash = calculate_hash(data, previous_hash)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "event_type": self.event_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class ChainManager:
    """Manages an immutable, tamper-evident hash chain for security and agent audit logs."""

    def __init__(self, storage_path: str = "./audit/storage/audit_log.json") -> None:
        self.storage_path = storage_path
        self.chain: List[AuditBlock] = []
        self._load_chain()

    def _load_chain(self) -> None:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    raw_blocks = json.load(f)
                    for b in raw_blocks:
                        block = AuditBlock(
                            index=b["index"],
                            event_type=b["event_type"],
                            data=b["data"],
                            previous_hash=b["previous_hash"],
                        )
                        self.chain.append(block)
            except Exception as e:
                logger.warning("Could not load existing audit chain: %s", e)

        if not self.chain:
            genesis = AuditBlock(0, "GENESIS", {"message": "Thanatos Security Chain Initialized"}, "0" * 64)
            self.chain.append(genesis)
            self._save_chain()

    def _save_chain(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=2)
        except Exception as e:
            logger.warning("Could not persist audit chain: %s", e)

    def append_event(self, event_type: str, data: Dict[str, Any]) -> str:
        last_block = self.chain[-1]
        new_block = AuditBlock(
            index=len(self.chain),
            event_type=event_type,
            data=data,
            previous_hash=last_block.hash,
        )
        self.chain.append(new_block)
        self._save_chain()
        return new_block.hash

    def verify_integrity(self) -> bool:
        """Verifies every block hash against its predecessor."""
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr.previous_hash != prev.hash:
                return False
            if curr.hash != calculate_hash(curr.data, curr.previous_hash):
                return False
        return True
