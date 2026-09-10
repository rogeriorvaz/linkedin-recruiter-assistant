from .config import HEADLESS, MAX_RECRUITERS_PER_SESSION, MAX_RESULTS_PER_TERM, RECRUITERS_CSV, SEARCH_LOCATION, SEARCH_TERMS
from .csv_store import CsvStore
from .linkedin import LinkedInClient
from .messages import connection_message
from .recruiter import is_current_recruiter, Recruiter
from .scoring import score_recruiter


def main():
    store = CsvStore(RECRUITERS_CSV)
    print(f"Recruiter file: {RECRUITERS_CSV}")
    print(f"CSV exists: {'YES' if RECRUITERS_CSV.exists() else 'NO'}")
    print(f"CSV records: {store.count()}")
    print(f"Previously processed: {sum(1 for r in store.load_all().values() if r.get('last_processed'))}")
    print()

    client = LinkedInClient(headless=HEADLESS)
    try:
        client.start()
        print("Log into LinkedIn manually if required.")
        print("Complete any verification or security checks manually.")
        client.wait_for_manual_login()

        qualified = []
        seen = set(store.load_all())

        for term in SEARCH_TERMS:
            if len(qualified) >= MAX_RECRUITERS_PER_SESSION:
                break
            print(f"Searching: {term}")
            recruiters = client.search_results(term, SEARCH_LOCATION, MAX_RESULTS_PER_TERM)

            for recruiter in recruiters:
                if recruiter.profile_url in seen:
                    continue
                seen.add(recruiter.profile_url)

                # Save the search-card information immediately.
                store.save_recruiter(recruiter, action="discovered", processed=False)

                if not is_current_recruiter(recruiter.current_role, recruiter.current_company):
                    store.record_action(recruiter, "rejected_not_current_recruiter", processed=True)
                    continue

                recruiter.score, recruiter.reason = score_recruiter(recruiter)
                store.save_recruiter(recruiter, action="qualified", processed=False)

                if recruiter.relationship_status != "CONNECT_AVAILABLE":
                    store.record_action(recruiter, f"skipped_{recruiter.relationship_status.lower()}", processed=True)
                    continue

                qualified.append(recruiter)
                if len(qualified) >= MAX_RECRUITERS_PER_SESSION:
                    break

        print(f"Qualified recruiters for this session: {len(qualified)}")

        for recruiter in qualified:
            print("\\n" + "=" * 72)
            print(recruiter.name)
            print("=" * 72)
            print(f"Profile: {recruiter.profile_url}")
            print(f"Headline: {recruiter.headline}")
            print(f"Current role: {recruiter.current_role}")
            print(f"Company: {recruiter.current_company}")
            print(f"Location: {recruiter.location}")
            print(f"Relationship: {recruiter.relationship_status}")
            print(f"Score: {recruiter.score}")
            print(f"Reason: {recruiter.reason}")

            message = connection_message(recruiter.first_name)
            print("\\nSuggested message:\n")
            print(message)

            try:
                store.record_action(recruiter, "preparing_connection", processed=False)

                # Primary path: connect directly from the People search result card.
                clicked = client.click_connect_from_card(recruiter)
                if not clicked:
                    print("Connect button not available on search card. Opening profile as fallback...")
                    clicked = client.connect_from_profile_fallback(recruiter.profile_url)

                if not clicked:
                    print("Connect could not be found. Skipping recruiter.")
                    store.record_action(recruiter, "connect_not_available", processed=True)
                    continue

                print("✓ Connect clicked")
                if not client.prepare_connection_note(message):
                    print("Add a note/message field could not be prepared. Skipping recruiter.")
                    store.record_action(recruiter, "note_not_available", processed=True)
                    continue

                print("✓ Add a note opened")
                print("✓ Message entered")
                print("\\nReview the message and click SEND in LinkedIn.")
                input("Press ENTER here after sending the connection request...")
                store.record_action(recruiter, "connection_requested", processed=True)
                print(f"✓ Saved to CSV: {RECRUITERS_CSV}")

            except Exception as exc:
                print(f"Connection workflow failed: {exc}")
                store.record_action(recruiter, "connection_workflow_failed", processed=True)

        print(f"\\nFinished. CSV records: {store.count()}")
    finally:
        client.stop()
