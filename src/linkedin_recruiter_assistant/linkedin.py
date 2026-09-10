import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from .config import HEADLESS, MAX_RESULTS_PER_TERM
from .recruiter import Recruiter


class LinkedInClient:
    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 1000})
        self.page = self.context.new_page()
        self.page.goto("https://www.linkedin.com/", wait_until="domcontentloaded")

    def stop(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def wait_for_manual_login(self):
        input("Press ENTER when LinkedIn is ready...")

    def search(self, term: str, location: str, max_results: int = MAX_RESULTS_PER_TERM) -> list[str]:
        url = "https://www.linkedin.com/search/results/people/"
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        # Search via LinkedIn UI when possible. This keeps the interaction closer to normal browser use.
        try:
            search_box = self.page.get_by_role("combobox", name=re.compile("Search", re.I)).first
            search_box.fill(f"{term} {location}")
            search_box.press("Enter")
            self.page.wait_for_timeout(2500)
        except Exception:
            # Fall back to the search URL used by LinkedIn if the UI search box is unavailable.
            from urllib.parse import quote_plus
            self.page.goto(
                f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(term)}&location={quote_plus(location)}",
                wait_until="domcontentloaded",
            )
            self.page.wait_for_timeout(2500)

        urls = []
        for href in self.page.locator('a[href*="/in/"]').evaluate_all("els => els.map(e => e.href)"):
            href = href.split("?")[0]
            if "/in/" in href and href not in urls:
                urls.append(href)
            if len(urls) >= max_results:
                break
        return urls

    def inspect_profile(self, profile_url: str) -> Recruiter:
        self.page.goto(profile_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1800)
        body = self.page.locator("body").inner_text(timeout=10000)
        lines = [x.strip() for x in body.splitlines() if x.strip()]

        name = self._profile_name(lines)
        headline = self._headline(lines, name)
        location = self._location(lines)
        relationship = self.detect_relationship()
        current_role, current_company = self._extract_current_experience(lines)

        return Recruiter(
            name=name,
            profile_url=profile_url,
            headline=headline,
            current_role=current_role,
            current_company=current_company,
            location=location,
            relationship_status=relationship,
        )

    def _profile_name(self, lines):
        for line in lines[:15]:
            if 2 <= len(line.split()) <= 5 and not line.lower().startswith(("about", "experience", "contact")):
                return re.sub(r"\\s+", " ", line)
        return "Unknown"

    def _headline(self, lines, name):
        try:
            idx = lines.index(name)
            for line in lines[idx + 1:idx + 5]:
                if len(line) > 20:
                    return line
        except ValueError:
            pass
        return ""

    def _location(self, lines):
        for line in lines[:30]:
            if line in {"United Kingdom", "London Area, United Kingdom", "Manchester Area, United Kingdom", "Birmingham, England, United Kingdom"}:
                return line
        return ""

    def _extract_current_experience(self, lines):
        # Conservative heuristic: locate Experience and inspect the first plausible role entry.
        # If current status cannot be established, return empty values rather than using page-wide text.
        try:
            start = next(i for i, x in enumerate(lines) if x.lower() == "experience")
        except StopIteration:
            return "", ""

        section = lines[start + 1:start + 45]
        stop_words = {"education", "skills", "licenses & certifications", "recommendations"}
        cleaned = []
        for line in section:
            if line.lower() in stop_words:
                break
            cleaned.append(line)

        for i, line in enumerate(cleaned):
            lower = line.lower()
            if "present" in lower or "current" in lower:
                # Look backwards for a plausible title and company.
                for j in range(max(0, i - 4), i):
                    candidate = cleaned[j]
                    if len(candidate) < 120 and not self._looks_like_date(candidate):
                        # Prefer a recruiter-like title.
                        if any(t in candidate.lower() for t in ["recruiter", "recruitment", "talent acquisition", "talent partner", "resourcing"]):
                            company = cleaned[j + 1] if j + 1 < len(cleaned) else ""
                            return candidate, company

        # If the first experience item is clearly a current-looking role without an explicit date,
        # use it only when its structure strongly resembles an experience entry.
        for i, line in enumerate(cleaned[:12]):
            if any(t in line.lower() for t in ["recruiter", "recruitment", "talent acquisition", "talent partner", "resourcing"]):
                company = cleaned[i + 1] if i + 1 < len(cleaned) else ""
                if company and len(company) < 120:
                    return line, company
        return "", ""

    @staticmethod
    def _looks_like_date(value):
        return bool(re.search(r"\\b(20\\d{2}|19\\d{2}|present|month|year)\\b", value.lower()))

    def detect_relationship(self) -> str:
        # Prefer visible buttons and explicit status text. UNKNOWN is safer than a false positive.
        body = self.page.locator("body").inner_text(timeout=10000).lower()
        if re.search(r"\\bpending\\b", body):
            return "PENDING"
        if re.search(r"\\bconnected\\b", body):
            return "CONNECTED"
        try:
            if self.page.get_by_role("button", name=re.compile(r"^connect$", re.I)).count() > 0:
                return "CONNECT_AVAILABLE"
            if self.page.get_by_role("button", name=re.compile(r"message", re.I)).count() > 0:
                return "MESSAGE_ONLY"
        except Exception:
            pass
        return "UNKNOWN"

    def connect_and_prepare_message(self, message: str) -> bool:
        """Click Connect, open Add a note, and fill the message. Never click Send."""
        connect = self.page.get_by_role("button", name=re.compile(r"^connect$", re.I)).first
        connect.click()
        self.page.wait_for_timeout(800)

        add_note = self.page.get_by_role("button", name=re.compile(r"add a note", re.I)).first
        try:
            add_note.click(timeout=5000)
        except PlaywrightTimeoutError:
            # Some LinkedIn variants expose Add a note as visible text rather than a button.
            self.page.get_by_text(re.compile(r"^add a note$", re.I)).first.click(timeout=5000)

        self.page.wait_for_timeout(500)
        textbox = self.page.get_by_role("textbox").last
        textbox.fill(message)
        return True
