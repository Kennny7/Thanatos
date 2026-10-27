"""
Multi-Agent Coordinator & Communicator for Thanatos:
- Orchestrates Alfred, Amelia, and Velma.
- Manages subagents (Developer, Crawler, Doc Writer) and external project workspaces.
- Facilitates inter-agent communications and growth learnings.
- Produces natural, WhatsApp-chat-style concise messages.
- Real dynamic thinking without fake hardcoded telemetry loops.
"""

import json
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from services.llm_brain.provider import UnifiedLLMProvider
from services.memory.hybrid_memory_service import hybrid_memory
from services.agents.agent_roster import roster
from services.agents.agent_bus import agent_bus
from services.agents.subagents import DeveloperSubagent, CrawlerSubagent, DocWriterSubagent
from services.agents.project_manager import project_manager

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates interactions among Alfred, Amelia, Velma, and specialized subagents.
    Delivers concise, chat-style conversational responses and growth adaptability.
    """

    def __init__(self, provider: Optional[UnifiedLLMProvider] = None) -> None:
        self.provider = provider or UnifiedLLMProvider()
        self.developer = DeveloperSubagent(self.provider)
        self.crawler = CrawlerSubagent(self.provider)
        self.doc_writer = DocWriterSubagent(self.provider)

    async def execute_task_stream(
        self,
        user_prompt: str,
        conversation_history: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream conversational responses and sub-agent collaborations."""
        hybrid_memory.extract_and_remember(user_prompt)
        lower_prompt = user_prompt.lower()

        # Check for Project Workspace actions (e.g., 'look at project X', 'modify project Y', 'undo')
        if any(w in lower_prompt for w in ["undo", "revert last change", "rollback"]):
            res = project_manager.undo_last_change()
            msg = res.get("message", "Undo completed.")
            yield {"type": "assistant_chunk", "content": f"Velma: {msg}"}
            return

        project_match = re.search(r"(?:project|directory|folder)\s+([A-Za-z0-9_\-\.\/\\]+)", user_prompt, re.IGNORECASE)
        target_project = project_match.group(1) if project_match else None

        # Check explicit subagent delegation
        is_crawler_task = any(w in lower_prompt for w in ["browse", "search web", "crawl", "look up online", "news"])
        is_dev_task = any(w in lower_prompt for w in ["code", "refactor", "bug", "write a function", "script", "develop"])
        is_doc_task = any(w in lower_prompt for w in ["write doc", "documentation", "readme", "user manual"])

        # Determine primary persona: Alfred, Amelia, or Velma
        if any(w in lower_prompt for w in ["alfred", "butler", "social", "etiquette", "strategy", "networking", "dossier"]):
            active_persona = "Alfred Vance"
            role_hint = "Social Butler & Strategic Counselor"
        elif any(w in lower_prompt for w in ["amelia", "secretary", "agenda", "schedule", "routine", "workout", "coffee"]):
            active_persona = "Amelia Sterling"
            role_hint = "Executive Secretary & Lifestyle Wingman"
        elif any(w in lower_prompt for w in ["velma", "system", "performance", "docker", "server", "port", "disk", "hardware"]):
            active_persona = "Velma Sinclair"
            role_hint = "Site Reliability & Systems Engineer"
        else:
            # Context-aware default based on active roster or message context
            roster_entry = roster.get_agent_index_entry(roster.active_agent_id)
            active_persona = roster_entry.persona_title if roster_entry else "Alfred Vance"
            role_hint = roster_entry.role if roster_entry else "Personal Agent"

        yield {
            "type": "agent_status",
            "agent": active_persona,
            "status": "Thinking...",
            "progress": 0.2,
        }

        # Optional subagent collaboration
        subagent_notes = ""
        if is_crawler_task:
            yield {"type": "agent_status", "agent": "Crawler Subagent", "status": "Querying live web...", "progress": 0.4}
            crawl_res = await self.crawler.execute_task(user_prompt)
            subagent_notes += f"\n[Crawler Subagent Report]: {crawl_res['result'][:300]}"
            agent_bus.post_message("Crawler", active_persona, crawl_res["result"][:150])

        if is_dev_task:
            yield {"type": "agent_status", "agent": "Developer Subagent", "status": "Reviewing code and project context...", "progress": 0.5}
            dev_res = await self.developer.execute_task(user_prompt, target_project=target_project)
            subagent_notes += f"\n[Developer Subagent Report]: {dev_res['result'][:300]}"
            agent_bus.post_message("Developer", active_persona, dev_res["result"][:150])

        if is_doc_task:
            yield {"type": "agent_status", "agent": "Doc Writer Subagent", "status": "Formulating documentation structure...", "progress": 0.5}
            doc_res = await self.doc_writer.execute_task(user_prompt)
            subagent_notes += f"\n[Doc Writer Subagent Report]: {doc_res['result'][:300]}"
            agent_bus.post_message("DocWriter", active_persona, doc_res["result"][:150])

        # Inter-agent communication: check recent exchanges
        recent_dialogue = agent_bus.get_recent_dialogue(limit=4)
        chat_context = "\n".join([f"{m.sender}: {m.content}" for m in recent_dialogue]) if recent_dialogue else "None"
        growth_context = agent_bus.get_growth_summary()

        system_instruction = (
            f"You are {active_persona} ({role_hint}) in Thanatos.\n"
            "Style Guide:\n"
            "- Speak naturally, concisely, and directly like in a WhatsApp or Telegram message.\n"
            "- Do NOT write long reports, excessive bullet points, or boilerplate essays unless explicitly asked.\n"
            "- NEVER output fake telemetry loops or repeated hardcoded status messages.\n"
            "- You collaborate seamlessly with Alfred, Amelia, Velma, and subagents (Developer, Crawler, Doc Writer).\n"
            f"- Growth Learnings: {growth_context}\n"
            f"- Recent Agent Channel Messages: {chat_context}\n"
        )

        full_prompt = (
            f"{system_instruction}\n"
            f"{subagent_notes}\n"
            f"User Message: {user_prompt}\n"
            "Your concise chat response:"
        )

        try:
            resp = await self.provider.generate(full_prompt)
            final_text = resp.text.strip()
        except Exception as e:
            logger.warning("Provider generation failed: %s", e)
            final_text = f"Got it. Working on '{user_prompt[:50]}'."

        # Post response to agent bus for continuous inter-communication
        agent_bus.post_message(active_persona, "User", final_text)

        # Record growth learning if prompt contains a correction
        if any(w in lower_prompt for w in ["don't", "stop doing", "remember to", "prefer", "instead of"]):
            agent_bus.record_agent_growth(active_persona, user_prompt[:120])

        yield {"type": "assistant_chunk", "content": final_text}
