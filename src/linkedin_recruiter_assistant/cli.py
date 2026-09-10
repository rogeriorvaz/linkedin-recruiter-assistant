import random

from .config import (HEADLESS, MAX_RECRUITERS_PER_SESSION, MAX_RESULTS_PER_TERM, RECRUITERS_CSV, SEARCH_LOCATION, SEARCH_TERMS, SEARCH_DELAY_MIN_SECONDS, SEARCH_DELAY_MAX_SECONDS)
from .csv_store import CsvStore
from .linkedin import LinkedInClient
from .messages import connection_message
from .recruiter import is_current_recruiter
from .scoring import score_recruiter

def main():
    store=CsvStore(RECRUITERS_CSV)
    print(f"Recruiter file: {RECRUITERS_CSV}")
    print(f"CSV exists: {'YES' if RECRUITERS_CSV.exists() else 'NO'}")
    print(f"CSV records: {store.count()}")
    print(f"Previously processed: {sum(1 for r in store.load_all().values() if r.get('last_processed'))}")
    print()
    client=LinkedInClient(HEADLESS)
    try:
        client.start(); print("Log into LinkedIn manually if required."); print("Complete any verification or security checks manually."); client.wait_for_manual_login()
        processed_count=0; seen=set(store.load_all())
        for index, term in enumerate(SEARCH_TERMS):
            if processed_count>=MAX_RECRUITERS_PER_SESSION: break
            # Random pause between search terms, but not before the first search.
            if index > 0:
                delay = random.uniform(
                    SEARCH_DELAY_MIN_SECONDS,
                    SEARCH_DELAY_MAX_SECONDS,
                )

                print(
                    f"\nWaiting {delay:.1f} seconds before searching: {term}"
                )

                client.page.wait_for_timeout(int(delay * 1000))            
            print(f"Searching: {term}")
            client.open_people_search(term, SEARCH_LOCATION)
            cards=client.get_search_cards(MAX_RESULTS_PER_TERM)
            for card, profile_url in cards:
                if processed_count>=MAX_RECRUITERS_PER_SESSION: break
                recruiter=client._parse_search_card(card)
                if not recruiter:
                    print("  Skipping result: could not parse search card")
                    continue
                if recruiter.profile_url in seen: continue
                seen.add(recruiter.profile_url)
                store.save_recruiter(recruiter, "discovered", False)
                if not is_current_recruiter(recruiter.current_role,recruiter.current_company,recruiter.headline):
                    store.record_action(recruiter,"rejected_not_current_recruiter",True); continue
                recruiter.score,recruiter.reason=score_recruiter(recruiter); store.save_recruiter(recruiter,"qualified",False)
                if recruiter.relationship_status!="CONNECT_AVAILABLE":
                    store.record_action(recruiter,f"skipped_{recruiter.relationship_status.lower()}",True); continue
                print("\n"+"="*72); print(recruiter.name); print("="*72)
                print(f"Profile: {recruiter.profile_url}\nHeadline: {recruiter.headline}\nCurrent role: {recruiter.current_role}\nCompany: {recruiter.current_company}\nLocation: {recruiter.location}\nRelationship: {recruiter.relationship_status}\nScore: {recruiter.score}\nReason: {recruiter.reason}")
                message=connection_message(recruiter.first_name); print("\nSuggested message:\n"); print(message)
                store.record_action(recruiter,"preparing_connection",False)
                # We are still on the same search page, so click this result's Connect button now.
                if not client.click_connect_on_card(recruiter.profile_url):
                    print("Connect button not available on search card. Opening profile as fallback...")
                    if not client.click_connect_profile_fallback(recruiter.profile_url):
                        store.record_action(recruiter,"connect_not_available",True); continue
                print("✓ Connect clicked")
                if not client.prepare_connection_note(message):
                    store.record_action(recruiter,"note_not_available",True); continue
                print("✓ Add a note opened"); print("✓ Message entered"); print("\nReview the message and click SEND in LinkedIn.")
                input("Press ENTER here after sending the connection request...")
                store.record_action(recruiter,"connection_requested",True); processed_count+=1
                print(f"✓ Saved to CSV: {RECRUITERS_CSV}")
        print(f"\nQualified/processed recruiters this session: {processed_count}"); print(f"Finished. CSV records: {store.count()}")
    finally: client.stop()
