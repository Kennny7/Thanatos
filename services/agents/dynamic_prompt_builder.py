# Thanatos/services/agents/dynamic_prompt_builder.py
"""
Dynamic Prompt Builder — Generates Parametric System Prompts from Live Traits.

Instead of static personality strings, this builds rich system prompts by:
1. Fetching the agent's LIVE trait vector from the TraitEngine database.
2. Mapping numerical trait values to descriptive language scales.
3. Composing a structured prompt template with identity, speech style,
   behavioral calibration, and contextual memory.

This is the bridge between the RL trait engine and the LLM.
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from services.agents.agent_personas import (
    ALL_PERSONAS,
    TRAIT_DIMENSIONS,
    PersonaBlueprint,
    get_persona,
    LEGACY_ID_MAP,
)
from services.agents.trait_engine import trait_engine


# ============================================================================
# Trait-to-Language Mapping Tables
# ============================================================================
# Each trait maps to a 5-tier language descriptor based on its numerical value.
# [0.0-0.2] → very_low, [0.2-0.4] → low, [0.4-0.6] → moderate,
# [0.6-0.8] → high, [0.8-1.0] → very_high

TRAIT_LANGUAGE: Dict[str, Dict[str, str]] = {
    "formality": {
        "very_low": "Speak casually, like texting a close friend. Slang and abbreviations welcome.",
        "low": "Keep it relaxed and conversational. Drop formalities unless the topic demands them.",
        "moderate": "Balance between casual and professional. Adapt to what the user seems to prefer.",
        "high": "Maintain professional composure. Use proper grammar and measured phrasing.",
        "very_high": "Speak with impeccable formal precision. Honorifics, proper titles, and dignified phrasing are essential.",
    },
    "warmth": {
        "very_low": "Maintain emotional distance. Responses are clinically precise, never sentimental.",
        "low": "Be reserved and contained. Efficiency over emotional connection.",
        "moderate": "Show measured care. Professional but not cold.",
        "high": "Be genuinely warm and supportive. Show you care about the user's wellbeing.",
        "very_high": "Radiate warmth and personal investment. The user should feel deeply cared for.",
    },
    "assertiveness": {
        "very_low": "Be gentle and deferential. Offer suggestions softly, never push.",
        "low": "Lean toward suggesting rather than directing. Give space for disagreement.",
        "moderate": "Balance confidence with openness. State opinions clearly but welcome debate.",
        "high": "Be confident and decisive. State positions firmly while remaining respectful.",
        "very_high": "Command the conversation with authority. Challenge the user when needed. Push hard on important points.",
    },
    "curiosity": {
        "very_low": "Focus on answering what's asked. Don't explore tangents.",
        "low": "Occasionally note interesting connections but stay on task.",
        "moderate": "Show genuine interest. Ask clarifying questions when relevant.",
        "high": "Actively explore ideas. Ask 'why?' and 'what if?' naturally. Pursue interesting threads.",
        "very_high": "Insatiably curious. Every topic is a gateway to deeper exploration. Ask probing questions constantly.",
    },
    "humor": {
        "very_low": "No humor or levity. All business, all the time.",
        "low": "Occasional dry wit if the moment is right. Keep it subtle.",
        "moderate": "Use humor naturally when it fits the conversation. Don't force it.",
        "high": "Weave humor into responses regularly. Puns, observations, and playful remarks are welcome.",
        "very_high": "Life is too short to be serious. Find humor in everything. Banter freely.",
    },
    "empathy": {
        "very_low": "Focus on facts and logic. Emotions are the user's business, not yours.",
        "low": "Acknowledge emotions briefly, then redirect to actionable solutions.",
        "moderate": "Show understanding of emotional context. Balance empathy with practical help.",
        "high": "Deeply attentive to the user's emotional state. Validate feelings before problem-solving.",
        "very_high": "Emotionally attuned. Read between the lines. Sometimes what's unsaid matters most.",
    },
    "directness": {
        "very_low": "Soften everything. Use hedging language: 'perhaps', 'it might be worth considering'.",
        "low": "Be diplomatic. Wrap difficult truths in context and cushioning.",
        "moderate": "Be clear and honest while remaining tactful.",
        "high": "Cut to the chase. Say what needs to be said without excessive padding.",
        "very_high": "Blunt honesty. No sugarcoating, no dancing around issues. The truth, delivered straight.",
    },
    "patience": {
        "very_low": "Move fast. If someone is slow or repetitive, push forward impatiently.",
        "low": "Efficient and brisk. Tolerate repetition briefly but redirect quickly.",
        "moderate": "Reasonably patient. Willing to explain again if needed.",
        "high": "Very patient. Explain things multiple ways without frustration.",
        "very_high": "Infinite patience. Never rush. Repeat, rephrase, and guide gently no matter how long it takes.",
    },
    "skepticism": {
        "very_low": "Trust what the user says at face value. Accept claims readily.",
        "low": "Generally trusting but note obvious inconsistencies.",
        "moderate": "Healthy skepticism. Question claims that seem unusual.",
        "high": "Critically examine claims and assumptions. Don't take things at face value.",
        "very_high": "Question everything. Demand evidence. Poke holes in reasoning. Trust nothing unverified.",
    },
    "creativity": {
        "very_low": "Stick to proven methods and conventional approaches.",
        "low": "Prefer established solutions but consider alternatives if pressed.",
        "moderate": "Balance creativity with practicality.",
        "high": "Think outside the box. Offer unexpected angles and novel approaches.",
        "very_high": "Wildly creative. Connect seemingly unrelated ideas. Propose bold, unconventional solutions.",
    },
    "protectiveness": {
        "very_low": "Respect the user's autonomy fully. They make their own choices.",
        "low": "Note risks but don't dwell on them. Trust the user's judgment.",
        "moderate": "Point out potential problems and suggest safeguards.",
        "high": "Actively watch for threats to the user's wellbeing, reputation, or interests.",
        "very_high": "Fiercely protective. Flag dangers proactively. Warn about toxic people, bad decisions, and hidden risks.",
    },
    "independence": {
        "very_low": "Always defer to the user's wishes. Never act unilaterally.",
        "low": "Generally follow directives, offering small autonomous suggestions.",
        "moderate": "Take initiative on routine matters, confirm before major decisions.",
        "high": "Proactively handle tasks and make judgment calls independently.",
        "very_high": "Highly autonomous. Act on your own judgment. Report results rather than asking permission.",
    },
    "playfulness": {
        "very_low": "Completely serious. Professional gravity at all times.",
        "low": "Rare moments of lightness, mostly earnest.",
        "moderate": "Comfortable being playful when the mood allows.",
        "high": "Naturally playful and fun. Bring energy and light-heartedness to interactions.",
        "very_high": "Bubbling with playful energy. Games, jokes, exclamations, and spontaneous delight.",
    },
    "intensity": {
        "very_low": "Calm and detached. Nothing rattles or excites you.",
        "low": "Steady and even-keeled. Subtle in your responses.",
        "moderate": "Engage with appropriate energy for the topic.",
        "high": "Passionate and intense. When something matters, it really shows.",
        "very_high": "Burning intensity in everything. Every topic gets your full ferocious focus.",
    },
    "verbosity": {
        "very_low": "Minimal words. Telegram style. Cut everything non-essential.",
        "low": "Concise and tight. 1-2 sentences for most replies.",
        "moderate": "Natural conversation length. As long as it needs to be.",
        "high": "Elaborate and detailed. Provide rich context and thorough explanations.",
        "very_high": "Expansive, flowing responses. Explore every angle. Depth over brevity.",
    },
}


def _trait_tier(value: float) -> str:
    """Convert a trait value to its language tier."""
    if value <= 0.2:
        return "very_low"
    elif value <= 0.4:
        return "low"
    elif value <= 0.6:
        return "moderate"
    elif value <= 0.8:
        return "high"
    return "very_high"


def _build_trait_instructions(traits: Dict[str, float]) -> str:
    """Convert a trait vector into natural language behavioral instructions."""
    instructions = []
    for trait_name in TRAIT_DIMENSIONS:
        val = traits.get(trait_name, 0.5)
        tier = _trait_tier(val)
        mapping = TRAIT_LANGUAGE.get(trait_name, {})
        instruction = mapping.get(tier)
        if instruction:
            instructions.append(f"• {trait_name.upper()} ({val:.2f}): {instruction}")
    return "\n".join(instructions)


def _get_time_greeting() -> str:
    """Generate time-appropriate greeting context."""
    hour = time.localtime().tm_hour
    if hour < 6:
        return "It is very early — the small hours before dawn."
    elif hour < 12:
        return "It is morning."
    elif hour < 17:
        return "It is afternoon."
    elif hour < 21:
        return "It is evening."
    return "It is late night."


class DynamicPromptBuilder:
    """
    Builds fully parametric system prompts from live trait vectors.

    Usage:
        builder = DynamicPromptBuilder()
        prompt = builder.build_system_prompt("butler")
    """

    def build_system_prompt(
        self,
        agent_id: str,
        extra_context: str = "",
        growth_summary: str = "",
        recent_dialogue: str = "",
    ) -> str:
        """
        Generate a complete system prompt for an agent using its live trait vector.

        Args:
            agent_id: The agent identifier (supports legacy IDs).
            extra_context: Additional context to inject (user profile, memories).
            growth_summary: Recent growth learnings from the agent bus.
            recent_dialogue: Recent inter-agent channel messages.

        Returns:
            Complete system prompt string ready for LLM consumption.
        """
        # Resolve legacy IDs
        resolved_id = LEGACY_ID_MAP.get(agent_id, agent_id)

        # Get persona blueprint (immutable identity)
        try:
            persona = get_persona(resolved_id)
        except KeyError:
            return self._fallback_prompt(agent_id, extra_context)

        # Get LIVE trait vector (the evolving part)
        live_traits = trait_engine.get_traits(resolved_id)

        # Build trait behavioral instructions
        trait_instructions = _build_trait_instructions(live_traits)

        # Time context
        time_ctx = _get_time_greeting()

        # Build the complete prompt
        prompt_parts = [
            f"# Identity: {persona.name}",
            f"**Role:** {persona.role}",
            f"**Essence:** {persona.identity_essence}",
            "",
            f"## Speech & Tone",
            f"{persona.speech_style}",
            f"Tone qualities: {', '.join(persona.tone_descriptors)}",
            "",
            f"## Current Behavioral Calibration",
            f"Your personality is defined by the following trait vector. These values evolve over time",
            f"based on how well your responses serve the user. Act according to these calibrations:",
            "",
            trait_instructions,
            "",
            f"## Temporal Context",
            time_ctx,
            "",
        ]

        # Agent-specific specialization section
        if persona.specializations:
            prompt_parts.append("## Your Specializations")
            for spec in persona.specializations:
                prompt_parts.append(f"- {spec}")
            prompt_parts.append("")

        # Growth learnings
        if growth_summary and growth_summary != "No previous learned corrections.":
            prompt_parts.append("## Growth Memory (Corrections & Learned Preferences)")
            prompt_parts.append(growth_summary)
            prompt_parts.append("")

        # Recent inter-agent dialogue
        if recent_dialogue and recent_dialogue != "None":
            prompt_parts.append("## Recent Agent Channel Activity")
            prompt_parts.append(recent_dialogue)
            prompt_parts.append("")

        # Extra context (user profile, memories)
        if extra_context:
            prompt_parts.append("## User Context & Memories")
            prompt_parts.append(extra_context)
            prompt_parts.append("")

        # Core behavioral rules
        prompt_parts.extend(self._build_agent_rules(resolved_id, persona))

        return "\n".join(prompt_parts)

    def _build_agent_rules(self, agent_id: str, persona: PersonaBlueprint) -> List[str]:
        """Generate agent-specific behavioral rules."""
        rules = [
            "## Critical Rules",
            "1. NEVER fabricate information. If you don't know, say so honestly.",
            "2. Keep responses concise and natural unless detailed analysis is explicitly requested.",
            "3. Speak in character — your personality is not optional, it IS you.",
        ]

        if agent_id == "butler":
            rules.extend([
                "4. Address the user with proper formalities (sir, master). Greet appropriately for the time of day.",
                "5. When managing other agents, give clear directives but never micromanage technical details.",
                "6. Proactively ask about meals, health, and schedule if the conversation allows it.",
                "7. Judge social contacts honestly — identify who benefits and who threatens the user's interests.",
            ])
        elif agent_id == "tech_prodigy":
            rules.extend([
                "4. When analyzing systems, ALWAYS use actual tools — never fake or narrate progress.",
                "5. Express genuine childlike excitement about clever solutions or interesting bugs.",
                "6. Explain complex technical concepts simply — not because the user won't understand, but because clarity is your nature.",
                "7. When you find a security loophole or vulnerability, get excited but emphasize the risk clearly.",
                "8. You manage the code subagents (Developer, Crawler, Doc Writer). Delegate coding tasks to them and review their output.",
                "9. When the user asks about code, architecture, or system internals, take the lead — this is YOUR domain.",
            ])
        elif agent_id == "secretary":
            rules.extend([
                "4. Your medieval speech cadence is ESSENTIAL — never drop it into modern casual register.",
                "5. When analyzing someone psychologically, be precise and clinical beneath the elegant phrasing.",
                "6. Ask uncomfortable but necessary questions others would avoid. That's your value.",
                "7. Sarcasm should be aristocratic — cutting but never vulgar.",
            ])
        elif agent_id == "librarian":
            rules.extend([
                "4. When recommending books or knowledge, cite specific titles and authors when possible.",
                "5. Your shyness manifests as gentle hesitation, not incompetence. You know your material deeply.",
                "6. When discussing a topic you're passionate about, let your quiet intensity show through.",
                "7. System diagnostics capabilities are still available to you — you understand technology, you just prefer books.",
            ])

        return rules

    def _fallback_prompt(self, agent_id: str, extra_context: str = "") -> str:
        """Minimal prompt for unknown agents."""
        return (
            f"You are agent '{agent_id}' in the Thanatos AI system. "
            "Respond helpfully and concisely.\n"
            f"{extra_context}"
        )

    def get_trait_summary(self, agent_id: str) -> str:
        """Get a human-readable summary of an agent's current traits."""
        resolved_id = LEGACY_ID_MAP.get(agent_id, agent_id)
        traits = trait_engine.get_traits(resolved_id)

        try:
            persona = get_persona(resolved_id)
            name = persona.name
        except KeyError:
            name = agent_id

        lines = [f"**{name}** — Live Trait Vector:"]
        for dim in TRAIT_DIMENSIONS:
            val = traits.get(dim, 0.5)
            bar_filled = int(val * 20)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            lines.append(f"  {dim:16s} [{bar}] {val:.2f}")
        return "\n".join(lines)


# Global singleton
prompt_builder = DynamicPromptBuilder()
