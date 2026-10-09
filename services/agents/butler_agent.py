# Thanatos/services/agents/butler_agent.py

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ContactDossier(BaseModel):
    contact_id: str
    full_name: str
    organization: Optional[str] = None
    role: Optional[str] = None
    social_dynamics: Dict[str, Any] = Field(default_factory=dict)
    key_traits: List[str] = Field(default_factory=list)
    interaction_history: List[Dict[str, Any]] = Field(default_factory=list)
    strategic_value: str = "Neutral"
    notes: List[str] = Field(default_factory=list)
    last_contact_ts: float = Field(default_factory=time.time)


class ButlerAgent:
    """
    Autonomous Butler Agent:
    - Maintains character dossiers and social dynamics from past interactions.
    - Evaluates social leverage, long-term strategic alignment, and interpersonal etiquette.
    - Operates with an isolated memory store to keep personal dossier intelligence segregated.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = storage_dir or os.path.join("data", "agent_memory", "butler")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.dossier_file = os.path.join(self.storage_dir, "social_dossiers.json")
        self.dossiers: Dict[str, ContactDossier] = self._load_dossiers()

    def _load_dossiers(self) -> Dict[str, ContactDossier]:
        if not os.path.exists(self.dossier_file):
            return {}
        try:
            with open(self.dossier_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: ContactDossier(**v) for k, v in data.items()}
        except Exception as e:
            logger.error("Failed loading Butler dossiers: %s", e)
            return {}

    def _save_dossiers(self) -> None:
        try:
            with open(self.dossier_file, "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.dossiers.items()}, f, indent=2)
        except Exception as e:
            logger.error("Failed saving Butler dossiers: %s", e)

    def record_interaction(
        self,
        name: str,
        interaction_summary: str,
        organization: Optional[str] = None,
        role: Optional[str] = None,
        observed_traits: Optional[List[str]] = None,
        strategic_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record or update a person's character dossier after an encounter or correspondence."""
        contact_id = name.lower().replace(" ", "_").strip()
        if contact_id not in self.dossiers:
            self.dossiers[contact_id] = ContactDossier(
                contact_id=contact_id,
                full_name=name,
                organization=organization,
                role=role,
                strategic_value=strategic_value or "Neutral"
            )

        dossier = self.dossiers[contact_id]
        if organization:
            dossier.organization = organization
        if role:
            dossier.role = role
        if strategic_value:
            dossier.strategic_value = strategic_value
        if observed_traits:
            for t in observed_traits:
                if t not in dossier.key_traits:
                    dossier.key_traits.append(t)

        dossier.interaction_history.append({
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": interaction_summary
        })
        dossier.last_contact_ts = time.time()
        self._save_dossiers()

        return {
            "status": "updated",
            "contact_id": contact_id,
            "name": dossier.full_name,
            "total_interactions": len(dossier.interaction_history),
            "traits": dossier.key_traits
        }

    def get_contact_briefing(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve executive dossier and behavioral dynamics before a call or meeting."""
        cid = name_or_id.lower().replace(" ", "_").strip()
        if cid in self.dossiers:
            return self.dossiers[cid].model_dump()
        for d in self.dossiers.values():
            if name_or_id.lower() in d.full_name.lower():
                return d.model_dump()
        return None

    def list_all_dossiers(self) -> List[Dict[str, Any]]:
        """List active contacts tracked in Butler intelligence memory."""
        return [
            {
                "contact_id": d.contact_id,
                "name": d.full_name,
                "org": d.organization,
                "strategic_value": d.strategic_value,
                "interactions_count": len(d.interaction_history)
            }
            for d in self.dossiers.values()
        ]
