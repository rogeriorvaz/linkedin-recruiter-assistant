"""Local Ollama assisted classification for LinkedIn search results."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class AIRecruiterAssessment:
    profile_url: str
    is_recruiter: bool
    technology_recruiter: bool
    confidence: float
    reason: str

    @property
    def qualified(self) -> bool:
        return self.is_recruiter and self.technology_recruiter and self.confidence >= 0.65


class OllamaClassifier:
    """Small Ollama client using the local HTTP API, with no extra dependency."""

    def __init__(self, base_url: str, model: str, timeout: int = 120, enabled: bool = True):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.enabled = enabled
        self.available: bool | None = None

    def check_available(self) -> bool:
        if not self.enabled:
            self.available = False
            return False
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            models = {item.get("name") for item in data.get("models", [])}
            self.available = self.model in models or any(
                name and name.split(":", 1)[0] == self.model.split(":", 1)[0]
                for name in models
            )
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            self.available = False
        return bool(self.available)

    def classify(self, candidates: list[dict]) -> dict[str, AIRecruiterAssessment]:
        if not self.enabled or not candidates:
            return {}
        if self.available is False:
            return {}
        if self.available is None and not self.check_available():
            return {}

        schema = {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "profile_url": {"type": "string"},
                            "is_recruiter": {"type": "boolean"},
                            "technology_recruiter": {"type": "boolean"},
                            "confidence": {"type": "number"},
                            "reason": {"type": "string"},
                        },
                        "required": [
                            "profile_url",
                            "is_recruiter",
                            "technology_recruiter",
                            "confidence",
                            "reason",
                        ],
                    },
                }
            },
            "required": ["candidates"],
        }

        compact_candidates = [
            {
                "profile_url": item["profile_url"],
                "name": item.get("name", ""),
                "headline": item.get("headline", ""),
                "current_role": item.get("current_role", ""),
                "current_company": item.get("current_company", ""),
                "location": item.get("location", ""),
                "relationship_status": item.get("relationship_status", "UNKNOWN"),
                "search_term": item.get("search_term", ""),
                "card_text": item.get("card_text", "")[:1200],
            }
            for item in candidates
        ]

        prompt = """
You are classifying LinkedIn People search results for a UK technology professional who wants to connect with genuine technology recruiters.

Use semantic judgement. Do NOT require an exact title such as 'IT Recruiter'. Consider equivalent recruiting language such as talent acquisition, talent partner, tech talent, technical recruitment, resourcing, recruitment consultant, recruitment lead, recruitment director, and similar wording.

Classify a person as technology_recruiter=true when the available search-card evidence indicates that they recruit technology, IT, software, engineering, data, cloud, cyber, digital, infrastructure, or other technical talent.

The LinkedIn search term is evidence of why the person appeared, but do not treat the search term alone as proof that the person is a recruiter.

A generic headline such as 'Connecting Top Talent with Leading Tech Opportunities' may be recruitment evidence, but only mark it as a confident technology recruiter when the surrounding evidence supports that interpretation. Otherwise use a lower confidence score and explain why.

A recruiter remains a qualified prospect even when LinkedIn shows Pending, Connected, Follow or another relationship state. Relationship state determines the next action, not whether the person is a relevant recruiter.

Return one assessment for every candidate provided.
"""

        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.strip()},
                {
                    "role": "user",
                    "content": json.dumps(compact_candidates, ensure_ascii=False),
                },
            ],
            "stream": False,
            "think": False,
            "format": schema,
            "options": {"temperature": 0},
        }

        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload.get("message", {}).get("content", "")
            data = json.loads(content)
        except (OSError, urllib.error.URLError, json.JSONDecodeError, TimeoutError):
            return {}

        results: dict[str, AIRecruiterAssessment] = {}
        for item in data.get("candidates", []):
            try:
                assessment = AIRecruiterAssessment(
                    profile_url=item["profile_url"],
                    is_recruiter=bool(item["is_recruiter"]),
                    technology_recruiter=bool(item["technology_recruiter"]),
                    confidence=max(0.0, min(1.0, float(item["confidence"]))),
                    reason=str(item["reason"]).strip(),
                )
            except (KeyError, TypeError, ValueError):
                continue
            results[assessment.profile_url] = assessment

        return results
