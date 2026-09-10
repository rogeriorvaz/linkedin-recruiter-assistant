import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from .recruiter import Recruiter, now_iso

FIELDS = [
    "profile_url", "name", "headline", "current_role", "current_company", "location",
    "relationship_status", "score", "reason", "action", "first_seen", "last_seen", "last_processed",
]


class CsvStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists() or self.path.stat().st_size == 0:
            self._write_rows([])

    def load_all(self) -> dict[str, dict]:
        with self.path.open("r", encoding="utf-8", newline="") as f:
            return {row["profile_url"]: row for row in csv.DictReader(f) if row.get("profile_url")}

    def count(self) -> int:
        return len(self.load_all())

    def is_processed(self, profile_url: str) -> bool:
        row = self.load_all().get(profile_url)
        return bool(row and row.get("last_processed"))

    def save_recruiter(self, recruiter: Recruiter, action: str | None = None, processed: bool = False):
        rows = self.load_all()
        existing = rows.get(recruiter.profile_url, {})
        recruiter.first_seen = existing.get("first_seen") or recruiter.first_seen
        recruiter.last_seen = now_iso()
        if action:
            recruiter.action = action
        if processed:
            recruiter.last_processed = now_iso()
        rows[recruiter.profile_url] = {field: str(getattr(recruiter, field, "") or "") for field in FIELDS}
        self._write_rows(list(rows.values()))
        self._verify_saved(recruiter.profile_url)

    def record_action(self, recruiter: Recruiter, action: str, processed: bool = True):
        self.save_recruiter(recruiter, action=action, processed=processed)

    def _write_rows(self, rows: list[dict]):
        with NamedTemporaryFile("w", encoding="utf-8", newline="", dir=self.path.parent, delete=False) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_name = tmp.name
        os.replace(temp_name, self.path)

    def _verify_saved(self, profile_url: str):
        if profile_url not in self.load_all():
            raise IOError(f"CSV write verification failed for {profile_url}")
