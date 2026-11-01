# collectors/turing.py — SKELETON ONLY, needs login and real selectors
import os
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from collectors.base import BaseCollector
from models import Job
import config


class TuringCollector(BaseCollector):
    name = "turing"

    async def fetch(self) -> list[Job]:
        jobs = []
        email = os.getenv("TURING_EMAIL")
        password = os.getenv("TURING_PASSWORD")
        if not email or not password:
            print(f"[{self.name}] missing TURING_EMAIL/TURING_PASSWORD in .env")
            return jobs

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=config.HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            # TODO: replace with real login flow after inspecting turing.com/login
            await page.goto("https://www.turing.com/login")
            # await page.fill("input[name=email]", email)
            # await page.fill("input[name=password]", password)
            # await page.click("button[type=submit]")
            # await page.wait_for_url("**/jobs**")

            await page.goto("https://www.turing.com/jobs", wait_until="domcontentloaded")
            await page.wait_for_selector("[data-job-card]", timeout=20000)

            cards = await page.query_selector_all("[data-job-card]")
            print(f"[{self.name}] {len(cards)} cards found")
            for card in cards:
                # TODO: extract title, url from card
                pass

            await browser.close()
        return jobs