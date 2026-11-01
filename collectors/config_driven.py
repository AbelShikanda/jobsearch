# collectors/config_driven.py
"""Config-driven collector with optional browser reuse."""
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
    "Chrome/124.0.0.0 Safari/537.36"
)

COOKIE_BUTTONS = [
    "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
    "button:has-text('Allow all')",
    "button:has-text('Accept All Cookies')",
    "button:has-text('Accept All')",
    "button:has-text('Allow selection')",
]


class ConfigDrivenCollector(BaseCollector):
    name = "config_driven"

    def __init__(self, site_config: dict):
        self.cfg = site_config
        self.name = site_config.get("name", "config_driven")

    async def fetch(self, browser: Browser | None = None) -> list[Job]:
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
                locale="en-KE",
                timezone_id="Africa/Nairobi",
                extra_http_headers={
                    "Accept-Language": "en-KE,en;q=0.9",
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,image/avif,"
                        "image/webp,*/*;q=0.8"
                    ),
                    "Referer": "https://www.google.com/",
                    "Upgrade-Insecure-Requests": "1",
                },
            )
            page = await context.new_page()
            page.set_default_navigation_timeout(config.NAV_TIMEOUT_MS)

            try:
                await page.goto(
                    self.cfg["url"],
                    wait_until="domcontentloaded",
                )
            except PWTimeout:
                print(f"[{self.name}] timeout loading "
                      f"{self.cfg['url']}")
                await context.close()
                return jobs

            await self._dismiss_cookies(page)

            try:
                await page.wait_for_selector(
                    self.cfg["wait_for"],
                    timeout=15000,
                )
            except PWTimeout:
                print(f"[{self.name}] timeout waiting for "
                      f"'{self.cfg['wait_for']}' on "
                      f"{self.cfg['url']}")
                await context.close()
                return jobs

            extra = self.cfg.get("extra_wait_ms", 0)
            if extra:
                await page.wait_for_timeout(extra)

            cards = await page.query_selector_all(
                self.cfg["card_selector"]
            )

            if not cards:
                all_links = await page.query_selector_all("a")
                print(f"[{self.name}] DEBUG: 0 cards matched "
                      f"'{self.cfg['card_selector']}' — "
                      f"{len(all_links)} anchors on page")
                for a in all_links[:10]:
                    t = ((await a.inner_text()) or "").strip()[:50]
                    h = await a.get_attribute("href")
                    print(f"[{self.name}] DEBUG:   {t!r} → {h}")

            link_sel = self.cfg.get("link_selector", "a")
            card_is_link = (link_sel == "")

            seen = set()
            for card in cards:
                if card_is_link:
                    href = await card.get_attribute("href")
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = urljoin(self.cfg["url"], href)
                    if href in seen:
                        continue
                    seen.add(href)

                    if self.cfg.get("title_selector"):
                        title_el = await card.query_selector(
                            self.cfg["title_selector"]
                        )
                        title = (
                            ((await title_el.inner_text()) or "").strip()
                            if title_el else ""
                        )
                    else:
                        title = ((await card.inner_text()) or "").strip()

                    if not title or len(title) < 4:
                        continue

                else:
                    title_el = await card.query_selector(
                        self.cfg["title_selector"]
                    )
                    if not title_el:
                        continue
                    title = ((await title_el.inner_text()) or "").strip()
                    if not title or len(title) < 4:
                        continue

                    link_el = await card.query_selector(link_sel)
                    if not link_el:
                        continue
                    href = await link_el.get_attribute("href")
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = urljoin(self.cfg["url"], href)
                    if href in seen:
                        continue
                    seen.add(href)

                company = self.cfg.get("company", "")
                if self.cfg.get("company_selector"):
                    c_el = await card.query_selector(
                        self.cfg["company_selector"]
                    )
                    if c_el:
                        company = (
                            ((await c_el.inner_text()) or "").strip()
                            or company
                        )

                location = self.cfg.get("location", "")
                if self.cfg.get("location_selector"):
                    l_el = await card.query_selector(
                        self.cfg["location_selector"]
                    )
                    if l_el:
                        location = (
                            ((await l_el.inner_text()) or "").strip()
                            or location
                        )

                jobs.append(Job(
                    title=title[:120],
                    company=company[:100],
                    location=location[:60],
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

    async def _dismiss_cookies(self, page) -> None:
        for sel in COOKIE_BUTTONS:
            try:
                await page.click(sel, timeout=1500)
                await page.wait_for_timeout(500)
                return
            except Exception:
                continue