from linkedin_recruiter_assistant.csv_store import CsvStore
from linkedin_recruiter_assistant.recruiter import Recruiter

def test_csv_persists(tmp_path):
    s=CsvStore(tmp_path/"recruiters.csv"); r=Recruiter("Test","https://www.linkedin.com/in/test/"); s.save_recruiter(r); assert s.count()==1; s.record_action(r,"connection_requested",True); assert s.load_all()[r.profile_url]["last_processed"]
