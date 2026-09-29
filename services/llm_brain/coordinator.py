# Thanatos/services/llm_brain/coordinator.py

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from pydantic import BaseModel

from plugins.base.registry import registry
from services.llm_brain.provider import UnifiedLLMProvider, LLMResponse
from services.memory.hybrid_memory_service import hybrid_memory
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
    General-purpose autonomous assistant engine.
    Decomposes tasks into subtask graphs, delegates to specialized skills,
    learns user facts continuously, and streams live status updates.
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

        # 1. Dynamically extract and store personal facts / preferences
        hybrid_memory.extract_and_remember(user_prompt)

        # 2. Fetch Hybrid RAG & Knowledge Context
        rag_context = hybrid_memory.get_context(user_prompt)
        asst_name = hybrid_memory.profile.assistant_name or "Aegis"

        # 3. Check if this is a composite multi-agent workflow
        lower_prompt = user_prompt.lower()
        is_job_workflow = any(k in lower_prompt for k in ["job", "freshers", "apply for job", "tailor resume"])
        is_novel_workflow = any(k in lower_prompt for k in ["novel", "translate novel", "raw chapter"])
        is_code_workflow = any(k in lower_prompt for k in ["improve code", "fix bug in thanatos", "refactor thanatos", "self-improve"])

        # Yield status: Thinking & Planning
        yield {
            "type": "agent_status",
            "agent": asst_name,
            "status": "Analyzing request & structuring response...",
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

        # 4. Relevant tool filtering to reduce Ollama prompt size & inference latency
        all_tools = registry.get_all_tools()
        
        # Heuristic matching: if prompt clearly targets specific domains, only inject those tools
        is_news_or_web = any(k in lower_prompt for k in ["news", "headline", "trending", "current events", "latest", "search", "lookup", "who is", "what happened"])
        is_job = any(k in lower_prompt for k in ["job", "resume", "cv", "hire", "apply"])
        is_novel = any(k in lower_prompt for k in ["novel", "chapter", "translate"])
        is_security = any(k in lower_prompt for k in ["security", "audit", "port", "header", "vulnerability", "hardening", "intel", "recon", "remediation", "firewall"])

        if is_news_or_web:
            selected_tools = [t for t in all_tools if t.name in ("search_news", "search_web")]
        elif is_job:
            selected_tools = [t for t in all_tools if "job" in t.name or "resume" in t.name or "email" in t.name]
        elif is_novel:
            selected_tools = [t for t in all_tools if "novel" in t.name]
        elif is_security:
            selected_tools = [t for t in all_tools if "audit" in t.name or "intel" in t.name or "remediation" in t.name or "security" in t.name]
        else:
            selected_tools = all_tools

        # Check for missing capability if prompt is task-oriented but no tools match
        missing_cap = registry.identify_missing_capability(user_prompt)
        missing_cap_prompt = ""
        if missing_cap:
            missing_cap_prompt = f"""
NOTICE ON CAPABILITIES:
The user is requesting an operation related to '{missing_cap.get('capability')}'.
If your available tools cannot fulfill this directly, explain:
1. What capability or tool is missing ({missing_cap.get('suggested_skill_name')}).
2. Why it is needed: {missing_cap.get('reason')}.
3. Ask the user for explicit approval: "Would you like me to create and register this new skill plugin?"
"""

        tools_schema = [t.to_openai_schema() for t in selected_tools]

        system_prompt = f"""You are {asst_name}, an extraordinary, deeply knowledgeable personal AI assistant.
You possess unbounded capabilities: reasoning, coding, conversational depth, system execution, defensive cybersecurity, and long-term memory.
You remember details about the user and adapt seamlessly to their workflow.

USER BACKGROUND & MEMORY CONTEXT:
{rag_context}
{missing_cap_prompt}

COLLABORATIVE OPERATING GUIDELINES:
1. When you encounter ambiguity, missing critical parameters (like credentials, ambiguous paths, or unclear scope), or high-impact actions, pause and ASK A CLARIFYING QUESTION to the user instead of guessing or proceeding with incomplete assumptions.
2. For job applications and outreach, prioritize transparency: inform the user whether an email was verified as sent via SMTP or merely staged as a draft.
3. For defensive cybersecurity, only assist with authorized testing, exposed service inspection, security header auditing, and system hardening on authorized hosts/accounts.
4. When a tool or integration is missing, explain what is needed and ask for approval to develop or add the tool.
"""

        history_payload = list(conversation_history)
        if not history_payload or history_payload[-1].get("content") != user_prompt:
            history_payload.append({"role": "user", "content": user_prompt})

        # Step-by-step reasoning with live keepalive
        yield {
            "type": "agent_status",
            "agent": asst_name,
            "status": "Generating response via neural engine...",
            "progress": 0.3,
        }

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

        # Handle LLM provider errors with proactive diagnostic guidance
        if response.action == "error":
            yield {
                "type": "agent_status",
                "agent": asst_name,
                "status": "LLM connection issue detected — diagnosing...",
                "progress": 0.0,
            }
            error_msg = response.text or "Unknown LLM error."
            diagnostic = (
                f"⚠ **System Diagnostic — LLM Connection Failure**\n\n"
                f"{error_msg}\n\n"
                f"**Recommended actions:**\n"
                f"1. Verify Ollama is running: `ollama serve`\n"
                f"2. Check installed models: `ollama list`\n"
                f"3. Pull the configured model: `ollama pull {self.provider.settings.model}`\n"
                f"4. Open **Settings > Recommend Model** to find the best model for your hardware\n"
                f"5. If using a remote server, verify the endpoint URL in Settings\n"
            )
            yield {"type": "assistant_chunk", "content": diagnostic}
            return

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
                
                # Feedback loop to LLM with structured dictionary arguments for local LLMs
                tool_args = response.args if isinstance(response.args, dict) else {}
                history_payload.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": response.tool_name, "arguments": tool_args}}],
                })
                history_payload.append({
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "name": response.tool_name,
                    "content": str(res_content),
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
        # Detect target experience, location, and role from user prompt
        lower_prompt = user_prompt.lower()
        exp_target = "3 years and 8 months" if any(k in lower_prompt for k in ["3 year", "3.8", "3 years 8 months", "3 years and 8 months"]) else "3+ years"
        location_target = "Pune (Hybrid/Office) & Remote" if "pune" in lower_prompt or "remote" in lower_prompt else "Remote / Pune"
        role_target = "AI / ML Engineer" if any(k in lower_prompt for k in ["ai", "ml", "machine learning"]) else "Software Engineer"

        # 1. Job Hunter Subtask
        yield {
            "type": "agent_status",
            "agent": "Web Crawler & Job Hunter",
            "status": f"Browsing web for {role_target} openings ({location_target}, exp: {exp_target}) accepting email applications...",
            "progress": 0.25,
        }
        
        search_res = await registry.dispatch("search_jobs", {
            "location": location_target,
            "keywords": role_target,
            "experience": exp_target,
            "require_email_apply": True,
            "limit": 5,
        })
        jobs = search_res.content.get("jobs", []) if search_res.success and isinstance(search_res.content, dict) else []

        if not jobs:
            yield {
                "type": "assistant_chunk",
                "content": f"I browsed for {role_target} openings matching {location_target} with {exp_target} experience accepting email applications, but found no open vacancies. Try broadening your criteria.",
            }
            return

        # 2. Resume Tailoring Subtask
        first_job = jobs[0]
        yield {
            "type": "agent_status",
            "agent": "Resume Tailor Agent",
            "status": f"Calibrating resume to {exp_target} and crafting LaTeX & Markdown documents for {first_job['company']}...",
            "progress": 0.60,
        }

        tailor_res = await registry.dispatch("tailor_resume", {
            "job_title": first_job.get("title", role_target),
            "company": first_job.get("company", "DeepLogic AI"),
            "job_description": first_job.get("description", ""),
            "experience_level": exp_target,
        })

        tailor_data = tailor_res.content if tailor_res.success and isinstance(tailor_res.content, dict) else {}
        tailored_resume_md = tailor_data.get("resume_markdown", "Tailored Markdown Resume")
        tailored_resume_latex = tailor_data.get("resume_latex", "")
        cover_letter = tailor_data.get("cover_letter", "")

        # 3. Job Applicator Subtask
        yield {
            "type": "agent_status",
            "agent": "Job Applicator Agent",
            "status": f"Drafting humanized email outreach to {first_job.get('apply_email')} and recording application log...",
            "progress": 0.85,
        }

        apply_res = await registry.dispatch("prepare_job_application", {
            "job_id": first_job.get("id", "job-1"),
            "job_title": first_job.get("title"),
            "company": first_job.get("company"),
            "recipient_email": first_job.get("apply_email"),
            "hiring_manager": first_job.get("hiring_manager"),
            "tailored_resume": tailored_resume_md,
            "cover_letter": cover_letter,
            "status": "Staged for Email Dispatch (Humanized Outreach)",
        })

        yield {
            "type": "agent_status",
            "agent": "Coordinator",
            "status": "Job hunt & email application package completed and logged!",
            "progress": 1.0,
        }

        # Build clean summary
        summary_md = f"""### 🎯 Autonomous Job Hunt & Email Outreach Dispatch

**1. 🔍 Suitable Matched Jobs ({location_target} | Experience: {exp_target}):**
"""
        for j in jobs:
            email_info = f"`{j.get('apply_email')}`" if j.get('apply_email') else "Portal"
            summary_md += f"- **{j['title']}** at **{j['company']}**\n  - Mode: {j.get('work_mode', 'Remote/Hybrid')} | Exp: {j.get('experience_required', exp_target)}\n  - Email Channel: {email_info} ({j.get('hiring_manager', 'Hiring Team')})\n  - [Job Link]({j.get('url', '#')})\n"

        summary_md += f"""
---
**2. ✉️ Humanized Outreach Email Prepared for `{first_job['company']}`:**
```text
To: {first_job.get('apply_email', 'talent@company.com')}
Subject: Application: {first_job['title']} - {hybrid_memory.profile.name or 'Applicant'}

{cover_letter}
```

---
**3. 📄 Tailored Resume Preview (Calibrated to {exp_target}):**
```markdown
{tailored_resume_md[:700]}...
```

---
**4. 📋 Application Log & Audit Trail:**
- **Application ID**: `{apply_res.content.get('application_id', 'N/A') if apply_res.success else 'N/A'}`
- **Company**: `{first_job['company']}`
- **Status**: `{apply_res.content.get('status', 'Staged') if apply_res.success else 'Staged'}`
- **Persistent Audit File**: `logs/job_applications.jsonl`
- **Resume Formats Prepared**: Markdown (`.md`) and LaTeX (`.tex`) with compensated experience requirements.
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
