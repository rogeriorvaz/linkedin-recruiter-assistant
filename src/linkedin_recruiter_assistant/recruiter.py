from dataclasses import dataclass, field
from datetime import datetime, timezone
import re

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def normalise(value):
    return re.sub(r"\\s+", " ", (value or "").strip().lower())

def contains_any(text, terms):
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
    def first_name(self):
        return self.name.split()[0] if self.name else "there"

def is_current_recruiter(current_role, current_company="", headline=""):
    from .config import CURRENT_RECRUITER_TERMS, NEGATIVE_CURRENT_TERMS
    role = normalise(current_role)
    headline = normalise(headline)
    if role and contains_any(role, NEGATIVE_CURRENT_TERMS):
        return False
    # Prefer explicit Current: evidence. If LinkedIn does not expose it,
    # allow a clearly recruiter-focused headline as search-page evidence.
    return contains_any(role, CURRENT_RECRUITER_TERMS) or contains_any(headline, CURRENT_RECRUITER_TERMS)
