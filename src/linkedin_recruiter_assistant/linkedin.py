import re
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from .config import HEADLESS, MAX_RESULTS_PER_TERM
from .recruiter import Recruiter

class LinkedInClient:
    def __init__(self, headless=HEADLESS): self.headless=headless; self.playwright=self.browser=self.context=self.page=None
    def start(self):
        self.playwright=sync_playwright().start(); self.browser=self.playwright.chromium.launch(headless=self.headless)
        self.context=self.browser.new_context(viewport={"width":1440,"height":1000}); self.page=self.context.new_page(); self.page.set_default_timeout(8000)
        self.page.goto("https://www.linkedin.com/", wait_until="domcontentloaded")
    def stop(self):
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
    def wait_for_manual_login(self): input("Press ENTER when LinkedIn is ready...")
    def open_people_search(self, term, location):
        url=f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(term)}&location={quote_plus(location)}"
        self.page.goto(url, wait_until="domcontentloaded"); self.page.wait_for_timeout(2500)
        self._wait_for_results()
    def _wait_for_results(self):
        try:
            self.page.locator('a[href*="/in/"]').first.wait_for(timeout=10000)
        except Exception:
            pass

    def get_search_cards(self, max_results=MAX_RESULTS_PER_TERM):
        """Find LinkedIn People search result cards without relying on CSS classes."""
        profile_links = self.page.locator('a[href*="/in/"]')
        link_count = profile_links.count()
        print(f"Profile links found: {link_count}")

        # Build candidate <li> elements containing profile links and buttons.
        # LinkedIn's result-card class names change, but the result remains a
        # list item with a profile link and an action button.
        list_items = self.page.locator("li").filter(
            has=self.page.locator('a[href*="/in/"]')
        ).filter(
            has=self.page.locator("button")
        )

        candidates = {}
        for i in range(list_items.count()):
            item = list_items.nth(i)
            try:
                links = item.locator('a[href*="/in/"]')
                if links.count() == 0:
                    continue

                href = (links.first.get_attribute("href") or "").split("?")[0].strip()
                if not href:
                    continue

                text = item.inner_text(timeout=1500).strip()
                lower = text.lower()
                if not any(x in lower for x in (
                    "connect", "pending", "follow", "current:", "past:"
                )):
                    continue

                # There can be several nested <li> elements for one result.
                # Keep the smallest useful one, which is normally the actual card.
                existing = candidates.get(href)
                if existing is None:
                    candidates[href] = (item, len(text))
                elif len(text) < existing[1]:
                    candidates[href] = (item, len(text))
            except Exception:
                continue

        cards = [(item, href) for href, (item, _) in candidates.items()]
        cards = cards[:max_results]

        print(f"Search cards found: {len(cards)}")
        if link_count and not cards:
            print("WARNING: Profile links were found, but no result cards matched.")
        return cards
    def search_results(self, term, location, max_results=MAX_RESULTS_PER_TERM):
        self.open_people_search(term, location)
        return [r for card, _ in self.get_search_cards(max_results) if (r:=self._parse_search_card(card))]
    def _parse_search_card(self, card):
        try:
            links=card.locator('a[href*="/in/"]'); profile_url=(links.first.get_attribute("href") or "").split("?")[0]
            if not profile_url: return None
            lines=[re.sub(r"\s+"," ",x).strip() for x in card.inner_text().splitlines() if x.strip()]
            name=links.first.inner_text().strip() or (lines[0] if lines else "Unknown")
            headline=self._headline(lines,name); location=self._location(lines); role,company=self._current(lines); rel=self._relationship(card, lines)
            return Recruiter(name=name, profile_url=profile_url, headline=headline, current_role=role, current_company=company, location=location, relationship_status=rel)
        except Exception: return None
    def _headline(self, lines, name):
        for i,x in enumerate(lines):
            if x.lower().startswith(name.lower()) and i+1<len(lines): return lines[i+1]
        return lines[1] if len(lines)>1 else ""
    def _location(self, lines):
        for x in lines:
            if any(k in x.lower() for k in ["united kingdom","england","scotland","wales","northern ireland"]): return x
        return ""
    def _current(self, lines):
        for x in lines:
            if x.lower().startswith("current:"):
                return self._split_role_company(x.split(":",1)[1].strip())
        return "",""
    def _split_role_company(self, value):
        m=re.match(r"(.+?)\s+at\s+(.+)$", value, re.I)
        return (m.group(1).strip(),m.group(2).strip()) if m else (value,"")
    def _relationship(self, card, lines):
        try:
            buttons=card.get_by_role("button")
            labels=[]
            for i in range(buttons.count()):
                b=buttons.nth(i); labels.append(((b.get_attribute("aria-label") or b.inner_text()).strip()).lower())
            for label in labels:
                if re.search(r"\bpending\b",label): return "PENDING"
                if re.search(r"\bconnected\b",label): return "CONNECTED"
                if re.search(r"\bconnect\b",label): return "CONNECT_AVAILABLE"
                if re.search(r"\bmessage\b",label): return "MESSAGE_ONLY"
                if re.search(r"\bfollow\b",label): return "FOLLOW_ONLY"
        except Exception: pass
        text=" ".join(lines).lower()
        if re.search(r"\bpending\b",text): return "PENDING"
        if re.search(r"\bconnected\b",text): return "CONNECTED"
        return "UNKNOWN"
    def click_connect_on_card(self, profile_url):
        for card, href in self.get_search_cards(MAX_RESULTS_PER_TERM):
            if href==profile_url:
                btn=card.get_by_role("button",name=re.compile(r"^connect$",re.I)).first
                if btn.count()>0: btn.click(); self.page.wait_for_timeout(700); return True
        return False
    def click_connect_profile_fallback(self, profile_url):
        self.page.goto(profile_url,wait_until="domcontentloaded"); self.page.wait_for_timeout(1200)
        btn=self.page.get_by_role("button",name=re.compile(r"^connect$",re.I)).first
        if btn.count()==0:return False
        btn.click(); self.page.wait_for_timeout(700); return True
    def prepare_connection_note(self,message):
        try:
            add=self.page.get_by_role("button",name=re.compile(r"add a note",re.I)).first
            if add.count()>0:add.click(timeout=5000)
            else:self.page.get_by_text(re.compile(r"^add a note$",re.I)).first.click(timeout=5000)
            self.page.wait_for_timeout(500); boxes=self.page.get_by_role("textbox")
            if boxes.count()==0:return False
            boxes.last.fill(message); return True
        except PlaywrightTimeoutError:return False
