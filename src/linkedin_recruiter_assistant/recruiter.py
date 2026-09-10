"""Recruiter domain model and classification helpers."""

from dataclasses import dataclass

from .config import CURRENT_RECRUITER_TERMS, NEGATIVE_CURRENT_TERMS


@dataclass
class Recruiter:
    name: str
    profile_url: str
    headline: str = ""
    current_role: str = ""
    current_company: str = ""
    location: str = ""
    relationship_status: str = "UNKNOWN"
    score: int = 0
    reason: str = ""
    action: str = ""
    first_seen: str = ""
    last_seen: str = ""
    last_processed: str = ""


def normalise(text: str) -> str:
    return " ".join((text or "").lower().split())


def contains_any(text: str, terms: list[str]) -> bool:
    value = normalise(text)
    return any(term.lower() in value for term in terms)


def is_current_recruiter(recruiter: Recruiter) -> bool:
    role = normalise(recruiter.current_role)

    if not role:
        return False

    if not contains_any(role, CURRENT_RECRUITER_TERMS):
        return False

    if contains_any(role, NEGATIVE_CURRENT_TERMS):
        return False

    return True
