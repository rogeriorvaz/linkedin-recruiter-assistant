import csv, os
from pathlib import Path
from tempfile import NamedTemporaryFile
from .recruiter import Recruiter, now_iso

FIELDS = ["profile_url","name","headline","current_role","current_company","location","relationship_status","score","reason","action","first_seen","last_seen","last_processed"]

class CsvStore:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self._ensure_file()
    def _ensure_file(self):
        if not self.path.exists() or self.path.stat().st_size == 0: self._write_rows([])
    def load_all(self):
        with self.path.open("r", encoding="utf-8", newline="") as f:
            return {r["profile_url"]: r for r in csv.DictReader(f) if r.get("profile_url")}
    def count(self): return len(self.load_all())
    def is_processed(self, url): return bool(self.load_all().get(url, {}).get("last_processed"))
    def save_recruiter(self, recruiter, action=None, processed=False):
        rows = self.load_all(); old = rows.get(recruiter.profile_url, {})
        recruiter.first_seen = old.get("first_seen") or recruiter.first_seen
        recruiter.last_seen = now_iso()
        if action: recruiter.action = action
        if processed: recruiter.last_processed = now_iso()
        rows[recruiter.profile_url] = {f: str(getattr(recruiter, f, "") or "") for f in FIELDS}
        self._write_rows(list(rows.values())); self._verify_saved(recruiter.profile_url)
    def record_action(self, recruiter, action, processed=True): self.save_recruiter(recruiter, action, processed)
    def _write_rows(self, rows):
        with NamedTemporaryFile("w", encoding="utf-8", newline="", dir=self.path.parent, delete=False) as tmp:
            w = csv.DictWriter(tmp, fieldnames=FIELDS); w.writeheader(); w.writerows(rows); tmp.flush(); os.fsync(tmp.fileno()); name = tmp.name
        os.replace(name, self.path)
    def _verify_saved(self, url):
        if url not in self.load_all(): raise IOError(f"CSV write verification failed for {url}")
