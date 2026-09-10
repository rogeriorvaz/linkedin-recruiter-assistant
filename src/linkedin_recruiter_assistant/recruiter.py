from dataclasses import dataclass, field
from datetime import datetime, timezone
import re


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalise(value: str) -> str:
    return re.sub(r"\\s+", " ", (value or "").strip().lower())


def contains_any(text: str, terms: list[str]) -> bool:
    value = normalise(text)
    return any(term in value for term in terms)


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
    action: str = "discovered"
    first_seen: str = field(default_factory=now_iso)
    last_seen: str = field(default_factory=now_iso)
    last_processed: str = ""

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name else "there"


def is_current_recruiter(current_role: str, current_company: str = "") -> bool:
    # Only the explicitly extracted CURRENT role is considered.
    # Do not infer current employment from recommendations, About text, or page-wide text.
    role = normalise(current_role)
    if not role:
        return False
    from .config import CURRENT_RECRUITER_TERMS, NEGATIVE_CURRENT_TERMS
    if contains_any(role, NEGATIVE_CURRENT_TERMS):
        return False
    return contains_any(role, CURRENT_RECRUITER_TERMS)
