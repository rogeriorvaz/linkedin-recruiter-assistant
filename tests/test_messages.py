from linkedin_recruiter_assistant.messages import connection_message


def test_message_contains_name():
    assert "Hi Dominic" in connection_message("Dominic")
