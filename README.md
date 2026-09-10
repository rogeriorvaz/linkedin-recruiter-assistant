# LinkedIn Recruiter Assistant

A Python and Playwright based browser assistant for finding relevant UK IT and technology recruiters on LinkedIn.

The application searches for recruiters, verifies their current employment, checks the available LinkedIn relationship status, scores recruiter relevance, maintains persistent progress, and presents suitable recruiters for manual connection.

The application **does not automatically send connection invitations or messages**.

## Features

* Search LinkedIn for UK IT and technology recruiters.
* Search using multiple recruiter titles.
* Inspect current employment information.
* Distinguish current recruiter roles from previous employment where possible.
* Identify technology focused recruiters.
* Detect existing connections where LinkedIn exposes the status.
* Detect pending invitations where LinkedIn exposes the status.
* Avoid processing previously handled profiles.
* Maintain persistent state between sessions.
* Store recruiter information in SQLite.
* Score recruiters based on relevance.
* Generate a suggested connection message.
* Allow manual approval before connecting.
* Introduce a configurable delay between manual processing steps.
* Gracefully preserve progress when the application stops.
* Provide a foundation for additional recruiter matching rules.

## Important

This project is a browser automation and research assistant.

It does not automatically click LinkedIn's **Connect** button or automatically send connection requests.

The final connection action is performed manually by the user.

Users are responsible for complying with LinkedIn's current terms, policies, and applicable laws.

LinkedIn changes its user interface regularly. Selectors and profile parsing logic may therefore require maintenance.

## Why manual connection?

The purpose of this project is to reduce repetitive research while keeping the final account action under the user's control.

The application can identify a suitable recruiter and prepare the information required for a connection, but the user decides whether to connect.

This also provides an opportunity to review the recruiter before sending a request.

## Requirements

* Python 3.11 or later
* Google Chrome or Chromium compatible browser
* LinkedIn account
* Playwright

The project currently uses SQLite, which is included with Python and requires no separate database server.

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/linkedin-recruiter-assistant.git

cd linkedin-recruiter-assistant
```

Create a virtual environment:

### Linux / macOS

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### Windows

```powershell
py -m venv .venv

.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -e .
```

Install the Playwright browser:

```bash
playwright install chromium
```

## Running

Run:

```bash
python -m linkedin_recruiter_assistant
```

The application opens a browser.

Log into LinkedIn manually.

Complete any security or verification steps manually.

Return to the terminal and press Enter.

The application then begins searching for recruiters.

## Configuration

Configuration is stored in:

```text
src/linkedin_recruiter_assistant/config.py
```

The main settings include:

```python
SEARCH_LOCATION = "United Kingdom"
```

Recruiter search terms:

```python
SEARCH_TERMS = [
    "IT Recruiter",
    "Technology Recruiter",
    "Technical Recruiter",
    "IT Recruitment Consultant",
    "Technology Recruitment Consultant",
    "Tech Recruiter",
]
```

Maximum recruiters reviewed in one session:

```python
MAX_RECRUITERS_PER_SESSION = 10
```

Delay between manual processing:

```python
MIN_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 300
```

The default range is therefore between 1 and 5 minutes.

## Recruiter matching

The application evaluates several signals.

### Current recruiter role

Examples include:

* IT Recruiter
* Technology Recruiter
* Technical Recruiter
* Technology Recruitment Consultant
* IT Recruitment Consultant
* Technical Talent Partner
* Technology Talent Acquisition

### Technology focus

The application looks for terms such as:

* Technology
* Technical
* Software
* Engineering
* Cloud
* Data
* Cyber
* Digital
* Infrastructure
* DevOps
* IT

### Seniority

Additional points can be awarded for roles containing:

* Senior
* Lead
* Principal
* Manager
* Director
* Head
* Partner

### Negative signals

The application can reject profiles where the current role appears to be something such as:

* Software Engineer
* Software Developer
* Project Manager
* Programme Manager
* Delivery Manager
* Scrum Master
* Product Manager
* Product Owner
* Business Analyst
* Solutions Architect

The purpose is to avoid treating someone as a recruiter simply because they previously worked in recruitment.

## Recruiter scoring

The scoring system is configurable.

A typical score might be:

| Signal                         | Points |
| ------------------------------ | -----: |
| Current recruiter role         |     +5 |
| Technology focus               |     +3 |
| UK location                    |     +2 |
| Recruitment company            |     +2 |
| Senior recruiter               |     +1 |
| Clearly unrelated current role |    -10 |

Only recruiters above the configured threshold are presented for manual review.

## Connection workflow

When a suitable recruiter is found, the application displays:

* Name
* Profile URL
* Current role
* Current company
* Location
* Relationship status
* Recruiter score
* Reason for the score
* Suggested connection message

The user then chooses an action.

```text
C = Connect
S = Skip
M = Manual review
Q = Quit
```

If `C` is selected, the application instructs the user to click **Connect manually** in the browser.

If LinkedIn presents the **Add a note** option, the user can paste the generated message.

The application then records the result.

## Persistent state

The application uses SQLite:

```text
linkedin_recruiters.db
```

The database stores information such as:

* Profile URL
* Name
* Headline
* Current role
* Current company
* Location
* Relationship status
* Recruiter score
* Reason
* Action
* First seen timestamp
* Last seen timestamp
* Last processed timestamp

This means the application does not depend on LinkedIn returning profiles in the same order during every session.

### Example

Session 1:

```text
Recruiter A → connected
Recruiter B → skipped
Recruiter C → pending
Recruiter D → connected
Recruiter E → quit
```

Session 2:

```text
Recruiter A → already processed
Recruiter B → already processed
Recruiter C → pending
Recruiter D → already processed
Recruiter E → available for future processing
```

The application searches for new candidates and uses the database to determine which profiles still require processing.

## Relationship status

The application attempts to classify profiles as:

```text
CONNECTED
PENDING
CONNECT_AVAILABLE
MESSAGE_ONLY
UNKNOWN
```

`UNKNOWN` is intentional.

LinkedIn can change its interface, and the application should not assume that an uncertain state means that a connection is available.

When the state is unknown, the user can manually inspect the profile.

## Message template

The default message is configured in:

```text
src/linkedin_recruiter_assistant/messages.py
```

Example:

> Hi [Name], I’m currently exploring senior technology delivery opportunities and noticed you specialise in technology recruitment. I have 20+ years’ experience across software delivery, Agile, Waterfall, Hybrid delivery and technical leadership. I’d be glad to connect.

Users should customise this message to reflect their own experience and job search.

## Project structure

The project is intentionally split into separate modules.

```text
src/
└── linkedin_recruiter_assistant/
    ├── __init__.py
    ├── __main__.py
    ├── config.py
    ├── database.py
    ├── linkedin.py
    ├── recruiter.py
    ├── scoring.py
    ├── messages.py
    └── cli.py
```

### `config.py`

Contains configurable application settings.

Examples:

* Search terms
* Location
* Score threshold
* Session limits
* Delay settings

### `database.py`

Responsible for:

* SQLite connection
* Database creation
* Recruiter persistence
* Session state
* Action history

### `linkedin.py`

Responsible for browser interaction.

Examples:

* Opening LinkedIn
* Performing searches
* Opening profiles
* Reading visible profile information
* Detecting relationship status

### `recruiter.py`

Contains recruiter data structures and recruiter-related business logic.

### `scoring.py`

Contains recruiter relevance scoring.

This module should not contain browser-specific code.

That separation makes the scoring logic easier to test.

### `messages.py`

Contains connection-message generation.

### `cli.py`

Controls the interactive command-line workflow.

### `__main__.py`

Provides the application entry point:

```bash
python -m linkedin_recruiter_assistant
```

## Tests

Tests should be stored under:

```text
tests/
```

For example:

```text
tests/
├── test_scoring.py
├── test_database.py
└── test_messages.py
```

The scoring and database logic should be tested without opening a browser.

Browser integration tests should be kept separate because they depend on an external website and its current UI.

## Development

Install the project in editable mode:

```bash
python -m pip install -e .
```

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Customising for another user

Before another person uses the application, they should review:

### 1. Search terms

Edit:

```text
config.py
```

Add the recruitment titles relevant to their target market.

### 2. Location

Change:

```python
SEARCH_LOCATION = "United Kingdom"
```

For example:

```python
SEARCH_LOCATION = "United States"
```

### 3. Technology terms

Users targeting different areas can add terms such as:

```text
SAP
Oracle
Salesforce
Microsoft
AI
Machine Learning
Cybersecurity
Data Engineering
DevOps
Cloud
```

### 4. Target roles

The scoring rules should reflect the user's own career objectives.

For example, a software engineer would use different recruiter relevance rules from a programme manager.

### 5. Connection message

Update:

```text
messages.py
```

The message should represent the user's own experience.

### 6. Session limits

Users can change:

```python
MAX_RECRUITERS_PER_SESSION = 10
```

### 7. Delay

Users can change:

```python
MIN_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 300
```

These delays are workflow pacing controls. They are not intended to bypass LinkedIn controls or detection mechanisms.

## Data privacy

The application should not store LinkedIn passwords.

Users log into LinkedIn through the browser.

The SQLite database can contain personal information obtained from public LinkedIn profiles.

Users should therefore:

* Keep the database private.
* Avoid committing the database to Git.
* Add the database to `.gitignore`.
* Avoid sharing personal recruiter data publicly.
* Review local data retention requirements.

The default `.gitignore` should include:

```text
linkedin_recruiters.db
*.db
.venv/
__pycache__/
*.pyc
```

## Limitations

LinkedIn is a third-party website.

Its HTML, CSS selectors, search behaviour, profile layout and available information can change.

Consequently:

* Search parsing may require maintenance.
* Profile parsing may require maintenance.
* Relationship detection may sometimes return `UNKNOWN`.
* The application cannot guarantee that every recruiter is identified.
* The application cannot guarantee that every recruiter is correctly classified.
* Search results depend on LinkedIn's own search system.

The application should therefore be treated as an assistant, not as an authoritative data source.

## Future improvements

Potential improvements include:

* Configurable target job titles.
* Industry-specific recruiter scoring.
* Company-level recruiter filtering.
* Better current-role detection.
* Improved relationship-status detection.
* Recruiter history tracking.
* CSV export.
* JSON export.
* Web dashboard.
* Recruiter prioritisation.
* Personalised connection messages.
* Unit tests for recruiter classification.
* Playwright integration tests.
* Structured logging.
* Configuration through environment variables.
* GitHub Actions CI.
* Automated dependency checks.

## Contributing

Contributions are welcome.

Before submitting a pull request:

1. Create a feature branch.
2. Add or update tests.
3. Keep browser interaction separate from business logic.
4. Avoid storing credentials.
5. Do not commit personal recruiter data.
6. Update the README when behaviour changes.
7. Run the test suite.

## Licence

This project is licensed under the MIT License.

See:

```text
LICENSE
```

## Disclaimer

This project is provided for educational and personal productivity purposes.

It is not affiliated with, endorsed by, or sponsored by LinkedIn.

Users are responsible for complying with LinkedIn's terms, applicable laws, and any organisational policies governing browser automation and data processing.

```
```
