"""Interactive command-line workflow."""

from playwright.sync_api import sync_playwright

from .config import (
    HEADLESS,
    MAX_DELAY_SECONDS,
    MAX_RECRUITERS_PER_SESSION,
    MIN_DELAY_SECONDS,
    RECRUITERS_CSV,
    SEARCH_TERMS,
)
from .csv_store import RecruiterStore
from .linkedin import (
    collect_search_results,
    inspect_profile,
    login,
    random_delay,
)
from .messages import create_connection_message
from .recruiter import Recruiter, is_current_recruiter
from .scoring import score_recruiter


def display_recruiter(
    recruiter: Recruiter,
) -> None:
    print()
    print("=" * 72)
    print(recruiter.name)
    print("=" * 72)
    print(f"Profile: {recruiter.profile_url}")
    print(f"Headline: {recruiter.headline}")
    print(f"Current role: {recruiter.current_role}")
    print(f"Company: {recruiter.current_company}")
    print(f"Location: {recruiter.location}")
    print(
        f"Relationship: "
        f"{recruiter.relationship_status}"
    )
    print(f"Score: {recruiter.score}")
    print(f"Reason: {recruiter.reason}")
    print()
    print("Suggested message:")
    print(create_connection_message(recruiter.name))
    print()
    print("C = manually Connect")
    print("S = skip")
    print("M = manual review")
    print("Q = quit")


def main() -> None:
    store = RecruiterStore(RECRUITERS_CSV)

    existing = store.load_all()

    print("=" * 72)
    print("LinkedIn UK IT Recruiter Assistant")
    print("=" * 72)
    print(f"Recruiter file: {RECRUITERS_CSV}")
    print(f"Recruiters recorded: {len(existing)}")
    print(
        f"Previously processed: "
        f"{len(store.processed_urls())}"
    )
    print()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=HEADLESS
        )

        context = browser.new_context(
            viewport={
                "width": 1440,
                "height": 1000,
            }
        )

        page = context.new_page()

        try:
            login(page)

            candidates = {}

            for search_term in SEARCH_TERMS:
                print(f"Searching: {search_term}")

                results = collect_search_results(
                    page,
                    search_term,
                )

                for recruiter in results:
                    candidates.setdefault(
                        recruiter.profile_url,
                        recruiter,
                    )

            print(
                f"\nUnique candidates discovered: "
                f"{len(candidates)}"
            )

            qualified = []

            for recruiter in candidates.values():

                if store.is_processed(
                    recruiter.profile_url
                ):
                    print(
                        f"Skipping processed: "
                        f"{recruiter.name}"
                    )
                    continue

                try:
                    inspect_profile(
                        page,
                        recruiter,
                    )

                    if not is_current_recruiter(
                        recruiter
                    ):
                        recruiter.reason = (
                            "not a current IT/technology recruiter"
                        )
                        store.save(recruiter)
                        store.record_action(
                            recruiter,
                            "rejected",
                        )
                        continue

                    score_recruiter(
                        recruiter
                    )

                    store.save(recruiter)

                    if recruiter.relationship_status == "CONNECTED":
                        store.record_action(
                            recruiter,
                            "connected",
                        )
                        continue

                    if recruiter.relationship_status == "PENDING":
                        store.record_action(
                            recruiter,
                            "pending",
                        )
                        continue

                    if recruiter.score >= 7:
                        qualified.append(recruiter)
                    else:
                        store.record_action(
                            recruiter,
                            "rejected",
                        )

                except Exception as exc:
                    print(
                        f"Inspection error for "
                        f"{recruiter.name}: {exc}"
                    )

            qualified.sort(
                key=lambda item: item.score,
                reverse=True,
            )

            qualified = qualified[
                :MAX_RECRUITERS_PER_SESSION
            ]

            print()
            print(
                f"Qualified recruiters for this session: "
                f"{len(qualified)}"
            )

            for recruiter in qualified:

                page.goto(
                    recruiter.profile_url,
                    wait_until="domcontentloaded",
                )

                display_recruiter(
                    recruiter
                )

                while True:
                    choice = input(
                        "Choice: "
                    ).strip().lower()

                    if choice in {
                        "c",
                        "s",
                        "m",
                        "q",
                    }:
                        break

                if choice == "q":
                    store.record_action(
                        recruiter,
                        "quit",
                    )
                    print(
                        "Session stopped. "
                        "Progress is stored in the CSV."
                    )
                    break

                if choice == "s":
                    store.record_action(
                        recruiter,
                        "skipped",
                    )

                    random_delay(
                        MIN_DELAY_SECONDS,
                        MAX_DELAY_SECONDS,
                    )
                    continue

                if choice == "m":
                    input(
                        "Inspect the profile manually, "
                        "then press ENTER..."
                    )

                    store.record_action(
                        recruiter,
                        "manual_review",
                    )

                    random_delay(
                        MIN_DELAY_SECONDS,
                        MAX_DELAY_SECONDS,
                    )
                    continue

                print()
                print(
                    "Click Connect manually in the browser."
                )
                print(
                    "If Add a note appears, paste the "
                    "suggested message."
                )
                print(
                    "Do not use Message."
                )

                input(
                    "Press ENTER after completing "
                    "the connection request..."
                )

                store.record_action(
                    recruiter,
                    "manually_connected",
                )

                random_delay(
                    MIN_DELAY_SECONDS,
                    MAX_DELAY_SECONDS,
                )

        except KeyboardInterrupt:
            print(
                "\nInterrupted. "
                "Progress has already been saved."
            )

        finally:
            context.close()
            browser.close()

    print()
    print("Session complete.")
    print(
        f"Recruiter data: {RECRUITERS_CSV}"
    )
