# tests/unit/test_multi_agent_skills.py

import pytest
from plugins.base.registry import registry
from plugins.system_skills.job_hunter.job_hunter_skill import JobHunterSkill
from plugins.system_skills.resume_tailor.resume_tailor_skill import ResumeTailorSkill
from plugins.system_skills.job_applicator.job_applicator_skill import JobApplicatorSkill
from plugins.system_skills.novel_agent.novel_skill import NovelAgentSkill
from plugins.system_skills.self_improvement.self_improvement_skill import SelfImprovementSkill


@pytest.mark.asyncio
async def test_job_hunter_skill():
    skill = JobHunterSkill()
    res = await skill.execute("search_jobs", {"location": "Pune", "keywords": "freshers software engineer", "limit": 2})
    assert res.success is True
    assert res.content["total"] >= 1
    assert "Persistent Systems" in str(res.content) or "Cybage" in str(res.content) or "Pune" in str(res.content)


@pytest.mark.asyncio
async def test_resume_tailor_skill():
    skill = ResumeTailorSkill()
    res = await skill.execute("tailor_resume", {"job_title": "AI Engineer", "company": "TechCorp"})
    assert res.success is True
    assert "AI Engineer" in res.content["resume_markdown"]
    assert "TechCorp" in res.content["cover_letter"]


@pytest.mark.asyncio
async def test_job_applicator_skill():
    skill = JobApplicatorSkill()
    res = await skill.execute("prepare_job_application", {"job_title": "AI Engineer", "company": "TechCorp"})
    assert res.success is True
    assert res.content["status"] == "Ready"


@pytest.mark.asyncio
async def test_novel_agent_skill():
    skill = NovelAgentSkill()
    res = await skill.execute("translate_and_edit_novel", {"raw_text": "The Cultivator sought the Dao above the Sect."})
    assert res.success is True
    assert "Immortal Cultivator" in res.content["output"]
    assert "Great Dao" in res.content["output"]


@pytest.mark.asyncio
async def test_skill_registry_dispatch():
    res = await registry.dispatch("search_jobs", {"location": "Pune", "keywords": "developer"})
    assert res.success is True
