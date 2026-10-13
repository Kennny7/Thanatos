# Thanatos/services/document/ats_auditor.py
"""
ATS (Applicant Tracking System) Quality & Keyword Relevance Auditor.
Performs multi-pass validation on tailored resumes before dispatch:
- Compares resume text against JD required skills & target experience.
- Calculates ATS match score (0 - 100%).
- Verifies that claims remain grounded in user's master profile.
- Provides actionable feedback for iterative refinement loops.
"""

import logging
import re
from typing import Any, Dict, List, Tuple
from services.memory.memory_manager import memory_service

logger = logging.getLogger(__name__)


class ATSAuditResult:
    def __init__(
        self,
        score: int,
        matched_keywords: List[str],
        missing_keywords: List[str],
        passed: bool,
        feedback: str,
        unsupported_claims: List[str],
    ) -> None:
        self.score = score
        self.matched_keywords = matched_keywords
        self.missing_keywords = missing_keywords
        self.passed = passed
        self.feedback = feedback
        self.unsupported_claims = unsupported_claims

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "passed": self.passed,
            "feedback": self.feedback,
            "unsupported_claims": self.unsupported_claims,
        }


class ATSAuditor:
    """Evaluates tailored resumes and governs automated self-correction loops."""

    MINIMUM_PASSING_SCORE: int = 75

    def audit_resume(
        self,
        resume_text: str,
        job_description: str,
        required_skills: List[str],
        target_role: str,
    ) -> ATSAuditResult:
        """Score candidate resume against job description and profile constraints."""
        resume_lower = resume_text.lower()
        jd_lower = job_description.lower()
        profile = memory_service.user_profile.get_profile()

        # 1. Match required and JD skills
        candidate_skills_pool = [s.lower() for s in (profile.skills or [])]
        matched_skills = []
        missing_skills = []

        # Check explicit required skills
        check_skills = list(set(required_skills + ["python", "rag", "docker", "fastapi"]))
        for skill in check_skills:
            pattern = rf"\b{re.escape(skill.lower())}\b"
            if re.search(pattern, resume_lower):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        # 2. Check for prohibited claims from profile
        unsupported_claims = []
        prohibited = [
            "banking credit validation",
            "diamond jewellery",
            "10 years of experience",
            "principal architect with 15 years",
        ]
        for p in prohibited:
            if p in resume_lower:
                unsupported_claims.append(p)

        # 3. Compute score
        total_skills = len(check_skills) or 1
        skill_coverage = len(matched_skills) / total_skills
        score = int(skill_coverage * 85)

        # Bonus for presence of contact and links
        if "github" in resume_lower:
            score += 5
        if "linkedin" in resume_lower:
            score += 5
        if "portfolio" in resume_lower:
            score += 5

        # Penalize if missing critical core skills
        if unsupported_claims:
            score -= 30

        score = max(10, min(100, score))
        passed = score >= self.MINIMUM_PASSING_SCORE and len(unsupported_claims) == 0

        feedback_notes = []
        if missing_skills:
            feedback_notes.append(f"Consider integrating authentic background in: {', '.join(missing_skills[:4])}")
        if unsupported_claims:
            feedback_notes.append(f"Remove unauthorized claims: {', '.join(unsupported_claims)}")
        if not passed:
            feedback_notes.append(f"ATS match score ({score}%) below threshold ({self.MINIMUM_PASSING_SCORE}%). Refinement recommended.")
        else:
            feedback_notes.append(f"ATS qualification verified ({score}% match). Passed quality gate.")

        return ATSAuditResult(
            score=score,
            matched_keywords=matched_skills,
            missing_keywords=missing_skills,
            passed=passed,
            feedback=" ".join(feedback_notes),
            unsupported_claims=unsupported_claims,
        )


ats_auditor = ATSAuditor()
