import random

from .ai import OllamaClassifier
from .config import (
    HEADLESS,
    MAX_RECRUITERS_PER_SESSION,
    MAX_RESULTS_PER_TERM,
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT_SECONDS,
    RECRUITERS_CSV,
    SEARCH_DELAY_MAX_SECONDS,
    SEARCH_DELAY_MIN_SECONDS,
    SEARCH_LOCATION,
    SEARCH_TERMS,
)
from .csv_store import CsvStore
from .linkedin import LinkedInClient
from .messages import connection_message
from .recruiter import is_current_recruiter
from .scoring import score_recruiter


def main():
    store = CsvStore(RECRUITERS_CSV)
    print(f"Recruiter file: {RECRUITERS_CSV}")
    print(f"CSV exists: {'YES' if RECRUITERS_CSV.exists() else 'NO'}")
    print(f"CSV records: {store.count()}")
    print(f"Previously processed: {sum(1 for r in store.load_all().values() if r.get('last_processed'))}")
    print()

    ai = OllamaClassifier(
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        timeout=OLLAMA_TIMEOUT_SECONDS,
        enabled=OLLAMA_ENABLED,
    )
    if ai.check_available():
        print(f"Local AI: Ollama {OLLAMA_MODEL} available")
    else:
        print("Local AI: Ollama unavailable, using deterministic fallback")

    client = LinkedInClient(HEADLESS)
    try:
        client.start()
        print("Log into LinkedIn manually if required.")
        print("Complete any verification or security checks manually.")
        client.wait_for_manual_login()

        processed_count = 0
        qualified_count = 0
        session_seen = set()

        for index, term in enumerate(SEARCH_TERMS):
            if processed_count >= MAX_RECRUITERS_PER_SESSION:
                break

            if index > 0:
                delay = random.uniform(SEARCH_DELAY_MIN_SECONDS, SEARCH_DELAY_MAX_SECONDS)
                print(f"\nWaiting {delay:.1f} seconds before searching: {term}")
                client.page.wait_for_timeout(int(delay * 1000))

            print(f"\nSearching first page: {term}")
            client.open_people_search(term, SEARCH_LOCATION)
            cards = client.get_search_cards(MAX_RESULTS_PER_TERM)

            candidates = []
            parsed = []
            for card, profile_url in cards:
                if processed_count >= MAX_RECRUITERS_PER_SESSION:
                    break
                if profile_url in session_seen:
                    continue

                recruiter = client._parse_search_card(card)
                if not recruiter:
                    print("  Skipping result: could not parse search card")
                    continue

                session_seen.add(profile_url)
                parsed.append((card, recruiter))
                candidates.append({
                    "profile_url": recruiter.profile_url,
                    "name": recruiter.name,
                    "headline": recruiter.headline,
                    "current_role": recruiter.current_role,
                    "current_company": recruiter.current_company,
                    "location": recruiter.location,
                    "relationship_status": recruiter.relationship_status,
                    "search_term": term,
                    "card_text": card.inner_text(),
                })

            assessments = ai.classify(candidates)

            for card, recruiter in parsed:
                assessment = assessments.get(recruiter.profile_url)
                if assessment:
                    print(
                        f"\nAI: {recruiter.name} | recruiter={assessment.is_recruiter} "
                        f"technology={assessment.technology_recruiter} "
                        f"confidence={assessment.confidence:.2f}"
                    )
                    print(f"  Reason: {assessment.reason}")
                    is_qualified = assessment.qualified
                    recruiter.reason = f"AI: {assessment.reason}"
                    recruiter.score = round(assessment.confidence * 10)
                else:
                    is_qualified = is_current_recruiter(
                        recruiter.current_role,
                        recruiter.current_company,
                        recruiter.headline,
                    )
                    if is_qualified:
                        recruiter.score, recruiter.reason = score_recruiter(recruiter)
                    else:
                        recruiter.score = 0
                        recruiter.reason = "Deterministic classifier did not identify recruiter evidence"

                store.save_recruiter(recruiter, "discovered", False)

                if not is_qualified:
                    store.record_action(recruiter, "rejected_not_relevant_recruiter", True)
                    continue

                qualified_count += 1
                print(
                    f"✓ QUALIFIED RECRUITER: {recruiter.name} | "
                    f"{recruiter.relationship_status} | {recruiter.headline}"
                )

                # Qualification is independent from LinkedIn relationship state.
                # Pending, Connected and Follow-only candidates remain in the CSV.
                if recruiter.relationship_status != "CONNECT_AVAILABLE":
                    store.record_action(
                        recruiter,
                        f"qualified_skipped_{recruiter.relationship_status.lower()}",
                        True,
                    )
                    continue

                print("\n" + "=" * 72)
                print(recruiter.name)
                print("=" * 72)
                print(
                    f"Profile: {recruiter.profile_url}\n"
                    f"Headline: {recruiter.headline}\n"
                    f"Current role: {recruiter.current_role}\n"
                    f"Company: {recruiter.current_company}\n"
                    f"Location: {recruiter.location}\n"
                    f"Relationship: {recruiter.relationship_status}\n"
                    f"Score: {recruiter.score}\n"
                    f"Reason: {recruiter.reason}"
                )

                message = connection_message(recruiter.first_name)
                print("\nSuggested message:\n")
                print(message)
                store.record_action(recruiter, "preparing_connection", False)

                if not client.click_connect_on_card(recruiter.profile_url):
                    print("Connect button not available on search card. Opening profile as fallback...")
                    if not client.click_connect_profile_fallback(recruiter.profile_url):
                        store.record_action(recruiter, "connect_not_available", True)
                        continue

                print("✓ Connect clicked")
                if not client.prepare_connection_note(message):
                    store.record_action(recruiter, "note_not_available", True)
                    continue

                print("✓ Add a note opened")
                print("✓ Message entered")
                print("\nReview the message and click SEND in LinkedIn.")
                input("Press ENTER here after sending the connection request...")
                store.record_action(recruiter, "connection_requested", True)
                processed_count += 1
                print(f"✓ Saved to CSV: {RECRUITERS_CSV}")

        print(f"\nQualified recruiters found this session: {qualified_count}")
        print(f"Connection requests manually confirmed this session: {processed_count}")
        print(f"Finished. CSV records: {store.count()}")
    finally:
        client.stop()
