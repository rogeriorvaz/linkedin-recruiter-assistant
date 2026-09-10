# LinkedIn Recruiter Assistant

The application uses LinkedIn People search results as the primary source. It does not open every recruiter profile to qualify the person.

## Workflow

1. Search LinkedIn People results.
2. Read each visible result card for name, headline, current role/company, location and relationship state.
3. Save the result to CSV immediately.
4. Qualify the recruiter from search-page evidence.
5. Skip Pending, Connected, Follow-only and other unavailable relationships.
6. Click Connect directly on the search result card.
7. Fall back to the profile only if the search card has no usable Connect button.
8. Open Add a note and enter the connection message.
9. Stop so the user can review and click Send manually.
10. Continue to the next recruiter after ENTER is pressed.

There is no random delay.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

## Run

```bash
python -m linkedin_recruiter_assistant
```

LinkedIn changes its DOM regularly. The search-card parser intentionally avoids relying on one LinkedIn CSS class. It starts from profile links and finds the nearest result ancestor containing action buttons. The final Send action remains manual.
