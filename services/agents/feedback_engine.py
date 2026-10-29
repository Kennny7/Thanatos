# Thanatos/services/agents/feedback_engine.py
"""
Feedback Engine — The Reward Signal Generator for Agent Trait Evolution.

Collects feedback from three sources:
1. EXPLICIT: User commands like '/rate good', '/rate bad', thumbs up/down
2. IMPLICIT: Heuristic sentiment analysis on the user's follow-up response
3. INTER-AGENT: Agents can rate each other's contributions

Feeds reward signals into the TraitEngine to shift personality vectors.
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from services.agents.trait_engine import trait_engine
from services.agents.topic_router import topic_router


# Sentiment heuristic patterns for implicit feedback
POSITIVE_INDICATORS = [
    r"\bthank",
    r"\bthanks\b",
    r"\bperfect\b",
    r"\bgreat\b",
    r"\bexcellent\b",
    r"\bawesome\b",
    r"\bexactly\b",
    r"\bthat'?s right\b",
    r"\byep\b",
    r"\byes\b",
    r"\byeah\b",
    r"\bcorrect\b",
    r"\bspot on\b",
    r"\bwell done\b",
    r"\bgood job\b",
    r"\bnice\b",
    r"\blove it\b",
    r"\bhelpful\b",
    r"\bbrilliant\b",
    r"\b(?:this|that) (?:is|was) (?:good|great|helpful|useful|perfect)\b",
    r"\bkeep (?:it up|going)\b",
    r"\bgot it\b",
    r"\bmakes sense\b",
    r"\b(?:really |very )?useful\b",
    r"\bhaha\b",
    r"\blol\b",
    r"\b(?:ha)+\b",  # laughter
]

NEGATIVE_INDICATORS = [
    r"\bwrong\b",
    r"\bno\b(?:\s|$|,|\.)",
    r"\bnope\b",
    r"\bstop\b",
    r"\bdon'?t\b",
    r"\bthat'?s not\b",
    r"\bincorrect\b",
    r"\bwhy (?:did|would|are) you\b",
    r"\bidiot\b",
    r"\buseless\b",
    r"\bterrible\b",
    r"\bawful\b",
    r"\bbad\b",
    r"\bstupid\b",
    r"\bwhat\?\b",
    r"\bi said\b",
    r"\bi already\b",
    r"\byou'?re not listening\b",
    r"\bthat makes no sense\b",
    r"\bnot (?:what|how|right)\b",
    r"\bi (?:didn'?t|don'?t) (?:ask|want|mean|say)\b",
    r"\brepeat\b(?:ed|ing)?\b",
    r"\bfixed? (?:this|that|it)\b",
]

CORRECTION_INDICATORS = [
    r"\binstead\b",
    r"\brather\b",
    r"\bactually\b",
    r"\bI (?:meant|mean)\b",
    r"\bno,?\s+(?:I|it|what)\b",
    r"\bshould (?:be|have)\b",
    r"\bnot (?:that|this)\b",
    r"\bprefer\b",
    r"\bremember (?:to|that)\b",
    r"\bstop (?:doing|saying|being)\b",
    r"\bdon'?t (?:do|say|be)\b",
]


class FeedbackEngine:
    """
    Collects and processes feedback signals for agent trait evolution.

    The engine maintains a short-term interaction buffer to link
    feedback to the agent/response that generated it.
    """

    def __init__(self) -> None:
        # Recent interaction buffer: list of (agent_id, user_text, timestamp)
        self._interaction_buffer: List[Dict[str, Any]] = []
        self._max_buffer = 20

    def record_interaction(self, agent_id: str, user_text: str, response_text: str) -> None:
        """Record an interaction so future feedback can be attributed."""
        self._interaction_buffer.append({
            "agent_id": agent_id,
            "user_text": user_text,
            "response_text": response_text[:200],
            "timestamp": time.time(),
        })
        # Trim buffer
        if len(self._interaction_buffer) > self._max_buffer:
            self._interaction_buffer = self._interaction_buffer[-self._max_buffer:]

    def _get_last_interaction(self) -> Optional[Dict[str, Any]]:
        """Get the most recent interaction from the buffer."""
        if self._interaction_buffer:
            return self._interaction_buffer[-1]
        return None

    # ------------------------------------------------------------------
    # Explicit Feedback
    # ------------------------------------------------------------------

    def process_explicit_feedback(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Check if user_text contains an explicit feedback command.

        Supported formats:
            /rate good, /rate bad, /rate [agent_name] good, /rate [agent_name] bad
            thumbs up, thumbs down, 👍, 👎
            good response, bad response

        Returns:
            Reward result dict if feedback was detected, None otherwise.
        """
        lower = user_text.strip().lower()

        # Check for /rate command
        rate_match = re.match(
            r"/?rate\s+(?:(\w+)\s+)?(good|bad|great|terrible|excellent|awful|perfect|horrible|ok|meh)",
            lower,
        )
        if rate_match:
            agent_name = rate_match.group(1)
            rating = rate_match.group(2)

            # Map rating to reward
            reward_map = {
                "good": 0.6, "great": 0.8, "excellent": 1.0, "perfect": 1.0,
                "ok": 0.2, "meh": 0.0,
                "bad": -0.6, "terrible": -0.8, "awful": -1.0, "horrible": -1.0,
            }
            reward = reward_map.get(rating, 0.0)
            return self._apply_feedback(reward, "explicit", f"User rated: {rating}", agent_name)

        # Check for thumbs/emoji
        if any(s in lower for s in ["👍", "thumbs up", "thumb up"]):
            return self._apply_feedback(0.6, "explicit", "Thumbs up")
        if any(s in lower for s in ["👎", "thumbs down", "thumb down"]):
            return self._apply_feedback(-0.6, "explicit", "Thumbs down")

        return None

    # ------------------------------------------------------------------
    # Implicit Feedback
    # ------------------------------------------------------------------

    def analyze_implicit_feedback(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze user's follow-up message for implicit sentiment signals.

        This runs on every user message (after checking for explicit feedback).
        Detects positive/negative patterns and applies a modest reward signal.
        Implicit rewards are weaker than explicit ones (capped at ±0.3).
        """
        lower = user_text.strip().lower()

        # Don't analyze very short messages or questions
        if len(lower) < 4 or lower.endswith("?"):
            return None

        positive_score = sum(
            1 for pattern in POSITIVE_INDICATORS
            if re.search(pattern, lower, re.IGNORECASE)
        )
        negative_score = sum(
            1 for pattern in NEGATIVE_INDICATORS
            if re.search(pattern, lower, re.IGNORECASE)
        )
        correction_score = sum(
            1 for pattern in CORRECTION_INDICATORS
            if re.search(pattern, lower, re.IGNORECASE)
        )

        # Net sentiment
        net = positive_score - negative_score - (correction_score * 0.5)

        if abs(net) < 1.0:
            return None  # Too ambiguous, skip

        # Cap implicit rewards to ±0.3 (much weaker than explicit)
        reward = max(-0.3, min(0.3, net * 0.1))

        detail = f"Implicit sentiment: +{positive_score}/-{negative_score}, corrections={correction_score}"
        return self._apply_feedback(reward, "implicit", detail)

    # ------------------------------------------------------------------
    # Inter-Agent Feedback
    # ------------------------------------------------------------------

    def apply_inter_agent_feedback(
        self,
        from_agent: str,
        to_agent: str,
        reward: float,
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        One agent rates another agent's performance.
        Used when agents collaborate and the managing agent (Alfred)
        evaluates subordinate agent contributions.
        """
        reward = max(-0.5, min(0.5, reward))  # Cap inter-agent rewards
        return trait_engine.apply_reward(
            agent_id=to_agent,
            reward=reward,
            trigger_type="inter_agent",
            trigger_detail=f"From {from_agent}: {reason}",
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _apply_feedback(
        self,
        reward: float,
        trigger_type: str,
        detail: str,
        target_agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply reward to the appropriate agent."""
        # Determine target agent
        agent_id = None

        if target_agent_name:
            # User specified an agent by name
            from services.agents.agent_personas import ALL_PERSONAS
            for aid, persona in ALL_PERSONAS.items():
                if target_agent_name.lower() in (
                    persona.name.lower(),
                    persona.persona_title.lower(),
                    aid,
                ):
                    agent_id = aid
                    break

        if not agent_id:
            # Default to last interacting agent
            last = self._get_last_interaction()
            if last:
                agent_id = last["agent_id"]
                detail += f" (attributed to last interaction)"

        if not agent_id:
            return {"applied": False, "reason": "No agent to attribute feedback to."}

        # Apply reward via trait engine
        result = trait_engine.apply_reward(
            agent_id=agent_id,
            reward=reward,
            trigger_type=trigger_type,
            trigger_detail=detail,
        )

        # Also update topic affinities based on the interaction
        last = self._get_last_interaction()
        if last and reward != 0.0:
            topic_router.learn_from_interaction(agent_id, last["user_text"], reward)

        result["applied"] = True
        return result

    def process_user_message(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point: check a user message for any feedback signal.
        Called by the coordinator on every message.

        Returns feedback result if detected, None if the message is just a normal prompt.
        """
        # 1. Check explicit feedback first (higher priority)
        explicit = self.process_explicit_feedback(user_text)
        if explicit:
            return explicit

        # 2. Check implicit feedback
        return self.analyze_implicit_feedback(user_text)


# Global singleton
feedback_engine = FeedbackEngine()
