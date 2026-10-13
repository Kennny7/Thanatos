# Multi-Agent Personas & Architecture

Thanatos employs an autonomous multi-agent model with decoupled identities, persistent memory partitions, and voice profiles.

---

## 1. Personas Overview

All persona profiles, names, and parameters are centrally stored and editable in [`config/agents.json`](file:///c:/Users/ACER/Desktop/Self-Projects/Thanatos/config/agents.json).

| Agent ID | Assigned Identity | Role | Voice Profile | Memory Partition |
| :--- | :--- | :--- | :--- | :--- |
| `site_engineer` | **Velma Sinclair** | Site Reliability & Systems Engineer | `en-US-JennyNeural` | `data/agent_memory/site_engineer/` |
| `secretary` | **Amelia Sterling** | Executive Secretary & Lifestyle Wingman | `en-US-AriaNeural` | `data/agent_memory/secretary/` |
| `butler` | **Alfred Vance** | Autonomous Social Butler & Strategist | `en-GB-RyanNeural` | `data/agent_memory/butler/` |

---

## 2. Decoupled Memory Architecture

To ensure data continuity, memories are keyed to immutable internal agent IDs (`site_engineer`, `secretary`, `butler`). Even if you rename an agent (e.g., from Velma to another name) or assign a new display title, the underlying memory partitions, character dossiers, telemetry logs, and shared memories remain intact.

### Memory Partitions:
1. **Private Partitions**:
   - `data/agent_memory/site_engineer/engineer_notes.json`: Telemetry snapshots, diagnostic benchmarks, performance patches.
   - `data/agent_memory/secretary/agenda.json`, `taste_profile.json`: Executive calendar, routines, workout goals, and taste preferences.
   - `data/agent_memory/butler/social_dossiers.json`: Contact dossiers, interpersonal dynamics, etiquette assessments.
2. **Shared Team Memory**:
   - Master User Profile: `data/profile_dir/profile.json`
   - Semantic Vector Store: `memory_store/`

---

## 3. CLI Commands & Interaction

In the Thanatos terminal (`thanatos`), interact with agents via the `/agents` command suite:

```bash
# View active agent table and identity status
thanatos> /agents

# Direct Private Message to a specific agent:
thanatos> /agents dm site_engineer Velma, check current CPU and memory consumption.
thanatos> /agents dm secretary Amelia, what is my focus schedule for tomorrow morning?
thanatos> /agents dm butler Alfred, prepare an introductory outreach draft for a VP of Engineering.

# Change active default persona:
thanatos> /agents set site_engineer   # Directly chat with Velma
thanatos> /agents set auto            # Intelligent multi-agent routing (default)

# Safely rename an agent without data loss:
thanatos> /agents rename site_engineer "Velma Vance"
```

---

## 4. Autonomous Job Hunting Suite (`/jobs`)

The job hunting suite scans openings from **LinkedIn**, **Naukri**, and direct corporate channels, extracting recruiter email addresses and gating applications via an ATS Auditor:

```bash
# Show job target criteria, active portals, and usage
thanatos> /jobs

# Search LinkedIn and Naukri without dispatching applications
thanatos> /jobs search AI/ML Engineer in Pune

# Run end-to-end autonomous tailoring, ATS quality check, and draft preview
thanatos> /jobs run AI/ML Engineer
```
