# Thanatos/audit/crypto_utils.py

import hashlib
import json
from typing import Any


def calculate_hash(data: Any, previous_hash: str = "") -> str:
    """Computes a deterministic SHA-256 hash for audit events."""
    if isinstance(data, dict):
        payload_str = json.dumps(data, sort_keys=True)
    else:
        payload_str = str(data)
    combined = f"{previous_hash}:{payload_str}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()
