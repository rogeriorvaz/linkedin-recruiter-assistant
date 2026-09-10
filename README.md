# LinkedIn Recruiter Assistant

Browser-assisted research and connection workflow for finding relevant UK technology recruiters on LinkedIn.

## Workflow

The application searches for recruiter profiles, verifies the current role conservatively, stores candidates in CSV, and prepares the LinkedIn connection request.

For a qualified recruiter the browser workflow is:

1. Open the recruiter profile.
2. Click **Connect** automatically.
3. Click **Add a note** automatically.
4. Enter the generated connection message automatically.
5. Stop and wait for you to review and click **Send** manually.
6. Press ENTER in the terminal after sending.
7. Save the result to `data/recruiters.csv`.
8. Immediately continue to the next recruiter.

There is deliberately **no random delay** between recruiters because the final Send action is manual.

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

Recruiters are saved when discovered, before connection preparation, and after the final manual Send confirmation. The application verifies each CSV write.

`data/recruiters.csv` is intentionally ignored by Git because it can contain personal recruiter information. Use `data/recruiters.example.csv` as the committed template.

## Important limitation

LinkedIn's interface can change. Current-role extraction and button detection therefore use conservative heuristics and may require maintenance when LinkedIn changes its UI. The application does not click **Send** automatically.
