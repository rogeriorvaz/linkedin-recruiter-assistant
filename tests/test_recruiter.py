from linkedin_recruiter_assistant.recruiter import is_current_recruiter


def test_current_recruiter():
    assert is_current_recruiter("Technology Recruiter")


def test_non_recruiter():
    assert not is_current_recruiter("Software Engineer")


def test_recommendation_text_is_not_role():
    assert not is_current_recruiter("phenomenal talent partner, focuses on the needs of the customer")
