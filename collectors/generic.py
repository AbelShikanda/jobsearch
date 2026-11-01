from urllib.parse import urljoin
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from collectors.base import BaseCollector
from models import Job
import config


class PlaywrightGenericCollector(BaseCollector):
    name = "generic"

    def __init__(self, start_url: str, link_selector: str = "a"):
        self.start_url = start_url
        self.link_selector = link_selector

    async def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=config.HEADLESS)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 900},
                )
                page = await context.new_page()
                page.set_default_navigation_timeout(config.NAV_TIMEOUT_MS)

                try:
                    await page.goto(self.start_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    anchors = await page.query_selector_all(self.link_selector)
                except PWTimeout:
                    print(f"[{self.name}] timeout on {self.start_url}")
                    anchors = []

                seen = set()
                for a in anchors:
                    href = await a.get_attribute("href")
                    text = ((await a.inner_text()) or "").strip()
                    if not href or not text or len(text) < 8:
                        continue
                    if href.startswith("/"):
                        href = urljoin(self.start_url, href)
                    if href in seen:
                        continue
                    seen.add(href)
                    if not self._matches(text):
                        continue
                    jobs.append(Job(
                        title=text[:120],
                        company="",
                        location="",
                        url=href,
                        source=self.name,
                    ))
        except Exception as e:
            print(f"[{self.name}] crashed: {e}")
        return jobs

    def _matches(self, text: str) -> bool:
        t = text.lower()
        return any(term.lower() in t for term in config.SEARCH_TERMS)