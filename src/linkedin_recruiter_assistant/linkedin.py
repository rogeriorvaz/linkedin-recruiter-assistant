"""LinkedIn browser interaction using Playwright."""

import random
import re
import time
from urllib.parse import quote_plus

from playwright.sync_api import Page

from .config import (
    CURRENT_RECRUITER_TERMS,
    MAX_SEARCH_RESULTS_PER_TERM,
    SEARCH_LOCATION,
)
from .recruiter import Recruiter


def build_search_url(search_term: str) -> str:
    return (
        "https://www.linkedin.com/search/results/people/"
        f"?keywords={quote_plus(search_term)}"
        f"&location={quote_plus(SEARCH_LOCATION)}"
    )


def login(page: Page) -> None:
    page.goto(
        "https://www.linkedin.com/",
        wait_until="domcontentloaded",
    )

    print()
    print("Log into LinkedIn manually if required.")
    print("Complete any verification or security checks manually.")
    print()

    input("Press ENTER when LinkedIn is ready...")


def collect_search_results(
    page: Page,
    search_term: str,
) -> list[Recruiter]:
    page.goto(
        build_search_url(search_term),
        wait_until="domcontentloaded",
    )

    page.wait_for_timeout(
        random.randint(2500, 4500)
    )

    for _ in range(4):
        page.mouse.wheel(0, 1300)
        page.wait_for_timeout(900)

    candidates = []
    seen = set()

    links = page.locator('a[href*="/in/"]')

    count = min(
        links.count(),
        MAX_SEARCH_RESULTS_PER_TERM,
    )

    for index in range(count):
        try:
            link = links.nth(index)

            href = link.get_attribute("href")

            if not href or "/in/" not in href:
                continue

            profile_url = href.split("?", 1)[0]

            if profile_url in seen:
                continue

            name = link.inner_text(
                timeout=1000
            ).strip()

            if not name or len(name) > 150:
                continue

            seen.add(profile_url)

            candidates.append(
                Recruiter(
                    name=name,
                    profile_url=profile_url,
                )
            )

        except Exception:
            continue

    return candidates


def extract_headline(page: Page) -> str:
    selectors = [
        "div.text-body-medium.break-words",
        "div.text-body-medium",
    ]

    for selector in selectors:
        try:
            value = page.locator(
                selector
            ).first.inner_text(
                timeout=1000
            ).strip()

            if value:
                return value

        except Exception:
            continue

    return ""


def extract_location(page: Page) -> str:
    selectors = [
        "span.text-body-small.inline.t-black--light.break-words",
        "span.text-body-small",
    ]

    for selector in selectors:
        try:
            value = page.locator(
                selector
            ).first.inner_text(
                timeout=1000
            ).strip()

            if value:
                return value

        except Exception:
            continue

    return ""


def extract_current_role(
    page_text: str,
) -> tuple[str, str]:

    match = re.search(
        r"\bExperience\b",
        page_text,
        flags=re.IGNORECASE,
    )

    if not match:
        return "", ""

    section = page_text[
        match.start():match.start() + 8000
    ]

    lines = [
        line.strip()
        for line in section.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if any(
            term in line.lower()
            for term in CURRENT_RECRUITER_TERMS
        ):

            role = line
            company = ""

            for following in lines[
                index + 1:index + 6
            ]:

                if not following:
                    continue

                if re.search(
                    r"\b\d{4}\b",
                    following,
                ):
                    continue

                if any(
                    term in following.lower()
                    for term in (
                        "present",
                        "current",
                        "months",
                        "years",
                        "full-time",
                        "part-time",
                    )
                ):
                    continue

                company = following
                break

            return role, company

    return "", ""


def detect_relationship_status(
    page: Page,
) -> str:
    """
    Return a conservative relationship classification.

    UNKNOWN is intentionally preserved when the page does not provide
    enough evidence. UNKNOWN must never be treated as permission to connect.
    """

    try:
        body = " ".join(
            page.locator(
                "body"
            ).inner_text(
                timeout=5000
            ).lower().split()
        )

    except Exception:
        return "UNKNOWN"

    if "pending" in body and (
        "invitation" in body
        or "withdraw" in body
    ):
        return "PENDING"

    if re.search(
        r"\bconnected\b",
        body,
    ):
        return "CONNECTED"

    if re.search(
        r"\bconnect\b",
        body,
    ):
        return "CONNECT_AVAILABLE"

    if re.search(
        r"\bmessage\b",
        body,
    ):
        return "MESSAGE_ONLY"

    return "UNKNOWN"


def inspect_profile(
    page: Page,
    recruiter: Recruiter,
) -> str:

    page.goto(
        recruiter.profile_url,
        wait_until="domcontentloaded",
    )

    page.wait_for_timeout(
        random.randint(2200, 4000)
    )

    for _ in range(4):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(700)

    body = page.locator(
        "body"
    ).inner_text(
        timeout=5000
    )

    recruiter.headline = extract_headline(page)
    recruiter.location = extract_location(page)

    (
        recruiter.current_role,
        recruiter.current_company,
    ) = extract_current_role(body)

    recruiter.relationship_status = (
        detect_relationship_status(page)
    )

    return body


def random_delay(
    minimum: int,
    maximum: int,
) -> None:

    seconds = random.randint(
        minimum,
        maximum,
    )

    print(
        f"Waiting {seconds // 60}m "
        f"{seconds % 60}s before the next recruiter..."
    )

    time.sleep(seconds)
