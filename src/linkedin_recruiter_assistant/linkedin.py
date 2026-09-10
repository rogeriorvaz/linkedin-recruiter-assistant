import re
from urllib.parse import quote_plus
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
        self.page.set_default_timeout(8000)
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

    def open_people_search(self, term: str, location: str):
        url = (
            "https://www.linkedin.com/search/results/people/?keywords="
            f"{quote_plus(term)}&location={quote_plus(location)}"
        )
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(2000)

    def get_search_cards(self, max_results: int = MAX_RESULTS_PER_TERM) -> list:
        """Return People search result cards without opening profiles."""
        cards = self.page.locator("li.reusable-search__result-container")
        if cards.count() == 0:
            cards = self.page.locator("li").filter(has=self.page.locator('a[href*="/in/"]'))

        results = []
        seen_urls = set()
        count = min(cards.count(), max_results)
        for i in range(count):
            card = cards.nth(i)
            links = card.locator('a[href*="/in/"]')
            if links.count() == 0:
                continue
            url = links.first.get_attribute("href") or ""
            url = url.split("?")[0]
            if "/in/" not in url or url in seen_urls:
                continue
            seen_urls.add(url)
            results.append(card)
        return results

    def search_results(self, term: str, location: str, max_results: int = MAX_RESULTS_PER_TERM) -> list[Recruiter]:
        """Extract recruiter information directly from People search result cards."""
        self.open_people_search(term, location)
        recruiters = []
        for card in self.get_search_cards(max_results):
            recruiter = self._parse_search_card(card)
            if recruiter:
                recruiters.append(recruiter)
        return recruiters

    def _parse_search_card(self, card) -> Recruiter | None:
        try:
            profile_url = (card.locator('a[href*="/in/"]').first.get_attribute("href") or "").split("?")[0]
            text = card.inner_text(" ")
        except Exception:
            return None
        if not profile_url:
            return None

        lines = [re.sub(r"\\s+", " ", x).strip() for x in card.inner_text().splitlines() if x.strip()]
        name = self._extract_name(card, lines)
        headline = self._extract_headline(lines, name)
        location = self._extract_location(lines)
        current_role, current_company = self._extract_current(lines)
        relationship = self._extract_relationship(card, text)

        return Recruiter(
            name=name,
            profile_url=profile_url,
            headline=headline,
            current_role=current_role,
            current_company=current_company,
            location=location,
            relationship_status=relationship,
        )

    def _extract_name(self, card, lines):
        try:
            # The first profile link is normally the member's name.
            value = card.locator('a[href*="/in/"]').first.inner_text().strip()
            if value:
                return re.sub(r"\\s+", " ", value)
        except Exception:
            pass
        return lines[0] if lines else "Unknown"

    def _extract_headline(self, lines, name):
        for i, line in enumerate(lines):
            if line.lower().startswith(name.lower()):
                if i + 1 < len(lines):
                    return lines[i + 1]
        return lines[1] if len(lines) > 1 else ""

    def _extract_location(self, lines):
        for line in lines:
            lower = line.lower()
            if any(x in lower for x in ["united kingdom", "england", "scotland", "wales", "northern ireland"]):
                return line
        return ""

    def _extract_current(self, lines):
        # Search cards commonly expose a line such as:
        # Current: Technical Recruiter at Index
        # Past: ...
        # We deliberately only accept Current:, never Past: or page-wide text.
        for line in lines:
            if line.lower().startswith("current:"):
                value = line.split(":", 1)[1].strip()
                return self._split_role_company(value)
        return "", ""

    @staticmethod
    def _split_role_company(value):
        # Handles "Technical Recruiter at Index". Keep the role/company conservative.
        match = re.match(r"(.+?)\\s+at\\s+(.+)$", value, flags=re.I)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return value, ""

    def _extract_relationship(self, card, text):
        try:
            buttons = card.get_by_role("button")
            for i in range(buttons.count()):
                label = (buttons.nth(i).get_attribute("aria-label") or buttons.nth(i).inner_text()).strip().lower()
                if re.search(r"\\bpending\\b", label):
                    return "PENDING"
                if re.search(r"\\bconnect\\b", label):
                    return "CONNECT_AVAILABLE"
                if re.search(r"\\bconnected\\b", label):
                    return "CONNECTED"
                if re.search(r"\\bmessage\\b", label):
                    return "MESSAGE_ONLY"
        except Exception:
            pass

        lower = text.lower()
        if re.search(r"\\bpending\\b", lower):
            return "PENDING"
        if re.search(r"\\bconnected\\b", lower):
            return "CONNECTED"
        return "UNKNOWN"

    def click_connect_from_card(self, recruiter: Recruiter) -> bool:
        """Find the search card for this recruiter and click its Connect button."""
        card = self._find_card_by_profile_url(recruiter.profile_url)
        if card is None:
            return False
        button = card.get_by_role("button", name=re.compile(r"^connect$", re.I)).first
        if button.count() == 0:
            return False
        button.click()
        self.page.wait_for_timeout(700)
        return True

    def _find_card_by_profile_url(self, profile_url: str):
        cards = self.page.locator("li.reusable-search__result-container")
        if cards.count() == 0:
            cards = self.page.locator("li").filter(has=self.page.locator('a[href*="/in/"]'))
        for i in range(cards.count()):
            card = cards.nth(i)
            links = card.locator('a[href*="/in/"]')
            for j in range(links.count()):
                href = (links.nth(j).get_attribute("href") or "").split("?")[0]
                if href == profile_url:
                    return card
        return None

    def connect_from_profile_fallback(self, profile_url: str) -> bool:
        """Fallback only when the search card has no usable Connect button."""
        self.page.goto(profile_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1200)
        button = self.page.get_by_role("button", name=re.compile(r"^connect$", re.I)).first
        if button.count() == 0:
            return False
        button.click()
        self.page.wait_for_timeout(700)
        return True

    def prepare_connection_note(self, message: str) -> bool:
        """Open Add a note and fill the message. Never clicks Send."""
        try:
            add_note = self.page.get_by_role("button", name=re.compile(r"add a note", re.I)).first
            if add_note.count() > 0:
                add_note.click(timeout=5000)
            else:
                self.page.get_by_text(re.compile(r"^add a note$", re.I)).first.click(timeout=5000)
        except PlaywrightTimeoutError:
            return False

        self.page.wait_for_timeout(500)
        boxes = self.page.get_by_role("textbox")
        if boxes.count() == 0:
            return False
        boxes.last.fill(message)
        return True
