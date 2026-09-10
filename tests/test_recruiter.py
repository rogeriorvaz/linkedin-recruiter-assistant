from linkedin_recruiter_assistant.recruiter import is_current_recruiter

def test_current_role(): assert is_current_recruiter("Technical Recruiter","Index")
def test_headline_can_qualify_when_current_line_missing(): assert is_current_recruiter("","", "Head of recruitment - Tech & IT")
def test_delivery_manager_not_recruiter(): assert not is_current_recruiter("Delivery Manager","Adecco","IT and Technology Recruitment")
