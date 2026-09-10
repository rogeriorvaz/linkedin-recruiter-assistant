from .config import (
    RECRUITMENT_COMPANY_TERMS,
    SENIOR_TERMS,
    TECHNOLOGY_TERMS,
)
from .recruiter import Recruiter, contains_any, normalise, is_current_recruiter


def score_recruiter(recruiter: Recruiter) -> tuple[int, str]:
    score = 0
    reasons = []

    if is_current_recruiter(recruiter.current_role, recruiter.current_company):
        score += 5
        reasons.append("current recruiter role")

    combined = f"{recruiter.current_role} {recruiter.headline} {recruiter.current_company}"
    if contains_any(combined, TECHNOLOGY_TERMS):
        score += 3
        reasons.append("technology focus")

    if any(x in normalise(recruiter.location) for x in ["united kingdom", "uk", "england", "scotland", "wales", "northern ireland"]):
        score += 2
        reasons.append("UK location")

    if contains_any(recruiter.current_company, RECRUITMENT_COMPANY_TERMS):
        score += 2
        reasons.append("recruitment company")

    if contains_any(recruiter.current_role, SENIOR_TERMS):
        score += 1
        reasons.append("senior recruiter")

    return score, ", ".join(reasons)
