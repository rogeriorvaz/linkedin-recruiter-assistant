"""CSV persistence for recruiter records.

CSV is deliberately used instead of a database because this project is
small, single-user, and benefits from a human-readable/editable data file.
"""

import csv
from datetime import datetime
from pathlib import Path

from .recruiter import Recruiter


FIELDNAMES = [
    "profile_url",
    "name",
    "headline",
    "current_role",
    "current_company",
    "location",
    "relationship_status",
    "score",
    "reason",
    "action",
    "first_seen",
    "last_seen",
    "last_processed",
]


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class RecruiterStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self) -> None:
        if self.path.exists():
            return

        with self.path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES,
            )
            writer.writeheader()

    def load_all(self) -> dict[str, Recruiter]:
        recruiters = {}

        with self.path.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                url = (row.get("profile_url") or "").strip()

                if not url:
                    continue

                recruiters[url] = Recruiter(
                    name=row.get("name", ""),
                    profile_url=url,
                    headline=row.get("headline", ""),
                    current_role=row.get("current_role", ""),
                    current_company=row.get("current_company", ""),
                    location=row.get("location", ""),
                    relationship_status=row.get(
                        "relationship_status",
                        "UNKNOWN",
                    ),
                    score=int(row.get("score") or 0),
                    reason=row.get("reason", ""),
                    action=row.get("action", ""),
                    first_seen=row.get("first_seen", ""),
                    last_seen=row.get("last_seen", ""),
                    last_processed=row.get(
                        "last_processed",
                        "",
                    ),
                )

        return recruiters

    def get(self, profile_url: str) -> Recruiter | None:
        return self.load_all().get(profile_url)

    def save(self, recruiter: Recruiter) -> None:
        records = self.load_all()
        existing = records.get(recruiter.profile_url)

        timestamp = now()

        if not recruiter.first_seen:
            recruiter.first_seen = (
                existing.first_seen
                if existing and existing.first_seen
                else timestamp
            )

        recruiter.last_seen = timestamp

        records[recruiter.profile_url] = recruiter

        self._write(records.values())

    def record_action(
        self,
        recruiter: Recruiter,
        action: str,
    ) -> None:
        records = self.load_all()

        existing = records.get(recruiter.profile_url)

        if existing:
            recruiter.first_seen = existing.first_seen

        recruiter.action = action
        recruiter.last_processed = now()
        recruiter.last_seen = now()

        records[recruiter.profile_url] = recruiter

        self._write(records.values())

    def is_processed(self, profile_url: str) -> bool:
        recruiter = self.get(profile_url)

        if not recruiter:
            return False

        return recruiter.action in {
            "manually_connected",
            "skipped",
            "rejected",
            "pending",
            "connected",
        }

    def processed_urls(self) -> set[str]:
        records = self.load_all()

        return {
            url
            for url, recruiter in records.items()
            if recruiter.action in {
                "manually_connected",
                "skipped",
                "rejected",
                "pending",
                "connected",
            }
        }

    def _write(self, recruiters) -> None:
        temporary = self.path.with_suffix(".tmp")

        with temporary.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=FIELDNAMES,
            )

            writer.writeheader()

            for recruiter in sorted(
                recruiters,
                key=lambda item: (
                    item.last_seen,
                    item.name.lower(),
                ),
            ):
                writer.writerow(
                    {
                        field: getattr(
                            recruiter,
                            field,
                            "",
                        )
                        for field in FIELDNAMES
                    }
                )

        temporary.replace(self.path)
