# Thanatos/services/agents/secretary_agent.py

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TasteProfile(BaseModel):
    coffee_preference: Optional[str] = "Double shot espresso, no sugar"
    work_routine: Optional[str] = "High-focus deep work mornings, meetings afternoons"
    dietary_preferences: List[str] = Field(default_factory=list)
    preferred_music_genres: List[str] = Field(default_factory=lambda: ["Synthwave", "Cyberpunk Dark Ambient", "Lo-Fi"])
    travel_habits: Dict[str, Any] = Field(default_factory=dict)
    custom_quirks: Dict[str, Any] = Field(default_factory=dict)


class AgendaItem(BaseModel):
    item_id: str
    title: str
    time_target: str
    priority: str = "Medium" # Urgent, High, Medium, Low
    category: str = "Work" # Work, Health, Personal, Jogging
    completed: bool = False
    created_at: float = Field(default_factory=time.time)


class SecretaryAgent:
    """
    Autonomous Secretary & Wingman Agent:
    - Oversees daily agendas, proactive reminders, workout/jogging routines.
    - Curates user taste preferences and lifestyle habits.
    - Operates with an isolated memory partition distinct from Butler and Career agents.
    """

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.storage_dir = storage_dir or os.path.join("data", "agent_memory", "secretary")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.agenda_file = os.path.join(self.storage_dir, "agenda.json")
        self.taste_file = os.path.join(self.storage_dir, "taste_profile.json")
        
        self.agenda: List[AgendaItem] = self._load_agenda()
        self.taste: TasteProfile = self._load_taste()

    def _load_agenda(self) -> List[AgendaItem]:
        if not os.path.exists(self.agenda_file):
            return []
        try:
            with open(self.agenda_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [AgendaItem(**item) for item in data]
        except Exception as e:
            logger.error("Failed loading agenda: %s", e)
            return []

    def _save_agenda(self) -> None:
        try:
            with open(self.agenda_file, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self.agenda], f, indent=2)
        except Exception as e:
            logger.error("Failed saving agenda: %s", e)

    def _load_taste(self) -> TasteProfile:
        if not os.path.exists(self.taste_file):
            return TasteProfile()
        try:
            with open(self.taste_file, "r", encoding="utf-8") as f:
                return TasteProfile(**json.load(f))
        except Exception as e:
            logger.error("Failed loading taste profile: %s", e)
            return TasteProfile()

    def _save_taste(self) -> None:
        try:
            with open(self.taste_file, "w", encoding="utf-8") as f:
                json.dump(self.taste.model_dump(), f, indent=2)
        except Exception as e:
            logger.error("Failed saving taste profile: %s", e)

    def add_schedule_task(self, title: str, time_target: str, priority: str = "High", category: str = "Work") -> Dict[str, Any]:
        """Add an event, reminder or milestone to the executive schedule."""
        item_id = f"task_{int(time.time())}_{len(self.agenda)}"
        item = AgendaItem(
            item_id=item_id,
            title=title,
            time_target=time_target,
            priority=priority,
            category=category
        )
        self.agenda.append(item)
        self._save_agenda()
        return item.model_dump()

    def list_pending_agenda(self) -> List[Dict[str, Any]]:
        """Retrieve all active schedule items and reminders."""
        return [item.model_dump() for item in self.agenda if not item.completed]

    def update_taste_preference(self, key: str, value: Any) -> Dict[str, Any]:
        """Adaptively learn user preferences (routine, food, music, style)."""
        if hasattr(self.taste, key):
            setattr(self.taste, key, value)
        else:
            self.taste.custom_quirks[key] = value
        self._save_taste()
        return {"status": "saved", "taste_profile": self.taste.model_dump()}
