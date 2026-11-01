# collectors/wwr.py
from urllib.parse import urljoin
from playwright.async_api import (
    async_playwright,
    TimeoutError as PWTimeout,
    Browser,
)
from collectors.base import BaseCollector
from models import Job
import config


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


class WWRCollector(BaseCollector):
    name = "wwr"
    BASE = "https://weworkremotely.com/remote-jobs/search?term={term}"

    def __init__(self, term: str = "python"):
        self.term = term
        self.url = self.BASE.format(term=term)

    async def fetch(self, browser: Browser | None = None) -> list[Job]:
        """
        If browser is provided, reuse it. Otherwise launch a temporary one.
        """
        jobs: list[Job] = []
        owns_browser = browser is None
        local_browser = browser
        playwright_ctx = None

        try:
            if local_browser is None:
                playwright_ctx = await async_playwright().start()
                local_browser = await playwright_ctx.chromium.launch(
                    headless=config.HEADLESS
                )

            context = await local_browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 900},
            )
            page = await context.new_page()
            page.set_default_navigation_timeout(config.NAV_TIMEOUT_MS)

            try:
                await page.goto(self.url, wait_until="domcontentloaded")
                await page.wait_for_selector(
                    "section.jobs, li.feature, article",
                    timeout=15000,
                )
            except PWTimeout:
                print(f"[{self.name}] timeout on {self.url}")
                await context.close()
                return jobs

            # Grab only job links — filtered by URL pattern
            anchors = await page.query_selector_all("a[href*='/remote-jobs/']")
            print(f"[{self.name}] '{self.term}': {len(anchors)} job links")

            # ── DEBUG: if zero, dump what we see ───────────
            if len(anchors) == 0:
                all_anchors = await page.query_selector_all("a")
                print(f"[{self.name}] DEBUG: {len(all_anchors)} total anchors")
                for a in all_anchors[:15]:
                    t = ((await a.inner_text()) or "").strip()[:50]
                    href = await a.get_attribute("href")
                    print(f"[{self.name}] DEBUG:   {t!r} → {href}")

            seen = set()
            for a in anchors:
                href = await a.get_attribute("href")
                if not href or href in seen:
                    continue
                seen.add(href)
                if href.startswith("/"):
                    href = urljoin("https://weworkremotely.com", href)

                text = ((await a.inner_text()) or "").strip()
                if not text or len(text) < 4:
                    continue

                jobs.append(Job(
                    title=text[:120],
                    company="",
                    location="Remote",
                    url=href,
                    source=self.name,
                ))

            await context.close()

        except Exception as e:
            print(f"[{self.name}] crashed: {e}")
        finally:
            if owns_browser and local_browser is not None:
                await local_browser.close()
            if playwright_ctx is not None:
                await playwright_ctx.stop()

        return jobs