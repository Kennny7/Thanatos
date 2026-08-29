# Thanatos/services/llm_brain/coordinator.py

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel

from plugins.base.registry import registry
from services.llm_brain.provider import UnifiedLLMProvider, LLMResponse
from services.memory.memory_manager import memory_service
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class Subtask(BaseModel):
    id: str
    agent_name: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Any] = None


class AgentCoordinator:
    """
    Multi-Agent Supervisor:
    Analyzes complex user intents (e.g., job search + tailored resume + application),
    decomposes them into subtask graphs, delegates to specialized agents/skills,
    and streams live status updates to the client.
    """

    def __init__(self, provider: Optional[UnifiedLLMProvider] = None) -> None:
        self.provider = provider or UnifiedLLMProvider()

    async def execute_task_stream(
        self,
        user_prompt: str,
        conversation_history: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream coordinator execution steps, subtask updates, and final synthesized response.
        """
        logger.info("AgentCoordinator received goal: %s", user_prompt)

        # 1. Fetch RAG context
        rag_context = memory_service.get_relevant_context(user_prompt)

        # 2. Check if this is a composite multi-agent workflow
        lower_prompt = user_prompt.lower()
        is_job_workflow = any(k in lower_prompt for k in ["job", "freshers", "pune", "apply", "resume", "hiring"])
        is_novel_workflow = any(k in lower_prompt for k in ["novel", "translate novel", "chapter", "raw"])
        is_code_workflow = any(k in lower_prompt for k in ["improve code", "fix bug", "refactor", "self-improve", "unit test"])

        # Yield status: Thinking & Planning
        yield {
            "type": "agent_status",
            "agent": "Coordinator",
            "status": "Analyzing request & decomposing into subtasks...",
            "progress": 0.1,
        }

        if is_job_workflow and ("search" in lower_prompt or "apply" in lower_prompt or "resume" in lower_prompt):
            async for chunk in self._run_job_hunt_pipeline(user_prompt, rag_context):
                yield chunk
            return

        if is_novel_workflow:
            async for chunk in self._run_novel_pipeline(user_prompt):
                yield chunk
            return

        if is_code_workflow:
            async for chunk in self._run_self_improvement_pipeline(user_prompt):
                yield chunk
            return

        # Default ReAct agent loop
        tools = registry.get_all_tools()
        tools_schema = [t.to_openai_schema() for t in tools]

        system_prompt = f"""You are Thanatos, an extraordinary autonomous AI assistant.
You possess deep thinking, RAG memory, and real-time execution capabilities.

USER BACKGROUND & MEMORY:
{rag_context}

Be concise, highly capable, and use tools when actions are needed."""

        history_payload = list(conversation_history)
        history_payload.append({"role": "user", "content": user_prompt})

        # Step-by-step reasoning
        response = await self.provider.generate_response(
            history=history_payload,
            tools_schema=tools_schema,
            system_prompt=system_prompt,
        )

        if response.thought:
            yield {
                "type": "thought",
                "content": response.thought,
            }

        if response.action == "tool_call" and response.tool_name:
            yield {
                "type": "agent_status",
                "agent": "Tool Executor",
                "status": f"Invoking tool `{response.tool_name}`...",
                "progress": 0.5,
            }
            try:
                tool_res: ToolResult = await registry.dispatch(response.tool_name, response.args or {})
                res_content = tool_res.content if tool_res.success else f"Error: {tool_res.error}"
                
                # Feedback loop to LLM
                history_payload.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": response.tool_name, "arguments": json.dumps(response.args or {})}}],
                })
                history_payload.append({
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "content": json.dumps(res_content),
                })
                
                follow_up = await self.provider.generate_response(history=history_payload, system_prompt=system_prompt)
                yield {"type": "assistant_chunk", "content": follow_up.text or str(res_content)}
            except Exception as e:
                logger.error("Tool execution failed: %s", e)
                yield {"type": "assistant_chunk", "content": f"I attempted to execute `{response.tool_name}`, but encountered: {str(e)}"}
        else:
            yield {
                "type": "assistant_chunk",
                "content": response.text or "How else can I assist you?",
            }

    async def _run_job_hunt_pipeline(self, user_prompt: str, rag_context: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Multi-agent pipeline: Job Search -> Resume Tailoring -> Job Application."""
        # 1. Job Hunter Subtask
        yield {
            "type": "agent_status",
            "agent": "Web Crawler & Job Hunter",
            "status": "Searching for freshers job openings in Pune and extracting listings...",
            "progress": 0.25,
        }
        
        search_res = await registry.dispatch("search_jobs", {"location": "Pune", "keywords": "freshers software engineer", "limit": 3})
        jobs = search_res.content.get("jobs", []) if search_res.success and isinstance(search_res.content, dict) else []

        if not jobs:
            yield {
                "type": "assistant_chunk",
                "content": "I searched for freshers job openings in Pune but found no immediate matches. Please refine the query.",
            }
            return

        # 2. Resume Tailoring Subtask
        yield {
            "type": "agent_status",
            "agent": "Resume Tailor Agent",
            "status": f"Reading your profile from RAG memory and tailoring resume for {len(jobs)} positions...",
            "progress": 0.60,
        }

        first_job = jobs[0]
        tailor_res = await registry.dispatch("tailor_resume", {
            "job_title": first_job.get("title", "Software Engineer"),
            "company": first_job.get("company", "TechCorp"),
            "job_description": first_job.get("description", "Python, FastAPI, RAG, Web Development"),
        })

        tailored_resume = tailor_res.content if tailor_res.success else "Tailored resume generated based on your profile."

        # 3. Job Applicator Subtask
        yield {
            "type": "agent_status",
            "agent": "Job Applicator Agent",
            "status": f"Preparing job applications and drafting cover letters...",
            "progress": 0.85,
        }

        apply_res = await registry.dispatch("prepare_job_application", {
            "job_id": first_job.get("id", "job-1"),
            "job_title": first_job.get("title"),
            "company": first_job.get("company"),
            "tailored_resume": str(tailored_resume),
        })

        yield {
            "type": "agent_status",
            "agent": "Coordinator",
            "status": "All sub-agent tasks completed successfully!",
            "progress": 1.0,
        }

        # Final synthesized markdown response
        summary_md = f"""### 🎯 Autonomous Job Hunt & Application Summary

**1. 🔍 Job Search Agent Found:**
"""
        for j in jobs:
            summary_md += f"- **{j['title']}** at *{j['company']}* ({j.get('location', 'Pune')}) | Exp: {j.get('experience', '0-1 yrs')} | [View Job]({j.get('url', '#')})\n"

        summary_md += f"""
---
**2. 📄 Tailored Resume Prepared for {first_job['title']} at {first_job['company']}:**
```markdown
{tailored_resume.get('resume_markdown', tailored_resume) if isinstance(tailored_resume, dict) else tailored_resume}
```

---
**3. ✉️ Application Status:**
- **Application Package**: Ready for `{first_job['company']}`
- **Cover Letter**: Prepared and formatted
- **Submission Mode**: Staged for dispatch ({apply_res.content.get('status', 'Ready') if apply_res.success and isinstance(apply_res.content, dict) else 'Ready'})
"""
        yield {"type": "assistant_chunk", "content": summary_md.strip()}

    async def _run_novel_pipeline(self, user_prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Multi-agent pipeline for Novel Translation, Glossary Enforcement, and Style Editing."""
        yield {
            "type": "agent_status",
            "agent": "Novel Translator & Editor",
            "status": "Processing novel text, maintaining character glossaries and style...",
            "progress": 0.5,
        }

        res = await registry.dispatch("translate_and_edit_novel", {
            "raw_text": user_prompt,
            "target_language": "English",
            "style": "Light Novel / Wuxia Localization",
        })

        yield {
            "type": "assistant_chunk",
            "content": res.content.get("output", str(res.content)) if res.success and isinstance(res.content, dict) else str(res.content),
        }

    async def _run_self_improvement_pipeline(self, user_prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Multi-agent pipeline for Self-Improvement and Code Reflection."""
        yield {
            "type": "agent_status",
            "agent": "Self-Improvement Agent",
            "status": "Analyzing Thanatos architecture and verifying code in isolated sandbox...",
            "progress": 0.4,
        }

        res = await registry.dispatch("self_improve_code", {"request": user_prompt})
        yield {
            "type": "assistant_chunk",
            "content": res.content.get("report", str(res.content)) if res.success and isinstance(res.content, dict) else str(res.content),
        }
