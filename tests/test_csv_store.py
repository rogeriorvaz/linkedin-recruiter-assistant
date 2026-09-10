from linkedin_recruiter_assistant.csv_store import CsvStore
from linkedin_recruiter_assistant.recruiter import Recruiter


def test_csv_persists_recruiter(tmp_path):
    store = CsvStore(tmp_path / "recruiters.csv")
    recruiter = Recruiter(name="Test Recruiter", profile_url="https://www.linkedin.com/in/test/")
    store.save_recruiter(recruiter)
    assert store.count() == 1
    store.record_action(recruiter, "connection_requested", processed=True)
    row = store.load_all()[recruiter.profile_url]
    assert row["action"] == "connection_requested"
    assert row["last_processed"]
