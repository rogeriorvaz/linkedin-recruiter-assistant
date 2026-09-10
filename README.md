# LinkedIn Recruiter Assistant

Browser-assisted research and connection workflow for finding relevant UK technology recruiters on LinkedIn.

## Search-first workflow

The application now uses the LinkedIn **People search results page as the primary data source**. It does not open each recruiter profile just to determine whether the person is relevant.

From each search result card it reads:

- Name
- Headline
- Current role and company when LinkedIn exposes a `Current:` line
- Location
- Connection state such as Connect, Pending or Connected
- Profile URL

A recruiter profile is opened only as a fallback when the search result card does not expose a usable Connect button.

## Connection workflow

For a qualified recruiter:

1. Click **Connect** directly on the People search result card.
2. If the card has no usable Connect button, open the profile and try Connect there.
3. Click **Add a note**.
4. Enter the generated connection message.
5. Stop and wait for you to review and click **Send** manually.
6. Press ENTER in the terminal after sending.
7. Save the result to `data/recruiters.csv`.
8. Continue immediately to the next recruiter.

There is no artificial random delay.

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

or:

```bash
linkedin-recruiter-assistant
```

## CSV persistence

Recruiters are saved as soon as their People search result is parsed. They are then updated as they are qualified, skipped, or processed. Each write is verified.

`data/recruiters.csv` is ignored by Git because it can contain personal recruiter information. Use `data/recruiters.example.csv` as the committed template.

## LinkedIn UI changes

LinkedIn can change its page structure and accessible labels. The People search parser therefore uses Playwright locators and conservative fallbacks. If the search card structure changes, `linkedin.py` is the main file that will need updating.

The final **Send** action is intentionally manual.
