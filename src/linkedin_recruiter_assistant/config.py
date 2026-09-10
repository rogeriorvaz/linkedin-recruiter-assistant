from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RECRUITERS_CSV = DATA_DIR / "recruiters.csv"

SEARCH_DELAY_MIN_SECONDS = 5
SEARCH_DELAY_MAX_SECONDS = 20

SEARCH_LOCATION = "United Kingdom"
MAX_RESULTS_PER_TERM = 20
MAX_RECRUITERS_PER_SESSION = 10
HEADLESS = False

SEARCH_TERMS = [
    "IT Recruiter", "Technology Recruiter", "Technical Recruiter",
    "IT Recruitment Consultant", "Technology Recruitment Consultant",
    "Tech Recruiter", "Technology Talent Acquisition", "IT Talent Acquisition",
    "Technical Talent Partner",
]

CURRENT_RECRUITER_TERMS = [
    "it recruiter", "technology recruiter", "technical recruiter", "tech recruiter",
    "it recruitment", "technology recruitment", "technical recruitment",
    "recruitment consultant", "talent acquisition", "technical talent",
    "technology talent", "talent partner", "resourcing consultant",
    "recruitment lead", "recruitment director", "head of recruitment",
]

TECHNOLOGY_TERMS = [
    "technology", "technical", "information technology", "software", "engineering",
    "cloud", "data", "cyber", "digital", "infrastructure", "devops", "development", "it",
]
SENIOR_TERMS = ["senior", "lead", "principal", "manager", "director", "head", "partner"]
NEGATIVE_CURRENT_TERMS = [
    "software engineer", "software developer", "developer", "project manager",
    "programme manager", "program manager", "delivery manager", "delivery lead",
    "scrum master", "product manager", "product owner", "business analyst",
    "solutions architect", "technical architect",
]
RECRUITMENT_COMPANY_TERMS = ["recruitment", "recruiting", "staffing", "talent", "resourcing", "executive search"]
