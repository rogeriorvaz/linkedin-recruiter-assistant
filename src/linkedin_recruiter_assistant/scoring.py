"""Recruiter relevance scoring."""

from .config import (
    CURRENT_RECRUITER_TERMS,
    NEGATIVE_CURRENT_TERMS,
    RECRUITMENT_COMPANY_TERMS,
    SENIOR_TERMS,
    TECHNOLOGY_TERMS,
)
from .recruiter import Recruiter, contains_any, normalise


def score_recruiter(recruiter: Recruiter) -> int:
    score = 0
    reasons = []

    role = normalise(recruiter.current_role)
    headline = normalise(recruiter.headline)
    company = normalise(recruiter.current_company)
    location = normalise(recruiter.location)

    if contains_any(role, CURRENT_RECRUITER_TERMS):
        score += 5
        reasons.append("current recruiter role")

    if contains_any(role + " " + headline, TECHNOLOGY_TERMS):
        score += 3
        reasons.append("technology focus")

    if any(
        term in location
        for term in (
            "uk",
            "united kingdom",
            "england",
            "scotland",
            "wales",
            "northern ireland",
        )
    ):
        score += 2
        reasons.append("UK location")

    if contains_any(company, RECRUITMENT_COMPANY_TERMS):
        score += 2
        reasons.append("recruitment company")

    if contains_any(role, SENIOR_TERMS):
        score += 1
        reasons.append("senior recruiter")

    if contains_any(role, NEGATIVE_CURRENT_TERMS):
        score -= 10
        reasons.append("current role appears unrelated")

    recruiter.score = score
    recruiter.reason = ", ".join(reasons)

    return score
