# Thanatos/services/agents/topic_router.py
"""
Intelligent Topic-Based Agent Router — Replaces Hardcoded Keyword Matching.

Uses a lightweight embedding similarity approach to determine which agent(s)
should handle a given user message. Each agent has an evolving topic affinity
vector stored in the database (seeded from agent_personas.py, grown by the
RL trait engine based on interaction patterns).

Routing Algorithm:
1. Tokenize user message into key phrases.
2. Score each agent by matching against their topic affinity database.
3. Return ranked list of agents with relevance scores.
4. Primary agent handles the response; high-affinity secondary agents
   are CC'd on the agent bus for potential commentary.

This module avoids hardcoded keyword-to-agent mappings. The topic affinities
themselves evolve over time, so the routing becomes more personalized.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from services.agents.agent_personas import ALL_PERSONAS, LEGACY_ID_MAP
from services.agents.trait_engine import trait_engine

# Minimum score threshold for an agent to be considered relevant
PRIMARY_THRESHOLD = 0.15
SECONDARY_THRESHOLD = 0.10

# Common stop words to filter out during topic extraction
STOP_WORDS = frozenset({
    "i", "me", "my", "we", "our", "you", "your", "it", "its", "the", "a", "an",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "shall", "can", "may",
    "might", "must", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below", "up",
    "down", "out", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "not", "only", "same",
    "so", "than", "too", "very", "just", "don", "dont", "t", "s", "and", "but",
    "or", "nor", "if", "while", "about", "what", "which", "who", "whom", "this",
    "that", "these", "those", "any", "also", "been", "get", "got", "let", "tell",
    "think", "know", "want", "need", "like", "make", "take", "go", "come", "see",
    "look", "give", "use", "find", "say", "said", "please", "thanks", "thank",
    "hey", "hi", "hello", "ok", "okay", "yeah", "yes", "no", "right", "well",
})


class TopicRouter:
    """
    Scores and routes messages to the most relevant agent(s) based on
    evolving topic affinity vectors.
    """

    def __init__(self) -> None:
        # Cache for name/title-based direct addressing
        self._name_map: Dict[str, str] = {}
        self._build_name_map()

    def _build_name_map(self) -> None:
        """Build a mapping from agent names/titles to agent IDs for direct addressing."""
        for agent_id, persona in ALL_PERSONAS.items():
            name_lower = persona.name.lower()
            title_lower = persona.persona_title.lower()
            self._name_map[name_lower] = agent_id
            self._name_map[title_lower] = agent_id
            # Also map first name
            first_name = name_lower.split()[0]
            self._name_map[first_name] = agent_id

        # Legacy mappings
        self._name_map["velma"] = "librarian"
        self._name_map["sinclair"] = "librarian"
        self._name_map["pip"] = "tech_prodigy"
        self._name_map["ashworth"] = "tech_prodigy"
        self._name_map["prodigy"] = "tech_prodigy"

    def _extract_topics(self, text: str) -> List[str]:
        """Extract meaningful topic tokens from user text."""
        # Normalize and tokenize
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = clean.split()

        # Filter stop words and very short tokens
        meaningful = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

        # Also extract bigrams for compound topics
        bigrams = []
        for i in range(len(meaningful) - 1):
            bigrams.append(f"{meaningful[i]} {meaningful[i+1]}")

        return meaningful + bigrams

    def _check_direct_address(self, text: str) -> Optional[str]:
        """Check if the user is directly addressing a specific agent by name."""
        lower = text.lower().strip()
        for name, agent_id in self._name_map.items():
            # Check if name appears at the start, after a comma, or as a standalone mention
            if lower.startswith(name) or f" {name}" in lower or f", {name}" in lower:
                return agent_id
        return None

    def route(
        self,
        user_text: str,
        active_agent_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route a user message to the most relevant agent(s).

        Args:
            user_text: The user's message.
            active_agent_override: Force a specific agent (e.g., from roster.active_agent_id).

        Returns:
            Dict with:
                - primary_agent_id: The agent that should respond.
                - secondary_agents: List of agents to CC on the bus.
                - scores: All agent scores for debugging.
                - routing_reason: Why this agent was chosen.
        """
        # 1. Check for direct address (e.g., "Alfred, what should I have for lunch?")
        direct_agent = self._check_direct_address(user_text)
        if direct_agent:
            scores = self._compute_all_scores(user_text)
            secondary = [
                aid for aid, score in scores.items()
                if aid != direct_agent and score >= SECONDARY_THRESHOLD
            ]
            return {
                "primary_agent_id": direct_agent,
                "secondary_agents": secondary[:2],
                "scores": scores,
                "routing_reason": f"Direct address detected for '{direct_agent}'",
            }

        # 2. Check for forced override
        if active_agent_override and active_agent_override != "auto":
            resolved = LEGACY_ID_MAP.get(active_agent_override, active_agent_override)
            if resolved in ALL_PERSONAS:
                scores = self._compute_all_scores(user_text)
                secondary = [
                    aid for aid, score in scores.items()
                    if aid != resolved and score >= SECONDARY_THRESHOLD
                ]
                return {
                    "primary_agent_id": resolved,
                    "secondary_agents": secondary[:2],
                    "scores": scores,
                    "routing_reason": f"Active agent override: '{resolved}'",
                }

        # 3. Score all agents by topic affinity
        scores = self._compute_all_scores(user_text)

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Primary agent is the highest scorer (or default to butler if all scores are low)
        primary_id = ranked[0][0] if ranked[0][1] >= PRIMARY_THRESHOLD else "butler"

        # Secondary agents are any others above the secondary threshold
        secondary = [
            aid for aid, score in ranked[1:]
            if score >= SECONDARY_THRESHOLD and aid != primary_id
        ][:2]  # Max 2 secondary agents

        reason = f"Topic affinity scoring: {ranked[0][0]}={ranked[0][1]:.3f}"
        if ranked[0][1] < PRIMARY_THRESHOLD:
            reason = "Low affinity scores across all agents, defaulting to butler"

        return {
            "primary_agent_id": primary_id,
            "secondary_agents": secondary,
            "scores": scores,
            "routing_reason": reason,
        }

    def _compute_all_scores(self, user_text: str) -> Dict[str, float]:
        """Compute topic affinity scores for all agents against a user message."""
        extracted_topics = self._extract_topics(user_text)
        if not extracted_topics:
            return {aid: 0.0 for aid in ALL_PERSONAS}

        scores: Dict[str, float] = {}
        for agent_id in ALL_PERSONAS:
            affinities = trait_engine.get_topic_affinities(agent_id)
            if not affinities:
                scores[agent_id] = 0.0
                continue

            # Score: sum of affinities for matching topics, normalized
            total_score = 0.0
            matches = 0
            for topic in extracted_topics:
                # Exact match
                if topic in affinities:
                    total_score += affinities[topic]
                    matches += 1
                    continue

                # Substring/containment match
                for aff_topic, aff_val in affinities.items():
                    if topic in aff_topic or aff_topic in topic:
                        total_score += aff_val * 0.7  # Partial match discount
                        matches += 1
                        break

            # Normalize by number of extracted topics to get a 0-1 score
            if matches > 0:
                # Weighted: ratio of matching topics × average affinity strength
                coverage = matches / len(extracted_topics)
                avg_strength = total_score / matches
                scores[agent_id] = round(coverage * avg_strength, 4)
            else:
                scores[agent_id] = 0.0

        return scores

    def learn_from_interaction(
        self,
        agent_id: str,
        user_text: str,
        reward: float,
    ) -> None:
        """
        Update topic affinities based on interaction outcomes.
        If an agent handled a topic well (positive reward), increase its affinity.
        If poorly (negative reward), decrease it.
        """
        topics = self._extract_topics(user_text)
        delta = 0.02 * reward  # Small, gradual shifts

        for topic in topics[:10]:  # Cap to prevent over-updating on verbose messages
            trait_engine.update_topic_affinity(agent_id, topic, delta)


# Global singleton
topic_router = TopicRouter()
