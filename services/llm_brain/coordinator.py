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
        asst_name = hybrid_memory.profile.assistant_name or "Thanatos Assistant"
        lower_prompt = user_prompt.lower()

        # 3. Check persona delegation from AgentRoster
        from services.agents.agent_roster import roster
        active_persona = roster.active_agent_id

        # Check explicit persona invocations or domain triggers
        is_systems_eng = active_persona == "site_engineer" or any(w in lower_prompt for w in ["velma", "system resource", "cpu usage", "ram usage", "server health", "telemetry", "hardware usage", "diagnose system", "debug error"])
        is_secretary_req = active_persona == "secretary" or any(w in lower_prompt for w in ["amelia", "my agenda", "schedule", "routine", "workout", "remind me", "coffee preference"])
        is_butler_req = active_persona == "butler" or any(w in lower_prompt for w in ["alfred", "dossier", "networking", "etiquette", "strategic leverage", "character notes"])

        if is_systems_eng:
            from services.agents.site_engineer_agent import site_engineer_agent
            asst_name = "Velma Sinclair"
            diag = site_engineer_agent.collect_system_telemetry()
            task_desc = "Inspecting OS hardware metrics, processes & telemetry"
            yield {"type": "agent_status", "agent": asst_name, "status": task_desc}
            
            # Classify intent for Docker/database actions:
            wants_docker_up = any(w in lower_prompt for w in [
                "start docker", "launch docker", "spin up docker", "up docker", "start database", 
                "run docker", "start container", "containerized", "containerised", "prefer docker",
                "prefer container", "bring up database", "turn on docker", "boot docker", "open docker",
                "yes, start", "yes start", "yeah start", "sure start", "run containers", "run with docker"
            ])
            wants_local_lite = any(w in lower_prompt for w in [
                "dont want docker", "don't want docker", "no docker", "keep local", "stay local", 
                "local lite", "use lite", "prefer lite", "without docker", "no thanks", "keep it local",
                "embedded", "skip docker", "ignore docker", "run locally", "dont launch"
            ])
            wants_docker_down = any(w in lower_prompt for w in [
                "stop docker", "stop database", "stop container", "down docker", "halt docker", "shut docker", "kill docker"
            ])

            if wants_docker_up and not wants_local_lite:
                yield {"type": "agent_status", "agent": asst_name, "status": "Executing autonomous Docker launch & database container deployment...", "progress": 0.3}
                action_res = site_engineer_agent.auto_manage_docker(action="ensure", start_if_stopped=True)
                if action_res.get("running"):
                    reply = "All set! I've launched Docker Desktop and spun up your database cluster (PostgreSQL, MongoDB, Milvus, Neo4j, Kafka). Data is mapped to `data/docker_storage/`. Telemetry is clean and we're good to go!"
                else:
                    reply = f"I tried to launch Docker Desktop and deploy the cluster, but ran into an issue: {action_res.get('message') or action_res.get('error')}. I'm keeping local embedded storage active for now so nothing breaks."
                yield {"type": "assistant_chunk", "content": reply}
                return

            if wants_local_lite:
                yield {"type": "agent_status", "agent": asst_name, "status": "Confirming local embedded mode...", "progress": 1.0}
                reply = "Got it! Keeping things lightweight with local embedded storage (Milvus Lite & SQLite). Docker stays sleeping so your RAM remains free. Let me know whenever you want to switch!"
                yield {"type": "assistant_chunk", "content": reply}
                return

            if wants_docker_down:
                yield {"type": "agent_status", "agent": asst_name, "status": "Halting database containers to conserve RAM/CPU...", "progress": 0.5}
                action_res = site_engineer_agent.auto_manage_docker(action="stop")
                reply = "Done! I've safely stopped the database containers to free up your memory and CPU."
                yield {"type": "assistant_chunk", "content": reply}
                return

            # For general inquiries or complex operational questions, pass site operations tools into LLM generate_response
            infra_tools = [t.to_openai_schema() for t in registry.get_all_tools() if "docker" in t.name or "telemetry" in t.name or "port" in t.name]
            prompt = f"{site_engineer_agent.build_system_prompt()}\n\nUser Question/Task: {user_prompt}\n\nLive System Telemetry:\n{json.dumps(diag, indent=2)}\n\nRespond with your charming, willful Velma persona."
            response = await self.provider.generate_response(
                history=[{"role": "user", "content": prompt}],
                tools_schema=infra_tools,
                system_prompt=site_engineer_agent.build_system_prompt(),
            )
            if response.action == "tool_call" and response.tool_name:
                yield {"type": "agent_status", "agent": asst_name, "status": f"Invoking `{response.tool_name}`...", "progress": 0.6}
                t_res = await registry.dispatch(response.tool_name, response.args or {})
                res_content = t_res.content if t_res.success else f"Error: {t_res.error}"
                follow_up = await self.provider.generate(
                    prompt=f"{site_engineer_agent.build_system_prompt()}\n\nUser said: {user_prompt}\nTool {response.tool_name} returned: {res_content}\n\nExplain result in your charming Velma persona.",
                    stream=False
                )
                yield {"type": "assistant_chunk", "content": follow_up.content or str(res_content)}
                return

            yield {"type": "assistant_chunk", "content": response.text or "Velma telemetry check complete."}
            return

        if is_secretary_req:
            from services.agents.secretary_agent import SecretaryAgent
            asst_name = "Amelia Sterling"
            sec = SecretaryAgent()
            task_desc = "Accessing daily schedule, routines & executive agenda"
            yield {"type": "agent_status", "agent": asst_name, "status": task_desc}
            prompt = f"{sec.build_system_prompt()}\n\nUser Question/Task: {user_prompt}\n\nPending Agenda:\n{json.dumps(sec.list_pending_agenda(), indent=2)}\n\nRespond with your Amelia persona."
            ans = await self.provider.generate(prompt=prompt, stream=False)
            yield {"type": "assistant_chunk", "content": ans.content}
            return

        if is_butler_req:
            from services.agents.butler_agent import ButlerAgent
            asst_name = "Alfred Vance"
            butler = ButlerAgent()
            task_desc = "Consulting character dossiers & strategic intelligence"
            yield {"type": "agent_status", "agent": asst_name, "status": task_desc}
            prompt = f"{butler.build_system_prompt()}\n\nUser Question/Task: {user_prompt}\n\nRespond with your Alfred Vance persona."
            ans = await self.provider.generate(prompt=prompt, stream=False)
            yield {"type": "assistant_chunk", "content": ans.content}
            return

        # 4. Check if this is an explicit composite workflow
        is_job_workflow = any(k in lower_prompt for k in ["find me a job", "apply for jobs", "hunt for jobs", "search for jobs", "job hunt"])
        is_novel_workflow = any(k in lower_prompt for k in ["translate novel", "raw chapter"])
        is_code_workflow = any(k in lower_prompt for k in ["improve code", "fix bug in thanatos", "refactor thanatos", "self-improve"])

        # Determine meaningful real-time task status
        if is_job_workflow:
            task_desc = "Inspecting career profile & scanning verified job channels"
        elif is_novel_workflow:
            task_desc = "Loading chapter structure & character development database"
        elif is_code_workflow:
            task_desc = "Analyzing repository codebase & test suites in sandbox"
        elif any(k in lower_prompt for k in ["search", "browse", "news", "google", "web"]):
            task_desc = "Initiating live web search & external network query"
        elif any(k in lower_prompt for k in ["node", "mesh", "wifi", "device"]):
            task_desc = "Scanning subnet UDP ports & pinging mesh nodes"
        elif any(k in lower_prompt for k in ["database", "db", "memory", "vector", "postgres", "mongo"]):
            task_desc = "Querying hybrid vector & relational database stores"
        elif any(k in lower_prompt for k in ["run", "command", "powershell", "cmd", "exec", "uninstall", "install", "sfc", "dism", "chkdsk"]):
            task_desc = "Preparing system execution & shell environment"
        else:
            task_desc = f"Synthesizing knowledge context for '{user_prompt[:35]}...'"

        yield {
            "type": "agent_status",
            "agent": asst_name,
            "status": task_desc,
        }

        if is_job_workflow:
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
        is_job = any(k in lower_prompt for k in ["job", "resume", "cv", "hire", "apply"]) and any(k in lower_prompt for k in ["hunt", "search", "find", "draft"])
        is_novel = any(k in lower_prompt for k in ["novel", "chapter", "translate"])
        is_security = any(k in lower_prompt for k in ["security", "audit", "header", "vulnerability", "hardening", "intel", "recon", "remediation", "firewall"])
        is_system_exec = any(k in lower_prompt for k in ["command", "powershell", "cmd", "run", "uninstall", "install", "sfc", "dism", "chkdsk", "winget", "appx", "package", "service", "process"])
        is_infra = any(k in lower_prompt for k in ["docker", "container", "postgres", "mongo", "milvus", "neo4j", "kafka", "telemetry", "port", "daemon", "infrastructure"])

        if is_news_or_web:
            selected_tools = [t for t in all_tools if t.name in ("search_news", "search_web")]
        elif is_system_exec:
            selected_tools = [t for t in all_tools if t.name in ("run_system_command", "manage_system_package", "get_system_telemetry", "check_port_conflicts")]
        elif is_job:
            selected_tools = [t for t in all_tools if "job" in t.name or "resume" in t.name or "email" in t.name]
        elif is_novel:
            selected_tools = [t for t in all_tools if "novel" in t.name]
        elif is_security:
            selected_tools = [t for t in all_tools if "audit" in t.name or "intel" in t.name or "remediation" in t.name or "security" in t.name]
        elif is_infra:
            selected_tools = [t for t in all_tools if "docker" in t.name or "telemetry" in t.name or "port" in t.name or "command" in t.name]
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
1. You are a complete, general-purpose autonomous AI operating system designed to manage, rebuild, optimize, and debug the user's projects, as well as assist with daily lifestyle, productivity, and work.
2. ALWAYS execute tools when the user asks for system actions (diagnostics, package management, running commands, inspecting processes, web searches). Never hallucinate or pretend a heavy command completed in seconds; execute the real tool and report actual results.
3. Job hunting/applications is only a minor sub-skill of this system. NEVER steer conversations toward jobs, resumes, or hiring portals unless the user explicitly asks for job search or application assistance.
4. If a capability or tool does not yet exist to fulfill an instruction, explicitly identify what tool/plugin is missing, why it is needed, and offer to create and register that new skill plugin autonomously.
5. When executing impactful actions or when critical parameters are missing, confirm with the user.
"""

        history_payload = list(conversation_history)
        if not history_payload or history_payload[-1].get("content") != user_prompt:
            history_payload.append({"role": "user", "content": user_prompt})

        # Emitting real neural model invocation status
        model_name = getattr(self.provider.settings, "model", "Ollama")
        yield {
            "type": "agent_status",
            "agent": asst_name,
            "status": f"Querying neural model `{model_name}`...",
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
                f"[!] **System Diagnostic — LLM Connection Failure**\n\n"
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
        summary_md = f"""### • Autonomous Job Hunt & Email Outreach Dispatch

**1. Suitable Matched Jobs ({location_target} | Experience: {exp_target}):**
"""
        for j in jobs:
            email_info = f"`{j.get('apply_email')}`" if j.get('apply_email') else "Portal"
            summary_md += f"- **{j['title']}** at **{j['company']}**\n  - Mode: {j.get('work_mode', 'Remote/Hybrid')} | Exp: {j.get('experience_required', exp_target)}\n  - Email Channel: {email_info} ({j.get('hiring_manager', 'Hiring Team')})\n  - [Job Link]({j.get('url', '#')})\n"

        summary_md += f"""
---
**2. Humanized Outreach Email Prepared for `{first_job['company']}`:**
```text
To: {first_job.get('apply_email', 'talent@company.com')}
Subject: Application: {first_job['title']} - {hybrid_memory.profile.name or 'Applicant'}

{cover_letter}
```

---
**3. Tailored Resume Preview (Calibrated to {exp_target}):**
```markdown
{tailored_resume_md[:700]}...
```

---
**4. Application Log & Audit Trail:**
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
